"""Local MCP learning package."""

from .adapter import call_mcp_tool, call_mcp_tool_response, list_mcp_tools
from .clients.local_client import LocalMCPClient
from .policy import build_default_mcp_policy, evaluate_mcp_tool_permission
from .schema import MCPPermissionDecision, MCPPermissionPolicy, MCPRequest, MCPResponse, MCPToolSpec
from .servers.local_server import LocalMCPServer

__all__ = [
    "LocalMCPClient",
    "LocalMCPServer",
    "MCPPermissionDecision",
    "MCPPermissionPolicy",
    "MCPRequest",
    "MCPResponse",
    "MCPToolSpec",
    "build_default_mcp_policy",
    "call_mcp_tool",
    "call_mcp_tool_response",
    "evaluate_mcp_tool_permission",
    "list_mcp_tools",
]
