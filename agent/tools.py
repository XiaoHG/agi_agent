"""Local tools available to the workspace agent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mcp import call_mcp_tool, list_mcp_tools
from rag import answer_question, answer_question_with_llm
from skills import describe_skills, select_skill
from subagent import build_collaboration_plan, describe_subagents

from .llm import LLMError


MAX_FILE_BYTES = 64_000


class ToolError(Exception):
    """Raised when a tool cannot safely complete the request."""


@dataclass(frozen=True)
class ToolResult:
    """Standard tool output wrapper."""

    tool_name: str
    output: str


def _resolve_within_root(root: Path, raw_path: str) -> Path:
    """Resolve a path and ensure it stays inside the workspace root."""

    root = root.resolve()
    candidate = (root / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path).resolve()
    if candidate == root:
        return candidate
    if root not in candidate.parents:
        raise ToolError(f"Path escapes workspace root: {raw_path}")
    return candidate


def read_file(root: Path, raw_path: str) -> ToolResult:
    """Read a text file from the workspace root."""

    path = _resolve_within_root(root, raw_path)
    if not path.exists():
        raise ToolError(f"File does not exist: {raw_path}")
    if not path.is_file():
        raise ToolError(f"Path is not a file: {raw_path}")
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise ToolError(f"File is too large to read: {raw_path} ({size} bytes)")

    text = path.read_text(encoding="utf-8", errors="replace")
    header = f"[read_file] {path.relative_to(root.resolve())}"
    return ToolResult("read_file", f"{header}\n{text}")


def list_dir(root: Path, raw_path: str = ".") -> ToolResult:
    """List a directory inside the workspace root."""

    path = _resolve_within_root(root, raw_path)
    if not path.exists():
        raise ToolError(f"Directory does not exist: {raw_path}")
    if not path.is_dir():
        raise ToolError(f"Path is not a directory: {raw_path}")

    items = []
    for child in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        suffix = "/" if child.is_dir() else ""
        items.append(f"- {child.name}{suffix}")
    header = f"[list_dir] {path.relative_to(root.resolve())}"
    body = "\n".join(items) if items else "- <empty>"
    return ToolResult("list_dir", f"{header}\n{body}")


def count_lines(root: Path, raw_path: str = ".") -> ToolResult:
    """Count the number of lines in a file inside the workspace root."""

    path = _resolve_within_root(root, raw_path)
    if not path.exists():
        raise ToolError(f"File does not exist: {raw_path}")
    if not path.is_file():
        raise ToolError(f"Path is not a file: {raw_path}")

    with path.open("r", encoding="utf-8", errors="replace") as f:
        line_count = sum(1 for _ in f)

    header = f"[count_lines] {path.relative_to(root.resolve())}"
    return ToolResult("count_lines", f"{header}\nLine count: {line_count}")


def search_docs(root: Path, question: str) -> ToolResult:
    """Search local project documents and return referenced context."""

    answer = answer_question(root, question)
    return ToolResult("search_docs", answer.to_text())


def answer_docs_with_llm(root: Path, question: str) -> ToolResult:
    """Answer from local project documents with DeepSeek-grounded RAG."""

    try:
        answer = answer_question_with_llm(root, question)
    except LLMError as error:
        raise ToolError(str(error)) from error
    return ToolResult("answer_docs_with_llm", answer.to_text())


def list_mcp_server_tools(root: Path) -> ToolResult:
    """List tools exposed through the local MCP adapter."""

    return ToolResult("list_mcp_tools", list_mcp_tools(root))


def mcp_workspace_summary(root: Path) -> ToolResult:
    """Call the local MCP workspace summary tool."""

    output = call_mcp_tool(root, "workspace_summary")
    return ToolResult("mcp_workspace_summary", output)


def list_agent_skills() -> ToolResult:
    """List reusable skills available to the agent."""

    return ToolResult("list_skills", describe_skills())


def plan_skill(task: str) -> ToolResult:
    """Select a skill for a task and explain the skill steps."""

    skill = select_skill(task)
    return ToolResult("plan_skill", skill.describe())


def list_project_subagents() -> ToolResult:
    """List subagents available in the project."""

    return ToolResult("list_subagents", describe_subagents())


def plan_subagent_collaboration(task: str) -> ToolResult:
    """Build a small subagent collaboration plan."""

    plan = build_collaboration_plan(task)
    return ToolResult("plan_subagents", plan.to_text())
