"""Command-line entrypoint for the workspace agent.

This CLI is the easiest way to exercise the runtime end to end. It exposes:

- normal single-turn runs
- interactive mode
- checkpoint listing / inspection
- replay / compare / resume operations
- memory inspection
- runtime policy toggles such as classic-vs-graph execution

Example:
    python -m cli.main --input "Read README.md and summarize the project goals."
    python -m cli.main --list-runs
    python -m cli.main --resume-last-run
"""

from __future__ import annotations

import argparse
from pathlib import Path

from agent import WorkspaceAgent
from skills import SkillRuntimePolicy


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the primary runtime entrypoint."""

    parser = argparse.ArgumentParser(description="Minimal workspace agent")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument(
        "--history-dir",
        default=None,
        help="checkpoint directory; defaults to <root>/logs/agent-runs",
    )
    parser.add_argument(
        "--memory-dir",
        default=None,
        help="memory directory; defaults to <root>/logs/agent-memory",
    )
    parser.add_argument("--session-id", default="default", help="session id used for long-horizon memory")
    parser.add_argument("--task-id", default=None, help="task id used for long-horizon memory")
    parser.add_argument("--list-runs", action="store_true", help="list recent checkpoints")
    parser.add_argument("--list-session-memory", action="store_true", help="list stored session memory records")
    parser.add_argument("--list-task-memory", action="store_true", help="list stored task memory records")
    parser.add_argument("--input", help="single user input")
    parser.add_argument("--show-run", help="show a checkpoint by run id")
    parser.add_argument("--show-last-run", action="store_true", help="show the latest persisted run")
    parser.add_argument("--replay-run", help="replay a checkpoint by run id")
    parser.add_argument("--replay-last-run", action="store_true", help="replay the latest persisted run")
    parser.add_argument(
        "--compare-last-two-runs",
        action="store_true",
        help="compare the latest two persisted runs",
    )
    parser.add_argument(
        "--compare-runs",
        nargs=2,
        metavar=("OLDER_RUN_ID", "NEWER_RUN_ID"),
        help="compare two persisted runs by run id",
    )
    parser.add_argument("--resume-run", help="resume a checkpoint by run id")
    parser.add_argument("--resume-last-run", action="store_true", help="resume the latest persisted run")
    parser.add_argument(
        "--show-session-memory",
        nargs="?",
        const="",
        help="show one session memory record; empty means current session",
    )
    parser.add_argument(
        "--show-task-memory",
        nargs="?",
        const="",
        help="show one task memory record; empty means current task",
    )
    parser.add_argument("--llm-planner", action="store_true", help="use real DeepSeek planning for LangGraph runs")
    parser.add_argument("--classic-runtime", action="store_true", help="disable the default LangGraph runtime wrapper")
    parser.add_argument(
        "--skill-policy",
        choices=["default", "builtin-only", "project-only"],
        default="default",
        help="skill runtime policy preset",
    )
    parser.add_argument("--allow-skill", action="append", default=[], help="explicitly allow a skill name")
    parser.add_argument("--deny-skill", action="append", default=[], help="explicitly deny a skill name")
    parser.add_argument("--trace", action="store_true", help="print reasoning trace")
    return parser


def run_once(agent: WorkspaceAgent, user_input: str, show_trace: bool) -> None:
    """Run one request and print either the answer or the full trace."""

    run = agent.run(user_input)
    print(agent.format_trace(run) if show_trace else run.answer)


def show_last_run(agent: WorkspaceAgent, show_trace: bool) -> int:
    """Print the latest persisted run if available."""

    checkpoint = agent.load_latest_checkpoint()
    if checkpoint is None:
        print("No checkpoint found.")
        return 1
    if show_trace:
        print(checkpoint.get("trace_text", ""))
    else:
        print(agent.format_checkpoint_summary())
    return 0


def list_runs(agent: WorkspaceAgent) -> int:
    """Print recent persisted runs."""

    print(agent.list_checkpoint_history())
    return 0


def list_session_memory(agent: WorkspaceAgent) -> int:
    """Print stored session memory records."""

    print(agent.list_session_memory())
    return 0


def list_task_memory(agent: WorkspaceAgent, session_id: str | None = None) -> int:
    """Print stored task memory records."""

    print(agent.list_task_memory(session_id=session_id))
    return 0


def replay_last_run(agent: WorkspaceAgent) -> int:
    """Print a replay report for the latest persisted checkpoint."""

    print(agent.replay_latest_checkpoint())
    return 0


def replay_run(agent: WorkspaceAgent, run_id: str) -> int:
    """Print a replay report for a checkpoint selected by run id."""

    print(agent.replay_checkpoint(run_id))
    return 0


def compare_last_two_runs(agent: WorkspaceAgent) -> int:
    """Print a replay diff report for the latest two persisted checkpoints."""

    print(agent.compare_latest_two_checkpoints())
    return 0


def compare_runs(agent: WorkspaceAgent, older_run_id: str, newer_run_id: str) -> int:
    """Print a replay diff report for two selected checkpoints."""

    print(agent.compare_checkpoints(older_run_id, newer_run_id))
    return 0


def resume_last_run(agent: WorkspaceAgent) -> int:
    """Print a checkpoint-guided resume report for the latest persisted checkpoint."""

    print(agent.resume_latest_checkpoint())
    return 0


def resume_run(agent: WorkspaceAgent, run_id: str) -> int:
    """Print a checkpoint-guided resume report for a checkpoint selected by run id."""

    print(agent.resume_checkpoint(run_id))
    return 0


def show_session_memory(agent: WorkspaceAgent, session_id: str | None) -> int:
    """Print one session memory record."""

    resolved_session_id = None if session_id == "" else session_id
    print(agent.format_session_memory(resolved_session_id))
    return 0


def show_task_memory(agent: WorkspaceAgent, task_id: str | None) -> int:
    """Print one task memory record."""

    resolved_task_id = None if task_id == "" else task_id
    print(agent.format_task_memory(resolved_task_id))
    return 0


def show_run(agent: WorkspaceAgent, run_id: str, show_trace: bool) -> int:
    """Print a checkpoint selected by run id."""

    checkpoint = agent.load_checkpoint(run_id)
    if checkpoint is None:
        print(f"No checkpoint found for run id: {run_id}")
        return 1
    if show_trace:
        print(checkpoint.get("trace_text", ""))
    else:
        from agent.persistence import format_checkpoint_summary

        print(format_checkpoint_summary(checkpoint))
    return 0


def interactive_loop(agent: WorkspaceAgent, show_trace: bool) -> None:
    """Start an interactive REPL-like loop."""

    print("Agent started. Type exit to quit.")
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


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    history_dir = Path(args.history_dir) if args.history_dir else None
    memory_dir = Path(args.memory_dir) if args.memory_dir else None
    llm_client = None
    if args.llm_planner:
        from agent import DeepSeekLLMClient

        llm_client = DeepSeekLLMClient()
    skill_policy = _build_skill_policy(args)
    agent = WorkspaceAgent(
        Path(args.root),
        llm_client=llm_client,
        history_dir=history_dir,
        memory_dir=memory_dir,
        session_id=args.session_id,
        task_id=args.task_id,
        use_graph_runtime=not args.classic_runtime,
        skill_policy=skill_policy,
    )
    if args.list_runs:
        return list_runs(agent)
    if args.list_session_memory:
        return list_session_memory(agent)
    if args.list_task_memory:
        return list_task_memory(agent, args.session_id)
    if args.replay_run:
        return replay_run(agent, args.replay_run)
    if args.replay_last_run:
        return replay_last_run(agent)
    if args.compare_runs:
        return compare_runs(agent, args.compare_runs[0], args.compare_runs[1])
    if args.compare_last_two_runs:
        return compare_last_two_runs(agent)
    if args.resume_run:
        return resume_run(agent, args.resume_run)
    if args.resume_last_run:
        return resume_last_run(agent)
    if args.show_session_memory is not None:
        return show_session_memory(agent, args.show_session_memory or args.session_id)
    if args.show_task_memory is not None:
        return show_task_memory(agent, args.show_task_memory or args.task_id)
    if args.show_run:
        return show_run(agent, args.show_run, args.trace)
    if args.show_last_run:
        return show_last_run(agent, args.trace)
    if args.input:
        run_once(agent, args.input, args.trace)
        return 0
    interactive_loop(agent, args.trace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
