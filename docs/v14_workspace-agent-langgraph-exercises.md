# Workspace Agent LangGraph 集成 v14 练习

对应版本：v14  
主题：Workspace Agent LangGraph integration  
用途：理解 LangGraph 如何从独立 demo 变成主 Agent 的执行通道

## 练习 1：理解本阶段目标

请回答：

1. v14 为什么不是“再做一个 LangGraph demo”，而是“把 graph 接回 `WorkspaceAgent`”？
2. `action = "graph"` 和 `tool_name = "langgraph_workflow"` 分别代表什么？
3. 为什么 `WorkspaceAgent.run()` 要把 graph 结果回填到 `AgentRun.tool_result` 和 `AgentRun.answer`？
4. 为什么这次要保留 trace，而不是只返回最终 answer？
5. 为什么 v14 仍然需要 deterministic tests？

## 练习 2：读 LangGraph 接入链路

阅读以下文件：

- `agent/router.py`
- `agent/core.py`
- `tests/test_agent.py`
- `tests/test_langgraph_workflow.py`
- `evals/regression_cases.json`

请回答：

1. `route_intent()` 新增了哪些 `graph` 相关关键词？
2. `_run_langgraph()` 的职责是什么？
3. `_format_langgraph_answer()` 和 `_describe_langgraph_state()` 分别做什么？
4. `WorkspaceAgent` 为什么还要保留原有 `workflow / use_tool / direct_answer` 分支？
5. `test_agent_runs_langgraph_workflow` 这类测试主要验证了什么？

## 练习 3：读 graph 状态与 trace

请结合 v14 版本文档理解：

- `versions/v14_workspace-agent-langgraph.md`
- `docs/current-learning-state.md`

请回答：

1. graph 执行结果里哪些字段应该进入 trace？
2. `selected_tool` 和 `route` 在 v14 中为什么都重要？
3. 为什么 `graph steps` 不能只存在于 CLI 文本里？
4. 如果 graph 无 context 返回了不足信息，Agent 应该如何呈现？
5. 为什么 graph 结果仍要保持和 classic Agent surface 兼容？

## 练习 4：手动运行验证

运行：

```bash
python -m unittest tests.test_agent tests.test_langgraph_workflow tests.test_evals -v
```

请记录：

1. 总共运行了多少个测试？
2. 是否全部通过？
3. 哪些测试是 v14 直接相关的？

运行：

```bash
python -m cli.main --input "Use LangGraph to search docs for MCP." --trace
```

请记录：

1. route 是什么？
2. selected tool 是什么？
3. trace 中是否保留了 graph steps？
4. 最终答案是否回填到了 `run.answer`？

## 练习 5：阶段评估题

请用自己的话回答：

1. v14 解决的是哪类“执行入口收口”问题？
2. 为什么主 Agent 接入 graph 后，trace 反而更重要了？
3. 这次为什么没有直接把所有能力都并入 graph？
4. 你认为下一阶段最值得继续 graph 化的是什么？

## 完成标准

可以进入下一阶段的标准：

- 能画出 `WorkspaceAgent -> LangGraph -> answer` 的完整链路。
- 能解释 `route`、`selected_tool`、`steps` 和 `answer` 的关系。
- 能说明为什么 v14 只是把 graph 接回主链路，而不是一次性重写所有能力。
- 能运行定向测试并理解新增回归用例的覆盖范围。

## 答案

### 练习 1

1. 因为 v14 的重点是把 graph 纳入主 Agent 执行链，而不是单独做演示。
2. `action = "graph"` 表示路由到 graph 执行；`tool_name = "langgraph_workflow"` 表示具体调用 graph 工具。
3. 因为 graph 不是独立输出，必须回填到统一的 Agent run 结构里。
4. 因为 trace 是学习和排错的核心证据。
5. 因为路由和 graph 行为都需要稳定回归。

### 练习 2

1. `langgraph`、`use graph`、`run graph`、`graph workflow`、`graph answer`、`answer with graph`。
2. `_run_langgraph()` 负责执行 graph 并拿到结果。
3. `_format_langgraph_answer()` 负责渲染最终答案；`_describe_langgraph_state()` 负责描述 graph state。
4. 因为这些分支仍然是主 Agent 的基础能力，不应被 graph 一次性替换。
5. 主要验证主 Agent 能否真正走进 graph 分支并返回正确结果。

### 练习 3

1. `route`、`selected_tool`、`steps`、`answer` 和必要的 graph state 结果。
2. `route` 说明意图层路由，`selected_tool` 说明 graph 内部选择的执行工具。
3. 因为 graph steps 是可追踪执行证据，不应只停留在一次性文本输出里。
4. 应该明确说明上下文不足，并保留 graph 的结构化信息。
5. 因为学习阶段仍要兼容现有 CLI 和 Agent 输出 surface。

### 练习 4

1. 以本地测试实际输出为准。
2. 以测试结果实际输出为准。
3. `test_agent_runs_langgraph_workflow`、`test_langgraph_workflow_*`、相关 eval case。
4. `route` 应该进入 graph；`selected tool` 应该是 graph 对应工具；`steps` 和 `run.answer` 应该可见。

### 练习 5

1. 解决的是“主入口如何统一进入 graph”的问题。
2. 因为 graph 承担了更多执行细节，必须更容易观察。
3. 因为这阶段目标是主链路接回，不是完全重构所有能力。
4. RAG、tool、Skills 的统一编排。
