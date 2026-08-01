"""Tests for the local MCP learning layer."""

from pathlib import Path
import tempfile  # 临时工作区，隔离测试文件
import unittest  # Python 官方测试框架

from agent import WorkspaceAgent, route_intent
from mcp import LocalMCPClient, LocalMCPServer, call_mcp_tool, list_mcp_tools


class FakeMCPReadClient:
    """Fake LLM client that selects the MCP file reader."""

    def chat(self, messages):  # noqa: ANN001 - test double keeps the signature loose
        from agent.llm import LLMResponse

        return LLMResponse(
            model="fake",
            content=(
                '{"action":"use_tool","tool_name":"mcp_read_project_file",'
                '"tool_input":"Use MCP to read README.md",'
                '"reason":"The task asks to read a file through MCP."}'
            ),
            raw={"messages": len(messages)},
        )


class LocalMCPTests(unittest.TestCase):
    """Verify local MCP server, client, adapter, and agent integration."""

    def test_server_lists_tools(self) -> None:
        server = LocalMCPServer(Path("."))

        tools = server.list_tools()
        names = {tool.name for tool in tools}

        self.assertIn("workspace_summary", names)
        self.assertIn("read_project_file", names)

    def test_client_calls_workspace_summary(self) -> None:
        client = LocalMCPClient(LocalMCPServer(Path(".")))

        response = client.call_tool("workspace_summary")

        self.assertFalse(response.is_error)
        self.assertIn("Workspace:", response.content)

    def test_client_reads_existing_project_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "demo.md").write_text("hello mcp", encoding="utf-8")
            client = LocalMCPClient(LocalMCPServer(root))

            response = client.call_tool("read_project_file", {"path": "demo.md"})

            self.assertFalse(response.is_error)
            self.assertIn("hello mcp", response.content)

    def test_adapter_lists_mcp_tools(self) -> None:
        output = list_mcp_tools(Path("."))

        self.assertIn("Available MCP tools", output)
        self.assertIn("workspace_summary", output)

    def test_adapter_renders_mcp_error(self) -> None:
        output = call_mcp_tool(Path("."), "missing_tool")

        self.assertIn("[mcp:error]", output)
        self.assertIn("Unknown MCP tool", output)

    def test_route_to_mcp_tools(self) -> None:
        route = route_intent("List MCP tools.")

        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "list_mcp_tools")

    def test_agent_lists_mcp_tools(self) -> None:
        agent = WorkspaceAgent(Path("."))

        run = agent.run("List MCP tools.")

        self.assertEqual(run.route.tool_name, "list_mcp_tools")
        self.assertIn("Available MCP tools", run.answer)

    def test_agent_calls_mcp_workspace_summary(self) -> None:
        agent = WorkspaceAgent(Path("."))

        run = agent.run("Use MCP workspace summary.")

        self.assertEqual(run.route.tool_name, "mcp_workspace_summary")
        self.assertIn("[mcp:ok]", run.answer)

    def test_agent_reads_project_file_through_mcp_tool(self) -> None:
        client = FakeMCPReadClient()
        agent = WorkspaceAgent(Path("."), llm_client=client)

        run = agent.run("Use tool calling to read README.md through MCP.")

        self.assertEqual(run.route.action, "tool_call")
        self.assertIsNotNone(run.tool_call)
        self.assertEqual(run.tool_call.tool_name if run.tool_call else None, "mcp_read_project_file")
        self.assertIn("[mcp:ok]", run.answer)
        self.assertIn("[read_project_file] README.md", run.answer)

    def test_adapter_returns_error_for_missing_file_path(self) -> None:
        output = call_mcp_tool(Path("."), "read_project_file", {"path": ""})

        self.assertIn("[mcp:error]", output)
        self.assertIn("Missing required argument", output)

    def test_client_rejects_escaped_project_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            client = LocalMCPClient(LocalMCPServer(root))
            response = client.call_tool("read_project_file", {"path": "../outside.md"})

            self.assertTrue(response.is_error)
            self.assertIn("Path escapes workspace root", response.content)


if __name__ == "__main__":
    unittest.main()
