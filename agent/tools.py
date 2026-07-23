"""Local tools available to the workspace agent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


MAX_FILE_BYTES = 64_000


class ToolError(Exception):
    """Raised when a tool cannot safely complete the request."""


@dataclass(frozen=True)
class ToolResult:
    """Standard tool output wrapper."""

    tool_name: str
    output: str


def _resolve_within_root(root: Path, raw_path: str) -> Path:
    """Resolve a path and ensure it stays inside the workspace root."""

    root = root.resolve()
    candidate = (root / raw_path).resolve() if not Path(raw_path).is_absolute() else Path(raw_path).resolve()
    if candidate == root:
        return candidate
    if root not in candidate.parents:
        raise ToolError(f"路径越界：{raw_path}")
    return candidate


def read_file(root: Path, raw_path: str) -> ToolResult:
    """Read a text file from the workspace root."""

    path = _resolve_within_root(root, raw_path)
    if not path.exists():
        raise ToolError(f"文件不存在：{raw_path}")
    if not path.is_file():
        raise ToolError(f"不是文件：{raw_path}")
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise ToolError(f"文件过大，拒绝读取：{raw_path}（{size} bytes）")

    text = path.read_text(encoding="utf-8", errors="replace")
    header = f"[read_file] {path.relative_to(root.resolve())}"
    return ToolResult("read_file", f"{header}\n{text}")


def list_dir(root: Path, raw_path: str = ".") -> ToolResult:
    """List a directory inside the workspace root."""

    path = _resolve_within_root(root, raw_path)
    if not path.exists():
        raise ToolError(f"目录不存在：{raw_path}")
    if not path.is_dir():
        raise ToolError(f"不是目录：{raw_path}")

    items = []
    for child in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        suffix = "/" if child.is_dir() else ""
        items.append(f"- {child.name}{suffix}")
    header = f"[list_dir] {path.relative_to(root.resolve())}"
    body = "\n".join(items) if items else "- <empty>"
    return ToolResult("list_dir", f"{header}\n{body}")

