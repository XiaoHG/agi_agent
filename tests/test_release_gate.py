"""Tests for the release gate."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import unittest

from cli import release_gate as cli_release_gate
from evals.release_gate import (
    ReleaseCheckResult,
    ReleaseCheckSpec,
    ReleaseGateReport,
    format_release_gate_report,
    run_release_gate,
)


class ReleaseGateTests(unittest.TestCase):
    """Verify release gate orchestration and CLI wiring."""

    def test_default_release_gate_specs_cover_ci_checks(self) -> None:
        """Verify that default release gate specs cover ci checks."""
        from evals.release_gate import build_default_release_gate_specs

        specs = build_default_release_gate_specs(Path("."))

        self.assertEqual(len(specs), 4)
        self.assertEqual(specs[0].id, "unit-tests")
        self.assertEqual(specs[-1].id, "failure-bench")

    def test_release_gate_report_summarizes_checks(self) -> None:
        """Verify that release gate report summarizes checks."""
        specs = (
            ReleaseCheckSpec(id="ok", title="OK", command=("ok",)),
            ReleaseCheckSpec(id="bad", title="Bad", command=("bad",)),
        )

        def fake_executor(root: Path, spec: ReleaseCheckSpec) -> ReleaseCheckResult:
            """Verify that fake executor."""
            return ReleaseCheckResult(
                id=spec.id,
                title=spec.title,
                command=spec.command,
                description=spec.description,
                returncode=0 if spec.id == "ok" else 1,
                passed=spec.id == "ok",
                output_preview=f"output for {spec.id}",
            )

        report = run_release_gate(Path("."), specs=specs, executor=fake_executor)
        rendered = format_release_gate_report(report)

        self.assertFalse(report.release_ready)
        self.assertEqual(report.passed, 1)
        self.assertEqual(report.failed, 1)
        self.assertIn("Release gate report", rendered)
        self.assertIn("bad", rendered)

    def test_release_gate_cli_uses_report(self) -> None:
        """Verify that release gate cli uses report."""
        output = io.StringIO()
        original = cli_release_gate.run_release_gate
        try:
            cli_release_gate.run_release_gate = lambda root: ReleaseGateReport(
                name="fake",
                total_checks=1,
                passed=1,
                failed=0,
                release_ready=True,
                check_results=(
                    ReleaseCheckResult(
                        id="ok",
                        title="OK",
                        command=("ok",),
                        description="",
                        returncode=0,
                        passed=True,
                        output_preview="ok",
                    ),
                ),
            )
            with redirect_stdout(output):
                exit_code = cli_release_gate.main(["--root", "."])
        finally:
            cli_release_gate.run_release_gate = original

        self.assertEqual(exit_code, 0)
        self.assertIn("Release gate report", output.getvalue())


if __name__ == "__main__":
    unittest.main()
