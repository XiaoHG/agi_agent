"""Agent-facing adapter for local MCP experiments."""

from __future__ import annotations

from pathlib import Path

from mcp.clients.local_client import LocalMCPClient
from mcp.policy import build_default_mcp_policy, evaluate_mcp_tool_permission
from mcp.schema import MCPPermissionPolicy, MCPResponse
from mcp.servers.local_server import LocalMCPServer


def list_mcp_tools(root: Path) -> str:
    """Return available local MCP tools as text."""

    client = _build_client(root)
    lines = ["Available MCP tools:"]
    for spec in client.list_tools():
        lines.append(f"- {spec.name} [{spec.permission_level}]: {spec.description}")
    return "\n".join(lines)


def call_mcp_tool(root: Path, tool_name: str, arguments: dict[str, object] | None = None) -> str:
    """Call a local MCP tool and render the response."""

    response = call_mcp_tool_response(root, tool_name, arguments)
    status = "error" if response.is_error else "ok"
    return f"[mcp:{status}] {response.tool_name}\n{response.content}"


def call_mcp_tool_response(
    root: Path,
    tool_name: str,
    arguments: dict[str, object] | None = None,
    *,
    policy: MCPPermissionPolicy | None = None,
) -> MCPResponse:
    """Call a local MCP tool and preserve structured permission metadata."""

    client = _build_client(root)
    spec = client.get_tool_spec(tool_name)
    if spec is None:
        return MCPResponse(tool_name, f"Unknown MCP tool: {tool_name}", is_error=True)

    resolved_policy = policy or build_default_mcp_policy()
    decision = evaluate_mcp_tool_permission(spec, resolved_policy)
    metadata = {
        "permission_decision": decision.to_dict(),
        "permission_policy": resolved_policy.to_dict(),
    }
    if not decision.allowed:
        return MCPResponse(
            tool_name,
            (
                f"Permission denied for MCP tool: {tool_name}\n"
                f"Permission level: {decision.permission_level}\n"
                f"Reason: {decision.reason}\n"
                f"Next safe action: {decision.next_safe_action}"
            ),
            is_error=True,
            metadata=metadata,
        )

    response = client.call_tool(tool_name, arguments)
    return MCPResponse(
        tool_name=response.tool_name,
        content=response.content,
        is_error=response.is_error,
        metadata={**metadata, **response.metadata},
    )


def _build_client(root: Path) -> LocalMCPClient:
    """Create the local client/server pair used by the adapter."""

    server = LocalMCPServer(root)
    return LocalMCPClient(server)
