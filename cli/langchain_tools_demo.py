"""Command-line demo for LangChain tool adapters."""

from __future__ import annotations

import argparse
from pathlib import Path

from integrations import build_langchain_tools


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for listing LangChain tools."""

    parser = argparse.ArgumentParser(description="LangChain tool adapter demo")
    parser.add_argument("--root", default=".", help="workspace root")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    tools = build_langchain_tools(Path(args.root))

    print("LangChain tools:")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
