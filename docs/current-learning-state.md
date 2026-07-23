# 当前学习进度状态

此文件用于跨会话恢复学习进度。每次学习任务结束后都应更新。

## Last Updated

2026-07-23

## 当前阶段

Week 1：Agent 基础 / 最小 CLI Agent。

## 当前教师判断

项目结构已经具备学习型 Agent 工程仓库的基本形态：

- 核心能力目录已经存在：`agent/ mcp/ rag/ skills/ subagent/`
- 工程支撑目录已经存在：`prompts/ evals/ tests/ examples/ docs/ configs/ scripts/`
- 默认协作 Agent 已定义：Teacher Agent 和 Coding Agent

当前缺口：

- 还没有实际可运行 Agent 代码。
- 还没有 Week 1 eval case。
- 还没有示例运行记录。
- 还没有测试。

## 当前总目标

完成 Week 1 的最小 CLI Agent。

## 当前具体任务

下一步应由 Coding Agent 执行：

1. 创建 `agent/week1-basic-agent/`。
2. 实现最小 Agent loop。
3. 实现 `read_file` 和 `list_dir` 两个安全工具。
4. 创建 CLI 入口。
5. 创建 Week 1 eval case。
6. 运行最小验证。

## 当前学习重点

学习者需要重点理解：

- Agent 不是一次 prompt，而是“模型决策 + 工具执行 + 结果回传”的循环。
- 工具必须有明确边界，否则 Agent 会变成不安全的命令执行器。
- eval case 是学习 Agent 的核心资产，用于判断系统是否真的变好。

## 已完成

- 初始化项目目录。
- 创建 README 学习路线。
- 创建 Teacher Agent / Coding Agent 定义。
- 创建仓库级 `AGENTS.md` 协作规则。
- 创建学习总任务大纲：`docs/learning-master-plan.md`。
- 创建 Week 1 任务计划：`docs/week1-task-plan.md`。

## 未完成

- Week 1 最小 CLI Agent 代码。
- Week 1 eval case 文件。
- Week 1 示例运行记录。
- Week 1 复盘。

## 恢复指令

下一个会话恢复时，请先读取：

1. `AGENTS.md`
2. `docs/current-learning-state.md`
3. `docs/week1-task-plan.md`
4. `subagent/teacher-agent/agent.md`
5. `subagent/coding-agent/agent.md`

然后继续执行当前具体任务。

## 下一步建议

直接进入 Coding Agent 阶段，开始实现 Week 1 最小 CLI Agent。

建议第一版使用 Python，因为：

- 学习成本低。
- CLI 实现简单。
- 后续接 RAG、MCP、eval 都方便。
- 工具函数和测试容易组织。

