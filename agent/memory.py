"""Long-horizon memory models for session continuity and task tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SessionMemory:
    """Long-horizon memory for one agent session."""

    session_id: str                         # 会话 ID
    created_at: str                         # 首次创建时间
    updated_at: str                         # 最近更新时间
    run_ids: tuple[str, ...] = ()           # 属于该会话的运行 ID
    recent_inputs: tuple[str, ...] = ()     # 最近用户输入
    active_task_ids: tuple[str, ...] = ()   # 当前会话涉及的任务 ID
    latest_answer_preview: str = ""         # 最新答案摘要
    key_facts: tuple[str, ...] = ()         # 会话层关键事实
    continuity_notes: tuple[str, ...] = ()  # 会话连续性备注

    def to_dict(self) -> dict[str, Any]:
        """Render the session memory as JSON-ready data."""

        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "run_ids": list(self.run_ids),
            "recent_inputs": list(self.recent_inputs),
            "active_task_ids": list(self.active_task_ids),
            "latest_answer_preview": self.latest_answer_preview,
            "key_facts": list(self.key_facts),
            "continuity_notes": list(self.continuity_notes),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SessionMemory":
        """Load session memory from JSON-ready data."""

        return cls(
            session_id=str(payload.get("session_id", "default")),
            created_at=str(payload.get("created_at", _now_iso())),
            updated_at=str(payload.get("updated_at", _now_iso())),
            run_ids=_tuple_of_strings(payload.get("run_ids")),
            recent_inputs=_tuple_of_strings(payload.get("recent_inputs")),
            active_task_ids=_tuple_of_strings(payload.get("active_task_ids")),
            latest_answer_preview=str(payload.get("latest_answer_preview", "")),
            key_facts=_tuple_of_strings(payload.get("key_facts")),
            continuity_notes=_tuple_of_strings(payload.get("continuity_notes")),
        )

    def to_text(self) -> str:
        """Render the session memory for CLI output."""

        return "\n".join(
            [
                "Session memory",
                f"Session ID: {self.session_id}",
                f"Created at: {self.created_at}",
                f"Updated at: {self.updated_at}",
                f"Run count: {len(self.run_ids)}",
                f"Active tasks: {', '.join(self.active_task_ids) if self.active_task_ids else 'none'}",
                f"Latest answer: {self.latest_answer_preview or 'none'}",
                f"Key facts: {', '.join(self.key_facts) if self.key_facts else 'none'}",
                f"Continuity notes: {', '.join(self.continuity_notes) if self.continuity_notes else 'none'}",
            ]
        )


@dataclass(frozen=True)
class TaskMemory:
    """Long-horizon memory for one tracked task."""

    task_id: str                                # 任务 ID
    session_id: str                             # 所属会话 ID
    objective: str                              # 任务目标
    created_at: str                             # 首次创建时间
    updated_at: str                             # 最近更新时间
    status: str = "active"                      # 当前任务状态
    run_ids: tuple[str, ...] = ()               # 属于该任务的运行 ID
    latest_run_id: str = ""                     # 最近一次运行 ID
    latest_route: str = ""                      # 最近一次执行路由
    related_tools: tuple[str, ...] = ()         # 该任务涉及的工具
    related_skills: tuple[str, ...] = ()        # 该任务涉及的技能
    related_delegations: tuple[str, ...] = ()   # 该任务涉及的委派角色
    latest_answer_preview: str = ""             # 最新答案摘要
    continuity_notes: tuple[str, ...] = ()      # 任务连续性备注

    def to_dict(self) -> dict[str, Any]:
        """Render the task memory as JSON-ready data."""

        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "objective": self.objective,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "run_ids": list(self.run_ids),
            "latest_run_id": self.latest_run_id,
            "latest_route": self.latest_route,
            "related_tools": list(self.related_tools),
            "related_skills": list(self.related_skills),
            "related_delegations": list(self.related_delegations),
            "latest_answer_preview": self.latest_answer_preview,
            "continuity_notes": list(self.continuity_notes),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TaskMemory":
        """Load task memory from JSON-ready data."""

        return cls(
            task_id=str(payload.get("task_id", "unknown")),
            session_id=str(payload.get("session_id", "default")),
            objective=str(payload.get("objective", "")),
            created_at=str(payload.get("created_at", _now_iso())),
            updated_at=str(payload.get("updated_at", _now_iso())),
            status=str(payload.get("status", "active")),
            run_ids=_tuple_of_strings(payload.get("run_ids")),
            latest_run_id=str(payload.get("latest_run_id", "")),
            latest_route=str(payload.get("latest_route", "")),
            related_tools=_tuple_of_strings(payload.get("related_tools")),
            related_skills=_tuple_of_strings(payload.get("related_skills")),
            related_delegations=_tuple_of_strings(payload.get("related_delegations")),
            latest_answer_preview=str(payload.get("latest_answer_preview", "")),
            continuity_notes=_tuple_of_strings(payload.get("continuity_notes")),
        )

    def to_text(self) -> str:
        """Render the task memory for CLI output."""

        return "\n".join(
            [
                "Task memory",
                f"Task ID: {self.task_id}",
                f"Session ID: {self.session_id}",
                f"Objective: {self.objective}",
                f"Status: {self.status}",
                f"Created at: {self.created_at}",
                f"Updated at: {self.updated_at}",
                f"Latest run: {self.latest_run_id or 'none'}",
                f"Latest route: {self.latest_route or 'none'}",
                f"Related tools: {', '.join(self.related_tools) if self.related_tools else 'none'}",
                f"Related skills: {', '.join(self.related_skills) if self.related_skills else 'none'}",
                f"Related delegations: {', '.join(self.related_delegations) if self.related_delegations else 'none'}",
                f"Latest answer: {self.latest_answer_preview or 'none'}",
                f"Continuity notes: {', '.join(self.continuity_notes) if self.continuity_notes else 'none'}",
            ]
        )


@dataclass(frozen=True)
class MemorySnapshot:
    """Combined memory snapshot attached to one persisted run."""

    session_id: str                 # 会话 ID
    task_id: str                    # 任务 ID
    session_memory: SessionMemory   # 会话记忆
    task_memory: TaskMemory         # 任务记忆

    def to_dict(self) -> dict[str, Any]:
        """Render the snapshot as JSON-ready data."""

        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "session_memory": self.session_memory.to_dict(),
            "task_memory": self.task_memory.to_dict(),
        }

    def to_text(self) -> str:
        """Render the memory snapshot for traces."""

        return (
            f"Session ID: {self.session_id}\n"
            f"Task ID: {self.task_id}\n"
            f"Session runs: {len(self.session_memory.run_ids)}\n"
            f"Task runs: {len(self.task_memory.run_ids)}\n"
            f"Task status: {self.task_memory.status}"
        )


@dataclass(frozen=True)
class AgentMemoryStore:
    """Local JSON store for long-horizon session and task memory."""

    memory_dir: Path  # 记忆存储根目录

    def __post_init__(self) -> None:
        """Normalize derived fields immediately after dataclass initialization."""
        object.__setattr__(self, "memory_dir", self.memory_dir.resolve())

    def update_from_trace(self, session_id: str, task_id: str, trace: dict[str, Any]) -> MemorySnapshot:
        """Update session and task memory from one JSON-ready run trace."""

        existing_session = self.load_session(session_id)
        existing_task = self.load_task(task_id)
        session_memory = _build_session_memory(existing_session, session_id, task_id, trace)
        task_memory = _build_task_memory(existing_task, session_id, task_id, trace)
        self.save_session(session_memory)
        self.save_task(task_memory)
        return MemorySnapshot(
            session_id=session_id,
            task_id=task_id,
            session_memory=session_memory,
            task_memory=task_memory,
        )

    def save_session(self, memory: SessionMemory) -> Path:
        """Save one session memory record."""

        path = self.memory_dir / "sessions" / f"{memory.session_id}.json"
        return _save_json(path, memory.to_dict())

    def load_session(self, session_id: str) -> SessionMemory | None:
        """Load one session memory record."""

        path = self.memory_dir / "sessions" / f"{session_id}.json"
        payload = _load_json(path)
        return SessionMemory.from_dict(payload) if isinstance(payload, dict) else None

    def list_sessions(self, limit: int = 10) -> list[SessionMemory]:
        """List recent session memory records."""

        return [
            SessionMemory.from_dict(payload)
            for payload in _list_json_records(self.memory_dir / "sessions", limit=limit)
        ]

    def save_task(self, memory: TaskMemory) -> Path:
        """Save one task memory record."""

        path = self.memory_dir / "tasks" / f"{memory.task_id}.json"
        return _save_json(path, memory.to_dict())

    def load_task(self, task_id: str) -> TaskMemory | None:
        """Load one task memory record."""

        path = self.memory_dir / "tasks" / f"{task_id}.json"
        payload = _load_json(path)
        return TaskMemory.from_dict(payload) if isinstance(payload, dict) else None

    def list_tasks(self, limit: int = 10, session_id: str | None = None) -> list[TaskMemory]:
        """List recent task memory records."""

        tasks = [
            TaskMemory.from_dict(payload)
            for payload in _list_json_records(self.memory_dir / "tasks", limit=limit * 2)
        ]
        if session_id is not None:
            tasks = [task for task in tasks if task.session_id == session_id]
        return tasks[:limit]


def format_session_memory_list(records: list[SessionMemory]) -> str:
    """Render a compact session memory list."""

    if not records:
        return "No session memory found."
    return "\n".join(
        f"{index}. {record.session_id} runs={len(record.run_ids)} tasks={len(record.active_task_ids)} updated={record.updated_at}"
        for index, record in enumerate(records, start=1)
    )


def format_task_memory_list(records: list[TaskMemory]) -> str:
    """Render a compact task memory list."""

    if not records:
        return "No task memory found."
    return "\n".join(
        f"{index}. {record.task_id} [{record.status}] session={record.session_id} updated={record.updated_at}"
        for index, record in enumerate(records, start=1)
    )


def _build_session_memory(
    existing: SessionMemory | None,
    session_id: str,
    task_id: str,
    trace: dict[str, Any],
) -> SessionMemory:
    """Build the next session memory snapshot."""

    now = _now_iso()
    run_id = str(trace.get("run_id", "unknown"))
    user_input = str(trace.get("user_input", ""))
    answer_preview = str(trace.get("answer_preview", ""))
    key_facts = _merge_with_limit(
        existing.key_facts if existing is not None else (),
        _extract_key_facts(trace),
        limit=8,
    )
    continuity_notes = _merge_with_limit(
        existing.continuity_notes if existing is not None else (),
        (
            f"Latest route: {_extract_route_label(trace)}",
            f"Latest run: {run_id}",
        ),
        limit=8,
    )
    return SessionMemory(
        session_id=session_id,
        created_at=existing.created_at if existing is not None else now,
        updated_at=now,
        run_ids=_append_with_limit(existing.run_ids if existing is not None else (), run_id, limit=20),
        recent_inputs=_append_with_limit(existing.recent_inputs if existing is not None else (), user_input, limit=5),
        active_task_ids=_append_with_limit(existing.active_task_ids if existing is not None else (), task_id, limit=8),
        latest_answer_preview=answer_preview,
        key_facts=key_facts,
        continuity_notes=continuity_notes,
    )


def _build_task_memory(
    existing: TaskMemory | None,
    session_id: str,
    task_id: str,
    trace: dict[str, Any],
) -> TaskMemory:
    """Build the next task memory snapshot."""

    now = _now_iso()
    run_id = str(trace.get("run_id", "unknown"))
    tool_result = trace.get("tool_result", {})
    skill_run = trace.get("skill_run", {})
    delegation = trace.get("subagent_delegation", {})
    related_tools = _extract_related_tools(trace, tool_result)
    related_skills = _extract_related_skills(skill_run)
    related_delegations = _extract_related_delegations(delegation)
    status = "blocked" if trace.get("tool_error") else "active"
    continuity_notes = _merge_with_limit(
        existing.continuity_notes if existing is not None else (),
        (
            f"Latest route: {_extract_route_label(trace)}",
            f"Latest answer: {trace.get('answer_preview', '')}",
        ),
        limit=8,
    )
    return TaskMemory(
        task_id=task_id,
        session_id=session_id,
        objective=existing.objective if existing is not None and existing.objective else str(trace.get("user_input", "")),
        created_at=existing.created_at if existing is not None else now,
        updated_at=now,
        status=status,
        run_ids=_append_with_limit(existing.run_ids if existing is not None else (), run_id, limit=20),
        latest_run_id=run_id,
        latest_route=_extract_route_label(trace),
        related_tools=_merge_with_limit(existing.related_tools if existing is not None else (), related_tools, limit=12),
        related_skills=_merge_with_limit(existing.related_skills if existing is not None else (), related_skills, limit=12),
        related_delegations=_merge_with_limit(existing.related_delegations if existing is not None else (), related_delegations, limit=12),
        latest_answer_preview=str(trace.get("answer_preview", "")),
        continuity_notes=continuity_notes,
    )


def _extract_key_facts(trace: dict[str, Any]) -> tuple[str, ...]:
    """Extract stable session-level facts from a run trace."""

    facts = [f"Route: {_extract_route_label(trace)}"]
    skill_run = trace.get("skill_run", {})
    if isinstance(skill_run, dict):
        skill = skill_run.get("skill", {})
        if isinstance(skill, dict) and isinstance(skill.get("name"), str):
            facts.append(f"Skill: {skill['name']} ({skill_run.get('status', 'unknown')})")
    delegation = trace.get("subagent_delegation", {})
    delegation_names = _extract_related_delegations(delegation)
    if delegation_names:
        facts.append(f"Delegations: {', '.join(delegation_names)}")
    if trace.get("tool_error"):
        facts.append(f"Latest failure: {trace['tool_error']}")
    return tuple(facts)


def _extract_route_label(trace: dict[str, Any]) -> str:
    """Build a stable route label from a run trace."""

    route = trace.get("route", {})
    if not isinstance(route, dict):
        return "unknown / none"
    action = str(route.get("action", "unknown"))
    tool_name = str(route.get("tool_name", "none"))
    return f"{action} / {tool_name}"


def _extract_related_tools(trace: dict[str, Any], tool_result: Any) -> tuple[str, ...]:
    """Extract tool names mentioned in a run trace."""

    names: list[str] = []
    route = trace.get("route", {})
    if isinstance(route, dict) and isinstance(route.get("tool_name"), str):
        names.append(str(route["tool_name"]))
    if isinstance(tool_result, dict) and isinstance(tool_result.get("tool_name"), str):
        names.append(str(tool_result["tool_name"]))
    return tuple(dict.fromkeys(name for name in names if name and name != "none"))


def _extract_related_skills(skill_run: Any) -> tuple[str, ...]:
    """Extract skill names mentioned in a run trace."""

    if not isinstance(skill_run, dict):
        return ()
    skill = skill_run.get("skill", {})
    if isinstance(skill, dict) and isinstance(skill.get("name"), str):
        return (str(skill["name"]),)
    return ()


def _extract_related_delegations(delegation: Any) -> tuple[str, ...]:
    """Extract delegation role names mentioned in a run trace."""

    if not isinstance(delegation, dict):
        return ()
    names: list[str] = []
    for item in delegation.get("delegations", []):
        if not isinstance(item, dict):
            continue
        role = item.get("role", {})
        if isinstance(role, dict) and isinstance(role.get("name"), str):
            names.append(str(role["name"]))
    return tuple(dict.fromkeys(names))


def _append_with_limit(items: tuple[str, ...], value: str, limit: int) -> tuple[str, ...]:
    """Append one value while keeping order and a fixed maximum size."""

    if not value:
        return items
    merged = [item for item in items if item != value]
    merged.append(value)
    return tuple(merged[-limit:])


def _merge_with_limit(existing: tuple[str, ...], values: tuple[str, ...], limit: int) -> tuple[str, ...]:
    """Merge unique string values with a fixed maximum size."""

    merged = list(existing)
    for value in values:
        if not value:
            continue
        if value in merged:
            merged.remove(value)
        merged.append(value)
    return tuple(merged[-limit:])


def _tuple_of_strings(value: Any) -> tuple[str, ...]:
    """Normalize unknown list-like values into a tuple of strings."""

    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value if str(item))


def _save_json(path: Path, payload: dict[str, Any]) -> Path:
    """Save one JSON record to disk."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _load_json(path: Path) -> dict[str, Any] | None:
    """Load one JSON record from disk."""

    if not path.exists():
        return None
    raw_text = path.read_text(encoding="utf-8").strip()
    if not raw_text:
        return None
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _list_json_records(directory: Path, limit: int) -> list[dict[str, Any]]:
    """List recent JSON records from a directory."""

    if not directory.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:limit]:
        payload = _load_json(path)
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _now_iso() -> str:
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()
