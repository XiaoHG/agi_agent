"""Regression and benchmark eval runner for the workspace agent."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any

from agent import AgentRun, WorkspaceAgent


@dataclass(frozen=True)
class EvalCase:
    """One deterministic eval case."""

    id: str             # 用例 ID
    input: str = ""     # 用户输入
    expected_route: str | None = None   # 期望路由 action
    expected_tool: str | None = None    # 期望工具名
    required_answer_terms: list[str] = field(default_factory=list)  # 输出中必须出现的关键词
    expected_selected_tool: str | None = None   # tool_call 分支中期望模型选择的实际工具
    category: str = "regression"                # 用例类别，例如 route / tool / skill / recovery / replay
    operation: str = "agent_run"                # 执行入口，例如 agent_run / replay_latest_checkpoint
    setup_inputs: list[str] = field(default_factory=list)  # 在正式评估前先执行的输入


@dataclass(frozen=True)
class EvalResult:
    """Result of one evaluated case."""

    id: str                         # 用例 ID
    category: str                   # 用例类别
    operation: str                  # 执行入口
    passed: bool                    # 是否通过
    failures: list[str]             # 失败原因
    route: str | None               # 实际路由 action
    tool_name: str | None           # 实际工具名
    selected_tool_name: str | None  # tool_call 分支中模型选择的实际工具
    answer_preview: str             # 输出摘要


def load_eval_cases(path: Path) -> list[EvalCase]:
    """Load eval cases from a JSON file."""

    data = json.loads(path.read_text(encoding="utf-8"))
    return [EvalCase(**item) for item in data]


def run_eval_cases(agent: WorkspaceAgent, cases: list[EvalCase]) -> list[EvalResult]:
    """Run all eval cases against the agent."""

    return [evaluate_case(agent, case) for case in cases]


def evaluate_case(agent: WorkspaceAgent, case: EvalCase) -> EvalResult:
    """Run one eval case and judge it with deterministic checks."""

    run, output_text = _execute_case(agent, case)
    failures = _check_case(run, output_text, case)
    return EvalResult(
        id=case.id,
        category=case.category,
        operation=case.operation,
        passed=not failures,
        failures=failures,
        route=None if run is None else run.route.action,
        tool_name=None if run is None else run.route.tool_name,
        selected_tool_name=run.tool_call.tool_name if run is not None and run.tool_call else None,
        answer_preview=_preview(output_text),
    )


def build_eval_report(results: list[EvalResult]) -> dict[str, Any]:
    """Build a JSON-serializable report."""

    passed = sum(1 for result in results if result.passed)
    by_category = _build_count_by_key(results, "category")
    by_operation = _build_count_by_key(results, "operation")
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "by_category": by_category,
        "by_operation": by_operation,
        "results": [asdict(result) for result in results],
    }


def _execute_case(agent: WorkspaceAgent, case: EvalCase) -> tuple[AgentRun | None, str]:
    """Execute one eval case through the selected entrypoint."""

    for setup_input in case.setup_inputs:
        agent.run(setup_input)

    if case.operation == "agent_run":
        run = agent.run(case.input)
        return run, run.answer
    if case.operation == "replay_latest_checkpoint":
        return None, agent.replay_latest_checkpoint()
    if case.operation == "compare_latest_two_checkpoints":
        return None, agent.compare_latest_two_checkpoints()
    if case.operation == "resume_latest_checkpoint":
        return None, agent.resume_latest_checkpoint()
    raise ValueError(f"Unsupported eval operation: {case.operation}")


def _check_case(run: AgentRun | None, output_text: str, case: EvalCase) -> list[str]:
    """Return all deterministic failures for a case output."""

    failures: list[str] = []
    if case.expected_route is not None:
        actual_route = None if run is None else run.route.action
        if actual_route != case.expected_route:
            failures.append(f"Expected route {case.expected_route}, got {actual_route}")
    if case.expected_tool != actual_tool_name(run):
        failures.append(f"Expected tool {case.expected_tool}, got {actual_tool_name(run)}")
    if case.expected_selected_tool is not None:
        selected_tool = run.tool_call.tool_name if run is not None and run.tool_call else None
        if selected_tool != case.expected_selected_tool:
            failures.append(f"Expected selected tool {case.expected_selected_tool}, got {selected_tool}")
    lowered_output = output_text.lower()
    for term in case.required_answer_terms:
        if term.lower() not in lowered_output:
            failures.append(f"Missing answer term: {term}")
    return failures


def actual_tool_name(run: AgentRun | None) -> str | None:
    """Read the routed tool name from an AgentRun when available."""

    return None if run is None else run.route.tool_name


def _build_count_by_key(results: list[EvalResult], key: str) -> dict[str, dict[str, int]]:
    """Build pass/fail counts grouped by one result field."""

    summary: dict[str, dict[str, int]] = {}
    for result in results:
        label = str(getattr(result, key))
        bucket = summary.setdefault(label, {"total": 0, "passed": 0, "failed": 0})
        bucket["total"] += 1
        if result.passed:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1
    return summary


def _preview(text: str, limit: int = 180) -> str:
    """Return a compact single-line preview."""

    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 15] + "... (truncated)"
