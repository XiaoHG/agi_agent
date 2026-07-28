# LangGraph 条件路由与多工具编排 v13

版本：v13

日期：2026-07-28

## 本次目标

把 v12 的固定 LangGraph workflow 升级为带条件路由的多工具 graph。

v12 流程：

```text
prepare -> call_tool -> finalize
```

v13 流程：

```text
route -> conditional edge -> call_tool -> finalize
```

## 修改文件

### `integrations/langgraph_workflow.py`

行号范围：`1-166`

新增变更：

- `RAGGraphState` 新增 `route`
- `RAGGraphState` 新增 `route_reason`
- `RAGGraphState` 新增 `tool_input`
- 将 `prepare()` 替换为 `route()`
- 新增 `_next_after_route()`
- 新增 `_looks_like_search_only()`
- 新增 `_looks_like_file_read()`
- 新增 `_extract_file_path()`
- 使用 `graph.add_conditional_edges()`

当前支持三类路由：

```text
read_file -> read_workspace_file
search_docs -> search_workspace_docs
answer_docs_with_llm -> answer_workspace_docs_with_llm
```

### `cli/langgraph_demo.py`

行号范围：`1-38`

新增变更：

- 输出 `Route`
- 输出 `Route reason`
- 保留 selected tool、steps、answer

### `tests/test_langgraph_workflow.py`

行号范围：`1-65`

新增变更：

- 验证 answer docs 路由
- 验证 search docs 路由
- 验证 read file 路由
- 验证 route reason

## 新增交互流程

```text
python -m cli.langgraph_demo --question "Search docs for MCP."
  -> route node
  -> selected_tool = search_workspace_docs
  -> call_tool
  -> finalize
```

```text
python -m cli.langgraph_demo --question "Read README.md."
  -> route node
  -> selected_tool = read_workspace_file
  -> call_tool
  -> finalize
```

```text
python -m cli.langgraph_demo --question "What does MCP mean in this project?"
  -> route node
  -> selected_tool = answer_workspace_docs_with_llm
  -> call_tool
  -> finalize
```

## 验证命令

```bash
python -m unittest discover -s tests -v
python -m cli.langgraph_demo --question "Search docs for MCP."
python -m cli.langgraph_demo --question "Read README.md."
python -m cli.langgraph_demo --question "the and of"
```

## 当前限制

- 路由仍是规则判断，不是 LLM router。
- 条件分支还只在 route 后选择工具，没有复杂循环。
- 没有 checkpoint。
- 没有 streaming。
- 没有 graph-level eval cases。
- 没有把 LangGraph workflow 接回 `WorkspaceAgent`。

## 下一步建议

下一步进入：

```text
v14：LangGraph 与 WorkspaceAgent 集成
```

目标：

- 让主 Agent 可以选择 LangGraph workflow 作为执行后端。
- 保留原有 deterministic path。
- 为 LangGraph 增加 graph-level eval cases。
