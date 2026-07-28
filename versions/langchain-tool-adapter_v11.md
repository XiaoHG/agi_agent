# LangChain Tool Adapter v11

版本：v11

日期：2026-07-28

## 本次目标

进入专业 Agent 框架适配阶段。

本次目标不是重写工具实现，而是把已有本地工具包装为真实 LangChain `StructuredTool`，为后续 LangGraph workflow 做准备。

## 新增文件

### `integrations/__init__.py`

行号范围：`1-5`

职责：

- 暴露框架集成入口。
- 当前导出 `build_langchain_tools()`。

### `integrations/langchain_tools.py`

行号范围：`1-169`

职责：

- 使用真实 `langchain_core.tools.StructuredTool`
- 使用 Pydantic schema 定义工具输入
- 将 `agent/tools.py` 中的本地工具包装为 LangChain tools
- 保持 core tools 与框架 adapter 分离

当前包装的工具：

- `read_workspace_file`
- `list_workspace_directory`
- `count_workspace_file_lines`
- `search_workspace_docs`
- `answer_workspace_docs_with_llm`
- `list_workspace_mcp_tools`
- `summarize_workspace_with_mcp`
- `list_workspace_skills`
- `plan_workspace_skill`
- `list_workspace_subagents`
- `plan_workspace_subagents`

### `cli/langchain_tools_demo.py`

行号范围：`1-33`

职责：

- 提供 LangChain tool adapter demo。
- 输出当前可用 LangChain tools 的名称和描述。

运行：

```bash
python -m cli.langchain_tools_demo
```

### `tests/test_langchain_tools.py`

行号范围：`1-58`

职责：

- 验证 adapter 返回真实 `StructuredTool`
- 验证工具名称集合
- 验证 read file tool 能调用 core tool
- 验证 DeepSeek RAG tool 标记网络和 API Key 依赖
- 验证无参数工具可以被 invoke

## 修改文件

### `pyproject.toml`

新增依赖：

```text
langchain-core>=1.5.1
```

新增 package：

```text
integrations
```

## 新增交互流程

```text
python -m cli.langchain_tools_demo
  -> build_langchain_tools()
  -> wrap core tools with StructuredTool.from_function()
  -> print LangChain tool names and descriptions
```

## 设计原因

`agent/tools.py` 是 core tool implementation。

`integrations/langchain_tools.py` 是 framework adapter。

这两个层次必须分开，否则会导致：

- core tools 依赖外部框架
- 后续换框架困难
- 工具实现和框架包装混杂
- 测试边界变差

## 验证命令

```bash
python -m unittest discover -s tests -v
python -m cli.langchain_tools_demo
python -m cli.eval_runner
```

## 当前限制

- 目前只完成 LangChain Tool Adapter，还没有接 LangGraph。
- 还没有使用 LangChain ChatModel 调用 DeepSeek。
- 还没有 tool calling agent executor。
- DeepSeek RAG tool 仍然可能触发真实网络请求，因此默认测试只验证 metadata，不直接 invoke。

## 下一步建议

下一步进入：

```text
v12：LangGraph Workflow
```

目标：

- 用 LangGraph 表达 Agent workflow。
- 将 LangChain tools 放入 graph node。
- 从固定流程逐步过渡到专业状态图编排。
