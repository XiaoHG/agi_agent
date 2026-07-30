"""Tests for bounded LLM tool loops."""

from pathlib import Path
import unittest

from agent import WorkspaceAgent
from agent.llm import LLMResponse


class SequenceToolLoopClient:
    """Fake LLM client that returns one structured response per call."""

    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls = 0

    def chat(self, messages):  # noqa: ANN001 - test double keeps the signature flexible
        response = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return LLMResponse(model="fake", content=response, raw={"messages": len(messages)})


class ToolLoopTests(unittest.TestCase):
    """Verify multi-step tool loop behavior."""

    def test_workspace_agent_runs_two_step_tool_loop(self) -> None:
        client = SequenceToolLoopClient(
            [
                '{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"Read the file first."}',
                '{"action":"answer_directly","tool_name":null,"tool_input":null,"reason":"The README observation is enough."}',
                "The README was read successfully, so the tool loop has enough evidence to answer.",
            ]
        )
        agent = WorkspaceAgent(Path("."), llm_client=client)

        run = agent.run("Use tool loop to read README.md and then answer.")

        self.assertEqual(run.route.action, "tool_loop")
        self.assertIsNotNone(run.tool_loop_result)
        self.assertEqual(run.tool_loop_result.stop_reason if run.tool_loop_result else "", "model_answered_directly")
        self.assertEqual(run.tool_loop_result.final_answer_source if run.tool_loop_result else "", "llm")
        self.assertEqual(len(run.tool_loop_result.steps) if run.tool_loop_result else 0, 2)
        self.assertIn("read_file", run.answer)
        self.assertIn("The README was read successfully", run.answer)

    def test_tool_loop_stops_on_repeated_tool_call(self) -> None:
        client = SequenceToolLoopClient(
            [
                '{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"Read the file."}',
                '{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"Read the same file again."}',
                "The loop stopped because the model repeated the same read_file call.",
            ]
        )
        agent = WorkspaceAgent(Path("."), llm_client=client)

        run = agent.run("Use tool loop to read README.md and then answer.")

        self.assertIsNotNone(run.tool_loop_result)
        self.assertEqual(run.tool_loop_result.stop_reason if run.tool_loop_result else "", "repeated_tool_call")
        self.assertIn("repeated the same read_file call", run.answer)

    def test_tool_loop_trace_dict_contains_steps(self) -> None:
        client = SequenceToolLoopClient(
            [
                '{"action":"use_tool","tool_name":"count_lines","tool_input":"README.md","reason":"Count the README lines."}',
                '{"action":"answer_directly","tool_name":null,"tool_input":null,"reason":"Line count is enough."}',
                "README.md has a verified line count observation.",
            ]
        )
        agent = WorkspaceAgent(Path("."), llm_client=client)

        trace = agent.to_trace_dict(agent.run("Use tool loop to count lines in README.md and answer."))

        self.assertEqual(trace["route"]["action"], "tool_loop")
        self.assertEqual(trace["tool_loop"]["step_count"], 2)
        self.assertEqual(trace["tool_loop"]["stop_reason"], "model_answered_directly")
        self.assertEqual(trace["tool_loop"]["final_answer_source"], "llm")

    def test_tool_loop_keeps_deterministic_fallback_when_synthesis_fails(self) -> None:
        client = SequenceToolLoopClient(
            [
                '{"action":"use_tool","tool_name":"count_lines","tool_input":"README.md","reason":"Count the README lines."}',
                '{"action":"answer_directly","tool_name":null,"tool_input":null,"reason":"Line count is enough."}',
                "",
            ]
        )
        agent = WorkspaceAgent(Path("."), llm_client=client)

        run = agent.run("Use tool loop to count lines in README.md and answer.")

        self.assertIsNotNone(run.tool_loop_result)
        self.assertEqual(
            run.tool_loop_result.final_answer_source if run.tool_loop_result else "",
            "deterministic_fallback",
        )
        self.assertIn("Final synthesis fallback reason", run.answer)


if __name__ == "__main__":
    unittest.main()
