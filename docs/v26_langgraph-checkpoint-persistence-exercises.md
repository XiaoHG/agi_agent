# v26 练习：LangGraph Checkpoint and Recoverable Run Persistence

## 练习 1：什么信息必须持久化？

回答：

1. 一个 LangGraph run 最少应该保存哪些字段？
2. 哪些字段适合落盘，哪些字段只适合内存？
3. 为什么 `runtime_events` 不能替代完整 state？

答案：

1. 最少要保存 run id、用户输入、route、steps、tool 状态、error/recovery 信息、最终 answer，以及能复盘执行过程的 trace。
2. 适合落盘的是 JSON-ready 的稳定字段，比如 route、steps、tool_result、tool_error、recovery_plan、runtime_events、answer；只适合内存的是临时对象、LLM client、函数闭包、graph 编译对象等。
3. 因为 `runtime_events` 只是“发生了什么”的事件视图，不一定包含恢复一次 run 所需的全部状态边界；它能回放过程，但不能单独重建完整上下文。

## 练习 2：checkpoint 和 trace 的关系是什么？

回答：

1. trace 和 checkpoint 的目标分别是什么？
2. 两者可以共用哪些数据？
3. 如果只保留 trace，不保留 checkpoint，会少什么能力？

答案：

1. trace 主要用于观察和调试，checkpoint 主要用于保存和恢复运行状态。
2. 两者可以共用 run id、route、steps、tool_result、tool_error、recovery_plan、runtime_events 这些结构化数据。
3. 只保留 trace，会少掉“从上一次运行继续恢复”“从文件读取最近一次运行”“跨会话接续分析”的能力。

## 练习 3：恢复和回放有什么区别？

回答：

1. replay 是重新生成结果，还是恢复原始状态？
2. 恢复失败时，应该返回什么信息？
3. 哪些失败适合自动恢复，哪些必须人工确认？

答案：

1. replay 更接近“重新走一遍记录过的过程”或“从保存点重建状态”，不是重新让模型自由发挥生成一个新答案。
2. 恢复失败时，应该返回失败原因、失败来源、当前状态、下一步安全动作，以及能帮助人继续排查的上下文。
3. 本地文件缺失、路径错误、简单格式问题通常可以自动恢复或提示修正；权限、外部依赖、写入动作、网络调用、模型不确定修复等场景必须人工确认。

## 练习 4：结合当前项目举例

回答：

1. `recover_tool_failure` 的结果适合怎样保存？
2. `RecoveryPlan` 适合怎样落盘？
3. `RuntimeEvent` 适合怎样用于复盘？

答案：

1. `recover_tool_failure` 的结果适合保存在 checkpoint 的 `trace`、`tool_result.metadata` 和 `trace_text` 里，这样既能程序读取也能人类阅读。
2. `RecoveryPlan` 适合以 JSON-ready dict 落盘，因为它是结构化恢复对象，后续可以直接被 eval、CLI、replay 使用。
3. `RuntimeEvent` 适合用于复盘事件序列，帮助回答“运行中按什么顺序发生了什么、失败点在哪里、恢复计划是怎么生成的”。

## 练习 5：设计思考

回答：

1. 如果给 `WorkspaceAgent` 增加 run history，你会放在哪一层？
2. 如果要支持 CLI 查看最近一次 graph run，你会先保存什么？
3. 如果要从文件恢复一次 run，你最担心什么问题？

答案：

1. 我会放在 `agent/` 的持久化层，而不是 CLI 或 graph node 里，因为 run history 是核心运行能力，不是展示逻辑。
2. 我会先保存 `run_id`、`route`、`steps`、`trace`、`trace_text` 和 `answer`，因为这些字段最小就能支撑查看和复盘。
3. 我最担心的是恢复边界不一致：比如 state 里塞了不可序列化对象、不同版本字段不兼容、或者恢复时缺少足够的上下文导致 replay 结果漂移。
