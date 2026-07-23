"""Core orchestration for the workspace agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from .prompts import load_system_prompt, load_tool_router_prompt
from .router import ToolRoute, route_intent
from .tools import ToolError, ToolResult, list_dir, read_file


@dataclass(frozen=True)
class AgentStep:
    """One recorded step in a run trace."""

    title: str
    detail: str


@dataclass
class AgentRun:
    """In-memory record of one agent execution."""

    run_id: str
    user_input: str
    route: ToolRoute
    steps: list[AgentStep] = field(default_factory=list)
    tool_result: ToolResult | None = None
    tool_error: str | None = None
    answer: str = ""


class WorkspaceAgent:
    """Minimal agent that can answer directly or call local tools."""

    def __init__(self, workspace_root: Path | str = ".") -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.system_prompt = load_system_prompt()
        self.tool_router_prompt = load_tool_router_prompt()

    def run(self, user_input: str) -> AgentRun:
        """Execute one turn and return a structured run record."""

        run = AgentRun(
            run_id=uuid4().hex[:8],
            user_input=user_input,
            route=route_intent(user_input),
            steps=[],
        )
        run.steps.append(AgentStep("Receive input", user_input))
        run.steps.append(AgentStep("Load prompts", "system prompt and tool-router prompt loaded"))
        run.steps.append(AgentStep("Route request", f"{run.route.action} / {run.route.tool_name or 'none'}"))

        if run.route.action == "use_tool":
            try:
                run.tool_result = self._call_tool(run.route)
                run.steps.append(AgentStep("Run tool", f"{run.tool_result.tool_name} completed"))
                run.answer = self._compose_tool_answer(run)
            except ToolError as error:
                run.tool_error = str(error)
                run.steps.append(AgentStep("Tool failed", run.tool_error))
                run.answer = self._compose_tool_error_answer(run)
        else:
            run.answer = self._compose_direct_answer(user_input)
            run.steps.append(AgentStep("Answer directly", "no tool was called"))

        run.steps.append(AgentStep("Complete", "final answer generated"))
        return run

    def _call_tool(self, route: ToolRoute) -> ToolResult:
        """Dispatch tool calls based on the router decision."""

        if route.tool_name == "read_file":
            return read_file(self.workspace_root, route.tool_input or ".")
        if route.tool_name == "list_dir":
            return list_dir(self.workspace_root, route.tool_input or ".")
        raise ToolError(f"Unknown tool: {route.tool_name}")

    def _compose_tool_error_answer(self, run: AgentRun) -> str:
        """Convert a tool failure into a user-facing answer."""

        return (
            "Result: the tool call failed, so the task was not completed.\n\n"
            f"Reason: {run.tool_error}\n\n"
            "Next step: check whether the file or directory exists, or use another relative path inside the workspace."
        )

    def _compose_tool_answer(self, run: AgentRun) -> str:
        """Turn tool output into a concise answer."""

        assert run.tool_result is not None
        if run.tool_result.tool_name == "read_file":
            return (
                f"Result: read {run.route.tool_input}.\n\n"
                f"Key content:\n{self._summarize_text(run.tool_result.output)}"
            )
        if run.tool_result.tool_name == "list_dir":
            return (
                "Result: inspected the current directory structure.\n\n"
                f"Directory listing:\n{run.tool_result.output}\n\n"
                f"Responsibilities:\n{self._describe_known_project_dirs(run.tool_result.output)}"
            )
        return run.tool_result.output

    def _compose_direct_answer(self, user_input: str) -> str:
        """Provide a structured direct answer for non-tool requests."""

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

    def _summarize_text(self, text: str, limit: int = 20) -> str:
        """Summarize read_file output while keeping the result deterministic."""

        lines = text.splitlines()
        learning_goal_summary = self._extract_markdown_section(lines, "## Learning Goals")
        if learning_goal_summary:
            return "Project learning goals:\n" + learning_goal_summary

        head = lines[:limit]
        if len(lines) > limit:
            head.append("... (truncated)")
        return "\n".join(head)

    def _extract_markdown_section(self, lines: list[str], heading: str) -> str:
        """Extract a Markdown section until the next heading."""

        try:
            start = lines.index(heading)
        except ValueError:
            return ""
        collected: list[str] = []
        for line in lines[start + 1 :]:
            if line.startswith("## "):
                break
            if line.strip():
                collected.append(line)
        return "\n".join(collected).strip()

    def _describe_known_project_dirs(self, listing: str) -> str:
        """Explain the purpose of directories shown by list_dir."""

        descriptions: dict[str, str] = {
            "agent/": "Core agent loop experiments, including workflow, state, and tool calling.",
            "cli/": "Command-line entrypoints for running and debugging the agent locally.",
            "prompts/": "Versioned prompts for system behavior, tool routing, and agent roles.",
            "evals/": "Evaluation cases, expected behavior, and actual output records.",
            "tests/": "Automated tests for tools, routing, and agent behavior.",
            "docs/": "Learning plans, architecture notes, reviews, and progress state.",
            "examples/": "Reproducible sample inputs and outputs.",
            "mcp/": "MCP server/client and external tool protocol experiments.",
            "rag/": "Document loading, chunking, retrieval, and question-answering experiments.",
            "skills/": "Reusable task capability definitions.",
            "subagent/": "Teacher Agent, Coding Agent, and future multi-agent experiments.",
            "configs/": "Configuration templates for models, tools, logging, and permissions.",
            "scripts/": "Developer helper scripts and one-off automation.",
            "data/": "Local experimental data.",
            "logs/": "Local runtime logs.",
        }
        result = []
        for dirname, description in descriptions.items():
            if f"- {dirname}" in listing:
                result.append(f"- `{dirname}`：{description}")
        return "\n".join(result) if result else "- No known project directories were found in the listing."

    def format_trace(self, run: AgentRun) -> str:
        """Render the run as a human-readable execution trace."""

        parts: list[str] = [f"Run ID: {run.run_id}"]
        for index, step in enumerate(run.steps, start=1):
            parts.append(f"{index}. {step.title}: {step.detail}")
        if run.tool_result is not None:
            parts.append("")
            parts.append(f"[Tool] {run.tool_result.tool_name}")
            parts.append(run.tool_result.output)
        if run.tool_error is not None:
            parts.append("")
            parts.append("[Tool Error]")
            parts.append(run.tool_error)
        parts.append("")
        parts.append("[Final Answer]")
        parts.append(run.answer)
        return "\n".join(parts)
