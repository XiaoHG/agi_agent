# LangGraph Skill Failure Recovery v23 练习

本练习对应版本：v23

目标：确认你理解 Skill 失败后如何进入 LangGraph recovery node，以及 recovery plan 如何进入主 Agent trace。

## 练习 1：说明为什么失败也要进入 graph state

请回答：

为什么 `skill_status == failed` 时，不应该只返回一段错误文本，而应该继续生成 `recovery_plan`？

参考答案：

因为失败本身也是 Agent 执行过程中的重要状态，不能只当成一段最终文本处理。

如果只返回错误文本，系统后续很难知道：

- 哪个 skill 失败了
- 哪一步失败了
- 失败原因是什么
- 已经完成了哪些步骤
- 下一步应该如何安全恢复

生成 `recovery_plan` 的价值是把失败变成结构化数据。这样失败信息可以进入 graph state、主 Agent trace、测试、eval 和后续恢复流程。

在专业 Agent 工程中，失败路径必须可观察、可测试、可恢复。否则系统只能“报错”，不能“恢复”。

## 练习 2：说明 `recover_skill_failure` node 的职责

请回答：

`recover_skill_failure()` 应该负责什么？它不应该负责什么？

参考答案：

`recover_skill_failure()` 应该负责把失败的 SkillRun 转换成结构化恢复计划。

它应该负责：

- 读取 `skill_run`
- 判断失败的 skill 名称
- 找到失败步骤
- 提取失败原因
- 记录已完成步骤数量
- 给出下一步安全操作建议
- 把恢复计划写入 `recovery_plan`
- 把恢复计划格式化为 `tool_output`

它不应该负责：

- 重新执行 skill
- 自动修改文件
- 自动忽略失败
- 隐藏错误
- 直接调用 LLM 编造恢复结论
- 执行有风险的修复动作

也就是说，这个 node 的职责是“诊断和规划恢复”，不是“直接修复”。

## 练习 3：追踪失败路径

请基于下面测试场景，写出完整失败路径：

```text
Use skill for learning explanation.
```

要求至少包含：

- `route`
- `call_skill`
- `SkillRun.status`
- `_next_after_skill`
- `recover_skill_failure`
- `recovery_plan`
- `finalize`

参考答案：

完整失败路径如下：

```text
Use skill for learning explanation.
  -> run_rag_graph()
  -> route node
  -> route = skill_execution
  -> selected_tool = execute_workspace_skill
  -> call_skill node
  -> run_skill_with_workspace()
  -> execute_skill()
  -> learning_explanation skill
  -> skill step tries to read docs/current-learning-state.md
  -> temporary workspace does not contain that file
  -> SkillRun.status = failed
  -> graph state["skill_status"] = "failed"
  -> _next_after_skill()
  -> returns "skill_failed"
  -> recover_skill_failure node
  -> _build_skill_recovery_plan()
  -> graph state["recovery_plan"]
  -> graph state["tool_output"] = formatted recovery plan
  -> finalize node
  -> graph state["answer"] = recovery plan text
```

关键点是：失败没有直接结束 graph，而是继续进入恢复节点，把失败转换成可读、可追踪的恢复计划。

## 练习 4：解释 recovery plan 字段

请说明下面字段分别解决什么问题：

- `status`
- `skill_name`
- `failed_step`
- `reason`
- `completed_steps`
- `next_safe_action`

参考答案：

- `status`

  表示恢复计划对应的执行状态。当前失败恢复中通常是 `failed`，用于明确这是失败后的恢复信息。

- `skill_name`

  表示哪个 skill 失败了，例如 `learning_explanation`。这可以帮助定位失败属于哪个能力模块。

- `failed_step`

  表示失败发生在哪个 skill step。它通常包含步骤序号、步骤说明、调用的工具和输入参数。

- `reason`

  表示失败原因。优先来自 failed step 的 `error`，如果没有则退回到 observation 或 graph error。

- `completed_steps`

  表示失败前已经完成了多少步骤。这个字段有助于判断是否可以局部恢复，还是需要从头执行。

- `next_safe_action`

  表示下一步建议做什么。它强调“安全恢复”，不会自动执行有风险操作，而是告诉用户或后续 Agent 应该先检查什么。

## 练习 5：阅读 LangGraph 测试

请阅读 `tests/test_langgraph_workflow.py` 中的 `test_rag_graph_recovers_failed_skill_run`，并回答：

1. 这个测试为什么使用临时工作区？
2. 为什么它可以触发 `learning_explanation` 失败？
3. 哪个断言证明 graph 进入了 recovery node？
4. 哪个断言证明最终 answer 是恢复计划？

