# v31：MCP 工具注册与权限策略

## 本阶段目标

把本地学习版 MCP 从“只有工具名和描述”升级为“带权限分类、默认拒绝策略和结构化权限判断”的专业工具层原型。

本阶段要形成的闭环是：

```text
MCPToolSpec
-> permission_level
-> MCPPermissionPolicy
-> permission decision
-> adapter refusal / allow path
-> Agent / CLI / tests / eval / trace
```

## 本阶段新增文件

| 文件 | 作用 |
|---|---|
| `mcp/policy.py` | MCP 权限策略和权限判断逻辑 |
| `versions/mcp-tool-permission-policy_v31.md` | 本阶段版本说明 |
| `docs/mcp-tool-permission-policy-exercises_v31.md` | 本阶段练习 |

## 本阶段修改文件

| 文件 | 主要变化 |
|---|---|
| `mcp/schema.py` | 新增 permission level 常量、`MCPPermissionPolicy`、`MCPPermissionDecision`、`MCPResponse.metadata` |
| `mcp/servers/local_server.py` | MCP tool spec 增加权限分类，新增 `write_project_file` |
| `mcp/clients/local_client.py` | 增加 `get_tool_spec()` |
| `mcp/adapter.py` | 新增 `call_mcp_tool_response()`，接入默认策略和拒绝路径 |
| `mcp/__init__.py` | 导出 permission policy 相关类型和函数 |
| `agent/tools.py` | MCP 工具 wrapper 接入结构化权限 metadata，新增 `mcp_write_project_file` |
| `agent/core.py` | `WorkspaceAgent._call_tool()` 支持 `mcp_write_project_file` |
| `agent/router.py` | MCP 请求区分 list / summary / read / write |
| `agent/tool_schema.py` | 将 `mcp_write_project_file` 暴露给 LLM tool catalog |
| `agent/tool_calling.py` | `mcp_write_project_file` 进入 task-input tools |
| `cli/mcp_demo.py` | 新增 `--content` 和 `--allow-write` |
| `tests/test_mcp.py` | 增加 permission policy、拒绝路径、CLI 写入测试 |
| `tests/test_tool_calling.py` | 增加 MCP write tool schema 测试 |
| `evals/regression_cases.json` | 增加 `mcp-write-denied` 回归用例 |
| `cli/README.md` | 补充 MCP 权限 demo 命令 |
| `mcp/README.md` | 补充 MCP 权限分类和默认策略 |
| `docs/current-learning-state.md` | 更新当前阶段和下一步建议 |

## 核心实现说明

### 1. MCPToolSpec 权限分类

`MCPToolSpec` 现在新增：

- `permission_level`

当前支持：

- `read_only`
- `write`
- `network`
- `destructive`

本阶段实际使用了：

- `workspace_summary` -> `read_only`
- `read_project_file` -> `read_only`
- `write_project_file` -> `write`

### 2. 默认策略

`build_default_mcp_policy()` 当前返回：

```text
allow_read_only=True
allow_write=False
allow_network=False
allow_destructive=False
```

这意味着 MCP 默认是“只读优先”，写入型工具即使已注册，也不会默认执行。

### 3. 权限判断与拒绝路径

`call_mcp_tool_response()` 会先：

```text
tool_name
-> tool spec
-> evaluate_mcp_tool_permission()
-> allow / deny
```

拒绝时会返回结构化 metadata：

- `permission_decision`
- `permission_policy`

并给出用户可读 refusal path：

```text
Permission denied for MCP tool: write_project_file
Permission level: write
Reason: ...
Next safe action: ...
```

### 4. 真实 allow path

为了证明策略不是静态标签，本阶段新增了：

```text
write_project_file
```

行为：

- 默认策略下拒绝
- 显式 `allow_write=True` 时允许
- 真正写入 workspace 内文件

### 5. Agent / CLI 接入

当前已接入：

- `list_mcp_tools`
- `mcp_workspace_summary`
- `mcp_read_project_file`
- `mcp_write_project_file`

CLI demo：

```bash
python -m cli.mcp_demo --list-tools
python -m cli.mcp_demo --tool write_project_file --path notes.txt --content "hello mcp"
python -m cli.mcp_demo --tool write_project_file --path notes.txt --content "hello mcp" --allow-write
```

### 6. Trace / eval

MCP tool wrapper 现在会把 permission decision 放进 `ToolResult.metadata`。

这意味着：

- `WorkspaceAgent.to_trace_dict()` 可见权限判断
- tests 可以断言 `allowed=True/False`
- eval 可以覆盖默认拒绝写入的行为

## 当前可见行为

### 列出 MCP 工具

```bash
python -m cli.mcp_demo --list-tools
```

输出现在会带权限标签，例如：

```text
- workspace_summary [read_only]
- read_project_file [read_only]
- write_project_file [write]
```

### 默认拒绝写入

```bash
python -m cli.mcp_demo --tool write_project_file --path notes.txt --content "hello mcp"
```

输出会明确给出 refusal path。

### 显式允许写入

```bash
python -m cli.mcp_demo --tool write_project_file --path notes.txt --content "hello mcp" --allow-write
```

这条路径会真正写入 workspace 内文件。

## 设计取舍

### 为什么先做本地策略，而不接真实远程 MCP

因为当前阶段的重点是：

- 明确工具权限分类
- 明确默认策略
- 明确拒绝路径
- 明确 trace / eval 证据

这些都不依赖远程传输。先在本地 in-process MCP 边界里把策略闭环做稳，更适合当前学习阶段。

### 为什么要新增一个 write 工具

因为如果所有 MCP 工具都是 read-only，就无法证明策略真的在影响执行行为。

新增 `write_project_file` 后，系统能展示：

- 已注册工具
- 默认拒绝
- 显式允许

这才构成真正的权限策略验证链路。

## 验证命令

已验证：

```bash
python -m unittest tests.test_mcp tests.test_tool_calling -v
python -m cli.mcp_demo --list-tools
python -m cli.mcp_demo --tool write_project_file --path notes.txt --content "hello mcp"
python -m unittest discover -s tests -q
python -m cli.eval_runner
```

## 当前限制

- MCP 仍是本地 in-process 学习版，不是真实跨进程 / 远程传输。
- permission policy 目前是静态布尔配置，不是基于用户/会话/审批上下文的动态策略。
- `mcp_write_project_file` 目前只演示受控写入，不涉及 destructive 工具。
- LangGraph 还没有把 MCP 工具作为独立 graph node 接入。

## 下一步建议

下一阶段建议进入：

- 默认 LangGraph 主执行器

原因：

- 现在 RAG、Skills、MCP 都已经具备更完整的结构化边界。
- 继续推进的关键不是再补单点 helper，而是把这些能力统一纳入主执行 runtime。
