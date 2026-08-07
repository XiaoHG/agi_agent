# v33 练习：workflow 并入默认 LangGraph orchestration

## 练习目标

理解为什么 `workflow` 是 graph 内统一多步 orchestration 的第一站，以及这次迭代如何把“计划、执行、停止、汇总”从经典主控迁移进 LangGraph。

## 一、理解题

1. 为什么 v33 优先把 `workflow` 并入 graph，而不是先做 `tool_loop`？
   答：因为 `workflow` 已经天然具备显式计划和顺序步骤，最容易映射成 graph node + conditional edge。`tool_loop` 还要管理 observation、重复调用保护、最大步数和 final synthesis，状态复杂度明显更高，更适合后置。
2. v33 和 v32 的核心差别是什么？
   答：v32 主要把单步主路径 `direct_answer` / `use_tool` 默认切到 graph；v33 则开始把真正的多步 `workflow` 也并入 graph，让 LangGraph 不只是默认外壳，而开始承担多步 orchestration。
3. 为什么这次没有删除 classic workflow executor？
   答：因为当前阶段仍然需要学习对照面和稳定 fallback。保留 classic workflow 可以直接比较 graph trace 和旧执行器 trace，也能在 graph 路径异常时快速回退。
4. workflow graph 化之后，顶层 `route_intent()` 的职责变化了吗？
   答：有变化但没有消失。它仍然负责把请求识别为 `workflow`，但默认不再直接执行工作流，而是把这个判断作为 route hint 交给 graph。
5. 为什么 `workflow_plan` 要转成 JSON-ready state，而不是直接把 dataclass 对象塞进 graph？
   答：因为 graph state 后续要服务 trace、checkpoint、持久化和可能的 replay。优先保存 JSON-ready 数据更稳，也更符合工程化长期方向。

## 二、源码定位题

1. 哪个文件负责把 workflow 计划转成 graph 可保存的数据？
   答：`agent/workflow.py`，其中 `WorkflowPlan.to_dict()` 负责把 plan 转成 JSON-ready 结构。
2. graph 内新增了哪三个 workflow 相关节点？
   答：`integrations/langgraph_workflow.py` 中新增了 `build_workflow`、`run_workflow_step`、`finalize_workflow`。
3. 哪个函数负责决定 workflow step 执行完之后是继续下一步，还是结束？
   答：`integrations/langgraph_workflow.py` 里的 `_next_after_workflow_step()`。
4. `WorkspaceAgent` 在哪里决定 workflow 默认走 graph，classic runtime 才走旧执行器？
   答：`agent/core.py` 的 `run()` 方法里，`run.route.action == "workflow"` 这一段分支。
5. 哪个方法负责把 workflow graph 结果重新映射回外层 `AgentRun`？
   答：还是 `agent/core.py` 里的 `_apply_graph_runtime_result()`，只是 v33 里新增了 `workflow` 对应的映射逻辑。

## 三、动手验证

运行：

```bash
python -m cli.main --input "Read README.md and then count lines." --trace
```

回答：

1. trace 中是否出现 `Run workflow graph`？
   答：会出现。
2. graph route 是什么？
   答：`route=workflow_execution`。
3. graph steps 中是否能看到 workflow 相关节点？
   答：能，至少会看到 `build_workflow` 和 `run_workflow_step`。
4. 最终答案里为什么同时能看到 `read_file` 和 `count_lines` 的结果？
   答：因为 graph 已经在 workflow 内顺序执行了多个 tool step，最后由 `finalize_workflow` 统一汇总输出。

再运行：

```bash
python -m cli.main --input "Read not-exist.md and then count lines." --trace
```

回答：

1. graph 会不会继续执行后面的 `count_lines`？
   答：不会。第一步读文件失败后，workflow 会直接停止并进入 `finalize_workflow`。
2. 失败证据主要看哪里？
   答：先看 trace 里的 `Run workflow graph` 步骤和后面的 recovery event，再看 `tool_result.metadata.recovery_plan`。
3. 为什么最终 `tool_result.tool_name` 仍然应该是 `workflow`？
   答：因为外层暴露的是 workflow 这个能力表面，底层失败工具细节应该留在 metadata / trace 中，而不是直接打散顶层能力抽象。

最后运行：

```bash
python -m cli.main --input "Read README.md and then count lines." --classic-runtime --trace
```

回答：

1. 这次 trace 和默认 graph runtime 最大区别是什么？
   答：classic runtime 会直接显示 `Build workflow`、`Start workflow`、`Workflow step` 等经典步骤，而默认 graph runtime 会显示 `Run workflow graph` 和 graph 内节点链路。
2. 为什么保留这组对照很有学习价值？
   答：因为你可以非常直观地比较“同一个 workflow 需求”在 classic 主控和 graph orchestration 下的执行组织方式。

## 四、测试题

运行：

```bash
python -m unittest tests.test_agent tests.test_langgraph_workflow -v
```

回答：

1. 哪个测试验证 Agent 默认 workflow 已通过 graph 执行？
   答：`tests/test_agent.py` 里的 `test_workflow_run`。
2. 哪个测试验证 workflow 仍可显式退回 classic runtime？
   答：`tests/test_agent.py` 里的 `test_workflow_can_opt_out_of_graph_runtime`。
3. 哪个测试直接验证 graph 内 workflow step loop？
   答：`tests/test_langgraph_workflow.py` 里的 `test_rag_graph_executes_workflow_steps_inside_graph`。
4. 哪个测试验证 workflow 在 graph 内失败后会提前停止？
   答：`tests/test_langgraph_workflow.py` 里的 `test_rag_graph_workflow_failure_stops_remaining_steps`。

## 五、思考题

1. v33 做完以后，classic 主控还剩哪些更明显的“大块能力”？
   答：主要还剩 `tool_call` 和 `tool_loop`。它们都还没有并入统一 graph 主执行器。
2. 如果下一步先 graph 化 `tool_call`，它和 `workflow` 最大不同在哪里？
   答：`tool_call` 重点不在顺序 step，而在“LLM 选择工具 + 代码校验 + 单次执行结果回写”。它更像 graph 内一个选择-执行闭环，而不是线性 step plan。
3. 如果之后 graph 化 `tool_loop`，最该警惕什么？
   答：最该警惕 observation state 爆炸和停止条件失控。如果没有清晰的 loop state、重复调用保护和 final synthesis 边界，graph 版本的 tool loop 会很难调试。
4. 为什么 v33 不是“简单把 `_run_workflow()` 挪个位置”？
   答：因为这次真正改变的是 orchestration ownership。workflow 的计划、逐步执行、停止条件和最终汇总，现在已经属于 graph state 和 graph edge 的职责，而不是顶层 Python if/else 的职责。

## 六、验收标准

完成本练习后，你应该能说明：

- v33 的重点是让 LangGraph 开始真正接管多步 `workflow` orchestration。
- graph 化 workflow 的关键不是“能跑起来”，而是把 plan、step、status、failure 和 summary 变成 graph state。
- classic workflow 仍保留，但默认主路径已经迁移到 graph。

补充验证结果：

- `python -m unittest tests.test_agent tests.test_langgraph_workflow -v` 已通过。
- `python -m cli.main --input "Read README.md and then count lines." --trace` 已验证默认 workflow graph 路径。
- `python -m cli.main --input "Read not-exist.md and then count lines." --trace` 已验证 workflow graph 失败提前停止路径。
