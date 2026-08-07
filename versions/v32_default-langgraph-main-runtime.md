# v32：默认 LangGraph 主执行器

## 本阶段目标

把 `WorkspaceAgent` 从“只有显式 graph 请求才走 LangGraph”推进到“LangGraph 成为默认主执行器”，同时保留 classic runtime 作为显式 fallback，方便学习和对照。

本阶段形成的闭环是：

```text
user input
-> top-level route_intent()
-> route hint
-> LangGraph main runtime
-> direct answer / tool / skill / MCP
-> classic surface answer + graph metadata
```

## 本阶段新增文件

| 文件 | 作用 |
|---|---|
| `versions/default-langgraph-main-runtime_v32.md` | 本阶段版本说明 |
| `docs/default-langgraph-main-runtime-exercises_v32.md` | 本阶段练习 |

## 本阶段修改文件

| 文件 | 主要变化 |
|---|---|
| `integrations/langgraph_workflow.py` | graph state 新增 route hint / logical tool / tool metadata，并扩展为主运行时可消费的统一图 |
| `agent/core.py` | `WorkspaceAgent` 默认走 graph runtime，并保留 `_run_classic_route()` fallback |
| `cli/main.py` | 新增 `--classic-runtime`，便于对照默认 graph runtime 和旧主控 |
| `tests/test_agent.py` | 增加默认 graph runtime 和 classic opt-out 测试 |
| `cli/README.md` | 增加默认 graph runtime 与 classic runtime 对照命令 |
| `docs/current-learning-state.md` | 更新当前阶段和下一步建议 |

## 核心实现说明

### 1. 顶层 router 不再直接执行，而是变成 graph route hint

`route_intent()` 仍然保留，它的职责不再只是最终决定执行分支，而是先提供一个稳定、可测试的 route hint。

例如：

```text
Read README.md
-> route.action = use_tool
-> route.tool_name = read_file
```

随后 `WorkspaceAgent` 会把这个 hint 传入 LangGraph，而不是直接在 if/else 里执行工具。

### 2. LangGraph 默认接管 direct answer / tool / skill / MCP

当 `use_graph_runtime=True` 时：

- `direct_answer`
- `use_tool`

都会进入 `_run_langgraph(...)`。

例外保留：

- `workflow`
- `tool_call`
- `tool_loop`
- 显式 `graph`

这样这次迭代是“主路径迁移”，不是“一次性重写所有路径”。

### 3. route hint 优先于 graph 内部 heuristics

`integrations/langgraph_workflow.py` 新增：

- `route_hint_action`
- `route_hint_tool_name`
- `route_hint_tool_input`

graph 会先尝试把外层 router 决策翻译成 graph state，再进入 node execution。

好处：

- 保留现有 router 的稳定性
- 不需要一口气重写所有 route heuristics
- 让 top-level router 逐步退化为 thin wrapper，而不是突然删除

### 4. 主 Agent surface 保持兼容

虽然默认运行时已经变成 graph，但 `run.answer` 仍尽量保持旧的用户体验：

- `read_file` 仍返回 `Result: read README.md...`
- direct answer 仍返回原来的 deterministic answer
- 失败时仍尽量走原有 `_compose_tool_error_answer()`

同时，graph metadata 会继续进入：

- `tool_result.metadata`
- `format_trace()`
- `to_trace_dict()`

这意味着：

- 用户看到的表层行为基本兼容
- 学习者仍能从 trace 里看到 graph runtime 已成为主执行器

### 5. classic runtime 作为显式回退

CLI 新增：

```bash
--classic-runtime
```

作用：

- 关闭默认 graph runtime
- 直接使用旧的 if/else 主控

这对学习很重要，因为你可以直接对比：

```bash
python -m cli.main --input "Read README.md..." --trace
python -m cli.main --input "Read README.md..." --classic-runtime --trace
```

## 当前可见行为

### 默认主运行时

```bash
python -m cli.main --input "Explain the difference between an agent and a chatbot." --trace
```

trace 中现在会出现：

```text
Run graph runtime
route=direct_answer
planner=router_wrapped
```

### classic fallback

```bash
python -m cli.main --input "Read README.md and summarize the project learning goals." --classic-runtime --trace
```

trace 中不会出现 `Run graph runtime`，而会继续看到经典的 `Run tool`。

## 设计取舍

### 为什么保留顶层 router

因为这个阶段的重点是“把主执行器迁移到 graph”，而不是“立即废弃一切旧路由逻辑”。

保留顶层 router 有两个价值：

- 继续给 graph 提供稳定 route hint
- 作为 classic runtime fallback 的基础

这让迁移过程更容易学习和回归验证。

### 为什么不把 workflow / tool_call / tool_loop 这次也强行并入 graph

因为那会让本阶段范围过大，学习上也不清晰。

当前先把最常见的：

- direct answer
- regular tool
- skill
- MCP

接成默认 graph 主路径，已经足够构成一次完整迭代。

## 验证命令

建议验证：

```bash
python -m unittest tests.test_agent tests.test_langgraph_workflow -v
python -m unittest discover -s tests -q
python -m cli.main --input "Explain the difference between an agent and a chatbot." --trace
python -m cli.main --input "Read README.md and summarize the project learning goals." --trace
python -m cli.main --input "Read README.md and summarize the project learning goals." --classic-runtime --trace
python -m cli.eval_runner
```

## 当前限制

- `workflow`、`tool_call`、`tool_loop` 仍然保留在 classic 主控分支之外，没有完全 graph 化。
- graph 当前仍依赖外层 router hint 承担一部分决策工作。
- direct answer 仍是 deterministic，本阶段没有把它切成默认 LLM direct answer。

## 下一步建议

下一阶段建议进入：

- graph 内统一多步 orchestration，继续把 workflow / tool loop / tool calling 主路径纳入 LangGraph。

原因：

- v32 已经把 LangGraph 提升为默认主执行器。
- 下一步最自然的演进，是减少剩余的 classic 分支，让 graph 真正成为统一 orchestration runtime。
