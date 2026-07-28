"""Command-line demo for the minimal LangGraph RAG workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

from integrations.langgraph_workflow import run_rag_graph


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the LangGraph demo."""

    parser = argparse.ArgumentParser(description="LangGraph RAG workflow demo")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--question", required=True, help="question for the LangGraph RAG workflow")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    result = run_rag_graph(Path(args.root), args.question)

    print("LangGraph result:")
    print(f"Selected tool: {result.get('selected_tool')}")
    print(f"Steps: {' -> '.join(result.get('steps', []))}")
    print()
    print(result.get("answer", ""))
    return 0 if not result.get("error") else 1


if __name__ == "__main__":
    raise SystemExit(main())
