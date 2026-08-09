"""Replay and comparison helpers for checkpointed agent runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .events import RuntimeEvent, build_runtime_events


@dataclass(frozen=True)
class ReplaySummary:
    """Compact comparison-ready summary for one persisted run."""

    run_id: str                             # 运行 ID
    run_kind: str                           # 运行类型
    created_at: str                         # 创建时间
    session_id: str                         # 会话 ID
    task_id: str                            # 任务 ID
    user_input: str                         # 用户输入
    route_action: str                       # 路由动作
    route_tool: str                         # 路由工具名
    graph_route: str                        # 图执行路由名
    answer: str                             # 最终答案
    step_count: int                         # 步骤数量
    runtime_event_count: int                # runtime event 数量
    tool_names: tuple[str, ...] = ()        # 涉及的工具名
    skill_names: tuple[str, ...] = ()       # 涉及的技能名
    delegation_names: tuple[str, ...] = ()  # 涉及的委派角色名
    has_memory: bool = False                # 是否包含长程记忆快照
    has_recovery: bool = False              # 是否包含恢复信息
    failure_type: str = "none"              # 失败类型

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
            "session_id": self.session_id,
            "task_id": self.task_id,
            "user_input": self.user_input,
            "route_action": self.route_action,
            "route_tool": self.route_tool,
            "graph_route": self.graph_route,
            "answer": self.answer,
            "step_count": self.step_count,
            "runtime_event_count": self.runtime_event_count,
            "tool_names": list(self.tool_names),
            "skill_names": list(self.skill_names),
            "delegation_names": list(self.delegation_names),
            "has_memory": self.has_memory,
            "has_recovery": self.has_recovery,
            "failure_type": self.failure_type,
        }


@dataclass(frozen=True)
class ReplayReport:
    """Structured replay report built from a saved checkpoint."""

    run_id: str             # 运行 ID
    run_kind: str           # 运行类型
    created_at: str         # 创建时间
    user_input: str         # 用户输入
    route: dict[str, Any]   # 路由信息
    answer: str             # 最终答案
    trace_text: str         # 原始 trace 文本
    events: list[RuntimeEvent] = field(default_factory=list)                    # 重建的 runtime events
    stored_runtime_events: list[dict[str, Any]] = field(default_factory=list)   # 持久化的 runtime events

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
            f"Session ID: {self.route.get('session_id', 'default') if isinstance(self.route, dict) else 'default'}",
            f"Task ID: {self.route.get('task_id', 'unknown') if isinstance(self.route, dict) else 'unknown'}",
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

    older: ReplaySummary                            # 较旧的运行摘要
    newer: ReplaySummary                            # 较新的运行摘要
    changed_fields: tuple[str, ...]                 # 变化字段名
    tool_names_added: tuple[str, ...] = ()          # 新增工具名
    tool_names_removed: tuple[str, ...] = ()        # 删除工具名
    skill_names_added: tuple[str, ...] = ()         # 新增技能名
    skill_names_removed: tuple[str, ...] = ()       # 删除技能名
    delegation_names_added: tuple[str, ...] = ()    # 新增委派角色名
    delegation_names_removed: tuple[str, ...] = ()  # 删除委派角色名

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
            "delegation_names_added": list(self.delegation_names_added),
            "delegation_names_removed": list(self.delegation_names_removed),
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
            f"- Session / Task: {self.older.session_id} / {self.older.task_id}",
            f"- Route: {self.older.route_action} / {self.older.route_tool}",
            f"- Graph route: {self.older.graph_route}",
            f"- Steps: {self.older.step_count}",
            f"- Runtime events: {self.older.runtime_event_count}",
            f"- Tools: {', '.join(self.older.tool_names) if self.older.tool_names else 'none'}",
            f"- Skills: {', '.join(self.older.skill_names) if self.older.skill_names else 'none'}",
            f"- Delegations: {', '.join(self.older.delegation_names) if self.older.delegation_names else 'none'}",
            f"- Memory: {'yes' if self.older.has_memory else 'no'}",
            f"- Recovery: {'yes' if self.older.has_recovery else 'no'}",
            f"- Failure type: {self.older.failure_type}",
            f"- Answer preview: {self.older.answer_preview()}",
            "",
            "Newer summary:",
            f"- Session / Task: {self.newer.session_id} / {self.newer.task_id}",
            f"- Route: {self.newer.route_action} / {self.newer.route_tool}",
            f"- Graph route: {self.newer.graph_route}",
            f"- Steps: {self.newer.step_count}",
            f"- Runtime events: {self.newer.runtime_event_count}",
            f"- Tools: {', '.join(self.newer.tool_names) if self.newer.tool_names else 'none'}",
            f"- Skills: {', '.join(self.newer.skill_names) if self.newer.skill_names else 'none'}",
            f"- Delegations: {', '.join(self.newer.delegation_names) if self.newer.delegation_names else 'none'}",
            f"- Memory: {'yes' if self.newer.has_memory else 'no'}",
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
                f"Delegations added: {', '.join(self.delegation_names_added) if self.delegation_names_added else 'none'}",
                f"Delegations removed: {', '.join(self.delegation_names_removed) if self.delegation_names_removed else 'none'}",
            ]
        )
        return "\n".join(lines)


@dataclass(frozen=True)
class CheckpointResumePlan:
    """Plan for resuming a persisted checkpoint."""

    source_run_id: str      # 源运行 ID
    source_run_kind: str    # 源运行类型
    session_id: str         # 源会话 ID
    task_id: str            # 源任务 ID
    user_input: str         # 原始用户输入
    route_action: str       # 源路由动作
    route_tool: str         # 源路由工具名
    graph_route: str        # 源 graph 路由
    failure_type: str       # 源失败类型
    has_recovery: bool      # 是否存在恢复信息
    resume_mode: str        # 恢复模式
    can_resume: bool        # 是否允许恢复
    reason: str             # 恢复原因
    next_safe_action: str   # 下一步安全动作

    def to_dict(self) -> dict[str, Any]:
        """Render the plan as JSON-ready data."""

        return {
            "source_run_id": self.source_run_id,
            "source_run_kind": self.source_run_kind,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "user_input": self.user_input,
            "route_action": self.route_action,
            "route_tool": self.route_tool,
            "graph_route": self.graph_route,
            "failure_type": self.failure_type,
            "has_recovery": self.has_recovery,
            "resume_mode": self.resume_mode,
            "can_resume": self.can_resume,
            "reason": self.reason,
            "next_safe_action": self.next_safe_action,
        }

    def to_text(self) -> str:
        """Render the resume plan for CLI output."""

        lines = [
            "Checkpoint resume plan",
            f"Source run: {self.source_run_id} [{self.source_run_kind}]",
            f"Session / Task: {self.session_id} / {self.task_id}",
            f"Route: {self.route_action} / {self.route_tool}",
            f"Graph route: {self.graph_route}",
            f"Failure type: {self.failure_type}",
            f"Has recovery: {'yes' if self.has_recovery else 'no'}",
            f"Resume mode: {self.resume_mode}",
            f"Can resume: {'yes' if self.can_resume else 'no'}",
            f"Reason: {self.reason}",
            f"Next safe action: {self.next_safe_action}",
        ]
        return "\n".join(lines)


@dataclass(frozen=True)
class CheckpointResumeReport:
    """Structured report for a checkpoint-guided resume."""

    plan: CheckpointResumePlan              # 恢复计划
    source: ReplaySummary                   # 源运行摘要
    resumed: ReplaySummary | None = None    # 恢复后的运行摘要
    diff: ReplayDiffReport | None = None    # 恢复前后差异

    def to_dict(self) -> dict[str, Any]:
        """Render the resume report as JSON-ready data."""

        return {
            "plan": self.plan.to_dict(),
            "source": self.source.to_dict(),
            "resumed": self.resumed.to_dict() if self.resumed is not None else None,
            "diff": self.diff.to_dict() if self.diff is not None else None,
        }

    def to_text(self) -> str:
        """Render the resume report for CLI output."""

        lines = [self.plan.to_text(), "", "Source summary:"]
        lines.extend(
            [
                f"- Run ID: {self.source.run_id}",
                f"- Answer preview: {self.source.answer_preview()}",
                f"- Steps: {self.source.step_count}",
                f"- Runtime events: {self.source.runtime_event_count}",
                f"- Tools: {', '.join(self.source.tool_names) if self.source.tool_names else 'none'}",
                f"- Skills: {', '.join(self.source.skill_names) if self.source.skill_names else 'none'}",
            ]
        )
        if self.resumed is not None:
            lines.extend(
                [
                    "",
                    "Resumed summary:",
                    f"- Run ID: {self.resumed.run_id}",
                    f"- Answer preview: {self.resumed.answer_preview()}",
                    f"- Steps: {self.resumed.step_count}",
                    f"- Runtime events: {self.resumed.runtime_event_count}",
                    f"- Tools: {', '.join(self.resumed.tool_names) if self.resumed.tool_names else 'none'}",
                    f"- Skills: {', '.join(self.resumed.skill_names) if self.resumed.skill_names else 'none'}",
                ]
            )
        if self.diff is not None:
            lines.extend(["", "Resume diff:", self.diff.to_text()])
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
        route={
            **route,
            "session_id": trace.get("session_id", "default"),
            "task_id": trace.get("task_id", "unknown"),
        },
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
    delegation_names = _collect_delegation_names(tool_metadata.get("subagent_delegation"))
    has_memory = isinstance(trace.get("memory"), dict)
    events = build_replay_report(record).events
    return ReplaySummary(
        run_id=str(record.get("run_id", "unknown")),
        run_kind=str(record.get("run_kind", "unknown")),
        created_at=str(record.get("created_at", "unknown")),
        session_id=str(trace.get("session_id", "default")),
        task_id=str(trace.get("task_id", "unknown")),
        user_input=str(record.get("user_input", "")),
        route_action=_normalize_label(route.get("action"), default="unknown"),
        route_tool=_normalize_label(route.get("tool_name"), default="none"),
        graph_route=_normalize_label(tool_metadata.get("graph_route", trace.get("route", route).get("tool_name", "none")), default="none"),
        answer=str(record.get("answer", "")),
        step_count=len(_steps_list(record)),
        runtime_event_count=len(events),
        tool_names=tool_names,
        skill_names=skill_names,
        delegation_names=delegation_names,
        has_memory=has_memory,
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
    if older.delegation_names != newer.delegation_names:
        changed_fields.append("delegation_usage")
    if older.session_id != newer.session_id or older.task_id != newer.task_id or older.has_memory != newer.has_memory:
        changed_fields.append("memory_continuity")
    if older.has_recovery != newer.has_recovery or older.failure_type != newer.failure_type:
        changed_fields.append("recovery")

    older_tools = set(older.tool_names)
    newer_tools = set(newer.tool_names)
    older_skills = set(older.skill_names)
    newer_skills = set(newer.skill_names)
    older_delegations = set(older.delegation_names)
    newer_delegations = set(newer.delegation_names)

    return ReplayDiffReport(
        older=older,
        newer=newer,
        changed_fields=tuple(changed_fields),
        tool_names_added=tuple(sorted(newer_tools - older_tools)),
        tool_names_removed=tuple(sorted(older_tools - newer_tools)),
        skill_names_added=tuple(sorted(newer_skills - older_skills)),
        skill_names_removed=tuple(sorted(older_skills - newer_skills)),
        delegation_names_added=tuple(sorted(newer_delegations - older_delegations)),
        delegation_names_removed=tuple(sorted(older_delegations - newer_delegations)),
    )


def format_replay_report(record: dict[str, Any]) -> str:
    """Render a replay report for CLI use."""

    return build_replay_report(record).to_text()


def format_replay_diff_report(older_record: dict[str, Any], newer_record: dict[str, Any]) -> str:
    """Render a replay diff report for CLI use."""

    return compare_replay_reports(older_record, newer_record).to_text()


def build_checkpoint_resume_plan(record: dict[str, Any]) -> CheckpointResumePlan:
    """Build a checkpoint-guided resume plan from a persisted run."""

    summary = build_replay_summary(record)
    route = _route_dict(record, _trace_dict(record))
    trace = _trace_dict(record)
    recovery_plan = _tool_metadata(trace).get("recovery_plan")
    if not isinstance(recovery_plan, dict):
        recovery_plan = {}
    next_safe_action = _normalize_label(recovery_plan.get("next_safe_action"), default="Reuse the persisted route hints and rerun the request.")
    reason = (
        "Resume the saved request with the checkpoint route hints so the same execution path can be re-entered."
        if summary.has_recovery
        else "No failure was recorded; rerun the saved request with the persisted route hints."
    )
    resume_mode = "guided_retry" if summary.has_recovery else "checkpoint_rerun"
    return CheckpointResumePlan(
        source_run_id=summary.run_id,
        source_run_kind=summary.run_kind,
        session_id=summary.session_id,
        task_id=summary.task_id,
        user_input=summary.user_input,
        route_action=summary.route_action,
        route_tool=summary.route_tool,
        graph_route=summary.graph_route,
        failure_type=summary.failure_type,
        has_recovery=summary.has_recovery,
        resume_mode=resume_mode,
        can_resume=True,
        reason=reason,
        next_safe_action=next_safe_action,
    )


def build_checkpoint_resume_report(
    source_record: dict[str, Any],
    resumed_record: dict[str, Any] | None = None,
) -> CheckpointResumeReport:
    """Build a structured resume report from checkpoint records."""

    plan = build_checkpoint_resume_plan(source_record)
    source_summary = build_replay_summary(source_record)
    resumed_summary = build_replay_summary(resumed_record) if resumed_record is not None else None
    diff = compare_replay_reports(source_record, resumed_record) if resumed_record is not None else None
    return CheckpointResumeReport(
        plan=plan,
        source=source_summary,
        resumed=resumed_summary,
        diff=diff,
    )


def format_checkpoint_resume_report(
    source_record: dict[str, Any],
    resumed_record: dict[str, Any] | None = None,
) -> str:
    """Render a checkpoint-guided resume report for CLI use."""

    return build_checkpoint_resume_report(source_record, resumed_record).to_text()


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


def _collect_delegation_names(subagent_delegation: dict[str, Any] | None) -> tuple[str, ...]:
    """Collect stable subagent delegation names mentioned by a run."""

    if not isinstance(subagent_delegation, dict):
        return ()
    names = set()
    delegations = subagent_delegation.get("delegations", [])
    if isinstance(delegations, list):
        for delegation in delegations:
            if not isinstance(delegation, dict):
                continue
            role = delegation.get("role", {})
            if isinstance(role, dict):
                name = role.get("name")
                if isinstance(name, str) and name.strip():
                    names.add(name.strip())
    return tuple(sorted(names))


def _normalize_label(value: Any, default: str) -> str:
    """Convert optional values into stable display labels."""

    if isinstance(value, str) and value.strip():
        return value.strip()
    return default
