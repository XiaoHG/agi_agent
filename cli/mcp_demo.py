"""Command-line demo for the local MCP learning layer."""

from __future__ import annotations

import argparse
from pathlib import Path

from mcp import call_mcp_tool, list_mcp_tools


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the MCP demo."""

    parser = argparse.ArgumentParser(description="Local MCP demo")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--list-tools", action="store_true", help="list available local MCP tools")
    parser.add_argument("--tool", help="tool name to call")
    parser.add_argument("--path", help="file path for read_project_file")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)

    if args.list_tools:
        print(list_mcp_tools(root))
        return 0

    if args.tool == "read_project_file":
        print(call_mcp_tool(root, args.tool, {"path": args.path or ""}))
        return 0

    if args.tool:
        print(call_mcp_tool(root, args.tool))
        return 0

    parser.error("use --list-tools or --tool")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
