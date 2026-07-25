# 本地 MCP 协议骨架 v4

版本：v4

日期：2026-07-25

## 本次目标

在本地 RAG 最小闭环之后，补齐 Week 3 的第二个核心能力：MCP 最小协议边界。

本次不直接接真实 MCP SDK，也不引入网络传输，而是先用本地进程内实现理解 MCP 的工程分层：

```text
MCP Server -> MCP Client -> Agent adapter -> Agent tool call -> CLI output
```

## 新增文件

### `mcp/__init__.py`

职责：

- 导出 MCP 学习层的主要对象
- 让 `mcp` 成为可导入的本地包

### `mcp/schema.py`

行号范围：`1-32`

职责：

- 定义 `MCPToolSpec`
- 定义 `MCPRequest`
- 定义 `MCPResponse`
- 表达 tool schema、调用请求和调用响应

### `mcp/servers/local_server.py`

行号范围：`1-71`

职责：

- 定义 `LocalMCPServer`
- 暴露 `workspace_summary`
- 暴露 `read_project_file`
- 处理未知工具和路径安全

### `mcp/clients/local_client.py`

行号范围：`1-24`

职责：

- 定义 `LocalMCPClient`
- 通过 `MCPRequest` 调用 server
- 从 client 侧封装 server 调用边界

### `mcp/adapter.py`

行号范围：`1-34`

职责：

- 将 MCP client/server 组合成当前 Agent 可调用的本地工具接口
- 提供 `list_mcp_tools`
- 提供 `call_mcp_tool`

### `cli/mcp_demo.py`

行号范围：`1-46`

职责：

- 提供独立 MCP CLI demo
- 支持列出工具
- 支持调用 `workspace_summary`
- 支持调用 `read_project_file`

### `tests/test_mcp.py`

行号范围：`1-78`

职责：

- 测试 server 工具声明
- 测试 client 调用
- 测试 adapter 输出
- 测试 Agent 路由和工具执行

## 修改文件

### `agent/tools.py`

变更行号范围：`8-107`

本次改动：

- 引入 MCP adapter
- 新增 `list_mcp_server_tools`
- 新增 `mcp_workspace_summary`

### `agent/router.py`

变更行号范围：`119-155`

本次改动：

- 新增 `_looks_like_mcp_request`
- 将一般 MCP 请求路由到 `list_mcp_tools`
- 将 workspace summary 请求路由到 `mcp_workspace_summary`
- 保持 `search docs for MCP` 优先走 RAG 检索

### `agent/core.py`

变更行号范围：`10-152`

本次改动：

- 导入 MCP 工具适配函数
- 在 `_call_tool()` 中接入 MCP 工具分支

### `agent/__init__.py`

变更行号范围：`6-32`

本次改动：

- 导出 MCP Agent 工具函数

### `pyproject.toml`

本次改动：

- 将 `mcp`、`mcp.clients`、`mcp.servers` 加入包列表

### `README.md`

本次改动：

- 新增 MCP demo 命令
- 更新当前阶段说明

### `docs/current-learning-state.md`

本次改动：

- 将当前状态更新为 MCP 最小骨架
- 更新恢复指令
- 更新下一步学习重点

## 新增交互流程

### 独立 MCP demo

```text
CLI input
  -> cli.mcp_demo
  -> MCP adapter
  -> LocalMCPClient
  -> LocalMCPServer
  -> MCPResponse
  -> CLI output
```

### Agent 调用 MCP

```text
User input
  -> route_intent()
  -> list_mcp_tools / mcp_workspace_summary
  -> WorkspaceAgent._call_tool()
  -> MCP adapter
  -> LocalMCPClient
  -> LocalMCPServer
  -> final answer
```

## 验证命令

```bash
python -m unittest discover -s tests -v
python -m cli.mcp_demo --list-tools
python -m cli.mcp_demo --tool workspace_summary
python -m cli.main --input "List MCP tools." --trace
python -m cli.main --input "Search docs for MCP." --trace
```

验证结果：

- 29 个测试全部通过。
- MCP demo 可以列出工具。
- MCP demo 可以调用 `workspace_summary`。
- Agent 可以路由到 MCP 工具。
- `Search docs for MCP.` 仍然正确走 RAG 检索，没有被 MCP 路由抢走。

## 当前限制

- 当前 MCP 是本地模拟，不是完整 MCP SDK 接入。
- 当前没有真实 transport。
- 当前只暴露两个简单工具。
- 当前还没有 MCP eval case。

## 下一步建议

先完成 MCP 练习和 eval，再判断是否进入 Skills 与 Subagent 阶段。
