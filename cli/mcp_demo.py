"""Command-line demo for the local MCP learning layer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from mcp import (
    MCPPermissionPolicy,
    build_environment_mcp_policy,
    call_mcp_tool,
    call_mcp_tool_exchange,
    call_mcp_tool_response,
    list_mcp_tools,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the MCP demo."""

    parser = argparse.ArgumentParser(description="Local MCP demo")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--list-tools", action="store_true", help="list available local MCP tools")
    parser.add_argument("--tool", help="tool name to call")
    parser.add_argument("--path", help="file path for read_project_file")
    parser.add_argument("--content", help="file content for write_project_file")
    parser.add_argument("--allow-write", action="store_true", help="allow write-capable MCP tools")
    parser.add_argument("--show-execution", action="store_true", help="print the standardized execution record")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)
    env_policy = build_environment_mcp_policy()
    policy = MCPPermissionPolicy(
        allow_read_only=env_policy.allow_read_only,
        allow_write=args.allow_write or env_policy.allow_write,
        allow_network=env_policy.allow_network,
        allow_destructive=env_policy.allow_destructive,
    )

    if args.list_tools:
        print(list_mcp_tools(root))
        return 0

    if args.tool == "read_project_file":
        if args.show_execution:
            print(json.dumps(call_mcp_tool_exchange(root, args.tool, {"path": args.path or ""}).to_dict(), indent=2))
        else:
            print(call_mcp_tool(root, args.tool, {"path": args.path or ""}))
        return 0

    if args.tool == "write_project_file":
        record = call_mcp_tool_exchange(
            root,
            args.tool,
            {"path": args.path or "", "content": args.content or ""},
            policy=policy,
        )
        if args.show_execution:
            print(json.dumps(record.to_dict(), indent=2))
        else:
            response = record.to_response()
            status = "error" if response.is_error else "ok"
            print(f"[mcp:{status}] {response.tool_name}\n{response.content}")
        return 0

    if args.tool:
        if args.show_execution:
            print(json.dumps(call_mcp_tool_exchange(root, args.tool).to_dict(), indent=2))
        else:
            print(call_mcp_tool(root, args.tool))
        return 0

    parser.error("use --list-tools or --tool")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
