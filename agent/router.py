"""Rule-based routing for the minimal workspace agent."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ToolRoute:
    """Describes how the agent should handle a user request."""

    action: str  # 路由动作，例如 use_tool / direct_answer / workflow
    tool_name: str | None = None  # 被选中的工具名
    tool_input: str | None = None  # 传给工具的输入
    reason: str = ""  # 路由判断原因


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


def _looks_like_workflow_request(text: str) -> bool:
    """Return True when the request looks like an ordered multi-step task."""

    lowered = f" {text.lower()} "
    markers = [
        " and then ",
        " then ",
        " after that ",
        " first ",
        " next ",
        "step by step",
        "workflow",
        "multiple steps",
    ]
    return any(marker in lowered for marker in markers)


def _looks_like_knowledge_search(text: str) -> bool:
    """Return True when the user is asking to search local knowledge documents."""

    keywords = [
        "ask docs",
        "ask documentation",
        "local docs",
        "local documentation",
        "project docs",
        "project documentation",
        "search docs",
        "search documentation",
        "search knowledge",
        "knowledge base",
        "rag",
    ]
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _looks_like_llm_rag_request(text: str) -> bool:
    """Return True when the user is asking for an LLM-grounded local docs answer."""

    keywords = [
        "answer docs",
        "answer documentation",
        "answer from docs",
        "answer from documentation",
        "answer with docs",
        "answer with local docs",
        "answer with local context",
        "deepseek rag",
        "grounded answer",
        "grounded rag",
        "llm rag",
        "rag answer",
        "use deepseek rag",
    ]
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _looks_like_vector_rag_request(text: str) -> bool:
    """Return True when the user asks for professional vector RAG search."""

    keywords = [
        "professional rag",
        "semantic search",
        "vector rag",
        "vector search",
        "search vector docs",
        "search with vector",
    ]
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _extract_llm_rag_question(text: str) -> str:
    """Extract the actual question from an LLM-grounded RAG request."""

    if ":" in text:
        return text.split(":", 1)[1].strip()

    lowered = text.lower()
    prefixes = [
        "answer with local docs and deepseek rag",
        "answer with local docs",
        "answer with local context",
        "answer from docs",
        "answer with docs",
        "use deepseek rag",
        "deepseek rag",
        "grounded rag",
        "llm rag",
        "rag answer",
    ]
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip(" .")
    return text


def _looks_like_langgraph_request(text: str) -> bool:
    """Return True when the user explicitly asks to use the LangGraph workflow."""

    lowered = text.lower()
    if "langgraph" in lowered:
        return True
    markers = [
        "use graph",
        "run graph",
        "graph workflow",
        "graph answer",
        "answer with graph",
        "route with graph",
        "through graph",
    ]
    return any(marker in lowered for marker in markers)


def _extract_langgraph_question(text: str) -> str:
    """Remove LangGraph command wording and keep the question passed into the graph."""

    if ":" in text:
        return text.split(":", 1)[1].strip()

    lowered = text.lower()
    prefixes = [
        "use langgraph to",
        "run langgraph to",
        "run with langgraph to",
        "answer with langgraph",
        "use graph to",
        "run graph to",
        "graph answer",
        "graph workflow",
    ]
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip(" .")
    return text


def _looks_like_tool_calling_request(text: str) -> bool:
    """Return True when the user explicitly wants the LLM to choose a tool."""

    lowered = text.lower()
    keywords = [
        "tool calling",
        "tool call",
        "tool selection",
        "select a tool",
        "choose a tool",
        "llm tool",
        "let the model choose",
        "let llm choose",
        "structured tool",
    ]
    return any(keyword in lowered for keyword in keywords)


def _looks_like_tool_loop_request(text: str) -> bool:
    """Return True when the user explicitly wants a multi-step tool loop."""

    lowered = text.lower()
    keywords = [
        "tool loop",
        "multi-step tool",
        "multi step tool",
        "multiple tool steps",
        "iterate tools",
        "tool iteration",
        "loop with tools",
    ]
    return any(keyword in lowered for keyword in keywords)


def _extract_tool_calling_question(text: str) -> str:
    """Remove tool-calling instruction wording and keep the actual task."""

    if ":" in text:
        return text.split(":", 1)[1].strip()

    lowered = text.lower()
    prefixes = [
        "use tool calling to",
        "use llm tool calling to",
        "let the model choose the tool for",
        "let llm choose the tool for",
        "choose a tool for",
        "select a tool for",
        "use structured tool calling to",
    ]
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip(" .")
    return text


def _extract_tool_loop_question(text: str) -> str:
    """Remove tool-loop instruction wording and keep the actual task."""

    if ":" in text:
        return text.split(":", 1)[1].strip()

    lowered = text.lower()
    prefixes = [
        "use tool loop to",
        "use a tool loop to",
        "run tool loop to",
        "run a tool loop to",
        "use multi-step tool loop to",
        "use multi step tool loop to",
        "loop with tools to",
    ]
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip(" .")
    return text


def _looks_like_mcp_request(text: str) -> bool:
    """Return True when the user is asking about MCP tools."""

    lowered = text.lower()
    return "mcp" in lowered


def _looks_like_skill_request(text: str) -> bool:
    """Return True when the user is asking about reusable skills."""

    lowered = text.lower()
    return "skill" in lowered or "skills" in lowered


def _looks_like_skill_execution_request(text: str) -> bool:
    """Return True when the user is asking to execute a reusable skill."""

    lowered = text.lower()
    keywords = [
        "execute skill",
        "run skill",
        "use skill",
        "perform skill",
        "skill execution",
    ]
    return any(keyword in lowered for keyword in keywords)


def _looks_like_subagent_request(text: str) -> bool:
    """Return True when the user is asking about subagents or collaboration."""

    lowered = text.lower()
    keywords = ["subagent", "subagents", "multi-agent", "collaboration", "collaborate", "team"]
    return any(keyword in lowered for keyword in keywords)


def _looks_like_subagent_execution_request(text: str) -> bool:
    """Return True when the user is asking to execute subagent collaboration."""

    lowered = text.lower()
    keywords = ["execute subagent", "run subagent", "execute collaboration", "run collaboration", "execute multi-agent"]
    return any(keyword in lowered for keyword in keywords)


def route_intent(user_input: str) -> ToolRoute:
    """Choose the simplest safe action for the current input.

    The router is intentionally rule-based for the first iteration so that the
    workflow is easy to inspect and later replace with model-based routing.
    """

    text = user_input.strip()
    match = FILE_PATTERN.search(text)

    if _looks_like_langgraph_request(text):
        return ToolRoute(
            action="graph",
            tool_name="langgraph_workflow",
            tool_input=_extract_langgraph_question(text),
            reason="The user is asking to run the request through the LangGraph workflow.",
        )

    if _looks_like_tool_loop_request(text):
        return ToolRoute(
            action="tool_loop",
            tool_name="llm_tool_loop",
            tool_input=_extract_tool_loop_question(text),
            reason="The user is asking the LLM to run a bounded multi-step tool loop.",
        )

    if _looks_like_tool_calling_request(text):
        return ToolRoute(
            action="tool_call",
            tool_name="llm_tool_selector",
            tool_input=_extract_tool_calling_question(text),
            reason="The user is asking the LLM to choose the best tool from the tool catalog.",
        )

    if _looks_like_llm_rag_request(text):
        return ToolRoute(
            action="use_tool",
            tool_name="answer_docs_with_llm",
            tool_input=_extract_llm_rag_question(text),
            reason="The user is asking for an LLM-grounded answer from local project documents.",
        )

    if _looks_like_vector_rag_request(text):
        return ToolRoute(
            action="use_tool",
            tool_name="search_vector_docs",
            tool_input=text,
            reason="The user is asking for professional vector RAG search over local documents.",
        )

    if _looks_like_knowledge_search(text):
        return ToolRoute(
            action="use_tool",
            tool_name="search_docs",
            tool_input=text,
            reason="The user is asking to search local project knowledge documents.",
        )

    if _looks_like_mcp_request(text):
        tool_name = "list_mcp_tools"
        reason = "The user is asking to inspect local MCP tools."
        lowered = text.lower()
        if "write" in lowered or "save" in lowered or "create" in lowered:
            tool_name = "mcp_write_project_file"
            reason = "The user is asking to call a write-capable MCP tool."
        elif "read" in lowered or "open" in lowered:
            tool_name = "mcp_read_project_file"
            reason = "The user is asking to read a workspace file through MCP."
        elif "summary" in lowered or "workspace" in lowered:
            tool_name = "mcp_workspace_summary"
            reason = "The user is asking to call the local MCP workspace summary tool."
        return ToolRoute(
            action="use_tool",
            tool_name=tool_name,
            tool_input=text,
            reason=reason,
        )

    if _looks_like_skill_request(text):
        tool_name = "plan_skill"
        reason = "The user is asking to select or explain a reusable skill."
        if "list" in text.lower() or "available" in text.lower():
            tool_name = "list_skills"
            reason = "The user is asking to list available skills."
        elif _looks_like_skill_execution_request(text):
            tool_name = "execute_skill"
            reason = "The user is asking to execute a reusable skill."
        return ToolRoute(
            action="use_tool",
            tool_name=tool_name,
            tool_input=text,
            reason=reason,
        )

    if _looks_like_subagent_request(text):
        tool_name = "plan_subagents"
        reason = "The user is asking to plan subagent collaboration."
        if "list" in text.lower() or "available" in text.lower():
            tool_name = "list_subagents"
            reason = "The user is asking to list available subagents."
        elif _looks_like_subagent_execution_request(text):
            tool_name = "execute_subagents"
            reason = "The user is asking to execute the subagent collaboration protocol."
        return ToolRoute(
            action="use_tool",
            tool_name=tool_name,
            tool_input=text,
            reason=reason,
        )

    if _looks_like_workflow_request(text):
        return ToolRoute(
            action="workflow",
            reason="The request contains ordered actions and should be handled as a workflow.",
        )

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
