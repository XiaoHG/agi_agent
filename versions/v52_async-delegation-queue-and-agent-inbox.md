# v52：Async Delegation Queue and Agent Inbox

## 本阶段目标

把 `v51` 的 runtime foundation 从“同步执行证据”推进到“异步任务收发证据”。

`v51` 已经解决了：

- runtime session
- context boundary
- message envelope
- state transition
- trace / checkpoint / graph runtime integration

但它还没有正式回答下面这些 async runtime 问题：

- 委派任务进入哪里等待处理
- 子 Agent 从哪里接收待办任务
- 谁在什么时候认领了任务
- 任务是 completed、failed 还是 blocked
- 这些 async 事实如何进入 runtime events、checkpoint 和 graph runtime

`v52` 的目标就是把这些异步协作对象补齐。

## 本阶段在工业 Agent 中的位置

工业级多 Agent runtime 不能只有 session 和消息，还必须把“任务如何挂起、接收、认领和回传”做成正式运行对象。

否则系统虽然已经有 runtime foundation，但仍然只是“同步顺序执行 + 更完整的证据”，还不能进入真正的协作调度阶段。

所以 `v52` 的定位不是做并发系统，也不是做远程消息中间件，而是先把 async delegation queue、agent inbox / outbox 和 claim lifecycle 做成最小可运行模型。

## 本阶段解决的问题

- 给 subagent collaboration 增加正式的 delegation queue 快照
- 把每个子 Agent 的 inbox / outbox 明确结构化
- 把 task claim / complete / fail / block 做成正式证据
- 把 pending / running / blocked / completed / failed 状态接入 runtime transition
- 把 async delegation 证据同步接入 classic runtime、graph runtime、trace 和 checkpoint

## 本阶段新增能力

### 1. Async delegation queue model

新增：

- `SubagentQueueItem`
- `SubagentInboxEntry`
- `SubagentOutboxEntry`
- `SubagentClaimRecord`

这让多 Agent 协作不再只是“执行过哪些 delegation”，而是第一次具备了 async-ready 的任务收发视角。

### 2. Inbox / outbox snapshot

`SubagentRuntimeSession` 现在除了 messages 和 transitions，还会保存：

- `queue_items`
- `inbox_entries`
- `outbox_entries`
- `claim_records`

这意味着 runtime session 不再只记录“发生过什么消息”，还开始记录“任务在队列和邮箱中的位置”。

### 3. Task claim lifecycle

`build_runtime_session()` 现在会把每个 delegation 映射为：

- 一个 queue item
- 一个 inbox entry
- 一个 claim record
- 一个 outbox entry

这样任务从 pending 到 running，再到 completed / failed / blocked 的路径第一次具备了明确的运行证据。

### 4. Blocked path evidence

`execute_collaboration_plan()` 现在除了 completed 和 failed，还能稳定产出 blocked 场景：

- 通过 `blocked` / `offline` / `unavailable` 关键词触发 blocked path
- runtime session 进入 `blocked`
- coding agent 的 inbox / outbox / claim 都保留 blocked 证据

这一步是后续 `v53` 审批流和 `v54` 长任务生命周期的前置基础。

### 5. Runtime integration enhancement

增强：

- `agent/tools.py` 对失败和 blocked path 输出更明确的 recovery metadata
- `agent/events.py` 新增 `delegation_queue` event
- `cli/collaboration_demo.py` 增加 `--queue-json`、`--inbox-role`、`--outbox-role`
- `integrations/langgraph_workflow.py` 继续保留完整 `subagent_runtime`

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `subagent/team.py` | 新增 queue/inbox/outbox/claim 数据模型，并把 runtime session 升级为 async delegation snapshot |
| `subagent/__init__.py` | 导出新的 async delegation runtime 对象 |
| `agent/tools.py` | 区分 delegation failed 和 delegation blocked recovery metadata |
| `agent/events.py` | 新增 `delegation_queue` event |
| `cli/collaboration_demo.py` | 增加 queue / inbox / outbox 的 JSON 检查入口 |
| `tests/test_collaboration.py` | 增加 blocked inbox path、queue CLI 验证和 runtime 断言 |
| `tests/test_events.py` | 增加 delegation queue event 测试 |
| `tests/test_langgraph_workflow.py` | 增加 graph runtime 保留 queue / claim 证据测试 |
| `subagent/README.md` | 更新 subagent runtime 的当前能力说明 |
| `docs/current-learning-state.md` | 更新当前阶段状态和下一步建议 |

## 核心实现说明

### 1. 为什么 `v52` 先做 queue / inbox / outbox，而不是直接做并发

因为真正的异步协作第一步不是“开线程”，而是先把任务对象、收件箱和认领动作建模清楚。

如果这些对象都没有正式结构，后续就很难继续做：

- 审批挂起
- 任务续跑
- stuck task detection
- 外部消息中间件接入

### 2. 为什么 claim record 很关键

因为在工业 runtime 里，“任务存在”和“任务开始运行”是两个不同事实。

`SubagentClaimRecord` 的作用是把这条边界显式记录下来：

- 哪个 role claim 了哪个 queue item
- claim 后是 completed、failed 还是 blocked
- 为什么进入当前状态

这对审计、恢复和长期任务监控都很重要。

### 3. 为什么 blocked 也必须是正式状态

因为工业 Agent 运行中，很多任务不是直接 failed，而是：

- 等待依赖
- 等待人工确认
- 等待资源恢复

如果系统只有 completed / failed 两种终态，后续审批流和生命周期管理就会缺少真实的中间状态。

### 4. 为什么 `delegation_queue` event 有价值

因为 `delegation_runtime` event 更偏 session 级信息，而 `delegation_queue` event 更偏 async delegation 的任务收发快照：

- queue 有多少任务
- inbox 有多少待处理项
- outbox 有多少回传项
- claim records 有多少条

这让 trace 和 checkpoint 更容易直接定位“任务卡在哪个收发层面”。

## 运行示例

执行正常 async delegation runtime：

```bash
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --runtime-json --queue-json
```

查看 blocked inbox 场景：

```bash
python -m cli.collaboration_demo --task "Implement a blocked offline code change." --execute-subagents --inbox-role coding_agent --outbox-role coding_agent
```

通过默认 Agent runtime 运行：

```bash
python -m cli.main --input "Execute subagent collaboration for a code review." --trace
```

## 验证命令

```bash
python -m unittest tests.test_collaboration tests.test_events tests.test_langgraph_workflow -v
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --runtime-json --queue-json
python -m cli.collaboration_demo --task "Implement a blocked offline code change." --execute-subagents --inbox-role coding_agent --outbox-role coding_agent
python -m cli.main --input "Execute subagent collaboration for a code review." --trace
```

## 当前边界

- 当前 async delegation 仍然是 deterministic 模拟，不是真正的并发或分布式 runtime
- queue / inbox / outbox 目前保存在本次 runtime session 中，还没有独立持久化存储或远程 transport
- blocked 目前是教学型确定性触发，不是来自真实资源依赖或审批服务
- claim record 目前只描述最小生命周期，还没有任务超时、重试和 lease 语义

## 下一步建议

`v52` 之后最自然的下一步是 `v53: Human Approval and Risk-Control Workflow`。

因为现在已经有了：

- runtime session
- message envelope
- state transition
- delegation queue
- agent inbox / outbox
- task claim / blocked 证据

接下来就可以继续解决“什么时候任务必须停下来等待人工审批，以及审批后如何 reject / revise / resume”的工业控制问题。
