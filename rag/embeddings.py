"""Deterministic local embeddings for professional RAG experiments."""

from __future__ import annotations

from hashlib import sha256
import math
import re

from .backends import EmbeddingBackendSpec, LOCAL_EMBEDDING_BACKEND


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


class LocalEmbeddingModel:
    """Small hashing-based embedding model for offline vector retrieval."""

    def __init__(self, dimensions: int = 64) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be greater than zero")
        self.dimensions = dimensions
        self.backend = EmbeddingBackendSpec(
            name=LOCAL_EMBEDDING_BACKEND.name,
            version=LOCAL_EMBEDDING_BACKEND.version,
            dimensions=dimensions,
            provider=LOCAL_EMBEDDING_BACKEND.provider,
        )

    def embed(self, text: str) -> tuple[float, ...]:
        """Embed text into a normalized deterministic vector."""

        vector = [0.0] * self.dimensions
        for token in tokenize_terms(text):
            digest = sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return tuple(vector)
        return tuple(value / norm for value in vector)

    def describe_backend(self) -> dict[str, object]:
        """Describe the embedding backend in JSON-ready form."""

        return self.backend.to_dict()


def cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    """Return cosine similarity for normalized local embedding vectors."""

    if len(left) != len(right):
        raise ValueError("vectors must have the same dimensions")
    return sum(left_value * right_value for left_value, right_value in zip(left, right))


def tokenize_terms(text: str) -> tuple[str, ...]:
    """Normalize text into embedding terms."""

    terms = [match.group(0).lower() for match in TOKEN_PATTERN.finditer(text)]
    return tuple(term for term in terms if term not in STOPWORDS and len(term) > 1)
