# v32 练习：默认 LangGraph 主执行器

## 练习目标

理解为什么这次迭代不是“删除 router 改成全 graph”，而是把顶层 router 退化成 graph route hint，再让 LangGraph 成为默认主执行器。

## 一、理解题

1. 为什么 v32 还要保留顶层 `route_intent()`，而不是直接删掉？
   答：因为 v32 的目标是“迁移主执行器”，不是“一次性废弃旧路由逻辑”。保留 `route_intent()` 可以继续提供稳定、可测试的 route hint，也能为 classic runtime fallback 继续服务，降低从 if/else 主控迁移到 graph runtime 的风险。
2. `route hint` 解决了什么迁移问题？
   答：它解决的是“旧 router 很稳定，但新 graph 还没完全接管所有能力”这个过渡问题。通过 route hint，顶层 router 先给出 `action/tool_name/tool_input`，graph 再把这些提示翻译成 graph state，这样不用一次性重写所有路由判断。
3. 为什么 v32 只先把 `direct_answer` 和 `use_tool` 默认接入 graph？
   答：因为这两类路径覆盖了最常见的单步主执行链，而且迁移成本最可控。`workflow`、`tool_call`、`tool_loop` 都带有更复杂的状态和多步控制，如果这次一起并入 graph，会让阶段范围过大，不利于学习和回归。
4. 为什么 classic runtime 仍然值得保留？
   答：因为它既是回退手段，也是学习对照面。现在可以直接比较默认 graph runtime 和 `--classic-runtime` 的 trace 差异，看到“同一条用户请求，主执行器不同，但表层回答尽量兼容”的迁移过程。
5. 这一阶段的“兼容性目标”具体体现在哪些用户可见行为上？
   答：主要体现在两点。第一，像 `Read README.md...` 这类请求，最终答案仍然保持 `Result: read README.md...` 风格；第二，direct answer 仍然保持原来的 deterministic 回答风格。也就是说，底层主执行器变了，但用户表层体验尽量不被打坏。

## 二、源码定位题

1. `WorkspaceAgent` 默认 graph runtime 的开关参数定义在哪？
   答：定义在 `agent/core.py` 的 `WorkspaceAgent.__init__(..., use_graph_runtime: bool = True)`。
2. 哪个方法负责把 graph 运行结果映射回 classic `AgentRun` surface？
   答：`agent/core.py` 里的 `_apply_graph_runtime_result()`。
3. graph state 里新增了哪些 route hint 字段？
   答：新增了 `route_hint_action`、`route_hint_tool_name`、`route_hint_tool_input`。
4. 哪个函数负责把 route hint 翻译成 graph route/state？
   答：`integrations/langgraph_workflow.py` 里的 `_build_route_hint_state()`。
5. CLI 是通过哪个参数显式退回 classic runtime 的？
   答：通过 `cli/main.py` 新增的 `--classic-runtime`。

## 三、动手验证

运行：

```bash
python -m cli.main --input "Explain the difference between an agent and a chatbot." --trace
```

回答：

1. trace 中是否出现 `Run graph runtime`？
   答：出现。
2. `route=` 是什么？
   答：`route=direct_answer`。
3. 最终答案是否仍然保持原来的 deterministic direct answer 风格？
   答：是，最终仍然输出 `main difference`、`Reason:`、`In this project:` 这类原有 deterministic 结构。

再运行：

```bash
python -m cli.main --input "Read README.md and summarize the project learning goals." --trace
```

回答：

1. 这次是否默认进入 graph runtime？
   答：是，trace 中会出现 `Run graph runtime: route=read_file; ... planner=router_wrapped`。
2. 最终答案是否仍然是 `Result: read README.md...` 风格？
   答：是，虽然底层已经走 graph runtime，但最终回答仍然保持 `Result: read README.md.` 这类 classic surface 风格。

最后运行：

```bash
python -m cli.main --input "Read README.md and summarize the project learning goals." --classic-runtime --trace
```

回答：

1. trace 中是否还出现 `Run graph runtime`？
   答：不会出现。
2. 这次和默认 runtime 的主要差异在哪里？
   答：主要差异在执行轨迹。默认 runtime 会记录 `Run graph runtime`，而 classic runtime 会直接记录 `Run tool`。用户最终看到的回答基本兼容，但 trace 能清楚看出底层主执行器不同。

## 四、测试题

运行：

```bash
python -m unittest tests.test_agent tests.test_langgraph_workflow -v
```

回答：

1. 哪个测试验证 Agent 默认 direct answer 已通过 graph runtime？
   答：`tests/test_agent.py` 里的 `test_agent_direct_answer`。
2. 哪个测试验证可以显式退回 classic runtime？
   答：`tests/test_agent.py` 里的 `test_agent_can_opt_out_of_default_graph_runtime`。
3. 哪个测试继续验证显式 `Use LangGraph ...` 路径？
   答：例如 `tests/test_agent.py` 里的 `test_agent_runs_langgraph_search`，以及 `tests/test_langgraph_workflow.py` 里的显式 graph 测试。

## 五、思考题

1. route hint 是不是长期架构终点？为什么？
   答：不是。它更像一个迁移期架构。长期更合理的状态应该是 graph 自己成为统一 orchestration runtime，而顶层 router 要么继续弱化成 very thin wrapper，要么只保留少量 fallback 责任。
2. 如果以后要把 `tool_loop` 也并入 graph，最麻烦的状态会是什么？
   答：最麻烦的是多轮 observation 状态和停止条件管理。`tool_loop` 不只是一次工具调用，它还要保存每一轮 selection、observation、重复调用保护、最大步数控制和 final synthesis，这些都需要更完整的 graph state。
3. 为什么“用户可见答案兼容”对这次迁移很重要？
   答：因为这次迭代的重点是底层主执行器替换，不是重新定义产品行为。如果迁移后用户直接感知到大量回答格式变化，就很难判断问题到底来自 graph 迁移、工具调用、还是文案层变化。保持表层兼容，才能把学习重点放在运行时迁移本身。
4. 下一阶段如果继续 graph 化，优先应该并入 `workflow`、`tool_call` 还是 `tool_loop`？为什么？
   答：我更倾向先并入 `workflow`。因为它已经是显式多步结构，最容易映射成 graph node/edge；`tool_call` 次之；`tool_loop` 最复杂，涉及多轮状态和 synthesis，放在最后更稳。

## 六、验收标准

完成本练习后，你应该能说明：

- v32 的重点是“主执行器迁移”，不是“功能新增”。
- LangGraph 已经成为默认主执行器，但 classic runtime 仍保留为学习和回退手段。
- route hint 是一种过渡期架构，用于降低从 if/else 主控迁移到统一 graph runtime 的风险。

补充验证结果：

- `python -m unittest tests.test_agent tests.test_langgraph_workflow -v` 已通过。
- `python -m unittest discover -s tests -q` 结果为 `155` 个测试通过。
- `python -m cli.eval_runner` 结果为 `21/21` 通过。
