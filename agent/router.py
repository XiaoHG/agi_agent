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
        "目录",
        "文件夹",
        "项目结构",
        "有哪些主要目录",
        "列出目录",
        "查看目录",
        "list dir",
        "list directory",
    ]
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _looks_like_file_question(text: str) -> bool:
    """Return True when the user is likely asking about a file."""

    keywords = ["读取", "查看", "打开", "总结", "阅读", "read", "show", "summarize", "summarise"]
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
            reason="用户在询问目录结构或项目结构。",
        )

    if match and _looks_like_file_question(text):
        return ToolRoute(
            action="use_tool",
            tool_name="read_file",
            tool_input=match.group("path"),
            reason="用户明确提到了文件名或文档名。",
        )

    if "README" in text.upper() and _looks_like_file_question(text):
        return ToolRoute(
            action="use_tool",
            tool_name="read_file",
            tool_input="README.md",
            reason="用户提到了 README，通常需要读取文档。",
        )

    return ToolRoute(action="direct_answer", reason="当前问题不需要本地工具。")

