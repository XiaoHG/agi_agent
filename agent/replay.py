"""Replay and comparison helpers for checkpointed agent runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .events import RuntimeEvent, build_runtime_events


@dataclass(frozen=True)
class ReplaySummary:
    """Compact comparison-ready summary for one persisted run."""

    run_id: str
    run_kind: str
    created_at: str
    user_input: str
    route_action: str
    route_tool: str
    graph_route: str
    answer: str
    step_count: int
    runtime_event_count: int
    tool_names: tuple[str, ...] = ()
    skill_names: tuple[str, ...] = ()
    has_recovery: bool = False
    failure_type: str = "none"

    def answer_preview(self, limit: int = 120) -> str:
        """Return a compact answer preview for text reports."""

        normalized = " ".join(self.answer.split())
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 15] + "... (truncated)"

    def to_dict(self) -> dict[str, Any]:
        """Render the summary as JSON-ready data."""

        return {
            "run_id": self.run_id,
            "run_kind": self.run_kind,
            "created_at": self.created_at,
            "user_input": self.user_input,
            "route_action": self.route_action,
            "route_tool": self.route_tool,
            "graph_route": self.graph_route,
            "answer": self.answer,
            "step_count": self.step_count,
            "runtime_event_count": self.runtime_event_count,
            "tool_names": list(self.tool_names),
            "skill_names": list(self.skill_names),
            "has_recovery": self.has_recovery,
            "failure_type": self.failure_type,
        }


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


@dataclass(frozen=True)
class ReplayDiffReport:
    """Structured diff between two replayable runs."""

    older: ReplaySummary
    newer: ReplaySummary
    changed_fields: tuple[str, ...]
    tool_names_added: tuple[str, ...] = ()
    tool_names_removed: tuple[str, ...] = ()
    skill_names_added: tuple[str, ...] = ()
    skill_names_removed: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Render the diff report as JSON-ready data."""

        return {
            "older": self.older.to_dict(),
            "newer": self.newer.to_dict(),
            "changed_fields": list(self.changed_fields),
            "tool_names_added": list(self.tool_names_added),
            "tool_names_removed": list(self.tool_names_removed),
            "skill_names_added": list(self.skill_names_added),
            "skill_names_removed": list(self.skill_names_removed),
            "step_count_delta": self.step_count_delta,
            "runtime_event_delta": self.runtime_event_delta,
        }

    @property
    def step_count_delta(self) -> int:
        """Return the delta in recorded steps."""

        return self.newer.step_count - self.older.step_count

    @property
    def runtime_event_delta(self) -> int:
        """Return the delta in rebuilt runtime events."""

        return self.newer.runtime_event_count - self.older.runtime_event_count

    def to_text(self) -> str:
        """Render the diff report for CLI output."""

        lines = [
            "Replay diff report",
            f"Older run: {self.older.run_id} [{self.older.run_kind}] {self.older.created_at}",
            f"Newer run: {self.newer.run_id} [{self.newer.run_kind}] {self.newer.created_at}",
            "",
            "Older summary:",
            f"- Route: {self.older.route_action} / {self.older.route_tool}",
            f"- Graph route: {self.older.graph_route}",
            f"- Steps: {self.older.step_count}",
            f"- Runtime events: {self.older.runtime_event_count}",
            f"- Tools: {', '.join(self.older.tool_names) if self.older.tool_names else 'none'}",
            f"- Skills: {', '.join(self.older.skill_names) if self.older.skill_names else 'none'}",
            f"- Recovery: {'yes' if self.older.has_recovery else 'no'}",
            f"- Failure type: {self.older.failure_type}",
            f"- Answer preview: {self.older.answer_preview()}",
            "",
            "Newer summary:",
            f"- Route: {self.newer.route_action} / {self.newer.route_tool}",
            f"- Graph route: {self.newer.graph_route}",
            f"- Steps: {self.newer.step_count}",
            f"- Runtime events: {self.newer.runtime_event_count}",
            f"- Tools: {', '.join(self.newer.tool_names) if self.newer.tool_names else 'none'}",
            f"- Skills: {', '.join(self.newer.skill_names) if self.newer.skill_names else 'none'}",
            f"- Recovery: {'yes' if self.newer.has_recovery else 'no'}",
            f"- Failure type: {self.newer.failure_type}",
            f"- Answer preview: {self.newer.answer_preview()}",
            "",
            "Differences:",
        ]
        if self.changed_fields:
            lines.extend(f"- {field}" for field in self.changed_fields)
        else:
            lines.append("- none")
        lines.extend(
            [
                f"Step count delta: {self.step_count_delta}",
                f"Runtime event delta: {self.runtime_event_delta}",
                f"Tools added: {', '.join(self.tool_names_added) if self.tool_names_added else 'none'}",
                f"Tools removed: {', '.join(self.tool_names_removed) if self.tool_names_removed else 'none'}",
                f"Skills added: {', '.join(self.skill_names_added) if self.skill_names_added else 'none'}",
                f"Skills removed: {', '.join(self.skill_names_removed) if self.skill_names_removed else 'none'}",
            ]
        )
        return "\n".join(lines)


def build_replay_report(record: dict[str, Any]) -> ReplayReport:
    """Build a replay report from a persisted checkpoint."""

    trace = _trace_dict(record)
    steps = _steps_list(record)
    tool_metadata = _tool_metadata(trace)
    tool_error = record.get("tool_error") or trace.get("tool_error")
    events = build_runtime_events(steps, tool_metadata, str(tool_error) if tool_error is not None else None)
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


