"""LangGraph workflows for the workspace agent project."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agent.llm import DeepSeekLLMClient
from agent.planner import plan_graph_route
from agent.prompts import load_langgraph_planner_prompt
from agent.recovery import (
    build_exception_recovery_plan,
    build_skill_recovery_plan,
    build_tool_recovery_plan,
)
from agent.tool_schema import build_workspace_tool_specs
from agent.tools import run_skill_with_workspace

from .langchain_tools import build_langchain_tools


class RAGGraphState(TypedDict, total=False):
    """State passed between LangGraph nodes for the RAG workflow."""

    question: str  # 用户问题
    route: str  # graph 路由结果
    route_reason: str  # 路由原因
    planner_status: str  # LLM planner 状态：llm_planned / deterministic_fallback
    planner_error: str  # planner 失败原因
    planner_raw_response: str  # planner 原始响应
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


def build_rag_graph(
    workspace_root: Path | str = ".",
    planner_client: DeepSeekLLMClient | None = None,
    planner_prompt: str | None = None,
):
    """Build a LangGraph workflow with simple conditional tool routing."""

    root = Path(workspace_root).resolve()  # 固定 graph 工作区根目录
    tools = {tool.name: tool for tool in build_langchain_tools(root)}
    tool_specs = build_workspace_tool_specs()
    resolved_planner_prompt = planner_prompt or load_langgraph_planner_prompt()

    def route(state: RAGGraphState) -> RAGGraphState:
        """Choose a route and tool input for the current question."""

        question = state["question"]
        lowered = question.lower()
        steps = [*state.get("steps", []), "route"]

        if planner_client is not None:
            try:
                plan = plan_graph_route(
                    planner_client,
                    question,
                    tool_specs,
                    prompt=resolved_planner_prompt,
                )
                return {
                    **state,
                    **plan.to_state_update(),
                    "steps": steps,
                }
            except Exception as error:
                state = {
                    **state,
                    "planner_status": "deterministic_fallback",
                    "planner_error": str(error),
                }

        if _looks_like_file_read(question):
            path = _extract_file_path(question)
            return {
                **state,
                "route": "read_file",
                "route_reason": "The question asks to read a workspace file.",
                "planner_status": state.get("planner_status", "deterministic_route"),
                "selected_tool": "read_workspace_file",
                "tool_input": {"path": path},
                "steps": steps,
            }

        if _looks_like_skill_execution(lowered):
            return {
                **state,
                "route": "skill_execution",
                "route_reason": "The question asks the graph to execute a reusable skill.",
                "planner_status": state.get("planner_status", "deterministic_route"),
                "selected_tool": "execute_workspace_skill",
                "tool_input": {"question": question},
                "steps": steps,
            }

        if _looks_like_search_only(lowered):
            return {
                **state,
                "route": "search_docs",
                "route_reason": "The question asks to search local context rather than synthesize an answer.",
                "planner_status": state.get("planner_status", "deterministic_route"),
                "selected_tool": "search_workspace_docs",
                "tool_input": {"question": question},
                "steps": steps,
            }

        return {
            **state,
            "route": "answer_docs_with_llm",
            "route_reason": "The question asks for a grounded answer from local documents.",
            "planner_status": state.get("planner_status", "deterministic_route"),
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
                "recovery_plan": build_exception_recovery_plan(str(error)).to_dict(),
                "steps": steps,
            }

    def recover_skill_failure(state: RAGGraphState) -> RAGGraphState:
        """Build a deterministic recovery plan for a failed skill run."""

        steps = [*state.get("steps", []), "recover_skill_failure"]
        recovery_plan = build_skill_recovery_plan(
            state.get("skill_run") if isinstance(state.get("skill_run"), dict) else None,
            state.get("error", ""),
        )
        return {
            **state,
            "recovery_plan": recovery_plan.to_dict(),
            "tool_output": recovery_plan.to_text(),
            "steps": steps,
        }

    def recover_tool_failure(state: RAGGraphState) -> RAGGraphState:
        """Build a deterministic recovery plan for a failed LangChain tool call."""

        steps = [*state.get("steps", []), "recover_tool_failure"]
        recovery_plan = build_tool_recovery_plan(
            state.get("selected_tool", "unknown"),
            state.get("tool_input", {}),
            state.get("tool_error") or state.get("error") or "Tool execution failed.",
        )
        return {
            **state,
            "error": "",
            "recovery_plan": recovery_plan.to_dict(),
            "tool_output": recovery_plan.to_text(),
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


def run_rag_graph(
    workspace_root: Path | str,
    question: str,
    planner_client: DeepSeekLLMClient | None = None,
) -> RAGGraphState:
    """Run the minimal LangGraph RAG workflow."""

    graph = build_rag_graph(workspace_root, planner_client=planner_client)
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
