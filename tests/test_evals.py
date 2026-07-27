"""Tests for deterministic eval runner."""

from pathlib import Path
import unittest  # Python 官方测试框架

from agent import WorkspaceAgent
from evals.runner import EvalCase, build_eval_report, load_eval_cases, run_eval_cases


class EvalRunnerTests(unittest.TestCase):
    """Verify regression eval loading and execution."""

    def test_load_eval_cases(self) -> None:
        cases = load_eval_cases(Path("evals/regression_cases.json"))

        self.assertGreaterEqual(len(cases), 5)
        self.assertEqual(cases[0].id, "direct-agent-difference")

    def test_run_eval_cases(self) -> None:
        cases = load_eval_cases(Path("evals/regression_cases.json"))
        results = run_eval_cases(WorkspaceAgent(Path(".")), cases)
        report = build_eval_report(results)

        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["passed"], report["total"])

        self.assertIn("total", report)
        self.assertIn("passed", report)
        self.assertIn("failed", report)
        self.assertIn("results", report)

    def test_eval_runner_reports_failed_case(self) -> None:
        cases = [
            EvalCase(
                id="bad-route",
                input="List MCP tools.",
                expected_route="direct_answer",
                expected_tool=None,
                required_answer_terms=["not-existing-term"],
            )
        ]
        results = run_eval_cases(WorkspaceAgent(Path(".")), cases)

        self.assertFalse(results[0].passed)
        self.assertGreaterEqual(len(results[0].failures), 2)
        self.assertIn("Expected route", ", ".join(results[0].failures))
        self.assertIn("Expected tool", ", ".join(results[0].failures))


if __name__ == "__main__":
    unittest.main()
