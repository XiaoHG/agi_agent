"""Question answering helpers built on top of local retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .chunking import chunk_documents
from .documents import load_text_documents
from .retrieval import SearchResult, retrieve
from .vector_index import VectorSearchResult, build_vector_index, search_vector_index


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


@dataclass(frozen=True)
class VectorRAGAnswer:
    """A deterministic answer produced from vector-indexed local context."""

    question: str  # 原始问题
    results: list[VectorSearchResult]  # 向量检索结果

    def to_text(self) -> str:
        """Render vector retrieval results with explicit citations."""

        if not self.results:
            return (
                f"Result: no vector context was found for '{self.question}'.\n\n"
                "Citations: none\n\n"
                "Next step: rebuild the RAG index or ask with more specific context."
            )

        parts = [f"Result: found {len(self.results)} vector context chunk(s) for '{self.question}'."]
        for index, result in enumerate(self.results, start=1):
            parts.append(
                "\n".join(
                    [
                        f"Citation {index}: {result.citation()}",
                        f"Vector score: {result.score:.3f}",
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


def answer_question_with_vector_index(root: Path, question: str, top_k: int = 3) -> VectorRAGAnswer:
    """Answer a question by searching a local vector index."""

    index = build_vector_index(root)
    results = search_vector_index(index, question, top_k=top_k)
    return VectorRAGAnswer(question=question, results=results)


def _preview(text: str, limit: int = 8) -> str:
    """Return a short context preview."""

    lines = [line for line in text.splitlines() if line.strip()]
    head = lines[:limit]
    if len(lines) > limit:
        head.append("... (truncated)")
    return "\n".join(head)
