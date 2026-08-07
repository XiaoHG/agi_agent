# v01：Minimal CLI Agent

## 本阶段目标

先打通最小可运行 Agent 闭环：用户输入、路由判断、工具调用、最终回答。

## 本阶段解决的问题

- 让 Agent 不只是聊天，而是能根据输入选择是否调用工具。
- 让路由、工具执行和回答渲染分层，避免后续无法扩展。
- 让最小 Agent 有可测试、可回归的基础结构。

## 核心实现说明

### 1. 路由

`route_intent()` 负责把自然语言转换成可执行路由，例如：

- `use_tool`
- `direct_answer`

### 2. Agent 主链路

`WorkspaceAgent` 负责把路由结果转成实际执行流程，并产出最终 `AgentRun`。

### 3. 测试入口

`tests/test_agent.py` 是这个阶段最关键的回归入口，用来确保最小闭环稳定。

## 验证命令

```bash
python -m unittest tests.test_agent -v
python -m cli.main --input "Explain the difference between an agent and a chatbot." --trace
```

## 当前理解

v01 的重点不是“做强”，而是“做通”。
后续所有阶段，都是在这个最小闭环上继续增加路由、工具、RAG、MCP、Skills 和 graph 能力。
