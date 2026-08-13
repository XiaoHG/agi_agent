"""Vector index helpers for local professional RAG."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .backends import JSON_VECTOR_INDEX_BACKEND, IndexBackendSpec
from .chunking import TextChunk, chunk_documents
from .documents import Document, load_text_documents
from .embeddings import LocalEmbeddingModel, cosine_similarity, tokenize_terms


VECTOR_INDEX_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class VectorRecord:
    """One vector-indexed chunk with citation metadata."""

    chunk: TextChunk                # 对应的文本块
    embedding: tuple[float, ...]    # 向量表示
    metadata: dict[str, Any]        # 附加元数据

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

    records: list[VectorRecord]                             # 索引记录
    dimensions: int                                         # 向量维度
    schema_version: int = VECTOR_INDEX_SCHEMA_VERSION       # 索引 schema 版本
    embedding_backend: dict[str, Any] | None = None         # embedding 后端描述
    index_backend: dict[str, Any] | None = None             # index 后端描述
    document_fingerprints: dict[str, str] | None = None     # source -> fingerprint

    def to_dict(self) -> dict[str, Any]:
        """Export the index to JSON-ready data."""

        return {
            "schema_version": self.schema_version,
            "dimensions": self.dimensions,
            "embedding_backend": self.embedding_backend,
            "index_backend": self.index_backend,
            "document_fingerprints": self.document_fingerprints or {},
            "records": [record.to_dict() for record in self.records],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "VectorIndex":
        """Load a vector index from JSON-ready data."""

        return cls(
            records=[VectorRecord.from_dict(record) for record in payload.get("records", [])],
            dimensions=int(payload["dimensions"]),
            schema_version=int(payload.get("schema_version", VECTOR_INDEX_SCHEMA_VERSION)),
            embedding_backend=dict(payload.get("embedding_backend", {})) or None,
            index_backend=dict(payload.get("index_backend", {})) or None,
            document_fingerprints=dict(payload.get("document_fingerprints", {})) or None,
        )


@dataclass(frozen=True)
class VectorSearchResult:
    """One vector retrieval result with source citation."""

    record: VectorRecord    # 命中的记录
    score: float            # 相似度分数

    @property
    def chunk(self) -> TextChunk:
        """Expose the underlying chunk for prompt compatibility."""

        return self.record.chunk

    def citation(self) -> str:
        """Return the source label used for grounded answers."""

        return self.record.chunk.source_label()


@dataclass(frozen=True)
class VectorIndexUpdatePlan:
    """Incremental update plan for one vector index rebuild."""

    added_sources: tuple[str, ...] = ()         # 新增文档
    changed_sources: tuple[str, ...] = ()       # 内容变化文档
    removed_sources: tuple[str, ...] = ()       # 被移除文档
    unchanged_sources: tuple[str, ...] = ()     # 未变化文档

    def to_dict(self) -> dict[str, object]:
        """Render the update plan as JSON-ready data."""

        return {
            "added_sources": list(self.added_sources),
            "changed_sources": list(self.changed_sources),
            "removed_sources": list(self.removed_sources),
            "unchanged_sources": list(self.unchanged_sources),
        }


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
    document_fingerprints = build_document_fingerprints(documents)
    records = build_vector_records(documents, model, max_lines=max_lines, overlap=overlap)
    return VectorIndex(
        records=records,
        dimensions=model.dimensions,
        embedding_backend=model.describe_backend(),
        index_backend=IndexBackendSpec(
            name=JSON_VECTOR_INDEX_BACKEND.name,
            version=JSON_VECTOR_INDEX_BACKEND.version,
            storage_format=JSON_VECTOR_INDEX_BACKEND.storage_format,
        ).to_dict(),
        document_fingerprints=document_fingerprints,
    )


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


def plan_vector_index_update(
    root: Path,
    current_index: VectorIndex | None,
    *,
    paths: tuple[str, ...] = ("README.md", "docs", "versions"),
) -> VectorIndexUpdatePlan:
    """Plan which sources need rebuilding for an incremental update."""

    documents = load_text_documents(root, paths=paths)
    current = current_index.document_fingerprints or {} if current_index is not None else {}
    latest = build_document_fingerprints(documents)
    added = tuple(sorted(source for source in latest if source not in current))
    changed = tuple(sorted(source for source, fingerprint in latest.items() if source in current and current[source] != fingerprint))
    removed = tuple(sorted(source for source in current if source not in latest))
    unchanged = tuple(sorted(source for source, fingerprint in latest.items() if current.get(source) == fingerprint))
    return VectorIndexUpdatePlan(
        added_sources=added,
        changed_sources=changed,
        removed_sources=removed,
        unchanged_sources=unchanged,
    )


def update_vector_index(
    root: Path,
    current_index: VectorIndex | None,
    *,
    paths: tuple[str, ...] = ("README.md", "docs", "versions"),
    max_lines: int = 40,
    overlap: int = 5,
    embedding_model: LocalEmbeddingModel | None = None,
) -> tuple[VectorIndex, VectorIndexUpdatePlan]:
    """Incrementally update a vector index by rebuilding only changed sources."""

    model = embedding_model or LocalEmbeddingModel()
    documents = load_text_documents(root, paths=paths)
    plan = plan_vector_index_update(root, current_index, paths=paths)
    if current_index is None:
        return build_vector_index(
            root,
            paths=paths,
            max_lines=max_lines,
            overlap=overlap,
            embedding_model=model,
        ), plan

    changed_sources = set(plan.added_sources + plan.changed_sources + plan.removed_sources)
    preserved = [
        record
        for record in current_index.records
        if record.chunk.source not in changed_sources
    ]
    rebuilt_documents = [document for document in documents if document.source in set(plan.added_sources + plan.changed_sources)]
    rebuilt_records = build_vector_records(rebuilt_documents, model, max_lines=max_lines, overlap=overlap)
    latest_fingerprints = build_document_fingerprints(documents)
    next_index = VectorIndex(
        records=sorted(
            [*preserved, *rebuilt_records],
            key=lambda record: (record.chunk.source, record.chunk.start_line, record.chunk.end_line),
        ),
        dimensions=model.dimensions,
        schema_version=current_index.schema_version,
        embedding_backend=model.describe_backend(),
        index_backend=current_index.index_backend or JSON_VECTOR_INDEX_BACKEND.to_dict(),
        document_fingerprints=latest_fingerprints,
    )
    return next_index, plan


def build_vector_records(
    documents: list[Document],
    embedding_model: LocalEmbeddingModel,
    *,
    max_lines: int = 40,
    overlap: int = 5,
) -> list[VectorRecord]:
    """Build vector records from documents with stable metadata."""

    chunks = chunk_documents(documents, max_lines=max_lines, overlap=overlap)
    return [
        VectorRecord(
            chunk=chunk,
            embedding=embedding_model.embed(chunk.text),
            metadata={
                "source": chunk.source,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "citation": chunk.source_label(),
                "document_fingerprint": _document_fingerprint(chunk.source, next(document.text for document in documents if document.source == chunk.source)),
                "embedding_backend": embedding_model.describe_backend(),
            },
        )
        for chunk in chunks
    ]


def build_document_fingerprints(documents: list[Document]) -> dict[str, str]:
    """Build stable source fingerprints for incremental index updates."""

    return {
        document.source: _document_fingerprint(document.source, document.text)
        for document in documents
    }


def _document_fingerprint(source: str, text: str) -> str:
    """Build a stable fingerprint for one source document."""

    return sha256(f"{source}\n{text}".encode("utf-8")).hexdigest()
