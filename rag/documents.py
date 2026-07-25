"""Document loading helpers for local RAG experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SUPPORTED_SUFFIXES = {".md", ".txt"}


@dataclass(frozen=True)
class Document:
    """One loaded text document."""

    source: str  # 文档相对路径，最终会作为引用来源展示
    text: str  # 文档完整文本


def load_text_documents(root: Path, paths: tuple[str, ...] = ("README.md", "docs", "versions")) -> list[Document]:
    """Load supported text documents from selected workspace paths."""

    workspace_root = root.resolve()  # 固定工作区根目录，避免路径越界
    documents: list[Document] = []

    for raw_path in paths:
        target = _resolve_within_root(workspace_root, raw_path)
        if not target.exists():
            continue
        if target.is_file():
            loaded = _load_file(workspace_root, target)
            if loaded is not None:
                documents.append(loaded)
            continue
        documents.extend(_load_directory(workspace_root, target))

    return documents


def _load_directory(root: Path, directory: Path) -> list[Document]:
    """Load supported files from a directory in stable order."""

    documents: list[Document] = []
    for path in sorted(directory.rglob("*"), key=lambda item: str(item.relative_to(root))):
        if path.is_file():
            loaded = _load_file(root, path)
            if loaded is not None:
                documents.append(loaded)
    return documents


def _load_file(root: Path, path: Path) -> Document | None:
    """Load one supported text file."""

    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    return Document(source=str(path.relative_to(root)), text=text)


def _resolve_within_root(root: Path, raw_path: str) -> Path:
    """Resolve a path and reject paths outside the workspace."""

    candidate = (root / raw_path).resolve()
    if candidate == root or root in candidate.parents:
        return candidate
    raise ValueError(f"Path escapes workspace root: {raw_path}")
