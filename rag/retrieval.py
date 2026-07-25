"""Deterministic keyword retrieval for local RAG experiments."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re

from .chunking import TextChunk


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_\-]+")
STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "for",
    "in",
    "is",
    "me",
    "of",
    "on",
    "please",
    "search",
    "the",
    "to",
    "what",
}


@dataclass(frozen=True)
class SearchResult:
    """One retrieved chunk with ranking metadata."""

    chunk: TextChunk  # 命中的文本块
    score: int  # 简单关键词分数
    matched_terms: tuple[str, ...]  # 命中的关键词


def retrieve(chunks: list[TextChunk], query: str, top_k: int = 3) -> list[SearchResult]:
    """Return the best matching chunks for a query."""

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    query_terms = _tokenize(query)
    if not query_terms:
        return []

    results: list[SearchResult] = []
    for chunk in chunks:
        chunk_terms = Counter(_tokenize(chunk.text))
        matched = tuple(term for term in query_terms if chunk_terms.get(term, 0) > 0)
        score = sum(chunk_terms[term] for term in matched)
        if score > 0:
            results.append(SearchResult(chunk=chunk, score=score, matched_terms=matched))

    return sorted(results, key=lambda result: (-result.score, result.chunk.source, result.chunk.start_line))[:top_k]


def _tokenize(text: str) -> tuple[str, ...]:
    """Normalize text into searchable terms."""

    terms = [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]
    return tuple(term for term in terms if term not in STOPWORDS and len(term) > 1)
