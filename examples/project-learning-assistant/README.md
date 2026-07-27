# Project Learning Assistant Example

这个示例是 Week 6 综合项目的最小原型。

它不是新增一套复杂框架，而是把前面阶段已经完成的能力串成一个可运行链路：

```text
README reading
  -> local RAG search
  -> MCP workspace summary
  -> skill selection
  -> subagent collaboration planning
  -> regression eval
  -> project report
```

## 运行命令

```bash
python -m cli.project_demo
```

指定目标：

```bash
python -m cli.project_demo --objective "Verify the learning assistant prototype."
```

## 当前能力

- 读取 `README.md`，确认项目学习目标。
- 检索本地文档，获取 workflow、RAG、MCP、skills、subagent、eval 的相关上下文。
- 调用本地 MCP workspace summary。
- 选择一个适合代码评审任务的 skill。
- 规划 Teacher Agent 和 Coding Agent 的协作流程。
- 运行 deterministic regression eval，确认已有主链路没有回归。

## 学习重点

本阶段重点不是“功能数量”，而是理解一个可交付 Agent 原型应该如何组合已有能力：

- 输入目标要清楚。
- 能力链路要可解释。
- 每一步输出要可检查。
- 最后要有自动化验证。
