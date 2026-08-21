"""Runtime event models for structured agent observability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RuntimeEvent:
    """One normalized event emitted during an Agent run."""

    index: int          # 事件序号，从 1 开始，保持稳定排序
    event_type: str     # 事件类型，例如 step / tool_result / error / recovery
    name: str           # 事件名称
    detail: str = ""    # 人类可读详情
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
        delegation = tool_result_metadata.get("subagent_delegation")
        if isinstance(delegation, dict):
            delegations = delegation.get("delegations", [])
            events.append(
                RuntimeEvent(
                    index=len(events) + 1,
                    event_type="delegation",
                    name=delegation.get("objective", "subagent_delegation"),
                    detail=f"delegations={len(delegations) if isinstance(delegations, list) else 0}",
                    payload=delegation,
                )
            )
            approval_request = delegation.get("approval_request")
            approval_decision = delegation.get("approval_decision")
            if isinstance(approval_request, dict) or isinstance(approval_decision, dict):
                events.append(
                    RuntimeEvent(
                        index=len(events) + 1,
                        event_type="approval_workflow",
                        name=(
                            approval_request.get("request_id", "approval_request")
                            if isinstance(approval_request, dict)
                            else "approval_request"
                        ),
                        detail=(
                            f"decision={approval_decision.get('decision', 'unknown')}"
                            if isinstance(approval_decision, dict)
                            else "decision=pending"
                        ),
                        payload={
                            "approval_request": approval_request,
                            "approval_decision": approval_decision,
                        },
                    )
                )
            executions = delegation.get("executions", [])
            if isinstance(executions, list) and executions:
                events.append(
                    RuntimeEvent(
                        index=len(events) + 1,
                        event_type="delegation_execution",
                        name="subagent_execution",
                        detail=f"executions={len(executions)} status={delegation.get('status', 'unknown')}",
                        payload={"executions": executions, "status": delegation.get("status", "unknown")},
                    )
                )
        subagent_runtime = tool_result_metadata.get("subagent_runtime")
        if isinstance(subagent_runtime, dict):
            messages = subagent_runtime.get("messages", [])
            transitions = subagent_runtime.get("transitions", [])
            queue_items = subagent_runtime.get("queue_items", [])
            inbox_entries = subagent_runtime.get("inbox_entries", [])
            outbox_entries = subagent_runtime.get("outbox_entries", [])
            claim_records = subagent_runtime.get("claim_records", [])
            task_lifecycle = subagent_runtime.get("task_lifecycle")
            watchdog_signals = subagent_runtime.get("watchdog_signals", [])
            events.append(
                RuntimeEvent(
                    index=len(events) + 1,
                    event_type="delegation_runtime",
                    name=subagent_runtime.get("session_id", "subagent_runtime"),
                    detail=(
                        f"messages={len(messages) if isinstance(messages, list) else 0} "
                        f"transitions={len(transitions) if isinstance(transitions, list) else 0} "
                        f"status={subagent_runtime.get('status', 'unknown')}"
                    ),
                    payload=subagent_runtime,
                )
            )
            if any(isinstance(items, list) and items for items in (queue_items, inbox_entries, outbox_entries, claim_records)):
                events.append(
                    RuntimeEvent(
                        index=len(events) + 1,
                        event_type="delegation_queue",
                        name="async_delegation_queue",
                        detail=(
                            f"queue={len(queue_items) if isinstance(queue_items, list) else 0} "
                            f"inbox={len(inbox_entries) if isinstance(inbox_entries, list) else 0} "
                            f"outbox={len(outbox_entries) if isinstance(outbox_entries, list) else 0} "
                            f"claims={len(claim_records) if isinstance(claim_records, list) else 0}"
                        ),
                        payload={
                            "queue_items": queue_items,
                            "inbox_entries": inbox_entries,
                            "outbox_entries": outbox_entries,
                            "claim_records": claim_records,
                        },
                    )
                )
            if isinstance(task_lifecycle, dict):
                events.append(
                    RuntimeEvent(
                        index=len(events) + 1,
                        event_type="task_lifecycle",
                        name=task_lifecycle.get("lifecycle_id", "task_lifecycle"),
                        detail=(
                            f"state={task_lifecycle.get('state', 'unknown')} "
                            f"health={task_lifecycle.get('health', 'unknown')}"
                        ),
                        payload=task_lifecycle,
                    )
                )
            if isinstance(watchdog_signals, list) and watchdog_signals:
                events.append(
                    RuntimeEvent(
                        index=len(events) + 1,
                        event_type="task_watchdog",
                        name="watchdog_signals",
                        detail=f"signals={len(watchdog_signals)}",
                        payload={"watchdog_signals": watchdog_signals},
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
