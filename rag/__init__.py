"""Local retrieval package for the Agent learning workspace."""

from .backends import EmbeddingBackendSpec, IndexBackendSpec
from .citations import CitationValidationResult, validate_answer_citations
from .chunking import TextChunk, chunk_document, chunk_documents
from .documents import Document, load_text_documents
from .embeddings import LocalEmbeddingModel, cosine_similarity
from .llm_qa import GroundedRAGAnswer, answer_question_with_llm, build_grounded_rag_prompt
from .qa import RAGAnswer, VectorRAGAnswer, answer_question, answer_question_with_vector_index
from .retrieval import SearchResult, retrieve
from .vector_index import (
    VectorIndex,
    VectorIndexUpdatePlan,
    VectorRecord,
    VectorSearchResult,
    build_vector_index,
    build_document_fingerprints,
    load_vector_index,
    plan_vector_index_update,
    save_vector_index,
    search_vector_index,
    update_vector_index,
)

__all__ = [
    "CitationValidationResult",
    "Document",
    "EmbeddingBackendSpec",
    "GroundedRAGAnswer",
    "IndexBackendSpec",
    "LocalEmbeddingModel",
    "RAGAnswer",
    "SearchResult",
    "TextChunk",
    "VectorIndex",
    "VectorIndexUpdatePlan",
    "VectorRAGAnswer",
    "VectorRecord",
    "VectorSearchResult",
    "answer_question",
    "answer_question_with_vector_index",
    "answer_question_with_llm",
    "build_document_fingerprints",
    "build_grounded_rag_prompt",
    "build_vector_index",
    "chunk_document",
    "chunk_documents",
    "cosine_similarity",
    "load_text_documents",
    "load_vector_index",
    "plan_vector_index_update",
    "retrieve",
    "save_vector_index",
    "search_vector_index",
    "update_vector_index",
    "validate_answer_citations",
]
