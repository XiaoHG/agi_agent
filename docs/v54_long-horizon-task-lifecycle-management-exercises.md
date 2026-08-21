# Long-Horizon Task Lifecycle Management v54 练习

对应版本：v54  
主题：Long-Horizon Task Lifecycle Management  
用途：理解长任务为什么要从“执行结果”升级为“生命周期治理”

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v53` 之后还不能说项目已经具备长任务治理能力？
2. `TaskLifecycleRecord` 主要解决什么问题？
3. 为什么 `TaskMilestoneRecord` 对 pause / resume 很关键？
4. 为什么 `TaskWatchdogSignal` 不能被简化成一个错误字符串？
5. 为什么 lifecycle state 不能直接等同于 execution status？

## 练习 2：读生命周期执行链路

阅读：

- `subagent/team.py`
- `agent/events.py`
- `agent/tools.py`
- `cli/collaboration_demo.py`
- `tests/test_collaboration.py`

请回答：

1. `execute_collaboration_plan()` 在 `v54` 中加入了什么生命周期判断？
2. `--lifecycle-json` 的作用是什么？
3. `task_lifecycle` event 记录了哪些生命周期事实？
4. 为什么 `watchdog_signals` 需要单独保存？
5. 为什么 paused / expired / abandoned 不应该只被当成普通 failed？

## 练习 3：动手验证

运行：

```bash
python -m unittest tests.test_collaboration tests.test_events tests.test_langgraph_workflow -v
python -m cli.collaboration_demo --task "Pause this long-horizon implementation task after review." --execute-subagents --lifecycle-json
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --runtime-json --queue-json
python -m cli.main --input "Execute subagent collaboration for a code review." --trace
```

请记录：

1. 生命周期 JSON 中是否出现 `task_lifecycle` 和 `watchdog_signals`？
2. 暂停任务是否会进入 `paused` 状态？
3. `runtime events` 中是否出现 `task_lifecycle` 和 `task_watchdog`？
4. `task_lifecycle` 是否能在 `trace` 中被直接查看？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么长任务治理必须放在 subagent runtime 里，而不是只放在 CLI 提示里？
2. 为什么 milestone 是长期任务恢复的基础？
3. 为什么 watchdog 更像治理信号，而不是普通错误处理？
4. 为什么 `v54` 仍然是学习版，但已经开始接近工业级任务控制？

## 答案

### 练习 1：理解本阶段目标

1. 因为 `v53` 主要解决的是审批和受保护交接，还没有正式表达长任务的暂停、恢复、过期和放弃。
2. `TaskLifecycleRecord` 解决的是“任务现在处于什么生命周期阶段、应该如何继续或退出”。
3. 因为 resume 需要知道任务已经走到哪个检查点，milestone 就是这个可恢复边界。
4. 因为 watchdog 需要保留健康状态、严重程度和推荐动作，方便后续恢复和审计。
5. 因为 execution status 关注一次执行，lifecycle state 关注整个任务时间轴。

### 练习 2：读生命周期执行链路

1. `execute_collaboration_plan()` 在 `v54` 中加入了生命周期状态判断：pause、resume、expire、abandon、watchdog / stalled / timeout。
2. `--lifecycle-json` 用来输出任务生命周期和 watchdog 信号的结构化 JSON。
3. `task_lifecycle` event 记录了生命周期状态、健康状态、当前里程碑和下一步安全动作。
4. 因为 `watchdog_signals` 是独立的健康证据，和普通执行结果不是同一层数据。
5. 因为这些状态表示的是任务生命周期治理，不只是执行失败，后续恢复策略也不同。

### 练习 3：动手验证

1. 是，生命周期 JSON 中应出现 `task_lifecycle` 和 `watchdog_signals`。
2. 是，暂停任务会进入 `paused` 状态。
3. 是，runtime events 中应出现 `task_lifecycle` 和 `task_watchdog`。
4. 是，`task_lifecycle` 可以在 trace 中直接查看。

### 练习 4：工程取舍题

1. 因为长任务治理必须和 runtime evidence 绑定，CLI 只负责展示，不能承担生命周期事实本身。
2. 因为 resume 需要可追踪的阶段边界，没有 milestone 就无法安全恢复。
3. 因为 watchdog 表示系统健康和进度治理，不只是某个操作失败。
4. 因为它已经把 pause / resume / expire / abandon 写进了协作模型，但还没有进入外部化任务调度平台。
