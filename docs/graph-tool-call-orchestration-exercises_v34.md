# v34 练习：tool_call 并入默认 LangGraph orchestration

## 练习目标

理解为什么 `tool_call` 是 `tool_loop` 之前最适合 graph 化的主路径，以及这次迭代如何把“LLM 选动作 -> 条件分流 -> 执行工具或结束”从顶层 classic 主控迁移进 LangGraph。

## 一、理解题

1. 为什么 v34 优先把 `tool_call` 并入 graph，而不是直接做 `tool_loop`？
   答：因为 `tool_call` 只需要处理一次 LLM 选择和一次后续分流，状态明显比 `tool_loop` 简单。它正好处在单步 graph 路径和多轮 `tool_loop` 之间，适合作为过渡阶段。
2. v34 和 v33 的核心差别是什么？
   答：v33 主要解决的是显式顺序步骤的 `workflow` graph 化；v34 则开始把“LLM 负责选择动作”的 `tool_call` 也放进 graph，让 graph 接手带模型决策的主路径。
3. 这次 graph 化 `tool_call`，最重要的不是“能调模型”，而是什么？
   答：而是把 `tool_call` 的决策结果变成结构化 graph state，并让后续执行通过条件边分流，而不是继续靠顶层 Python if/else 串联。
4. 为什么这次还保留 classic tool_call executor？
   答：因为仍然需要学习对照面和稳定 fallback。保留 classic runtime 可以直接比较 graph trace 和旧的 `Select tool -> Run tool` 轨迹，也能在 graph 路径异常时回退。
5. 为什么 `tool_call_selection` 需要进入 metadata / trace？
   答：因为 tool calling 的关键证据不只是“最后调了哪个工具”，而是“模型当时选了什么动作、给了什么参数、理由是什么”。这些信息进入 trace 后，才能用于调试、测试和后续恢复。

## 二、源码定位题

1. graph 内新增的 `tool_call` 核心节点叫什么？
   答：`integrations/langgraph_workflow.py` 里的 `select_tool_call` 节点。
2. 哪些 graph state 字段是 v34 新增的？
   答：`tool_call_selection`、`tool_call_status`、`tool_call_error`。
3. 哪个函数决定 `select_tool_call` 之后是 `call_tool`、`call_skill` 还是 `finalize`？
   答：`integrations/langgraph_workflow.py` 里的 `_next_after_tool_call_selection()`。
4. `WorkspaceAgent` 在哪里决定 `tool_call` 默认走 graph，classic runtime 才走旧执行器？
   答：`agent/core.py` 的 `run()` 方法里，`run.route.action == "tool_call"` 这一段分支。
5. 哪个方法负责把 graph 内的 `tool_call_selection` 重新映射回外层 `run.tool_call`？
   答：`agent/core.py` 里的 `_apply_graph_runtime_result()`。

## 三、动手验证

运行：

```bash
python -m cli.main --input "Use tool calling to read README.md." --trace
```

回答：

1. trace 中是否出现 `Run tool-call graph`？
   答：会出现。
2. graph route 是什么？
   答：`route=tool_call_execution`。
3. graph steps 中至少会出现什么节点？
   答：至少会出现 `select_tool_call`，如果模型选了普通工具，还会看到 `call_tool`。
4. 最终答案为什么仍然是 `Result: read README.md...` 风格？
   答：因为虽然默认 orchestration 已经 graph 化，但外层 `AgentRun` 仍然复用了 classic tool answer surface，保证学习接口兼容。

再运行：

```bash
python -m cli.main --input "Use tool calling to explain the difference between an agent and a chatbot." --trace
```

回答：

1. 如果模型选择 `answer_directly`，graph 会不会再进入 `call_tool`？
   答：不会，会直接 `finalize`。
2. 为什么这个场景比普通 `direct_answer` 更值得学习？
   答：因为这里不是顶层 router 直接判定不需要工具，而是“模型经过 tool calling prompt 后，主动决定不调用工具”，这两层决策边界不同。

最后运行：

```bash
python -m cli.main --input "Use tool calling to read README.md." --classic-runtime --trace
```

回答：

1. trace 和默认 graph runtime 最大差别是什么？
   答：classic runtime 会直接显示 `Select tool` 和 `Run tool`，而默认 graph runtime 会先显示 `Run tool-call graph`，并且 graph steps 会记录 `route -> select_tool_call -> call_tool -> finalize`。
2. 为什么这个对照有学习价值？
   答：因为它能帮助你区分“同一条 tool calling 逻辑”在 classic 主控和 graph orchestration 下的职责边界变化。

## 四、测试题

运行：

```bash
python -m unittest tests.test_tool_calling tests.test_langgraph_workflow tests.test_agent -v
```

回答：

1. 哪个测试验证 `WorkspaceAgent` 默认 `tool_call` 已通过 graph 运行？
   答：`tests/test_agent.py` 里的 `test_agent_tool_call_runs_through_default_graph_runtime`。
2. 哪个测试验证 `tool_call` 仍可显式退回 classic runtime？
   答：`tests/test_tool_calling.py` 里的 `test_workspace_agent_tool_calling_can_opt_out_of_graph_runtime`。
3. 哪个测试直接验证 graph 内 `tool_call` 选中普通工具后会继续执行工具？
   答：`tests/test_langgraph_workflow.py` 里的 `test_rag_graph_runs_tool_call_selection_then_tool`。
4. 哪个测试验证 graph 内 `tool_call` 可以直接回答？
   答：`tests/test_langgraph_workflow.py` 里的 `test_rag_graph_runs_tool_call_direct_answer`。
5. 哪个测试验证 graph 内 `tool_call` 可以要求澄清？
   答：`tests/test_langgraph_workflow.py` 里的 `test_rag_graph_runs_tool_call_clarification`。

## 五、思考题

1. v34 做完以后，classic 主控里最明显还剩下哪块大能力？
   答：最明显还剩 `tool_loop`。它仍然是 classic 主控里的独立大分支。
2. `tool_call` graph 化之后，为什么说 `tool_loop` 的 graph 化难度会更高？
   答：因为 `tool_loop` 不是一次选择，而是多轮选择和 observation 累积。它不仅要选择工具，还要维护 loop state、停止条件和 final synthesis，graph 状态会复杂得多。
3. 这次 `tool_call` graph 化后，外层 `run.tool_call` 还保留有什么价值？
   答：它仍然是测试、eval 和学习时最直接的表层入口。你不用先下潜到 graph state，也能快速看到模型到底选了什么动作和工具。
4. 为什么 v34 不是把 classic `tool_call` 逻辑整段复制到 graph 就算完成？
   答：因为这次真正的目标是 orchestration ownership 迁移。关键不在于代码搬家，而在于让选择结果、执行分流和失败状态变成 graph state 和 graph edge 的职责。

## 六、验收标准

完成本练习后，你应该能说明：

- v34 的重点是把带 LLM 决策的 `tool_call` 主路径并入默认 LangGraph orchestration。
- graph 化 `tool_call` 的关键是结构化状态和条件分流，而不是单纯“让模型能选工具”。
- classic tool_call 仍保留，但默认主路径已经迁移到 graph。

补充验证结果：

- `python -m unittest tests.test_tool_calling tests.test_langgraph_workflow tests.test_agent -v` 已通过。
- `python -m cli.main --input "Use tool calling to read README.md." --trace` 可用于查看默认 graph 路径。
- `python -m cli.main --input "Use tool calling to read README.md." --classic-runtime --trace` 可用于对照 classic 路径。
