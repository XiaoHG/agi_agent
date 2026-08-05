"""Vector index helpers for local professional RAG."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .chunking import TextChunk, chunk_documents
from .documents import load_text_documents
from .embeddings import LocalEmbeddingModel, cosine_similarity, tokenize_terms


VECTOR_INDEX_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class VectorRecord:
    """One vector-indexed chunk with citation metadata."""

    chunk: TextChunk
    embedding: tuple[float, ...]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Export the record to JSON-ready data."""

        return {
            "chunk_id": self.chunk.chunk_id,
            "source": self.chunk.source,
            "start_line": self.chunk.start_line,
            "end_line": self.chunk.end_line,
            "text": self.chunk.text,
            "embedding": list(self.embedding),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VectorRecord":
        """Load one vector record from JSON-ready data."""

        chunk = TextChunk(
            chunk_id=str(payload["chunk_id"]),
            source=str(payload["source"]),
            start_line=int(payload["start_line"]),
            end_line=int(payload["end_line"]),
            text=str(payload["text"]),
        )
        return cls(
            chunk=chunk,
            embedding=tuple(float(value) for value in payload["embedding"]),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True)
class VectorIndex:
    """In-memory vector index for local RAG chunks."""

    records: list[VectorRecord]
    dimensions: int
    schema_version: int = VECTOR_INDEX_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Export the index to JSON-ready data."""

        return {
            "schema_version": self.schema_version,
            "dimensions": self.dimensions,
            "records": [record.to_dict() for record in self.records],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VectorIndex":
        """Load a vector index from JSON-ready data."""

        return cls(
            records=[VectorRecord.from_dict(record) for record in payload.get("records", [])],
            dimensions=int(payload["dimensions"]),
            schema_version=int(payload.get("schema_version", VECTOR_INDEX_SCHEMA_VERSION)),
        )


@dataclass(frozen=True)
class VectorSearchResult:
    """One vector retrieval result with source citation."""

    record: VectorRecord
    score: float

    @property
    def chunk(self) -> TextChunk:
        """Expose the underlying chunk for prompt compatibility."""

        return self.record.chunk

    def citation(self) -> str:
        """Return the source label used for grounded answers."""

        return self.record.chunk.source_label()


def build_vector_index(
    root: Path,
    *,
    paths: tuple[str, ...] = ("README.md", "docs", "versions"),
    max_lines: int = 40,
    overlap: int = 5,
    embedding_model: LocalEmbeddingModel | None = None,
) -> VectorIndex:
    """Load documents, chunk them, and build a local vector index."""

    model = embedding_model or LocalEmbeddingModel()
    documents = load_text_documents(root, paths=paths)
    chunks = chunk_documents(documents, max_lines=max_lines, overlap=overlap)
    records = [
        VectorRecord(
            chunk=chunk,
            embedding=model.embed(chunk.text),
            metadata={
                "source": chunk.source,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "citation": chunk.source_label(),
            },
        )
        for chunk in chunks
    ]
    return VectorIndex(records=records, dimensions=model.dimensions)


def search_vector_index(
    index: VectorIndex,
    query: str,
    *,
    top_k: int = 3,
    embedding_model: LocalEmbeddingModel | None = None,
) -> list[VectorSearchResult]:
    """Search a vector index with cosine similarity."""

    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")
    if not query.strip():
        return []
    query_terms = set(tokenize_terms(query))
    if not query_terms:
        return []
    model = embedding_model or LocalEmbeddingModel(index.dimensions)
    query_embedding = model.embed(query)
    results = [
        VectorSearchResult(record=record, score=cosine_similarity(query_embedding, record.embedding))
        for record in index.records
        if query_terms.intersection(tokenize_terms(record.chunk.text))
    ]
    positive_results = [result for result in results if result.score > 0]
    return sorted(
        positive_results,
        key=lambda result: (-result.score, result.record.chunk.source, result.record.chunk.start_line),
    )[:top_k]


def save_vector_index(index: VectorIndex, path: Path) -> Path:
    """Save a vector index as JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_vector_index(path: Path) -> VectorIndex:
    """Load a vector index from JSON."""

    return VectorIndex.from_dict(json.loads(path.read_text(encoding="utf-8")))
