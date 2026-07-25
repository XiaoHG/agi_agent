# mcp/

放 MCP 相关实验。

适合放：

- MCP Server 示例
- MCP Client 示例
- 自定义工具协议适配
- 工具 schema 设计
- 工具权限边界实验

建议将 server 和 client 分开：

```text
mcp/
  servers/
  clients/
  examples/
```

## 当前实现

当前阶段实现的是本地进程内 MCP 学习骨架，不接真实网络传输。

```text
mcp/
  schema.py              # MCPToolSpec / MCPRequest / MCPResponse
  adapter.py             # Agent-facing MCP adapter
  clients/local_client.py
  servers/local_server.py
```

当前可用工具：

- `workspace_summary`：返回工作区概览
- `read_project_file`：通过 MCP server 读取工作区内文本文件

运行：

```bash
python -m cli.mcp_demo --list-tools
python -m cli.mcp_demo --tool workspace_summary
python -m cli.mcp_demo --tool read_project_file --path README.md
python -m cli.main --input "List MCP tools." --trace
```
