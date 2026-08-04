"""Command-line demo for the minimal LangGraph RAG workflow."""

from __future__ import annotations

import argparse
from pathlib import Path
from uuid import uuid4

from agent import RunCheckpointStore, build_graph_checkpoint
from integrations.langgraph_workflow import run_rag_graph


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the LangGraph demo."""

    parser = argparse.ArgumentParser(description="LangGraph RAG workflow demo")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--question", required=True, help="question for the LangGraph RAG workflow")
    parser.add_argument(
        "--history-dir",
        default=None,
        help="checkpoint directory; defaults to <root>/logs/graph-runs",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    result = run_rag_graph(Path(args.root), args.question)
    if args.history_dir is not None:
        history_dir = Path(args.history_dir)
    else:
        history_dir = Path(args.root) / "logs" / "graph-runs"
    store = RunCheckpointStore(history_dir)
    checkpoint = build_graph_checkpoint(
        run_id=uuid4().hex[:8],
        graph_state=result,
        graph_text=_format_graph_output(result),
    )
    store.save(checkpoint)

    print("LangGraph result:")
    print(f"Route: {result.get('route')}")
    print(f"Route reason: {result.get('route_reason')}")
    print(f"Selected tool: {result.get('selected_tool')}")
    print(f"Steps: {' -> '.join(result.get('steps', []))}")
    print()
    print(result.get("answer", ""))
    return 0 if not result.get("error") else 1


def _format_graph_output(result: dict[str, object]) -> str:
    """Render the LangGraph demo output for checkpoint storage."""

    return (
        "LangGraph result:\n"
        f"Route: {result.get('route')}\n"
        f"Route reason: {result.get('route_reason')}\n"
        f"Selected tool: {result.get('selected_tool')}\n"
        f"Steps: {' -> '.join(result.get('steps', []))}\n\n"
        f"{result.get('answer', '')}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
