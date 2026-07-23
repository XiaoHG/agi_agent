"""Command-line entrypoint for the workspace agent."""

from __future__ import annotations

import argparse
from pathlib import Path

from agent import WorkspaceAgent


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the agent."""

    parser = argparse.ArgumentParser(description="Minimal workspace agent")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--input", help="single user input")
    parser.add_argument("--trace", action="store_true", help="print reasoning trace")
    return parser


def run_once(agent: WorkspaceAgent, user_input: str, show_trace: bool) -> None:
    """Run one input through the agent and print the result."""

    run = agent.run(user_input)
    print(agent.format_trace(run) if show_trace else run.answer)


def interactive_loop(agent: WorkspaceAgent, show_trace: bool) -> None:
    """Start an interactive REPL-like loop."""

    print("Agent 已启动。输入 exit 退出。")
    while True:
        try:
            user_input = input("> ").strip()
        except EOFError:
            print()
            return
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            return
        run_once(agent, user_input, show_trace)
        print()


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    agent = WorkspaceAgent(Path(args.root))
    if args.input:
        run_once(agent, args.input, args.trace)
        return 0
    interactive_loop(agent, args.trace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

