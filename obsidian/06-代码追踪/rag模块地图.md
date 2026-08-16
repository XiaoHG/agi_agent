# rag模块地图

## 模块职责

`rag/` 负责文档加载、切分、embedding、索引、检索、引用和 grounded QA。

## 主要文件

- [rag/vector_index.py](../../rag/vector_index.py)
- [rag/retrieval.py](../../rag/retrieval.py)
- [rag/embeddings.py](../../rag/embeddings.py)
- [rag/backends.py](../../rag/backends.py)
- [rag/citations.py](../../rag/citations.py)
- [rag/llm_qa.py](../../rag/llm_qa.py)

## 关键阶段版本

- `v03`
- `v09-v10`
- `v29`
- `v49`

## 当前判断

RAG 主线已经从学习版推进到 backend hardening，是项目中相对成熟的能力线。

## 关联

- [[版本总台账]]
- [[工业Agent主链路]]
