# Tool-backed Skills v20

版本：v20  
日期：2026-08-01

## 本次目标

把 v19 的 deterministic skill execution 升级为 tool-backed skill execution。

v19 的执行链路是：

```text
task -> select_skill -> deterministic SkillStepResult -> SkillRun
```

v20 的执行链路是：

```text
task
-> select_skill
-> build executable SkillStep specs
-> call SkillToolRunner for tool-backed steps
-> collect SkillStepResult
-> build SkillRun
```

核心边界：

- `skills/` 包只定义 skill execution 结构和 runner 协议。
- `skills/` 不直接导入 `agent.tools`，避免反向依赖 Agent 主循环。
- `agent/tools.py` 提供 workspace tool runner，把 skill step 映射到现有 tools。
- 失败的 tool step 会让 `SkillRun.status` 变成 `failed`。

## 本次新增能力

1. 新增 `SkillToolRequest`。
2. 新增 `SkillToolResponse`。
3. 新增 `SkillStep`。
4. `SkillStepResult` 增加：
   - `action`
   - `tool_name`
   - `tool_input`
   - `error`
5. `execute_skill()` 支持可选 `tool_runner`。
6. 新增 `build_skill_steps()`，把 `SkillSpec` 转成可执行 step specs。
7. `SkillRun.final_output` 增加 completed / failed / tool-backed step 统计。
8. `agent/tools.py` 新增 workspace skill runner。
9. CLI 新增 `--tool-backed`。
10. 新增 runner 成功、runner 失败、Agent tool-backed、CLI tool-backed 测试。

## 交互流程

### 无 runner 的执行流程

命令：

```bash
python -m cli.collaboration_demo --task "Review this code and add tests." --execute-skill
```

流程：

```text
execute_skill(task)
-> select_skill(task)
-> build_skill_steps(skill, task)
-> planned tool steps produce deterministic observations
-> record-only steps produce deterministic observations
-> SkillRun(status="completed")
```

这个模式用于稳定学习和测试，不调用 workspace tools。

### tool-backed CLI 流程

命令：

```bash
python -m cli.collaboration_demo --task "Review this code and add tests." --execute-skill --tool-backed
```

流程：

```text
cli.collaboration_demo
-> agent.run_skill_with_workspace(Path("."), task)
-> execute_skill(task, tool_runner=workspace_runner)
-> step 1 calls list_dir(".")
-> step 2 calls search_docs(task)
-> step 3 calls search_docs("project tests evaluation workflow")
-> step 4 records final reporting step
-> SkillRun(status="completed")
```

### Agent tool 流程

输入：

```text
Execute skill for code review.
```

流程：

```text
route_intent
-> tool_name=execute_skill
-> WorkspaceAgent._call_tool()
-> run_skill_with_workspace(self.workspace_root, task)
-> execute_skill(task, tool_runner=workspace_runner)
-> ToolResult("execute_skill", SkillRun.to_text())
```

## 代码改动说明

### `skills/execution.py`

新增：

```python
SkillToolRequest
SkillToolResponse
SkillStep
SkillToolRunner
build_skill_steps()
```

`SkillToolRequest` 是 skill step 发出的工具请求：

- `tool_name`
- `tool_input`

`SkillToolResponse` 是 runner 返回的工具结果：

- `tool_name`
- `output`
- `is_error`

`SkillStep` 是可执行步骤定义：

- `index`
- `instruction`
- `action`
- `tool_name`
- `tool_input`

`execute_skill()` 现在支持：

```python
execute_skill(task, tool_runner=None)
```

如果没有 runner：

- tool step 会生成 planned-tool observation。
- 行为仍然 deterministic。

如果有 runner：

- tool step 会真实调用 runner。
- runner 失败时，当前 step 标记为 `failed`。
- `SkillRun.status` 标记为 `failed`。
- 后续步骤停止执行。

### `skills/__init__.py`

新增导出：

- `SkillStep`
- `SkillToolRequest`
- `SkillToolResponse`
- `build_skill_steps`

### `agent/tools.py`

新增：

```python
run_skill_with_workspace(root, task)
_build_skill_tool_runner(root)
```

workspace runner 当前支持：

- `list_dir`
- `read_file`
- `search_docs`
- `list_mcp_tools`
- `mcp_workspace_summary`

如果 skill step 请求不支持的工具，会返回：

```text
Unsupported skill tool
```

并标记为 error。

### `agent/core.py`

`execute_skill` 分支现在调用：

```python
run_skill_with_workspace(self.workspace_root, route.tool_input or "")
```

这样 Agent 执行 skill 时使用当前 workspace root。

### `agent/__init__.py`

新增导出：

- `run_skill_with_workspace`

### `cli/collaboration_demo.py`

新增：

```text
--tool-backed
```

它必须和：

```text
--execute-skill
```

一起使用。

### `tests/test_collaboration.py`

新增测试：

- `test_build_skill_steps_marks_tool_backed_steps`
- `test_execute_skill_uses_tool_runner`
- `test_execute_skill_stops_on_tool_error`
- `test_collaboration_demo_executes_tool_backed_skill`

更新：

- `test_agent_executes_skill` 现在验证输出包含 tool-backed step 统计。

### `agent/README.md`

更新 Skills tools 描述：

```text
execute structured or tool-backed skill runs
```

### `docs/current-learning-state.md`

更新当前阶段到 v20。

## 新增文件与行数

| 文件 | 行数 |
| --- | ---: |
| `versions/tool-backed-skills_v20.md` | 327 |
| `docs/tool-backed-skills-exercises.md` | 121 |

## 本次修改文件与行数

| 文件 | 行数 |
| --- | ---: |
| `skills/execution.py` | 260 |
| `skills/__init__.py` | 26 |
| `agent/tools.py` | 192 |
| `agent/core.py` | 636 |
| `agent/__init__.py` | 69 |
| `cli/collaboration_demo.py` | 60 |
| `tests/test_collaboration.py` | 198 |
| `agent/README.md` | 58 |
| `docs/current-learning-state.md` | 253 |

## 验证命令

定向测试：

```bash
python -m unittest tests.test_collaboration -v
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
python -m cli.collaboration_demo --task "Review this code and add tests." --execute-skill --tool-backed
```

Agent demo：

```bash
python -m cli.main --input "Execute skill for code review." --trace
```

## 本阶段学习重点

1. `SkillStep` 是“计划步骤”，`SkillStepResult` 是“执行结果”。
2. `SkillToolRequest` / `SkillToolResponse` 是 Skills 和工具层之间的协议边界。
3. `skills/` 不应该直接依赖 `agent/`。
4. Agent 可以提供 runner，把 skill step 映射到现有 workspace tools。
5. tool-backed execution 必须处理工具失败。
6. `SkillRun.status` 应该由 step results 决定。
7. CLI 需要同时支持 deterministic 模式和 tool-backed 模式。

## 下一阶段建议

下一阶段可以进入 “Skill execution trace / JSON export”：

- 为 `SkillRun` 增加 `to_dict()`。
- 让 Agent structured trace 包含 skill run 摘要。
- 增加 eval case 覆盖 `execute_skill`。
- 为 tool-backed skill steps 记录 tool input / output / error metadata。
- 为后续 LangGraph skill node 做准备。