def build_replay_summary(record: dict[str, Any]) -> ReplaySummary:
    """Build a compact summary for one replayable run."""

    trace = _trace_dict(record)
    route = _route_dict(record, trace)
    tool_metadata = _tool_metadata(trace)
    tool_result = trace.get("tool_result", record.get("tool_result", {}))
    if not isinstance(tool_result, dict):
        tool_result = {}
    skill_run = tool_metadata.get("skill_run")
    if not isinstance(skill_run, dict):
        skill_run = trace.get("skill_run", {})
    if not isinstance(skill_run, dict):
        skill_run = {}
    recovery_plan = tool_metadata.get("recovery_plan", trace.get("recovery_plan", {}))
    if not isinstance(recovery_plan, dict):
        recovery_plan = {}

    tool_names = _collect_tool_names(route, trace, tool_result, tool_metadata)
    skill_names = _collect_skill_names(skill_run)
    events = build_replay_report(record).events
    return ReplaySummary(
        run_id=str(record.get("run_id", "unknown")),
        run_kind=str(record.get("run_kind", "unknown")),
        created_at=str(record.get("created_at", "unknown")),
        user_input=str(record.get("user_input", "")),
        route_action=_normalize_label(route.get("action"), default="unknown"),
        route_tool=_normalize_label(route.get("tool_name"), default="none"),
        graph_route=_normalize_label(tool_metadata.get("graph_route", trace.get("route", route).get("tool_name", "none")), default="none"),
        answer=str(record.get("answer", "")),
        step_count=len(_steps_list(record)),
        runtime_event_count=len(events),
        tool_names=tool_names,
        skill_names=skill_names,
        has_recovery=bool(recovery_plan),
        failure_type=_normalize_label(recovery_plan.get("failure_type"), default="none"),
    )


def compare_replay_reports(older_record: dict[str, Any], newer_record: dict[str, Any]) -> ReplayDiffReport:
    """Compare two replayable run records and build a diff report."""

    older = build_replay_summary(older_record)
    newer = build_replay_summary(newer_record)

    changed_fields: list[str] = []
    if older.route_action != newer.route_action or older.route_tool != newer.route_tool:
        changed_fields.append("route")
    if older.graph_route != newer.graph_route:
        changed_fields.append("graph_route")
    if older.step_count != newer.step_count:
        changed_fields.append("step_count")
    if older.runtime_event_count != newer.runtime_event_count:
        changed_fields.append("runtime_event_count")
    if older.answer != newer.answer:
        changed_fields.append("answer")
    if older.tool_names != newer.tool_names:
        changed_fields.append("tool_usage")
    if older.skill_names != newer.skill_names:
        changed_fields.append("skill_usage")
    if older.has_recovery != newer.has_recovery or older.failure_type != newer.failure_type:
        changed_fields.append("recovery")

    older_tools = set(older.tool_names)
    newer_tools = set(newer.tool_names)
    older_skills = set(older.skill_names)
    newer_skills = set(newer.skill_names)

    return ReplayDiffReport(
        older=older,
        newer=newer,
        changed_fields=tuple(changed_fields),
        tool_names_added=tuple(sorted(newer_tools - older_tools)),
        tool_names_removed=tuple(sorted(older_tools - newer_tools)),
        skill_names_added=tuple(sorted(newer_skills - older_skills)),
        skill_names_removed=tuple(sorted(older_skills - newer_skills)),
    )


def format_replay_report(record: dict[str, Any]) -> str:
    """Render a replay report for CLI use."""

    return build_replay_report(record).to_text()


def format_replay_diff_report(older_record: dict[str, Any], newer_record: dict[str, Any]) -> str:
    """Render a replay diff report for CLI use."""

    return compare_replay_reports(older_record, newer_record).to_text()


def _trace_dict(record: dict[str, Any]) -> dict[str, Any]:
    """Read a safe trace dictionary from a checkpoint record."""

    trace = record.get("trace", {})
    return trace if isinstance(trace, dict) else {}


def _steps_list(record: dict[str, Any]) -> list[Any]:
    """Read the best available step list from a checkpoint record."""

    trace = _trace_dict(record)
    steps = trace.get("steps", record.get("steps", []))
    return steps if isinstance(steps, list) else []


def _tool_metadata(trace: dict[str, Any]) -> dict[str, Any]:
    """Read normalized tool metadata from a trace dictionary."""

    tool_result = trace.get("tool_result", {})
    if not isinstance(tool_result, dict):
        return {}
    metadata = tool_result.get("metadata", {})
    return metadata if isinstance(metadata, dict) else {}


def _route_dict(record: dict[str, Any], trace: dict[str, Any]) -> dict[str, Any]:
    """Read a safe route dictionary from a checkpoint record."""

    route = trace.get("route", record.get("route", {}))
    return route if isinstance(route, dict) else {}


def _collect_tool_names(
    route: dict[str, Any],
    trace: dict[str, Any],
    tool_result: dict[str, Any],
    tool_metadata: dict[str, Any],
) -> tuple[str, ...]:
    """Collect stable tool names mentioned by a run."""

    names = {
        str(value).strip()
        for value in [
            route.get("tool_name"),
            trace.get("selected_tool"),
            trace.get("logical_tool_name"),
            tool_result.get("tool_name"),
            tool_metadata.get("logical_tool_name"),
        ]
        if isinstance(value, str) and value.strip() and value != "none"
    }
    return tuple(sorted(names))


def _collect_skill_names(skill_run: dict[str, Any]) -> tuple[str, ...]:
    """Collect stable skill names mentioned by a run."""

    names = set()
    skill = skill_run.get("skill")
    if isinstance(skill, dict):
        name = skill.get("name")
        if isinstance(name, str) and name.strip():
            names.add(name.strip())
    return tuple(sorted(names))


def _normalize_label(value: Any, default: str) -> str:
    """Convert optional values into stable display labels."""

    if isinstance(value, str) and value.strip():
        return value.strip()
    return default
