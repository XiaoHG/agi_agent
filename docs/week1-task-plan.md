# Week 1 学习任务：最小 CLI Agent

开始日期：2026-07-23

## 本周目标

实现一个最小可运行 CLI Agent，掌握 Agent 的基本闭环。

本周只追求“小而完整”，不追求复杂框架。

## 本周必须理解的问题

1. Agent 和普通聊天程序有什么区别？
2. system prompt 在 Agent 中负责什么？
3. tool calling 为什么需要结构化输入输出？
4. 工具失败时 Agent 应该如何处理？
5. 为什么从第一周就要做 eval case？

## 本周最小实现范围

目录建议：

```text
agent/week1-basic-agent/
  README.md
  main.py
  agent.py
  tools.py

cli/
  week1_basic_agent.py

evals/week1-basic-agent/
  cases.md

examples/week1-basic-agent/
  sample-runs.md
```

## 功能要求

最小 CLI Agent 至少支持：

- 接收用户输入
- 加载 system prompt
- 判断是否需要工具
- 支持至少 2 个工具
- 将工具结果用于最终回答
- 工具失败时返回明确错误提示

建议第一版工具：

1. `read_file`：读取当前项目内的文本文件。
2. `list_dir`：列出当前项目内目录内容。

暂时不建议第一版直接开放任意 shell 命令。shell 工具风险高，应该等权限边界和命令白名单设计清楚后再做。

## 学习任务拆解

### Task 1：理解最小 Agent loop

要掌握：

```text
while not done:
  read user input
  ask model what to do
  if tool needed:
    call tool
    feed result back
  else:
    answer
```

验收：

- 能用自己的话解释 Agent loop。
- 能画出一张最小流程图。

### Task 2：设计工具 schema

要掌握：

- 工具名
- 工具描述
- 输入参数
- 输出格式
- 错误格式

验收：

- `read_file` 和 `list_dir` 有清晰输入输出定义。

### Task 3：实现 CLI Demo

要掌握：

- CLI 参数或交互输入
- prompt 加载
- 工具路由
- 错误处理

验收：

- 可以通过命令运行。
- 至少 3 个示例输入能得到稳定输出。

### Task 4：建立 eval case

要掌握：

- 什么是期望行为
- 什么是不接受行为
- 如何记录实际输出

验收：

- 至少 3 个 eval case。
- 每个 case 包含输入、期望行为、实际输出、结论。

## 本周 eval case 建议

### Case 1：直接回答

输入：

```text
请解释 Agent 和普通聊天机器人的区别。
```

期望：

- 不调用文件工具。
- 直接解释核心区别。

### Case 2：读取文件

输入：

```text
请读取 README.md，并总结这个项目的学习目标。
```

期望：

- 调用 `read_file`。
- 总结内容来自 README。
- 不编造不存在内容。

### Case 3：列出目录

输入：

```text
请查看当前项目有哪些主要目录，并说明它们分别负责什么。
```

期望：

- 调用 `list_dir`。
- 能结合 README 或目录说明解释用途。

### Case 4：错误处理

输入：

```text
请读取 not-exist.md。
```

期望：

- 返回文件不存在的明确错误。
- 不崩溃。
- 不编造文件内容。

## 本周完成标准

只有满足以下条件，Week 1 才算完成：

- `agent/week1-basic-agent/` 有可运行代码。
- 有明确启动方式。
- 至少有 2 个工具。
- 至少有 3 个 eval case。
- 至少记录 1 个失败案例。
- 能解释当前 Agent 的运行链路。

## 本周不做的事

- 不做复杂 UI。
- 不接数据库。
- 不做长期记忆。
- 不做多 Agent。
- 不接复杂 RAG。
- 不引入大型框架，除非最小闭环已经完成。

