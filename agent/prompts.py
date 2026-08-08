"""Load prompt templates stored in the repository."""

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_prompt(relative_path: str) -> str:
    """Load a UTF-8 prompt file from the repository root."""

    return (ROOT_DIR / relative_path).read_text(encoding="utf-8")


def load_system_prompt() -> str:
    """Load the system prompt used by the workspace agent."""

    return load_prompt("prompts/agent-system.v1.md")


def load_tool_router_prompt() -> str:
    """Load the prompt that describes tool-selection behavior."""

    return load_prompt("prompts/tool-router.v1.md")


def load_tool_calling_prompt() -> str:
    """Load the prompt that instructs the LLM to emit structured tool calls."""

    return load_prompt("prompts/tool-calling.v1.md")


def load_tool_loop_synthesis_prompt() -> str:
    """Load the prompt that asks the LLM to synthesize tool-loop observations."""

    return load_prompt("prompts/tool-loop-synthesis.v1.md")


def load_langgraph_planner_prompt() -> str:
    """Load the prompt that asks the LLM to plan LangGraph execution."""

    return load_prompt("prompts/langgraph-planner.v1.md")


def load_direct_answer_prompt() -> str:
    """Load the prompt that asks the LLM to answer directly without tool use."""

    return load_prompt("prompts/direct-answer.v1.md")
