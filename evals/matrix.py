"""Industrial eval matrix and failure bench orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from agent import WorkspaceAgent

from .runner import build_eval_report, load_eval_cases, run_eval_cases


@dataclass(frozen=True)
class EvalSuiteSpec:
    """One suite inside an industrial eval matrix."""

    id: str                 # suite ID
    title: str              # suite 标题
    category: str           # suite 类别
    cases_path: str         # case 文件路径
    description: str = ""   # suite 说明


@dataclass(frozen=True)
class EvalMatrixSpec:
    """Top-level industrial eval matrix specification."""

    name: str  # matrix 名称
    suites: tuple[EvalSuiteSpec, ...]  # matrix 下的 suite 列表


@dataclass(frozen=True)
class EvalSuiteReport:
    """Aggregated report for one eval suite."""

    id: str                 # suite ID
    title: str              # suite 标题
    category: str           # suite 类别
    description: str        # suite 说明
    report: dict[str, Any]  # suite 内部 eval report

    def to_dict(self) -> dict[str, Any]:
        """Render the suite report as JSON-ready data."""

        return asdict(self)


@dataclass(frozen=True)
class EvalMatrixReport:
    """Aggregated report for a full eval matrix."""

    name: str           # matrix 名称
    total_suites: int   # suite 总数
    total_cases: int    # case 总数
    passed: int         # 通过用例数
    failed: int         # 失败用例数
    suite_reports: tuple[EvalSuiteReport, ...]  # 各 suite 报告

    def to_dict(self) -> dict[str, Any]:
        """Render the matrix report as JSON-ready data."""

        return {
            "name": self.name,
            "total_suites": self.total_suites,
            "total_cases": self.total_cases,
            "passed": self.passed,
            "failed": self.failed,
            "suite_reports": [suite.to_dict() for suite in self.suite_reports],
        }


def load_eval_matrix(path: Path) -> EvalMatrixSpec:
    """Load one eval matrix specification from JSON."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    suites = tuple(EvalSuiteSpec(**item) for item in payload.get("suites", []))
    return EvalMatrixSpec(name=str(payload.get("name", path.stem)), suites=suites)


def run_eval_matrix(root: Path, matrix: EvalMatrixSpec) -> EvalMatrixReport:
    """Run all suites defined by one eval matrix."""

    suite_reports: list[EvalSuiteReport] = []
    total_cases = 0
    passed = 0
    failed = 0

    for suite in matrix.suites:
        cases = load_eval_cases(root / suite.cases_path)
        agent = WorkspaceAgent(
            root,
            history_dir=root / "logs" / "eval-matrix" / suite.id / "runs",
            memory_dir=root / "logs" / "eval-matrix" / suite.id / "memory",
            session_id=f"eval-{suite.id}",
            task_id=f"{suite.id}-suite",
        )
        report = build_eval_report(run_eval_cases(agent, cases))
        suite_reports.append(
            EvalSuiteReport(
                id=suite.id,
                title=suite.title,
                category=suite.category,
                description=suite.description,
                report=report,
            )
        )
        total_cases += int(report["total"])
        passed += int(report["passed"])
        failed += int(report["failed"])

    return EvalMatrixReport(
        name=matrix.name,
        total_suites=len(matrix.suites),
        total_cases=total_cases,
        passed=passed,
        failed=failed,
        suite_reports=tuple(suite_reports),
    )


def format_eval_matrix_report(report: EvalMatrixReport) -> str:
    """Render a matrix report for CLI output."""

    lines = [
        "Industrial eval matrix report",
        f"Name: {report.name}",
        f"Suites: {report.total_suites}",
        f"Cases: {report.total_cases}",
        f"Passed: {report.passed}",
        f"Failed: {report.failed}",
        "",
        "Suite breakdown:",
    ]
    for suite in report.suite_reports:
        suite_report = suite.report
        lines.extend(
            [
                f"- {suite.id} [{suite.category}] {suite.title}",
                f"  Description: {suite.description or 'none'}",
                f"  Cases: {suite_report['total']}",
                f"  Passed: {suite_report['passed']}",
                f"  Failed: {suite_report['failed']}",
            ]
        )
    return "\n".join(lines)
