"""LLM-first direct answer helpers with deterministic fallback."""

from __future__ import annotations

from dataclasses import dataclass

from .llm import DeepSeekLLMClient, LLMMessage


@dataclass(frozen=True)
class DirectAnswerResult:
    """Structured direct-answer result shared by classic and graph runtimes."""

    answer: str
    source: str  # llm / deterministic_fallback
    status: str  # completed / fallback
    error: str = ""

    def to_dict(self) -> dict[str, str]:
        """Render the result as JSON-ready data."""

        return {
            "answer": self.answer,
            "source": self.source,
            "status": self.status,
            "error": self.error,
        }


def build_direct_answer_messages(user_input: str, prompt: str) -> list[LLMMessage]:
    """Build the LLM messages for top-level direct answers."""

    user_prompt = (
        "User request:\n"
        f"{user_input}\n\n"
        "Answer directly without claiming you inspected local files unless the request already includes that context. "
        "If the request truly needs local project inspection, say so plainly instead of inventing file evidence."
    )
    return [
        LLMMessage(role="system", content=prompt),
        LLMMessage(role="user", content=user_prompt),
    ]


def answer_directly(
    user_input: str,
    *,
    prompt: str,
    client: DeepSeekLLMClient | None = None,
) -> DirectAnswerResult:
    """Use an LLM-first direct answer path with deterministic fallback."""

    resolved_client = client
    if resolved_client is None:
        return DirectAnswerResult(
            answer=compose_direct_answer_fallback(user_input),
            source="deterministic_fallback",
            status="fallback",
            error="Direct-answer client was not provided.",
        )

    try:
        response = resolved_client.chat(build_direct_answer_messages(user_input, prompt))
    except Exception as error:
        return DirectAnswerResult(
            answer=compose_direct_answer_fallback(user_input),
            source="deterministic_fallback",
            status="fallback",
            error=str(error),
        )

    content = response.content.strip()
    if not content:
        return DirectAnswerResult(
            answer=compose_direct_answer_fallback(user_input),
            source="deterministic_fallback",
            status="fallback",
            error="Direct-answer response was empty.",
        )
    return DirectAnswerResult(answer=content, source="llm", status="completed")


def compose_direct_answer_fallback(user_input: str) -> str:
    """Provide the deterministic fallback used when direct-answer LLM is unavailable."""

    text = user_input.lower()
    if "agent" in text and ("chat" in text or "chatbot" in text) and ("difference" in text or "different" in text):
        return (
            "Result: the main difference is that an agent makes task-oriented decisions, can call tools, can keep state, "
            "and can complete work through multiple steps.\n\n"
            "Reason: a chatbot is mostly a text responder, while an agent is closer to an execution loop that moves a task toward completion.\n\n"
            "In this project: start with the minimal loop, then add state, RAG, MCP, skills, and subagents.\n\n"
            "Next step: run the CLI with trace enabled and inspect each recorded step."
        )
    if "why" in text:
        return (
            "Result: start from engineering boundaries before adding frameworks.\n\n"
            "Reason: agent systems usually fail around tool boundaries, state transitions, and missing evaluation, not only around model quality.\n\n"
            "In this project: first make the minimal loop work, then add RAG, MCP, skills, and subagents incrementally.\n\n"
            "Next step: split the question into concept, implementation, and verification layers."
        )
    return (
        "Result: this request does not require a local tool, so the agent answered directly.\n\n"
        "Reason: the current version focuses on the minimal agent loop rather than broad knowledge coverage.\n\n"
        "In this project: use tool calls when the request involves project files, directory structure, or specific documents.\n\n"
        "Next step: ask the agent to read README.md or list the project directory if you want it to inspect local content."
    )
