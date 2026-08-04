"""Persistence helpers for recoverable agent and graph runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RunCheckpointStore:
    """Small JSON checkpoint store for recent agent runs."""

    history_dir: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "history_dir", self.history_dir.resolve())

    def save(self, record: dict[str, Any]) -> Path:
        """Save one run record and update the latest pointer."""

        self.history_dir.mkdir(parents=True, exist_ok=True)
        run_id = _normalize_run_id(record)
        record_path = self.history_dir / f"{run_id}.json"
        latest_path = self.history_dir / "latest.json"
        payload = json.dumps(record, ensure_ascii=False, indent=2)
        _write_text(record_path, payload)
        _write_text(latest_path, payload)
        return record_path

    def load_latest(self) -> dict[str, Any] | None:
        """Load the latest checkpoint if it exists."""

        return load_checkpoint(self.history_dir / "latest.json")


def build_run_checkpoint(
    *,
    run_id: str,
    run_kind: str,
    user_input: str,
    route: dict[str, Any],
    steps: list[dict[str, Any]],
    answer: str,
    trace: dict[str, Any],
    trace_text: str,
    tool_error: str | None = None,
    tool_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a JSON-ready checkpoint record for a single run."""

    return {
        "schema_version": 1,
        "run_id": run_id,
        "run_kind": run_kind,
        "created_at": _now_iso(),
        "user_input": user_input,
        "route": route,
        "steps": steps,
        "tool_result": tool_result,
        "tool_error": tool_error,
        "answer": answer,
        "trace": trace,
        "trace_text": trace_text,
    }


def build_graph_checkpoint(
    *,
    run_id: str,
    graph_state: dict[str, Any],
    graph_text: str,
) -> dict[str, Any]:
    """Build a JSON-ready checkpoint record for a LangGraph run."""

    return {
        "schema_version": 1,
        "run_id": run_id,
        "run_kind": "graph",
        "created_at": _now_iso(),
        "user_input": graph_state.get("question", ""),
        "route": {
            "action": graph_state.get("route"),
            "tool_name": graph_state.get("selected_tool"),
            "tool_input": graph_state.get("tool_input"),
            "reason": graph_state.get("route_reason"),
        },
        "steps": [{"title": step, "detail": step} for step in graph_state.get("steps", [])],
        "tool_result": {
            "tool_name": graph_state.get("selected_tool"),
            "output_preview": _preview_text(graph_state.get("answer", "")),
            "metadata": {
                key: graph_state.get(key)
                for key in ("tool_status", "tool_error", "skill_status", "skill_run", "recovery_plan")
                if graph_state.get(key) is not None
            },
        },
        "tool_error": graph_state.get("tool_error") or graph_state.get("error"),
        "answer": graph_state.get("answer", ""),
        "trace": graph_state,
        "trace_text": graph_text,
    }


def load_checkpoint(path: Path) -> dict[str, Any] | None:
    """Load a checkpoint JSON file if it exists."""

    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def format_checkpoint_summary(record: dict[str, Any]) -> str:
    """Render a compact summary for the latest checkpoint."""

    trace = record.get("trace", {}) if isinstance(record.get("trace"), dict) else {}
    route = trace.get("route", {}) if isinstance(trace.get("route"), dict) else record.get("route", {})
    if not isinstance(route, dict):
        route = {}
    answer_preview = _preview_text(record.get("answer", ""))
    return (
        f"Run ID: {record.get('run_id', 'unknown')}\n"
        f"Run kind: {record.get('run_kind', 'unknown')}\n"
        f"Created at: {record.get('created_at', 'unknown')}\n"
        f"User input: {record.get('user_input', '')}\n"
        f"Route: {route.get('action', 'unknown')} / {route.get('tool_name', 'none')}\n"
        f"Answer preview: {answer_preview}"
    )


def _normalize_run_id(record: dict[str, Any]) -> str:
    """Read a safe run id from a checkpoint record."""

    run_id = record.get("run_id")
    if isinstance(run_id, str) and run_id:
        return run_id
    return "unknown"


def _write_text(path: Path, content: str) -> None:
    """Write a text file atomically enough for local learning runs."""

    path.write_text(content, encoding="utf-8")


def _now_iso() -> str:
    """Return a UTC timestamp for checkpoint records."""

    return datetime.now(timezone.utc).isoformat()


def _preview_text(text: str, limit: int = 120) -> str:
    """Create a short preview for checkpoint summaries."""

    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 15] + "... (truncated)"
