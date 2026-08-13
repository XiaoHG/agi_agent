"""Command-line entrypoint for rebuilding and querying the local RAG vector index."""

from __future__ import annotations

import argparse
from pathlib import Path

from rag import build_vector_index, load_vector_index, plan_vector_index_update, save_vector_index, search_vector_index, update_vector_index


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the RAG index demo."""

    parser = argparse.ArgumentParser(description="Local RAG vector index demo")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--output", default="data/rag-index.json", help="where to write the vector index")
    parser.add_argument("--question", default=None, help="optional query to run after rebuilding the index")
    parser.add_argument("--top-k", type=int, default=3, help="number of vector results to show")
    parser.add_argument("--incremental", action="store_true", help="incrementally update an existing index when possible")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)
    output_path = root / args.output
    existing_index = load_vector_index(output_path) if args.incremental and output_path.exists() else None
    if args.incremental:
        plan = plan_vector_index_update(root, existing_index)
        index, _ = update_vector_index(root, existing_index)
        print(f"Incremental update plan: {plan.to_dict()}")
    else:
        index = build_vector_index(root)
    output_path = save_vector_index(index, output_path)
    print(f"Vector index saved: {output_path}")
    print(f"Records: {len(index.records)}")
    print(f"Dimensions: {index.dimensions}")
    if index.embedding_backend:
        print(f"Embedding backend: {index.embedding_backend['name']} ({index.embedding_backend['version']})")

    if args.question:
        print()
        print(f"Query: {args.question}")
        for result in search_vector_index(index, args.question, top_k=args.top_k):
            print(f"- {result.citation()} score={result.score:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
