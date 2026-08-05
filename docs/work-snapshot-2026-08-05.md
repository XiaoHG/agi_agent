# 工作快照：2026-08-05

此文件用于新窗口恢复 v29 项目状态。v29 已准备提交并推送。

## Git 状态

- 当前分支：`main`
- v29 提交前基线：`4853fec Add LLM planner for LangGraph`
- `.vscode/` 仍未跟踪，不需要提交。
- v29 交付内容见下方文件和功能说明。

## 当前阶段

当前阶段：v29 Professional RAG v1。

迭代依据：

- `docs/professional-agent-iteration-plan.md`

本阶段目标：

- 增加本地 deterministic embedding。
- 增加 vector index 数据模型。
- 增加 chunk metadata 和 source citation。
- 增加 RAG index rebuild CLI。
- 将 vector RAG 接入 Agent tool、tool schema、router、tests 和 eval。
- 将 DeepSeek-grounded RAG 的检索上下文切到 vector retrieval。

## v29 新增文件

- `rag/embeddings.py`
- `rag/vector_index.py`
- `cli/rag_index_demo.py`
- `versions/professional-rag-v1_v29.md`
- `docs/professional-rag-v1-exercises_v29.md`
- `docs/work-snapshot-2026-08-05.md`

## v29 修改文件

- `agent/__init__.py`
- `agent/core.py`
- `agent/router.py`
- `agent/tool_calling.py`
- `agent/tool_schema.py`
- `agent/tools.py`
- `cli/README.md`
- `docs/current-learning-state.md`
- `evals/regression_cases.json`
- `rag/README.md`
- `rag/__init__.py`
- `rag/llm_qa.py`
- `rag/qa.py`
- `tests/test_rag.py`
- `tests/test_rag_llm.py`

## 已实现的 v29 功能

### 1. 本地 embedding

`rag/embeddings.py` 新增：

- `LocalEmbeddingModel`
- `cosine_similarity()`
- `tokenize_terms()`

说明：

- 当前 embedding 是 deterministic hashing embedding。
- 目的不是追求语义质量，而是先建立专业 RAG 工程闭环。
- 已加入 stopword 过滤，避免无意义 query 误触发上下文检索。

### 2. Vector index

`rag/vector_index.py` 新增：

- `VectorRecord`
- `VectorIndex`
- `VectorSearchResult`
- `build_vector_index()`
- `search_vector_index()`
- `save_vector_index()`
- `load_vector_index()`

说明：

- index record 保存 chunk、embedding 和 citation metadata。
- citation 格式为 `source:start_line-end_line`。
- `search_vector_index()` 使用 token-overlap guard，避免 hash collision 造成无关命中。

### 3. RAG answer 层

`rag/qa.py` 新增：

- `VectorRAGAnswer`
- `answer_question_with_vector_index()`

`rag/llm_qa.py` 已调整：

- `answer_question_with_llm()` 现在先通过 vector index 检索上下文。
- 没有 vector context 时返回 insufficient，不触发真实 LLM。

### 4. Agent tool 接入

新增 Agent 工具：

- `search_vector_docs`

相关接入点：

- `agent/tools.py`
- `agent/core.py`
- `agent/router.py`
- `agent/tool_schema.py`
- `agent/tool_calling.py`
- `agent/__init__.py`

触发语义：

- `professional rag`
- `semantic search`
- `vector rag`
- `vector search`
- `search vector docs`
- `search with vector`

### 5. CLI

新增：

```bash
python -m cli.rag_index_demo --question "agent workflow"
```

默认输出：

```text
data/rag-index.json
```

注意：这是本地实验产物，不需要作为源码提交。

### 6. Tests / Eval / Docs

新增和更新：

- `tests/test_rag.py`
- `tests/test_rag_llm.py`
- `evals/regression_cases.json`
- `versions/professional-rag-v1_v29.md`
- `docs/professional-rag-v1-exercises_v29.md`
- `rag/README.md`
- `cli/README.md`
- `docs/current-learning-state.md`

## 最近验证结果

已通过：

```bash
python -m unittest tests.test_rag -v
python -m unittest tests.test_rag_llm -v
python -m unittest discover -s tests -v
python -m cli.eval_runner
```

结果：

- `tests.test_rag`：18 passed
- `tests.test_rag_llm`：4 passed
- 全量测试：140 passed
- eval：19/19 passed

## 重要修复记录

实现 vector retrieval 后，发现 hashing vector 可能因 hash collision 让无上下文 query 命中无关 chunk，从而触发真实 DeepSeek LLM。

已修复：

- `LocalEmbeddingModel` 增加 stopword 过滤。
- `search_vector_index()` 增加 token-overlap guard。
- `llm-rag-no-context` eval 现在保持 insufficient，不再触发真实网络请求。

## 新窗口恢复步骤

1. 进入项目目录：

   ```bash
   cd /Users/xiaohg/ai_agent/agi_agent
   ```

2. 读取关键文件：

   ```bash
   sed -n '1,260p' docs/current-learning-state.md
   sed -n '1,260p' docs/work-snapshot-2026-08-05.md
   sed -n '1,260p' docs/professional-agent-iteration-plan.md
   sed -n '1,260p' versions/professional-rag-v1_v29.md
   ```

3. 查看当前分支状态：

   ```bash
   git status --short
   ```

4. 如果需要继续验证：

   ```bash
   python -m unittest tests.test_rag -v
   python -m unittest tests.test_rag_llm -v
   python -m cli.eval_runner
   ```

## 下一步建议

v29 提交后，下一阶段建议进入项目内 Skill Registry，让项目内 `.codex/skills/professional-code-review` 成为 Agent 可发现能力。
