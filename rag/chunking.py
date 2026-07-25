"""Text chunking helpers for local RAG experiments."""

from __future__ import annotations

from dataclasses import dataclass

from .documents import Document


@dataclass(frozen=True)
class TextChunk:
    """A searchable piece of a document."""

    chunk_id: str  # 稳定 chunk ID，方便 trace 和测试断言
    source: str  # 原始文档路径
    start_line: int  # chunk 起始行号，从 1 开始
    end_line: int  # chunk 结束行号
    text: str  # chunk 文本

    def source_label(self) -> str:
        """Return a compact source label for user-facing output."""

        return f"{self.source}:{self.start_line}-{self.end_line}"


def chunk_document(document: Document, max_lines: int = 40, overlap: int = 5) -> list[TextChunk]:
    """Split one document into overlapping line-based chunks."""

    if max_lines <= 0:
        raise ValueError("max_lines must be greater than zero")
    if overlap < 0:
        raise ValueError("overlap must not be negative")
    if overlap >= max_lines:
        raise ValueError("overlap must be smaller than max_lines")

    lines = document.text.splitlines()
    if not lines:
        return []

    chunks: list[TextChunk] = []
    start = 0
    index = 1
    step = max_lines - overlap

    while start < len(lines):
        end = min(start + max_lines, len(lines))
        chunk_lines = lines[start:end]
        chunks.append(
            TextChunk(
                chunk_id=f"{document.source}#{index}",
                source=document.source,
                start_line=start + 1,
                end_line=end,
                text="\n".join(chunk_lines),
            )
        )
        if end == len(lines):
            break
        start += step
        index += 1

    return chunks


def chunk_documents(documents: list[Document], max_lines: int = 40, overlap: int = 5) -> list[TextChunk]:
    """Split multiple documents into chunks."""

    chunks: list[TextChunk] = []
    for document in documents:
        chunks.extend(chunk_document(document, max_lines=max_lines, overlap=overlap))
    return chunks
