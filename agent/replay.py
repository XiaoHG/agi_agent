"""Replay helpers for checkpointed agent runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .events import RuntimeEvent, build_runtime_events


@dataclass(frozen=True)
class ReplayReport:
    """Structured replay report built from a saved checkpoint."""

    run_id: str
    run_kind: str
    created_at: str
    user_input: str
    route: dict[str, Any]
    answer: str
    trace_text: str
    events: list[RuntimeEvent] = field(default_factory=list)
    stored_runtime_events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Render the replay report as JSON-ready data."""

        return {
            "run_id": self.run_id,
            "run_kind": self.run_kind,
            "created_at": self.created_at,
            "user_input": self.user_input,
            "route": self.route,
            "answer": self.answer,
            "trace_text": self.trace_text,
            "events": [event.to_dict() for event in self.events],
            "stored_runtime_events": self.stored_runtime_events,
        }

    def to_text(self) -> str:
        """Render the replay report for CLI output."""

        route_action = self.route.get("action", "unknown") if isinstance(self.route, dict) else "unknown"
        route_tool = self.route.get("tool_name", "none") if isinstance(self.route, dict) else "none"
        lines = [
            "Replay report",
            f"Run ID: {self.run_id}",
            f"Run kind: {self.run_kind}",
            f"Created at: {self.created_at}",
            f"User input: {self.user_input}",
            f"Route: {route_action} / {route_tool}",
        ]
        if route_action == "graph":
            lines.append(f"Graph route: {route_tool}")
        if isinstance(self.route, dict) and self.route.get("reason"):
            lines.append(f"Route reason: {self.route.get('reason', '')}")
        lines.extend([
            f"Recorded runtime events: {len(self.stored_runtime_events)}",
            f"Rebuilt runtime events: {len(self.events)}",
            "Runtime events:",
        ])
        if self.events:
            lines.extend(f"- {event.to_text()}" for event in self.events)
        else:
            lines.append("- none")
        lines.extend(["", f"Answer: {self.answer}", "", "Trace:"])
        lines.append(self.trace_text or "No trace text available.")
        return "\n".join(lines)


def build_replay_report(record: dict[str, Any]) -> ReplayReport:
    """Build a replay report from a persisted checkpoint."""

    trace = record.get("trace", {}) if isinstance(record.get("trace"), dict) else {}
    steps = trace.get("steps", record.get("steps", []))
    tool_metadata = trace.get("tool_result", {}).get("metadata", {}) if isinstance(trace.get("tool_result"), dict) else {}
    if not isinstance(tool_metadata, dict):
        tool_metadata = {}
    tool_error = record.get("tool_error") or trace.get("tool_error")
    events = build_runtime_events(steps if isinstance(steps, list) else [], tool_metadata, str(tool_error) if tool_error is not None else None)
    stored_runtime_events = trace.get("runtime_events", [])
    if not isinstance(stored_runtime_events, list):
        stored_runtime_events = []
    route = trace.get("route", record.get("route", {}))
    if not isinstance(route, dict):
        route = {}
    return ReplayReport(
        run_id=str(record.get("run_id", "unknown")),
        run_kind=str(record.get("run_kind", "unknown")),
        created_at=str(record.get("created_at", "unknown")),
        user_input=str(record.get("user_input", "")),
        route=route,
        answer=str(record.get("answer", "")),
        trace_text=str(record.get("trace_text", "")),
        events=events,
        stored_runtime_events=[event for event in stored_runtime_events if isinstance(event, dict)],
    )


def format_replay_report(record: dict[str, Any]) -> str:
    """Render a replay report for CLI use."""

    return build_replay_report(record).to_text()
