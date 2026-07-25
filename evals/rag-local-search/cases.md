# RAG 本地检索评估用例

本文件用于记录本地 RAG 最小闭环的可复现评估。

## Case 1：查询 workflow

输入：

```bash
python -m cli.rag_demo --question "What does workflow mean in this project?"
```

期望行为：

- 返回至少 1 个相关来源。
- 来源中应优先包含 `docs/state-workflow-flow.md` 或 `versions/state-workflow_v2.md`。
- 输出中包含 `Source`、`Score`、`Matched terms` 和 `Context`。

实际输出摘要：

- 返回了 3 个相关 chunk。
- 命中了 workflow 相关文档。
- 输出包含来源、分数、匹配词和上下文预览。

是否通过：通过。

不足分析：

- 当前关键词检索可能把 README 中的普通 demo 说明排在更前面。
- 后续需要加入更好的 query 清洗、权重设计或 rerank。

## Case 2：查询 RAG

输入：

```bash
python -m cli.main --input "Search docs for RAG." --trace
```

期望行为：

- Agent 路由到 `search_docs`。
- 不应被 workflow 路由抢走。
- 输出应包含 RAG 相关上下文。

实际输出摘要：

- Agent 进入 `use_tool / search_docs`。
- 工具返回本地文档检索结果。
- trace 中能看到 `Run tool: search_docs completed`。

是否通过：通过。

不足分析：

- 当前最终回答只是检索结果展示，还不是基于上下文生成的自然语言总结。

## Case 3：查询不存在的关键词

输入：

```python
answer = answer_question(Path("."), "zzzz-not-existing-keyword")
```

期望行为：

- `answer.results` 为空列表。
- `answer.to_text()` 包含 `no local context`。
- 系统不应该报错，也不应该编造答案。

实际输出摘要：

- 返回空结果。
- 文本提示没有找到本地上下文。

是否通过：通过。

不足分析：

- 后续可以把空结果作为 Agent 层的特殊失败类型，提示用户换关键词或补充文档。
