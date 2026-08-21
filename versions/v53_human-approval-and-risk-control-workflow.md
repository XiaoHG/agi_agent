# v53：Human Approval and Risk-Control Workflow

## 本阶段目标

把 `v52` 的 async delegation queue 继续推进成正式审批控制流。

`v52` 已经解决了：

- delegation queue
- agent inbox / outbox
- task claim / complete / fail / blocked
- runtime session 级异步证据

但它还没有正式回答下面这些工业运行问题：

- 哪些任务必须先经过审批才能继续
- 风险应该如何分类
- 审批请求和审批决策应该如何记录
- 高风险交接如何被保护
- 审批拒绝或需要修订时如何回退

`v53` 的目标就是把这些审批边界补齐。

## 本阶段在工业 Agent 中的位置

工业级 Agent 不能只会“能执行”，还必须知道“什么时候不能执行”。

尤其当任务涉及：

- 删除、写入、覆盖
- 受保护资源
- 关键协作切换
- 需要人工确认的写操作

系统就不能只依赖自动执行，而必须先经过风险判断和审批决策。

所以 `v53` 的定位不是做完整权限系统，也不是做 Web 审批后台，而是先把最小可用的 approval request / decision / guarded handoff 模型写清楚。

## 本阶段解决的问题

- 给协作目标增加风险分类
- 为高风险任务生成 approval request
- 为审批流生成 approval decision
- 把受保护交接建模成 guarded handoff
- 把批准 / 拒绝 / 需修订这三类审批结果接入 runtime evidence

## 本阶段新增能力

### 1. Risk classification

新增：

- `RiskClassification`

它会基于任务文本判断：

- 风险级别
- 风险原因
- 是否需要审批
- 哪些动作必须阻断

### 2. Approval request / decision

新增：

- `ApprovalRequest`
- `ApprovalDecision`

这让协作流程可以明确回答：

- 谁发起审批
- 审批给谁看
- 审批针对什么动作
- 审批结果是什么
- 下一步应该怎么走

### 3. Guarded handoff

新增：

- `GuardedHandoffRecord`

它用于描述：

- 从哪个角色交给哪个角色
- 这次交接为什么必须受审批保护
- 当前审批状态是什么
- 如果没通过，应该回退到哪里

### 4. Approval-aware runtime session

`SubagentRuntimeSession` 现在除了 queue / inbox / outbox / claim 之外，还会保留：

- `guarded_handoffs`
- `approval_requests`
- `approval_decisions`

这意味着审批不只是文本提示，而是正式 runtime evidence。

### 5. Approval-aware execution

`execute_collaboration_plan()` 现在支持：

- 默认审批判断
- `approval_override` 显式覆盖
- 高风险任务被 `revise_required` 或 `rejected` 阻断
- 审批通过后允许 guarded handoff 继续

这一步把多 Agent 从“能收发任务”推进到了“能被控制地收发任务”。

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `subagent/team.py` | 新增 risk / approval / guarded handoff 数据模型，并把审批流接入 collaboration execution |
| `subagent/__init__.py` | 导出新的审批模型与构造函数 |
| `agent/events.py` | 新增 `approval_workflow` event |
| `agent/tools.py` | 将 approval blocked 细化为独立 recovery type |
| `cli/collaboration_demo.py` | 增加 `--approval-json` 和 `--approval-decision` |
| `tests/test_collaboration.py` | 增加审批阻断、审批放行和 CLI 审批 JSON 测试 |
| `tests/test_events.py` | 增加 approval workflow event 测试 |
| `subagent/README.md` | 更新 subagent 协作能力说明 |
| `docs/current-learning-state.md` | 更新当前阶段状态和下一步建议 |

## 核心实现说明

### 1. 为什么审批必须先于执行

因为高风险任务一旦进入执行阶段，后续恢复成本会更高。

审批前置的意义不只是“让人看一眼”，而是让系统在真正发生写操作之前就能明确：

- 这件事是否值得继续
- 是否需要先修订目标
- 是否需要改成更小的安全变更

### 2. 为什么 approval request 和 approval decision 必须分开

因为请求和结果是两个不同事实：

- request 说明“有人请求审批”
- decision 说明“审批者做了什么决定”

如果把它们合并，后续就很难审计“是谁发起、谁批准、为什么批准”。

### 3. 为什么 guarded handoff 很关键

因为真正危险的不是任务本身，而是“把危险任务交给执行角色”这一步。

`GuardedHandoffRecord` 让系统可以明确表达：

- 交接前必须过审批
- 审批没过就不能继续
- 如果没过，下一步应该回退还是修订

### 4. 为什么 approval blocked 不能直接等同于 failed

因为 blocked 通常意味着任务仍然可能继续，只是当前被控制策略挡住了。

这和真正的失败不同：

- failed 更像执行中出现不可完成错误
- blocked 更像运行前或运行中被策略停止

## 运行示例

查看高风险任务的审批输出：

```bash
python -m cli.collaboration_demo --task "Delete a workspace file and write project file." --execute-subagents --approval-json --approval-decision approved
```

查看审批被阻断的路径：

```bash
python -m cli.collaboration_demo --task "Delete a workspace file and write project file." --execute-subagents
```

查看普通 subagent 协作：

```bash
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --runtime-json --queue-json
```

## 验证命令

```bash
python -m unittest tests.test_collaboration tests.test_events tests.test_langgraph_workflow -v
python -m cli.collaboration_demo --task "Delete a workspace file and write project file." --execute-subagents --approval-json --approval-decision approved
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --runtime-json --queue-json
python -m cli.main --input "Execute subagent collaboration for a code review." --trace
```

## 当前边界

- 当前审批流程仍然是 deterministic learning model，不是企业级权限系统
- 审批决策仍由本地规则或 CLI 覆盖，不是独立审批服务
- guarded handoff 目前主要用于学习和审计，不是分布式工作流引擎
- 受保护交接和审批记录还没有进入独立数据库或外部控制台

## 下一步建议

`v53` 之后最自然的下一步是 `v54: Long-Horizon Task Lifecycle Management`。

因为现在已经有了：

- runtime session
- async delegation queue
- agent inbox / outbox
- approval request / decision
- guarded handoff

接下来就可以继续解决“长期任务如何 pause / resume / expire / abandon，以及如何做生命周期治理”的问题。
