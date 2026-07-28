# LangGraph Workflow v12

版本：v12

日期：2026-07-28

## 本次目标

进入真实 LangGraph workflow 阶段。

本次使用官方 `langgraph` 的 `StateGraph`，把 v11 的 LangChain Tool Adapter 放入最小 graph workflow 中。

## 新增文件

### `integrations/langgraph_workflow.py`

行号范围：`1-91`

职责：

- 定义 `RAGGraphState`
- 定义 `build_rag_graph()`
- 定义 `run_rag_graph()`
- 使用真实 `StateGraph`
- 使用 `START` / `END`
- 将 `answer_workspace_docs_with_llm` LangChain tool 放入 graph node

当前 graph 节点：

```text
prepare -> call_tool -> finalize
```

### `cli/langgraph_demo.py`

行号范围：`1-36`

职责：

- 提供 LangGraph workflow demo。
- 接收 `--question`。
- 输出 selected tool、steps 和 final answer。

运行：

```bash
python -m cli.langgraph_demo --question "What does MCP mean in this project?"
```

### `tests/test_langgraph_workflow.py`

行号范围：`1-41`

职责：

- 验证 graph 可以被 build 并 invoke。
- 验证 no-context 输入不会触发真实 DeepSeek。
- 验证 graph state 包含 selected tool、steps、answer。

## 修改文件

### `pyproject.toml`

新增依赖：

```text
langgraph>=1.2.9
```

## 新增交互流程

```text
python -m cli.langgraph_demo --question "..."
  -> run_rag_graph()
  -> build_rag_graph()
  -> StateGraph(RAGGraphState)
  -> prepare node
  -> call_tool node
  -> finalize node
  -> compiled_graph.invoke()
  -> print graph result
```

## 当前限制

- 当前 graph 是固定流程，没有条件分支。
- 当前 selected tool 固定为 `answer_workspace_docs_with_llm`。
- 还没有 LLM router。
- 还没有 checkpoint / persistence。
- 还没有 streaming graph output。
- 还没有多工具自动选择。

## 下一步建议

下一步进入：

```text
v13：LangGraph 条件路由与多工具编排
```

目标：

- 根据问题类型选择不同工具。
- 将 search docs、read file、DeepSeek RAG 放入同一个 graph。
- 引入条件边，开始学习 LangGraph 的核心价值。
