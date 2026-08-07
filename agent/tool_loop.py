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

    def to_dict(self) -> dict[str, object]:
        """Convert one loop step into JSON-ready data."""

        return {
            "index": self.index,
            "selection": {
                "action": self.selection.action,
                "tool_name": self.selection.tool_name,
                "tool_input": self.selection.tool_input,
                "reason": self.selection.reason,
                "raw_response": self.selection.raw_response,
            },
            "observation": self.observation,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ToolLoopStep":
        """Restore one loop step from JSON-ready data."""

        selection_data = data.get("selection")
        selection = ToolCallSelection(
            action=str(selection_data.get("action", "")) if isinstance(selection_data, dict) else "",
            tool_name=str(selection_data["tool_name"]) if isinstance(selection_data, dict) and selection_data.get("tool_name") is not None else None,
            tool_input=str(selection_data["tool_input"]) if isinstance(selection_data, dict) and selection_data.get("tool_input") is not None else None,
            reason=str(selection_data.get("reason", "")) if isinstance(selection_data, dict) else "",
            raw_response=str(selection_data.get("raw_response", "")) if isinstance(selection_data, dict) else "",
        )
        return cls(
            index=int(data.get("index", 0)),
            selection=selection,
            observation=str(data.get("observation", "")),
            error=str(data["error"]) if data.get("error") is not None else None,
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

    def to_dict(self) -> dict[str, object]:
        """Convert the loop result into JSON-ready data."""

        return {
            "objective": self.objective,
            "steps": [step.to_dict() for step in self.steps],
            "final_answer": self.final_answer,
            "stop_reason": self.stop_reason,
            "final_answer_source": self.final_answer_source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ToolLoopResult":
        """Restore the loop result from JSON-ready data."""

        raw_steps = data.get("steps")
        steps = [
            ToolLoopStep.from_dict(step)
            for step in raw_steps
            if isinstance(raw_steps, list) and isinstance(step, dict)
        ]
        return cls(
            objective=str(data.get("objective", "")),
            steps=steps,
            final_answer=str(data.get("final_answer", "")),
            stop_reason=str(data.get("stop_reason", "")),
            final_answer_source=str(data.get("final_answer_source", "deterministic")),
        )
