"""Agent-facing adapter for local MCP experiments."""

from __future__ import annotations

from pathlib import Path

from mcp.clients.local_client import LocalMCPClient
from mcp.servers.local_server import LocalMCPServer


def list_mcp_tools(root: Path) -> str:
    """Return available local MCP tools as text."""

    client = _build_client(root)
    lines = ["Available MCP tools:"]
    for spec in client.list_tools():
        lines.append(f"- {spec.name}: {spec.description}")
    return "\n".join(lines)


def call_mcp_tool(root: Path, tool_name: str, arguments: dict[str, object] | None = None) -> str:
    """Call a local MCP tool and render the response."""

    client = _build_client(root)
    response = client.call_tool(tool_name, arguments)
    status = "error" if response.is_error else "ok"
    return f"[mcp:{status}] {response.tool_name}\n{response.content}"


def _build_client(root: Path) -> LocalMCPClient:
    """Create the local client/server pair used by the adapter."""

    server = LocalMCPServer(root)
    return LocalMCPClient(server)
