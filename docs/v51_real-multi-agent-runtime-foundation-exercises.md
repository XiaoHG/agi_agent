# Real Multi-Agent Runtime Foundation v51 练习

对应版本：v51  
主题：Real Multi-Agent Runtime Foundation  
用途：理解多 Agent 为什么要从“可执行协议”继续推进到“正式 runtime session”

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v50` 做完以后，还不能说项目已经拥有真实多 Agent runtime？
2. `SubagentRuntimeSession` 主要解决什么问题？
3. `SubagentMessageEnvelope` 和 `SubagentStateTransition` 分别代表什么？
4. 为什么 `SubagentContextBoundary` 必须显式记录 `allowed_inputs`、`blocked_inputs` 和 `expected_outputs`？
5. 为什么 `v51` 是 runtime foundation，而不是 async runtime？

## 练习 2：读 runtime 执行链路

阅读：

- `subagent/team.py`
- `agent/tools.py`
- `agent/events.py`
- `integrations/langgraph_workflow.py`
- `tests/test_collaboration.py`

请回答：

1. `execute_collaboration_plan()` 在 `v51` 中比 `v50` 多出了什么结构化产物？
2. `build_runtime_session()` 如何把 delegation / execution / return 串成 session 级证据？
3. 为什么 `execute_subagents` metadata 现在要同时带 `subagent_delegation` 和 `subagent_runtime`？
4. `delegation_runtime` event 和 `delegation_execution` event 的区别是什么？
5. graph runtime 为什么也必须保留 `subagent_runtime`？

## 练习 3：动手验证

运行：

```bash
python -m unittest tests.test_collaboration tests.test_events tests.test_langgraph_workflow -v
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --runtime-json
python -m cli.main --input "Execute subagent collaboration for a code review." --trace
```

请记录：

1. 文本输出中是否出现 `Runtime session:`？
2. JSON 输出中是否出现 `messages` 和 `transitions`？
3. trace 的 runtime events 中是否出现 `delegation_runtime`？
4. graph runtime 结果中是否保留 `subagent_runtime.status`？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么多 Agent 工程里“会话”比“角色数量”更重要？
2. 为什么 message envelope 是后续异步队列的前置基础？
3. 为什么 state transition 记录对于长期任务、审批和恢复都很关键？
4. 为什么 `v51` 不应该直接把异步队列、审批流和长任务一起塞进一个版本？

## 答案

### 练习 1：理解本阶段目标

1. 因为 `v50` 主要解决的是“协议是否完整”，比如 delegation、handoff、execution、return 和 recovery 是否都有正式记录；但它还没有正式表达运行会话、消息边界和状态迁移，所以还不能算真实 runtime。
2. `SubagentRuntimeSession` 解决的是“这次多 Agent 协作到底作为哪个运行会话存在”的问题。它统一保存 session_id、parent role、child roles、active role、current delegation、context boundary、messages 和 transitions，让协作过程第一次具备 session 级结构。
3. `SubagentMessageEnvelope` 表示运行中角色之间真正交换的消息单元，重点是 from/to/type/summary/reference；`SubagentStateTransition` 表示 runtime 从一个状态进入另一个状态的正式记录，重点是 from_state、to_state、actor 和 reason。
4. 因为工业 runtime 不能只知道“谁在跑”，还要知道“它允许接收什么、必须拒绝什么、应该产出什么”。这些边界不显式记录，后续就很难做安全恢复、审批判断和上下文隔离。
5. 因为 `v51` 只把运行基础对象补齐，并没有实现异步消息收发、任务认领、pending/running/blocked 调度等机制，所以它是 foundation，不是 async runtime。

### 练习 2：读 runtime 执行链路

1. `v51` 在 `execute_collaboration_plan()` 里除了 handoff、execution、return 之外，又增加了 runtime session，包括 context boundary、message list 和 state transition list。
2. `build_runtime_session()` 会遍历 delegation、execution 和 return，先建立 session，再把每次 delegation / handoff / return 变成 message envelope，把执行前后状态变化变成 transition，最后给出 completed 或 failed 的 terminal state。
3. 因为这两个对象解决的问题不同：`subagent_delegation` 更偏“协作协议和任务契约”，`subagent_runtime` 更偏“实际运行会话和状态流转”。两者都要保留，trace、checkpoint 和后续审计才完整。
4. `delegation_execution` 关注的是“哪些 delegated tasks 执行了、状态如何”；`delegation_runtime` 关注的是“整个 session 中有多少消息、多少状态迁移、最终 runtime status 是什么”。一个偏子任务执行证据，一个偏会话级运行证据。
5. 因为项目默认主执行器已经是 graph runtime。如果 graph runtime 不保留 `subagent_runtime`，那多 Agent runtime foundation 就只在 classic runtime 生效，checkpoint、trace 和 graph 路径会出现信息断层。

### 练习 3：动手验证

1. 是，`--execute-subagents` 的文本输出中应出现 `Runtime session:`。
2. 是，`--runtime-json` 输出中应出现 `messages` 和 `transitions`。
3. 是，`python -m cli.main --trace` 的 runtime events 中应出现 `delegation_runtime`。
4. 是，graph runtime 结果中应保留 `subagent_runtime.status`，并且正常场景应是 `completed`。

### 练习 4：工程取舍题

1. 因为真正的工业问题不是“系统里有几个角色”，而是“这次协作属于哪个会话、当前停在哪个状态、下一个消息应该发给谁”。这些都是 session 级问题，不是角色数量问题。
2. 因为异步队列的本质就是挂起、传递和消费消息。如果现在不先把消息变成正式 envelope，后面就没有稳定的数据结构来承接 inbox/outbox、task claim 和异步重放。
3. 因为长期任务、审批和恢复都依赖状态机。只有知道系统从哪个状态进入哪个状态、为什么变成 failed / blocked，后续才能决定是否继续、暂停、审批或回退。
4. 因为那样会把 runtime foundation、async scheduling、approval governance 和 lifecycle management 混成一个大杂烩版本，既难讲清楚，也难验证，更不利于学习和后续迭代拆分。工业项目更适合按基础层逐层推进。
