# v35 练习：tool_loop 并入默认 LangGraph orchestration

## 练习目标

理解为什么 `tool_loop` 是默认 LangGraph 主执行器吞并 classic 主控的最后一块大分支，以及这次迭代如何把“多轮选择、observation、停止条件、final synthesis”迁移进 graph state 和 graph edge。

## 一、理解题

1. 为什么 v35 要单独把 `tool_loop` 拿出来做一次迭代？
   答：因为它是 classic 主控里最后一个明显的大 orchestration 分支，而且状态复杂度最高。它不仅有 LLM 选工具，还有 observations、重复调用保护、最大步数和 final synthesis，单独做一阶段最利于学习和回归。
2. v35 和 v34 的核心差别是什么？
   答：v34 解决的是一次性 `tool_call` 决策；v35 解决的是多轮 `tool_loop` orchestration。前者是“选一次动作再分流”，后者是“反复决策直到满足停止条件再综合答案”。
3. 为什么说这次迁移的重点不是“让 graph 能跑循环”，而是“让循环状态结构化”？
   答：因为真正有工程价值的是把 observations、seen calls、stop reason、final answer source 等事实写进 graph state，这样后续才能支撑 trace、checkpoint、replay 和恢复，而不是只把 while/for 换成另一种写法。
4. 为什么 final synthesis 也必须进入 graph，而不是继续留在 `WorkspaceAgent` 外层？
   答：因为 final synthesis 是 `tool_loop` 的关键执行阶段之一。既然要把完整 tool-loop orchestration 收拢到 graph，就不能只迁移前半段选择和执行，把最后的综合留在 classic 外层。
5. 为什么 classic `tool_loop` 仍然值得保留？
   答：因为它仍然是学习对照面和显式 fallback。你可以直接比较默认 graph runtime 和 `--classic-runtime` 的 trace，看到同一个 tool loop 在两种主执行器里的职责分布差异。

## 二、源码定位题

1. graph 内新增了哪些 `tool_loop` 相关节点？
   答：`integrations/langgraph_workflow.py` 中新增了 `initialize_tool_loop`、`run_tool_loop_iteration`、`synthesize_tool_loop`、`finalize_tool_loop`。
2. 哪些 graph state 字段是 v35 新增的 `tool_loop` 关键状态？
   答：至少包括 `tool_loop_steps`、`tool_loop_observations`、`tool_loop_seen_calls`、`tool_loop_stop_reason`、`tool_loop_final_answer`、`tool_loop_final_answer_source`、`tool_loop_status`、`tool_loop_result`。
3. 哪个函数负责决定 `tool_loop` 是继续下一轮，还是进入 synthesis / finalize？
   答：`integrations/langgraph_workflow.py` 里的 `_next_after_tool_loop_iteration()`。
4. `WorkspaceAgent` 在哪里决定 `tool_loop` 默认走 graph，而 classic runtime 才走旧执行器？
   答：`agent/core.py` 的 `run()` 方法里，`run.route.action == "tool_loop"` 这一段分支。
5. 哪个方法负责把 graph 内的 `tool_loop_result` 重新映射回外层 `run.tool_loop_result`？
   答：`agent/core.py` 里的 `_apply_graph_runtime_result()`。

## 三、动手验证

运行：

```bash
python -m cli.main --input "Use tool loop to read README.md and then answer." --trace
```

回答：

1. trace 中是否出现 `Run tool-loop graph`？
   答：会出现。
2. graph route 是什么？
   答：`route=tool_loop_execution`。
3. graph steps 中至少会出现哪些节点？
   答：至少会出现 `initialize_tool_loop` 和 `run_tool_loop_iteration`；如果 loop 结束后还会出现 `synthesize_tool_loop` 和 `finalize_tool_loop`。
4. 为什么最终答案仍然是 `Result: tool loop stopped by ...` 这类旧表面格式？
   答：因为外层 `AgentRun` 仍然复用了 `ToolLoopResult.to_text()` 作为用户表层输出，底层 orchestration 已迁移，但表面行为尽量保持兼容。

