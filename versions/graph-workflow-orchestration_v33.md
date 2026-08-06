# v33：workflow 并入默认 LangGraph orchestration

## 本阶段目标

在 v32 已经让 LangGraph 成为默认主执行器的基础上，继续把多步 `workflow` 主路径纳入 graph runtime，减少 `WorkspaceAgent` 顶层经典 if/else 对多步流程的直接控制。

本阶段形成的新闭环是：

```text
user input
-> top-level route_intent()
-> workflow route hint
-> LangGraph build_workflow
-> LangGraph run_workflow_step loop
-> LangGraph finalize_workflow
-> classic Agent surface answer + graph metadata
```

## 本阶段新增文件

| 文件 | 作用 |
|---|---|
| `versions/graph-workflow-orchestration_v33.md` | 本阶段版本说明 |
| `docs/graph-workflow-orchestration-exercises_v33.md` | 本阶段练习 |

## 本阶段修改文件

| 文件 | 主要变化 |
|---|---|
| `integrations/langgraph_workflow.py` | graph 新增 workflow plan/build/step/finalize 状态与节点 |
| `agent/workflow.py` | `WorkflowPlan` 增加 `to_dict()`，新增脱离 `AgentState` 的 workflow summary helper |
| `agent/core.py` | `workflow` 默认走 graph runtime，并保留 classic workflow fallback |
| `tests/test_langgraph_workflow.py` | 增加 graph 内 workflow 成功/失败路径测试 |
| `tests/test_agent.py` | 增加 workflow 默认 graph 和 classic opt-out 测试 |
| `cli/README.md` | 增加 workflow 默认 graph 与 classic runtime 对照命令 |
| `docs/current-learning-state.md` | 更新当前阶段与下一步建议 |

## 核心实现说明

### 1. 顶层 `workflow` 路由仍保留，但执行权转移给 graph

`route_intent()` 仍然返回：

```text
action = workflow
```

但 `WorkspaceAgent.run()` 不再直接把多步流程交给经典 `_run_workflow()`。

默认情况下它会把 `workflow` 作为 route hint 传给 LangGraph，再由 graph 内部去做：

- plan 构建
- step 执行
- 失败停止
- 最终汇总

只有显式关闭默认 graph runtime 时，才退回 classic workflow executor。

### 2. graph 内新增 workflow 专用节点

本阶段新增节点：

- `build_workflow`
- `run_workflow_step`
- `finalize_workflow`

这样 graph 不再只会做单步 tool / skill routing，也开始承担真正的多步 orchestration。

### 3. workflow plan 改成 JSON-ready graph state

`WorkflowPlan` 新增 `to_dict()`，graph state 新增：

- `workflow_plan`
- `workflow_results`
- `workflow_summary`
- `workflow_current_step`
- `workflow_status`
- `workflow_error`

原因很直接：

- graph state 应优先保存 JSON-ready 数据
- 这样更利于 checkpoint、trace、后续 replay 和持久化

### 4. workflow step 在 graph 内循环推进

`run_workflow_step` 每次只处理一个 step：

- tool step：执行一个 workspace tool，并记录结果
- synthesize step：写入 `workflow_summary`
- 失败：立刻停止后续 step，并生成 recovery plan

条件边根据：

- 当前 step 下标
- `workflow_status`

决定是继续下一步，还是进入 `finalize_workflow`。

### 5. workflow 失败保持“workflow surface”，不泄漏底层执行细节

虽然 graph 内部失败点可能是：

- `read_workspace_file`
- `count_workspace_file_lines`

但外层 `AgentRun` 现在会统一暴露：

- `tool_result.tool_name = workflow`

这样对学习更清晰：

- 顶层能力是 workflow
- 底层失败工具和 recovery plan 仍保留在 metadata / trace 中

## 当前可见行为

### 默认 workflow graph runtime

```bash
python -m cli.main --input "Read README.md and then count lines." --trace
```

trace 中现在会出现：

```text
Run workflow graph
route=workflow_execution
steps=route -> build_workflow -> run_workflow_step -> ...
```

### classic workflow fallback

```bash
python -m cli.main --input "Read README.md and then count lines." --classic-runtime --trace
```

trace 中会重新看到：

```text
Build workflow
Start workflow
Workflow step
```

## 设计取舍

### 为什么这次先 graph 化 `workflow`

因为它是最自然的多步 orchestration 入口：

- 已经有显式 plan
- 已经有明确 step 顺序
- 已经有成功/失败停止语义

比起 `tool_loop`，它的状态更简单；比起 `tool_call`，它更直接体现 graph 对多步任务的价值。

### 为什么还保留 classic workflow

因为当前阶段重点是：

- 让 graph 统一接管多步流程
- 同时保留一个可对照、可回退的经典执行器

这对学习很重要。你可以直接比较两条 trace，看到“同一需求，graph 和 classic 如何组织多步执行”。

## 验证命令

建议验证：

```bash
python -m unittest tests.test_agent tests.test_langgraph_workflow -v
python -m unittest discover -s tests -q
python -m cli.main --input "Read README.md and then count lines." --trace
python -m cli.main --input "Read not-exist.md and then count lines." --trace
python -m cli.main --input "Read README.md and then count lines." --classic-runtime --trace
python -m cli.eval_runner
```

## 当前限制

- `tool_call` 还没有并入统一 graph 主执行器。
- `tool_loop` 还没有并入统一 graph 主执行器。
- workflow plan 仍然是 deterministic rule-based planner，不是 LLM workflow planner。

## 下一步建议

下一阶段建议优先推进：

- `tool_call` graph 化

然后再进入：

- `tool_loop` graph 化

原因：

- `tool_call` 仍然是单次选择，复杂度低于 `tool_loop`
- `tool_loop` 需要多轮 observation、停止条件和 final synthesis，应该最后并入
