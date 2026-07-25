# 当前学习进度状态

此文件用于跨会话恢复学习进度。每次学习任务结束后都应更新。

## Last Updated

2026-07-25

## 当前阶段

Week 3：RAG 与 MCP。

当前状态：RAG 最小闭环已提交，MCP 最小骨架已开始实现。

## 当前教师判断

项目已经从“本地知识检索实验”进入“本地 MCP 协议边界实验”阶段。

已具备：

- Week 1 最小 CLI Agent
- Week 2 状态与工作流
- Week 3 本地 RAG 最小闭环
- 本地工具：`read_file`、`list_dir`、`count_lines`、`search_docs`
- 本地 MCP server / client / adapter 骨架
- Agent 可调用 MCP 工具列表和 workspace summary
- trace 输出
- 工具失败处理
- 自动化测试

当前缺口：

- MCP 还只是进程内模拟，没有接真实 MCP SDK 或传输层。
- MCP eval case 还未补充。
- MCP 还没有和 RAG 形成组合 workflow。

## 当前总目标

先巩固 MCP 最小边界：理解 server、client、schema、adapter 分别负责什么。

最小 MCP 学习链路：

```text
MCP Server -> MCP Client -> Agent adapter -> Agent tool call -> CLI output
```

## 当前具体任务

下一步建议：

1. 由 Teacher Agent 讲解 MCP 最小骨架。
2. 你手动运行 MCP CLI 示例，观察 server/client/adapter 的边界。
3. 补 MCP eval case。
4. 再评估是否进入 Skills 与 Subagent 阶段。

## 当前学习重点

学习者需要重点理解：

- MCP 的价值不是某个具体工具，而是用统一协议暴露外部能力。
- server 负责声明和执行工具。
- client 负责按协议请求 server。
- adapter 负责把 MCP 能力转换成当前 Agent 可以调用的本地工具。
- 当前实现是学习版模拟，不等于完整生产 MCP 接入。

## 已完成

- 初始化项目目录。
- 创建 README 学习路线。
- 创建 Teacher Agent / Coding Agent 定义。
- 创建仓库级 `AGENTS.md` 协作规则。
- 创建学习总任务大纲：`docs/learning-master-plan.md`。
- 实现 Week 1 最小 CLI Agent。
- 完成 Week 2 状态与工作流实现。
- 完成 Week 3 本地 RAG 最小闭环。
- 提交 RAG 阶段代码：`03c0005 Add local RAG search stage`。
- 开始实现 MCP 最小骨架。

## 未完成

- MCP 评估用例。
- MCP 练习复盘。
- 真实 MCP SDK / transport 接入。
- 后续接入真实 LLM 决策层。

## 恢复指令

下一个会话恢复时，请先读取：

1. `AGENTS.md`
2. `docs/current-learning-state.md`
3. `docs/learning-master-plan.md`
4. `mcp/README.md`
5. `tests/test_mcp.py`
6. `versions/mcp-local-protocol_v4.md`

然后继续执行当前具体任务。

## 下一步建议

下一步优先让 Teacher Agent 讲解这次新增代码：

- `mcp/schema.py`
- `mcp/servers/local_server.py`
- `mcp/clients/local_client.py`
- `mcp/adapter.py`
- `cli/mcp_demo.py`
- `agent/tools.py`
- `agent/router.py`
