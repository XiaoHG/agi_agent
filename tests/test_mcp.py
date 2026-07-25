"""Tests for the local MCP learning layer."""

from pathlib import Path
import tempfile  # 临时工作区，隔离测试文件
import unittest  # Python 官方测试框架

from agent import WorkspaceAgent, route_intent
from mcp import LocalMCPClient, LocalMCPServer, call_mcp_tool, list_mcp_tools


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
