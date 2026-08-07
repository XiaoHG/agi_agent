"""Runtime event models for structured agent observability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RuntimeEvent:
    """One normalized event emitted during an Agent run."""

    index: int  # 事件序号，从 1 开始，保持稳定排序
    event_type: str  # 事件类型，例如 step / tool_result / error / recovery
    name: str  # 事件名称
    detail: str = ""  # 人类可读详情
    payload: dict[str, Any] = field(default_factory=dict)  # JSON-ready 结构化数据

    def to_dict(self) -> dict[str, Any]:
        """Render the event as JSON-ready trace data."""

        return {
            "index": self.index,
            "event_type": self.event_type,
            "name": self.name,
            "detail": self.detail,
            "payload": self.payload,
        }

    def to_text(self) -> str:
        """Render the event as a compact human-readable trace line."""

        payload_text = f" payload={self.payload}" if self.payload else ""
        return f"{self.index}. [{self.event_type}] {self.name}: {self.detail}{payload_text}"


def build_runtime_events(
    steps: list[Any],
    tool_result_metadata: dict[str, Any] | None = None,
    tool_error: str | None = None,
) -> list[RuntimeEvent]:
    """Build normalized runtime events from existing trace data."""

    events: list[RuntimeEvent] = []
    for step in steps:
        if isinstance(step, dict):
            step_name = str(step.get("title", step.get("name", "unknown")))
            step_detail = str(step.get("detail", step.get("description", "")))
        else:
            step_name = getattr(step, "title", getattr(step, "name", "unknown"))
            step_detail = getattr(step, "detail", getattr(step, "description", ""))
        events.append(
            RuntimeEvent(
                index=len(events) + 1,
                event_type="step",
                name=step_name,
                detail=step_detail,
            )
        )

    if tool_result_metadata:
        graph_route = tool_result_metadata.get("graph_route")
        if graph_route is not None:
            events.append(
                RuntimeEvent(
                    index=len(events) + 1,
                    event_type="graph",
                    name="graph_state",
                    detail=f"route={graph_route}",
                    payload={
                        "graph_route": graph_route,
                        "graph_steps": tool_result_metadata.get("graph_steps", []),
                    },
                )
            )
        recovery_plan = tool_result_metadata.get("recovery_plan")
        if isinstance(recovery_plan, dict):
            events.append(
                RuntimeEvent(
                    index=len(events) + 1,
                    event_type="recovery",
                    name="recovery_plan",
                    detail=recovery_plan.get("reason", ""),
                    payload=recovery_plan,
                )
            )
        skill_run = tool_result_metadata.get("skill_run")
        if isinstance(skill_run, dict):
            events.append(
                RuntimeEvent(
                    index=len(events) + 1,
                    event_type="skill",
                    name=skill_run.get("skill", {}).get("name", "unknown"),
                    detail=f"status={skill_run.get('status', 'unknown')}",
                    payload=skill_run,
                )
            )

    if tool_error:
        events.append(
            RuntimeEvent(
                index=len(events) + 1,
                event_type="error",
                name="tool_error",
                detail=tool_error,
            )
        )

    return events
