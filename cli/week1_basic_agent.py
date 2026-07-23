from __future__ import annotations

import argparse
from pathlib import Path
import sys

from agent.week1_basic_agent import Week1Agent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Week 1 minimal CLI Agent")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--input", help="single user input")
    parser.add_argument("--trace", action="store_true", help="print reasoning trace")
    return parser


def run_once(agent: Week1Agent, user_input: str, show_trace: bool) -> None:
    run = agent.run(user_input)
    if show_trace:
        print(agent.format_trace(run))
    else:
        print(run.answer)


def interactive_loop(agent: Week1Agent, show_trace: bool) -> None:
    print("Week 1 CLI Agent 已启动。输入 exit 退出。")
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
    parser = build_parser()
    args = parser.parse_args(argv)
    agent = Week1Agent(Path(args.root))
    if args.input:
        run_once(agent, args.input, args.trace)
        return 0
    interactive_loop(agent, args.trace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

