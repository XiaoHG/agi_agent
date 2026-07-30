"""LLM final synthesis for tool-loop observations."""

from __future__ import annotations

from .llm import DeepSeekLLMClient, LLMError, LLMMessage
from .tool_loop import ToolLoopResult


def build_tool_loop_synthesis_messages(result: ToolLoopResult, prompt: str) -> list[LLMMessage]:
    """Build messages for final synthesis from a completed tool loop."""

    step_blocks = []
    for step in result.steps:
        step_blocks.append(
            "\n".join(
                [
                    f"Step: {step.index}",
                    f"Action: {step.selection.action}",
                    f"Tool: {step.selection.tool_name or 'none'}",
                    f"Input: {step.selection.tool_input or 'none'}",
                    f"Reason: {step.selection.reason}",
                    f"Observation: {step.observation or 'none'}",
                    f"Error: {step.error or 'none'}",
                ]
            )
        )

    user_prompt = (
        f"Objective:\n{result.objective}\n\n"
        f"Stop reason:\n{result.stop_reason}\n\n"
        "Tool loop steps:\n"
        f"{chr(10).join(step_blocks) if step_blocks else 'none'}\n\n"
        "Generate the final user-facing answer."
    )
    return [
        LLMMessage(role="system", content=prompt),
        LLMMessage(role="user", content=user_prompt),
    ]


def synthesize_tool_loop_answer(
    client: DeepSeekLLMClient,
    result: ToolLoopResult,
    *,
    prompt: str,
) -> str:
    """Ask the LLM to synthesize a final answer from tool-loop observations."""

    response = client.chat(build_tool_loop_synthesis_messages(result, prompt))
    if not response.content.strip():
        raise LLMError("Tool-loop final synthesis returned an empty answer.")
    return response.content
