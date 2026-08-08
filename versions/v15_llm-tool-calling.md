# LLM Tool Calling 与 Tool Schema v15

版本：v15  
日期：2026-07-28

## 本次目标

把“模型参与工具选择”接入 `WorkspaceAgent` 主链路，但仍保持工程上的确定性边界：

- 模型负责输出结构化选择结果
- 代码负责校验、归一化、执行、trace 和回归

这不是完整的 OpenAI 原生 function calling，而是一个更容易学习和调试的本地 tool calling 分层实现。

## 本次新增能力

1. 新增统一 tool schema 目录。
2. 新增 tool calling prompt。
3. 新增 LLM-assisted tool selection 模块。
4. `WorkspaceAgent` 新增 `tool_call` 路径。
5. 主 Agent trace 新增 tool call 记录。
6. 回归 eval 新增 `expected_selected_tool`。
7. 新增专用 CLI demo。

## 代码改动说明

### `agent/tool_schema.py`

新增工具目录与参数描述：

- `ToolArgumentSpec`
- `ToolSpec`
- `build_workspace_tool_specs()`

它负责把工作区能力整理成模型可读的 schema 文本，覆盖：

- `read_file`
- `list_dir`
- `count_lines`
- `search_docs`
- `answer_docs_with_llm`
- `list_mcp_tools`
- `mcp_workspace_summary`
- `list_skills`
- `plan_skill`
- `list_subagents`
- `plan_subagents`

### `prompts/v15_tool-calling.md`

新增工具选择 prompt，要求模型：

- 只输出 JSON
- 返回 `action / tool_name / tool_input / reason`
- 尽量选择最小必要动作

### `agent/tool_calling.py`

新增结构化工具选择管线：

- `ToolCallSelection`
- `build_tool_calling_messages()`
- `select_tool_call()`
- `parse_tool_call_selection()`
- `normalize_tool_call_selection()`

其中 `normalize_tool_call_selection()` 负责处理模型偶尔输出空 `tool_input` 的情况，避免把可执行任务变成路径错误。

### `agent/core.py`

`WorkspaceAgent` 新增：

- `tool_call` 数据记录
- `tool_calling_prompt`
- `tool_specs`
- `_select_tool_call()`
- `_describe_tool_call()`

`run()` 新增 `tool_call` 分支，支持：

- 模型选工具
- 模型直接回答
- 模型请求补充信息

`format_trace()` 和 `to_trace_dict()` 也新增了 tool call 记录。

### `agent/router.py`

新增了显式 `tool_call` 路由入口，用于用户明确要求“让模型选工具”的场景。

### `agent/prompts.py`

新增 prompt loader：

- `load_tool_calling_prompt()`

### `agent/__init__.py`

导出新模块，方便测试、CLI 和后续扩展复用。

### `cli/tool_calling_demo.py`

新增 CLI demo，用于直接观察：

- 路由结果
- 模型选择的工具
- 执行结果
- trace

### `tests/test_tool_calling.py`

新增单测覆盖：

- JSON 解析
- schema 驱动的 tool selection
- 主 Agent 的 tool calling 执行闭环
- direct answer 分支

### `tests/test_evals.py`

新增 eval 侧测试：

- `expected_selected_tool`
- fake LLM client 注入

### `evals/runner.py`

新增回归判断字段：

- `expected_selected_tool`
- `selected_tool_name`

这让 eval 能区分：

- 路由是否正确
- 模型是否选对工具
- 工具执行后答案是否正确

### `README.md`

新增 tool calling 运行入口。

### `agent/README.md`

补充 `tool_calling.py` 和 `tool_schema.py`。

### `cli/README.md`

补充 `cli/tool_calling_demo.py`。

### `evals/README.md`

补充 tool_call 分支的评估维度说明。

### `docs/current-learning-state.md`

更新当前阶段、已完成、未完成、恢复指令和下一步建议。

## 新增文件与行数

| 文件 | 行数 |
| --- | ---: |
| `agent/tool_schema.py` | 97 |
| `agent/tool_calling.py` | 183 |
| `prompts/v15_tool-calling.md` | 31 |
| `cli/tool_calling_demo.py` | 35 |
| `tests/test_tool_calling.py` | 80 |
| `versions/llm-tool-calling_v15.md` | 213 |

## 本次修改文件与行数

| 文件 | 行数 |
| --- | ---: |
| `agent/core.py` | 442 |
| `agent/router.py` | 389 |
| `agent/prompts.py` | 30 |
| `agent/__init__.py` | 57 |
| `tests/test_evals.py` | 79 |
| `evals/runner.py` | 104 |
| `README.md` | 609 |
| `agent/README.md` | 46 |
| `cli/README.md` | 32 |
| `evals/README.md` | 55 |
| `docs/current-learning-state.md` | 188 |

## 验证命令

```bash
python -m unittest discover -s tests -v
python -m cli.tool_calling_demo --input "Use tool calling to read README.md." --trace
python -m cli.eval_runner
```

## 验证结果

- 全量测试通过：80 / 80
- tool calling 单测通过
- eval 侧新增 selected tool 检查通过
- CLI demo 能正确显示 tool call / tool / final answer

## 关键学习点

1. tool calling 不能只靠提示词，必须有 schema。
2. 模型输出不能直接信任，必须校验和归一化。
3. trace 需要同时记录 route、tool_call 和 tool_result。
4. eval 不能只看结果文本，还要看模型是否选对工具。

## 下一阶段建议

下一阶段可以继续做两件事：

1. 把 `tool_call` 扩展成多步 tool loop，而不是只做单次选择。
2. 把 MCP 和 Skills 接到同一 tool schema 层，形成更完整的专业 Agent 工具层。
