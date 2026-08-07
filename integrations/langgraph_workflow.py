"""LangGraph workflows for the workspace agent project."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from agent.llm import DeepSeekLLMClient
from agent.planner import plan_graph_route
from agent.prompts import load_langgraph_planner_prompt, load_tool_calling_prompt
from agent.recovery import (
    build_exception_recovery_plan,
    build_skill_recovery_plan,
    build_tool_recovery_plan,
)
from agent.tool_schema import build_workspace_tool_specs
from agent.tool_calling import ToolCallSelection, select_tool_call
from agent.tools import (
    ToolResult,
    answer_docs_with_llm,
    count_lines,
    list_agent_skills,
    list_dir,
    list_mcp_server_tools,
    list_project_subagents,
    mcp_read_project_file,
    mcp_write_project_file,
    mcp_workspace_summary,
    plan_skill,
    plan_subagent_collaboration,
    read_file,
    run_skill_with_workspace,
    search_docs,
    search_vector_docs,
)
from agent.workflow import (
    WorkflowPlan,
    WorkflowStep,
    build_workflow_plan,
    build_workflow_summary_from_results,
)


class RAGGraphState(TypedDict, total=False):
    """State passed between LangGraph nodes for the RAG workflow."""

    question: str  # 用户问题
    route: str  # graph 路由结果
    route_reason: str  # 路由原因
    planner_status: str  # LLM planner 状态：llm_planned / deterministic_fallback
    planner_error: str  # planner 失败原因
    planner_raw_response: str  # planner 原始响应
    route_hint_action: str  # 外层 router action，用于默认 graph runtime
    route_hint_tool_name: str  # 外层 router tool name
    route_hint_tool_input: str  # 外层 router tool input
    selected_tool: str  # 选哪个工具
    tool_input: dict[str, str]  # 传给 LangChain tool 的输入
    tool_output: str  # 工具返回结果
    tool_metadata: dict[str, Any]  # 工具 metadata，供主 Agent trace 继续使用
    tool_status: str  # 普通工具执行状态，用于 graph 条件边判断
    tool_error: str  # 普通工具失败原因
    logical_tool_name: str  # graph 内部执行的逻辑工具名，对应 Agent tool 层
    skill_run: dict[str, Any]  # skill 执行的结构化 trace
    skill_status: str  # skill 执行状态，用于 graph 条件边判断
    recovery_plan: dict[str, Any]  # 失败后的结构化恢复计划
    tool_call_selection: dict[str, Any]  # tool calling 结构化选择结果
    tool_call_status: str  # tool calling 执行状态
    tool_call_error: str  # tool calling 失败原因
    workflow_plan: dict[str, Any]  # workflow plan 的 JSON-ready 数据
    workflow_results: list[dict[str, Any]]  # workflow 已执行 tool result 列表
    workflow_summary: str  # workflow 的综合说明
    workflow_current_step: int  # 当前 workflow step 下标
    workflow_status: str  # workflow 执行状态
    workflow_error: str  # workflow 失败原因
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
    tool_specs = build_workspace_tool_specs()
    resolved_planner_prompt = planner_prompt or load_langgraph_planner_prompt()
    tool_calling_prompt = load_tool_calling_prompt()
    tools = _build_graph_tool_registry(root)

    def route(state: RAGGraphState) -> RAGGraphState:
        """Choose a route and tool input for the current question."""

        question = state["question"]
        lowered = question.lower()
        steps = [*state.get("steps", []), "route"]

        route_hint = _build_route_hint_state(state)
        if route_hint is not None:
            return {
                **state,
                **route_hint,
                "steps": steps,
            }

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
                "logical_tool_name": "read_file",
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
                "logical_tool_name": "execute_skill",
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
                "logical_tool_name": "search_docs",
                "steps": steps,
            }

        return {
            **state,
            "route": "answer_docs_with_llm",
            "route_reason": "The question asks for a grounded answer from local documents.",
            "planner_status": state.get("planner_status", "deterministic_route"),
            "selected_tool": "answer_workspace_docs_with_llm",
            "tool_input": {"question": question},
            "logical_tool_name": "answer_docs_with_llm",
            "steps": steps,
        }

    def call_tool(state: RAGGraphState) -> RAGGraphState:
        """Invoke the selected LangChain tool and store the output."""

        steps = [*state.get("steps", []), "call_tool"]
        tool_name = state["selected_tool"]
        tool = tools[tool_name]
        try:
            result = tool(state["tool_input"])
            return {
                **state,
                "tool_output": result.output,
                "tool_metadata": result.metadata or {},
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
                "tool_metadata": result.metadata or {},
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

    def build_workflow(state: RAGGraphState) -> RAGGraphState:
        """Build a workflow plan inside graph state for multi-step execution."""

        steps = [*state.get("steps", []), "build_workflow"]
        workflow_plan = build_workflow_plan(state["question"])
        return {
            **state,
            "workflow_plan": workflow_plan.to_dict(),
            "workflow_results": [],
            "workflow_summary": "",
            "workflow_current_step": 0,
            "workflow_status": "planned",
            "steps": steps,
        }

    def select_tool_call_in_graph(state: RAGGraphState) -> RAGGraphState:
        """Run structured tool calling inside graph state."""

        steps = [*state.get("steps", []), "select_tool_call"]
        client = planner_client or DeepSeekLLMClient()
        question = state.get("route_hint_tool_input") or state["question"]
        try:
            selection = select_tool_call(
                client,
                question,
                tool_specs,
                prompt=tool_calling_prompt,
            )
        except Exception as error:
            recovery_plan = build_exception_recovery_plan(str(error))
            answer = (
                "Result: the tool call failed, so the task was not completed.\n\n"
                f"Reason: {error}\n\n"
                "Next step: retry the request with a clearer tool target or inspect the tool-calling prompt/output."
            )
            return {
                **state,
                "selected_tool": "llm_tool_selector",
                "logical_tool_name": "llm_tool_selector",
                "tool_call_status": "failed",
                "tool_call_error": str(error),
                "recovery_plan": recovery_plan.to_dict(),
                "answer": answer,
                "steps": steps,
            }

        if selection.action == "answer_directly":
            return {
                **state,
                "route_reason": "The tool-calling model decided to answer directly without a local tool.",
                "selected_tool": "none",
                "logical_tool_name": "llm_tool_selector",
                "tool_call_selection": _tool_call_selection_to_dict(selection),
                "tool_call_status": "answer_directly",
                "answer": _compose_direct_answer(question),
                "steps": steps,
            }

        if selection.action == "ask_clarification":
            return {
                **state,
                "route_reason": "The tool-calling model needs more user detail before selecting a tool.",
                "selected_tool": "none",
                "logical_tool_name": "llm_tool_selector",
                "tool_call_selection": _tool_call_selection_to_dict(selection),
                "tool_call_status": "needs_clarification",
                "answer": (
                    "Result: the agent needs more information before acting.\n\n"
                    f"Reason: {selection.reason}\n\n"
                    "Next step: provide the missing details and try again."
                ),
                "steps": steps,
            }

        logical_tool_name = selection.tool_name or "unknown"
        mapped_tool_name = _map_agent_tool_to_graph_tool(logical_tool_name)
        payload = _build_tool_payload_from_selection(selection)
        next_status = "call_skill" if logical_tool_name == "execute_skill" else "ready_to_execute"
        return {
            **state,
            "route_reason": f"The tool-calling model selected tool '{logical_tool_name}'.",
            "selected_tool": mapped_tool_name,
            "logical_tool_name": logical_tool_name,
            "tool_input": payload,
            "tool_call_selection": _tool_call_selection_to_dict(selection),
            "tool_call_status": next_status,
            "steps": steps,
        }

    def run_workflow_step(state: RAGGraphState) -> RAGGraphState:
        """Execute one workflow step and keep progress in graph state."""

        steps = [*state.get("steps", []), "run_workflow_step"]
        plan = _workflow_plan_from_state(state)
        index = int(state.get("workflow_current_step", 0))
        if index >= len(plan.steps):
            return {
                **state,
                "workflow_status": "completed",
                "steps": steps,
            }

        step = plan.steps[index]
        workflow_results = [*state.get("workflow_results", [])]
        if step.kind == "synthesize":
            return {
                **state,
                "workflow_summary": "Synthesis step completed.",
                "workflow_current_step": index + 1,
                "workflow_status": "running",
                "steps": steps,
            }

        if step.tool_name is None:
            return {
                **state,
                "workflow_status": "failed",
                "workflow_error": f"Workflow step is missing a tool name: {step.title}",
                "steps": steps,
            }

        selected_tool = _map_agent_tool_to_graph_tool(step.tool_name)
        tool = tools[selected_tool]
        try:
            result = tool(_build_workflow_payload(step))
            workflow_results.append(_tool_result_to_dict(result))
            return {
                **state,
                "selected_tool": selected_tool,
                "logical_tool_name": step.tool_name,
                "tool_input": _build_workflow_payload(step),
                "tool_output": result.output,
                "tool_metadata": result.metadata or {},
                "tool_status": "completed",
                "workflow_results": workflow_results,
                "workflow_current_step": index + 1,
                "workflow_status": "running",
                "steps": steps,
            }
        except Exception as error:
            recovery_plan = build_tool_recovery_plan(
                selected_tool,
                _build_workflow_payload(step),
                str(error),
            )
            return {
                **state,
                "selected_tool": selected_tool,
                "logical_tool_name": step.tool_name,
                "tool_input": _build_workflow_payload(step),
                "tool_status": "failed",
                "tool_error": str(error),
                "workflow_status": "failed",
                "workflow_error": str(error),
                "recovery_plan": recovery_plan.to_dict(),
                "steps": steps,
            }

    def finalize_workflow(state: RAGGraphState) -> RAGGraphState:
        """Summarize workflow execution back into the standard answer channel."""

        steps = [*state.get("steps", []), "finalize_workflow"]
        plan = _workflow_plan_from_state(state)
        if state.get("workflow_status") == "failed":
            reason = state.get("workflow_error") or state.get("tool_error") or "Workflow execution failed."
            return {
                **state,
                "tool_output": (
                    "Result: the workflow failed before completion.\n\n"
                    f"Reason: {reason}\n\n"
                    "Next step: inspect the requested file or directory path and try again."
                ),
                "answer": (
                    "Result: the workflow failed before completion.\n\n"
                    f"Reason: {reason}\n\n"
                    "Next step: inspect the requested file or directory path and try again."
                ),
                "steps": steps,
            }

        tool_results = [_tool_result_from_dict(item) for item in state.get("workflow_results", [])]
        answer = build_workflow_summary_from_results(
            plan,
            tool_results,
            state.get("workflow_summary", ""),
        )
        return {
            **state,
            "workflow_status": "completed",
            "tool_output": answer,
            "answer": answer,
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
        if state.get("answer"):
            return {
                **state,
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
    graph.add_node("select_tool_call", select_tool_call_in_graph)
    graph.add_node("build_workflow", build_workflow)
    graph.add_node("run_workflow_step", run_workflow_step)
    graph.add_node("finalize_workflow", finalize_workflow)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "route")
    graph.add_conditional_edges(
        "route",
        _next_after_route,
        {
            "call_tool": "call_tool",
            "call_skill": "call_skill",
            "select_tool_call": "select_tool_call",
            "build_workflow": "build_workflow",
            "finalize": "finalize",
        },
    )
    graph.add_conditional_edges(
        "select_tool_call",
        _next_after_tool_call_selection,
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
    graph.add_edge("build_workflow", "run_workflow_step")
    graph.add_conditional_edges(
        "run_workflow_step",
        _next_after_workflow_step,
        {
            "run_next_workflow_step": "run_workflow_step",
            "workflow_finalize": "finalize_workflow",
        },
    )
    graph.add_edge("finalize_workflow", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


def run_rag_graph(
    workspace_root: Path | str,
    question: str,
    planner_client: DeepSeekLLMClient | None = None,
    route_hint_action: str | None = None,
    route_hint_tool_name: str | None = None,
    route_hint_tool_input: str | None = None,
) -> RAGGraphState:
    """Run the minimal LangGraph RAG workflow."""

    graph = build_rag_graph(workspace_root, planner_client=planner_client)
    return graph.invoke(
        {
            "question": question,
            "steps": [],
            "route_hint_action": route_hint_action,
            "route_hint_tool_name": route_hint_tool_name,
            "route_hint_tool_input": route_hint_tool_input,
        }
    )


def _next_after_route(state: RAGGraphState) -> str:
    """Return the next node after routing."""

    if state.get("error"):
        return "finalize"
    if state.get("route") == "direct_answer":
        return "finalize"
    if state.get("route") == "skill_execution":
        return "call_skill"
    if state.get("route") == "tool_call_execution":
        return "select_tool_call"
    if state.get("route") == "workflow_execution":
        return "build_workflow"
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


def _next_after_workflow_step(state: RAGGraphState) -> str:
    """Continue workflow execution until every step has been processed."""

    if state.get("workflow_status") == "failed":
        return "workflow_finalize"
    plan = _workflow_plan_from_state(state)
    if int(state.get("workflow_current_step", 0)) < len(plan.steps):
        return "run_next_workflow_step"
    return "workflow_finalize"


def _next_after_tool_call_selection(state: RAGGraphState) -> str:
    """Route after tool-call selection based on the structured selection status."""

    status = state.get("tool_call_status")
    if status == "ready_to_execute":
        return "call_tool"
    if status == "call_skill":
        return "call_skill"
    return "finalize"


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


def _build_graph_tool_registry(root: Path) -> dict[str, Any]:
    """Build the tool registry used by the graph runtime."""

    return {
        "read_workspace_file": lambda payload: read_file(root, payload.get("path", ".")),
        "list_workspace_directory": lambda payload: list_dir(root, payload.get("path", ".")),
        "count_workspace_file_lines": lambda payload: count_lines(root, payload.get("path", ".")),
        "search_workspace_docs": lambda payload: search_docs(root, payload.get("question", "")),
        "search_workspace_vector_docs": lambda payload: search_vector_docs(root, payload.get("question", "")),
        "answer_workspace_docs_with_llm": lambda payload: answer_docs_with_llm(root, payload.get("question", "")),
        "list_workspace_mcp_tools": lambda payload: list_mcp_server_tools(root),
        "summarize_workspace_with_mcp": lambda payload: mcp_workspace_summary(root),
        "read_workspace_file_through_mcp": lambda payload: mcp_read_project_file(root, payload.get("path", "")),
        "write_workspace_file_through_mcp": lambda payload: mcp_write_project_file(root, payload.get("task", "")),
        "list_workspace_skills": lambda payload: list_agent_skills(root),
        "plan_workspace_skill": lambda payload: plan_skill(root, payload.get("question", "")),
        "list_workspace_subagents": lambda payload: list_project_subagents(),
        "plan_workspace_subagents": lambda payload: plan_subagent_collaboration(payload.get("question", "")),
    }


def _build_route_hint_state(state: RAGGraphState) -> dict[str, Any] | None:
    """Translate the outer router decision into a graph route."""

    action = state.get("route_hint_action")
    tool_name = state.get("route_hint_tool_name")
    tool_input = state.get("route_hint_tool_input") or state.get("question", "")

    if action == "direct_answer":
        return {
            "route": "direct_answer",
            "route_reason": "The outer router determined that no local tool is required.",
            "planner_status": "router_wrapped",
            "selected_tool": "none",
            "logical_tool_name": "direct_answer",
            "answer": _compose_direct_answer(tool_input),
        }

    if action == "workflow":
        return {
            "route": "workflow_execution",
            "route_reason": "The outer router determined that this request needs ordered multi-step execution.",
            "planner_status": "router_wrapped",
            "selected_tool": "workflow_plan",
            "logical_tool_name": "workflow",
        }

    if action == "tool_call":
        return {
            "route": "tool_call_execution",
            "route_reason": "The outer router determined that the LLM should choose the smallest sufficient tool action.",
            "planner_status": "router_wrapped",
            "selected_tool": "llm_tool_selector",
            "logical_tool_name": "llm_tool_selector",
        }

    if action != "use_tool" or not tool_name:
        return None

    mapping: dict[str, dict[str, Any]] = {
        "read_file": {"route": "read_file", "selected_tool": "read_workspace_file", "tool_input": {"path": tool_input}},
        "list_dir": {"route": "list_dir", "selected_tool": "list_workspace_directory", "tool_input": {"path": tool_input or "."}},
        "count_lines": {"route": "count_lines", "selected_tool": "count_workspace_file_lines", "tool_input": {"path": tool_input}},
        "search_docs": {"route": "search_docs", "selected_tool": "search_workspace_docs", "tool_input": {"question": tool_input}},
        "search_vector_docs": {
            "route": "search_vector_docs",
            "selected_tool": "search_workspace_vector_docs",
            "tool_input": {"question": tool_input},
        },
        "answer_docs_with_llm": {
            "route": "answer_docs_with_llm",
            "selected_tool": "answer_workspace_docs_with_llm",
            "tool_input": {"question": tool_input},
        },
        "list_mcp_tools": {"route": "list_mcp_tools", "selected_tool": "list_workspace_mcp_tools", "tool_input": {}},
        "mcp_workspace_summary": {
            "route": "mcp_workspace_summary",
            "selected_tool": "summarize_workspace_with_mcp",
            "tool_input": {},
        },
        "mcp_read_project_file": {
            "route": "mcp_read_project_file",
            "selected_tool": "read_workspace_file_through_mcp",
            "tool_input": {"path": tool_input},
        },
        "mcp_write_project_file": {
            "route": "mcp_write_project_file",
            "selected_tool": "write_workspace_file_through_mcp",
            "tool_input": {"task": tool_input},
        },
        "list_skills": {"route": "list_skills", "selected_tool": "list_workspace_skills", "tool_input": {}},
        "plan_skill": {"route": "plan_skill", "selected_tool": "plan_workspace_skill", "tool_input": {"question": tool_input}},
        "list_subagents": {"route": "list_subagents", "selected_tool": "list_workspace_subagents", "tool_input": {}},
        "plan_subagents": {
            "route": "plan_subagents",
            "selected_tool": "plan_workspace_subagents",
            "tool_input": {"question": tool_input},
        },
    }

    if tool_name == "execute_skill":
        return {
            "route": "skill_execution",
            "route_reason": "The outer router selected reusable skill execution.",
            "planner_status": "router_wrapped",
            "selected_tool": "execute_workspace_skill",
            "tool_input": {"question": tool_input},
            "logical_tool_name": "execute_skill",
        }

    mapped = mapping.get(tool_name)
    if mapped is None:
        return None
    return {
        **mapped,
        "route_reason": f"The outer router selected tool '{tool_name}'.",
        "planner_status": "router_wrapped",
        "logical_tool_name": tool_name,
    }


def _compose_direct_answer(user_input: str) -> str:
    """Provide the same deterministic direct answer used by the classic runtime."""

    text = user_input.lower()
    if "agent" in text and ("chat" in text or "chatbot" in text) and ("difference" in text or "different" in text):
        return (
            "Result: the main difference is that an agent makes task-oriented decisions, can call tools, can keep state, "
            "and can complete work through multiple steps.\n\n"
            "Reason: a chatbot is mostly a text responder, while an agent is closer to an execution loop that moves a task toward completion.\n\n"
            "In this project: start with the minimal loop, then add state, RAG, MCP, skills, and subagents.\n\n"
            "Next step: run the CLI with trace enabled and inspect each recorded step."
        )
    if "why" in text:
        return (
            "Result: start from engineering boundaries before adding frameworks.\n\n"
            "Reason: agent systems usually fail around tool boundaries, state transitions, and missing evaluation, not only around model quality.\n\n"
            "In this project: first make the minimal loop work, then add RAG, MCP, skills, and subagents incrementally.\n\n"
            "Next step: split the question into concept, implementation, and verification layers."
        )
    return (
        "Result: this request does not require a local tool, so the agent answered directly.\n\n"
        "Reason: the current version focuses on the minimal agent loop rather than broad knowledge coverage.\n\n"
        "In this project: use tool calls when the request involves project files, directory structure, or specific documents.\n\n"
        "Next step: ask the agent to read README.md or list the project directory if you want it to inspect local content."
    )


def _map_agent_tool_to_graph_tool(tool_name: str) -> str:
    """Map the agent tool name used by workflow planning to the graph tool registry."""

    mapping = {
        "read_file": "read_workspace_file",
        "list_dir": "list_workspace_directory",
        "count_lines": "count_workspace_file_lines",
        "search_docs": "search_workspace_docs",
        "search_vector_docs": "search_workspace_vector_docs",
        "answer_docs_with_llm": "answer_workspace_docs_with_llm",
        "list_mcp_tools": "list_workspace_mcp_tools",
        "mcp_workspace_summary": "summarize_workspace_with_mcp",
        "mcp_read_project_file": "read_workspace_file_through_mcp",
        "mcp_write_project_file": "write_workspace_file_through_mcp",
        "list_skills": "list_workspace_skills",
        "plan_skill": "plan_workspace_skill",
        "list_subagents": "list_workspace_subagents",
        "plan_subagents": "plan_workspace_subagents",
        "execute_skill": "execute_workspace_skill",
    }
    return mapping.get(tool_name, tool_name)


def _build_tool_payload_from_selection(selection: ToolCallSelection) -> dict[str, str]:
    """Translate a structured tool-call selection into graph tool payload."""

    tool_input = selection.tool_input or ""
    if selection.tool_name in {"read_file", "count_lines", "mcp_read_project_file"}:
        return {"path": tool_input or "."}
    if selection.tool_name == "list_dir":
        return {"path": tool_input or "."}
    if selection.tool_name in {"list_mcp_tools", "mcp_workspace_summary", "list_skills", "list_subagents"}:
        return {}
    if selection.tool_name == "mcp_write_project_file":
        return {"task": tool_input}
    return {"question": tool_input}


def _tool_call_selection_to_dict(selection: ToolCallSelection) -> dict[str, Any]:
    """Convert ToolCallSelection into JSON-ready graph state."""

    return {
        "action": selection.action,
        "tool_name": selection.tool_name,
        "tool_input": selection.tool_input,
        "reason": selection.reason,
        "raw_response": selection.raw_response,
    }


def _build_workflow_payload(step: WorkflowStep) -> dict[str, str]:
    """Translate a workflow step into the graph tool payload shape."""

    if step.tool_name in {"read_file", "list_dir", "count_lines", "mcp_read_project_file"}:
        return {"path": step.tool_input or "."}
    if step.tool_name == "mcp_write_project_file":
        return {"task": step.tool_input or ""}
    return {"question": step.tool_input or ""}


def _tool_result_to_dict(result: ToolResult) -> dict[str, Any]:
    """Convert ToolResult into JSON-ready workflow state."""

    return {
        "tool_name": result.tool_name,
        "output": result.output,
        "metadata": result.metadata or {},
    }


def _tool_result_from_dict(data: dict[str, Any]) -> ToolResult:
    """Restore ToolResult from JSON-ready workflow state."""

    return ToolResult(
        str(data.get("tool_name", "unknown")),
        str(data.get("output", "")),
        data.get("metadata") if isinstance(data.get("metadata"), dict) else None,
    )


def _workflow_plan_from_state(state: RAGGraphState) -> WorkflowPlan:
    """Restore WorkflowPlan from graph state."""

    raw_plan = state.get("workflow_plan")
    if not isinstance(raw_plan, dict):
        return WorkflowPlan(objective=state.get("question", ""), steps=[])
    raw_steps = raw_plan.get("steps")
    steps: list[WorkflowStep] = []
    if isinstance(raw_steps, list):
        for item in raw_steps:
            if not isinstance(item, dict):
                continue
            steps.append(
                WorkflowStep(
                    title=str(item.get("title", "")),
                    kind=str(item.get("kind", "")),
                    tool_name=str(item["tool_name"]) if item.get("tool_name") is not None else None,
                    tool_input=str(item["tool_input"]) if item.get("tool_input") is not None else None,
                    note=str(item.get("note", "")),
                )
            )
    return WorkflowPlan(objective=str(raw_plan.get("objective", state.get("question", ""))), steps=steps)
