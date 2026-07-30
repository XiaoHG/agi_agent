"""Multi-step LLM tool loop records for the workspace agent."""

from __future__ import annotations

from dataclasses import dataclass, field

from .tool_calling import ToolCallSelection


@dataclass(frozen=True)
class ToolLoopStep:
    """One decision and observation inside a tool loop."""

    index: int                      # 当前 loop 轮次，从 1 开始
    selection: ToolCallSelection    # 本轮 LLM 选择结果
    observation: str = ""           # 工具执行后的观察结果摘要
    error: str | None = None        # 本轮错误信息

    def describe(self) -> str:
        """Render one loop step as a compact trace line."""

        tool_name = self.selection.tool_name or "none"
        tool_input = self.selection.tool_input or "none"
        status = f"error={self.error}" if self.error else "ok"
        return (
            f"step={self.index}; action={self.selection.action}; "
            f"tool={tool_name}; input={tool_input}; {status}"
        )


@dataclass(frozen=True)
class ToolLoopResult:
    """Final result produced by a bounded tool loop."""

    objective: str                              # 原始任务目标
    steps: list[ToolLoopStep] = field(default_factory=list)  # loop 内部步骤
    final_answer: str = ""                     # 面向用户的最终回答
    stop_reason: str = ""                      # loop 停止原因
    final_answer_source: str = "deterministic"  # 最终答案来源：llm 或 deterministic fallback

    def to_text(self) -> str:
        """Render the loop result for the user."""

        step_lines = [f"- {step.describe()}" for step in self.steps]
        if not step_lines:
            step_lines = ["- no loop step was executed"]
        return (
            f"Result: tool loop stopped by {self.stop_reason}.\n\n"
            f"Objective: {self.objective}\n\n"
            "Loop steps:\n"
            f"{chr(10).join(step_lines)}\n\n"
            f"Final answer source: {self.final_answer_source}\n\n"
            f"Final answer:\n{self.final_answer}"
        )
