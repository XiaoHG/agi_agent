# 工作快照：2026-08-05

此文件用于新窗口恢复当前项目状态。

新会话恢复命令：

```text
恢复项目
```

恢复目标：回到 v29 Professional RAG v1 已完成、已提交、已推送后的学习状态。

## Git 状态

- 当前分支：`main`
- v29 功能基线提交：`597ea59 Add professional RAG vector index`
- v29 提交前基线：`4853fec Add LLM planner for LangGraph`
- 当前 `main` 已推送到 `origin/main`。
- `.vscode/` 仍未跟踪，不需要提交。
- 除 `.vscode/` 本地编辑器配置外，源码工作区应保持干净。

## 当前阶段

当前阶段：v29 Professional RAG v1 已完成。

迭代依据：

- `docs/plans/professional-agent-iteration-plan.md`

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
- `versions/v29_professional-rag-v1.md`
- `docs/v29_professional-rag-v1-exercises.md`
- `docs/snapshots/work-snapshot-2026-08-05.md`

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
- `versions/v29_professional-rag-v1.md`
- `docs/v29_professional-rag-v1-exercises.md`
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

提交前最终验证结果：

```bash
python -m unittest discover -s tests -v
python -m cli.eval_runner
```

结果：

- 全量测试：140 passed
- eval：19/19 passed

## 重要修复记录

实现 vector retrieval 后，发现 hashing vector 可能因 hash collision 让无上下文 query 命中无关 chunk，从而触发真实 DeepSeek LLM。

已修复：

- `LocalEmbeddingModel` 增加 stopword 过滤。
- `search_vector_index()` 增加 token-overlap guard。
- `llm-rag-no-context` eval 现在保持 insufficient，不再触发真实网络请求。

## 新窗口恢复步骤

当用户输入“恢复项目”时，按下面步骤恢复上下文。

1. 进入项目目录：

   ```bash
   cd /Users/xiaohg/ai_agent/agi_agent
   ```

2. 确认 git 状态：

   ```bash
   git status --short --branch
   git log --oneline -n 3
   ```

   预期：

   ```text
   ## main...origin/main
   ?? .vscode/

   最新提交应包含当前恢复快照；`597ea59 Add professional RAG vector index` 是 v29 功能基线提交。
   ```

3. 读取关键文件：

   ```bash
   sed -n '1,260p' docs/current-learning-state.md
   sed -n '1,260p' docs/snapshots/work-snapshot-2026-08-05.md
   sed -n '1,260p' docs/plans/professional-agent-iteration-plan.md
   sed -n '1,260p' versions/v29_professional-rag-v1.md
   sed -n '1,320p' docs/v29_professional-rag-v1-exercises.md
   ```

4. 重点代码入口：

   ```bash
   sed -n '1,260p' rag/embeddings.py
   sed -n '1,320p' rag/vector_index.py
   sed -n '1,260p' rag/qa.py
   sed -n '1,220p' agent/tools.py
   sed -n '1,220p' cli/rag_index_demo.py
   ```

5. 如果需要继续验证：

   ```bash
   python -m unittest discover -s tests -v
   python -m cli.eval_runner
   ```

## 下一步建议

下一阶段建议进入项目内 Skill Registry，让项目内 `.codex/skills/professional-code-review` 成为 Agent 可发现能力。
