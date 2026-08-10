"""Command-line entrypoint for regression evals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agent import WorkspaceAgent
from evals.matrix import format_eval_matrix_report, load_eval_matrix, run_eval_matrix
from evals.runner import build_eval_report, load_eval_cases, run_eval_cases


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for eval runs."""

    parser = argparse.ArgumentParser(description="Run deterministic agent eval cases")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--cases", default="evals/regression_cases.json", help="eval case JSON path")
    parser.add_argument("--matrix", help="industrial eval matrix JSON path")
    parser.add_argument("--failure-bench", help="industrial failure bench JSON path")
    parser.add_argument("--output", help="optional JSON report output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)
    if args.matrix:
        matrix = load_eval_matrix(root / args.matrix)
        matrix_report = run_eval_matrix(root, matrix)
        report = matrix_report.to_dict()
        text = json.dumps(report, ensure_ascii=False, indent=2)
        console_text = format_eval_matrix_report(matrix_report)
        exit_code = 0 if report["failed"] == 0 else 1
    elif args.failure_bench:
        matrix = load_eval_matrix(root / args.failure_bench)
        matrix_report = run_eval_matrix(root, matrix)
        report = matrix_report.to_dict()
        text = json.dumps(report, ensure_ascii=False, indent=2)
        console_text = format_eval_matrix_report(matrix_report)
        exit_code = 0 if report["failed"] == 0 else 1
    else:
        cases = load_eval_cases(root / args.cases)
        agent = WorkspaceAgent(root)
        report = build_eval_report(run_eval_cases(agent, cases))
        text = json.dumps(report, ensure_ascii=False, indent=2)
        console_text = text
        exit_code = 0 if report["failed"] == 0 else 1

    if args.output:
        output_path = root / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")

    print(console_text)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
