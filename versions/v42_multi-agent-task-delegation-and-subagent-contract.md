# v42：Multi-Agent Task Delegation and Subagent Contract

## 本阶段目标

把主 Agent 与 subagent 的协作从“规划文本”升级为“结构化委派契约”，让子任务具备清晰的输入边界、输出边界、委派记录和可回放 trace。

## 本阶段在工业 Agent 中的位置

工业 Agent 的多角色协作不能只停留在“谁负责什么”的描述层。

它必须具备：

- 可序列化的子任务契约
- 明确的输入 / 输出边界
- 稳定的 delegation record
- 能进入 trace / recovery / replay 的子任务记录

`v42` 解决的是“主 Agent 如何把任务安全、结构化地委派给 subagent”。

## 本阶段解决的问题

- 让 subagent 不再只是角色名
- 让协作计划同时包含契约和委派记录
- 让 trace 可以直接看到子任务边界
- 让 replay / recovery 能识别 delegation 级别的历史记录

## 本阶段新增能力

### 1. SubagentTaskContract

新增 `SubagentTaskContract`，定义：

- role_name
- objective
- input_boundary
- required_inputs
- output_boundary
- expected_outputs
- recovery_handoff

这让每个 subagent 的任务边界变成结构化数据，而不是纯文本说明。

### 2. SubagentDelegationRecord

新增 `SubagentDelegationRecord`，用于记录：

- delegation_id
- parent_objective
- role
- contract
- status
- child_task
- order
- notes

这让子任务计划能进入 trace、checkpoint 和 replay 逻辑。

### 3. CollaborationPlan 升级

`CollaborationPlan` 现在同时包含：

- assigned_roles
- contracts
- delegations
- workflow steps

这样 CLI 输出、Agent trace 和测试都能消费同一份计划结构。

### 4. Trace / replay 接入

`plan_subagents` 的工具结果现在会携带 `subagent_delegation` 元数据。

`RuntimeEvent` 也会生成 delegation 事件，便于回放和比较。

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `subagent/team.py` | 新增 contract / delegation / structured collaboration plan |
| `subagent/__init__.py` | 导出新数据模型 |
| `agent/tools.py` | `plan_subagents` 返回结构化 delegation 元数据 |
| `agent/events.py` | 增加 delegation runtime event |
| `agent/core.py` | trace 透出 `subagent_delegation` |
| `agent/persistence.py` | checkpoint 保留 delegation metadata |
| `agent/replay.py` | replay summary / diff 支持 delegation |
| `tests/test_collaboration.py` | 增加 contract、plan、trace 测试 |
| `docs/current-learning-state.md` | 更新当前学习状态 |

## 核心实现说明

### 1. 为什么 subagent contract 必须结构化

因为工业 Agent 的协作边界必须可检查、可记录、可回放。

只有文本描述时，系统很难判断：

- 该 subagent 能接收什么输入
- 该 subagent 应输出什么结果
- 失败后应该交回哪个角色

### 2. 为什么 delegation record 不能只写在日志里

因为日志适合人看，不适合程序稳定读取。

delegation record 进入 trace 之后，后续才能做：

- replay
- diff
- checkpoint resume
- 协作失败分析

### 3. 为什么本阶段仍然不做真实多 Agent 对话

因为当前目标是先把协作协议和边界做正确。

真实消息传递、异步执行和多轮协商会显著扩大复杂度，适合放到下一阶段继续推进。

## 运行示例

查看 subagent 信息：

```bash
python -m cli.collaboration_demo --list-subagents
```

生成协作计划：

```bash
python -m cli.collaboration_demo --task "Review this code and add tests."
```

通过 Agent 查看 trace：

```bash
python -m cli.main --input "Plan subagent collaboration for a code review." --trace
```

## 验证命令

```bash
python -m unittest tests.test_collaboration tests.test_replay -v
python -m unittest discover -s tests -v
```

## 当前边界

- 这是结构化委派协议层，不是真实多 Agent runtime
- delegation record 先覆盖 teacher / coding 两个默认角色
- recovery / replay 先支持读取子任务历史，不做自动重放执行

## 下一步建议

下一阶段建议进入：

`v43：Long-Horizon Memory and Session Continuity`

重点是把委派后的子任务历史和长期会话连续性接起来，继续推进工业 Agent 的跨轮次协作能力。
