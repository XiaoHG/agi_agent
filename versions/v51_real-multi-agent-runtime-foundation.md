# v51：Real Multi-Agent Runtime Foundation

## 本阶段目标

把 `v50` 的“可执行委派协议”继续推进成真正的多 Agent runtime 基础层。

`v50` 已经解决了：

- delegation
- handoff
- execution
- return
- recovery_handoff

但它还没有正式回答下面这些 runtime 问题：

- 父 Agent 和子 Agent 之间到底处于哪个 session 中运行
- 子任务交接时到底传递什么消息封装
- 当前激活角色是谁
- 执行状态是如何变化的
- 这些运行事实如何进入 trace / checkpoint / graph runtime

`v51` 的目标就是把这些 runtime 基础对象补齐。

## 本阶段在工业 Agent 中的位置

工业级多 Agent 系统不能只会“规划谁做什么”，还必须能表达：

- 当前运行会话是谁发起的
- 消息从谁发给谁
- 当前上下文边界是什么
- 状态从 created 到 completed / failed 是怎么迁移的

否则系统虽然看起来有多个角色，但本质上仍然只是“带角色标签的顺序函数”。

所以 `v51` 的定位不是再做一个新 demo，而是把多 Agent 从“协议层”推进到“runtime foundation 层”。

## 本阶段解决的问题

- 给 subagent collaboration 补充正式的 runtime session 数据模型
- 把 parent / child context boundary 结构化
- 把角色间传递的信息变成 message envelope
- 把执行过程中的状态变化变成 state transition
- 把 runtime session 同步接入 classic runtime、graph runtime、trace 和 checkpoint

## 本阶段新增能力

### 1. Runtime session model

新增：

- `SubagentRuntimeSession`
- `SubagentContextBoundary`
- `SubagentMessageEnvelope`
- `SubagentStateTransition`

这让多 Agent 协作现在不只是“发生过 delegation”，而是有了正式的运行会话对象。

### 2. Execution state machine evidence

`execute_collaboration_plan()` 现在除了 handoff / execution / return 之外，还会产出：

- session status
- active role
- current delegation
- message list
- transition list

这意味着协作过程第一次具备了可回放的 runtime 状态流转证据。

### 3. Parent / child context boundary

`v51` 明确记录：

- parent role
- active role
- allowed inputs
- blocked inputs
- expected outputs

这样子 Agent 的运行上下文不再是隐含在注释或推理里，而是正式进入数据结构。

### 4. Runtime integration

增强：

- `agent/tools.py` 会同时返回 `subagent_delegation` 和 `subagent_runtime`
- `agent/core.py` trace dict 增加 `subagent_runtime`
- `agent/events.py` 新增 `delegation_runtime` event
- `agent/persistence.py` 把 `subagent_runtime` 进入 checkpoint metadata
- `integrations/langgraph_workflow.py` graph runtime 保留 `subagent_runtime`

### 5. CLI demo enhancement

增强：

- `cli.collaboration_demo --runtime-json`

现在可以直接查看 runtime session JSON：

```bash
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --runtime-json
```

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `subagent/team.py` | 新增 runtime session、message envelope、context boundary、state transition |
| `subagent/__init__.py` | 导出新的 runtime foundation 数据模型 |
| `agent/tools.py` | `execute_subagents` 返回 `subagent_runtime` metadata |
| `agent/events.py` | 新增 `delegation_runtime` event |
| `agent/core.py` | trace dict 暴露 `subagent_runtime` |
| `agent/persistence.py` | checkpoint metadata 保留 `subagent_runtime` |
| `integrations/langgraph_workflow.py` | graph runtime 保留 `subagent_runtime` |
| `cli/collaboration_demo.py` | 增加 `--runtime-json` 入口 |
| `tests/test_collaboration.py` | 增加 runtime session / CLI JSON 验证 |
| `tests/test_events.py` | 增加 `delegation_runtime` event 测试 |
| `tests/test_langgraph_workflow.py` | 增加 graph runtime 保留 session 测试 |
| `subagent/README.md` | 更新当前 subagent runtime 能力说明 |
| `docs/current-learning-state.md` | 更新当前阶段状态 |

## 核心实现说明

### 1. 为什么 `v50` 之后还需要 runtime session

因为 `v50` 只回答了“协议怎么执行”，没有回答“执行时系统内部如何表达当前会话状态”。

工业系统中，下面这些问题都必须有正式对象：

- 当前是谁在执行
- 运行属于哪个 session
- 当前还能接收什么输入
- 状态为什么进入失败
- 失败时最后停在哪个角色

如果没有 runtime session，后续就很难继续做：

- 异步队列
- agent inbox / outbox
- 审批挂起
- 长任务跨会话续跑

### 2. 为什么 message envelope 很重要

因为多 Agent 协作本质上不是“角色数量”，而是“消息交换”。

`SubagentMessageEnvelope` 的价值在于，它把这些事实结构化了：

- 谁发消息
- 发给谁
- 是 delegation、handoff、return 还是 recovery
- 这条消息引用了哪些记录

这一步是后续异步委派和消息队列的直接前置基础。

### 3. 为什么 state transition 必须显式记录

因为工业 runtime 不能只看最终结果，还要看：

- 从哪个状态进入哪个状态
- 哪个角色触发了变化
- 为什么发生变化

`SubagentStateTransition` 的作用就是把这些变化变成正式证据。

后续如果要做：

- runtime audit
- stuck task detection
- pause / resume
- long-horizon lifecycle

这些都会依赖状态迁移记录。

### 4. 为什么当前仍然不是“真实多 Agent runtime”

因为 `v51` 解决的是 runtime foundation，不是异步执行系统。

当前仍然没有：

- inbox / outbox 队列
- pending / claimed / blocked 调度
- 独立子 Agent 轮询执行
- 并发消息驱动

所以 `v51` 的边界很清楚：

- 已经是 runtime foundation
- 但还不是 async runtime

## 运行示例

列出 subagents：

```bash
python -m cli.collaboration_demo --list-subagents
```

执行 subagent runtime：

```bash
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents
```

查看 runtime session JSON：

```bash
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --runtime-json
```

通过默认 Agent runtime 运行：

```bash
python -m cli.main --input "Execute subagent collaboration for a code review." --trace
```

## 验证命令

```bash
python -m unittest tests.test_collaboration tests.test_events tests.test_langgraph_workflow -v
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --runtime-json
python -m cli.main --input "Execute subagent collaboration for a code review." --trace
```

## 当前边界

- 当前 runtime 仍是 deterministic-runtime-foundation，不是 async runtime
- 还没有 agent inbox / outbox 和 delegation queue
- context boundary 目前仍围绕当前委派契约，不是多轮动态上下文裁剪系统
- checkpoint 现在能保留 `subagent_runtime`，但还不能基于该 session 做真正的挂起和恢复执行

## 下一步建议

`v51` 之后最自然的下一步是 `v52: Async Delegation Queue and Agent Inbox`。

因为现在已经有了：

- runtime session
- message envelope
- state transition
- graph / trace / checkpoint integration

接下来就可以继续解决“消息如何挂起、接收、认领和完成”的 async runtime 问题。
