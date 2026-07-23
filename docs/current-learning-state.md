# 当前学习进度状态

此文件用于跨会话恢复学习进度。每次学习任务结束后都应更新。

## Last Updated

2026-07-23

## 当前阶段

Week 1：Agent 基础 / 最小 CLI Agent。

当前状态：Week 1 基线已实现。

## 当前教师判断

项目已经从“学习目录骨架”进入“可运行 Agent 实验”阶段。

已具备：

- 核心能力目录：`agent/ mcp/ rag/ skills/ subagent/`
- 工程支撑目录：`prompts/ evals/ tests/ examples/ docs/ configs/ scripts/`
- 默认协作 Agent：Teacher Agent 和 Coding Agent
- Week 1 最小 CLI Agent
- 本地工具：`read_file`、`list_dir`
- trace 输出
- 工具失败处理
- 自动化测试

当前缺口：

- Week 1 复盘还未完成。
- Week 1 eval case 还可以继续扩充。
- 还没有进入 Week 2 的状态/记忆/workflow 实现。

## 当前总目标

先巩固 Week 1：确认你理解最小 Agent 闭环，然后进入 Week 2。

最小闭环：

```text
用户输入 -> 路由判断 -> 工具调用或直接回答 -> 工具结果/错误 -> 最终回答
```

## 当前具体任务

下一步建议：

1. 由 Teacher Agent 讲解 Week 1 代码结构。
2. 你手动运行 3-4 个 CLI 示例，观察 trace。
3. 补一份 Week 1 复盘。
4. 再进入 Week 2：状态、记忆与工作流。

## 当前学习重点

学习者需要重点理解：

- Agent 不是一次 prompt，而是“路由判断 + 工具执行 + 结果合成”的流程。
- 工具必须有明确边界，否则 Agent 会变成不安全的命令执行器。
- 错误处理是 Agent 最小闭环的一部分，不是后期再补的细节。
- eval case 是学习 Agent 的核心资产，用于判断系统是否真的变好。

## 已完成

- 初始化项目目录。
- 创建 README 学习路线。
- 创建 Teacher Agent / Coding Agent 定义。
- 创建仓库级 `AGENTS.md` 协作规则。
- 创建学习总任务大纲：`docs/learning-master-plan.md`。
- 创建 Week 1 任务计划：`docs/week1-task-plan.md`。
- 实现 Week 1 最小 CLI Agent。
- 实现 `read_file` 和 `list_dir` 两个本地安全工具。
- 实现输入路由、trace 和失败处理。
- 补充自动化测试并通过验证。
- 补充 Week 1 架构图：`docs/week1-architecture.md`。
- 补充 Week 1 示例运行记录：`examples/week1-basic-agent/sample-runs.md`。
- 更新 Week 1 eval case 实际结果：`evals/week1-basic-agent/cases.md`。

## 未完成

- Week 1 复盘总结。
- Week 2 状态与工作流设计。
- 后续接入真实 LLM 决策层。

## 恢复指令

下一个会话恢复时，请先读取：

1. `AGENTS.md`
2. `docs/current-learning-state.md`
3. `docs/week1-task-plan.md`
4. `docs/week1-architecture.md`
5. `subagent/teacher-agent/agent.md`
6. `subagent/coding-agent/agent.md`

然后继续执行当前具体任务。

## 下一步建议

先不要马上接复杂框架。下一步优先让 Teacher Agent 讲解这次新增代码：

- `agent/core.py`
- `agent/router.py`
- `agent/tools.py`
- `cli/main.py`

理解后再进入 Week 2。
