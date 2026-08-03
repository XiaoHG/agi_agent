# v25：统一 Agent 运行事件与恢复模型

## 本阶段目标

本阶段从“分别处理 LangGraph tool failure / skill failure”推进到“统一的 Agent 运行事件与恢复模型”。

核心目标：

1. 把普通 tool、Skill、graph exception 的失败恢复统一成同一种 `RecoveryPlan` 数据结构。
2. 把 Agent 执行过程转换成统一的 `RuntimeEvent`，为后续观测、恢复、checkpoint 和审计做基础。
3. 让 `WorkspaceAgent.format_trace()` 和 `WorkspaceAgent.to_trace_dict()` 同时暴露 runtime events。
4. 保持 LangGraph state 仍然使用 JSON-ready dict，避免 graph state 中混入不可序列化对象。

## 新增代码文件

### `agent/recovery.py`

新增 248 行。

关键新增内容：

- 第 9-24 行：新增 `RecoveryPlan` 数据模型，统一描述失败状态、失败分类、失败来源、失败原因和下一步安全动作。
- 第 26-42 行：新增 `to_dict()`，把恢复计划转换成 JSON-ready trace 数据。
- 第 44-71 行：新增 `to_text()`，把恢复计划转换成人类可读输出。
- 第 74-87 行：新增 `build_tool_recovery_plan()`，为普通 LangChain tool 失败生成恢复计划。
- 第 90-121 行：新增 `build_skill_recovery_plan()`，从 `SkillRun` trace 中提取失败步骤上下文。
- 第 124-134 行：新增 `build_exception_recovery_plan()`，处理 graph 或 skill 执行过程中尚未形成结构化 run 的异常。
- 第 137-149 行：新增 `classify_failure()`，把错误原因归类为 `missing_resource`、`unsafe_or_denied_access`、`external_dependency`、`input_too_large` 或 `execution_error`。
- 第 152-185 行：新增 skill trace 解析辅助函数，用于找出失败 step、skill name 和失败原因。
- 第 188-248 行：新增恢复动作生成与防御性数据转换 helper。

### `agent/events.py`

新增 103 行。

关键新增内容：

- 第 9-17 行：新增 `RuntimeEvent` 数据模型，统一描述 Agent 运行过程中的事件。
- 第 19-28 行：新增 `to_dict()`，导出结构化事件。
- 第 30-34 行：新增 `to_text()`，导出紧凑的人类可读事件。
- 第 37-103 行：新增 `build_runtime_events()`，从已有 `AgentStep`、LangGraph metadata、recovery plan、skill run 和 tool error 中构造统一事件流。

### `tests/test_recovery.py`

新增 94 行。

覆盖内容：

- tool recovery plan 的 dict / text 导出。
- skill recovery plan 对失败 step 的上下文提取。
- exception recovery plan 的来源标记。
- 常见 failure reason 到 `failure_type` 的映射。
- `RecoveryPlan` 对可选上下文字段的兼容。

### `tests/test_events.py`

新增 67 行。

覆盖内容：

- `RuntimeEvent` 的 dict / text 导出。
- 从普通 `AgentStep` 构造 runtime events。
- 从 LangGraph metadata 构造 graph / recovery events。
- 从 skill run 和 tool error 构造 skill / error events。

## 修改代码文件

### `integrations/langgraph_workflow.py`

关键修改：

- 第 10-14 行：引入 `agent.recovery` 中的统一恢复计划构造函数。
- 第 20-36 行：`RAGGraphState` 继续保留 `recovery_plan: dict[str, Any]`，保证 graph state 可序列化。
- 第 129-135 行：`call_skill()` 异常路径改为使用 `build_exception_recovery_plan(...).to_dict()`。
- 第 138-151 行：`recover_skill_failure()` 改为使用统一 `build_skill_recovery_plan()`。
- 第 153-168 行：`recover_tool_failure()` 改为使用统一 `build_tool_recovery_plan()`。
- 第 205-213 行：普通 tool 失败后进入 `recover_tool_failure` 节点。
- 第 214-222 行：skill 失败后进入 `recover_skill_failure` 节点。

本文件删除了之前局部定义的 tool recovery / skill recovery helper，避免恢复逻辑分散在 graph 文件内部。

### `agent/core.py`

关键修改：

- 第 15 行：引入 `build_runtime_events()`。
- 第 619-626 行：`format_trace()` 新增 `[Runtime Events]` 区块。
- 第 635-664 行：`to_trace_dict()` 新增 `runtime_events` 字段。

这让 CLI 文本 trace 和结构化 trace 都能看到同一套运行事件。

### `agent/__init__.py`

关键修改：

- 第 4 行：导出 `RuntimeEvent` 和 `build_runtime_events`。
- 第 6-12 行：导出 `RecoveryPlan` 和 recovery builder。
- 第 47-64 行：把新增模型和函数加入 `__all__`。

### `tests/test_langgraph_workflow.py`

关键修改：

- 补充断言：tool recovery / skill recovery 的 `recovery_plan` 必须包含 `source_type` 和 `source_name`。

### `tests/test_agent.py`

关键修改：

- 补充断言：`format_trace()` 必须输出 `[Runtime Events]`。
- 补充断言：`to_trace_dict()` 必须包含 `runtime_events`。
- 补充断言：LangGraph recovery metadata 能被转换成 runtime recovery event。

## 新增功能说明

### 1. 统一恢复模型

之前普通 tool failure 和 skill failure 的恢复逻辑分别写在 LangGraph workflow 内部。这样短期能工作，但后续会出现三个问题：

