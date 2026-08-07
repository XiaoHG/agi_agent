# LangGraph Tool Failure Recovery v24 练习

本练习对应版本：v24

目标：确认你理解普通 LangChain tool 失败后如何进入 LangGraph recovery node，以及 tool recovery plan 如何进入主 Agent trace。

## 练习 1：说明为什么 `call_tool` 失败后不应该直接 `finalize`

请回答：

为什么普通工具失败后，要先进入 `recover_tool_failure()`，而不是直接在 `finalize()` 中返回错误？

参考答案：

因为 `finalize()` 的职责应该是把已有的 graph state 转换成最终答案，而不是负责分析失败原因、分类失败类型、生成恢复建议。

如果普通工具失败后直接进入 `finalize()`，系统通常只能输出一段错误文本，例如“文件不存在”。这不利于后续测试、恢复和自动化处理。

先进入 `recover_tool_failure()` 的价值是：

- 把失败从错误字符串转换成结构化 `recovery_plan`
- 记录失败工具名
- 记录工具输入
- 记录失败原因
- 判断 `failure_type`
- 给出下一步安全操作建议
- 让失败恢复路径在 graph 中显式可见

因此普通工具失败后的合理路径是：

```text
call_tool -> recover_tool_failure -> finalize
```

而不是：

```text
call_tool -> finalize
```

## 练习 2：说明 `tool_status` 和 `tool_error`

请回答：

`tool_status` 和 `tool_error` 分别解决什么问题？它们和 v23 的 `skill_status`、`skill_run` 有什么对应关系？

参考答案：

`tool_status` 用来表示普通工具调用的执行状态，例如：

- `completed`
- `failed`

它主要用于 graph 条件边判断，让 `_next_after_tool()` 决定下一步进入 `finalize` 还是 `recover_tool_failure`。

`tool_error` 用来保存普通工具失败时的错误原因。它是生成 `recovery_plan.reason` 和判断 `failure_type` 的依据。

它们和 v23 的字段对应关系是：

| Tool failure | Skill failure | 说明 |
| --- | --- | --- |
| `tool_status` | `skill_status` | 都用于判断成功或失败 |
| `tool_error` | `skill_run.steps[].error` | 都用于提取失败原因 |
| `tool_input` | `skill_run.steps[].tool_input` | 都用于定位失败输入 |
| `selected_tool` | `skill_run.skill.name` | 都用于定位失败能力 |

区别在于：普通 tool 是单步调用，所以没有完整的 `SkillRun`；Skill 是多步骤执行，所以需要 `skill_run` 保留步骤级 trace。

## 练习 3：追踪普通工具失败路径

请基于下面命令写出完整执行路径：

```bash
python -m cli.main --input "Use LangGraph to read not-exist.md." --trace
```

要求至少包含：

- `WorkspaceAgent`
- `run_rag_graph`
- `route`
- `call_tool`
- `_next_after_tool`
- `recover_tool_failure`
- `recovery_plan`
- `finalize`
- `WorkspaceAgent.to_trace_dict`

参考答案：

完整执行路径如下：

```text
用户输入
  -> WorkspaceAgent.run()
  -> route_intent()
  -> route.action = graph
  -> WorkspaceAgent._run_langgraph()
  -> run_rag_graph()
  -> build_rag_graph()
  -> route node
  -> route = read_file
  -> selected_tool = read_workspace_file
  -> tool_input = {"path": "not-exist.md"}
  -> call_tool node
  -> read_workspace_file.invoke()
  -> read_file()
  -> File does not exist: not-exist.md
  -> graph state["tool_status"] = "failed"
  -> graph state["tool_error"] = "File does not exist: not-exist.md"
  -> _next_after_tool()
  -> returns "tool_failed"
  -> recover_tool_failure node
  -> _build_tool_recovery_plan()
  -> graph state["recovery_plan"]
  -> graph state["tool_output"] = formatted tool recovery plan
  -> finalize node
  -> graph state["answer"]
  -> WorkspaceAgent._build_langgraph_metadata()
  -> ToolResult.metadata["recovery_plan"]
  -> WorkspaceAgent.to_trace_dict()
```

