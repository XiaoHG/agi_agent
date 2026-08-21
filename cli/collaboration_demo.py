"""Command-line demo for skills and subagent collaboration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from skills import SkillRuntimePolicy, describe_skills, execute_skill, select_skill
from subagent import build_collaboration_plan, describe_subagents, execute_collaboration_plan


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the collaboration demo."""

    parser = argparse.ArgumentParser(description="Skills and subagent collaboration demo")
    parser.add_argument("--list-skills", action="store_true", help="list available skills")
    parser.add_argument("--list-subagents", action="store_true", help="list available subagents")
    parser.add_argument("--execute-subagents", action="store_true", help="execute the deterministic subagent collaboration protocol")
    parser.add_argument("--runtime-json", action="store_true", help="print the subagent runtime session as JSON after execution")
    parser.add_argument("--queue-json", action="store_true", help="print the async delegation queue, inbox, outbox, and claim snapshot as JSON")
    parser.add_argument("--approval-json", action="store_true", help="print the approval request and decision snapshot as JSON")
    parser.add_argument("--lifecycle-json", action="store_true", help="print the long-horizon task lifecycle snapshot as JSON")
    parser.add_argument(
        "--approval-decision",
        choices=["approved", "rejected", "revise_required"],
        help="override the deterministic approval decision for collaboration execution",
    )
    parser.add_argument("--inbox-role", help="print inbox entries for one role after subagent execution")
    parser.add_argument("--outbox-role", help="print outbox entries for one role after subagent execution")
    parser.add_argument("--execute-skill", action="store_true", help="execute the selected skill for --task")
    parser.add_argument("--tool-backed", action="store_true", help="execute skill steps with workspace tools")
    parser.add_argument("--skill", help="explicit skill name to inspect or execute")
    parser.add_argument("--task", help="task to route through skills and subagents")
    parser.add_argument(
        "--skill-policy",
        choices=["default", "builtin-only", "project-only"],
        default="default",
        help="skill runtime policy preset",
    )
    parser.add_argument("--allow-skill", action="append", default=[], help="explicitly allow a skill name")
    parser.add_argument("--deny-skill", action="append", default=[], help="explicitly deny a skill name")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(".")
    policy = _build_skill_policy(args)

    if args.list_skills:
        print(describe_skills(root, policy=policy))
        return 0

    if args.list_subagents:
        print(describe_subagents())
        return 0

    if args.task:
        if args.execute_subagents:
            plan = execute_collaboration_plan(args.task, approval_override=args.approval_decision)
            print(plan.to_text())
            if args.runtime_json and plan.runtime_session is not None:
                print()
                print(json.dumps(plan.runtime_session.to_dict(), ensure_ascii=False, indent=2))
            if args.queue_json and plan.runtime_session is not None:
                print()
                print(
                    json.dumps(
                        {
                            "queue_items": [item.to_dict() for item in plan.runtime_session.queue_items],
                            "inbox_entries": [entry.to_dict() for entry in plan.runtime_session.inbox_entries],
                            "outbox_entries": [entry.to_dict() for entry in plan.runtime_session.outbox_entries],
                            "claim_records": [record.to_dict() for record in plan.runtime_session.claim_records],
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            if args.approval_json and plan.runtime_session is not None:
                print()
                print(
                    json.dumps(
                        {
                            "risk": None if plan.risk is None else plan.risk.to_dict(),
                            "approval_request": None if plan.approval_request is None else plan.approval_request.to_dict(),
                            "approval_decision": None if plan.approval_decision is None else plan.approval_decision.to_dict(),
                            "guarded_handoffs": [handoff.to_dict() for handoff in plan.guarded_handoffs],
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            if args.lifecycle_json and plan.runtime_session is not None:
                print()
                print(
                    json.dumps(
                        {
                            "task_lifecycle": None
                            if plan.task_lifecycle is None
                            else plan.task_lifecycle.to_dict(),
                            "watchdog_signals": [signal.to_dict() for signal in plan.watchdog_signals],
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            if args.inbox_role and plan.runtime_session is not None:
                print()
                print(
                    json.dumps(
                        [
                            entry.to_dict()
                            for entry in plan.runtime_session.inbox_entries
                            if entry.role_name == args.inbox_role
                        ],
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            if args.outbox_role and plan.runtime_session is not None:
                print()
                print(
                    json.dumps(
                        [
                            entry.to_dict()
                            for entry in plan.runtime_session.outbox_entries
                            if entry.role_name == args.outbox_role
                        ],
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            return 0

        if args.execute_skill:
            if args.tool_backed:
                from agent import run_skill_with_workspace

                task = _inject_skill_hint(args.task, args.skill)
                print(run_skill_with_workspace(root, task, policy=policy).output)
                return 0
            print(execute_skill(args.task, root=root, skill_name=args.skill, policy=policy).to_text())
            return 0

        skill = select_skill(args.task, root=root, skill_name=args.skill)
        plan = build_collaboration_plan(args.task)
        print(skill.describe())
        print()
        print(plan.to_text())
        return 0

    parser.error("use --list-skills, --list-subagents, or --task")
    return 2


def _build_skill_policy(args: argparse.Namespace) -> SkillRuntimePolicy:
    """Build a runtime skill policy from CLI arguments."""

    if args.skill_policy == "builtin-only":
        return SkillRuntimePolicy(
            policy_name="builtin-only",
            allow_builtin=True,
            allow_project=False,
            allowed_skill_names=tuple(args.allow_skill),
            denied_skill_names=tuple(args.deny_skill),
        )
    if args.skill_policy == "project-only":
        return SkillRuntimePolicy(
            policy_name="project-only",
            allow_builtin=False,
            allow_project=True,
            allowed_skill_names=tuple(args.allow_skill),
            denied_skill_names=tuple(args.deny_skill),
        )
    return SkillRuntimePolicy(
        policy_name="default",
        allow_builtin=True,
        allow_project=True,
        allowed_skill_names=tuple(args.allow_skill),
        denied_skill_names=tuple(args.deny_skill),
    )


def _inject_skill_hint(task: str, skill_name: str | None) -> str:
    """Inject an explicit skill selector into the task for tool-based execution."""

    if not skill_name:
        return task
    return f"{task} skill={skill_name}"


if __name__ == "__main__":
    raise SystemExit(main())
