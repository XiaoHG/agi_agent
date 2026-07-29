"""Tests for deterministic eval runner."""

from pathlib import Path
import unittest  # Python 官方测试框架

from agent import WorkspaceAgent
from agent.llm import LLMResponse
from evals.runner import EvalCase, build_eval_report, load_eval_cases, run_eval_cases


class FakeToolCallingClient:
    """Minimal fake LLM client for eval tests."""

    def chat(self, messages):  # noqa: ANN001 - keep the test double flexible
        return LLMResponse(
            model="fake",
            content='{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"Inspect the README."}',
            raw={"messages": len(messages)},
        )


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

    def test_eval_runner_checks_selected_tool(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
