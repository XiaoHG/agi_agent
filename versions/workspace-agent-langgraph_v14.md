# Workspace Agent LangGraph 集成 v14

版本：v14  
日期：2026-07-28

## 本次目标

把现有的 `LangGraph` 工作流正式接回 `WorkspaceAgent` 主链路。  
用户显式要求“用 LangGraph 处理”时，主 Agent 不再只把它当成独立 demo，而是直接进入 graph 执行路径，并把 graph 的路由、选用工具、步骤和最终答案一起写回 trace。

这次迭代的重点不是“再加一个 demo”，而是让主 Agent 的执行体系更完整。

## 本次新增能力

1. 主路由新增 `graph` 分支。
2. `WorkspaceAgent.run()` 可以直接执行 LangGraph workflow。
3. graph 的执行结果会进入 `AgentRun.tool_result` 和 `AgentRun.answer`。
4. 主 Agent trace 会保留 graph route、selected tool 和 graph steps。
5. 回归评估新增 3 个 LangGraph 用例。
6. 学习状态文档更新了恢复入口。

## 代码改动说明

### `agent/router.py`

新增 LangGraph 显式路由判断：

- `langgraph`
- `use graph`
- `run graph`
- `graph workflow`
- `graph answer`
- `answer with graph`

同时新增了问句清理逻辑，确保像下面这种输入会被正确抽取：

- `Use LangGraph to search docs for MCP.`
- `Use LangGraph to read README.md.`
- `Use LangGraph to answer: the and of`

返回结果是：

- `action = "graph"`
- `tool_name = "langgraph_workflow"`
- `tool_input = 清理后的问题`

### `agent/core.py`

在 `WorkspaceAgent.run()` 中新增 graph 分支：

- 先执行 `run_rag_graph()`
- 再把 graph state 格式化成 trace
- 最后把 graph answer 回填给用户

新增了两个辅助方法：

- `_run_langgraph()`
- `_format_langgraph_answer()`
- `_describe_langgraph_state()`

这让主 Agent 继续保持原有的 `workflow / use_tool / direct_answer` 逻辑，同时增加一条独立的 graph 执行通道。

### `tests/test_agent.py`

新增覆盖：

- LangGraph 路由识别
- LangGraph 搜索文档
- LangGraph 读取 README
- LangGraph 无上下文回答
- LangGraph trace 记录

### `evals/regression_cases.json`

新增 3 条回归用例：

- `langgraph-search-docs`
- `langgraph-read-readme`
- `langgraph-no-context`

### `README.md`

补充了一个新的运行入口：

```bash
python -m cli.main --input "Use LangGraph to search docs for MCP." --trace
```

### `docs/current-learning-state.md`

更新了：

- 当前阶段状态
- 已完成项
- 未完成项
- 恢复指令

这样下次会话可以直接从 v14 继续。

### `evals/README.md`

补充了对 LangGraph 回归用例的说明。

## 新增文件与行数

| 文件 | 行数 |
| --- | ---: |
| `versions/workspace-agent-langgraph_v14.md` | 146 |

## 本次修改文件与行数

| 文件 | 行数 |
| --- | ---: |
| `agent/router.py` | 341 |
| `agent/core.py` | 363 |
| `tests/test_agent.py` | 155 |
| `evals/regression_cases.json` | 100 |
| `docs/current-learning-state.md` | 171 |
| `README.md` | 602 |
| `evals/README.md` | 54 |

## 验证命令

```bash
python -m unittest tests.test_agent tests.test_langgraph_workflow tests.test_evals -v
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.main --input "Use LangGraph to search docs for MCP." --trace
python -m cli.main --input "Use LangGraph to read README.md." --trace
python -m cli.main --input "Use LangGraph to answer: the and of" --trace
```

## 结果

- 全量测试通过：74 / 74
- 回归用例通过：14 / 14
- LangGraph 主 Agent trace 正常输出 route、selected tool、steps 和 final answer

## 当前理解

这次改动把 LangGraph 从“独立 workflow demo”提升为“主 Agent 可调用的编排层”。  
下一阶段更值得做的不是继续堆 demo，而是继续把 graph 做深：

- 让 graph 承担更复杂的分支
- 让 graph 接入 MCP / Skills / RAG 的统一选择
- 让主 Agent 的默认执行路径更接近真实产品化编排
