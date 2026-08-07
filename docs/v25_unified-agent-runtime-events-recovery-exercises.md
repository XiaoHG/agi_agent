# v25 练习：统一 Agent 运行事件与恢复模型

## 练习 1：解释 `RecoveryPlan`

阅读 `agent/recovery.py`，回答：

1. `RecoveryPlan` 为什么需要同时包含 `source_type` 和 `source_name`？
2. `failure_type` 和 `reason` 的职责有什么区别？
3. 为什么 `RecoveryPlan` 要提供 `to_dict()` 和 `to_text()` 两种导出方式？

答案：

1. `source_type` 用来区分失败来自 tool、skill 还是 exception，`source_name` 用来标记具体来源名称。两者一起才能同时回答“哪一类失败”与“具体是哪个对象失败”。
2. `failure_type` 是标准化分类，用于后续策略选择；`reason` 是原始失败原因，用于排查和展示。
3. `to_dict()` 服务于 trace、eval、checkpoint 和 JSON 传输；`to_text()` 服务于 CLI 输出和人工阅读。

## 练习 2：对比普通 tool recovery 和 Skill recovery

阅读：

- `agent/recovery.py`
- `integrations/langgraph_workflow.py`

回答：

1. `build_tool_recovery_plan()` 主要依赖哪些输入？
2. `build_skill_recovery_plan()` 为什么需要读取 `skill_run.steps`？
3. 普通 tool failure 和 Skill failure 的上下文差异是什么？

答案：

1. 它主要依赖 `tool_name`、`tool_input` 和 `reason`，因为普通 tool recovery 的关键信息就是调用了什么工具、传了什么参数、为什么失败。
2. 因为 Skill failure 往往不是单一工具失败，而是多个 step 中某一步失败；读取 `skill_run.steps` 才能定位失败 step、恢复工具名、输入和失败原因。
3. 普通 tool failure 的上下文较薄，通常只有单次调用信息；Skill failure 的上下文更厚，包含 skill 名称、step 序列、已完成步数、失败步和失败工具。

## 练习 3：解释 `RuntimeEvent`

阅读 `agent/events.py`，回答：

1. `RuntimeEvent` 解决了原有 trace 的什么问题？
2. `build_runtime_events()` 当前会生成哪些事件类型？
3. 为什么 runtime events 不直接替代 `AgentStep`？

答案：

1. 它把分散在 `AgentStep`、tool metadata、recovery plan 和 error 字符串里的信息统一成稳定事件流，方便程序消费和后续扩展。
2. 当前会生成 `step`、`graph`、`recovery`、`skill` 和 `error` 事件。
3. `AgentStep` 记录的是 Agent 执行过程中的高层步骤，`RuntimeEvent` 是从已有 trace 派生出的统一事件视图；两者职责不同，不能互相完全替代。

## 练习 4：跟踪 `WorkspaceAgent.to_trace_dict()`

阅读 `agent/core.py` 中的 `format_trace()` 和 `to_trace_dict()`，回答：

1. `runtime_events` 是从哪些数据构造出来的？
2. 当 LangGraph 产生 `recovery_plan` 时，它如何进入 `runtime_events`？
3. 文本 trace 和结构化 trace 分别适合什么场景？

答案：

1. 它由 `run.steps`、`run.tool_result.metadata` 和 `run.tool_error` 构造。
2. `run.tool_result.metadata` 中的 `recovery_plan` 会被 `build_runtime_events()` 识别，并转换成 `recovery` 事件。
3. 文本 trace 更适合人工排查和 CLI 阅读；结构化 trace 更适合测试、eval、持久化和程序化分析。

## 练习 5：解释 graph state 的序列化边界

阅读 `integrations/langgraph_workflow.py`，回答：

1. 为什么 `RAGGraphState["recovery_plan"]` 保存的是 dict，而不是 `RecoveryPlan` 实例？
2. 这个设计对后续 checkpoint、replay、eval 有什么好处？
3. 如果未来要把 graph state 写入 JSON 文件，这个设计能减少什么问题？

答案：

1. 因为 graph state 需要保持可序列化和跨边界传输能力，dict 比 dataclass 更适合直接进入 state。
2. 它让 checkpoint 和 replay 更容易落盘、读取和比较，也让 eval 更容易断言状态字段。
3. 可以减少自定义序列化、反序列化和对象兼容问题，避免把 Python 对象直接塞进 JSON 状态。

## 练习 6：手动验证普通 tool failure recovery

运行：

```bash
python -m cli.main --input "Use LangGraph to read not-exist.md." --trace
```

观察并记录：

1. Graph steps 是否包含 `recover_tool_failure`？
2. 输出中是否包含 `Tool recovery plan`？
3. trace 中是否出现 `[Runtime Events]`？
4. runtime events 中是否出现 `recovery` event？

答案：

1. 是，`call_tool` 失败后会进入 `recover_tool_failure`，再进入 `finalize`。
2. 是，失败恢复会把恢复计划文本输出到最终结果中。
3. 是，`format_trace()` 会追加 `[Runtime Events]` 区块。
4. 是，`build_runtime_events()` 会把 `recovery_plan` 转成 `recovery` 事件。

## 练习 7：手动验证测试与 eval

运行：

```bash
python -m unittest tests.test_recovery tests.test_events tests.test_langgraph_workflow tests.test_agent -v
python -m unittest discover -s tests -v
python -m cli.eval_runner
```

记录：

1. 本阶段相关测试是否全部通过？
2. 全项目测试是否全部通过？
3. eval 是否全部通过？
4. 如果测试失败，你会优先从哪个文件开始定位？为什么？

答案：

1. 是，本阶段相关测试已通过。
2. 是，全项目测试已通过。
3. 是，eval 全部通过。
4. 我会先看失败对应能力的直接实现文件，例如 recovery 问题先看 `agent/recovery.py`，事件问题先看 `agent/events.py`，graph 问题先看 `integrations/langgraph_workflow.py`，因为这些文件最靠近行为源头。

## 练习 8：下一阶段设计思考

基于 v25，回答：

1. 如果要支持 checkpoint，最应该持久化哪些字段？
2. `RuntimeEvent` 是否足够恢复一次 run？如果不够，还缺什么？
3. 恢复计划什么时候可以自动执行，什么时候必须等待人工确认？

答案：

1. 至少应持久化 `run_id`、用户输入、route、steps、tool_call、tool_loop_result、tool_result、tool_error、recovery_plan、runtime_events 和最终 answer。
2. 不够。`RuntimeEvent` 能帮助回放过程，但恢复一次 run 还需要完整 state、路由决策、工具输入输出、错误上下文和当前执行阶段。
3. 当失败属于可确定的本地问题、风险低且动作可逆时可以自动执行；当涉及权限、外部依赖、文件写入、网络调用或不确定修复时，应等待人工确认。
