"""Local MCP client for calling the in-process learning server."""

from __future__ import annotations

from mcp.schema import MCPRequest, MCPResponse, MCPToolSpec
from mcp.servers.local_server import LocalMCPServer


class LocalMCPClient:
    """Client-side wrapper around the local MCP server boundary."""

    def __init__(self, server: LocalMCPServer) -> None:
        self.server = server  # 当前阶段用进程内 server 模拟协议边界

    def list_tools(self) -> list[MCPToolSpec]:
        """Ask the server which tools are available."""

        return self.server.list_tools()

    def get_tool_spec(self, tool_name: str) -> MCPToolSpec | None:
        """Ask the server for one registered tool spec."""

        return self.server.get_tool_spec(tool_name)

    def call_tool(self, tool_name: str, arguments: dict[str, object] | None = None) -> MCPResponse:
        """Call one server tool through a request object."""

        request = MCPRequest(tool_name=tool_name, arguments=arguments or {})
        return self.server.call_tool(request)
