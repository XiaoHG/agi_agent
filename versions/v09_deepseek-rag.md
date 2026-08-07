# DeepSeek 驱动的专业 RAG v9

版本：v9

日期：2026-07-27

## 本次目标

进入 DeepSeek 驱动的专业 RAG 阶段。

本次把原有 deterministic RAG 从“只返回检索 chunk”推进到“检索本地上下文后交给真实 DeepSeek LLM 生成 grounded answer”。

核心链路：

```text
用户问题 -> 本地文档加载 -> chunk -> retrieve -> 构造 grounded prompt -> DeepSeek V4 Pro -> 引用来源回答
```

## 新增文件

### `rag/llm_qa.py`

行号范围：`1-91`

职责：

- 定义 `GroundedRAGAnswer`
- 定义 `answer_question_with_llm()`
- 定义 `build_grounded_rag_prompt()`
- 复用现有 `answer_question()` 做本地检索
- 将检索结果转换为带 source label 的 LLM prompt
- 调用 `DeepSeekLLMClient` 生成真实 grounded answer

设计重点：

- 不替换原有 deterministic RAG，避免破坏已有测试和 eval。
- LLM 回答必须基于本地 context。
- 无检索结果时不调用 LLM，直接返回 context insufficient。
- 保留 sources，后续可以用于引用、报告和 eval。

### `cli/rag_llm_demo.py`

行号范围：`1-39`

职责：

- 提供 DeepSeek RAG 命令行入口。
- 支持 `--root` 指定工作区。
- 支持 `--question` 输入问题。
- 支持 `--top-k` 控制送入 LLM 的 chunk 数量。
- LLM 请求失败时返回非 0 exit code。

运行示例：

```bash
python -m cli.rag_llm_demo --question "What does MCP mean in this project?"
```

### `tests/test_rag_llm.py`

行号范围：`1-66`

职责：

- 测试 grounded RAG prompt 是否包含问题、来源和上下文。
- 测试无检索结果时不调用真实 LLM。
- 测试 grounded answer 能保留 source labels。

说明：

默认测试不调用真实网络。真实 DeepSeek RAG 行为通过 `cli/rag_llm_demo.py` 验证。

## 修改文件

### `rag/__init__.py`

新增导出：

- `GroundedRAGAnswer`
- `answer_question_with_llm`
- `build_grounded_rag_prompt`

### `README.md`

新增 DeepSeek RAG demo 命令：

```bash
python -m cli.rag_llm_demo --question "What does MCP mean in this project?"
```

### `docs/current-learning-state.md`

新增变更：

- 当前阶段更新为 DeepSeek 驱动的专业 RAG。
- 恢复指令新增 v9 文件。
- 下一步建议更新为把 LLM-grounded RAG 接回主 Agent。

## 新增交互流程

```text
python -m cli.rag_llm_demo --question "..."
  -> answer_question_with_llm()
  -> answer_question()
  -> load_text_documents()
  -> chunk_documents()
  -> retrieve()
  -> build_grounded_rag_prompt()
  -> DeepSeekLLMClient.chat()
  -> GroundedRAGAnswer.to_text()
```

## 当前限制

- LLM-grounded RAG 还没有接入 `WorkspaceAgent` 的 `search_docs` 工具。
- 检索仍是关键词检索，不是 embedding/vector search。
- prompt 上下文长度还没有 token-aware 控制。
- 还没有 answer faithfulness eval。
- 还没有 stream 输出。
- 还没有把 source citation 结构化到 JSON。

## 下一步建议

下一步建议进入：

```text
v10：将 DeepSeek RAG 接入 WorkspaceAgent 工具链
```

目标：

- 新增或升级 Agent tool，使用户可以通过主 Agent 直接调用 LLM-grounded RAG。
- 在 trace 中记录 retrieval sources 和 LLM answer。
- 增加针对 RAG + LLM 的 eval case。
