from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


def load_prompt(relative_path: str) -> str:
    path = ROOT_DIR / relative_path
    return path.read_text(encoding="utf-8")


def load_system_prompt() -> str:
    return load_prompt("prompts/agent-system.v1.md")


def load_tool_router_prompt() -> str:
    return load_prompt("prompts/tool-router.v1.md")

