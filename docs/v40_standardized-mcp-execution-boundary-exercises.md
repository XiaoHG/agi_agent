# Standardized MCP Execution Boundary v40 练习

对应版本：v40  
主题：Standardized MCP Execution Boundary  
用途：理解为什么 MCP 工具层需要标准化执行边界

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v40` 不是“把 MCP 再包一层”？
2. `MCPExecutionRecord` 的职责是什么？
3. `MCPError` 为什么要单独建模？
4. 为什么 execution record 和 response metadata 要同时存在？
5. 为什么本阶段要保留旧的 `MCPResponse` 接口？

## 练习 2：读 MCP 链路

阅读：

- `mcp/schema.py`
- `mcp/adapter.py`
- `cli/mcp_demo.py`
- `tests/test_mcp.py`

请回答：

1. `call_mcp_tool_exchange()` 做了哪些事？
2. unknown tool 是怎么被结构化表达的？
3. denied tool 的 `next_safe_action` 为什么重要？
4. `--show-execution` 会输出什么？
5. `to_response()` 为什么要把 execution record 放进 metadata？

## 练习 3：动手验证

运行：

```bash
python -m cli.mcp_demo --tool workspace_summary --show-execution
python -m cli.mcp_demo --tool write_project_file --path notes.txt --content "hello mcp" --show-execution
```

请记录：

1. 输出里是否包含 `protocol_version`？
2. 是否包含 `permission_decision`？
3. 是否包含 `error`？
4. denied write 时，是否能看到下一步安全动作？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么 MCP 工具层需要统一 execution record？
2. 为什么结构化错误比纯字符串错误更适合工业 Agent？
3. 下一阶段做 Skills governance 时，`v40` 最重要的基础价值是什么？

## 答案

### 练习 1：理解本阶段目标

1. `v40` 不是“把 MCP 再包一层”，因为它改的是执行协议边界，不只是代码组织。它让每次 MCP 调用都有统一 request、permission、response、error 和 execution id。
2. `MCPExecutionRecord` 的职责是把一次完整 MCP 执行结构化起来，方便 trace、调试、测试和后续恢复。
3. `MCPError` 要单独建模，是因为错误不是普通文本，而是包含阶段、错误码、消息和下一步安全动作的工程事实。
4. execution record 和 response metadata 要同时存在，是为了兼顾新旧链路：record 用来表达完整执行过程，metadata 用来把关键信息挂回现有 `MCPResponse`。
5. 保留旧的 `MCPResponse` 接口，是为了不破坏现有 agent 和 CLI 代码，同时让内部实现逐步升级。

### 练习 2：读 MCP 链路

1. `call_mcp_tool_exchange()` 会构造 client、查找 tool spec、评估权限、执行工具、封装 response，并返回标准化执行记录。遇到 unknown tool、permission denied 或 tool error 时，也会生成对应的结构化记录。
2. unknown tool 通过 `MCPRequest`、`MCPResponse`、`MCPPermissionDecision` 和 `MCPError` 一起表达，这样失败不是一句话，而是完整的可审计事件。
3. denied tool 的 `next_safe_action` 很重要，因为工业系统不仅要说“拒绝了”，还要说“下一步怎么修正”。这能让学习者看到可恢复边界。
4. `--show-execution` 会输出 execution record 的 JSON，包括 protocol version、execution id、request、permission decision、response 和 error。
5. `to_response()` 要把 execution record 放进 metadata，是为了让现有调用路径仍然拿到 `MCPResponse`，同时不丢失标准化执行信息。

### 练习 3：动手验证

1. 输出应当包含 `protocol_version`，因为这是执行记录的协议标记。
2. 输出应当包含 `permission_decision`，因为每次 MCP 执行都要留下权限判断证据。
3. denied write 时通常会包含 `error`，因为拒绝本身就是一种结构化失败。
4. 能看到下一步安全动作，说明系统不仅拒绝了请求，还给出了可执行的修正方向。

### 练习 4：工程取舍题

1. MCP 工具层需要统一 execution record，因为只有统一记录，才能把不同工具、不同失败、不同权限结果放到同一套观测和验证体系里。
2. 结构化错误比纯字符串错误更适合工业 Agent，因为它能被测试断言、日志分析、恢复策略和 CLI 检查程序直接消费。
3. `v40` 最重要的基础价值是：它把工具层从“可调用”推进到“可治理”。后续做 Skills governance 时，可以沿用同样的记录、权限和错误建模思路。

## 验证

```bash
python -m unittest tests.test_mcp -v
python -m cli.mcp_demo --tool workspace_summary --show-execution
```
