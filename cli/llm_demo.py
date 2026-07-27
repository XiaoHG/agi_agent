"""Command-line entrypoint for real DeepSeek LLM reasoning."""

from __future__ import annotations

import argparse

from agent.llm import DeepSeekLLMClient, LLMError


DEFAULT_SYSTEM_PROMPT = (
    "You are a professional agent engineering teacher. "
    "Explain agent development concepts clearly and give practical engineering guidance."
)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for real LLM calls."""

    parser = argparse.ArgumentParser(description="Real DeepSeek LLM reasoning demo")
    parser.add_argument("--input", required=True, help="user input for the LLM")
    parser.add_argument("--system", default=DEFAULT_SYSTEM_PROMPT, help="system prompt")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Program entrypoint."""

    parser = build_parser()
    args = parser.parse_args(argv)

    client = DeepSeekLLMClient()
    try:
        response = client.complete(args.input, system_prompt=args.system)
    except LLMError as error:
        print(f"LLM request failed: {error}")
        return 1

    print(response.content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
