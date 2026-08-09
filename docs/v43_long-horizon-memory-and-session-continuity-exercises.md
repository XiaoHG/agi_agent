# Long-Horizon Memory and Session Continuity v43 练习

对应版本：v43  
主题：Long-Horizon Memory and Session Continuity  
用途：理解 Agent 如何在多次运行之间保持会话和任务连续性

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v43` 不能只继续扩展 checkpoint？
2. `SessionMemory` 和 `TaskMemory` 的职责差别是什么？
3. 为什么 resume 需要恢复 session / task ID？
4. `MemorySnapshot` 为什么要进入 trace？
5. 这一步为什么属于工业 Agent 的长任务基础设施？

## 练习 2：读 memory 链路

阅读：

- `agent/memory.py`
- `agent/core.py`
- `agent/persistence.py`
- `agent/replay.py`
- `cli/main.py`

请回答：

1. `AgentMemoryStore.update_from_trace()` 会同时更新哪两类对象？
2. `WorkspaceAgent.run()` 如何决定 session id 和 task id？
3. `format_checkpoint_summary()` 为什么要展示 session / task 信息？
4. replay summary 里为什么要标记 `has_memory`？
5. `cli.main` 为什么要提供单独的 memory 查看入口？

## 练习 3：动手验证

运行：

```bash
python -m cli.main \
  --input "Read README.md and summarize the project learning goals." \
  --session-id learning-session \
  --task-id readme-learning

python -m cli.main --session-id learning-session --show-session-memory
python -m cli.main --task-id readme-learning --show-task-memory
```

请记录：

1. checkpoint 摘要里是否出现 `Session ID` 和 `Task ID`？
2. session memory 里是否能看到 run count 和 active tasks？
3. task memory 里是否能看到 latest route 和 related tools？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么 task id 先采用规则推断，而不是一开始就做语义聚类？
2. 为什么本阶段先用本地 JSON memory store？
3. 如果后续要接外部 memory service，`v43` 最重要的基础价值是什么？

## 答案

### 练习 1：理解本阶段目标

1. `v43` 不能只继续扩展 checkpoint，因为 checkpoint 只描述单次运行快照，而 memory 要解决的是多次运行之间的持续累计。
2. `SessionMemory` 管会话连续性，`TaskMemory` 管具体任务连续性。
3. resume 需要恢复 session / task ID，因为真正的连续工作不只是重跑 route，还要继续原来的会话和任务。
4. `MemorySnapshot` 要进入 trace，是为了让 checkpoint、replay 和 CLI 都能读取同一份连续性状态。
5. 这一步属于工业 Agent 的长任务基础设施，因为跨轮次工作、长任务推进和历史状态复用都离不开它。

### 练习 2：读 memory 链路

1. `AgentMemoryStore.update_from_trace()` 会同时更新 `SessionMemory` 和 `TaskMemory`。
2. `WorkspaceAgent.run()` 会优先使用显式传入的 session/task id，其次使用 Agent 默认值，再退化到规则推断的 task id。
3. `format_checkpoint_summary()` 要展示 session / task 信息，是为了让单次运行快照也能说明自己属于哪条长期连续工作链。
4. replay summary 标记 `has_memory`，是为了比较不同 run 时连续性状态是否完整。
5. `cli.main` 提供单独的 memory 查看入口，是因为 memory 属于 Agent 能力，不应依赖人工直接翻 JSON 文件。

### 练习 3：动手验证

1. checkpoint 摘要里应当出现 `Session ID` 和 `Task ID`。
2. session memory 里应当能看到 run count 和 active tasks。
3. task memory 里应当能看到 latest route 和 related tools。

### 练习 4：工程取舍题

1. task id 先采用规则推断，是因为它实现简单、边界清晰、测试稳定，适合作为学习项目的第一版任务连续性模型。
2. 本阶段先用本地 JSON memory store，是因为目标是先打通结构和联动，而不是先引入外部依赖。
3. `v43` 最重要的基础价值是把 session/task continuity 的数据模型、持久化和 CLI 入口全部打通了，后续可以平滑替换成更强的 memory backend。

## 验证

```bash
python -m unittest tests.test_memory tests.test_persistence -v
python -m cli.main --session-id learning-session --show-session-memory
```
