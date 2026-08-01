# Skills Execution v19

版本：v19  
日期：2026-08-01

## 本次目标

把 Skills 从“可描述、可选择、可规划”升级为“可执行、可测试、可追踪”的结构化能力。

v18 已经完成：

```text
MCP / Skills tools -> tool schema -> LLM tool selection -> tool loop observations -> LLM final synthesis
```

v19 继续推进 Skills：

```text
task -> select skill -> execute skill steps -> SkillRun -> ToolResult -> Agent answer / trace
```

核心边界：

- 当前执行是 deterministic execution，不调用真实外部资源。
- 本阶段先建立执行记录、步骤状态、最终输出和测试边界。
- 后续再把每个 skill step 接入真实 tool runner、MCP、RAG 或 subagent。

## 本次新增能力

1. 新增 `skills/execution.py`。
2. 新增 `SkillStepResult`，记录 skill 内单步执行结果。
3. 新增 `SkillRun`，记录完整 skill execution。
4. 新增 `execute_skill(task)`，根据 task 选择并执行内置 skill。
5. Agent 工具层新增 `run_skill()`。
6. tool schema 新增 `execute_skill`。
7. router 可识别 `Execute skill ...` 请求。
8. CLI 新增 `--execute-skill`。
9. 测试覆盖 skill execution、Agent tool、CLI 和 tool schema。

## 交互流程

### CLI 执行流程

命令：

```bash
python -m cli.collaboration_demo --task "Review this code and add tests." --execute-skill
```

流程：

```text
cli.collaboration_demo
-> execute_skill(task)
-> select_skill(task)
-> build SkillStepResult for each skill step
-> build SkillRun
-> SkillRun.to_text()
-> print output
```

### Agent 执行流程

输入：

```text
Execute skill for code review.
```

流程：

```text
route_intent
-> action=use_tool
-> tool_name=execute_skill
-> WorkspaceAgent._call_tool()
-> run_skill(task)
-> execute_skill(task)
-> SkillRun.to_text()
-> ToolResult("execute_skill", output)
-> Agent answer
```

### LLM tool calling 流程

如果用户通过 tool calling 让模型选择工具：

```text
Use tool calling to execute the best skill for code review.
```

模型可以从 tool schema 中选择：

```text
execute_skill(task)
```

随后代码会把它当作 task-input tool 处理。

## 代码改动说明

### `skills/execution.py`

新增核心数据结构：

```python
SkillStepResult
SkillRun
execute_skill()
```

`SkillStepResult` 表示 skill 的一个步骤执行结果，包括：

- `index`
- `instruction`
- `status`
- `observation`

`SkillRun` 表示一次完整 skill 执行，包括：

- `task`
- `skill`
- `status`
- `steps`
- `final_output`

`execute_skill(task)` 当前执行逻辑：

```text
select_skill(task)
-> for each skill.steps build SkillStepResult
-> build SkillRun(status="completed")
```

### `skills/__init__.py`

导出：

- `SkillRun`
- `SkillStepResult`
- `execute_skill`

### `agent/tools.py`

新增：

```python
run_skill(task: str) -> ToolResult
```

职责：

- 调用 `skills.execute_skill(task)`。
- 把 `SkillRun.to_text()` 包装成统一 `ToolResult`。

### `agent/core.py`

新增：

- 导入 `run_skill`
- `_call_tool()` 分发 `execute_skill`

职责：

- 让 `WorkspaceAgent` 可以执行 skill run。

### `agent/tool_schema.py`

新增 tool spec：

```text
execute_skill
```

参数：

```text
task: Task description.
```

职责：

- 让 LLM 能选择“执行 skill”，而不只是“规划 skill”。

### `agent/tool_calling.py`

更新：

- `_TASK_INPUT_TOOLS` 新增 `execute_skill`

原因：

- skill execution 需要完整任务上下文。
- 不能像 path-input tool 一样只提取文件路径。

### `agent/router.py`

新增：

- `_looks_like_skill_execution_request()`

规则：

- `execute skill`
- `run skill`
- `use skill`
- `perform skill`
- `skill execution`

命中后路由到：

```text
tool_name=execute_skill
```

### `cli/collaboration_demo.py`

新增：

```text
--execute-skill
```

当用户同时传入 `--task` 和 `--execute-skill` 时，CLI 会输出 `SkillRun.to_text()`。

### `tests/test_collaboration.py`

新增测试：

- `test_execute_skill_returns_structured_run`
- `test_route_to_execute_skill`
- `test_agent_executes_skill`
- `test_collaboration_demo_executes_skill`

### `tests/test_tool_calling.py`

新增测试：

- `test_tool_schema_exposes_skill_execution`

### `agent/__init__.py`

新增导出：

- `run_skill`
- `mcp_read_project_file`

其中 `mcp_read_project_file` 是 v18 工具，本次补齐包导出一致性。

## 新增文件与行数

| 文件 | 行数 |
| --- | ---: |
| `skills/execution.py` | 89 |
| `versions/skills-execution_v19.md` | 324 |
| `docs/skills-execution-exercises.md` | 125 |

## 本次修改文件与行数

| 文件 | 行数 |
| --- | ---: |
| `skills/__init__.py` | 14 |
| `agent/tools.py` | 161 |
| `agent/core.py` | 636 |
| `agent/__init__.py` | 67 |
| `agent/tool_schema.py` | 106 |
| `agent/tool_calling.py` | 217 |
| `agent/router.py` | 452 |
| `cli/collaboration_demo.py` | 53 |
| `tests/test_collaboration.py` | 138 |
| `tests/test_tool_calling.py` | 121 |
| `agent/README.md` | 58 |
| `docs/current-learning-state.md` | 242 |

## 验证命令

定向测试：

```bash
python -m unittest tests.test_collaboration tests.test_tool_calling -v
```

全量测试：

```bash
python -m unittest discover -s tests -v
```

回归评估：

```bash
python -m cli.eval_runner
```

CLI demo：

```bash
python -m cli.collaboration_demo --task "Review this code and add tests." --execute-skill
```

Agent demo：

```bash
python -m cli.main --input "Execute skill for code review." --trace
```

## 本阶段学习重点

1. `select_skill` 和 `execute_skill` 是两层不同能力。
2. `SkillRun` 是 skill execution 的核心状态对象。
3. `SkillStepResult` 让每一步执行结果可追踪。
4. Agent tool 不应该直接返回任意文本，而应该从结构化 run 渲染输出。
5. 当前 deterministic execution 是为了先建立工程边界。
6. 后续真实 skill runner 应该替换 step observation 生成逻辑，而不是重写 Agent 主循环。

## 下一阶段建议

下一阶段可以进入 “Skill runner 接入 tool layer”：

- 给 `SkillStep` 增加 action 类型。
- 允许 skill step 调用本地 tools、RAG、MCP 或 subagent。
- 给 `SkillRun` 增加失败状态。
- 增加 step-level error handling。
- 让 tool loop 可以调用 `execute_skill` 并把 skill run 结果用于 final synthesis。
