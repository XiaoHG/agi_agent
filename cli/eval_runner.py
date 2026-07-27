"""Command-line entrypoint for regression evals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent import WorkspaceAgent
from evals.runner import build_eval_report, load_eval_cases, run_eval_cases


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for eval runs."""

    parser = argparse.ArgumentParser(description="Run deterministic agent eval cases")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--cases", default="evals/regression_cases.json", help="eval case JSON path")
    parser.add_argument("--output", help="optional JSON report output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)
    cases = load_eval_cases(root / args.cases)
    agent = WorkspaceAgent(root)
    report = build_eval_report(run_eval_cases(agent, cases))
    text = json.dumps(report, ensure_ascii=False, indent=2)

    if args.output:
        output_path = root / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")

    print(text)
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
