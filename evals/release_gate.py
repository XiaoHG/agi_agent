"""Release gate orchestration for CI readiness.

This module models a local, deterministic release gate. The project does not
yet assume a hosted CI platform, but it already defines the set of checks that
must pass before a version is considered release-ready:

- unit tests
- regression eval
- industrial evaluation matrix
- failure bench

That makes this file the bridge between learning code and production-style
delivery discipline.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence


@dataclass(frozen=True)
class ReleaseCheckSpec:
    """One deterministic release gate check."""

    id: str                     # 检查 ID
    title: str                  # 检查标题
    command: tuple[str, ...]    # 需要执行的命令
    description: str = ""       # 检查说明


@dataclass(frozen=True)
class ReleaseCheckResult:
    """Execution result for one release check."""

    id: str                     # 检查 ID
    title: str                  # 检查标题
    command: tuple[str, ...]    # 实际执行的命令
    description: str            # 检查说明
    returncode: int             # 进程返回码
    passed: bool                # 是否通过
    output_preview: str         # 输出摘要


@dataclass(frozen=True)
class ReleaseGateReport:
    """Aggregated release gate report."""

    name: str               # 门禁名称
    total_checks: int       # 检查总数
    passed: int             # 通过数
    failed: int             # 失败数
    release_ready: bool     # 是否满足发布条件
    check_results: tuple[ReleaseCheckResult, ...]  # 各项检查结果

    def to_dict(self) -> dict[str, object]:
        """Render the report as JSON-ready data."""

        return asdict(self)


def build_default_release_gate_specs(_root: Path) -> tuple[ReleaseCheckSpec, ...]:
    """Build the default release checks that approximate a CI gate."""

    python = sys.executable
    return (
        ReleaseCheckSpec(
            id="unit-tests",
            title="Unit tests",
            command=(python, "-m", "unittest", "discover", "-s", "tests", "-q"),
            description="Run the deterministic project unit test suite.",
        ),
        ReleaseCheckSpec(
            id="regression-eval",
            title="Regression eval",
            command=(python, "-m", "cli.eval_runner"),
            description="Run the default regression eval cases.",
        ),
        ReleaseCheckSpec(
            id="industrial-matrix",
            title="Industrial eval matrix",
            command=(python, "-m", "cli.eval_runner", "--matrix", "evals/industrial_eval_matrix.json"),
            description="Run the layered industrial eval matrix.",
        ),
        ReleaseCheckSpec(
            id="failure-bench",
            title="Failure bench",
            command=(python, "-m", "cli.eval_runner", "--failure-bench", "evals/industrial_failure_bench.json"),
            description="Run the known failure-path benchmark.",
        ),
    )


def run_release_gate(
    root: Path,
    specs: Sequence[ReleaseCheckSpec] | None = None,
    executor: Callable[[Path, ReleaseCheckSpec], ReleaseCheckResult] | None = None,
) -> ReleaseGateReport:
    """Run all configured checks and aggregate the release decision.

    The caller may inject a custom executor during tests so the orchestration
    can be validated without launching real subprocesses.
    """

    selected_specs = tuple(specs or build_default_release_gate_specs(root))
    run_executor = executor or execute_release_check
    results = tuple(run_executor(root, spec) for spec in selected_specs)
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed
    return ReleaseGateReport(
        name="release-gate",
        total_checks=len(results),
        passed=passed,
        failed=failed,
        release_ready=failed == 0,
        check_results=results,
    )


def execute_release_check(root: Path, spec: ReleaseCheckSpec) -> ReleaseCheckResult:
    """Execute one release gate check via subprocess."""

    completed = subprocess.run(
        spec.command,
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    return ReleaseCheckResult(
        id=spec.id,
        title=spec.title,
        command=spec.command,
        description=spec.description,
        returncode=completed.returncode,
        passed=completed.returncode == 0,
        output_preview=_preview(output),
    )


def format_release_gate_report(report: ReleaseGateReport) -> str:
    """Render a human-readable release gate report."""

    lines = [
        "Release gate report",
        f"Name: {report.name}",
        f"Checks: {report.total_checks}",
        f"Passed: {report.passed}",
        f"Failed: {report.failed}",
        f"Release ready: {'yes' if report.release_ready else 'no'}",
        "",
        "Check breakdown:",
    ]
    for result in report.check_results:
        lines.extend(
            [
                f"- {result.id} {result.title}",
                f"  Description: {result.description or 'none'}",
                f"  Command: {' '.join(result.command)}",
                f"  Return code: {result.returncode}",
                f"  Status: {'passed' if result.passed else 'failed'}",
            ]
        )
        if not result.passed and result.output_preview:
            lines.append(f"  Output: {result.output_preview}")
    return "\n".join(lines)


def _preview(text: str, limit: int = 220) -> str:
    """Return a compact single-line preview."""

    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 15] + "... (truncated)"
