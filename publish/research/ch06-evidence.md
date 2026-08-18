# 第 6 章证据笔记

## 可引用事实

- `v04` 的目标是先建立本地 MCP 最小协议骨架，而不是直接接完整外部 SDK。
- 项目已经具备 `mcp/schema.py`、`mcp/adapter.py`、`mcp/clients/local_client.py` 和 `mcp/servers/local_server.py` 等分层。
- `agent/tools.py` 已接入 MCP 相关工具分支。
- `agent/router.py` 和 `agent/core.py` 已能把 MCP 请求纳入统一执行面。
- `tests/test_mcp.py` 为 MCP 工具、adapter 和 Agent 路由提供了回归覆盖。

## 证据来源

- `versions/v04_mcp-local-protocol.md`
- `mcp/schema.py`
- `mcp/adapter.py`
- `mcp/clients/local_client.py`
- `mcp/servers/local_server.py`
- `mcp/policy.py`
- `agent/tools.py`
- `agent/router.py`
- `agent/core.py`
- `tests/test_mcp.py`

## 写作提醒

- 先讲“工具边界为什么要协议化”，再讲 MCP 结构。
- 避免把本章写成单纯 API 介绍。
- 重点是职责拆分、治理边界和主链路接入方式。
