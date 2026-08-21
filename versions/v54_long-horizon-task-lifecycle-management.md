# v54：Long-Horizon Task Lifecycle Management

## 本阶段目标

把 `v53` 的审批与受保护交接，继续推进为长期任务生命周期管理。

`v53` 已经解决了：

- approval request / decision
- guarded handoff
- risk classification
- blocked / revised approval path

但工业级 Agent 还缺少一个更高层的问题：

- 长任务如何暂停
- 暂停后如何恢复
- 任务何时过期
- 任务何时应该放弃并重开
- 任务健康状态如何被持续观察

`v54` 的目标就是把这些生命周期边界补齐。

## 本阶段在工业 Agent 中的位置

工业级 Agent 不只是“能执行一个请求”，还要能管理“一个会跨多个阶段推进的任务”。

当任务变长以后，系统必须能够表达：

- 当前任务处于什么状态
- 现在推进到哪个里程碑
- 是否出现卡住或超时
- 哪些状态允许继续恢复
- 哪些状态必须重新规划

所以 `v54` 不是再加一个协作角色，而是把任务本身写成一等对象。

## 本阶段解决的问题

- 为长任务增加生命周期记录
- 为长任务增加里程碑记录
- 为长任务增加 watchdog 健康信号
- 把 pause / resume / expire / abandon 写成可追踪状态
- 把生命周期状态接入 runtime evidence 和 CLI 输出

## 本阶段新增能力

### 1. Task lifecycle record

新增：

- `TaskLifecycleRecord`

它描述：

- 当前任务状态
- 当前健康状态
- 当前里程碑
- 暂停原因
- 恢复提示
- 下一步安全动作

### 2. Milestone records

新增：

- `TaskMilestoneRecord`

它用于记录长任务推进过程中的阶段性检查点，便于后续 resume 和复盘。

### 3. Watchdog signals

新增：

- `TaskWatchdogSignal`

它用于表达：

- 当前任务是否健康
- 是否进入 stalled / paused / expired / abandoned 状态
- 应该采取什么安全动作

### 4. Lifecycle-aware runtime session

`SubagentRuntimeSession` 现在除了 queue / inbox / outbox / approval 之外，还会保留：

- `task_lifecycle`
- `watchdog_signals`

这意味着长任务状态不再只是文字提示，而是正式 runtime evidence。

### 5. Lifecycle-aware execution

`execute_collaboration_plan()` 现在支持：

- pause
- resume
- expire
- abandon
- watchdog / stalled / timeout

这一步把多 Agent 从“能协作”推进到了“能管理长任务协作”。

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `subagent/team.py` | 新增长任务生命周期、里程碑和 watchdog 数据模型，并接入 collaboration execution |
| `subagent/__init__.py` | 导出新的生命周期模型与构造函数 |
| `agent/events.py` | 新增 `task_lifecycle` 和 `task_watchdog` event |
| `agent/tools.py` | 将生命周期状态纳入 recovery metadata |
| `cli/collaboration_demo.py` | 增加 `--lifecycle-json` |
| `tests/test_collaboration.py` | 增加生命周期、watchdog 和 CLI JSON 测试 |
| `tests/test_events.py` | 增加生命周期 event 测试 |
| `subagent/README.md` | 更新 subagent 协作能力说明 |
| `docs/current-learning-state.md` | 更新当前阶段状态和下一步建议 |

## 核心实现说明

### 1. 为什么要把任务做成一等对象

因为 long-horizon 场景里，真正重要的不只是“这个请求完成没有”，而是“它现在处于什么生命周期阶段”。

### 2. 为什么要单独记录 milestone

因为暂停和恢复都依赖“已经走到哪一步”。

没有 milestone，resume 只能靠模糊记忆。

### 3. 为什么 watchdog 不能只靠失败错误

因为长任务最危险的状态往往不是失败，而是静默卡住、长时间停滞或被人为暂停。

### 4. 为什么 lifecycle state 不直接等于 execution status

因为 execution status 关注一次执行结果，lifecycle state 关注整个任务在时间轴上的阶段。

## 运行示例

查看暂停任务的生命周期输出：

```bash
python -m cli.collaboration_demo --task "Pause this long-horizon implementation task after review." --execute-subagents --lifecycle-json
```

查看普通 subagent 协作：

```bash
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --runtime-json --queue-json
```

## 验证命令

```bash
python -m unittest tests.test_collaboration tests.test_events tests.test_langgraph_workflow -v
python -m cli.collaboration_demo --task "Pause this long-horizon implementation task after review." --execute-subagents --lifecycle-json
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --runtime-json --queue-json
python -m cli.main --input "Execute subagent collaboration for a code review." --trace
```

## 当前边界

- 当前生命周期仍是 deterministic learning model，不是分布式任务编排引擎
- pause / resume / expire / abandon 仍由本地规则模拟，不是外部任务控制台
- watchdog 目前用于学习和审计，不是独立调度服务

## 下一步建议

`v54` 之后最自然的下一步是 `v55: Externalized Registry and Runtime Governance`。

因为现在已经有了：

- runtime session
- async delegation queue
- approval request / decision
- guarded handoff
- task lifecycle
- watchdog signals

接下来就可以继续解决“能力治理如何外部化、策略如何统一加载、环境如何审计”的问题。
