"""Command-line demo for skills and subagent collaboration."""

from __future__ import annotations

import argparse
from pathlib import Path

from skills import describe_skills, execute_skill, select_skill
from subagent import build_collaboration_plan, describe_subagents


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the collaboration demo."""

    parser = argparse.ArgumentParser(description="Skills and subagent collaboration demo")
    parser.add_argument("--list-skills", action="store_true", help="list available skills")
    parser.add_argument("--list-subagents", action="store_true", help="list available subagents")
    parser.add_argument("--execute-skill", action="store_true", help="execute the selected skill for --task")
    parser.add_argument("--tool-backed", action="store_true", help="execute skill steps with workspace tools")
    parser.add_argument("--skill", help="explicit skill name to inspect or execute")
    parser.add_argument("--task", help="task to route through skills and subagents")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(".")

    if args.list_skills:
        print(describe_skills(root))
        return 0

    if args.list_subagents:
        print(describe_subagents())
        return 0

    if args.task:
        if args.execute_skill:
            if args.tool_backed:
                from agent import run_skill_with_workspace

                task = _inject_skill_hint(args.task, args.skill)
                print(run_skill_with_workspace(root, task).output)
                return 0
            print(execute_skill(args.task, root=root, skill_name=args.skill).to_text())
            return 0

        skill = select_skill(args.task, root=root, skill_name=args.skill)
        plan = build_collaboration_plan(args.task)
        print(skill.describe())
        print()
        print(plan.to_text())
        return 0

    parser.error("use --list-skills, --list-subagents, or --task")
    return 2


def _inject_skill_hint(task: str, skill_name: str | None) -> str:
    """Inject an explicit skill selector into the task for tool-based execution."""

    if not skill_name:
        return task
    return f"{task} skill={skill_name}"


if __name__ == "__main__":
    raise SystemExit(main())
