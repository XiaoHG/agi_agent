#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def render_one(source: Path, output: Path, scale: int, width: int) -> None:
    if not shutil.which("npx"):
        raise RuntimeError("Missing `npx`; install Node.js tooling first.")
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "npx",
        "-y",
        "@mermaid-js/mermaid-cli",
        "-i",
        str(source),
        "-o",
        str(output),
        "-s",
        str(scale),
        "-w",
        str(width),
        "-b",
        "white",
    ]
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, nargs="+")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--width", type=int, default=2400)
    args = parser.parse_args()

    for source in args.source:
        source = source.resolve()
        if not source.exists():
            raise FileNotFoundError(source)
        if args.output_dir:
            output = args.output_dir.resolve() / f"{source.stem}.png"
        else:
            output = source.with_suffix(".png")
        render_one(source, output, args.scale, args.width)
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
