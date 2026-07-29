"""Regression eval runner for the workspace agent."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from agent import AgentRun, WorkspaceAgent


@dataclass(frozen=True)
class EvalCase:
    """One deterministic regression case."""

    id: str  # 用例 ID
    input: str  # 用户输入
    expected_route: str  # 期望路由 action
    expected_tool: str | None  # 期望工具名
    required_answer_terms: list[str]  # 答案中必须出现的关键词
    expected_selected_tool: str | None = None  # tool_call 分支中期望 LLM 选择的实际工具


@dataclass(frozen=True)
class EvalResult:
    """Result of one evaluated case."""

    id: str  # 用例 ID
    passed: bool  # 是否通过
    failures: list[str]  # 失败原因
    route: str  # 实际路由 action
    tool_name: str | None  # 实际工具名
    selected_tool_name: str | None  # tool_call 分支中模型选择的实际工具
    answer_preview: str  # 答案摘要


def load_eval_cases(path: Path) -> list[EvalCase]:
    """Load eval cases from a JSON file."""

    data = json.loads(path.read_text(encoding="utf-8"))
    return [EvalCase(**item) for item in data]


def run_eval_cases(agent: WorkspaceAgent, cases: list[EvalCase]) -> list[EvalResult]:
    """Run all eval cases against the agent."""

    return [evaluate_case(agent, case) for case in cases]


def evaluate_case(agent: WorkspaceAgent, case: EvalCase) -> EvalResult:
    """Run one eval case and judge it with deterministic checks."""

    run = agent.run(case.input)
    failures = _check_run(run, case)
    return EvalResult(
        id=case.id,
        passed=not failures,
        failures=failures,
        route=run.route.action,
        tool_name=run.route.tool_name,
        selected_tool_name=run.tool_call.tool_name if run.tool_call else None,
        answer_preview=_preview(run.answer),
    )


def build_eval_report(results: list[EvalResult]) -> dict[str, Any]:
    """Build a JSON-serializable report."""

    passed = sum(1 for result in results if result.passed)
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": [asdict(result) for result in results],
    }


def _check_run(run: AgentRun, case: EvalCase) -> list[str]:
    """Return all deterministic failures for a run."""

    failures: list[str] = []
    if run.route.action != case.expected_route:
        failures.append(f"Expected route {case.expected_route}, got {run.route.action}")
    if run.route.tool_name != case.expected_tool:
        failures.append(f"Expected tool {case.expected_tool}, got {run.route.tool_name}")
    if case.expected_selected_tool is not None:
        selected_tool = run.tool_call.tool_name if run.tool_call else None
        if selected_tool != case.expected_selected_tool:
            failures.append(f"Expected selected tool {case.expected_selected_tool}, got {selected_tool}")
    lowered_answer = run.answer.lower()
    for term in case.required_answer_terms:
        if term.lower() not in lowered_answer:
            failures.append(f"Missing answer term: {term}")
    return failures


def _preview(text: str, limit: int = 180) -> str:
    """Return a compact single-line preview."""

    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 15] + "... (truncated)"
