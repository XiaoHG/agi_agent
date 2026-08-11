# Standardized MCP Governance v47 练习

对应版本：v47  
主题：Standardized MCP Governance  
用途：理解 MCP 为什么必须先校验、再授权、最后执行

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v47` 要把 request validation 放在 permission check 前面？
2. `MCPRequestValidationResult` 解决了什么问题？
3. 为什么治理审计要记录 `lookup / validation / permission / execution`？
4. 为什么 `protocol_version` 需要升级到 `v2`？
5. 这一步为什么是“治理升级”，而不是普通 bugfix？

## 练习 2：读治理链路

阅读：

- `mcp/schema.py`
- `mcp/policy.py`
- `mcp/adapter.py`
- `tests/test_mcp.py`

请回答：

1. `MCPGovernancePolicy` 控制了哪几个行为？
2. `validate_mcp_request()` 如何判断缺失参数和多余参数？
3. `call_mcp_tool_exchange()` 在校验失败时会返回什么结构？
4. 为什么 unknown tool 也要返回结构化错误记录？
5. `MCPExecutionRecord.to_dict()` 为什么要包含 `governance_audit`？

## 练习 3：动手验证

运行：

```bash
python -m unittest tests.test_mcp -v
python -m cli.mcp_demo --tool workspace_summary --show-execution
python -m cli.mcp_demo --tool read_project_file --show-execution
```

请记录：

1. `workspace_summary` 的执行记录里是否出现 `protocol_version = v2`？
2. `read_project_file` 在缺少参数时是否进入 validation error？
3. `governance_audit` 里是否能看到阶段顺序？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么工具层不能只靠权限策略，必须同时做请求校验？
2. 为什么 `validation` 失败要早于 `permission` 失败？
3. 如果后续要接外部 MCP server，`v47` 最重要的基础价值是什么？

## 答案

### 练习 1：理解本阶段目标

1. 因为权限只能决定是否允许某类工具，不能判断参数是否符合工具 schema。
2. `MCPRequestValidationResult` 解决的是请求是否合法、缺了什么、多了什么、该如何规范化的问题。
3. 因为专业 Agent 需要可审计证据，知道失败发生在检索、校验、授权还是执行。
4. 因为治理规则已经改变，协议版本必须显式区分旧行为和新行为。
5. 因为 `v47` 改的是工具层正式边界，而不是修一个单点错误。

### 练习 2：读治理链路

1. `MCPGovernancePolicy` 控制协议版本、是否拒绝多余参数、是否拒绝缺失必填参数。
2. `validate_mcp_request()` 会读取工具 schema 的 `required` 和 `properties`，并据此判断缺失和多余参数。
3. 校验失败时会返回带 `request_validation`、`governance_policy` 和错误信息的结构化响应。
4. 因为 unknown tool 也是治理失败的一种，必须保留结构化证据，方便 trace 和恢复。
5. 因为 `governance_audit` 能把调用过程拆成阶段化证据，便于测试和后续扩展。

### 练习 3：动手验证

1. 是，`workspace_summary` 的执行记录里应出现 `protocol_version = v2`。
2. 是，`read_project_file` 缺少参数时应进入 validation error。
3. 是，`governance_audit` 应能看到 `lookup -> validation -> permission -> execution` 的阶段顺序。

### 练习 4：工程取舍题

1. 因为只做权限判断会放过非法请求，导致错误晚发现、晚定位。
2. 因为参数不合法时不应继续进入权限决策，先拦住请求更清晰也更省成本。
3. `v47` 最重要的基础价值，是把 MCP 从学习骨架推进到可治理、可审计、可扩展的正式工具边界。
