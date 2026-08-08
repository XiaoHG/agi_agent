# v40：Standardized MCP Execution Boundary

## 本阶段目标

把本地学习版 MCP 调用提升为标准化执行边界，让每次 MCP 调用都能产出统一的执行记录、结构化错误和可审计的 response metadata。

## 本阶段在工业 Agent 中的位置

工业 Agent 的工具层不能只“能调用”，还必须“可约束、可追踪、可恢复”。

`v40` 解决的是 MCP 工具执行从学习式适配，向标准执行协议靠拢的问题：

- 每次调用都有统一 execution record
- 每次失败都有结构化 error
- 每次 permission decision 都能落盘
- CLI 能直接查看执行边界

## 本阶段解决的问题

- 让 MCP 调用结果不再只是一个扁平字符串
- 让 unknown tool / denied tool / tool error 有统一结构
- 让 permission metadata 和 execution metadata 分离但可合并
- 让 agent / CLI / tests 共用同一套 MCP 执行边界

## 本阶段新增能力

### 1. MCPError

新增 `MCPError`，用于表达结构化错误：

- stage
- code
- message
- next_safe_action

### 2. MCPExecutionRecord

新增 `MCPExecutionRecord`，用于封装一次完整 MCP 执行：

- request
- permission policy
- permission decision
- response
- error
- protocol version
- execution id

### 3. 标准化 adapter 边界

新增 `call_mcp_tool_exchange()`，让 adapter 返回结构化执行记录，再由 `to_response()` 生成兼容旧接口的 `MCPResponse`。

### 4. execution inspection CLI

`cli.mcp_demo` 新增 `--show-execution`，可以直接打印标准化执行记录 JSON。

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `mcp/schema.py` | 新增 `MCPError` / `MCPExecutionRecord` |
| `mcp/adapter.py` | 新增标准化 MCP 执行边界 |
| `mcp/__init__.py` | 导出新模型和新入口 |
| `cli/mcp_demo.py` | 增加 `--show-execution` |
| `mcp/README.md` | 说明标准执行边界 |
| `cli/README.md` | 补充执行记录查看命令 |
| `tests/test_mcp.py` | 覆盖 execution record 与 CLI |
| `docs/current-learning-state.md` | 更新学习状态 |

## 核心实现说明

### 1. 为什么这是一个大功能版本

因为它改的不是一个小 helper，而是 MCP 工具层的执行边界：

- 调用前有 request
- 调用时有 permission decision
- 调用后有 response / error
- 对外有结构化 trace 入口

这使 MCP 从“本地演示工具”进入“可治理工具层”的学习阶段。

### 2. 为什么要保留旧的 response 接口

因为现有 agent / CLI / 测试已经依赖 `MCPResponse`。

本阶段采用的是：

- 内部升级为 `MCPExecutionRecord`
- 外部继续兼容 `MCPResponse`

这样可以平滑过渡，不打断现有链路。

### 3. 为什么 unknown tool 也要有 execution record

因为工业系统里，失败调用也是行为证据。

unknown tool 不是“没有结果”，而是：

- request 存在
- 选择失败
- 错误可分类
- 下一步动作可提示

## 运行示例

查看执行记录：

```bash
python -m cli.mcp_demo --tool workspace_summary --show-execution
```

查看写入型工具的执行记录：

```bash
python -m cli.mcp_demo --tool write_project_file --path notes.txt --content "hello mcp" --show-execution
```

## 验证命令

```bash
python -m unittest tests.test_mcp -v
python -m unittest tests.test_agent tests.test_langgraph_workflow tests.test_tool_calling tests.test_persistence -v
```

## 当前边界

- 仍然是本地 in-process MCP 学习层
- 还没有真实网络 transport
- 还没有完整 MCP 标准协议实现
- 但已经具备统一执行记录和结构化错误边界

## 下一步建议

下一阶段应进入：

`v41：Skills Governance and Runtime Policy`

重点是把 Skills 从“可执行”推进到“可治理、可约束、可版本化”。
