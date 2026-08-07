# v04 练习：本地 MCP 协议

对应版本：v04  
主题：Local MCP Protocol  
用途：理解工具协议边界、权限和安全约束

## 练习

1. 为什么 MCP 工具不能直接暴露成普通函数调用？
2. `LocalMCPServer` 为什么需要路径逃逸检查？
3. `MCPPermissionPolicy` 解决了什么问题？
4. `tests/test_mcp.py` 为什么是这个阶段的核心测试？

## 答案

1. 因为协议边界要统一输入输出、权限和错误模型。
2. 防止工具读取或写入工作区外的文件。
3. 它让 read/write 等工具能力有明确的权限边界。
4. 它验证 server/client/adapter/policy 的完整链路。

## 验证

```bash
python -m unittest tests.test_mcp -v
python -m cli.mcp_demo --list-tools
```
