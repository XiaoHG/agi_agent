# Skill Trace Export v21

版本：v21  
日期：2026-08-02

## 本次目标

把 v20 的 tool-backed SkillRun 接入结构化 trace 和 regression eval。

v20 已经实现：

```text
execute_skill
-> SkillToolRunner
-> workspace tools
-> SkillRun.to_text()
```

v21 补齐：

```text
SkillRun
-> SkillRun.to_dict()
-> ToolResult.metadata["skill_run"]
-> WorkspaceAgent.to_trace_dict()["skill_run"]
-> regression eval coverage
```

核心边界：

- 文本输出继续用于 CLI 和用户阅读。
- 结构化 dict 用于 trace、测试、eval、后续 LangGraph state。
- `ToolResult.metadata` 承载工具专属结构化结果，不污染所有工具的文本输出。

## 本次新增能力

1. `SkillToolRequest` 新增 `to_dict()`。
2. `SkillToolResponse` 新增 `to_dict()`。
3. `SkillStep` 新增 `to_dict()`。
4. `SkillStepResult` 新增 `to_dict()`。
5. `SkillRun` 新增 `to_dict()`。
6. `ToolResult` 新增 `metadata`。
7. `run_skill()` 和 `run_skill_with_workspace()` 把 `SkillRun.to_dict()` 写入 metadata。
8. `WorkspaceAgent.to_trace_dict()` 新增：
   - `tool_result.metadata`
   - 顶层 `skill_run`
9. 新增 `skills-execution` regression eval case。
10. 新增结构化 trace 测试。

## 交互流程

### Agent trace 流程

输入：

```text
Execute skill for code review.
```

流程：

```text
route_intent
-> execute_skill
-> run_skill_with_workspace()
-> execute_skill(..., tool_runner=...)
-> SkillRun
-> SkillRun.to_text()
-> SkillRun.to_dict()
-> ToolResult(output=text, metadata={"skill_run": dict})
-> WorkspaceAgent.to_trace_dict()
-> trace["skill_run"]
```

### eval 流程

新增用例：

```json
{
  "id": "skills-execution",
  "input": "Execute skill for code review.",
  "expected_route": "use_tool",
  "expected_tool": "execute_skill",
  "required_answer_terms": ["Skill run: code_review", "tool-backed steps", "[list_dir]"]
}
```

验证点：

- router 能识别 skill execution。
- Agent 能调用 `execute_skill`。
- skill run 使用 tool-backed runner。
- answer 中包含真实工具输出标记 `[list_dir]`。

## 代码改动说明

### `skills/execution.py`

新增 `to_dict()` 方法：

- `SkillToolRequest.to_dict()`
- `SkillToolResponse.to_dict()`
- `SkillStep.to_dict()`
- `SkillStepResult.to_dict()`
- `SkillRun.to_dict()`

`SkillRun.to_dict()` 输出：

- `task`
- `skill`
- `status`
- `step_count`
- `completed_steps`
- `failed_steps`
- `tool_backed_steps`
- `steps`
- `final_output`

这让 skill execution 不再只能依赖文本解析。

### `agent/tools.py`

`ToolResult` 新增：

```python
metadata: dict[str, Any] | None = None
```

`run_skill()` 和 `run_skill_with_workspace()` 现在返回：

```python
ToolResult(
    "execute_skill",
    skill_run.to_text(),
    {"skill_run": skill_run.to_dict()},
)
```

### `agent/core.py`

`to_trace_dict()` 的 `tool_result` 增加：

```python
"metadata": run.tool_result.metadata
```

并新增顶层字段：

```python
"skill_run": ...
```

这样调用方不需要从 `tool_result.metadata` 深层寻找 skill run。

### `evals/regression_cases.json`

新增：

- `skills-execution`

eval 总数从 14 增加到 15。

### `tests/test_collaboration.py`

新增测试：

- `test_skill_run_exports_trace_dict`
- `test_agent_trace_dict_contains_skill_run`

## 新增文件与行数

| 文件 | 行数 |
| --- | ---: |
| `versions/skill-trace-export_v21.md` | 246 |
| `docs/skill-trace-export-exercises_v21.md` | 123 |

## 本次修改文件与行数

| 文件 | 行数 |
| --- | ---: |
| `skills/execution.py` | 321 |
| `agent/tools.py` | 194 |
| `agent/core.py` | 640 |
| `tests/test_collaboration.py` | 219 |
| `evals/regression_cases.json` | 107 |
| `docs/current-learning-state.md` | 266 |

## 验证命令

定向测试：

```bash
python -m unittest tests.test_collaboration tests.test_evals -v
```

全量测试：

```bash
python -m unittest discover -s tests -v
```

回归评估：

```bash
python -m cli.eval_runner
```

结构化 trace 检查：

```bash
python - <<'PY'
from pathlib import Path
from agent import WorkspaceAgent

agent = WorkspaceAgent(Path("."))
trace = agent.to_trace_dict(agent.run("Execute skill for code review."))
print(trace["skill_run"]["skill"]["name"])
print(trace["skill_run"]["status"])
print(trace["skill_run"]["tool_backed_steps"])
PY
```

## 当前验证结果

已通过：

- 定向测试：26/26
- eval：15/15

## 本阶段学习重点

1. `to_text()` 面向人读，`to_dict()` 面向系统读。
2. `ToolResult.metadata` 是工具专属结构化结果的承载位置。
3. 顶层 `trace["skill_run"]` 是为了让调用方更容易消费 skill run。
4. eval case 应该覆盖新增关键能力，而不是只依赖单测。
5. 结构化 trace 是后续 LangGraph state、日志、恢复和可视化的基础。

## 下一阶段建议

下一阶段可以进入 “LangGraph Skill Node”：

- 把 `execute_skill` 包装成 LangGraph node。
- 让 graph state 携带 `skill_run`。
- 根据 `SkillRun.status` 决定 graph edge。
- 为 failed skill run 增加 fallback path。
