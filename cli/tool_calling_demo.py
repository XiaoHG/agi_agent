"""Command-line demo for LLM-assisted tool calling."""

from __future__ import annotations

import argparse
from pathlib import Path

from agent import WorkspaceAgent


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the tool-calling demo."""

    parser = argparse.ArgumentParser(description="LLM-assisted tool calling demo")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--input", required=True, help="user input for tool calling")
    parser.add_argument("--trace", action="store_true", help="print reasoning trace")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)

    agent = WorkspaceAgent(Path(args.root))
    run = agent.run(args.input)
    print(agent.format_trace(run) if args.trace else run.answer)
    return 0 if not run.tool_error else 1


if __name__ == "__main__":
    raise SystemExit(main())

