"""Command-line entrypoint for the release gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evals.release_gate import format_release_gate_report, run_release_gate


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the release gate."""

    parser = argparse.ArgumentParser(description="Run the release gate checks")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument("--output", help="optional JSON report output path")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)

    report = run_release_gate(root)
    text = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    if args.output:
        output_path = root / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")

    print(format_release_gate_report(report))
    return 0 if report.release_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
