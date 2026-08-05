# v31 练习：MCP 工具注册与权限策略

## 练习目标

理解为什么专业 Agent 不能只暴露 MCP 工具名，还必须显式维护权限分类、默认策略和拒绝路径。

## 一、理解题

1. 为什么 v31 要新增 `permission_level`，而不是只靠工具描述文本说明风险？
2. 为什么默认策略要允许 `read_only`，但拒绝 `write`？
3. `MCPPermissionDecision` 为什么要进入 `MCPResponse.metadata`？
4. 为什么 v31 要专门新增 `write_project_file`，而不是只给已有工具打上权限标签？
5. 当前 refusal path 解决的是什么问题？它还没有解决什么问题？

## 二、源码定位题

1. `MCPPermissionPolicy` 和 `MCPPermissionDecision` 定义在哪个文件？
2. 哪个函数构建默认 MCP 策略？
3. 哪个函数真正执行权限判断？
4. 哪个函数在调用 MCP 工具前先检查权限？
5. `WorkspaceAgent` 是通过哪个工具 wrapper 调用 `write_project_file` 的？

## 三、动手验证

运行：

```bash
python -m cli.mcp_demo --list-tools
```

回答：

1. 输出中是否包含 `write_project_file [write]`？
2. 其他两个默认工具的权限标签是什么？

再运行：

```bash
python -m cli.mcp_demo --tool write_project_file --path notes.txt --content "hello mcp"
```

回答：

1. 当前状态是 `[mcp:ok]` 还是 `[mcp:error]`？
2. 输出中是否包含 `Permission denied for MCP tool`？
3. 输出中是否包含 `Next safe action`？

最后运行：

```bash
python -m cli.mcp_demo --tool write_project_file --path notes.txt --content "hello mcp" --allow-write
```

回答：

1. 这次是否成功写入？
2. 为什么这次和上一次行为不同？

## 四、测试题

运行：

```bash
python -m unittest tests.test_mcp tests.test_tool_calling -v
```

回答：

1. 哪个测试验证默认拒绝 write 工具？
2. 哪个测试验证显式允许 write 工具？
3. 哪个测试验证 Agent 默认拒绝 MCP 写入？
4. 哪个测试验证 tool schema 已暴露 `mcp_write_project_file`？

## 五、思考题

1. 如果未来有 `network` 和 `destructive` MCP 工具，当前布尔型策略是否够用？
2. permission policy 更适合继续放在 adapter 层，还是应该前移到 Agent route / graph state？
3. 如果 project skill 想调用 write-capable MCP 工具，权限判断应该发生在 skill registry、tool runner，还是 MCP adapter？
4. 为什么 v31 之后更适合进入“默认 LangGraph 主执行器”，而不是继续在 MCP 层再补更多工具？

## 六、验收标准

完成本练习后，你应该能说明：

- MCP 工具注册和权限策略是两个不同层次的问题。
- 工具“已注册”不代表“默认可执行”。
- refusal path 是专业 Agent 工具层的重要组成部分。
