# v29：Professional RAG v1

## 本阶段目标

按照 `docs/plans/v3_professional-agent-iteration-plan.md` 的专业 RAG 方向，把原来的关键词检索扩展为一个可 rebuild、可测试、可引用来源的本地 vector RAG 原型。

本阶段不是接入外部 embedding 服务，而是先用 deterministic local embedding 建立工程闭环：

```text
documents
-> chunks with metadata
-> local embeddings
-> vector index
-> vector search
-> source citations
-> Agent tool / CLI / tests / eval
```

## 本阶段新增文件

| 文件 | 作用 |
|---|---|
| `rag/embeddings.py` | 本地 deterministic embedding 和 cosine similarity |
| `rag/vector_index.py` | vector index 数据模型、rebuild、search、save、load |
| `cli/rag_index_demo.py` | rebuild 本地 RAG vector index，并可立即查询 |
| `versions/v29_professional-rag-v1.md` | 本阶段版本说明 |
| `docs/v29_professional-rag-v1-exercises.md` | 本阶段练习 |

## 本阶段修改文件

| 文件 | 主要变化 |
|---|---|
| `rag/__init__.py` | 导出 embedding、vector index 和 vector RAG answer 能力 |
| `rag/qa.py` | 新增 `VectorRAGAnswer` 和 `answer_question_with_vector_index()` |
| `rag/llm_qa.py` | DeepSeek-grounded RAG 改为先使用 vector retrieval 取上下文 |
| `agent/tools.py` | 新增 `search_vector_docs` Agent tool |
| `agent/core.py` | 将 `search_vector_docs` 接入 `WorkspaceAgent._call_tool()` |
| `agent/router.py` | 增加 professional/vector/semantic RAG 路由 |
| `agent/tool_schema.py` | 将 `search_vector_docs` 暴露给 LLM tool catalog |
| `agent/tool_calling.py` | 允许 tool calling 选择 `search_vector_docs` |
| `tests/test_rag.py` | 增加 vector index、tool、Agent、CLI 测试 |
| `evals/regression_cases.json` | 增加 `rag-vector-search` 回归用例 |
| `cli/README.md` | 增加 vector index rebuild 命令 |
| `rag/README.md` | 记录本地 vector index 使用方式 |
| `docs/current-learning-state.md` | 更新当前阶段和学习任务 |

## 核心实现说明

### 1. Local embedding

`LocalEmbeddingModel` 使用 hashing 方式把文本转换为固定维度向量。

这个实现的目标不是语义质量，而是工程闭环：

- 不依赖外部网络
- 测试稳定
- 接口类似真实 embedding provider
- 后续可替换成 DeepSeek / OpenAI / 本地模型 embedding

### 2. Vector index

`VectorIndex` 保存一组 `VectorRecord`。

每条 record 包含：

- chunk text
- source
- start line
- end line
- embedding
- citation metadata

这些字段支撑 source citation、debug、eval 和后续 checkpoint。

### 3. Source citation

vector search 输出使用：

```text
source:start_line-end_line
```

例如：

```text
README.md:1-20
```

这比只输出一段文本更适合专业 RAG，因为用户和测试都能确认答案来自哪里。

### 4. Agent tool

新增工具：

```text
search_vector_docs
```

触发方式包括：

- `professional rag`
- `semantic search`
- `vector rag`
- `vector search`

普通 `search_docs` 仍保留关键词检索路径，避免破坏之前阶段。

### 5. Grounded RAG

`answer_question_with_llm()` 现在先通过 vector index 检索上下文，再把带 source label 的 context 交给 DeepSeek。

这样 LLM-grounded RAG 和 vector retrieval 使用同一套 citation 结构。

### 6. Index rebuild CLI

新增命令：

```bash
python -m cli.rag_index_demo --question "agent workflow"
```

默认输出：

```text
data/rag-index.json
```

这个文件属于本地实验产物，不是必须提交的源代码。

## 运行流程

### Vector RAG tool

```text
User input
-> route_intent()
-> search_vector_docs
-> answer_question_with_vector_index()
-> build_vector_index()
-> search_vector_index()
-> VectorRAGAnswer.to_text()
```

### Index rebuild CLI

```text
CLI args
-> build_vector_index()
-> save_vector_index()
-> optional search_vector_index()
-> print citations and scores
```

## 验证命令

```bash
python -m unittest tests.test_rag -v
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.rag_index_demo --question "agent workflow"
```

## 当前限制

- 当前 embedding 是 deterministic local hashing，不是真实语义 embedding。
- 当前 vector index 是 JSON 文件，不是 FAISS / Chroma / LanceDB。
- 当前没有 reranker。
- 当前 LLM-grounded RAG 已使用 vector retrieval，但还没有接入 reranker。

## 下一步建议

下一阶段可以继续两个方向之一：

1. 把 DeepSeek-grounded RAG 切换到 vector index，并保留 source citation。
2. 按迭代计划进入项目内 Skill Registry，让 `.codex/skills/professional-code-review` 成为 Agent 可发现能力。
