"""Tests for LLM final synthesis from tool-loop observations."""

import unittest

from agent.llm import LLMResponse
from agent.tool_calling import ToolCallSelection
from agent.tool_loop import ToolLoopResult, ToolLoopStep
from agent.tool_synthesis import build_tool_loop_synthesis_messages, synthesize_tool_loop_answer


class FakeSynthesisClient:
    """Minimal fake client for final synthesis tests."""

    def chat(self, messages):  # noqa: ANN001 - test double keeps the signature flexible
        """Return a deterministic chat response used by the surrounding test or fake client."""
        return LLMResponse(model="fake", content="Final answer from observations.", raw={"messages": len(messages)})


class ToolSynthesisTests(unittest.TestCase):
    """Verify final synthesis prompt construction and execution."""

    def test_build_tool_loop_synthesis_messages_includes_observations(self) -> None:
        """Verify that build tool loop synthesis messages includes observations."""
        result = _build_sample_loop_result()

        messages = build_tool_loop_synthesis_messages(result, "Synthesis prompt")

        self.assertEqual(messages[0].role, "system")
        self.assertIn("Synthesis prompt", messages[0].content)
        self.assertIn("count lines in README.md", messages[1].content)
        self.assertIn("Line count: 609", messages[1].content)
        self.assertIn("model_answered_directly", messages[1].content)

    def test_synthesize_tool_loop_answer_returns_llm_content(self) -> None:
        """Verify that synthesize tool loop answer returns llm content."""
        answer = synthesize_tool_loop_answer(
            FakeSynthesisClient(),  # type: ignore[arg-type]
            _build_sample_loop_result(),
            prompt="Synthesis prompt",
        )

        self.assertEqual(answer, "Final answer from observations.")


def _build_sample_loop_result() -> ToolLoopResult:
    """Build a deterministic loop result for synthesis tests."""

    return ToolLoopResult(
        objective="count lines in README.md",
        steps=[
            ToolLoopStep(
                index=1,
                selection=ToolCallSelection(
                    action="use_tool",
                    tool_name="count_lines",
                    tool_input="README.md",
                    reason="Count lines.",
                    raw_response="{}",
                ),
                observation="[count_lines] README.md Line count: 609",
            )
        ],
        final_answer="Deterministic fallback answer.",
        stop_reason="model_answered_directly",
    )


if __name__ == "__main__":
    unittest.main()

