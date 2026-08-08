"""Load prompt templates stored in the repository."""

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def load_prompt(relative_path: str) -> str:
    """Load a UTF-8 prompt file from the repository root."""

    return (ROOT_DIR / relative_path).read_text(encoding="utf-8")


def load_system_prompt() -> str:
    """Load the system prompt used by the workspace agent."""

    return load_prompt("prompts/v1_agent-system.md")


def load_tool_router_prompt() -> str:
    """Load the prompt that describes tool-selection behavior."""

    return load_prompt("prompts/v2_tool-router.md")


def load_tool_calling_prompt() -> str:
    """Load the prompt that instructs the LLM to emit structured tool calls."""

    return load_prompt("prompts/v15_tool-calling.md")


def load_tool_loop_synthesis_prompt() -> str:
    """Load the prompt that asks the LLM to synthesize tool-loop observations."""

    return load_prompt("prompts/v17_tool-loop-synthesis.md")


def load_langgraph_planner_prompt() -> str:
    """Load the prompt that asks the LLM to plan LangGraph execution."""

    return load_prompt("prompts/v28_langgraph-planner.md")


def load_direct_answer_prompt() -> str:
    """Load the prompt that asks the LLM to answer directly without tool use."""

    return load_prompt("prompts/v39_direct-answer.md")
