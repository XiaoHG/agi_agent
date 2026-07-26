"""Command-line demo for skills and subagent collaboration."""

from __future__ import annotations

import argparse

from skills import describe_skills, select_skill
from subagent import build_collaboration_plan, describe_subagents


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the collaboration demo."""

    parser = argparse.ArgumentParser(description="Skills and subagent collaboration demo")
    parser.add_argument("--list-skills", action="store_true", help="list available skills")
    parser.add_argument("--list-subagents", action="store_true", help="list available subagents")
    parser.add_argument("--task", help="task to route through skills and subagents")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.list_skills:
        print(describe_skills())
        return 0

    if args.list_subagents:
        print(describe_subagents())
        return 0

    if args.task:
        skill = select_skill(args.task)
        plan = build_collaboration_plan(args.task)
        print(skill.describe())
        print()
        print(plan.to_text())
        return 0

    parser.error("use --list-skills, --list-subagents, or --task")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
