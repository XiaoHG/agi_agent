"""Question answering helpers built on top of local retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .chunking import chunk_documents
from .documents import load_text_documents
from .retrieval import SearchResult, retrieve


@dataclass(frozen=True)
class RAGAnswer:
    """A deterministic answer produced from retrieved local context."""

    question: str  # 原始问题
    results: list[SearchResult]  # 检索结果

    def to_text(self) -> str:
        """Render the answer with source references."""

        if not self.results:
            return (
                f"Result: no local context was found for '{self.question}'.\n\n"
                "Sources: none\n\n"
                "Next step: add more documents or ask with more specific keywords."
            )

        parts = [f"Result: found {len(self.results)} relevant local context chunk(s) for '{self.question}'."]
        for index, result in enumerate(self.results, start=1):
            parts.append(
                "\n".join(
                    [
                        f"Source {index}: {result.chunk.source_label()}",
                        f"Score: {result.score}",
                        f"Matched terms: {', '.join(result.matched_terms)}",
                        "Context:",
                        _preview(result.chunk.text),
                    ]
                )
            )
        return "\n\n".join(parts)


def answer_question(root: Path, question: str, top_k: int = 3) -> RAGAnswer:
    """Answer a question by retrieving local project documents."""

    documents = load_text_documents(root)
    chunks = chunk_documents(documents)
    results = retrieve(chunks, question, top_k=top_k)
    return RAGAnswer(question=question, results=results)


def _preview(text: str, limit: int = 8) -> str:
    """Return a short context preview."""

    lines = [line for line in text.splitlines() if line.strip()]
    head = lines[:limit]
    if len(lines) > limit:
        head.append("... (truncated)")
    return "\n".join(head)
