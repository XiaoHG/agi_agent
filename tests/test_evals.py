"""Tests for deterministic eval runner."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import unittest  # Python 官方测试框架

from agent import WorkspaceAgent
from agent.llm import LLMResponse
from cli import eval_runner as cli_eval_runner
from evals.matrix import format_eval_matrix_report, load_eval_matrix, run_eval_matrix
from evals.runner import EvalCase, build_eval_report, load_eval_cases, run_eval_cases


class FakeToolCallingClient:
    """Minimal fake LLM client for eval tests."""

    def chat(self, messages):  # noqa: ANN001 - keep the test double flexible
        """Return a deterministic chat response used by the surrounding test or fake client."""
        return LLMResponse(
            model="fake",
            content='{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"Inspect the README."}',
            raw={"messages": len(messages)},
        )


class EvalRunnerTests(unittest.TestCase):
    """Verify regression eval loading and execution."""

    def test_load_eval_cases(self) -> None:
        """Verify that load eval cases."""
        cases = load_eval_cases(Path("evals/regression_cases.json"))

        self.assertGreaterEqual(len(cases), 5)
        self.assertEqual(cases[0].id, "direct-agent-difference")

    def test_run_eval_cases(self) -> None:
        """Verify that run eval cases."""
        cases = load_eval_cases(Path("evals/regression_cases.json"))
        results = run_eval_cases(WorkspaceAgent(Path(".")), cases)
        report = build_eval_report(results)

        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["passed"], report["total"])

        self.assertIn("total", report)
        self.assertIn("passed", report)
        self.assertIn("failed", report)
        self.assertIn("results", report)
        self.assertIn("by_category", report)
        self.assertIn("by_operation", report)

    def test_eval_runner_reports_failed_case(self) -> None:
        """Verify that eval runner reports failed case."""
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

    def test_eval_runner_checks_selected_tool(self) -> None:
        """Verify that eval runner checks selected tool."""
        case = EvalCase(
            id="tool-call-readme",
            input="Use tool calling to read README.md.",
            expected_route="tool_call",
            expected_tool="llm_tool_selector",
            expected_selected_tool="read_file",
            required_answer_terms=["Result: read README.md"],
        )
        agent = WorkspaceAgent(Path("."), llm_client=FakeToolCallingClient())

        results = run_eval_cases(agent, [case])

        self.assertTrue(results[0].passed)
        self.assertEqual(results[0].selected_tool_name, "read_file")

    def test_load_eval_matrix(self) -> None:
        """Verify that load eval matrix."""
        matrix = load_eval_matrix(Path("evals/industrial_eval_matrix.json"))

        self.assertEqual(matrix.name, "industrial-eval-matrix")
        self.assertGreaterEqual(len(matrix.suites), 5)
        self.assertEqual(matrix.suites[0].id, "route")

    def test_run_eval_matrix(self) -> None:
        """Verify that run eval matrix."""
        matrix = load_eval_matrix(Path("evals/industrial_eval_matrix.json"))
        report = run_eval_matrix(Path("."), matrix)
        rendered = format_eval_matrix_report(report)

        self.assertEqual(report.failed, 0)
        self.assertGreaterEqual(report.total_suites, 5)
        self.assertGreaterEqual(report.total_cases, 10)
        self.assertIn("Industrial eval matrix report", rendered)
        self.assertIn("Suite breakdown:", rendered)

    def test_run_failure_bench(self) -> None:
        """Verify that run failure bench."""
        matrix = load_eval_matrix(Path("evals/industrial_failure_bench.json"))
        report = run_eval_matrix(Path("."), matrix)

        self.assertEqual(report.failed, 0)
        self.assertEqual(report.total_suites, 1)
        self.assertGreaterEqual(report.total_cases, 5)

    def test_cli_eval_runner_can_run_matrix(self) -> None:
        """Verify that cli eval runner can run matrix."""
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = cli_eval_runner.main(["--matrix", "evals/industrial_eval_matrix.json"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Industrial eval matrix report", output.getvalue())

    def test_cli_eval_runner_can_run_failure_bench(self) -> None:
        """Verify that cli eval runner can run failure bench."""
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = cli_eval_runner.main(["--failure-bench", "evals/industrial_failure_bench.json"])

        self.assertEqual(exit_code, 0)
        self.assertIn("Industrial eval matrix report", output.getvalue())


if __name__ == "__main__":
    unittest.main()
