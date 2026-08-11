"""Tests for the local MCP learning layer."""

from pathlib import Path
import subprocess
import sys
import tempfile  # 临时工作区，隔离测试文件
import unittest  # Python 官方测试框架

from agent import WorkspaceAgent, route_intent
from mcp import (
    LocalMCPClient,
    LocalMCPServer,
    MCPPermissionPolicy,
    call_mcp_tool,
    call_mcp_tool_exchange,
    call_mcp_tool_response,
    list_mcp_tools,
)


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
        self.assertIn("write_project_file", names)
        write_tool = next(tool for tool in tools if tool.name == "write_project_file")
        self.assertEqual(write_tool.permission_level, "write")

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
        self.assertIn("write_project_file [write]", output)

    def test_adapter_renders_mcp_error(self) -> None:
        output = call_mcp_tool(Path("."), "missing_tool")

        self.assertIn("[mcp:error]", output)
        self.assertIn("Unknown MCP tool", output)

    def test_adapter_returns_standardized_execution_record(self) -> None:
        record = call_mcp_tool_exchange(Path("."), "workspace_summary")

        self.assertEqual(record.protocol_version, "v2")
        self.assertEqual(record.request.tool_name, "workspace_summary")
        self.assertEqual(record.status, "ok")
        self.assertIn("mcp_execution", record.to_response().metadata)
        self.assertEqual(record.to_dict()["response"]["tool_name"], "workspace_summary")
        self.assertIn("request_validation", record.to_dict())
        self.assertIn("governance_audit", record.to_dict())

    def test_adapter_rejects_missing_required_arguments_during_governance_validation(self) -> None:
        record = call_mcp_tool_exchange(Path("."), "read_project_file", {})

        self.assertEqual(record.protocol_version, "v2")
        self.assertTrue(record.response.is_error)
        self.assertEqual(record.error.stage, "validation")
        self.assertIn("Request validation failed", record.response.content)
        self.assertFalse(record.request_validation.valid)
        self.assertGreaterEqual(len(record.governance_audit), 2)
        self.assertEqual(record.governance_audit[1]["stage"], "validation")

    def test_route_to_mcp_tools(self) -> None:
        route = route_intent("List MCP tools.")

        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "list_mcp_tools")

    def test_route_to_mcp_write_tool(self) -> None:
        route = route_intent("Use MCP to write notes.txt with content hello.")

        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "mcp_write_project_file")

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

    def test_agent_denies_mcp_write_by_default(self) -> None:
        agent = WorkspaceAgent(Path("."))

        run = agent.run("Use MCP to write notes.txt with content hello mcp.")
        trace = agent.to_trace_dict(run)

        self.assertEqual(run.route.tool_name, "mcp_write_project_file")
        self.assertIn("[mcp:error]", run.answer)
        self.assertIn("Permission denied for MCP tool", run.answer)
        metadata = trace["tool_result"]["metadata"]
        self.assertEqual(metadata["permission_decision"]["permission_level"], "write")
        self.assertEqual(metadata["permission_decision"]["allowed"], False)

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

    def test_adapter_denies_write_tool_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            response = call_mcp_tool_response(
                root,
                "write_project_file",
                {"path": "notes.txt", "content": "hello mcp"},
            )

            self.assertTrue(response.is_error)
            self.assertIn("Permission denied", response.content)
            self.assertEqual(response.metadata["permission_decision"]["allowed"], False)

    def test_adapter_allows_write_tool_with_explicit_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            response = call_mcp_tool_response(
                root,
                "write_project_file",
                {"path": "notes.txt", "content": "hello mcp"},
                policy=MCPPermissionPolicy(allow_read_only=True, allow_write=True),
            )

            self.assertFalse(response.is_error)
            self.assertIn("Wrote", response.content)
            self.assertEqual((root / "notes.txt").read_text(encoding="utf-8"), "hello mcp")
            self.assertEqual(response.metadata["permission_decision"]["allowed"], True)

    def test_client_rejects_escaped_project_file_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            client = LocalMCPClient(LocalMCPServer(root))
            response = client.call_tool("read_project_file", {"path": "../outside.md"})

            self.assertTrue(response.is_error)
            self.assertIn("Path escapes workspace root", response.content)

    def test_mcp_demo_denies_write_without_policy_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cli.mcp_demo",
                    "--root",
                    tmp,
                    "--tool",
                    "write_project_file",
                    "--path",
                    "notes.txt",
                    "--content",
                    "hello mcp",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("[mcp:error]", result.stdout)
            self.assertIn("Permission denied", result.stdout)

    def test_mcp_demo_allows_write_with_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cli.mcp_demo",
                    "--root",
                    tmp,
                    "--tool",
                    "write_project_file",
                    "--path",
                    "notes.txt",
                    "--content",
                    "hello mcp",
                    "--allow-write",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("[mcp:ok]", result.stdout)
            self.assertEqual((Path(tmp) / "notes.txt").read_text(encoding="utf-8"), "hello mcp")

    def test_mcp_demo_shows_execution_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cli.mcp_demo",
                    "--root",
                    tmp,
                    "--tool",
                    "workspace_summary",
                    "--show-execution",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn('"protocol_version": "v2"', result.stdout)
            self.assertIn('"permission_decision"', result.stdout)
            self.assertIn('"request_validation"', result.stdout)
            self.assertIn('"governance_audit"', result.stdout)
            self.assertIn('"response"', result.stdout)


if __name__ == "__main__":
    unittest.main()