1. 恢复字段不稳定，不同失败路径输出结构可能不一致。
2. 新增 MCP、RAG、LLM、Skills failure 时容易复制 helper。
3. 后续 checkpoint、人工审批、自动重试都缺少统一输入。

v25 通过 `RecoveryPlan` 把失败恢复抽成统一对象。

核心字段：

- `status`：当前恢复计划状态。
- `failure_type`：标准失败类型。
- `source_type`：失败来自 tool、skill 还是 exception。
- `source_name`：失败来源名称。
- `reason`：原始失败原因。
- `next_safe_action`：下一步安全动作建议。
- `tool_name` / `tool_input`：普通工具或 Skill step 的工具上下文。
- `skill_name` / `failed_step` / `completed_steps`：Skill 失败上下文。
- `metadata`：预留扩展字段。

### 2. 统一运行事件

之前 `AgentRun.steps`、`tool_result.metadata`、`tool_error` 都是分散信息。人可以读 trace，但程序后续很难稳定消费。

v25 通过 `RuntimeEvent` 把这些信息转换成统一事件流：

- `step`：普通 AgentStep。
- `graph`：LangGraph route 和 graph steps。
- `recovery`：结构化恢复计划。
- `skill`：SkillRun trace。
- `error`：tool error。

这一步不是为了替代原有 trace，而是给后续专业 Agent 能力打基础：

- runtime observability
- checkpoint / replay
- recovery policy
- human approval
- eval evidence
- long-running agent audit

### 3. LangGraph state 仍然保存 dict

`RecoveryPlan` 是 Python dataclass，但 `RAGGraphState["recovery_plan"]` 仍然保存 `dict`。

原因：

1. LangGraph state 后续可能需要持久化、checkpoint 或跨进程传输。
2. JSON-ready dict 更适合作为 state 边界。
3. dataclass 只在构造恢复计划时使用，进入 graph state 前调用 `to_dict()`。

## 交互流程

### 普通 tool 成功路径

```text
route
  -> call_tool
  -> finalize
```

状态变化：

1. `route` 选择 `selected_tool` 和 `tool_input`。
2. `call_tool` 执行 LangChain tool。
3. 成功时写入 `tool_output` 和 `tool_status="completed"`。
4. `finalize` 把 `tool_output` 转换成最终答案。

### 普通 tool 失败恢复路径

```text
route
  -> call_tool
  -> recover_tool_failure
  -> finalize
```

状态变化：

1. `call_tool` 捕获异常。
2. 写入 `tool_error`、`tool_status="failed"`。
3. `_next_after_tool()` 根据 `tool_status` 进入 `recover_tool_failure`。
4. `recover_tool_failure()` 生成 `RecoveryPlan`。
5. `recovery_plan` 以 dict 形式进入 graph state。
6. `tool_output` 变成恢复计划文本。
7. `finalize` 输出恢复计划。

### Skill 失败恢复路径

```text
route
  -> call_skill
  -> recover_skill_failure
  -> finalize
```

状态变化：

1. `call_skill` 执行 project skill。
2. 如果 `SkillRun.status == failed`，graph 写入 `skill_status="failed"`。
3. `_next_after_skill()` 进入 `recover_skill_failure`。
4. `recover_skill_failure()` 从 `skill_run.steps` 中提取失败 step。
5. 生成包含 `skill_name`、`failed_step`、`completed_steps` 的 `RecoveryPlan`。

### Agent trace 导出路径

```text
WorkspaceAgent.run()
  -> ToolResult.metadata
  -> build_runtime_events()
  -> format_trace() / to_trace_dict()
```

结果：

- CLI trace 会出现 `[Runtime Events]`。
- 结构化 trace 会出现 `runtime_events` 数组。

## 本阶段验证命令

```bash
python -m unittest tests.test_recovery tests.test_events tests.test_langgraph_workflow tests.test_agent -v
```

用途：验证本阶段直接相关的 recovery、runtime events、LangGraph workflow、WorkspaceAgent trace。

```bash
python -m unittest discover -s tests -v
```

用途：运行整个项目测试，确认 v25 没有破坏历史能力。

```bash
python -m cli.eval_runner
```

用途：运行 regression eval，确认 Agent 行为仍符合可回归预期。

```bash
python -m cli.main --input "Use LangGraph to read not-exist.md." --trace
```

用途：手动观察普通 tool failure 是否进入 recovery path，并在 trace 中看到 `[Runtime Events]`。

```bash
python -m cli.main --input "Use LangGraph to execute skill for learning explanation." --trace
```

用途：手动观察 Skill execution path 是否仍能输出 graph metadata 和 runtime events。

## 已验证结果

已运行：

```bash
python -m unittest discover -s tests -v
```

结果：121 个测试全部通过。

已运行：

```bash
python -m cli.eval_runner
```

结果：17 个 eval case 全部通过。

## 本阶段学习重点

学习时重点看四件事：

1. 为什么 recovery plan 要从 LangGraph 文件中抽出来。
2. 为什么 graph state 里保存 dict，而不是保存 dataclass。
3. `RuntimeEvent` 如何把分散 trace 变成统一事件流。
4. 测试为什么不仅检查最终答案，也检查结构化 metadata 和 trace。

## 下一阶段建议

下一阶段可以进入：

`v26：LangGraph Checkpoint and Recoverable Run Persistence`

建议目标：

1. 给 LangGraph run 引入可恢复的 run id。
2. 把 graph state / runtime events 写入本地 checkpoint 文件。
3. 提供 CLI 命令查看最近一次 graph run。
4. 为 checkpoint 写测试和 eval。

原因：v25 已经有统一事件和恢复模型，下一步应该让这些信息从“单次内存对象”升级为“可持久化、可恢复的运行记录”。
