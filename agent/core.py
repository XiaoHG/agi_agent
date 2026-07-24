"""Core orchestration for the workspace agent."""
from __future__ import annotations  # 支持类型注解的前向引用
from dataclasses import dataclass, field  # 数据类，简化数据结构定义{insert\_element\_0\_}
from pathlib import Path  # 路径处理，跨平台
from uuid import uuid4  # 生成唯一运行ID

# 内部模块依赖（需配套实现）
from .prompts import load_system_prompt, load_tool_router_prompt  # 加载提示词
from .router import ToolRoute, route_intent  # 意图路由（核心决策模块）
from .tools import ToolError, ToolResult, list_dir, read_file, count_lines  # 工具定义与异常


@dataclass(frozen=True)  # frozen=True：不可变，确保轨迹不可篡改
class AgentStep:
    """One recorded step in a run trace."""
    title: str    # 步骤标题（如"Receive input"）
    detail: str   # 步骤详情（如用户输入内容）


@dataclass
class AgentRun:
    """In-memory record of one agent execution."""
    run_id: str                  # 唯一会话ID（uuid4.hex[:8]生成）
    user_input: str              # 用户原始输入
    route: ToolRoute             # 路由决策结果（来自route_intent）
    steps: list[AgentStep] = field(default_factory=list)  # 执行步骤列表
    tool_result: ToolResult | None = None  # 工具执行结果（成功时）
    tool_error: str | None = None          # 工具执行错误（失败时）
    answer: str = ""                       # 最终返回给用户的答案


class WorkspaceAgent:
    """Minimal agent that can answer directly or call local tools."""

    def __init__(self, workspace_root: Path | str = ".") -> None:
        self.workspace_root = Path(workspace_root).resolve()  # 解析为绝对路径
        self.system_prompt = load_system_prompt()            # 加载系统提示词
        self.tool_router_prompt = load_tool_router_prompt()  # 加载工具路由提示词

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
        return run

    def _call_tool(self, route: ToolRoute) -> ToolResult:
        """Dispatch tool calls based on the router decision."""
        if route.tool_name == "read_file":
            return read_file(self.workspace_root, route.tool_input or ".")
        if route.tool_name == "list_dir":
            return list_dir(self.workspace_root, route.tool_input or ".")
        if route.tool_name == "count_lines":
            return count_lines(self.workspace_root, route.tool_input or ".")
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
        if run.tool_result.tool_name == "read_file":
            return (
                f"Result: read {run.route.tool_input}.\n\n"
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
        if run.tool_result is not None:
            parts.append("\n[Tool] " + run.tool_result.tool_name)
            parts.append(run.tool_result.output)
        if run.tool_error is not None:
            parts.append("\n[Tool Error]")
            parts.append(run.tool_error)
        # 追加最终答案
        parts.append("\n[Final Answer]")
        parts.append(run.answer)
        return "\n".join(parts)
