# Human Approval and Risk-Control Workflow v53 练习

对应版本：v53  
主题：Human Approval and Risk-Control Workflow  
用途：理解多 Agent 为什么要在 async delegation 之后继续引入审批边界

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v52` 之后还不能说项目已经具备审批控制流？
2. `RiskClassification` 主要解决什么问题？
3. `ApprovalRequest` 和 `ApprovalDecision` 为什么不能合并成一个对象？
4. 为什么 `GuardedHandoffRecord` 是工业 Agent 里必须有的对象？
5. 为什么 `blocked` 不应该直接等同于 `failed`？

## 练习 2：读审批执行链路

阅读：

- `subagent/team.py`
- `agent/events.py`
- `agent/tools.py`
- `cli/collaboration_demo.py`
- `tests/test_collaboration.py`

请回答：

1. `execute_collaboration_plan()` 在 `v53` 中加入了什么审批判断？
2. `approval_override` 的作用是什么？
3. `approval_workflow` event 记录了哪些审批事实？
4. `guarded_handoffs` 为什么需要单独和普通 `handoffs` 分开保存？
5. `approval_blocked` 为什么应该和 `delegation_failed` 分开区分？

## 练习 3：动手验证

运行：

```bash
python -m unittest tests.test_collaboration tests.test_events tests.test_langgraph_workflow -v
python -m cli.collaboration_demo --task "Delete a workspace file and write project file." --execute-subagents --approval-json --approval-decision approved
python -m cli.collaboration_demo --task "Delete a workspace file and write project file." --execute-subagents
python -m cli.main --input "Execute subagent collaboration for a code review." --trace
```

请记录：

1. 审批 JSON 中是否出现 `risk`、`approval_request`、`approval_decision` 和 `guarded_handoffs`？
2. 高风险任务是否能通过 `--approval-decision approved` 正常通过 guarded handoff？
3. 默认审批路径是否会将高风险任务阻断成 `blocked` 或 `revise_required`？
4. runtime events 中是否出现 `approval_workflow`？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么审批流必须和 task claim / inbox / outbox 分开建模？
2. 为什么高风险任务要先走受保护交接，而不是直接进入执行？
3. 为什么 `v53` 的审批模型仍然是学习版，但已经比纯协议更接近工业系统？
4. 为什么审批流、长任务治理和 release gate 需要按版本逐步推进？

## 答案

### 练习 1：理解本阶段目标

1. 因为 `v52` 主要解决的是任务收发、认领和 blocked 状态，还没有正式表达风险分类、审批请求、审批决策和受保护交接，所以还不能算完整审批控制流。
2. `RiskClassification` 解决的是“这次任务风险有多高、为什么高、是否需要审批、哪些动作必须阻断”。
3. 因为 request 代表请求事实，decision 代表审批结果事实。两者分开后，系统才能清楚审计谁请求、谁审批、为什么审批。
4. 因为它把“从一个角色交给另一个角色”这一步变成了一个明确受审批保护的动作，后续可以检查是否允许继续，或者应该回退和修订。
5. 因为 blocked 更像“当前被策略或依赖挡住了”，不一定是任务本身不可完成。failed 则更偏向执行过程已经产生了不可恢复的失败。

### 练习 2：读审批执行链路

1. `execute_collaboration_plan()` 在 `v53` 中加入了风险分类和审批判断：先生成 `RiskClassification`，再生成 `ApprovalRequest` 和 `ApprovalDecision`，并用 `approval_override` 控制审批结果。
2. `approval_override` 允许测试或演示显式指定审批结果，例如 `approved`、`rejected` 或 `revise_required`，从而复现不同审批路径。
3. `approval_workflow` event 记录了审批请求和审批决策，以及它们对应的 decision 状态。
4. 因为普通 handoff 只是角色之间的正常交接，而 guarded handoff 是经过审批控制的受保护交接。两者语义不同，应该分开保存。
5. 因为 `approval_blocked` 表示任务被审批控制挡住了，和执行中失败的 `delegation_failed` 不是同一类问题。后续恢复策略也不同。

### 练习 3：动手验证

1. 是，审批 JSON 中应出现 `risk`、`approval_request`、`approval_decision` 和 `guarded_handoffs`。
2. 是，高风险任务可以通过 `--approval-decision approved` 正常通过 guarded handoff。
3. 是，默认审批路径会根据风险与规则把高风险任务阻断成 `blocked` 或 `revise_required`。
4. 是，runtime events 中应出现 `approval_workflow`。

### 练习 4：工程取舍题

1. 因为审批流解决的是“能不能继续做”，task claim / inbox / outbox 解决的是“任务现在在哪、谁在处理、如何回传”。两个层次不同。
2. 因为高风险任务一旦进入执行，后续代价更高。先走受保护交接可以把风险拦在执行前。
3. 因为它已经把审批请求、审批决策、风险分类和 guarded handoff 这些工业概念写进了运行模型，但还没有引入企业级权限系统和完整审批平台。
4. 因为这些能力都属于工业 Agent 的治理层，必须按层次逐步推进，否则会把运行层、治理层和交付层混成一个不可学习的大版本。
