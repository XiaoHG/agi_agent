# LangGraph Skill Node v22 练习

本练习对应版本：v22

目标：确认你理解 `Skill` 如何作为 LangGraph node 执行，以及 `SkillRun` 如何从 graph state 进入主 Agent trace。

## 练习 1：说明 graph state 的新增字段

请回答：

`RAGGraphState` 中新增的 `skill_run` 和 `skill_status` 分别解决什么问题？

参考答案：

`skill_run` 用来保存 Skill 执行后的结构化 trace。它不是给用户看的普通文本，而是给系统后续调试、测试、eval、恢复和跨节点传递使用的数据。它通常包含 skill 名称、执行状态、步骤数量、每一步 observation、失败信息和最终输出。

`skill_status` 用来保存 Skill 执行的状态结果，例如 `completed` 或 `failed`。它的价值是让 LangGraph 可以根据执行结果继续选择后续路径，而不是只根据用户输入做一次静态路由。

简单说：

- `skill_run` 解决“执行过程是否可观察”的问题。
- `skill_status` 解决“执行完成后 graph 应该往哪里走”的问题。

## 练习 2：说明 `call_skill` node 的职责边界

请回答：

为什么本阶段新增了单独的 `call_skill()`，而不是把 skill execution 直接放进原来的 `call_tool()`？

参考答案：

因为 Skill execution 不只是普通工具调用。

普通 `call_tool()` 的核心职责是调用 LangChain tool，并把工具输出写入 `tool_output`。这种模式适合 `read_file`、`search_docs`、`answer_docs_with_llm` 这类主要返回文本的工具。

但 Skill execution 会产生更复杂的结构化结果：

- `SkillRun`
- `SkillStepResult`
- 每一步的 `status`
- 每一步的 `observation`
- tool-backed step 统计
- 最终 `skill_status`

如果直接塞进 `call_tool()`，会让通用工具节点承担过多职责，导致 graph state 不清晰，也不利于后续做 failure recovery、approval gate、retry 等专业 Agent 流程。

因此本阶段新增 `call_skill()`，让 Skill 成为 LangGraph 中一个独立、可观察、可分支的执行节点。

## 练习 3：追踪一次完整调用链

请基于下面命令，写出从用户输入到最终 trace 的关键步骤：

```bash
python -m cli.main --input "Use LangGraph to execute skill for code review." --trace
```

要求至少包含：

- `WorkspaceAgent`
- `run_rag_graph`
- `route`
- `call_skill`
- `run_skill_with_workspace`
- `SkillRun.to_dict`
- `finalize`
- `WorkspaceAgent.to_trace_dict`

参考答案：

完整调用链可以理解为：

```text
用户输入
  -> WorkspaceAgent.run()
  -> route_intent()
  -> route.action = graph
  -> WorkspaceAgent._run_langgraph()
  -> run_rag_graph()
  -> build_rag_graph()
  -> route node
  -> route = skill_execution
  -> selected_tool = execute_workspace_skill
  -> call_skill node
  -> run_skill_with_workspace()
  -> execute_skill()
  -> SkillRun.to_dict()
  -> graph state["skill_run"]
  -> graph state["skill_status"]
  -> _next_after_skill()
  -> finalize node
  -> graph state["answer"]
  -> WorkspaceAgent._build_langgraph_metadata()
  -> ToolResult.metadata["skill_run"]
  -> WorkspaceAgent.to_trace_dict()
```

这条链路的关键点是：`SkillRun` 不是只被格式化进最终文本，而是同时进入了 graph state 和主 Agent trace。

## 练习 4：解释条件边

请回答：

`_next_after_skill()` 为什么要基于 `skill_status` 返回不同分支？当前两个分支都进入 `finalize`，这样设计还有没有意义？

参考答案：

`_next_after_skill()` 基于 `skill_status` 返回不同分支，是为了让 graph 的后续路径依赖真实执行结果，而不是只依赖用户输入。

当前实现中：

```text
skill_completed -> finalize
skill_failed -> finalize
```

虽然两个分支现在都进入 `finalize`，但这个设计仍然有意义。原因是当前阶段先建立了“执行结果驱动条件边”的结构，后续可以很自然地扩展为：

```text
skill_completed -> finalize
skill_failed -> recover_skill_failure
```

也就是说，v22 的重点不是马上实现失败恢复，而是先把 graph 的分支边界建好。这样下一阶段新增 recovery node 时，不需要重写 Skill 执行节点，只需要扩展失败分支。

## 练习 5：阅读测试并解释断言

