# v47：Standardized MCP Governance

## 本阶段目标

把本地 MCP 学习骨架升级为带请求校验、权限治理和审计轨迹的标准化执行边界。

## 本阶段在工业 Agent 中的位置

MCP 是外部工具层的正式接口。没有统一治理时，工具调用会变成：

- 只看工具名，不看参数是否合法
- 只看能不能执行，不看是否应该执行
- 只看结果，不保留治理证据

`v47` 解决的是“工具层如何从可调用，升级到可治理、可审计、可回放”。

## 本阶段解决的问题

- 让 MCP request 在权限判断前先做 schema 校验
- 让请求校验、权限判断、执行结果进入统一审计轨迹
- 让未知工具、非法参数、权限拒绝都返回结构化记录
- 让 MCP 协议版本显式升级到 `v2`

## 本阶段新增能力

### 1. MCP 请求校验结果

新增：

- `MCPRequestValidationResult`
- `validate_mcp_request()`

支持：

- 缺失必填参数检测
- 多余参数检测
- 参数规范化

### 2. 标准化 MCP 治理策略

新增：

- `MCPGovernancePolicy`
- `build_default_mcp_governance_policy()`

支持：

- 协议版本声明
- 是否拒绝多余参数
- 是否拒绝缺失必填参数

### 3. 治理审计轨迹

增强：

- `MCPExecutionRecord`
- `call_mcp_tool_exchange()`

现在每次调用都会记录：

- `lookup`
- `validation`
- `permission`
- `execution`

### 4. 协议版本升级

当前协议版本：

- `v2`

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `mcp/schema.py` | 增加请求校验结果和执行记录字段 |
| `mcp/policy.py` | 增加治理策略和请求校验逻辑 |
| `mcp/adapter.py` | 把校验、权限、执行串成标准治理链路 |
| `mcp/__init__.py` | 导出新模型与函数 |
| `mcp/README.md` | 更新协议版本和治理说明 |
| `tests/test_mcp.py` | 增加治理校验与审计轨迹测试 |
| `docs/current-learning-state.md` | 更新当前学习状态 |
| `docs/plans/v3_professional-agent-iteration-plan.md` | 已包含 v47 规划 |

## 核心实现说明

### 1. 为什么要先做请求校验

因为权限判断只能决定“能不能用”，不能决定“参数对不对”。

先校验请求，再判断权限，才能把错误尽早拦下并给出明确修正方向。

### 2. 为什么治理审计必须分阶段记录

因为专业 Agent 需要知道问题发生在哪一层：

- 工具不存在
- 参数不合法
- 权限不允许
- 工具执行失败

分阶段记录后，测试、eval 和恢复都能直接复用这些证据。

### 3. 为什么协议版本要显式升级

因为治理规则变了，协议语义也变了。

显式版本号可以避免后续文档、测试和客户端误把旧行为当成新规范。

## 运行示例

查看 MCP 工具：

```bash
python -m cli.mcp_demo --list-tools
```

查看标准执行记录：

```bash
python -m cli.mcp_demo --tool workspace_summary --show-execution
```

查看校验失败示例：

```bash
python -m cli.mcp_demo --tool read_project_file --show-execution
```

## 验证命令

```bash
python -m unittest tests.test_mcp -v
python -m unittest discover -s tests -q
python -m cli.mcp_demo --tool workspace_summary --show-execution
```

## 当前边界

- 这是本地进程内 MCP 学习版，不是真实网络 MCP server/client
- 当前校验逻辑偏向学习型 schema 检查，还不是完整 JSON Schema 引擎
- 目前重点是先把治理边界做清楚，再继续扩展外部接入

## 下一步建议

下一阶段建议进入 `v48`，继续做 `Skills Governance and Versioning`，把技能层也推进到可治理、可版本化的专业能力层。
