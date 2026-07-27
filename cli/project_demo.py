"""Command-line demo for the comprehensive project learning assistant."""

from __future__ import annotations

import argparse
from pathlib import Path

from agent.project import ProjectLearningAssistant


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the project demo."""

    parser = argparse.ArgumentParser(description="Project learning assistant demo")
    parser.add_argument("--root", default=".", help="workspace root")
    parser.add_argument(
        "--objective",
        default="Build a project learning assistant report.",
        help="project demo objective",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)

    assistant = ProjectLearningAssistant(Path(args.root))
    report = assistant.run(args.objective)
    print(report.to_text())
    return 0 if report.regression_report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