请阅读 `tests/test_langgraph_workflow.py` 中新增的三个测试，并回答：

1. 哪个测试验证 graph 路由到了 skill execution？
2. 哪个测试验证 graph state 保留了 `skill_run`？
3. 哪个测试验证 `skill_status` 参与了 graph 后续路径判断？

参考答案：

1. `test_rag_graph_routes_to_skill_execution` 验证 graph 路由到了 skill execution。

   关键断言包括：

   - `result["route"] == "skill_execution"`
   - `result["selected_tool"] == "execute_workspace_skill"`
   - `result["steps"] == ["route", "call_skill", "finalize"]`

2. `test_rag_graph_keeps_skill_run_trace` 验证 graph state 保留了 `skill_run`。

   关键断言包括：

   - `skill_run["skill"]["name"] == "code_review"`
   - `skill_run["status"] == "completed"`
   - `skill_run["tool_backed_steps"] >= 1`
   - `skill_run["step_count"] >= 1`

3. `test_rag_graph_skill_status_controls_next_edge` 验证 `skill_status` 参与了 graph 后续路径判断。

   关键断言包括：

   - `result["skill_status"] == "completed"`
   - `result["steps"][-1] == "finalize"`
   - `error` 不在结果中

## 练习 6：阅读主 Agent trace 测试

请阅读 `tests/test_agent.py` 中的 `test_agent_langgraph_skill_trace_dict_contains_skill_run`，并回答：

这个测试为什么不只检查 `run.answer`，还要检查 `agent.to_trace_dict(run)`？

参考答案：

因为 `run.answer` 是面向用户的文本输出，而 `agent.to_trace_dict(run)` 是面向系统的结构化执行记录。

只检查 `run.answer` 只能证明最终文本里出现了某些内容，不能证明系统真的保留了可复用的结构化数据。对于 Agent 工程来说，这不够。

检查 `agent.to_trace_dict(run)` 可以确认：

- 主 Agent route 是 `graph`
- graph 内部 route 是 `skill_execution`
- `ToolResult.metadata` 中保存了 graph metadata
- `trace["skill_run"]` 可以直接访问
- `skill_run["skill"]["name"]` 是 `code_review`
- `skill_run["status"]` 是 `completed`

这说明 `SkillRun` 没有只停留在文本输出里，而是进入了可测试、可恢复、可分析的 trace 数据结构。

## 练习 7：手动验证

请手动运行：

```bash
python -m unittest tests.test_langgraph_workflow tests.test_agent tests.test_evals -v
python -m cli.eval_runner
python -m cli.main --input "Use LangGraph to execute skill for code review." --trace
```

记录：

1. 测试是否通过？
2. eval 是否通过？
3. trace 中是否出现 `Graph route: skill_execution`？
4. trace 中是否出现 `Skill status: completed`？
5. trace 中是否出现 `Skill run: code_review`？

参考答案：

本阶段验证结果如下：

1. 测试通过。

   ```text
   Ran 107 tests
   OK
   ```

2. eval 通过。

   ```text
   total: 16
   passed: 16
   failed: 0
   ```

3. trace 中出现了 `Graph route: skill_execution`。

4. trace 中出现了 `Skill status: completed`。

5. trace 中出现了 `Skill run: code_review`。

这说明 v22 的主路径已经连通：

```text
WorkspaceAgent -> LangGraph -> call_skill -> SkillRun -> graph state -> trace
```

## 练习 8：设计下一阶段 failure recovery

请根据当前代码回答：

如果 `skill_status == failed`，你认为下一阶段应该新增什么 node？这个 node 应该输出哪些信息，才能帮助用户或 Agent 继续恢复？

参考答案：

下一阶段应该新增一个类似 `recover_skill_failure` 或 `build_skill_recovery_plan` 的 node。

这个 node 的职责不是重新执行 skill，而是把失败状态转换成可行动的恢复计划。它应该读取：

- `skill_run`
- `skill_status`
- failed step
- error message
- 已完成步骤
- 原始 task

然后输出：

- 失败发生在哪个 skill
- 失败发生在哪一步
- 失败原因是什么
- 已经完成了哪些步骤
- 哪些步骤没有执行
- 建议用户如何修复输入、文件或环境
- Agent 下一步可以安全执行什么操作

理想的 graph 结构可以演进为：

```text
call_skill
  -> skill_completed -> finalize
  -> skill_failed -> recover_skill_failure -> finalize
```

这样做的工程价值是：失败不会只变成一句错误文本，而是会被标准化为可观察、可测试、可恢复的状态。
