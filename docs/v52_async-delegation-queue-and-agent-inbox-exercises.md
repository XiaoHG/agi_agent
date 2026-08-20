# Async Delegation Queue and Agent Inbox v52 练习

对应版本：v52  
主题：Async Delegation Queue and Agent Inbox  
用途：理解多 Agent runtime 为什么要从 runtime foundation 继续推进到 async delegation queue、agent inbox / outbox 和 task claim

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v51` 做完以后，还不能说项目已经拥有真正的异步多 Agent 协作能力？
2. `SubagentQueueItem`、`SubagentInboxEntry`、`SubagentOutboxEntry` 和 `SubagentClaimRecord` 分别解决什么问题？
3. 为什么 async delegation 的第一步不是并发，而是 queue / inbox / outbox / claim 建模？
4. 为什么 blocked 状态在工业 Agent 中不能被简单视为 failed？
5. 为什么 `v52` 应该先做收发模型，而不是直接跳去做审批流？

## 练习 2：读 async delegation 执行链路

阅读：

- `subagent/team.py`
- `agent/tools.py`
- `agent/events.py`
- `cli/collaboration_demo.py`
- `tests/test_collaboration.py`

请回答：

1. `build_runtime_session()` 在 `v52` 中比 `v51` 多出了什么结构化产物？
2. `execute_collaboration_plan()` 是如何区分 completed、failed 和 blocked 的？
3. `delegation_runtime` event 和 `delegation_queue` event 的区别是什么？
4. 为什么 `cli.collaboration_demo` 要增加 `--queue-json`、`--inbox-role` 和 `--outbox-role`？
5. `agent/tools.py` 为什么要区分 `delegation_failed` 和 `delegation_blocked`？

## 练习 3：动手验证

运行：

```bash
python -m unittest tests.test_collaboration tests.test_events tests.test_langgraph_workflow -v
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --runtime-json --queue-json
python -m cli.collaboration_demo --task "Implement a blocked offline code change." --execute-subagents --inbox-role coding_agent --outbox-role coding_agent
python -m cli.main --input "Execute subagent collaboration for a code review." --trace
```

请记录：

1. `--runtime-json` 输出中是否出现 `queue_items`、`inbox_entries`、`outbox_entries` 和 `claim_records`？
2. blocked 场景下 `coding_agent` 的 inbox entry 是否为 `blocked`？
3. runtime events 中是否同时出现 `delegation_runtime` 和 `delegation_queue`？
4. graph runtime 结果中是否保留 `subagent_runtime.queue_items` 和 `subagent_runtime.claim_records`？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么 queue item 和 message envelope 要同时存在，而不是只保留一种结构？
2. 为什么 claim record 对后续审批流和长期任务生命周期都很重要？
3. 为什么 `v52` 先做 deterministic async-ready model 也有学习价值？
4. 为什么工业级多 Agent 不能只靠“角色切换”来表达异步协作？

## 答案

### 练习 1：理解本阶段目标

1. 因为 `v51` 主要解决的是 session、message、state 和 context 这些 runtime foundation 问题，但还没有正式表达任务进入哪里等待、谁来接收、谁来认领、什么时候 blocked，所以还不能算真正的异步协作模型。
2. `SubagentQueueItem` 解决“任务在队列中如何存在”；`SubagentInboxEntry` 解决“某个子 Agent 看到了哪些待处理任务”；`SubagentOutboxEntry` 解决“子 Agent 完成、失败或 blocked 后向外回传了什么”；`SubagentClaimRecord` 解决“谁在什么时候正式认领了任务并使它进入运行状态”。
3. 因为并发只是执行方式，queue / inbox / outbox / claim 才是任务生命周期的核心对象。对象边界不清楚，并发只会把问题放大，不能真正提升可恢复性和可审计性。
4. 因为 blocked 常常表示任务还可以继续，只是当前被依赖、资源、权限或人工决策卡住。它不是彻底失败，而是一个必须被系统显式记录和后续处理的中间状态。
5. 因为审批流依赖“任务现在挂在哪、谁认领了、为什么停住、如何恢复”这些信息。如果 `v52` 不先把 async delegation 的任务收发模型做好，`v53` 审批流就会缺少可靠的运行载体。

### 练习 2：读 async delegation 执行链路

1. `build_runtime_session()` 在 `v52` 中比 `v51` 多出了 `queue_items`、`inbox_entries`、`outbox_entries` 和 `claim_records`。它不再只描述消息和状态，还开始描述任务在异步收发层中的快照。
2. `execute_collaboration_plan()` 通过输入关键词做确定性分支：普通实现请求走 completed，`ambiguous` / `unclear` / `underspecified` 走 failed，`blocked` / `offline` / `unavailable` 走 blocked。随后把这个状态同步写入 execution、return 和 runtime session。
3. `delegation_runtime` 更偏 session 级视角，重点是 messages、transitions 和 session status；`delegation_queue` 更偏 async task-dispatch 视角，重点是 queue、inbox、outbox 和 claim 的数量与快照。一个关注“会话怎么流动”，一个关注“任务怎么收发”。
4. 因为 `v52` 的学习重点已经不是单纯看文本执行结果，而是要直接检查 async delegation 证据是否存在。`--queue-json` 用于整体看 queue/inbox/outbox/claim；`--inbox-role` 和 `--outbox-role` 用于按角色聚焦排查某个 Agent 的收发状态。
5. 因为 failed 和 blocked 的后续处理不同。`delegation_failed` 更偏请求本身或执行结果已经失败；`delegation_blocked` 更偏任务还可以继续，只是当前必须暂停等待恢复或人工介入。后续审批、恢复和生命周期策略会依赖这个区分。

### 练习 3：动手验证

1. 是，`--runtime-json` 输出中应出现 `queue_items`、`inbox_entries`、`outbox_entries` 和 `claim_records`。
2. 是，blocked 场景下 `coding_agent` 的 inbox entry 应为 `blocked`，并且对应 queue item、outbox entry 和 claim record 也应保留 blocked 状态。
3. 是，`python -m cli.main --trace` 的 runtime events 中应同时出现 `delegation_runtime` 和 `delegation_queue`。
4. 是，graph runtime 结果中应保留 `subagent_runtime.queue_items` 和 `subagent_runtime.claim_records`，说明 graph 路径没有丢失 async delegation 证据。

### 练习 4：工程取舍题

1. 因为它们解决的层次不同：message envelope 关注角色之间交换了什么消息；queue item 关注任务在调度链路里处于什么位置。只保留其中一种，会丢失通信层或任务层的一部分事实。
2. 因为审批流和长期任务管理都需要知道“任务是否已经被谁接手”。没有 claim record，系统就很难区分“任务还没开始”还是“任务已经开始但现在被卡住”。
3. 因为 deterministic async-ready model 先把数据结构、状态边界和验证入口讲清楚，学习者可以先理解运行机制，再逐步演进到真正并发或分布式版本。这比一上来堆复杂调度器更适合工程学习。
4. 因为角色切换只表达“谁做事”，不能表达“任务在哪里等待、是否被认领、是否 blocked、结果从哪条回传链路回来”。工业级异步协作必须有更细的任务收发和状态治理对象。
