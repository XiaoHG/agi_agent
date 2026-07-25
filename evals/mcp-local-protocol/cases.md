# MCP 本地协议评估用例

本文件用于记录 MCP 本地协议骨架的可复现评估。

## Case 1：列出 MCP 工具

输入：

```bash
python -m cli.mcp_demo --list-tools
```

期望行为：

- 输出 `Available MCP tools`。
- 至少包含 `workspace_summary`。
- 至少包含 `read_project_file`。

实际输出摘要：

- 成功输出本地 MCP server 暴露的两个工具。
- 每个工具都带有简短描述。

是否通过：通过。

失败或不足分析：

- 当前工具说明很简短，还没有完整展示 input schema。

## Case 2：调用 workspace summary

输入：

```bash
python -m cli.mcp_demo --tool workspace_summary
```

期望行为：

- 输出 `[mcp:ok] workspace_summary`。
- 输出当前 workspace 名称。
- 输出顶层目录或文件列表。

实际输出摘要：

- 成功返回 workspace 概览。
- 输出包含 `Workspace: agi_agent` 和 top-level entries。

是否通过：通过。

失败或不足分析：

- 当前 summary 只是目录概览，不包含更丰富的项目元数据。

## Case 3：调用不存在的 MCP 工具

输入：

```python
output = call_mcp_tool(Path("."), "missing_tool")
```

期望行为：

- 输出包含 `[mcp:error]`。
- 输出包含 `Unknown MCP tool`。
- 系统不应该抛出未处理异常。

实际输出摘要：

- adapter 正确渲染错误响应。
- server 通过 `MCPResponse(..., is_error=True)` 返回受控错误。

是否通过：通过。

失败或不足分析：

- 当前错误类型仍是字符串，后续可以扩展为结构化错误码。

## Case 4：读取文件缺少 path

输入：

```python
output = call_mcp_tool(Path("."), "read_project_file", {"path": ""})
```

期望行为：

- 输出包含 `[mcp:error]`。
- 输出包含 `Missing required argument`。

实际输出摘要：

- server 返回缺少参数的受控错误。
- adapter 正确把错误渲染成文本输出。

是否通过：通过。

失败或不足分析：

- 当前参数校验是手写逻辑，还没有自动基于 input schema 校验。

## Case 5：路径越界

输入：

```python
client = LocalMCPClient(LocalMCPServer(root))
response = client.call_tool("read_project_file", {"path": "../outside.md"})
```

期望行为：

- `response.is_error` 为 `True`。
- `response.content` 包含 `Path escapes workspace root`。

实际输出摘要：

- server 拒绝 workspace 外部路径。
- 测试验证路径边界保护有效。

是否通过：通过。

失败或不足分析：

- 当前只验证了文件路径安全，还没有更完整的权限策略。
