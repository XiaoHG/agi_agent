# Agent 开发学习总任务大纲

更新时间：2026-07-23

## 总目标

通过一个长期演进的本地 Agent 项目，系统掌握 Agent 开发的核心机制和工程化方法。

最终不是只会调用模型接口，而是能够独立设计、实现、调试、评估一个可维护的 Agent 系统。

## 能力地图

本项目学习分为 8 个能力层级。

### L1：最小 Agent 闭环

目标：理解 Agent 和普通聊天应用的本质区别。

必须掌握：

- 用户输入如何进入 Agent
- system prompt 如何约束行为
- 模型如何决定是否调用工具
- 工具结果如何回传给模型
- 最终回答如何生成

产出：

- `agent/week1-basic-agent/`
- 一个可运行 CLI Agent
- 至少 3 个 eval case

### L2：工具调用与安全边界

目标：让 Agent 能可靠调用工具，并避免危险行为。

必须掌握：

- tool schema 设计
- 工具参数校验
- 工具失败处理
- 超时、重试、错误分类
- 权限边界

产出：

- 文件读取工具
- 安全 shell 工具或模拟 shell 工具
- 工具调用日志

### L3：状态、记忆与工作流

目标：让 Agent 能分步骤完成任务，而不是一次性回答。

必须掌握：

- state
- step loop
- workflow
- short-term memory
- run id / trace id
- 中间结果复用

产出：

- `agent/week2-workflow-agent/`
- 状态流转图
- 多步任务样例

### L4：RAG

目标：让 Agent 能基于本地知识回答，而不是只依赖模型记忆。

必须掌握：

- 文档加载
- chunking
- embedding
- retrieval
- rerank
- context assembly
- 引用来源
- RAG eval

产出：

- `rag/week3-rag-demo/`
- 本地文档问答 Demo
- 检索失败案例分析

### L5：MCP

目标：理解如何把外部能力通过统一协议暴露给 Agent。

必须掌握：

- MCP Server
- MCP Client
- tools / resources / prompts
- 输入输出 schema
- 工具权限和隔离

产出：

- `mcp/week3-mcp-demo/`
- 一个自定义 MCP Server
- Agent 通过 MCP 调用工具

### L6：Skills

目标：把高频任务封装为可复用能力。

必须掌握：

- skill 适用场景
- skill 输入约束
- skill 执行步骤
- skill 输出格式
- skill 与 prompt/tool/workflow 的关系

产出：

- `skills/week4-skills/`
- 2-3 个可复用 Skill

### L7：Subagent / 多 Agent 协作

目标：理解什么时候需要多 Agent，以及多 Agent 的真实成本。

必须掌握：

- planner / executor / reviewer
- supervisor-worker
- 任务拆分
- 角色边界
- 消息协议
- 失败传播
- 成本与延迟控制

产出：

- `subagent/week4-multi-agent-demo/`
- 多角色协作 Demo

### L8：工程化、评估与产品原型

目标：把 Demo 变成可维护、可复现、可解释的项目。

必须掌握：

- configs
- logs
- traces
- tests
- evals
- examples
- README 运行说明
- 错误处理
- 已知限制

产出：

- `evals/week5-regression/`
- `tests/`
- 综合项目 Demo

## 学习节奏

默认节奏：6 周。

每周投入：8-12 小时。

每周固定节奏：

1. 学概念：理解本周主题。
2. 写 Demo：必须有可运行结果。
3. 做 eval：记录输入、期望行为和实际输出。
4. 复盘失败：按 prompt / tool / rag / state / architecture 分类。
5. 沉淀文档：更新进度文件，确保下个会话能恢复。

## 当前优先级

当前阶段从 L1 开始。

第一优先级不是接入复杂框架，而是先写出最小 Agent 闭环：

```text
用户输入 -> Agent 决策 -> 工具调用 -> 工具结果 -> 最终回答
```

暂时不建议：

- 一开始就上 LangGraph
- 一开始就做复杂多 Agent
- 一开始就接大型 RAG 系统
- 一开始就追求 UI
- 一开始就读大型源码

原因：这些都会掩盖 Agent 最核心的运行机制。