参考答案：

1. 这个测试使用临时工作区，是为了构造一个隔离、可重复的测试环境。

   临时工作区里只创建了 `README.md`，不会包含真实项目中的 `docs/current-learning-state.md`。这样测试不会依赖当前仓库真实文件状态，结果更稳定。

2. 它可以触发 `learning_explanation` 失败，是因为这个 skill 的 tool-backed step 会读取：

   ```text
   docs/current-learning-state.md
   ```

   临时工作区没有这个文件，所以 `read_file` 会失败，进而让 `SkillRun.status` 变成 `failed`。

3. 下面这个断言证明 graph 进入了 recovery node：

   ```python
   self.assertEqual(result["steps"], ["route", "call_skill", "recover_skill_failure", "finalize"])
   ```

   这里明确出现了 `recover_skill_failure`。

4. 下面这个断言证明最终 answer 是恢复计划：

   ```python
   self.assertIn("Skill recovery plan", result["answer"])
   ```

   同时，下面这些断言证明恢复计划包含了失败 skill 和失败原因：

   ```python
   self.assertEqual(result["recovery_plan"]["skill_name"], "learning_explanation")
   self.assertIn("docs/current-learning-state.md", result["recovery_plan"]["reason"])
   ```

## 练习 6：阅读主 Agent trace 测试

请阅读 `tests/test_agent.py` 中的 `test_agent_langgraph_metadata_contains_recovery_plan`，并回答：

为什么 recovery plan 要保存在 `ToolResult.metadata` 中？

参考答案：

因为 `ToolResult.output` 是面向用户展示的文本，而 `ToolResult.metadata` 是面向系统处理的结构化数据。

如果 recovery plan 只存在于最终文本中，后续测试、eval、恢复流程和调试工具都只能通过字符串解析来判断失败原因，这不稳定，也不符合工程化要求。

放进 `ToolResult.metadata` 后，主 Agent 的 `to_trace_dict()` 可以稳定访问：

```python
trace["tool_result"]["metadata"]["recovery_plan"]
```

这样可以明确拿到：

- `skill_name`
- `failed_step`
- `reason`
- `completed_steps`
- `next_safe_action`

这也是专业 Agent 可观测性的基本要求：用户看到文本，系统保留结构化 trace。

## 练习 7：手动验证

请手动运行：

```bash
python -m unittest tests.test_langgraph_workflow tests.test_agent -v
python -m unittest discover -s tests -v
python -m cli.eval_runner
```

记录：

1. LangGraph / Agent 相关测试是否通过？
2. 全量测试是否通过？
3. eval 是否通过？

参考答案：

本阶段验证结果如下：

1. LangGraph / Agent 相关测试通过。

   ```text
   python -m unittest tests.test_langgraph_workflow tests.test_agent -v
   OK
   ```

2. 全量测试通过。

   ```text
   Ran 109 tests
   OK
   ```

3. eval 通过。

   ```text
   total: 16
   passed: 16
   failed: 0
   ```

这说明 v23 没有破坏已有主路径，同时新增的 Skill failure recovery 路径也有测试保护。

## 练习 8：设计下一阶段

请回答：

如果下一阶段要为普通 `call_tool` 失败也加入 recovery node，你认为应该复用哪些设计？哪些地方需要和 Skill failure recovery 区分？

参考答案：

可以复用的设计：

- 在 graph state 中保留结构化 recovery plan。
- 使用独立 recovery node，而不是把恢复逻辑塞进 `finalize`。
- 条件边根据执行结果进入成功或失败路径。
- recovery plan 进入 `ToolResult.metadata`。
- 测试同时覆盖 graph state 和主 Agent trace。
- 恢复计划只做诊断和建议，不自动执行有风险修复。

需要区分的地方：

- Skill failure 有 `SkillRun`、`SkillStepResult`、`failed_step`，普通 tool failure 可能只有 `selected_tool`、`tool_input` 和 `error`。
- Skill failure 可以报告“第几步失败”，普通 tool failure 通常只能报告“哪个工具失败”。
- Skill failure 的 `completed_steps` 有明确统计，普通 tool failure 可能没有多步骤上下文。
- Skill recovery 更关注 skill step 和能力链路，tool recovery 更关注参数、路径、权限、文件存在性、API key、网络等工具执行条件。

下一阶段可以设计成：

```text
call_tool
  -> tool_completed -> finalize
  -> tool_failed -> recover_tool_failure -> finalize
```

并让 `recover_tool_failure` 输出类似：

- `tool_name`
- `tool_input`
- `reason`
- `failure_type`
- `next_safe_action`
