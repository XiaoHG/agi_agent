# v35：tool_loop 并入默认 LangGraph orchestration

## 本阶段目标

在 v34 已经把 `tool_call` 并入默认 LangGraph 主执行器之后，继续把 `tool_loop` 主路径纳入 graph runtime，让 bounded multi-step tool orchestration 也从顶层 classic while/for 分支迁移到 graph 内部状态与条件边。

本阶段形成的新闭环是：

```text
user input
-> top-level route_intent()
-> tool_loop route hint
-> LangGraph initialize_tool_loop
-> LangGraph run_tool_loop_iteration loop
-> LangGraph synthesize_tool_loop
-> LangGraph finalize_tool_loop
-> classic Agent surface answer + structured tool-loop trace
```

## 本阶段新增文件

| 文件 | 作用 |
|---|---|
| `versions/graph-tool-loop-orchestration_v35.md` | 本阶段版本说明 |
| `docs/graph-tool-loop-orchestration-exercises_v35.md` | 本阶段练习 |

## 本阶段修改文件

| 文件 | 主要变化 |
|---|---|
| `integrations/langgraph_workflow.py` | graph 新增 `tool_loop` 初始化、迭代、综合与收尾节点 |
| `agent/tool_loop.py` | `ToolLoopStep` / `ToolLoopResult` 新增 JSON-ready 序列化能力 |
| `agent/core.py` | `tool_loop` 默认走 graph runtime，并保留 classic fallback |
| `tests/test_tool_loop.py` | 增加默认 graph runtime 和 classic opt-out 测试 |
| `tests/test_langgraph_workflow.py` | 增加 graph 内 tool_loop 成功、重复调用、synthesis fallback 测试 |
| `tests/test_agent.py` | 增加默认 tool_loop graph 路径测试 |
| `cli/README.md` | 增加 tool_loop 默认 graph 与 classic runtime 对照命令 |
| `docs/current-learning-state.md` | 更新当前阶段与下一步建议 |

## 核心实现说明

### 1. 顶层 `tool_loop` 路由仍保留，但默认不再由 classic 分支直接驱动循环

`route_intent()` 仍然返回：

```text
action = tool_loop
tool_name = llm_tool_loop
```

但 `WorkspaceAgent.run()` 默认不再直接在顶层 Python 里做：

- 构造 loop input
- 多轮调用 LLM 选工具
- 维护 observations
- 维护 repeated tool call guard
- 维护 max step
- 调 final synthesis

这些职责现在迁移到了 LangGraph 内部状态与条件边。只有显式 `--classic-runtime` 时，才退回旧的 `_run_classic_tool_loop()`。

### 2. graph 内新增 `tool_loop` 专用节点

本阶段新增核心节点：

- `initialize_tool_loop`
- `run_tool_loop_iteration`
- `synthesize_tool_loop`
- `finalize_tool_loop`

这样 `tool_loop` 不再只是 classic executor 里的一个局部循环，而成为 graph 内部的一等 orchestration 路径。

### 3. tool_loop 关键状态进入 graph state

graph state 新增：

- `tool_loop_steps`
- `tool_loop_observations`
- `tool_loop_seen_calls`
- `tool_loop_stop_reason`
- `tool_loop_final_answer`
- `tool_loop_final_answer_source`
- `tool_loop_status`
- `tool_loop_error`
- `tool_loop_current_step`
- `tool_loop_max_steps`
- `tool_loop_result`

这些字段把 classic 里分散在局部变量里的 loop 运行事实，提升成了 graph 内可观察、可测试、可持久化的结构化状态。

### 4. 一次 iteration 同时负责选择、执行和停止条件判断

`run_tool_loop_iteration` 每次会完成一整轮 loop：

- 基于 objective + observations 构造下一轮输入
- 调用 `select_tool_call()`
- 处理 `answer_directly`
- 处理 `ask_clarification`
- 处理 repeated tool call
- 执行普通 tool 或 `execute_skill`
- 记录 observation
- 判断是否达到 max step

它的结果再通过条件边决定：

- 继续下一轮 iteration
- 进入 final synthesis
- 或在选择阶段异常时直接 finalize

### 5. final synthesis 也迁移到 graph

classic `tool_loop` 的最后一步不是直接返回 deterministic answer，而是：

- 先构造 deterministic result
- 再尝试让 LLM 基于 observations 做 final synthesis
- 如果 synthesis 失败，回退到 deterministic fallback

现在这条逻辑已经迁移到 `synthesize_tool_loop` 节点，并把：

- `final_answer_source = llm`
- `final_answer_source = deterministic_fallback`

都明确写回 graph state。

### 6. classic Agent surface 继续兼容

虽然 `tool_loop` 默认已经 graph 化，但外层 `AgentRun` 仍尽量保持原有表面行为：

- `run.tool_loop_result` 仍可读
- `run.tool_call` 仍指向最后一轮 selection
- `run.answer` 仍是 `ToolLoopResult.to_text()` 的表面格式
- classic fallback 仍可通过 `--classic-runtime` 对照

所以这次重点仍然是 orchestration ownership 迁移，而不是重做用户表层输出。

## 当前可见行为

### 默认 tool_loop graph runtime

```bash
python -m cli.main --input "Use tool loop to read README.md and then answer." --trace
```

trace 中现在会出现：

```text
Run tool-loop graph
route=tool_loop_execution
steps=route -> initialize_tool_loop -> run_tool_loop_iteration -> ...
```

### classic tool_loop fallback

```bash
python -m cli.main --input "Use tool loop to read README.md and then answer." --classic-runtime --trace
```

trace 中会重新看到：

```text
Run tool loop
```

以及 classic loop surface。

## 设计取舍

### 为什么 v35 必须单独做 `tool_loop`

因为 `tool_loop` 是 graph 化前最后一个明显的大 classic orchestration 分支，而且它的复杂度也最高，单独成阶段更利于学习和回归：

- 多轮 selection
- observations
- repeated tool call guard
- max step
- final synthesis

如果把它和前面阶段混在一起，学习上会看不清“graph 究竟吞掉了什么执行职责”。

### 为什么 iteration 采用“一轮全做完”的节点

因为当前阶段的重点是先让 `tool_loop` 主路径进入统一 graph runtime，而不是先把 loop 再拆成很多微节点。

这一设计有两个现实价值：

- 范围可控，迁移更稳
- 保留了后续继续把 iteration 再细拆成 `select -> execute -> observe -> branch` 的空间

## 验证命令

建议验证：

```bash
python -m unittest tests.test_tool_loop tests.test_langgraph_workflow tests.test_agent -v
python -m unittest discover -s tests -q
python -m cli.main --input "Use tool loop to read README.md and then answer." --trace
python -m cli.main --input "Use tool loop to read README.md and then answer." --classic-runtime --trace
python -m cli.eval_runner
```

## 当前限制

- tool_loop iteration 当前还是“一轮大节点”，还没有细拆成更原子化的 graph node。
- tool_loop 失败恢复目前主要是工具失败的 recovery plan，尚未形成更细的 loop-specific failure taxonomy。
- direct answer 仍然是 deterministic direct answer，不是默认 LLM direct answer。

## 下一步建议

下一阶段建议优先转向：

- replay / checkpoint / recovery / observability 深化

原因：

- `use_tool`
- `workflow`
- `tool_call`
- `tool_loop`

都已经并入默认 LangGraph 主执行器。接下来继续做“再吞一个 classic 分支”的收益明显下降，更值得转向统一运行时的可恢复、可回放、可审计能力深化。
