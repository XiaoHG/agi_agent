"""Mutable execution state for the workspace agent."""

from __future__ import annotations

from dataclasses import dataclass, field

from .router import ToolRoute
from .tools import ToolResult


@dataclass(frozen=True)  # 轨迹步骤只记录，不应被后续逻辑回写
class AgentStep:
    """One recorded step in a run trace."""

    title: str  # 步骤标题
    detail: str  # 步骤详情


@dataclass
class AgentState:
    """Mutable state collected while the agent is running."""

    run_id: str  # 本次运行的短 ID
    user_input: str  # 用户原始输入
    route: ToolRoute  # 路由判断结果
    steps: list[AgentStep] = field(default_factory=list)  # 执行轨迹
    tool_results: list[ToolResult] = field(default_factory=list)  # 已执行的工具结果
    tool_error: str | None = None  # 工具失败原因
    workflow_summary: str = ""  # 工作流摘要
    answer: str = ""  # 最终答案

    def add_step(self, title: str, detail: str) -> None:
        """Append a visible step to the execution trace."""

        self.steps.append(AgentStep(title, detail))

    def add_tool_result(self, result: ToolResult) -> None:
        """Record a successful tool result in execution order."""

        self.tool_results.append(result)

    def last_tool_result(self, tool_name: str | None = None) -> ToolResult | None:
        """Return the last tool result, optionally filtered by tool name."""

        if not self.tool_results:
            return None
        if tool_name is None:
            return self.tool_results[-1]
        for result in reversed(self.tool_results):
            if result.tool_name == tool_name:
                return result
        return None

