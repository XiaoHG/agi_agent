# LangGraph Skill Failure Recovery v23

版本：v23

日期：2026-08-03

## 本次目标

本阶段在 v22 的 LangGraph Skill Node 基础上，补齐 Skill 失败后的恢复路径。

v22 已经可以让 LangGraph 执行 `SkillRun`，并通过 `skill_status` 判断成功或失败。但失败分支当时仍直接进入 `finalize`。v23 的目标是把失败状态变成可观察、可测试、可恢复的结构化信息。

核心变化：

```text
call_skill
  -> skill_completed -> finalize
  -> skill_failed -> recover_skill_failure -> finalize
```

## 本次新增能力

1. `RAGGraphState` 新增 `recovery_plan`。
2. LangGraph 新增 `recover_skill_failure` node。
3. `skill_status == failed` 时不再直接进入 `finalize`。
4. 失败 SkillRun 会被转换成结构化 recovery plan。
5. recovery plan 会进入 graph state。
6. recovery plan 会通过 `WorkspaceAgent` 的 graph metadata 进入主 trace。
7. 测试覆盖 LangGraph 失败恢复路径。
8. 测试覆盖主 Agent trace 中的 recovery plan。

## 修改文件与关键行号

### `integrations/langgraph_workflow.py`

当前文件行数：`360`

关键新增区域：

- `26`：`RAGGraphState` 新增 `recovery_plan`。
- `124`：Skill 执行异常时写入 exception recovery plan。
- `128-138`：新增 `recover_skill_failure()` node。
- `161`：注册 `recover_skill_failure` node。
- `175-181`：`skill_failed` 分支改为进入 `recover_skill_failure`。
- `183`：`recover_skill_failure` 执行后进入 `finalize`。
- `227-249`：新增 `_build_skill_recovery_plan()`。
- `252-262`：新增 `_build_exception_recovery_plan()`。
- `265-274`：新增 `_find_failed_skill_step()`。
- `277-285`：新增 `_extract_skill_name()`。
- `288-298`：新增 `_extract_failure_reason()`。
- `301-308`：新增 `_build_next_safe_action()`。
- `311-330`：新增 `_format_recovery_plan()`。

### `agent/core.py`

当前文件行数：`660`

关键新增区域：

- `440-441`：`_build_langgraph_metadata()` 透传 `recovery_plan`。

### `tests/test_langgraph_workflow.py`

当前文件行数：`115`

关键新增区域：

- `90-101`：新增 `test_rag_graph_recovers_failed_skill_run()`，验证失败 Skill 会进入 `recover_skill_failure`。

### `tests/test_agent.py`

当前文件行数：`195`

关键新增区域：

- `169-181`：新增 `test_agent_langgraph_metadata_contains_recovery_plan()`，验证主 Agent trace 能拿到 recovery plan。

## 新增文件

| 文件 | 行数 | 说明 |
| --- | ---: | --- |
| `versions/langgraph-skill-failure-recovery_v23.md` | 180 | v23 迭代说明 |
| `docs/langgraph-skill-failure-recovery-exercises_v23.md` | 83 | 本阶段练习，文件名带版本号 |

## 新增交互流程

失败恢复路径：

```text
User input
  -> WorkspaceAgent.run()
  -> route_intent()
  -> action = graph
  -> run_rag_graph()
  -> route node
  -> route = skill_execution
  -> call_skill node
  -> run_skill_with_workspace()
  -> execute_skill()
  -> SkillRun.status = failed
  -> _next_after_skill()
  -> recover_skill_failure node
  -> recovery_plan
  -> finalize node
  -> WorkspaceAgent._build_langgraph_metadata()
  -> trace["tool_result"]["metadata"]["recovery_plan"]
```

本阶段的测试使用临时工作区触发失败：

```text
Use skill for learning explanation.
```

原因是 `learning_explanation` skill 会尝试读取：

```text
docs/current-learning-state.md
```

临时工作区中没有该文件，所以 SkillRun 会失败。这是一个真实失败场景，不是为了测试而硬编码的假失败。

## 当前设计判断

本阶段没有让失败直接抛异常终止 graph。

原因：

- SkillRun 已经可以表达 `failed` 状态。
- 失败仍然是一种可处理的 graph state。
- Agent 工程中，失败路径也需要进入 trace 和 eval。
- 用户更需要“下一步怎么恢复”，而不是只看到异常文本。

因此 v23 的处理方式是：

```text
failed SkillRun -> structured recovery_plan -> final answer
```

## 当前限制

- recovery plan 仍是 deterministic 规则生成，还没有接入 LLM synthesis。
- recovery plan 还没有进入 eval regression case。
- 失败后还不会自动重试。
- 还没有 human approval / interruption。
- LangGraph 仍没有 checkpoint / persistence。
- 失败恢复只覆盖 Skill failure，还没有覆盖普通 tool node failure。

## 验证命令

```bash
python -m unittest tests.test_langgraph_workflow tests.test_agent -v
python -m unittest discover -s tests -v
python -m cli.eval_runner
```

## 本阶段学习重点

你需要重点理解：

1. Agent 工程不能只设计成功路径，失败路径同样要结构化。
2. `SkillRun.status` 是 graph 分支判断依据，不只是展示字段。
3. recovery node 的职责是把失败状态转换成可行动信息。
4. recovery plan 应该进入 trace，否则后续无法测试、恢复或分析。
5. LangGraph 的价值不只是“调用节点”，而是把成功、失败、恢复这些状态转换关系显式表达出来。

## 下一步建议

下一阶段建议进入：

```text
v24：LangGraph Tool Failure Recovery
```

目标：

- 为普通 `call_tool` 失败新增 recovery node。
- 统一 tool failure 和 skill failure 的恢复计划结构。
- 为 graph error 增加可测试的 failure trace。
- 为失败恢复补充 eval case。
