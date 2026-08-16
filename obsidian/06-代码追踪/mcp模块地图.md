# mcp模块地图

## 模块职责

`mcp/` 负责本地学习版 MCP protocol、schema、policy、adapter 和 client/server 骨架。

## 主要文件

- [mcp/adapter.py](../../mcp/adapter.py)
- [mcp/policy.py](../../mcp/policy.py)
- [mcp/schema.py](../../mcp/schema.py)
- [mcp/clients/local_client.py](../../mcp/clients/local_client.py)
- [mcp/servers/local_server.py](../../mcp/servers/local_server.py)

## 关键阶段版本

- `v04`
- `v31`
- `v40`
- `v47`

## 当前判断

MCP 已经有执行边界和治理基础，但还偏本地治理，不是外部化 registry / client ecosystem。

## 关联

- [[当前治理与审批缺口]]
- [[版本总台账]]
