# v34：tool_call 并入默认 LangGraph orchestration

## 本阶段目标

在 v33 已经把 `workflow` 并入默认 LangGraph 主执行器之后，继续把 `tool_call` 主路径纳入 graph runtime，让 LLM 工具选择也从顶层 classic if/else 分支迁移到 graph 内部状态与条件边。

本阶段形成的新闭环是：

```text
user input
-> top-level route_intent()
-> tool_call route hint
-> LangGraph select_tool_call
-> use_tool / answer_directly / ask_clarification / call_skill
-> classic Agent surface answer + graph metadata
```

## 本阶段新增文件

| 文件 | 作用 |
|---|---|
| `versions/graph-tool-call-orchestration_v34.md` | 本阶段版本说明 |
| `docs/graph-tool-call-orchestration-exercises_v34.md` | 本阶段练习 |

## 本阶段修改文件

| 文件 | 主要变化 |
|---|---|
| `integrations/langgraph_workflow.py` | graph 新增 `tool_call` 选择节点与条件分流状态 |
| `agent/core.py` | `tool_call` 默认走 graph runtime，并保留 classic fallback |
| `tests/test_tool_calling.py` | 增加默认 graph runtime 和 classic opt-out 测试 |
| `tests/test_langgraph_workflow.py` | 增加 graph 内 tool_call 三类结果测试 |
| `tests/test_agent.py` | 增加默认 tool_call graph 路径测试 |
| `cli/README.md` | 增加 tool_call 默认 graph 与 classic runtime 对照命令 |
| `docs/current-learning-state.md` | 更新当前阶段与下一步建议 |

## 核心实现说明

### 1. 顶层 `tool_call` 路由仍保留，但默认不再由 classic 分支直接执行

`route_intent()` 仍然返回：

```text
action = tool_call
tool_name = llm_tool_selector
```

但 `WorkspaceAgent.run()` 默认不再直接做：

- 选择工具
- 执行工具
- 直接回答
- 追问澄清

这些职责现在转移给 LangGraph 内部节点和条件边。只有显式 `--classic-runtime` 时，才退回旧的 `_run_classic_tool_call()`。

### 2. graph 内新增 `select_tool_call` 节点

本阶段新增核心节点：

- `select_tool_call`

它负责：

- 调用 LLM 做结构化工具选择
- 记录 `tool_call_selection`
- 写入 `tool_call_status`
- 决定后续是执行普通 tool、执行 skill，还是直接 finalize

### 3. tool_call 结果进入结构化 graph state

graph state 新增：

- `tool_call_selection`
- `tool_call_status`
- `tool_call_error`

这样 `tool_call` 就不再只是 `AgentRun.tool_call` 上的一份临时对象，而成为 graph 内部的一等状态，能够进入：

- trace
- metadata
- structured export
- 后续恢复路径

### 4. tool_call 在 graph 内有明确条件分流

`select_tool_call` 的输出现在分成四类：

- `use_tool` -> `call_tool`
- `use_tool` 且选中 `execute_skill` -> `call_skill`
- `answer_directly` -> `finalize`
- `ask_clarification` -> `finalize`

如果 LLM 选择阶段本身失败，则：

- 生成异常恢复计划
- 输出结构化失败答案
- 直接 `finalize`

### 5. classic Agent surface 继续兼容

虽然 `tool_call` 默认已经 graph 化，但外层 `AgentRun` 仍尽量保持原有表面行为：

- `run.tool_call` 仍可读
- `selected_tool_name` 仍可用于 eval/test
- 选中 `read_file` 时，回答仍保持 `Result: read README.md...`
- 直接回答时仍保持原来的 deterministic direct answer 风格
- 要求澄清时仍保持原有 clarification answer 风格

也就是说：

- 内部 orchestration 迁移到了 graph
- 外层学习接口和现有测试表面基本兼容

## 当前可见行为

### 默认 tool_call graph runtime

```bash
python -m cli.main --input "Use tool calling to read README.md." --trace
```

trace 中现在会出现：

```text
Run tool-call graph
route=tool_call_execution
steps=route -> select_tool_call -> call_tool -> finalize
```

### classic tool_call fallback

```bash
python -m cli.main --input "Use tool calling to read README.md." --classic-runtime --trace
```

trace 中会重新看到：

```text
Select tool
Run tool
```

## 设计取舍

### 为什么 v34 先 graph 化 `tool_call`

因为它正好位于：

- 单步 graph runtime
- 多步 `tool_loop`

之间，是最自然的过渡层。

它比 `workflow` 更接近真实 LLM 决策；又比 `tool_loop` 少了多轮 observation 和停止条件复杂度，因此非常适合作为 `tool_loop` graph 化之前的中间阶段。

### 为什么没有顺手做 `tool_loop`

因为 `tool_loop` 还需要额外管理：

- 多轮 selection
- observations
- repeated tool call guard
- max step
- final synthesis

如果和 `tool_call` 一起并入，本阶段范围会明显失控，不利于学习和回归。

## 验证命令

建议验证：

```bash
python -m unittest tests.test_tool_calling tests.test_langgraph_workflow tests.test_agent -v
python -m unittest discover -s tests -q
python -m cli.main --input "Use tool calling to read README.md." --trace
python -m cli.main --input "Use tool calling to explain the difference between an agent and a chatbot." --trace
python -m cli.main --input "Use tool calling to read README.md." --classic-runtime --trace
python -m cli.eval_runner
```

## 当前限制

- `tool_loop` 还没有并入统一 graph 主执行器。
- tool_call 选择失败当前走的是异常恢复计划，还没有更细的 tool-calling-specific failure taxonomy。
- direct answer 仍然是 deterministic direct answer，不是默认 LLM direct answer。

## 下一步建议

下一阶段建议优先推进：

- `tool_loop` graph 化

原因：

- `use_tool`
- `workflow`
- `tool_call`

都已经并入默认 LangGraph 主执行器，剩下最明显的大块 classic orchestration 就是 `tool_loop`。
