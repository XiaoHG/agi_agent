# LangGraph Tool Failure Recovery v24

版本：v24

日期：2026-08-03

## 本次目标

本阶段把 v23 的 Skill failure recovery 扩展到普通 LangChain tool 调用。

v23 解决的是：

```text
call_skill -> skill_failed -> recover_skill_failure
```

v24 解决的是：

```text
call_tool -> tool_failed -> recover_tool_failure
```

这样 LangGraph 的失败恢复能力不再只覆盖 Skills，也覆盖 `read_workspace_file`、`search_workspace_docs`、`answer_workspace_docs_with_llm` 等普通工具节点。

## 本次新增能力

1. `RAGGraphState` 新增 `tool_status`。
2. `RAGGraphState` 新增 `tool_error`。
3. `call_tool()` 成功时写入 `tool_status = completed`。
4. `call_tool()` 失败时写入 `tool_status = failed` 和 `tool_error`。
5. 新增 `recover_tool_failure()` graph node。
6. 新增 `_next_after_tool()` 条件边判断。
7. 新增 tool recovery plan 结构。
8. 新增 tool failure 分类。
9. 主 Agent answer 新增 `Tool status`。
10. 主 Agent metadata 透传 `tool_status`、`tool_error` 和 `recovery_plan`。
11. 新增 LangGraph tool failure recovery 测试。
12. 新增主 Agent tool recovery metadata 测试。
13. 新增 eval case：`langgraph-tool-failure-recovery`。

## 修改文件与关键行号

### `integrations/langgraph_workflow.py`

当前文件行数：`456`

关键新增区域：

- `24-25`：`RAGGraphState` 新增 `tool_status` 和 `tool_error`。
- `98`：普通工具成功时写入 `tool_status = completed`。
- `104-106`：普通工具失败时写入 `error`、`tool_error` 和 `tool_status = failed`。
- `145-156`：新增 `recover_tool_failure()` node。
- `178`：注册 `recover_tool_failure` node。
- `193-200`：`call_tool` 后改为条件边。
- `201`：`recover_tool_failure` 执行后进入 `finalize`。
- `233-238`：新增 `_next_after_tool()`。
- `262-275`：新增 `_build_tool_recovery_plan()`。
- `278-290`：新增 `_classify_tool_failure()`。
- `293-306`：新增 `_build_tool_next_safe_action()`。
- `309-320`：新增 `_format_tool_recovery_plan()`。

### `agent/core.py`

当前文件行数：`665`

关键新增区域：

- `420`：读取 `tool_status`。
- `426`：graph answer 输出 `Tool status`。
- `439-441`：graph metadata 透传 `tool_status` 和 `tool_error`。

### `tests/test_langgraph_workflow.py`

当前文件行数：`139`

关键新增区域：

- `53-64`：新增 `test_rag_graph_recovers_failed_tool_call()`。
- `66-75`：新增 `test_rag_graph_tool_status_controls_next_edge()`。

### `tests/test_agent.py`

当前文件行数：`210`

关键新增区域：

- `183-196`：新增 `test_agent_langgraph_metadata_contains_tool_recovery_plan()`。

### `evals/regression_cases.json`

当前文件行数：`121`

关键新增区域：

- `114-120`：新增 `langgraph-tool-failure-recovery`。

## 新增文件

| 文件 | 行数 | 说明 |
| --- | ---: | --- |
| `versions/langgraph-tool-failure-recovery_v24.md` | 208 | v24 迭代说明 |
| `docs/langgraph-tool-failure-recovery-exercises_v24.md` | 98 | 本阶段练习，文件名带版本号 |

## 新增交互流程

普通工具失败恢复路径：

```text
User input
  -> WorkspaceAgent.run()
  -> route_intent()
  -> action = graph
  -> run_rag_graph()
  -> route node
  -> route = read_file
  -> call_tool node
  -> read_workspace_file
  -> tool raises error
  -> graph state["tool_status"] = failed
  -> graph state["tool_error"]
  -> _next_after_tool()
  -> recover_tool_failure node
  -> recovery_plan
  -> finalize node
  -> WorkspaceAgent._build_langgraph_metadata()
  -> trace["tool_result"]["metadata"]["recovery_plan"]
```

手动运行示例：

```bash
python -m cli.main --input "Use LangGraph to read not-exist.md." --trace
```

你应该重点观察：

- `Graph route: read_file`
- `Selected tool: read_workspace_file`
- `Tool status: failed`
- `Graph steps: route -> call_tool -> recover_tool_failure -> finalize`
- `Tool recovery plan`
- `Failure type: missing_resource`

## Tool failure 和 Skill failure 的区别

| 维度 | Tool failure | Skill failure |
| --- | --- | --- |
| 失败来源 | 单个 LangChain tool | 多步骤 SkillRun |
| 关键状态 | `tool_status` / `tool_error` | `skill_status` / `skill_run` |
| 恢复节点 | `recover_tool_failure` | `recover_skill_failure` |
| 恢复依据 | tool name、tool input、error | skill name、failed step、completed steps |
| 输出格式 | `Tool recovery plan` | `Skill recovery plan` |

## 当前设计判断

本阶段没有让 `call_tool()` 捕获异常后直接格式化答案，而是让它只写入 state，然后通过 `_next_after_tool()` 进入 `recover_tool_failure()`。

原因：

- `call_tool()` 的职责应该是执行工具和记录状态。
- recovery 逻辑应该放在独立 node 中。
- 条件边应该显式表达成功路径和失败路径。
- 后续可以为不同 failure type 增加不同 recovery node。

这是 LangGraph 相比普通函数编排的核心价值：执行状态和后续路径是显式的。

## 当前限制

- tool recovery plan 仍是 deterministic 规则生成。
- 目前只对常见错误做粗分类。
- 没有自动 retry。
- 没有 human approval。
- 没有 checkpoint / persistence。
- skill recovery plan 和 tool recovery plan 还没有抽成统一数据类。

## 验证命令

```bash
python -m unittest tests.test_langgraph_workflow tests.test_agent tests.test_evals -v
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.main --input "Use LangGraph to read not-exist.md." --trace
```

## 本阶段学习重点

你需要重点理解：

1. 普通 tool failure 和 Skill failure 都应该进入结构化恢复路径。
2. `tool_status` 是普通 tool 节点的条件边依据。
3. `recover_tool_failure()` 不负责重新执行工具，只负责生成恢复计划。
4. `failure_type` 是后续扩展不同恢复策略的入口。
5. 主 Agent trace 需要保留 recovery plan，否则失败恢复无法被测试和复盘。

## 下一步建议

下一阶段建议进入：

```text
v25：Unified Recovery Plan Model
```

目标：

- 将 tool recovery plan 和 skill recovery plan 统一成标准数据模型。
- 增加 `RecoveryPlan.to_dict()` / `RecoveryPlan.to_text()`。
- 减少 LangGraph workflow 中的字典拼装逻辑。
- 为未来 LLM recovery synthesis 和 human approval 做准备。
