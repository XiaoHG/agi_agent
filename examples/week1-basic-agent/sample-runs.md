# Week 1 Sample Runs

状态：已补充首轮运行样例。

## Run 1：直接回答

命令：

```bash
python -m cli.week1_basic_agent --input "请解释 Agent 和普通聊天机器人的区别。"
```

输入：

```text
请解释 Agent 和普通聊天机器人的区别。
```

输出摘要：

```text
Agent 会围绕目标主动做决策，并且可以调用工具、维护状态、分步骤完成任务。
```

## Run 2：读取 README

命令：

```bash
python -m cli.week1_basic_agent --input "请读取 README.md，并总结这个项目的学习目标。"
```

输入：

```text
请读取 README.md，并总结这个项目的学习目标。
```

输出摘要：

```text
项目学习目标包括：理解 Agent 和普通聊天问答程序的区别、设计单 Agent 系统、实现多步任务执行、接入 MCP/RAG/Skills/Subagent、读懂大型 Agent 项目的主链路、独立完成小型 Agent 应用。
```

## Run 3：目录说明

命令：

```bash
python -m cli.week1_basic_agent --input "请查看当前项目有哪些主要目录，并说明它们分别负责什么。"
```

输入：

```text
请查看当前项目有哪些主要目录，并说明它们分别负责什么。
```

输出摘要：

```text
agent/ 是 Agent 主链路实验目录，cli/ 是命令行入口，prompts/ 是 prompt 版本化目录，evals/ 是评估目录，tests/ 是测试目录，docs/ 是学习和复盘目录。
```

## Run 4：失败处理

命令：

```bash
python -m cli.week1_basic_agent --input "请读取 not-exist.md。"
```

输入：

```text
请读取 not-exist.md。
```

输出摘要：

```text
工具调用失败，原因是文件不存在：not-exist.md。
```

