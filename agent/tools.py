"""Local tools available to the workspace agent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from mcp import call_mcp_tool_response, list_mcp_tools
from rag import answer_question, answer_question_with_llm, answer_question_with_vector_index
from skills import (
    SkillRuntimePolicy,
    SkillToolRequest,
    SkillToolResponse,
    build_default_skill_runtime_policy,
    describe_skills,
    execute_skill,
    evaluate_skill_runtime_policy,
    select_skill,
)
from subagent import build_collaboration_plan, describe_subagents

from .llm import LLMError


MAX_FILE_BYTES = 64_000
SKILL_NAME_PATTERN = re.compile(r"skill\s*[:=]\s*(?P<name>[A-Za-z0-9_.-]+)", re.IGNORECASE)
FILE_PATH_PATTERN = re.compile(
    r"(?P<path>(?:[\w.\-]+/)*[\w.\-]+\.(?:md|txt|py|json|yaml|yml|toml|ini|cfg|csv|tsv|log))",
    re.IGNORECASE,
)


class ToolError(Exception):
    """Raised when a tool cannot safely complete the request."""


@dataclass(frozen=True)
class ToolResult:
    """Standard tool output wrapper."""

    tool_name: str
    output: str
    metadata: dict[str, Any] | None = None


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


def search_vector_docs(root: Path, question: str) -> ToolResult:
    """Search local project documents through the vector index."""

    answer = answer_question_with_vector_index(root, question)
    return ToolResult(
        "search_vector_docs",
        answer.to_text(),
        {"citations": [result.citation() for result in answer.results]},
    )


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

    response = call_mcp_tool_response(root, "workspace_summary")
    status = "error" if response.is_error else "ok"
    return ToolResult(
        "mcp_workspace_summary",
        f"[mcp:{status}] {response.tool_name}\n{response.content}",
        response.metadata,
    )


def mcp_read_project_file(root: Path, raw_path: str) -> ToolResult:
    """Read a workspace file through the local MCP adapter."""

    resolved_path = _extract_workspace_path(raw_path) or raw_path
    response = call_mcp_tool_response(root, "read_project_file", {"path": resolved_path})
    status = "error" if response.is_error else "ok"
    return ToolResult(
        "mcp_read_project_file",
        f"[mcp:{status}] {response.tool_name}\n{response.content}",
        response.metadata,
    )


def mcp_write_project_file(root: Path, task: str) -> ToolResult:
    """Attempt to write a workspace file through the local MCP adapter."""

    arguments = _parse_mcp_write_task(task)
    response = call_mcp_tool_response(root, "write_project_file", arguments)
    status = "error" if response.is_error else "ok"
    return ToolResult(
        "mcp_write_project_file",
        f"[mcp:{status}] {response.tool_name}\n{response.content}",
        response.metadata,
    )


def list_agent_skills(root: Path = Path("."), policy: SkillRuntimePolicy | None = None) -> ToolResult:
    """List reusable skills available to the agent."""

    resolved_policy = policy or build_default_skill_runtime_policy()
    return ToolResult("list_skills", describe_skills(root, policy=resolved_policy))

def plan_skill(root: Path, task: str, policy: SkillRuntimePolicy | None = None) -> ToolResult:
    """Select a skill for a task and explain the skill steps."""

    resolved_policy = policy or build_default_skill_runtime_policy()
    skill = select_skill(task, root=root, skill_name=_extract_skill_name(task))
    decision = evaluate_skill_runtime_policy(skill, resolved_policy)
    return ToolResult(
        "plan_skill",
        f"{resolved_policy.describe()}\n\nPolicy decision: {'allowed' if decision.allowed else 'blocked'}\n"
        f"Reason: {decision.reason}\n\n{skill.describe()}",
    )


def run_skill(task: str, root: Path = Path("."), policy: SkillRuntimePolicy | None = None) -> ToolResult:
    """Execute a selected skill with workspace tool support."""

    skill_run = execute_skill(
        task,
        tool_runner=_build_skill_tool_runner(root),
        root=root,
        skill_name=_extract_skill_name(task),
        policy=policy or build_default_skill_runtime_policy(),
    )
    return ToolResult("execute_skill", skill_run.to_text(), {"skill_run": skill_run.to_dict()})


def run_skill_with_workspace(
    root: Path,
    task: str,
    policy: SkillRuntimePolicy | None = None,
) -> ToolResult:
    """Execute a selected skill with access to workspace tools."""

    skill_run = execute_skill(
        task,
        tool_runner=_build_skill_tool_runner(root),
        root=root,
        skill_name=_extract_skill_name(task),
        policy=policy or build_default_skill_runtime_policy(),
    )
    return ToolResult("execute_skill", skill_run.to_text(), {"skill_run": skill_run.to_dict()})


def _build_skill_tool_runner(root: Path):
    """Build the small tool runner used by tool-backed skill steps."""

    def runner(request: SkillToolRequest) -> SkillToolResponse:
        try:
            if request.tool_name == "list_dir":
                result = list_dir(root, request.tool_input or ".")
            elif request.tool_name == "read_file":
                result = read_file(root, request.tool_input)
            elif request.tool_name == "search_docs":
                result = search_docs(root, request.tool_input)
            elif request.tool_name == "list_mcp_tools":
                result = list_mcp_server_tools(root)
            elif request.tool_name == "mcp_workspace_summary":
                result = mcp_workspace_summary(root)
            else:
                return SkillToolResponse(request.tool_name, f"Unsupported skill tool: {request.tool_name}", True)
        except ToolError as error:
            return SkillToolResponse(request.tool_name, str(error), True)
        return SkillToolResponse(result.tool_name, result.output)

    return runner


def list_project_subagents() -> ToolResult:
    """List subagents available in the project."""

    return ToolResult("list_subagents", describe_subagents())


def plan_subagent_collaboration(task: str) -> ToolResult:
    """Build a small subagent collaboration plan."""

    plan = build_collaboration_plan(task)
    return ToolResult("plan_subagents", plan.to_text())


def _extract_skill_name(task: str) -> str | None:
    """Extract an explicit skill name from task text when present."""

    match = SKILL_NAME_PATTERN.search(task)
    if match:
        return match.group("name")
    return None


def _parse_mcp_write_task(task: str) -> dict[str, str]:
    """Extract file path and content from a natural-language MCP write task."""

    path_match = FILE_PATH_PATTERN.search(task)
    path = path_match.group("path") if path_match else ""
    lowered = task.lower()
    content = ""
    markers = ["content:", "with content ", "with "]
    for marker in markers:
        if marker in lowered:
            start = lowered.index(marker) + len(marker)
            content = task[start:].strip().strip("\"'")
            break
    return {
        "path": path,
        "content": content.rstrip("."),
    }


def _extract_workspace_path(text: str) -> str | None:
    """Extract the first workspace-like file path from free-form text."""

    match = FILE_PATH_PATTERN.search(text)
    if match:
        return match.group("path")
    return None
