# Multi-Agent Task Delegation and Subagent Contract v42 练习

对应版本：v42  
主题：Multi-Agent Task Delegation and Subagent Contract  
用途：理解主 Agent 如何把任务结构化委派给 subagent

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v42` 不能只输出一段更漂亮的 collaboration 文本？
2. `SubagentTaskContract` 解决了什么问题？
3. `SubagentDelegationRecord` 为什么要进入 trace？
4. 为什么输入边界和输出边界必须分开写？
5. 这一步为什么还是“协议层”，不是“真实多 Agent runtime”？

## 练习 2：读 subagent 链路

阅读：

- `subagent/team.py`
- `subagent/__init__.py`
- `agent/tools.py`
- `agent/events.py`
- `agent/core.py`
- `agent/replay.py`

请回答：

1. `build_collaboration_plan()` 会为哪些任务分配 `coding_agent`？
2. `SubagentTaskContract.to_dict()` 包含哪些关键字段？
3. `plan_subagent_collaboration()` 为什么要返回 `subagent_delegation` 元数据？
4. `build_runtime_events()` 为什么要新增 delegation 事件？
5. replay summary 为什么需要收集 delegation names？

## 练习 3：动手验证

运行：

```bash
python -m cli.collaboration_demo --list-subagents
python -m cli.collaboration_demo --task "Review this code and add tests."
python -m cli.main --input "Plan subagent collaboration for a code review." --trace
```

请记录：

1. 输出里是否出现 `Input boundary` 和 `Output boundary`？
2. `Delegations:` 下是否包含 `teacher_agent` 和 `coding_agent`？
3. `trace` 里是否能看到 delegation 相关事件？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么子任务契约比“角色列表”更适合工业 Agent？
2. 为什么 delegation record 适合进入 checkpoint 和 replay？
3. 如果后续要做真实多 Agent 执行，`v42` 最重要的基础价值是什么？

## 答案

### 练习 1：理解本阶段目标

1. `v42` 不能只输出更漂亮的文本，因为工业 Agent 需要的是可读、可写、可回放的协作协议，不只是说明文字。
2. `SubagentTaskContract` 解决的是子任务输入、输出、恢复和交接边界不清的问题。
3. `SubagentDelegationRecord` 要进入 trace，是为了让子任务历史能被测试、replay 和恢复流程直接读取。
4. 输入边界和输出边界必须分开写，因为协作的关键不是“做什么”，而是“能接什么、要交什么”。
5. 这一步还是协议层，因为它只定义结构化委派和记录，不执行真实的多 Agent 消息传递。

### 练习 2：读 subagent 链路

1. `build_collaboration_plan()` 会为包含 `implement`、`fix`、`test`、`code`、`bug`、`review` 的任务分配 `coding_agent`。
2. `SubagentTaskContract.to_dict()` 包含 `role_name`、`objective`、`input_boundary`、`required_inputs`、`output_boundary`、`expected_outputs`、`recovery_handoff`。
3. `plan_subagent_collaboration()` 返回 `subagent_delegation` 元数据，是为了让 trace、checkpoint 和 replay 都能读取同一份计划结构。
4. `build_runtime_events()` 新增 delegation 事件，是为了让运行轨迹里直接出现子任务委派节点。
5. replay summary 需要收集 delegation names，是为了比较不同 run 时协作结构有没有变化。

### 练习 3：动手验证

1. 输出里应当出现 `Input boundary` 和 `Output boundary`。
2. `Delegations:` 下应当包含 `teacher_agent` 和 `coding_agent`。
3. `trace` 里应当能看到 delegation 相关事件。

### 练习 4：工程取舍题

1. 子任务契约比角色列表更适合工业 Agent，因为它描述的是协作接口，不只是职责名称。
2. delegation record 适合进入 checkpoint 和 replay，因为它能让历史协作路径稳定回放和比较。
3. `v42` 最重要的基础价值是把多 Agent 协作边界打通了，后续才能安全扩展到真实执行和长期连续协作。

## 验证

```bash
python -m unittest tests.test_collaboration tests.test_replay -v
python -m cli.collaboration_demo --task "Review this code and add tests."
```
