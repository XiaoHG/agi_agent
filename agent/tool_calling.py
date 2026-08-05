"""LLM-assisted tool selection for the workspace agent."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from .llm import DeepSeekLLMClient, LLMError, LLMMessage
from .tool_schema import ToolSpec


@dataclass(frozen=True)
class ToolCallSelection:
    """Structured decision returned by the tool-calling LLM prompt."""

    action: str               # 动作：use_tool / answer_directly / ask_clarification
    tool_name: str | None     # 选中的工具名（仅 action=use_tool 时有）
    tool_input: str | None    # 工具参数（仅 action=use_tool 时有）
    reason: str               # LLM 选择的理由
    raw_response: str         # 原始 LLM 响应（用于调试）


def build_tool_calling_messages(user_input: str, tool_specs: list[ToolSpec], prompt: str) -> list[LLMMessage]:
    """Build the messages sent to the LLM for structured tool selection."""

    catalog = "\n\n".join(spec.to_prompt_block() for spec in tool_specs)
    user_prompt = (
        f"User input:\n{user_input}\n\n"
        "Available tools:\n"
        f"{catalog}\n\n"
        "Return one JSON object with the keys action, tool_name, tool_input, and reason.\n"
        "Choose the smallest sufficient action."
    )
    return [
        LLMMessage(role="system", content=prompt),
        LLMMessage(role="user", content=user_prompt),
    ]


def select_tool_call(
    client: DeepSeekLLMClient,
    user_input: str,
    tool_specs: list[ToolSpec],
    *,
    prompt: str,
) -> ToolCallSelection:
    """Ask the LLM to choose a structured tool action."""

    response = client.chat(build_tool_calling_messages(user_input, tool_specs, prompt))
    selection = parse_tool_call_selection(response.content)
    return normalize_tool_call_selection(selection, user_input)


def normalize_tool_call_selection(selection: ToolCallSelection, user_input: str) -> ToolCallSelection:
    """Fill in missing tool input with deterministic heuristics."""

    if selection.action != "use_tool":
        return selection

    if selection.tool_name in _NO_ARGUMENT_TOOLS:
        return ToolCallSelection(
            action=selection.action,
            tool_name=selection.tool_name,
            tool_input=None,
            reason=selection.reason,
            raw_response=selection.raw_response,
        )

    normalized_input = selection.tool_input
    # 如果 tool_input 是空或像指令文本（如 "read README.md"），则推断参数
    if not normalized_input or _looks_like_instruction_text(normalized_input):
        normalized_input = _infer_tool_input(selection.tool_name, user_input)

    if normalized_input == selection.tool_input:
        return selection

    return ToolCallSelection(
        action=selection.action,
        tool_name=selection.tool_name,
        tool_input=normalized_input,
        reason=selection.reason,
        raw_response=selection.raw_response,
    )


def parse_tool_call_selection(raw_response: str) -> ToolCallSelection:
    """Parse the JSON response returned by the tool-calling prompt."""

    payload = _parse_json_object(raw_response)
    action = payload.get("action")
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    reason = payload.get("reason")

    if action not in {"use_tool", "answer_directly", "ask_clarification"}:
        raise LLMError(f"Invalid tool-calling action: {action}")
    if not isinstance(reason, str) or not reason.strip():
        raise LLMError("Tool-calling response is missing a reason.")

    normalized_tool_name = tool_name if isinstance(tool_name, str) and tool_name.strip() else None
    normalized_tool_input = tool_input if isinstance(tool_input, str) and tool_input.strip() else None
    if action == "use_tool" and not normalized_tool_name:
        raise LLMError("Tool-calling response is missing tool_name for use_tool.")
    if action != "use_tool":
        normalized_tool_name = None
        normalized_tool_input = None

    return ToolCallSelection(
        action=action,
        tool_name=normalized_tool_name,
        tool_input=normalized_tool_input,
        reason=reason.strip(),
        raw_response=raw_response,
    )


def _parse_json_object(raw_response: str) -> dict[str, Any]:
    """Extract a JSON object from the model response."""

    text = raw_response.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMError("Tool-calling response does not contain a JSON object.")

    try:
        decoded = json.loads(text[start : end + 1])
    except json.JSONDecodeError as error:
        raise LLMError("Tool-calling response is not valid JSON.") from error
    if not isinstance(decoded, dict):
        raise LLMError("Tool-calling response must be a JSON object.")
    return decoded


def _infer_tool_input(tool_name: str | None, user_input: str) -> str | None:
    """Infer a safer tool input from the original user request."""

    text = user_input.strip()
    if not tool_name:
        return text or None

    if tool_name in _PATH_INPUT_TOOLS:
        match = _FILE_PATTERN.search(text)
        if match:
            return match.group("path")
        return text or None

    if tool_name == "list_dir":
        match = _FILE_PATTERN.search(text)
        if match:
            return _parent_path(match.group("path"))
        return "."

    if tool_name in _TASK_INPUT_TOOLS:
        return text or None

    return text or None


def _looks_like_instruction_text(text: str) -> bool:
    """Return True when the tool input looks like a prompt fragment instead of a path."""

    lowered = text.lower().strip()
    return any(
        lowered.startswith(prefix)
        for prefix in (
            "read ",
            "open ",
            "show ",
            "count ",
            "search ",
            "answer ",
            "plan ",
            "list ",
            "use ",
        )
    )


def _parent_path(path: str) -> str:
    """Return the parent directory of a workspace-relative path."""

    if "/" not in path:
        return "."
    return path.rsplit("/", 1)[0] or "."


_FILE_PATTERN = re.compile(
    r"(?P<path>(?:[\w.\-]+/)*[\w.\-]+\.(?:md|txt|py|json|yaml|yml|toml|ini|cfg|csv|tsv|log))",
    re.IGNORECASE,
)


_NO_ARGUMENT_TOOLS = {
    "list_mcp_tools",
    "mcp_workspace_summary",
    "list_skills",
    "list_subagents",
}


_PATH_INPUT_TOOLS = {
    "read_file",
    "count_lines",
    "mcp_read_project_file",
}


_TASK_INPUT_TOOLS = {
    "search_docs",
    "search_vector_docs",
    "answer_docs_with_llm",
    "execute_skill",
    "plan_skill",
    "plan_subagents",
}
