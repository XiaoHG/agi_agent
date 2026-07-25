"""Local MCP learning package."""

from .adapter import call_mcp_tool, list_mcp_tools
from .clients.local_client import LocalMCPClient
from .schema import MCPRequest, MCPResponse, MCPToolSpec
from .servers.local_server import LocalMCPServer

__all__ = [
    "LocalMCPClient",
    "LocalMCPServer",
    "MCPRequest",
    "MCPResponse",
    "MCPToolSpec",
    "call_mcp_tool",
    "list_mcp_tools",
]
