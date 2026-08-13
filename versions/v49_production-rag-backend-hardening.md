# v49：Production RAG Backend Hardening

## 本阶段目标

把专业 RAG 从“单一本地向量原型”推进为“有后端描述、有增量更新路径、有 citation 校验”的可替换后端架构。

## 本阶段在工业 Agent 中的位置

工业 RAG 不能长期停留在：

- 每次都全量 rebuild
- 只有一个隐式 embedding 实现
- 只有检索结果，没有后端元数据
- grounded answer 输出来源，但不检查引用是否真的来自检索结果

它必须具备：

- embedding / index backend 抽象
- source fingerprint 与增量更新计划
- grounded answer citation validation
- CLI、tool、tests 都能看到这些后端信息

`v49` 解决的是“RAG 如何从学习版原型，升级为接近生产化的后端骨架”。

## 本阶段解决的问题

- 让 vector index 显式记录 embedding backend 和 index backend
- 让文档 fingerprint 进入 index，支持增量更新判断
- 让 `rag_index_demo` 支持 incremental update
- 让 grounded RAG answer 带 citation validation 结果
- 让 Agent tool metadata 也暴露 backend / citation validation

## 本阶段新增能力

### 1. RAG backend descriptors

新增：

- `EmbeddingBackendSpec`
- `IndexBackendSpec`

当前默认后端：

- `local_hash_embedding`
- `json_vector_index`

### 2. Incremental index update plan

新增：

- `VectorIndexUpdatePlan`
- `build_document_fingerprints()`
- `plan_vector_index_update()`
- `update_vector_index()`

现在 index 会记录：

- `document_fingerprints`
- `embedding_backend`
- `index_backend`

### 3. Citation validation

新增：

- `CitationValidationResult`
- `validate_answer_citations()`

`GroundedRAGAnswer` 现在会带：

- `sources`
- `citation_validation`

### 4. CLI / tool integration

增强：

- `cli/rag_index_demo.py`
- `agent/tools.py`

现在：

- `rag_index_demo` 支持 `--incremental`
- `search_vector_docs` metadata 会暴露 backend
- `answer_docs_with_llm` metadata 会暴露 citation validation

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `rag/backends.py` | RAG 后端描述模型 |
| `rag/citations.py` | citation 校验模型与逻辑 |
| `rag/embeddings.py` | embedding backend 描述 |
| `rag/vector_index.py` | index backend、fingerprint、增量更新 |
| `rag/qa.py` | vector answer 增加 backend 展示 |
| `rag/llm_qa.py` | grounded answer 增加 citation validation |
| `rag/__init__.py` | 导出新能力 |
| `cli/rag_index_demo.py` | 增量更新 CLI |
| `agent/tools.py` | Agent tool metadata 暴露 backend / citation validation |
| `tests/test_rag.py` | 增加后端和增量更新测试 |
| `tests/test_rag_llm.py` | 增加 citation validation 测试 |
| `rag/README.md` | 更新 RAG 当前能力说明 |
| `docs/current-learning-state.md` | 更新当前学习状态 |

## 核心实现说明

### 1. 为什么 backend descriptor 必须显式进入 index

因为后续一旦切换 embedding provider 或 index backend，系统必须能回答：

- 当前索引是用什么后端建的
- 维度是否兼容
- 哪次检索来自哪套后端

这些不能只靠人记忆或 README 说明。

### 2. 为什么先做 fingerprint 和增量更新计划

因为生产化 RAG 的关键问题不是“能不能重建”，而是“什么时候必须重建、哪些文档需要重建”。

即使当前仍是本地 JSON index，也应该先把：

- added
- changed
- removed
- unchanged

这些变化显式建模出来。

### 3. 为什么 grounded answer 还要做 citation validation

因为“列出 sources”不等于“答案真的基于这些 sources”。

先做最小 citation validation，可以帮助后续：

- faithfulness eval
- unsupported claim detection
- 审计 grounded answer 的基本可信度

## 运行示例

全量 rebuild：

```bash
python -m cli.rag_index_demo --question "agent workflow"
```

增量更新：

```bash
python -m cli.rag_index_demo --question "agent workflow" --incremental
```

## 验证命令

```bash
python -m unittest tests.test_rag tests.test_rag_llm -v
python -m unittest tests.test_agent tests.test_evals -v
python -m unittest discover -s tests -q
python -m cli.rag_index_demo --question "agent workflow" --incremental
```

## 当前边界

- embedding 仍是 deterministic local hashing，不是真实语义 embedding provider
- index backend 仍是本地 JSON 文件，不是外部 vector store
- citation validation 目前只做最小来源一致性校验，还不是完整 faithfulness checker

## 下一步建议

下一阶段建议进入 `v50`，继续做 `Multi-Agent Delegation Hardening`，把主 Agent 与 subagent 的协作协议收口到可交付层。