关键点是：工具失败没有直接结束，而是被转换成了可追踪的恢复计划。

## 练习 4：解释 tool recovery plan 字段

请说明下面字段分别解决什么问题：

- `status`
- `failure_type`
- `tool_name`
- `tool_input`
- `reason`
- `next_safe_action`

参考答案：

- `status`

  表示恢复计划对应的状态。当前普通工具失败时通常是 `failed`。

- `failure_type`

  表示失败分类，例如 `missing_resource`、`unsafe_or_denied_access`、`external_dependency`、`input_too_large`、`tool_execution_error`。它是后续选择不同恢复策略的入口。

- `tool_name`

  表示失败的工具名，例如 `read_workspace_file`。它用于定位失败发生在哪个能力边界。

- `tool_input`

  表示工具调用时的输入参数，例如 `{"path": "not-exist.md"}`。它用于判断是否是路径、参数、问题文本或其他输入导致失败。

- `reason`

  表示底层错误原因，例如 `File does not exist: not-exist.md`。它是恢复建议的证据来源。

- `next_safe_action`

  表示下一步安全操作建议。例如文件不存在时，建议先检查该文件是否存在、修正路径，然后重新运行工具。

## 练习 5：比较 Tool failure 和 Skill failure

请回答：

普通 tool failure recovery 和 Skill failure recovery 哪些设计可以统一？哪些地方必须区分？

参考答案：

可以统一的设计：

- 都应该有 `status`
- 都应该有失败原因 `reason`
- 都应该有下一步安全建议 `next_safe_action`
- 都应该进入 `recovery_plan`
- 都应该进入 graph state
- 都应该进入 `ToolResult.metadata`
- 都应该被测试覆盖
- 都应该避免自动执行有风险修复

必须区分的地方：

- 普通 tool failure 是单步失败，核心信息是 `tool_name`、`tool_input`、`tool_error`。
- Skill failure 是多步骤失败，核心信息是 `skill_name`、`failed_step`、`completed_steps`、`SkillRun`。
- 普通 tool recovery 更关注参数、路径、权限、API key、网络依赖。
- Skill recovery 更关注技能步骤、步骤顺序、哪个 tool-backed step 失败。

所以它们可以统一成一个通用 RecoveryPlan 模型，但字段要允许部分为空。

## 练习 6：阅读 LangGraph 测试

请阅读 `tests/test_langgraph_workflow.py` 中新增的两个 tool failure 测试，并回答：

1. 哪个测试验证失败工具进入了 `recover_tool_failure`？
2. 哪个测试验证成功工具不会进入 recovery node？
3. 为什么成功路径也要测 `tool_status`？

参考答案：

1. `test_rag_graph_recovers_failed_tool_call` 验证失败工具进入了 `recover_tool_failure`。

   关键断言是：

   ```python
   self.assertEqual(result["steps"], ["route", "call_tool", "recover_tool_failure", "finalize"])
   ```

2. `test_rag_graph_tool_status_controls_next_edge` 验证成功工具不会进入 recovery node。

   关键断言是：

   ```python
   self.assertEqual(result["steps"], ["route", "call_tool", "finalize"])
   self.assertNotIn("recovery_plan", result)
   ```

3. 成功路径也要测 `tool_status`，因为条件边依赖这个字段。

   如果成功路径没有正确写入：

   ```python
   result["tool_status"] == "completed"
   ```

   那么 `_next_after_tool()` 可能会误判，导致成功工具也进入失败恢复路径。

   因此成功状态和失败状态都必须测试。

## 练习 7：阅读主 Agent trace 测试

请阅读 `tests/test_agent.py` 中的 `test_agent_langgraph_metadata_contains_tool_recovery_plan`，并回答：

为什么这个测试要检查 `metadata["recovery_plan"]["failure_type"]`？

