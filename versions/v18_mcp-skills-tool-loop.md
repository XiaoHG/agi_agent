# MCP / Skills Tool Loop v18

版本：v18  
日期：2026-07-30

## 本次目标

把 MCP 和 Skills 从“可被规则路由调用的普通工具”，推进为“可被 LLM tool calling / tool loop 稳定选择的一等能力”。

v17 的重点是：

```text
tool observations -> LLM final synthesis
```

v18 的重点是：

```text
MCP / Skills tools -> tool schema -> LLM tool selection -> tool loop observations -> LLM final synthesis
```

核心边界：

- MCP / Skills 仍然通过统一 `ToolResult` 返回。
- LLM 负责选择工具和参数。
- 代码负责参数归一化、工具分发、安全执行和测试兜底。
- 本阶段不引入外部 MCP server，也不引入真实技能执行引擎，只先打通工程边界。

## 本次新增能力

1. 新增 agent 侧 MCP 文件读取工具：`mcp_read_project_file`。
2. `WorkspaceAgent._call_tool()` 支持调度 `mcp_read_project_file`。
3. `tool_schema` 对 LLM 暴露 `mcp_read_project_file`。
4. `tool_calling` 增加工具输入分类：
   - no-argument tools
   - path-input tools
   - task-input tools
5. 无参数工具会清空多余 `tool_input`，避免模型把自然语言指令误传给工具。
6. 文件型工具会从原始用户请求中提取 workspace-relative file path。
7. 新增 MCP 文件读取的 agent 测试。
8. 新增 MCP / Skills 一起进入 tool loop 的回归测试。

## 交互流程

### MCP 文件读取流程

示例输入：

```text
Use tool calling to read README.md through MCP.
```

执行链路：

```text
route_intent
-> action=tool_call
-> LLM selects mcp_read_project_file
-> normalize_tool_call_selection extracts README.md
-> WorkspaceAgent._call_tool()
-> mcp_read_project_file()
-> call_mcp_tool(read_project_file, {"path": "README.md"})
-> ToolResult
-> final answer
```

### MCP / Skills tool loop 流程

示例输入：

```text
Use tool loop to inspect MCP workspace summary, list skills, and then answer.
```

执行链路：

```text
route_intent
-> action=tool_loop
-> step 1: LLM selects mcp_workspace_summary
-> observation records MCP workspace summary
-> step 2: LLM selects list_skills
-> observation records available skills
-> step 3: LLM selects answer_directly
-> final synthesis uses MCP and Skills observations
```

## 代码改动说明

### `agent/tools.py`

新增：

```python
mcp_read_project_file(root: Path, raw_path: str) -> ToolResult
```

职责：

- 作为 agent 侧工具包装函数。
- 调用本地 MCP adapter 的 `read_project_file`。
- 把 MCP response 包装成统一 `ToolResult`。

新增代码位置：

- `mcp_read_project_file()`：新增函数，位于 `mcp_workspace_summary()` 之后。

### `agent/core.py`

新增：

- 导入 `mcp_read_project_file`
- `_call_tool()` 中新增 `mcp_read_project_file` 分发分支

职责：

- 让 `WorkspaceAgent` 可以执行 LLM 选择出来的 MCP 文件读取工具。

### `agent/tool_schema.py`

新增 tool spec：

```text
mcp_read_project_file
```

参数：

```text
path: Workspace-relative file path.
```

职责：

- 让 LLM 在工具目录中看到 MCP 文件读取能力。
- 明确它是 path-input tool，不是无参数 MCP 工具。

### `agent/tool_calling.py`

新增工具分类：

```python
_NO_ARGUMENT_TOOLS
_PATH_INPUT_TOOLS
_TASK_INPUT_TOOLS
```

新增行为：

- `list_mcp_tools`
- `mcp_workspace_summary`
- `list_skills`
- `list_subagents`

这些工具不需要输入参数。即使 LLM 返回了自然语言 `tool_input`，代码也会归一化为 `None`。

新增行为：

- `read_file`
- `count_lines`
- `mcp_read_project_file`

这些工具属于文件路径型工具。如果 LLM 返回的 `tool_input` 像一句指令，代码会从原始用户输入中提取文件路径。

### `tests/test_tool_calling.py`

新增测试：

- `test_tool_schema_exposes_mcp_file_reader`
- `test_select_tool_call_normalizes_mcp_file_path`
- `test_select_tool_call_removes_input_for_no_argument_mcp_tool`

验证点：

- MCP 文件读取工具已经进入 schema。
- MCP 文件读取能正确提取 `README.md`。
- 无参数 MCP 工具不会保留多余自然语言输入。

### `tests/test_mcp.py`

新增：

- `FakeMCPReadClient`
- `test_agent_reads_project_file_through_mcp_tool`

验证点：

- agent 能通过 tool calling 选择 MCP 文件读取工具。
- MCP adapter 返回 `[mcp:ok]`。
- MCP server 实际读取 `README.md`。

### `tests/test_tool_loop.py`

新增：

- `test_tool_loop_can_use_mcp_and_skills_as_capabilities`

验证点：

- tool loop 可以调用 MCP 工具。
- tool loop 可以调用 Skills 工具。
- observations 可以进入 final synthesis。

### `agent/README.md`

新增当前工具族说明：

- File tools
- RAG tools
- MCP tools
- Skills tools
- Subagent tools

### `docs/current-learning-state.md`

更新：

- 当前阶段切换到 v18。
- 当前缺口重新评估。
- 新增恢复文件。
- 新增学习重点。

## 新增文件与行数

本阶段新增文件：

| 文件 | 行数 |
| --- | ---: |
| `versions/mcp-skills-tool-loop_v18.md` | 294 |
| `docs/mcp-skills-tool-loop-exercises.md` | 114 |

## 本次修改文件与行数

本阶段修改文件：

| 文件 | 行数 |
| --- | ---: |
| `agent/tools.py` | 154 |
| `agent/core.py` | 633 |
| `agent/tool_schema.py` | 101 |
| `agent/tool_calling.py` | 216 |
| `tests/test_tool_calling.py` | 115 |
| `tests/test_mcp.py` | 123 |
| `tests/test_tool_loop.py` | 120 |
| `agent/README.md` | 58 |
| `docs/current-learning-state.md` | 227 |

## 验证命令

定向测试：

```bash
python -m unittest tests.test_mcp tests.test_tool_calling tests.test_tool_loop -v
```

全量测试：

```bash
python -m unittest discover -s tests -v
```

回归评估：

```bash
python -m cli.eval_runner
```

真实 LLM demo：

```bash
python -m cli.tool_loop_demo --input "Use tool loop to inspect MCP workspace summary, list skills, and then answer." --trace
```

## 本阶段学习重点

1. Tool schema 不是文档装饰，而是 LLM 选择工具的输入边界。
2. MCP 进入 agent 后，不应该绕过统一工具调度层。
3. 无参数工具和有参数工具必须区别处理。
4. LLM 生成的 `tool_input` 不能直接信任，必须由代码做归一化。
5. Skills 当前还不是外部执行系统，但已经成为 LLM 可选择、可追踪、可综合的能力。
6. 专业 Agent 的工具层要同时满足：
   - 可被模型理解
   - 可被代码安全执行
   - 可被测试稳定验证
   - 可被 trace 复盘

## 下一阶段建议

下一阶段可以进入 “标准化 Skills 执行系统”：

- 把 skill 从静态描述升级为可执行 plan。
- 统一 skill input / output schema。
- 记录 skill execution trace。
- 让 tool loop 可以调用具体 skill action，而不只是列出或选择 skill。
