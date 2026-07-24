"""Rule-based routing for the minimal workspace agent."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ToolRoute:
    """Describes how the agent should handle a user request."""

    action: str
    tool_name: str | None = None
    tool_input: str | None = None
    reason: str = ""


FILE_PATTERN = re.compile(
    r"(?P<path>(?:[\w.\-]+/)*[\w.\-]+\.(?:md|txt|py|json|yaml|yml|toml|ini|cfg|csv|tsv|log))",
    re.IGNORECASE,
)


def _looks_like_directory_question(text: str) -> bool:
    """Return True when the user is likely asking about directories."""

    keywords = [
        "list dir",
        "list directory",
        "directory",
        "directories",
        "folder",
        "folders",
        "project structure",
    ]
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _looks_like_file_question(text: str) -> bool:
    """Return True when the user is likely asking about a file."""

    keywords = ["read", "show", "open", "summarize", "summarise", "inspect"]
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords) or bool(FILE_PATTERN.search(text))

def _looks_like_file_count_lines(text: str) -> bool:
    """Return True when the user is likely asking about a file and counting lines."""
    keywords = [
        "count lines",
        "count the lines",
        "count line",
        "line count",
        "line counts",
        "number of lines",
        "total lines",
        "lines count",
        "count the number of lines",
        "count the number of line",
        "how many lines",
        "how many line",
        "how many lines are",
        "how many line are",
        "how many lines in",
        "how many line in",
        "line count of",
        "number of lines in",
        "total number of lines",
        "total number of line",
        "lines in",
        "line in",
        "lines for",
        "line for",
    ]
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords) or bool(FILE_PATTERN.search(text))


def route_intent(user_input: str) -> ToolRoute:
    """Choose the simplest safe action for the current input.

    The router is intentionally rule-based for the first iteration so that the
    workflow is easy to inspect and later replace with model-based routing.
    """

    text = user_input.strip()
    match = FILE_PATTERN.search(text)

    if _looks_like_directory_question(text):
        return ToolRoute(
            action="use_tool",
            tool_name="list_dir",
            tool_input=".",
            reason="The user is asking about the directory or project structure.",
        )

    if "lines" in text.lower() and _looks_like_file_count_lines(text):
                return ToolRoute(
                    action="use_tool",
                    tool_name="count_lines",
                    tool_input=match.group("path") if match else ".",
                    reason="The user is asking to count the number of lines in a file.",
                )
    
    if "README" in text.upper() and _looks_like_file_question(text):
        return ToolRoute(
            action="use_tool",
            tool_name="read_file",
            tool_input="README.md",
            reason="The user mentioned README, so the agent should read that document.",
        )

    if match and _looks_like_file_question(text):
        return ToolRoute(
            action="use_tool",
            tool_name="read_file",
            tool_input=match.group("path"),
            reason="The user mentioned a file or document path.",
        )


    return ToolRoute(action="direct_answer", reason="The current request does not require a local tool.")
