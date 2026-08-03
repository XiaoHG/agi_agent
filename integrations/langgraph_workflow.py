"""LangGraph workflows for the workspace agent project."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agent.tools import run_skill_with_workspace

from .langchain_tools import build_langchain_tools


class RAGGraphState(TypedDict, total=False):
    """State passed between LangGraph nodes for the RAG workflow."""

    question: str  # 用户问题
    route: str  # graph 路由结果
    route_reason: str  # 路由原因
    selected_tool: str  # 选哪个工具
    tool_input: dict[str, str]  # 传给 LangChain tool 的输入
    tool_output: str  # 工具返回结果
    tool_status: str  # 普通工具执行状态，用于 graph 条件边判断
    tool_error: str  # 普通工具失败原因
    skill_run: dict[str, Any]  # skill 执行的结构化 trace
    skill_status: str  # skill 执行状态，用于 graph 条件边判断
    recovery_plan: dict[str, Any]  # 失败后的结构化恢复计划
    answer: str  # 最终回答
    error: str  # 错误信息
    steps: list[str]  # 执行步骤记录（调试用）


def build_rag_graph(workspace_root: Path | str = "."):
    """Build a LangGraph workflow with simple conditional tool routing."""

    root = Path(workspace_root).resolve()  # 固定 graph 工作区根目录
    tools = {tool.name: tool for tool in build_langchain_tools(root)}

    def route(state: RAGGraphState) -> RAGGraphState:
        """Choose a route and tool input for the current question."""

        question = state["question"]
        lowered = question.lower()
        steps = [*state.get("steps", []), "route"]

        if _looks_like_file_read(question):
            path = _extract_file_path(question)
            return {
                **state,
                "route": "read_file",
                "route_reason": "The question asks to read a workspace file.",
                "selected_tool": "read_workspace_file",
                "tool_input": {"path": path},
                "steps": steps,
            }

        if _looks_like_skill_execution(lowered):
            return {
                **state,
                "route": "skill_execution",
                "route_reason": "The question asks the graph to execute a reusable skill.",
                "selected_tool": "execute_workspace_skill",
                "tool_input": {"question": question},
                "steps": steps,
            }

        if _looks_like_search_only(lowered):
            return {
                **state,
                "route": "search_docs",
                "route_reason": "The question asks to search local context rather than synthesize an answer.",
                "selected_tool": "search_workspace_docs",
                "tool_input": {"question": question},
                "steps": steps,
            }

        return {
            **state,
            "route": "answer_docs_with_llm",
            "route_reason": "The question asks for a grounded answer from local documents.",
            "selected_tool": "answer_workspace_docs_with_llm",
            "tool_input": {"question": question},
            "steps": steps,
        }

    def call_tool(state: RAGGraphState) -> RAGGraphState:
        """Invoke the selected LangChain tool and store the output."""

        steps = [*state.get("steps", []), "call_tool"]
        tool_name = state["selected_tool"]
        tool = tools[tool_name]
        try:
            output = tool.invoke(state["tool_input"])
            return {
                **state,
                "tool_output": output,
                "tool_status": "completed",
                "steps": steps,
            }
        except Exception as error:
            return {
                **state,
                "error": str(error),
                "tool_error": str(error),
                "tool_status": "failed",
                "steps": steps,
            }

    def call_skill(state: RAGGraphState) -> RAGGraphState:
        """Execute a project skill and keep its structured run inside graph state."""

        steps = [*state.get("steps", []), "call_skill"]
        try:
            result = run_skill_with_workspace(root, state["tool_input"]["question"])
            skill_run = (result.metadata or {}).get("skill_run")
            return {
                **state,
                "tool_output": result.output,
                "skill_run": skill_run,
                "skill_status": str(skill_run.get("status", "unknown")) if isinstance(skill_run, dict) else "unknown",
                "steps": steps,
            }
        except Exception as error:
            return {
                **state,
                "error": str(error),
                "skill_status": "failed",
                "recovery_plan": _build_exception_recovery_plan(state, error),
                "steps": steps,
            }

    def recover_skill_failure(state: RAGGraphState) -> RAGGraphState:
        """Build a deterministic recovery plan for a failed skill run."""

        steps = [*state.get("steps", []), "recover_skill_failure"]
        recovery_plan = _build_skill_recovery_plan(state)
        return {
            **state,
            "recovery_plan": recovery_plan,
            "tool_output": _format_recovery_plan(recovery_plan),
            "steps": steps,
        }

    def recover_tool_failure(state: RAGGraphState) -> RAGGraphState:
        """Build a deterministic recovery plan for a failed LangChain tool call."""

        steps = [*state.get("steps", []), "recover_tool_failure"]
        recovery_plan = _build_tool_recovery_plan(state)
        return {
            **state,
            "error": "",
            "recovery_plan": recovery_plan,
            "tool_output": _format_tool_recovery_plan(recovery_plan),
            "steps": steps,
        }

    def finalize(state: RAGGraphState) -> RAGGraphState:
        """Convert tool output or error into the final graph answer."""

        steps = [*state.get("steps", []), "finalize"]
        if state.get("error"):
            return {
                **state,
                "answer": f"Graph failed: {state['error']}",
                "steps": steps,
            }
        return {
            **state,
            "answer": state.get("tool_output", ""),
            "steps": steps,
        }

    graph = StateGraph(RAGGraphState)

    graph.add_node("route", route)
    graph.add_node("call_tool", call_tool)
    graph.add_node("recover_tool_failure", recover_tool_failure)
    graph.add_node("call_skill", call_skill)
    graph.add_node("recover_skill_failure", recover_skill_failure)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "route")
    graph.add_conditional_edges(
        "route",
        _next_after_route,
        {
            "call_tool": "call_tool",
            "call_skill": "call_skill",
            "finalize": "finalize",
        },
    )
    graph.add_conditional_edges(
        "call_tool",
        _next_after_tool,
        {
            "tool_completed": "finalize",
            "tool_failed": "recover_tool_failure",
        },
    )
    graph.add_edge("recover_tool_failure", "finalize")
    graph.add_conditional_edges(
        "call_skill",
        _next_after_skill,
        {
            "skill_completed": "finalize",
            "skill_failed": "recover_skill_failure",
        },
    )
    graph.add_edge("recover_skill_failure", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


def run_rag_graph(workspace_root: Path | str, question: str) -> RAGGraphState:
    """Run the minimal LangGraph RAG workflow."""

    graph = build_rag_graph(workspace_root)
    return graph.invoke({"question": question, "steps": []})


def _next_after_route(state: RAGGraphState) -> str:
    """Return the next node after routing."""

    if state.get("error"):
        return "finalize"
    if state.get("route") == "skill_execution":
        return "call_skill"
    return "call_tool"


def _next_after_tool(state: RAGGraphState) -> str:
    """Route after a normal tool call based on the structured tool status."""

    if state.get("tool_status") == "completed":
        return "tool_completed"
    return "tool_failed"


def _next_after_skill(state: RAGGraphState) -> str:
    """Route after skill execution based on the structured skill status."""

    if state.get("skill_status") == "completed":
        return "skill_completed"
    return "skill_failed"


def _looks_like_skill_execution(lowered_question: str) -> bool:
    """Return True when the graph should execute a reusable project skill."""

    keywords = [
        "execute skill",
        "run skill",
        "use skill",
        "perform skill",
        "skill execution",
    ]
    return any(keyword in lowered_question for keyword in keywords)


def _build_tool_recovery_plan(state: RAGGraphState) -> dict[str, Any]:
    """Create structured recovery data from a failed LangChain tool call."""

    tool_name = state.get("selected_tool", "unknown")
    tool_input = state.get("tool_input", {})
    reason = state.get("tool_error") or state.get("error") or "Tool execution failed."
    return {
        "status": "failed",
        "failure_type": _classify_tool_failure(reason),
        "tool_name": tool_name,
        "tool_input": tool_input,
        "reason": reason,
        "next_safe_action": _build_tool_next_safe_action(tool_name, tool_input, reason),
    }


def _classify_tool_failure(reason: str) -> str:
    """Classify common tool failures for recovery and eval readability."""

    lowered = reason.lower()
    if "does not exist" in lowered or "not found" in lowered:
        return "missing_resource"
    if "escapes workspace root" in lowered or "permission" in lowered:
        return "unsafe_or_denied_access"
    if "api key" in lowered or "network" in lowered or "connection" in lowered:
        return "external_dependency"
    if "too large" in lowered:
        return "input_too_large"
    return "tool_execution_error"


def _build_tool_next_safe_action(tool_name: str, tool_input: dict[str, str], reason: str) -> str:
    """Suggest a deterministic next action for a failed normal tool call."""

    failure_type = _classify_tool_failure(reason)
    if failure_type == "missing_resource":
        path = tool_input.get("path") or tool_input.get("question") or "the requested input"
        return f"Inspect whether {path} exists in the workspace, correct the input, then rerun {tool_name}."
    if failure_type == "unsafe_or_denied_access":
        return "Use a workspace-relative path that stays inside the project root, then rerun the graph."
    if failure_type == "external_dependency":
        return "Check the required API key or network dependency before rerunning the tool."
    if failure_type == "input_too_large":
        return "Use a smaller file or add a chunked reader before rerunning the tool."
    return f"Inspect the tool input and error message, then rerun {tool_name} with corrected arguments."


def _format_tool_recovery_plan(recovery_plan: dict[str, Any]) -> str:
    """Render a normal tool recovery plan as deterministic graph output."""

    return (
        "Tool recovery plan\n"
        f"Status: {recovery_plan.get('status')}\n"
        f"Failure type: {recovery_plan.get('failure_type')}\n"
        f"Tool: {recovery_plan.get('tool_name')}\n"
        f"Tool input: {recovery_plan.get('tool_input')}\n"
        f"Reason: {recovery_plan.get('reason')}\n"
        f"Next safe action: {recovery_plan.get('next_safe_action')}"
    )


def _build_skill_recovery_plan(state: RAGGraphState) -> dict[str, Any]:
    """Create structured recovery data from a failed skill run."""

    skill_run = state.get("skill_run")
    if not isinstance(skill_run, dict):
        return {
            "status": "failed",
            "skill_name": "unknown",
            "failed_step": None,
            "reason": state.get("error", "Skill execution failed without a structured run."),
            "completed_steps": 0,
            "next_safe_action": "Inspect the graph error and rerun the skill after fixing the execution context.",
        }

    failed_step = _find_failed_skill_step(skill_run)
    return {
        "status": "failed",
        "skill_name": _extract_skill_name(skill_run),
        "failed_step": failed_step,
        "reason": _extract_failure_reason(failed_step, state),
        "completed_steps": skill_run.get("completed_steps", 0),
        "next_safe_action": _build_next_safe_action(failed_step),
    }


def _build_exception_recovery_plan(state: RAGGraphState, error: Exception) -> dict[str, Any]:
    """Create recovery data when skill execution raises before returning SkillRun."""

    return {
        "status": "failed",
        "skill_name": "unknown",
        "failed_step": None,
        "reason": str(error),
        "completed_steps": 0,
        "next_safe_action": "Inspect the exception, fix the runtime context, and rerun the graph skill request.",
    }


def _find_failed_skill_step(skill_run: dict[str, Any]) -> dict[str, Any] | None:
    """Return the first failed step from a structured SkillRun trace."""

    steps = skill_run.get("steps", [])
    if not isinstance(steps, list):
        return None
    for step in steps:
        if isinstance(step, dict) and step.get("status") == "failed":
            return step
    return None


def _extract_skill_name(skill_run: dict[str, Any]) -> str:
    """Read the selected skill name from a SkillRun trace."""

    skill = skill_run.get("skill", {})
    if isinstance(skill, dict):
        name = skill.get("name")
        if isinstance(name, str):
            return name
    return "unknown"


def _extract_failure_reason(failed_step: dict[str, Any] | None, state: RAGGraphState) -> str:
    """Find the clearest available reason for a failed skill run."""

    if failed_step:
        error = failed_step.get("error")
        observation = failed_step.get("observation")
        if isinstance(error, str) and error:
            return error
        if isinstance(observation, str) and observation:
            return observation
    return state.get("error", "Skill execution failed.")


def _build_next_safe_action(failed_step: dict[str, Any] | None) -> str:
    """Suggest the next deterministic recovery action from the failed step."""

    if not failed_step:
        return "Inspect the skill trace and rerun after fixing the missing execution context."
    tool_name = failed_step.get("tool_name") or "the failed tool"
    tool_input = failed_step.get("tool_input") or "the requested input"
    return f"Inspect {tool_input} for {tool_name}, fix the missing resource or path, then rerun the skill."


def _format_recovery_plan(recovery_plan: dict[str, Any]) -> str:
    """Render a recovery plan as deterministic graph output."""

    failed_step = recovery_plan.get("failed_step")
    failed_step_text = "none"
    if isinstance(failed_step, dict):
        failed_step_text = (
            f"{failed_step.get('index')}. {failed_step.get('instruction')} "
            f"(tool={failed_step.get('tool_name')}, input={failed_step.get('tool_input')})"
        )

    return (
        "Skill recovery plan\n"
        f"Status: {recovery_plan.get('status')}\n"
        f"Skill: {recovery_plan.get('skill_name')}\n"
        f"Failed step: {failed_step_text}\n"
        f"Reason: {recovery_plan.get('reason')}\n"
        f"Completed steps: {recovery_plan.get('completed_steps')}\n"
        f"Next safe action: {recovery_plan.get('next_safe_action')}"
    )


def _looks_like_search_only(lowered_question: str) -> bool:
    """Return True when the graph should retrieve context without LLM synthesis."""

    keywords = [
        "find docs",
        "find local context",
        "search docs",
        "search local context",
        "show context",
        "show sources",
    ]
    return any(keyword in lowered_question for keyword in keywords)


def _looks_like_file_read(question: str) -> bool:
    """Return True when the graph should read a specific workspace file."""

    lowered = question.lower()
    return ("read" in lowered or "open" in lowered or "show" in lowered) and _extract_file_path(question) != "."


def _extract_file_path(question: str) -> str:
    """Extract the first simple workspace file path from a question."""

    import re

    match = re.search(r"((?:[\w.\-]+/)*[\w.\-]+\.(?:md|txt|py|json|toml|yaml|yml))", question)
    return match.group(1) if match else "."
