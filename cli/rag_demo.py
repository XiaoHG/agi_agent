"""Command-line demo for local RAG retrieval."""

from __future__ import annotations

import argparse
from pathlib import Path

from rag import answer_question


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the RAG demo."""

    parser = argparse.ArgumentParser(description="Local RAG demo")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--question", required=True, help="question to search in local project documents")
    parser.add_argument("--top-k", type=int, default=3, help="number of chunks to return")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    answer = answer_question(Path(args.root), args.question, top_k=args.top_k)
    print(answer.to_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