再运行：

```bash
python -m cli.main --input "Use tool loop to read README.md and then answer." --classic-runtime --trace
```

回答：

1. 这次和默认 graph runtime 的最大区别是什么？
   答：classic runtime 会直接显示 `Run tool loop` 这一条 classic 执行记录，而默认 graph runtime 会显示 `Run tool-loop graph`，并把 graph steps 记录成 `route -> initialize_tool_loop -> run_tool_loop_iteration -> ...`。
2. 为什么这个对照有学习价值？
   答：因为它能直接帮助你区分“循环仍然是同一条业务语义”，但 orchestration ownership 已经从 classic 主控迁移到了 graph state + graph edge。

## 四、测试题

运行：

```bash
python -m unittest tests.test_tool_loop tests.test_langgraph_workflow tests.test_agent -v
```

回答：

1. 哪个测试验证 `WorkspaceAgent` 默认 `tool_loop` 已通过 graph 运行？
   答：`tests/test_agent.py` 里的 `test_agent_tool_loop_runs_through_default_graph_runtime`。
2. 哪个测试验证 `tool_loop` 仍可显式退回 classic runtime？
   答：`tests/test_tool_loop.py` 里的 `test_tool_loop_can_opt_out_of_graph_runtime`。
3. 哪个测试直接验证 graph 内 `tool_loop` 成功路径？
   答：`tests/test_langgraph_workflow.py` 里的 `test_rag_graph_runs_tool_loop_inside_graph`。
4. 哪个测试验证 graph 内 `tool_loop` 遇到重复工具调用会停止？
   答：`tests/test_langgraph_workflow.py` 里的 `test_rag_graph_tool_loop_stops_on_repeated_tool_call`。
5. 哪个测试验证 graph 内 `tool_loop` 的 final synthesis 失败后会保留 deterministic fallback？
   答：`tests/test_langgraph_workflow.py` 里的 `test_rag_graph_tool_loop_keeps_deterministic_fallback_when_synthesis_fails`。

## 五、思考题

1. v35 做完以后，classic 主控里还剩什么明显的大能力分支？
   答：已经没有像 `workflow`、`tool_call`、`tool_loop` 这样明显的大主路径了。classic 主控更多只剩 fallback 和对照角色。
2. 为什么说下一阶段不一定应该继续做“再吞并一个 classic 分支”？
   答：因为收益已经下降了。现在更值得做的是统一 graph runtime 的 replay、checkpoint、恢复和可观测性深化，这些会直接提升工程质量，而不是继续为了 graph 化而 graph 化。
3. 这次 `tool_loop` graph 化后，为什么 `ToolLoopResult` 还要补 `to_dict()/from_dict()`？
   答：因为 graph state 和后续持久化更适合保存 JSON-ready 数据。补了序列化能力后，loop 结果就不再只是内存对象，而是可以稳定进入 graph state、trace 和 checkpoint。
4. 为什么 iteration 节点目前采用“一轮大节点”是合理的？
   答：因为当前阶段重点是先把完整 `tool_loop` 主路径并入 graph。先用一轮大节点控制范围更稳，也保留了后续再把 iteration 细拆成更原子节点的空间。

## 六、验收标准

完成本练习后，你应该能说明：

- v35 的重点是把 bounded multi-step `tool_loop` 主路径并入默认 LangGraph orchestration。
- graph 化 `tool_loop` 的关键是 observations、stop reason、final synthesis 等状态结构化。
- classic tool_loop 仍保留，但默认主路径已经迁移到 graph。

补充验证结果：

- `python -m unittest tests.test_tool_loop tests.test_langgraph_workflow tests.test_agent -v` 已通过。
- `python -m cli.main --input "Use tool loop to read README.md and then answer." --trace` 可用于查看默认 graph 路径。
- `python -m cli.main --input "Use tool loop to read README.md and then answer." --classic-runtime --trace` 可用于对照 classic 路径。
