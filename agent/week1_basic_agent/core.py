from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from .prompts import load_system_prompt, load_tool_router_prompt
from .router import ToolRoute, route_intent
from .tools import ToolError, ToolResult, list_dir, read_file


@dataclass(frozen=True)
class AgentStep:
    title: str
    detail: str


@dataclass
class AgentRun:
    run_id: str
    user_input: str
    route: ToolRoute
    steps: list[AgentStep] = field(default_factory=list)
    tool_result: ToolResult | None = None
    tool_error: str | None = None
    answer: str = ""


class Week1Agent:
    def __init__(self, workspace_root: Path | str = ".") -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.system_prompt = load_system_prompt()
        self.tool_router_prompt = load_tool_router_prompt()

    def run(self, user_input: str) -> AgentRun:
        run = AgentRun(
            run_id=uuid4().hex[:8],
            user_input=user_input,
            route=route_intent(user_input),
            steps=[],
        )
        run.steps.append(AgentStep("接收输入", user_input))
        run.steps.append(AgentStep("加载提示词", "system prompt / tool router prompt 已加载"))
        run.steps.append(AgentStep("路由判断", f"{run.route.action} / {run.route.tool_name or 'none'}"))

        if run.route.action == "use_tool":
            try:
                run.tool_result = self._call_tool(run.route)
                run.steps.append(AgentStep("工具执行", f"{run.tool_result.tool_name} 已完成"))
                run.answer = self._compose_tool_answer(run)
            except ToolError as error:
                run.tool_error = str(error)
                run.steps.append(AgentStep("工具失败", run.tool_error))
                run.answer = self._compose_tool_error_answer(run)
        else:
            run.answer = self._compose_direct_answer(user_input)
            run.steps.append(AgentStep("直接回答", "未调用工具"))

        run.steps.append(AgentStep("完成", "生成最终回答"))
        return run

    def _call_tool(self, route: ToolRoute) -> ToolResult:
        if route.tool_name == "read_file":
            return read_file(self.workspace_root, route.tool_input or ".")
        if route.tool_name == "list_dir":
            return list_dir(self.workspace_root, route.tool_input or ".")
        raise ToolError(f"未知工具：{route.tool_name}")

    def _compose_tool_error_answer(self, run: AgentRun) -> str:
        return (
            "结论：工具调用失败，任务没有完成。\n\n"
            f"失败原因：{run.tool_error}\n\n"
            "下一步：请检查文件或目录是否存在，或者换一个项目内的相对路径。"
        )

    def _compose_tool_answer(self, run: AgentRun) -> str:
        assert run.tool_result is not None
        title = "结论"
        if run.tool_result.tool_name == "read_file":
            return (
                f"{title}：我已经读取了 {run.route.tool_input}。\n\n"
                f"关键内容：\n{self._summarize_text(run.tool_result.output)}"
            )
        if run.tool_result.tool_name == "list_dir":
            return (
                f"{title}：我已经查看了当前目录结构。\n\n"
                f"目录概览：\n{run.tool_result.output}\n\n"
                f"核心职责：\n{self._describe_known_project_dirs(run.tool_result.output)}"
            )
        return run.tool_result.output

    def _compose_direct_answer(self, user_input: str) -> str:
        text = user_input.lower()
        if "agent" in text and ("聊天" in user_input or "chat" in text) and ("区别" in user_input or "difference" in text):
            return (
                "结论：Agent 和普通聊天机器人最大的区别，是 Agent 会围绕目标主动做决策，并且可以调用工具、维护状态、分步骤完成任务。\n\n"
                "原因：普通聊天机器人更像回答器，重点是生成文本；Agent 更像执行器，重点是把任务推进到结果。\n\n"
                "在本项目中怎么落地：Week 1 先做最小闭环，后续再加状态、RAG、MCP 和 Subagent。\n\n"
                "你下一步应该做什么：先运行本地 CLI Agent，再看一次它的 trace 输出。"
            )
        if "为什么" in user_input or "why" in text:
            return (
                "结论：先从工程边界回答为什么，而不是先堆框架。\n\n"
                "原因：Agent 项目最容易失败的地方不是模型本身，而是工具边界、状态流转和评估缺失。\n\n"
                "在本项目中怎么落地：先把最小 Agent loop 跑通，再逐步加 RAG、MCP、Skills 和 Subagent。\n\n"
                "你下一步应该做什么：把问题拆成概念、实现和验证三个层次。"
            )
        return (
            "结论：当前问题不需要本地工具，先做直接回答。\n\n"
            "原因：Week 1 的核心不是覆盖所有知识，而是让你理解 Agent 闭环。\n\n"
            "在本项目中怎么落地：当问题涉及项目文件、目录结构或具体文档时，再切换到工具调用。\n\n"
            "你下一步应该做什么：如果想看项目内容，直接要求读取 README 或列出目录。"
        )

    def _summarize_text(self, text: str, limit: int = 20) -> str:
        lines = text.splitlines()
        learning_goal_summary = self._extract_markdown_section(lines, "## 学习目标")
        if learning_goal_summary:
            return "项目学习目标包括：\n" + learning_goal_summary

        head = lines[:limit]
        if len(lines) > limit:
            head.append("...（已截断）")
        return "\n".join(head)

    def _extract_markdown_section(self, lines: list[str], heading: str) -> str:
        try:
            start = lines.index(heading)
        except ValueError:
            return ""
        collected: list[str] = []
        for line in lines[start + 1 :]:
            if line.startswith("## "):
                break
            if line.strip():
                collected.append(line)
        return "\n".join(collected).strip()

    def _describe_known_project_dirs(self, listing: str) -> str:
        descriptions: dict[str, str] = {
            "agent/": "Agent 主链路实验，包括最小 Agent、workflow、状态和工具调用。",
            "cli/": "命令行入口，用于本地运行和调试 Agent。",
            "prompts/": "system prompt、工具路由 prompt 和角色 prompt 的版本化存放位置。",
            "evals/": "评估用例、期望行为和实际输出记录。",
            "tests/": "自动化测试，用于验证工具、路由和 Agent 行为。",
            "docs/": "学习计划、架构说明、复盘和进度状态。",
            "examples/": "可复现的示例输入输出。",
            "mcp/": "MCP server/client 和外部工具协议实验。",
            "rag/": "文档加载、切分、检索和问答实验。",
            "skills/": "可复用任务能力封装。",
            "subagent/": "Teacher Agent、Coding Agent 和后续多 Agent 协作实验。",
            "configs/": "模型、工具、日志、权限等配置模板。",
            "scripts/": "开发辅助脚本和一次性脚本。",
            "data/": "本地实验数据。",
            "logs/": "本地运行日志。",
        }
        result = []
        for dirname, description in descriptions.items():
            if f"- {dirname}" in listing:
                result.append(f"- `{dirname}`：{description}")
        return "\n".join(result) if result else "- 当前目录未匹配到已知项目目录。"

    def format_trace(self, run: AgentRun) -> str:
        parts: list[str] = [f"Run ID: {run.run_id}"]
        for index, step in enumerate(run.steps, start=1):
            parts.append(f"{index}. {step.title}: {step.detail}")
        if run.tool_result is not None:
            parts.append("")
            parts.append(f"[Tool] {run.tool_result.tool_name}")
            parts.append(run.tool_result.output)
        if run.tool_error is not None:
            parts.append("")
            parts.append("[Tool Error]")
            parts.append(run.tool_error)
        parts.append("")
        parts.append("[Final Answer]")
        parts.append(run.answer)
        return "\n".join(parts)
