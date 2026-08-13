"""Backend descriptors for production-oriented RAG hardening."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingBackendSpec:
    """Stable descriptor for one embedding backend."""

    name: str           # embedding 后端名
    version: str        # embedding 后端版本
    dimensions: int     # 向量维度
    provider: str       # 后端提供者

    def to_dict(self) -> dict[str, object]:
        """Render the backend spec as JSON-ready data."""

        return {
            "name": self.name,
            "version": self.version,
            "dimensions": self.dimensions,
            "provider": self.provider,
        }


@dataclass(frozen=True)
class IndexBackendSpec:
    """Stable descriptor for one index backend."""

    name: str               # 索引后端名
    version: str            # 索引后端版本
    storage_format: str     # 存储格式

    def to_dict(self) -> dict[str, str]:
        """Render the backend spec as JSON-ready data."""

        return {
            "name": self.name,
            "version": self.version,
            "storage_format": self.storage_format,
        }


LOCAL_EMBEDDING_BACKEND = EmbeddingBackendSpec(
    name="local_hash_embedding",
    version="v1",
    dimensions=64,
    provider="local",
)

JSON_VECTOR_INDEX_BACKEND = IndexBackendSpec(
    name="json_vector_index",
    version="v1",
    storage_format="json",
)
