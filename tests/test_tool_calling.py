"""Tests for the LLM-assisted tool calling pipeline."""

from pathlib import Path
import unittest

from agent import WorkspaceAgent
from agent.llm import LLMResponse
from agent.tool_calling import parse_tool_call_selection, select_tool_call
from agent.tool_schema import build_workspace_tool_specs


class FakeToolCallingClient:
    """Minimal fake LLM client that returns a fixed structured response."""

    def __init__(self, content: str) -> None:
        """Initialize the instance state needed by this object."""
        self.content = content

    def chat(self, messages):  # noqa: ANN001 - test double keeps the signature loose
        """Return a deterministic chat response used by the surrounding test or fake client."""
        return LLMResponse(model="fake", content=self.content, raw={"messages": len(messages)})


class ToolCallingTests(unittest.TestCase):
    """Verify structured tool selection and agent execution."""

    def test_parse_tool_call_selection(self) -> None:
        """Verify that parse tool call selection."""
        selection = parse_tool_call_selection(
            '{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"Inspect the project README."}'
        )

        self.assertEqual(selection.action, "use_tool")
        self.assertEqual(selection.tool_name, "read_file")
        self.assertEqual(selection.tool_input, "README.md")
        self.assertIn("README", selection.reason)

    def test_select_tool_call_uses_tool_schema(self) -> None:
        """Verify that select tool call uses tool schema."""
        client = FakeToolCallingClient(
            '{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"The task asks to inspect the README."}'
        )

        selection = select_tool_call(
            client,  # type: ignore[arg-type]
            "Use tool calling to read README.md.",
            build_workspace_tool_specs(),
            prompt="Tool calling prompt",
        )

        self.assertEqual(selection.tool_name, "read_file")
        self.assertEqual(selection.tool_input, "README.md")

    def test_tool_schema_exposes_mcp_file_reader(self) -> None:
        """Verify that tool schema exposes mcp file reader."""
        specs = build_workspace_tool_specs()
        names = {spec.name for spec in specs}

        self.assertIn("mcp_read_project_file", names)

    def test_tool_schema_exposes_mcp_write_tool(self) -> None:
        """Verify that tool schema exposes mcp write tool."""
        specs = build_workspace_tool_specs()
        names = {spec.name for spec in specs}

        self.assertIn("mcp_write_project_file", names)

    def test_tool_schema_exposes_skill_execution(self) -> None:
        """Verify that tool schema exposes skill execution."""
        specs = build_workspace_tool_specs()
        names = {spec.name for spec in specs}

        self.assertIn("execute_skill", names)

    def test_select_tool_call_normalizes_mcp_file_path(self) -> None:
        """Verify that select tool call normalizes mcp file path."""
        client = FakeToolCallingClient(
            '{"action":"use_tool","tool_name":"mcp_read_project_file","tool_input":"Use MCP to read README.md","reason":"The task asks MCP to read a file."}'
        )

        selection = select_tool_call(
            client,  # type: ignore[arg-type]
            "Use tool calling to read README.md through MCP.",
            build_workspace_tool_specs(),
            prompt="Tool calling prompt",
        )

        self.assertEqual(selection.tool_name, "mcp_read_project_file")
        self.assertEqual(selection.tool_input, "README.md")

    def test_select_tool_call_removes_input_for_no_argument_mcp_tool(self) -> None:
        """Verify that select tool call removes input for no argument mcp tool."""
        client = FakeToolCallingClient(
            '{"action":"use_tool","tool_name":"mcp_workspace_summary","tool_input":"Use MCP workspace summary.","reason":"The task asks for the MCP workspace summary."}'
        )

        selection = select_tool_call(
            client,  # type: ignore[arg-type]
            "Use tool calling to call MCP workspace summary.",
            build_workspace_tool_specs(),
            prompt="Tool calling prompt",
        )

        self.assertEqual(selection.tool_name, "mcp_workspace_summary")
        self.assertIsNone(selection.tool_input)

    def test_workspace_agent_runs_tool_calling_read_file(self) -> None:
        """Verify that workspace agent runs tool calling read file."""
        client = FakeToolCallingClient(
            '{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"The task asks to inspect the README."}'
        )
        agent = WorkspaceAgent(Path("."), llm_client=client)

        run = agent.run("Use tool calling to read README.md.")

        self.assertEqual(run.route.action, "tool_call")
        self.assertIsNotNone(run.tool_call)
        self.assertEqual(run.tool_call.tool_name if run.tool_call else None, "read_file")
        self.assertIn("Result: read README.md", run.answer)
        self.assertIn("Run tool-call graph", agent.format_trace(run))

    def test_workspace_agent_runs_tool_calling_direct_answer(self) -> None:
        """Verify that workspace agent runs tool calling direct answer."""
        client = FakeToolCallingClient(
            '{"action":"answer_directly","tool_name":null,"tool_input":null,"reason":"The question can be answered directly."}'
        )
        agent = WorkspaceAgent(Path("."), llm_client=client)

        run = agent.run("Use tool calling to explain the difference between an agent and a chatbot.")

        self.assertEqual(run.route.action, "tool_call")
        self.assertIsNotNone(run.tool_call)
        self.assertEqual(run.tool_call.action if run.tool_call else None, "answer_directly")
        self.assertIn("main difference", run.answer)

    def test_workspace_agent_tool_calling_can_opt_out_of_graph_runtime(self) -> None:
        """Verify that workspace agent tool calling can opt out of graph runtime."""
        client = FakeToolCallingClient(
            '{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"The task asks to inspect the README."}'
        )
        agent = WorkspaceAgent(Path("."), llm_client=client, use_graph_runtime=False)

        run = agent.run("Use tool calling to read README.md.")

        self.assertIn("Result: read README.md", run.answer)
        self.assertIn("Select tool", agent.format_trace(run))
        self.assertNotIn("Run tool-call graph", agent.format_trace(run))


if __name__ == "__main__":
    unittest.main()
