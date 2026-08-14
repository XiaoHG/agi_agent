# v50：Multi-Agent Delegation Hardening

## 本阶段目标

把 subagent 协作从“结构化规划”升级为“可执行的委派协议”，让主 Agent 和子 Agent 之间具备 handoff、return、execution trace 和 delegation failure recovery。

## 本阶段在工业 Agent 中的位置

工业 Agent 的多角色协作不能只停留在：

- 生成一份 collaboration plan
- 说明 teacher / coding 各自做什么
- 把 delegation 放进 trace 但没有真正的子任务执行证据

它还必须具备：

- 明确的 handoff 协议
- 子任务执行记录
- 子任务返回记录
- delegation failure recovery
- 默认 runtime 与 graph runtime 的一致接入

`v50` 解决的是“多 Agent 协作如何从计划层，升级到可执行、可回放、可恢复的正式委派协议”。

## 本阶段解决的问题

- 让 subagent collaboration 不再只有 delegation record
- 让 teacher -> coding -> parent 的 handoff / return 流程结构化落盘
- 让 delegation failure 进入统一 recovery metadata
- 让 CLI、classic runtime、LangGraph runtime 都能执行同一套委派协议

## 本阶段新增能力

### 1. Delegation execution protocol

新增：

- `SubagentHandoffRecord`
- `SubagentReturnRecord`
- `SubagentExecutionRecord`
- `execute_collaboration_plan()`

现在一条协作链会显式记录：

- delegation
- handoff
- execution
- return

### 2. Execution-aware CollaborationPlan

增强：

- `CollaborationPlan.handoffs`
- `CollaborationPlan.returns`
- `CollaborationPlan.executions`
- `CollaborationPlan.status`
- `CollaborationPlan.recovery_handoff`

### 3. Agent / CLI integration

新增：

- `execute_subagents` Agent tool
- `--execute-subagents` collaboration CLI 入口

现在可以直接运行：

```bash
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents
```

### 4. Delegation recovery and observability

增强：

- delegation failure 会输出 `recovery_plan`
- runtime events 增加 `delegation_execution`
- replay 可稳定保留 delegation execution metadata

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `subagent/team.py` | 新增 handoff / return / execution 协议 |
| `subagent/__init__.py` | 导出新的 delegation execution 数据模型 |
| `agent/tools.py` | 增加 `execute_subagents` 工具入口 |
| `agent/router.py` | 增加 subagent execution 路由 |
| `agent/tool_schema.py` | 新增 `execute_subagents` schema |
| `agent/core.py` | classic runtime 接入执行型 subagent 工具 |
| `agent/events.py` | 增加 delegation execution 事件 |
| `integrations/langgraph_workflow.py` | graph runtime 接入 `execute_subagents` |
| `cli/collaboration_demo.py` | 增加 `--execute-subagents` |
| `tests/test_collaboration.py` | 增加 handoff / return / execution / failure 测试 |
| `tests/test_events.py` | 增加 delegation execution event 测试 |
| `tests/test_replay.py` | 增加 delegation execution replay 测试 |
| `subagent/README.md` | 更新 subagent 当前能力说明 |
| `docs/current-learning-state.md` | 更新当前学习状态 |

## 核心实现说明

### 1. 为什么 delegation 还不够

因为 delegation 只说明“任务派出去了”，不能说明：

- 中间怎么交接
- 有没有执行
- 执行后产出了什么
- 失败后应该交还给谁

真正的工业多 Agent 协作必须把这些过程都变成正式数据。

### 2. 为什么 handoff / return 必须结构化

因为多 Agent 协作的核心不是“谁在场”，而是“谁把什么交给谁，以及谁把什么交回来”。

只有 handoff / return 结构化之后，系统才能继续做：

- replay
- checkpoint
- delegation diff
- failure recovery
- 后续真实异步执行

### 3. 为什么当前仍然是 deterministic execution

因为本阶段目标是先把委派协议做稳，而不是一次性引入真实多 Agent 对话和并发。

当前 deterministic execution 的价值在于：

- 可以稳定测试
- 可以稳定回放
- 可以清楚讲解协议边界
- 为后续真实 runtime 留下清晰接口

## 运行示例

列出 subagents：

```bash
python -m cli.collaboration_demo --list-subagents
```

规划协作：

```bash
python -m cli.main --input "Plan subagent collaboration for a code review." --trace
```

执行协作协议：

```bash
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents
python -m cli.main --input "Execute subagent collaboration for a code review." --trace
```

## 验证命令

```bash
python -m unittest tests.test_collaboration tests.test_events tests.test_replay -v
python -m unittest discover -s tests -q
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents
```

## 当前边界

- 当前仍是 deterministic subagent execution，不是真实多 Agent 对话 runtime
- 还没有真正的并发执行和异步消息队列
- 失败恢复目前先回到 delegation-level safe handoff，还没有自动继续执行下游角色

## 下一步建议

`v50` 作为当前总纲收口版本，已经把多 Agent 委派协议推进到可执行、可追踪、可恢复的正式边界。下一轮版本规划可以继续围绕真实多 Agent runtime、长期任务和交付体系展开。
