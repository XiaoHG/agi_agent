# Multi-Agent Delegation Hardening v50 练习

对应版本：v50  
主题：Multi-Agent Delegation Hardening  
用途：理解多 Agent 协作为什么必须从 delegation plan 升级到 handoff / return / execution protocol

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v50` 不能只保留 `SubagentDelegationRecord`？
2. `SubagentHandoffRecord` 和 `SubagentReturnRecord` 分别解决什么问题？
3. 为什么 `CollaborationPlan` 现在必须带 `status` 和 `recovery_handoff`？
4. 为什么 subagent failure 也要进入统一 `recovery_plan`？
5. 这一步为什么是“委派协议硬化”，而不是只补 trace 字段？

## 练习 2：读 subagent 执行链路

阅读：

- `subagent/team.py`
- `agent/tools.py`
- `agent/router.py`
- `integrations/langgraph_workflow.py`
- `tests/test_collaboration.py`

请回答：

1. `execute_collaboration_plan()` 比 `build_collaboration_plan()` 多做了哪些事情？
2. teacher_agent 和 coding_agent 的 execution outputs 有什么区别？
3. failure 情况下为什么要提前返回，而不是继续执行后续角色？
4. `execute_subagents` 为什么要同时接入 classic runtime 和 graph runtime？
5. `delegation_execution` event 和普通 `delegation` event 有什么差别？

## 练习 3：动手验证

运行：

```bash
python -m unittest tests.test_collaboration tests.test_events tests.test_replay -v
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents
python -m cli.main --input "Execute subagent collaboration for a code review." --trace
```

请记录：

1. 输出中是否出现 `Handoffs:`、`Executions:`、`Returns:`？
2. `Plan status` 是否可见？
3. 失败场景下 trace 里是否出现 `recovery_plan.failure_type = delegation_blocked`？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么工业多 Agent 协作的关键是 handoff / return，而不是角色数量？
2. 为什么 deterministic execution 仍然有工程价值？
3. 如果后续要接真实多 Agent runtime，`v50` 最重要的基础价值是什么？

## 答案

### 练习 1：理解本阶段目标

1. 因为 `SubagentDelegationRecord` 只能表示“任务派出去了”，不能表示“怎么交接、有没有执行、执行后怎么返回”。
2. `SubagentHandoffRecord` 解决角色之间交接边界的问题，`SubagentReturnRecord` 解决子任务完成后如何把结果交回主流程的问题。
3. 因为没有 `status` 和 `recovery_handoff`，系统就无法稳定知道协作整体是否完成、失败后该怎么安全回退。
4. 因为 subagent failure 也是正式执行失败的一种，必须进入统一恢复链路，才能被 trace、replay 和后续门禁读取。
5. 因为 `v50` 改的是多 Agent 协作协议本身，把 delegation、handoff、execution、return 和 recovery 串成了完整闭环。

### 练习 2：读 subagent 执行链路

1. `execute_collaboration_plan()` 不只生成计划，还会生成 handoff、execution、return，并在失败时给出 recovery_handoff。
2. teacher_agent 更偏解释与边界澄清，coding_agent 更偏实现、测试和验证证据。
3. 因为一旦上游输入已经不安全或不明确，继续执行后续角色只会放大错误，先停在最近的安全 handoff 更符合工业边界。
4. 因为项目默认已经以 graph runtime 为主执行器，classic runtime 和 graph runtime 必须对同一能力保持一致入口。
5. `delegation` event 表示“有委派计划”，`delegation_execution` event 表示“委派已经执行并产生了结构化证据”。

### 练习 3：动手验证

1. 是，输出中应出现 `Handoffs:`、`Executions:`、`Returns:`。
2. 是，输出中应出现 `Plan status`。
3. 是，失败场景下 trace 中应出现 `recovery_plan.failure_type = delegation_blocked`。

### 练习 4：工程取舍题

1. 因为工业协作的关键不是“有几个 agent”，而是“信息如何安全地从一个角色交给另一个角色，并能安全返回”。
2. 因为 deterministic execution 可以稳定测试、稳定回放、稳定讲解协议，不会被真实外部依赖噪声掩盖边界问题。
3. `v50` 最重要的基础价值，是把多 Agent 协作正式拆成 delegation、handoff、execution、return 和 recovery 这些清晰接口，后续真实 runtime 可以直接复用这些协议结构。
