# WorkspaceAgent 接入 DeepSeek RAG v10

版本：v10

日期：2026-07-28

## 本次目标

将 v9 中独立运行的 DeepSeek-grounded RAG 接入 `WorkspaceAgent` 主工具链。

本次完成后，用户不仅可以通过独立 CLI 运行：

```bash
python -m cli.rag_llm_demo --question "What does MCP mean in this project?"
```

也可以通过主 Agent 入口运行：

```bash
python -m cli.main --input "Answer with local docs and DeepSeek RAG: What does MCP mean in this project?" --trace
```

## 修改文件

### `agent/tools.py`

核心行号：`101-108`

新增变更：

- 新增 `answer_docs_with_llm()`
- 调用 `rag.answer_question_with_llm()`
- 将 `LLMError` 转换为 `ToolError`
- 返回标准 `ToolResult("answer_docs_with_llm", output)`

设计原因：

- `search_docs` 继续保留为 deterministic retrieval 工具。
- `answer_docs_with_llm` 负责真实 LLM-grounded RAG。
- 两者职责分离，便于调试、测试和后续 eval。

### `agent/router.py`

核心行号：`119-203`

新增变更：

- 新增 `_looks_like_llm_rag_request()`
- 在普通 knowledge search 之前识别 LLM-grounded RAG 请求
- 将匹配请求路由到 `answer_docs_with_llm`

当前触发关键词包括：

- `answer with local docs`
- `answer with local context`
- `deepseek rag`
- `grounded answer`
- `grounded rag`
- `llm rag`
- `rag answer`

### `agent/core.py`

核心行号：`14`、`155-156`

新增变更：

- `_call_tool()` 新增 `answer_docs_with_llm` 分支
- 主 Agent 可以通过标准工具分发调用 DeepSeek RAG

### `agent/__init__.py`

核心行号：`10`、`36`

新增变更：

- 导出 `answer_docs_with_llm`

### `tests/test_rag.py`

核心行号：`57-91`

新增变更：

- 新增 LLM-grounded RAG 路由测试
- 新增 `answer_docs_with_llm` 无上下文边界测试
- 新增主 Agent 调用 `answer_docs_with_llm` 的无上下文测试
- 修正原无结果 RAG 测试，改为临时目录隔离，避免复盘文档污染检索结果

### `evals/regression_cases.json`

核心行号：`73-78`

新增变更：

- 新增 `llm-rag-no-context`
- 验证主 Agent 可以路由到 `answer_docs_with_llm`
- 使用无本地上下文问题，避免默认 eval 触发真实网络请求

### `evals/README.md`

新增变更：

- 说明 LLM-grounded RAG regression case 的边界
- 说明默认 eval 不触发真实 DeepSeek 网络请求

### `README.md`

新增变更：

- 新增通过主 Agent 调用 DeepSeek RAG 的命令

### `docs/current-learning-state.md`

新增变更：

- 当前状态更新为 DeepSeek-grounded RAG 已接入 `WorkspaceAgent`
- 下一步建议更新为 LangChain tool schema 和 LangGraph workflow

## 新增交互流程

```text
python -m cli.main --input "Answer with local docs and DeepSeek RAG: ..."
  -> WorkspaceAgent.run()
  -> route_intent()
  -> _looks_like_llm_rag_request()
  -> ToolRoute(tool_name="answer_docs_with_llm")
  -> WorkspaceAgent._call_tool()
  -> agent.tools.answer_docs_with_llm()
  -> rag.answer_question_with_llm()
  -> local retrieval
  -> DeepSeekLLMClient.chat()
  -> ToolResult("answer_docs_with_llm", grounded_answer)
  -> trace + final answer
```

## 验证命令

```bash
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.main --input "Answer with local docs and DeepSeek RAG: What does MCP mean in this project?" --trace
```

## 当前限制

- 路由仍是规则识别，不是 LLM router。
- 默认 regression eval 不调用真实 DeepSeek，只验证工具接线边界。
- RAG 检索仍是关键词检索，不是向量检索。
- citation 还没有结构化校验。
- 还没有 LangChain tool schema。
- 还没有 LangGraph workflow。

## 下一步建议

下一步进入：

```text
v11：LangChain Tool Adapter
```

目标：

- 将本地工具包装为专业 tool schema。
- 为 LangGraph workflow 做准备。
- 保持 core tools 与框架适配层分离。