参考答案：

因为 `failure_type` 是恢复计划中最重要的结构化判断字段之一。

只检查 `run.answer` 是否包含 `Tool recovery plan`，只能证明用户看到了恢复文本，不能证明系统真的完成了失败分类。

检查：

```python
metadata["recovery_plan"]["failure_type"]
```

可以确认：

- recovery plan 已进入主 Agent metadata
- 失败被分类为可处理类型
- 后续流程可以根据 `failure_type` 选择恢复策略

例如当前文件不存在场景应该被分类为：

```text
missing_resource
```

这比只输出“文件不存在”更适合后续自动化恢复。

## 练习 8：阅读 eval case

请阅读 `evals/regression_cases.json` 中的 `langgraph-tool-failure-recovery`，并回答：

这个 eval case 验证的是代码实现细节，还是 Agent 对外行为？为什么？

参考答案：

这个 eval case 验证的是 Agent 对外行为，不是代码实现细节。

它检查的是输入：

```text
Use LangGraph to read not-exist.md.
```

最终是否表现出正确行为：

- route 是 `graph`
- tool 是 `langgraph_workflow`
- answer 中包含 `Graph route: read_file`
- answer 中包含 `Tool status: failed`
- answer 中包含 `Tool recovery plan`
- answer 中包含 `missing_resource`

它没有检查内部函数名、具体实现方式或代码行号。

这说明 eval 的关注点是“用户请求进来后，Agent 是否表现出预期能力”。具体内部可以重构，只要外部行为稳定，eval 就应该通过。

## 练习 9：手动验证

请手动运行：

```bash
python -m unittest tests.test_langgraph_workflow tests.test_agent tests.test_evals -v
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.main --input "Use LangGraph to read not-exist.md." --trace
```

记录：

1. 相关测试是否通过？
2. 全量测试是否通过？
3. eval 是否通过？
4. CLI trace 是否出现 `Tool recovery plan`？

参考答案：

本阶段验证结果如下：

1. 相关测试通过。

   ```text
   python -m unittest tests.test_langgraph_workflow tests.test_agent tests.test_evals -v
   OK
   ```

2. 全量测试通过。

   ```text
   Ran 112 tests
   OK
   ```

3. eval 通过。

   ```text
   total: 17
   passed: 17
   failed: 0
   ```

4. CLI trace 出现了 `Tool recovery plan`。

   同时还出现了：

   ```text
   Tool status: failed
   Failure type: missing_resource
   Graph steps: route -> call_tool -> recover_tool_failure -> finalize
   ```

这说明 v24 的普通工具失败恢复路径已经接通。

## 练习 10：设计下一阶段统一模型

请回答：

如果下一阶段要把 tool recovery plan 和 skill recovery plan 统一为一个 `RecoveryPlan` 数据模型，这个模型至少应该有哪些字段？哪些字段应该允许为空？

参考答案：

一个可用的 `RecoveryPlan` 数据模型至少应该包含：

```python
@dataclass(frozen=True)
class RecoveryPlan:
    status: str
    failure_type: str
    source_type: str
    source_name: str
    reason: str
    next_safe_action: str
    tool_name: str | None = None
    tool_input: dict[str, str] | None = None
    skill_name: str | None = None
    failed_step: dict[str, object] | None = None
    completed_steps: int | None = None
```

建议必填字段：

- `status`
- `failure_type`
- `source_type`
- `source_name`
- `reason`
- `next_safe_action`

建议允许为空的字段：

- `tool_name`
- `tool_input`
- `skill_name`
- `failed_step`
- `completed_steps`

原因是 tool failure 和 skill failure 的上下文不同。

普通 tool failure 可能没有 `failed_step` 和 `completed_steps`；Skill failure 则不一定需要单独的 `tool_name`，因为失败工具可能已经包含在 `failed_step` 中。

统一模型的目标不是让所有字段都填满，而是让不同失败来源都能用同一种结构进入 graph state、metadata、测试和 eval。
