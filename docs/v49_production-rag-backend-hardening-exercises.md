# Production RAG Backend Hardening v49 练习

对应版本：v49  
主题：Production RAG Backend Hardening  
用途：理解为什么专业 RAG 不能只有检索结果，还必须有后端描述、增量更新和 citation 校验

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v49` 不能继续停留在单一本地 vector index？
2. `embedding_backend` 和 `index_backend` 进入 index 后解决了什么问题？
3. 为什么需要 `document_fingerprints`？
4. 为什么 grounded answer 还要做 citation validation？
5. 这一步为什么属于“后端硬化”，而不是普通功能补充？

## 练习 2：读 RAG 后端链路

阅读：

- `rag/backends.py`
- `rag/citations.py`
- `rag/vector_index.py`
- `rag/llm_qa.py`
- `tests/test_rag.py`

请回答：

1. `VectorIndexUpdatePlan` 记录了哪些变化类型？
2. `plan_vector_index_update()` 如何判断 added / changed / removed / unchanged？
3. `update_vector_index()` 为什么可以只重建部分 source？
4. `validate_answer_citations()` 会拦哪类问题？
5. `agent/tools.py` 现在把哪些 RAG 后端信息暴露给了上层？

## 练习 3：动手验证

运行：

```bash
python -m unittest tests.test_rag tests.test_rag_llm -v
python -m cli.rag_index_demo --question "agent workflow" --incremental
python -m cli.main --input "Use professional RAG to search docs for workflow." --trace
```

请记录：

1. CLI 输出里是否出现 `Embedding backend`？
2. incremental 模式下是否出现 update plan？
3. `search_vector_docs` 的 metadata 中是否带 backend？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么生产化 RAG 需要把“文档是否变化”建模成正式数据？
2. 为什么 citation validation 不能只留到后续 eval 再做？
3. 如果后续要替换成真实 embedding provider 和 vector store，`v49` 最重要的基础价值是什么？

## 答案

### 练习 1：理解本阶段目标

1. 因为单一本地 vector index 只能说明“现在能搜”，不能说明“索引来自什么后端、哪些文档变化了、答案引用是否合法”。
2. 它们解决的是后端可识别、可比较、可迁移的问题。
3. 因为没有 fingerprint，就无法稳定判断哪些 source 需要增量重建。
4. 因为列出 sources 不等于答案真的引用了这些 sources，最小 citation validation 是 grounded answer 的基础可信度检查。
5. 因为 `v49` 改的是 RAG 的底层后端结构、更新策略和引用治理，而不是只补一个新命令。

### 练习 2：读 RAG 后端链路

1. `VectorIndexUpdatePlan` 记录 `added_sources`、`changed_sources`、`removed_sources` 和 `unchanged_sources`。
2. 它通过比较当前 index 中保存的 `document_fingerprints` 和最新文档 fingerprint 来判断。
3. 因为 unchanged source 的旧 records 可以保留，只需要重建新增或变化的 source。
4. 它会拦“答案引用了不在 retrieval sources 里的来源”以及“完全没有引用任何 retrieval source”的情况。
5. `agent/tools.py` 现在会把 vector backend 和 grounded answer 的 citation validation 放进 tool metadata。

### 练习 3：动手验证

1. 是，CLI 输出里应出现 `Embedding backend`。
2. 是，incremental 模式下应先打印 update plan。
3. 是，`search_vector_docs` 的 metadata 中应带 backend。

### 练习 4：工程取舍题

1. 因为生产化系统需要知道“为什么这次重建发生”“哪些 source 被影响”，这不能只靠全量重跑掩盖。
2. 因为 citation validation 越靠近回答生成链路，越容易留下可审计证据，后续 eval 才有稳定输入。
3. `v49` 最重要的基础价值，是把 RAG 的后端描述、更新边界和引用校验结构化了，后续替换真实 provider 时不用重写上层 Agent 接口。
