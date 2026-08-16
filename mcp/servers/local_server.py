"""Local in-process MCP server for learning the protocol boundary."""

from __future__ import annotations

from pathlib import Path

from mcp.schema import MCPRequest, MCPResponse, MCPToolSpec, READ_ONLY_PERMISSION, WRITE_PERMISSION


class LocalMCPServer:
    """Expose a small set of workspace tools through an MCP-like interface."""

    def __init__(self, workspace_root: Path | str = ".") -> None:
        """Initialize the instance state needed by this object."""
        self.workspace_root = Path(workspace_root).resolve()  # 固定服务端工作区

    def list_tools(self) -> list[MCPToolSpec]:
        """Return tool descriptions available on this local server."""

        return [
            MCPToolSpec(
                name="workspace_summary",
                description="Summarize the workspace root and top-level entries.",
                input_schema={"type": "object", "properties": {}},
                permission_level=READ_ONLY_PERMISSION,
            ),
            MCPToolSpec(
                name="read_project_file",
                description="Read a small text file from the workspace.",
                input_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
                permission_level=READ_ONLY_PERMISSION,
            ),
            MCPToolSpec(
                name="write_project_file",
                description="Write a small text file inside the workspace.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
                permission_level=WRITE_PERMISSION,
            ),
        ]

    def get_tool_spec(self, tool_name: str) -> MCPToolSpec | None:
        """Return one registered tool spec by name."""

        for spec in self.list_tools():
            if spec.name == tool_name:
                return spec
        return None

    def call_tool(self, request: MCPRequest) -> MCPResponse:
        """Dispatch one request to a registered local tool."""

        if request.tool_name == "workspace_summary":
            return MCPResponse(request.tool_name, self._workspace_summary())
        if request.tool_name == "read_project_file":
            return self._read_project_file(request)
        if request.tool_name == "write_project_file":
            return self._write_project_file(request)
        return MCPResponse(request.tool_name, f"Unknown MCP tool: {request.tool_name}", is_error=True)

    def _workspace_summary(self) -> str:
        """Build a compact workspace summary."""

        entries = []
        for child in sorted(self.workspace_root.iterdir(), key=lambda path: (not path.is_dir(), path.name.lower())):
            suffix = "/" if child.is_dir() else ""
            entries.append(f"- {child.name}{suffix}")
        listing = "\n".join(entries) if entries else "- <empty>"
        return f"Workspace: {self.workspace_root.name}\nTop-level entries:\n{listing}"

    def _read_project_file(self, request: MCPRequest) -> MCPResponse:
        """Read a small file with workspace path protection."""

        raw_path = str(request.arguments.get("path", "")).strip()
        if not raw_path:
            return MCPResponse(request.tool_name, "Missing required argument: path", is_error=True)

        path = (self.workspace_root / raw_path).resolve()
        if self.workspace_root not in path.parents and path != self.workspace_root:
            return MCPResponse(request.tool_name, f"Path escapes workspace root: {raw_path}", is_error=True)
        if not path.exists():
            return MCPResponse(request.tool_name, f"File does not exist: {raw_path}", is_error=True)
        if not path.is_file():
            return MCPResponse(request.tool_name, f"Path is not a file: {raw_path}", is_error=True)

        text = path.read_text(encoding="utf-8", errors="replace")
        return MCPResponse(request.tool_name, f"[read_project_file] {raw_path}\n{text}")

    def _write_project_file(self, request: MCPRequest) -> MCPResponse:
        """Write a small file with workspace path protection."""

        raw_path = str(request.arguments.get("path", "")).strip()
        content = str(request.arguments.get("content", ""))
        if not raw_path:
            return MCPResponse(request.tool_name, "Missing required argument: path", is_error=True)
        if not content:
            return MCPResponse(request.tool_name, "Missing required argument: content", is_error=True)

        path = (self.workspace_root / raw_path).resolve()
        if self.workspace_root not in path.parents and path != self.workspace_root:
            return MCPResponse(request.tool_name, f"Path escapes workspace root: {raw_path}", is_error=True)
        if path.exists() and path.is_dir():
            return MCPResponse(request.tool_name, f"Path is not a file: {raw_path}", is_error=True)
        if not path.parent.exists():
            return MCPResponse(request.tool_name, f"Parent directory does not exist: {path.parent.relative_to(self.workspace_root)}", is_error=True)

        path.write_text(content, encoding="utf-8")
        return MCPResponse(
            request.tool_name,
            f"[write_project_file] {raw_path}\nWrote {len(content.encode('utf-8'))} bytes.",
        )
