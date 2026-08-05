"""Local retrieval package for the Agent learning workspace."""

from .chunking import TextChunk, chunk_document, chunk_documents
from .documents import Document, load_text_documents
from .embeddings import LocalEmbeddingModel, cosine_similarity
from .llm_qa import GroundedRAGAnswer, answer_question_with_llm, build_grounded_rag_prompt
from .qa import RAGAnswer, VectorRAGAnswer, answer_question, answer_question_with_vector_index
from .retrieval import SearchResult, retrieve
from .vector_index import (
    VectorIndex,
    VectorRecord,
    VectorSearchResult,
    build_vector_index,
    load_vector_index,
    save_vector_index,
    search_vector_index,
)

__all__ = [
    "Document",
    "GroundedRAGAnswer",
    "LocalEmbeddingModel",
    "RAGAnswer",
    "SearchResult",
    "TextChunk",
    "VectorIndex",
    "VectorRAGAnswer",
    "VectorRecord",
    "VectorSearchResult",
    "answer_question",
    "answer_question_with_vector_index",
    "answer_question_with_llm",
    "build_grounded_rag_prompt",
    "build_vector_index",
    "chunk_document",
    "chunk_documents",
    "cosine_similarity",
    "load_text_documents",
    "load_vector_index",
    "retrieve",
    "save_vector_index",
    "search_vector_index",
]
