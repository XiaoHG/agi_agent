"""Command-line demo for DeepSeek-grounded local RAG."""

from __future__ import annotations

import argparse
from pathlib import Path

from agent.llm import LLMError
from rag import answer_question_with_llm


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the DeepSeek RAG demo."""

    parser = argparse.ArgumentParser(description="DeepSeek-grounded local RAG demo")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--question", required=True, help="question to answer with local context and DeepSeek")
    parser.add_argument("--top-k", type=int, default=3, help="number of chunks to send to the LLM")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        answer = answer_question_with_llm(Path(args.root), args.question, top_k=args.top_k)
    except LLMError as error:
        print(f"RAG LLM request failed: {error}")
        return 1

    print(answer.to_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
