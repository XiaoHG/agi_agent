"""Core orchestration for the workspace agent."""
from __future__ import annotations  # 支持类型注解的前向引用
from dataclasses import dataclass, field  # 数据类，简化数据结构定义{insert\_element\_0\_}
from pathlib import Path  # 路径处理，跨平台
from typing import Any  # 结构化 trace 字典值类型
from uuid import uuid4  # 生成唯一运行ID

# 内部模块依赖（需配套实现）
from .prompts import (  # 加载提示词
    load_system_prompt,
    load_tool_calling_prompt,
    load_tool_loop_synthesis_prompt,
    load_tool_router_prompt,
)
from .events import build_runtime_events  # 统一运行事件导出
from .persistence import (
    RunCheckpointStore,
    build_run_checkpoint,
    format_checkpoint_history,
    format_checkpoint_summary,
)  # 运行记录持久化
from .router import ToolRoute, route_intent  # 意图路由（核心决策模块）
from .tool_calling import ToolCallSelection, select_tool_call  # 结构化工具调用选择
from .tool_loop import ToolLoopResult, ToolLoopStep  # 多步工具循环记录
from .tool_synthesis import synthesize_tool_loop_answer  # 工具循环最终综合
from .tool_schema import build_workspace_tool_specs  # 工具 schema 目录
from .tools import (  # 工具定义与异常
    ToolError,
    ToolResult,
    answer_docs_with_llm,
    count_lines,
    list_dir,
    list_mcp_server_tools,
    list_agent_skills,
    list_project_subagents,
    mcp_workspace_summary,
    mcp_read_project_file,
    plan_skill,
    plan_subagent_collaboration,
    read_file,
    run_skill_with_workspace,
    search_docs,
)
from .state import AgentState, AgentStep  # 运行状态与轨迹记录
from .workflow import WorkflowPlan, build_workflow_plan, build_workflow_summary  # 工作流规划与汇总


@dataclass
class AgentRun:
    """In-memory record of one agent execution."""
    run_id: str                  # 唯一会话ID（uuid4.hex[:8]生成）
    user_input: str              # 用户原始输入
    route: ToolRoute             # 路由决策结果（来自route_intent）
    tool_call: ToolCallSelection | None = None  # LLM 工具选择结果（仅 tool_call 分支使用）
    tool_loop_result: ToolLoopResult | None = None  # 多步工具循环结果
    steps: list[AgentStep] = field(default_factory=list)  # 执行步骤列表
    tool_result: ToolResult | None = None  # 工具执行结果（成功时）
    tool_error: str | None = None          # 工具执行错误（失败时）
    answer: str = ""                       # 最终返回给用户的答案


