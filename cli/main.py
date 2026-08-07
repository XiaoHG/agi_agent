"""Command-line entrypoint for the workspace agent."""

from __future__ import annotations

import argparse
from pathlib import Path

from agent import WorkspaceAgent


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the agent."""

    parser = argparse.ArgumentParser(description="Minimal workspace agent")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument(
        "--history-dir",
        default=None,
        help="checkpoint directory; defaults to <root>/logs/agent-runs",
    )
    parser.add_argument("--list-runs", action="store_true", help="list recent checkpoints")
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
    parser.add_argument("--llm-planner", action="store_true", help="use real DeepSeek planning for LangGraph runs")
    parser.add_argument("--classic-runtime", action="store_true", help="disable the default LangGraph runtime wrapper")
    parser.add_argument("--trace", action="store_true", help="print reasoning trace")
    return parser


def run_once(agent: WorkspaceAgent, user_input: str, show_trace: bool) -> None:
    """Run one input through the agent and print the result."""

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


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    history_dir = Path(args.history_dir) if args.history_dir else None
    llm_client = None
    if args.llm_planner:
        from agent import DeepSeekLLMClient

        llm_client = DeepSeekLLMClient()
    agent = WorkspaceAgent(
        Path(args.root),
        llm_client=llm_client,
        history_dir=history_dir,
        use_graph_runtime=not args.classic_runtime,
    )
    if args.list_runs:
        return list_runs(agent)
    if args.replay_run:
        return replay_run(agent, args.replay_run)
    if args.replay_last_run:
        return replay_last_run(agent)
    if args.compare_runs:
        return compare_runs(agent, args.compare_runs[0], args.compare_runs[1])
    if args.compare_last_two_runs:
        return compare_last_two_runs(agent)
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
