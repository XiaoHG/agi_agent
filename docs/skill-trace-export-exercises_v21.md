# Skill Trace Export 阶段练习

对应版本：v21  
主题：SkillRun structured trace / JSON export  
用途：理解 SkillRun 如何从文本输出升级为结构化可观测数据

## 练习 1：理解阶段目标

请回答：

1. v21 相比 v20 解决了什么问题？
2. 为什么 `SkillRun` 不能只有 `to_text()`？
3. `ToolResult.metadata` 的作用是什么？
4. 为什么 `WorkspaceAgent.to_trace_dict()` 要提供顶层 `skill_run` 字段？
5. 为什么需要给 `execute_skill` 增加 regression eval case？

## 练习 2：读 `skills/execution.py`

阅读：

- `skills/execution.py`

请回答：

1. 哪些类新增了 `to_dict()`？
2. `SkillStepResult.to_dict()` 导出了哪些字段？
3. `SkillRun.to_dict()` 中的 `completed_steps` 如何计算？
4. `SkillRun.to_dict()` 中的 `tool_backed_steps` 如何计算？
5. `to_text()` 和 `to_dict()` 分别面向什么使用场景？

## 练习 3：读 Agent trace 接入

阅读：

- `agent/tools.py`
- `agent/core.py`

请回答：

1. `ToolResult` 新增了哪个字段？
2. `run_skill_with_workspace()` 如何把 `SkillRun` 写入 metadata？
3. `to_trace_dict()` 的 `tool_result` 现在多了什么？
4. 顶层 `skill_run` 从哪里取值？
5. 如果工具没有 metadata，`skill_run` 应该是什么？

## 练习 4：读测试和 eval

阅读：

- `tests/test_collaboration.py`
- `evals/regression_cases.json`

请回答：

1. `test_skill_run_exports_trace_dict` 验证了什么？
2. `test_agent_trace_dict_contains_skill_run` 验证了什么？
3. `skills-execution` eval case 的输入是什么？
4. `skills-execution` eval case 期望 route 和 tool 分别是什么？
5. 为什么 eval case 要检查 `[list_dir]`？

## 练习 5：手动运行验证

运行：

```bash
python -m unittest tests.test_collaboration tests.test_evals -v
```

请记录：

1. 总共运行了多少个测试？
2. 是否全部通过？
3. 哪些测试是 v21 新增或直接相关？

运行：

```bash
python -m cli.eval_runner
```

请记录：

1. eval 总数是多少？
2. passed 是多少？
3. 是否出现 `skills-execution`？

运行：

```bash
python - <<'PY'
from pathlib import Path
from agent import WorkspaceAgent

agent = WorkspaceAgent(Path("."))
trace = agent.to_trace_dict(agent.run("Execute skill for code review."))
print(trace["skill_run"]["skill"]["name"])
print(trace["skill_run"]["status"])
print(trace["skill_run"]["tool_backed_steps"])
print(trace["skill_run"]["steps"][0]["tool_name"])
PY
```

请记录输出结果。

## 练习 6：阶段评估题

请用自己的话回答：

1. 为什么结构化 trace 比文本 trace 更适合 eval 和恢复？
2. `ToolResult.metadata` 和顶层 `trace["skill_run"]` 是否重复？为什么仍然都保留？
3. 如果未来要把 SkillRun 保存到日志文件，应该保存 `to_text()` 还是 `to_dict()`？
4. 如果未来要把 `execute_skill` 做成 LangGraph node，`skill_run.status` 可以如何影响 graph edge？
5. 下一阶段做 LangGraph Skill Node 时，最小可行设计是什么？

## 完成标准

可以进入下一阶段的标准：

- 能解释 `to_text()` 和 `to_dict()` 的边界。
- 能说明 `ToolResult.metadata` 的作用。
- 能从 `WorkspaceAgent.to_trace_dict()` 中找到 `skill_run`。
- 能解释 `skills-execution` eval case 的价值。
- 能说明为什么 v21 是 LangGraph skill node 的前置阶段。