class WorkspaceAgent:
    """Minimal agent that can answer directly or call local tools."""

    def __init__(
        self,
        workspace_root: Path | str = ".",
        llm_client: Any | None = None,
        history_dir: Path | str | None = None,
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()  # 解析为绝对路径
        self.system_prompt = load_system_prompt()            # 加载系统提示词
        self.tool_router_prompt = load_tool_router_prompt()  # 加载工具路由提示词
        self.tool_calling_prompt = load_tool_calling_prompt()  # 加载结构化工具调用提示词
        self.tool_loop_synthesis_prompt = load_tool_loop_synthesis_prompt()  # 加载工具循环最终综合提示词
        self.tool_specs = build_workspace_tool_specs()  # 工具 schema 目录
        self._llm_client = llm_client  # 测试可注入 fake client；生产环境延迟创建真实 client
        checkpoint_root = history_dir if history_dir is not None else self.workspace_root / "logs" / "agent-runs"
        self._history_store = RunCheckpointStore(Path(checkpoint_root))  # 本地 checkpoint 存储

    def run(self, user_input: str) -> AgentRun:
        """Execute one turn and return a structured run record."""
        # 1. 初始化AgentRun会话
        run = AgentRun(
            run_id=uuid4().hex[:8],  # 生成8位短UUID作为会话ID
            user_input=user_input,
            route=route_intent(user_input),  # 【关键】路由决策：判断是否需要调用工具
            steps=[],
        )

        # 2. 记录初始步骤（构建执行轨迹）
        run.steps.append(AgentStep("Receive input", user_input))
        run.steps.append(AgentStep("Load prompts", "system prompt and tool-router prompt loaded"))
        run.steps.append(AgentStep("Route request", f"{run.route.action} / {run.route.tool_name or 'none'}"))

        # 3.5 如果是工作流请求，则进入多步执行路径
        if run.route.action == "workflow":
            workflow_plan = build_workflow_plan(user_input)
            run.steps.append(AgentStep("Build workflow", workflow_plan.describe()))
            workflow_state = AgentState(
                run_id=run.run_id,
                user_input=user_input,
                route=run.route,
                steps=run.steps,
            )
            run.answer = self._run_workflow(workflow_state, workflow_plan)
            run.steps = workflow_state.steps
            return self._persist_run(run)

        # 3.6 如果显式要求 LangGraph，则进入图编排路径
        if run.route.action == "graph":
            try:
                graph_state = self._run_langgraph(run.route.tool_input or user_input)
                run.steps.append(AgentStep("Run graph", self._describe_langgraph_state(graph_state)))
                run.tool_result = ToolResult(
                    "langgraph_workflow",
                    self._format_langgraph_answer(graph_state),
                    self._build_langgraph_metadata(graph_state),
                )
                run.answer = run.tool_result.output
            except ToolError as error:
                run.tool_error = str(error)
                run.steps.append(AgentStep("Graph failed", run.tool_error))
                run.answer = self._compose_tool_error_answer(run)
            run.steps.append(AgentStep("Complete", "final answer generated"))
            return self._persist_run(run)

        # 3.7 如果要求多步工具循环，则让模型在观察结果后继续决策
        if run.route.action == "tool_loop":
            try:
                loop_input = run.route.tool_input or user_input
                run.tool_loop_result = self._run_tool_loop(loop_input)
                run.tool_loop_result = self._synthesize_tool_loop_result(run.tool_loop_result)
                if run.tool_loop_result.steps:
                    run.tool_call = run.tool_loop_result.steps[-1].selection
                run.steps.append(AgentStep("Run tool loop", self._describe_tool_loop(run.tool_loop_result)))
                run.answer = run.tool_loop_result.to_text()
            except ToolError as error:
                run.tool_error = str(error)
                run.steps.append(AgentStep("Tool loop failed", run.tool_error))
                run.answer = self._compose_tool_error_answer(run)
            run.steps.append(AgentStep("Complete", "final answer generated"))
            return self._persist_run(run)

        # 3.7 如果要求模型参与工具选择，则进入结构化 tool calling 路径
        if run.route.action == "tool_call":
            try:
                tool_call_input = run.route.tool_input or user_input
                run.tool_call = self._select_tool_call(tool_call_input)
                run.steps.append(AgentStep("Select tool", self._describe_tool_call(run.tool_call)))
                if run.tool_call.action == "use_tool":
                    tool_route = ToolRoute(
                        action="use_tool",
                        tool_name=run.tool_call.tool_name,
                        tool_input=run.tool_call.tool_input,
                        reason=run.tool_call.reason,
                    )
                    run.tool_result = self._call_tool(tool_route)
                    run.steps.append(AgentStep("Run tool", f"{run.tool_result.tool_name} completed"))
                    run.answer = self._compose_tool_answer(run)
                elif run.tool_call.action == "answer_directly":
                    run.answer = self._compose_direct_answer(tool_call_input)
                    run.steps.append(AgentStep("Answer directly", "LLM selected direct answer"))
                else:
                    run.answer = (
                        "Result: the agent needs more information before acting.\n\n"
                        f"Reason: {run.tool_call.reason}\n\n"
                        "Next step: provide the missing details and try again."
                    )
                    run.steps.append(AgentStep("Ask clarification", run.tool_call.reason))
            except ToolError as error:
                run.tool_error = str(error)
                run.steps.append(AgentStep("Tool calling failed", run.tool_error))
                run.answer = self._compose_tool_error_answer(run)
            run.steps.append(AgentStep("Complete", "final answer generated"))
            return self._persist_run(run)

        # 3. 分支逻辑：根据路由结果执行不同策略
        if run.route.action == "use_tool":
            # 分支A：需要调用工具
            try:
                run.tool_result = self._call_tool(run.route)  # 调用具体工具
                run.steps.append(AgentStep("Run tool", f"{run.tool_result.tool_name} completed"))
                run.answer = self._compose_tool_answer(run)   # 生成工具结果的自然语言回答
            except ToolError as error:
                # 工具调用失败，记录错误并生成错误回答
                run.tool_error = str(error)
                run.steps.append(AgentStep("Tool failed", run.tool_error))
                run.answer = self._compose_tool_error_answer(run)
        else:
            # 分支B：无需调用工具，直接回答
            run.answer = self._compose_direct_answer(user_input)
            run.steps.append(AgentStep("Answer directly", "no tool was called"))

        # 4. 记录完成步骤并返回完整会话
        run.steps.append(AgentStep("Complete", "final answer generated"))
        return self._persist_run(run)

    def _run_workflow(self, state: AgentState, plan: WorkflowPlan) -> str:
        """Execute a simple multi-step workflow and build the final answer."""

        # 1. 记录工作流开始
        state.add_step("Start workflow", f"{plan.objective}")

        # 2. 逐步执行计划中的每个步骤
        for index, step in enumerate(plan.steps, start=1):
            state.add_step("Workflow step", f"{index}. {step.title} -> {step.kind}")

            if step.kind == "tool":
                try:
                    result = self._call_tool(
                        ToolRoute(
                            action="use_tool",
                            tool_name=step.tool_name,
                            tool_input=step.tool_input,
                            reason=step.note,
                        )
                    )
                    state.add_tool_result(result)
                    state.add_step("Step completed", f"{result.tool_name} completed")
                except ToolError as error:
                    state.tool_error = str(error)
                    state.add_step("Step failed", state.tool_error)
                    state.answer = self._compose_tool_error_answer_for_workflow(state)
                    return state.answer

            if step.kind == "synthesize":
                state.workflow_summary = "Synthesis step completed."

        # 3. 汇总所有步骤结果，生成最终答案
        state.answer = build_workflow_summary(state, plan)
        state.add_step("Complete workflow", "final answer generated")
        return state.answer

    def _run_langgraph(self, question: str) -> dict[str, Any]:
        """Run the LangGraph workflow and return its final state."""

        # 延迟导入，避免 integrations -> agent -> core 的循环导入
        from integrations.langgraph_workflow import run_rag_graph

        try:
            return dict(run_rag_graph(self.workspace_root, question, planner_client=self._llm_client))
        except Exception as error:
            raise ToolError(f"LangGraph workflow failed: {error}") from error

    def _select_tool_call(self, user_input: str) -> ToolCallSelection:
        """Ask the real LLM to choose a tool from the workspace tool catalog."""

        from .llm import DeepSeekLLMClient

        if self._llm_client is None:
            self._llm_client = DeepSeekLLMClient()
        try:
            return select_tool_call(
                self._llm_client,
                user_input,
                self.tool_specs,
                prompt=self.tool_calling_prompt,
            )
        except Exception as error:
            raise ToolError(f"Tool calling selection failed: {error}") from error

    def _synthesize_tool_loop_result(self, result: ToolLoopResult) -> ToolLoopResult:
        """Ask the LLM for a final answer and keep deterministic fallback on failure."""

        from .llm import DeepSeekLLMClient

        if self._llm_client is None:
            self._llm_client = DeepSeekLLMClient()
        try:
            final_answer = synthesize_tool_loop_answer(
                self._llm_client,
                result,
                prompt=self.tool_loop_synthesis_prompt,
            )
        except Exception as error:
            fallback = (
                f"{result.final_answer}\n\n"
                f"Final synthesis fallback reason: {error}"
            )
            return ToolLoopResult(
                objective=result.objective,
                steps=result.steps,
                final_answer=fallback,
                stop_reason=result.stop_reason,
                final_answer_source="deterministic_fallback",
            )

        return ToolLoopResult(
            objective=result.objective,
            steps=result.steps,
            final_answer=final_answer,
            stop_reason=result.stop_reason,
            final_answer_source="llm",
        )

    def _run_tool_loop(self, objective: str, max_steps: int = 3) -> ToolLoopResult:
        """Run a bounded LLM tool loop with observations between steps."""

        loop_steps: list[ToolLoopStep] = [] # 每一步的记录
        observations: list[str] = []        # 工具执行结果，给下一轮 LLM 看
        seen_tool_calls: set[tuple[str | None, str | None]] = set() # 防止重复调用同一个工具

        for index in range(1, max_steps + 1):
            loop_input = self._build_tool_loop_input(objective, observations)
            selection = self._select_tool_call(loop_input)

            if selection.action == "answer_directly":
                final_answer = self._compose_tool_loop_final_answer(objective, observations, selection.reason)
                loop_steps.append(ToolLoopStep(index=index, selection=selection, observation=selection.reason))
                return ToolLoopResult(
                    objective=objective,
                    steps=loop_steps,
                    final_answer=final_answer,
                    stop_reason="model_answered_directly",
                )

            if selection.action == "ask_clarification":
                loop_steps.append(ToolLoopStep(index=index, selection=selection, observation=selection.reason))
                return ToolLoopResult(
                    objective=objective,
                    steps=loop_steps,
                    final_answer=f"The agent needs more information: {selection.reason}",
                    stop_reason="needs_clarification",
                )

            tool_key = (selection.tool_name, selection.tool_input)
            if tool_key in seen_tool_calls:
                loop_steps.append(
                    ToolLoopStep(index=index, selection=selection, error="Repeated tool call detected.")
                )
                return ToolLoopResult(
                    objective=objective,
                    steps=loop_steps,
                    final_answer=self._compose_tool_loop_final_answer(
                        objective,
                        observations,
                        "Stopped because the model repeated the same tool call.",
                    ),
                    stop_reason="repeated_tool_call",
                )
            seen_tool_calls.add(tool_key)

            try:
                result = self._call_tool(
                    ToolRoute(
                        action="use_tool",
                        tool_name=selection.tool_name,
                        tool_input=selection.tool_input,
                        reason=selection.reason,
                    )
                )
            except ToolError as error:
                loop_steps.append(ToolLoopStep(index=index, selection=selection, error=str(error)))
                return ToolLoopResult(
                    objective=objective,
                    steps=loop_steps,
                    final_answer=f"The tool loop failed while running {selection.tool_name}: {error}",
                    stop_reason="tool_error",
                )

            observation = self._preview_observation(result.output)
            observations.append(f"{result.tool_name}: {observation}")
            loop_steps.append(ToolLoopStep(index=index, selection=selection, observation=observation))

        return ToolLoopResult(
            objective=objective,
            steps=loop_steps,
            final_answer=self._compose_tool_loop_final_answer(
                objective,
                observations,
                f"Reached the max step limit of {max_steps}.",
            ),
            stop_reason="max_steps",
        )

    def _build_tool_loop_input(self, objective: str, observations: list[str]) -> str:
        """Build the next LLM input for a tool loop iteration."""

        if not observations:
            return objective
        return (
            f"Objective:\n{objective}\n\n"
            "Previous observations:\n"
            f"{chr(10).join(f'- {item}' for item in observations)}\n\n"
            "Choose the next smallest sufficient action. "
            "If the observations are enough, choose answer_directly."
        )

    def _compose_tool_loop_final_answer(self, objective: str, observations: list[str], reason: str) -> str:
        """Build a deterministic final answer from tool loop observations."""

        observation_text = "\n".join(f"- {item}" for item in observations) if observations else "- no observations"
        return (
            f"Objective: {objective}\n\n"
            f"Reason: {reason}\n\n"
            "Observations:\n"
            f"{observation_text}"
        )

    def _describe_tool_loop(self, result: ToolLoopResult) -> str:
        """Render the tool loop result as a compact trace line."""

        return f"steps={len(result.steps)}; stop_reason={result.stop_reason}"

    def _preview_observation(self, text: str, limit: int = 280) -> str:
        """Create a compact one-line observation for the next loop step."""

        normalized = " ".join(text.split())
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 15] + "... (truncated)"

    def _describe_tool_call(self, tool_call: ToolCallSelection) -> str:
        """Render the selected tool call as a compact trace line."""

        tool_name = tool_call.tool_name or "none"
        tool_input = tool_call.tool_input or "none"
        return f"action={tool_call.action}; tool={tool_name}; input={tool_input}; reason={tool_call.reason}"

    def _describe_langgraph_state(self, graph_state: dict[str, Any]) -> str:
        """Build a compact trace line for the graph execution."""

        route = graph_state.get("route", "unknown")
        tool = graph_state.get("selected_tool", "none")
        planner = graph_state.get("planner_status", "unknown")
        steps = " -> ".join(graph_state.get("steps", []))
        return f"route={route}; selected_tool={tool}; planner={planner}; steps={steps}"

    def _format_langgraph_answer(self, graph_state: dict[str, Any]) -> str:
        """Convert LangGraph state into the same answer channel used by the agent."""

        steps = " -> ".join(graph_state.get("steps", []))
        answer = graph_state.get("answer", "")
        tool_status = graph_state.get("tool_status", "none")
        skill_status = graph_state.get("skill_status", "none")
        return (
            f"Graph route: {graph_state.get('route', 'unknown')}\n"
            f"Route reason: {graph_state.get('route_reason', '')}\n"
            f"Planner status: {graph_state.get('planner_status', 'unknown')}\n"
            f"Selected tool: {graph_state.get('selected_tool', 'none')}\n"
            f"Tool status: {tool_status}\n"
            f"Skill status: {skill_status}\n"
            f"Graph steps: {steps}\n\n"
            f"{answer}"
        )

    def _build_langgraph_metadata(self, graph_state: dict[str, Any]) -> dict[str, Any] | None:
        """Expose important graph state fields through the normal tool metadata channel."""

        metadata: dict[str, Any] = {
            "graph_route": graph_state.get("route"),
            "graph_steps": graph_state.get("steps", []),
            "planner_status": graph_state.get("planner_status"),
            "planner_error": graph_state.get("planner_error"),
        }
        if graph_state.get("tool_status") is not None:
            metadata["tool_status"] = graph_state.get("tool_status")
            metadata["tool_error"] = graph_state.get("tool_error")
        if graph_state.get("skill_run") is not None:
            metadata["skill_run"] = graph_state["skill_run"]
            metadata["skill_status"] = graph_state.get("skill_status")
        if graph_state.get("recovery_plan") is not None:
            metadata["recovery_plan"] = graph_state["recovery_plan"]
        return metadata

    def _persist_run(self, run: AgentRun) -> AgentRun:
        """Persist the structured run as a local checkpoint."""

        if self._history_store is None:
            return run
        trace = self.to_trace_dict(run)
        checkpoint = build_run_checkpoint(
            run_id=run.run_id,
            run_kind=run.route.action,
            user_input=run.user_input,
            route=trace["route"],
            steps=trace["steps"],
            answer=run.answer,
            trace=trace,
            trace_text=self.format_trace(run),
            tool_error=run.tool_error,
            tool_result=trace["tool_result"],
        )
        self._history_store.save(checkpoint)
        return run

    def load_latest_checkpoint(self) -> dict[str, Any] | None:
        """Load the most recent persisted checkpoint."""

        return self._history_store.load_latest() if self._history_store is not None else None

    def format_checkpoint_summary(self) -> str:
        """Render the latest checkpoint summary for CLI use."""

        checkpoint = self.load_latest_checkpoint()
        if checkpoint is None:
            return "No checkpoint found."
        return format_checkpoint_summary(checkpoint)

    def load_checkpoint(self, run_id: str) -> dict[str, Any] | None:
        """Load a checkpoint by its run id."""

        return self._history_store.load_run(run_id) if self._history_store is not None else None

    def list_checkpoint_history(self, limit: int = 10) -> str:
        """Render a compact list of recent checkpoints."""

        if self._history_store is None:
            return "No checkpoint found."
        return format_checkpoint_history(self._history_store.list_runs(limit=limit))

    def _compose_tool_error_answer_for_workflow(self, state: AgentState) -> str:
        """Convert a workflow failure into a user-facing answer."""

        return (
            "Result: the workflow failed before completion.\n\n"
            f"Reason: {state.tool_error}\n\n"
            "Next step: inspect the requested file or directory path and try again."
        )

    def _call_tool(self, route: ToolRoute) -> ToolResult:
        """Dispatch tool calls based on the router decision."""
        if route.tool_name == "read_file":
            return read_file(self.workspace_root, route.tool_input or ".")
        if route.tool_name == "list_dir":
            return list_dir(self.workspace_root, route.tool_input or ".")
        if route.tool_name == "count_lines":
            return count_lines(self.workspace_root, route.tool_input or ".")
        if route.tool_name == "search_docs":
            return search_docs(self.workspace_root, route.tool_input or "")
        if route.tool_name == "answer_docs_with_llm":
            return answer_docs_with_llm(self.workspace_root, route.tool_input or "")
        if route.tool_name == "list_mcp_tools":
            return list_mcp_server_tools(self.workspace_root)
        if route.tool_name == "mcp_workspace_summary":
            return mcp_workspace_summary(self.workspace_root)
        if route.tool_name == "mcp_read_project_file":
            return mcp_read_project_file(self.workspace_root, route.tool_input or "")
        if route.tool_name == "list_skills":
            return list_agent_skills()
        if route.tool_name == "plan_skill":
            return plan_skill(route.tool_input or "")
        if route.tool_name == "execute_skill":
            return run_skill_with_workspace(self.workspace_root, route.tool_input or "")
        if route.tool_name == "list_subagents":
            return list_project_subagents()
        if route.tool_name == "plan_subagents":
            return plan_subagent_collaboration(route.tool_input or "")
        # 未知工具，抛出异常
        raise ToolError(f"Unknown tool: {route.tool_name}")

    def _compose_tool_error_answer(self, run: AgentRun) -> str:
        """Convert a tool failure into a user-facing answer."""

        return (
            "Result: the tool call failed, so the task was not completed.\n\n"
            f"Reason: {run.tool_error}\n\n"
            "Next step: check whether the file or directory exists, or use another relative path inside the workspace."
        )

    def _compose_tool_answer(self, run: AgentRun) -> str:
        """Turn tool output into a concise answer."""
        assert run.tool_result is not None  # 断言：确保工具结果存在
        display_input = run.tool_call.tool_input if run.tool_call and run.tool_call.tool_input else run.route.tool_input
        if run.tool_result.tool_name == "read_file":
            return (
                f"Result: read {display_input}.\n\n"
                f"Key content:\n{self._summarize_text(run.tool_result.output)}"
            )
        if run.tool_result.tool_name == "list_dir":
            return (
                "Result: inspected the current directory structure.\n\n"
                f"Directory listing:\n{run.tool_result.output}\n\n"
                f"Responsibilities:\n{self._describe_known_project_dirs(run.tool_result.output)}"
            )
        return run.tool_result.output  # 默认返回原始工具输出

    def _compose_direct_answer(self, user_input: str) -> str:
        """Provide a structured direct answer for non-tool requests."""

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

    def _summarize_text(self, text: str, limit: int = 20) -> str:
        """Summarize read_file output while keeping the result deterministic."""
        lines = text.splitlines()
        # 优先提取"## Learning Goals"章节（适配项目文档场景）
        learning_goal_summary = self._extract_markdown_section(lines, "## Learning Goals")
        if learning_goal_summary:
            return "Project learning goals:\n" + learning_goal_summary
        # 若无特定章节，取前20行并截断
        head = lines[:limit]
        if len(lines) > limit:
            head.append("... (truncated)")
        return "\n".join(head)

    def _extract_markdown_section(self, lines: list[str], heading: str) -> str:
        """Extract a Markdown section until the next heading."""
        try:
            start = lines.index(heading)  # 找到章节标题行
        except ValueError:
            return ""  # 标题不存在，返回空
        collected: list[str] = []
        # 提取标题后内容，直到下一个二级标题（##）
        for line in lines[start + 1 :]:
            if line.startswith("## "):
                break
            if line.strip():  # 忽略空行
                collected.append(line)
        return "\n".join(collected).strip()

    def _describe_known_project_dirs(self, listing: str) -> str:
        """Explain the purpose of directories shown by list_dir."""
        # 预定义项目标准目录的含义
        descriptions: dict[str, str] = {
            "agent/": "Core agent loop experiments, including workflow, state, and tool calling.",
            "cli/": "Command-line entrypoints for running and debugging the agent locally.",
            "prompts/": "Versioned prompts for system behavior, tool routing, and agent roles.",
            "evals/": "Evaluation cases, expected behavior, and actual output records.",
            "tests/": "Automated tests for tools, routing, and agent behavior.",
            "docs/": "Learning plans, architecture notes, reviews, and progress state.",
            "examples/": "Reproducible sample inputs and outputs.",
            "mcp/": "MCP server/client and external tool protocol experiments.",
            "rag/": "Document loading, chunking, retrieval, and question-answering experiments.",
            "skills/": "Reusable task capability definitions.",
            "subagent/": "Teacher Agent, Coding Agent, and future multi-agent experiments.",
            "configs/": "Configuration templates for models, tools, logging, and permissions.",
            "scripts/": "Developer helper scripts and one-off automation.",
            "data/": "Local experimental data.",
            "logs/": "Local runtime logs.",
        }
        result = []
        # 遍历目录列表，匹配预定义描述
        for dirname, description in descriptions.items():
            if f"- {dirname}" in listing:
                result.append(f"- `{dirname}`: {description}")
        return "\n".join(result) if result else "- No known project directories were found in the listing."

    def format_trace(self, run: AgentRun) -> str:
        """Render the run as a human-readable execution trace."""
        parts: list[str] = [f"Run ID: {run.run_id}"]
        # 格式化每一步执行记录
        for index, step in enumerate(run.steps, start=1):
            parts.append(f"{index}. {step.title}: {step.detail}")
        # 追加工具结果/错误
        if run.tool_call is not None:
            parts.append("\n[Tool Call]")
            parts.append(
                f"action={run.tool_call.action}, tool={run.tool_call.tool_name or 'none'}, "
                f"input={run.tool_call.tool_input or 'none'}"
            )
        if run.tool_loop_result is not None:
            parts.append("\n[Tool Loop]")
            parts.append(run.tool_loop_result.to_text())
        if run.tool_result is not None:
            parts.append("\n[Tool] " + run.tool_result.tool_name)
            parts.append(run.tool_result.output)
        if run.tool_error is not None:
            parts.append("\n[Tool Error]")
            parts.append(run.tool_error)
        runtime_events = build_runtime_events(
            run.steps,
            None if run.tool_result is None else run.tool_result.metadata,
            run.tool_error,
        )
        if runtime_events:
            parts.append("\n[Runtime Events]")
            parts.extend(event.to_text() for event in runtime_events)
        # 追加最终答案
        parts.append("\n[Final Answer]")
        parts.append(run.answer)
        return "\n".join(parts)

    def to_trace_dict(self, run: AgentRun) -> dict[str, Any]:
        """Render the run as structured trace data."""

        tool_metadata = None if run.tool_result is None else run.tool_result.metadata
        runtime_events = build_runtime_events(run.steps, tool_metadata, run.tool_error)
        return {
            "run_id": run.run_id,
            "user_input": run.user_input,
            "route": {
                "action": run.route.action,
                "tool_name": run.route.tool_name,
                "tool_input": run.route.tool_input,
                "reason": run.route.reason,
            },
            "tool_call": None
            if run.tool_call is None
            else {
                "action": run.tool_call.action,
                "tool_name": run.tool_call.tool_name,
                "tool_input": run.tool_call.tool_input,
                "reason": run.tool_call.reason,
            },
            "tool_loop": None
            if run.tool_loop_result is None
            else {
                "stop_reason": run.tool_loop_result.stop_reason,
                "step_count": len(run.tool_loop_result.steps),
                "steps": [step.describe() for step in run.tool_loop_result.steps],
                "final_answer_source": run.tool_loop_result.final_answer_source,
            },
            "selected_tool_name": None if run.tool_call is None else run.tool_call.tool_name,
            "steps": [{"title": step.title, "detail": step.detail} for step in run.steps],
            "runtime_events": [event.to_dict() for event in runtime_events],
            "tool_result": None
            if run.tool_result is None
            else {
                "tool_name": run.tool_result.tool_name,
                "output_preview": self._summarize_text(run.tool_result.output, limit=6),
                "metadata": tool_metadata,
            },
            "skill_run": None
            if tool_metadata is None
            else tool_metadata.get("skill_run"),
            "tool_error": run.tool_error,
            "answer_preview": self._summarize_text(run.answer, limit=8),
        }
