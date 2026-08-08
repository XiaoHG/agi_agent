# Checkpoint-Guided Recovery and Resume v38 练习

对应版本：v38  
主题：Checkpoint-Guided Recovery and Resume  
用途：理解为什么 checkpoint 的下一步不是直接 recovery，而是先做 guided resume

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v38` 是 checkpoint 的自然下一步？
2. 什么是 checkpoint-guided resume？
3. `CheckpointResumePlan` 的职责是什么？
4. `CheckpointResumeReport` 和 `ReplayDiffReport` 的关系是什么？
5. 为什么本阶段还不算真正的 stateful continue execution？

## 练习 2：读 resume 链路

阅读：

- `agent/replay.py`
- `agent/core.py`
- `cli/main.py`
- `tests/test_persistence.py`

请回答：

1. `WorkspaceAgent.run()` 为什么要支持 `route_override`？
2. `resume_checkpoint()` 实际上如何利用 checkpoint 的 route hints？
3. `resume_latest_checkpoint()` 和 `resume_checkpoint(run_id)` 的区别是什么？
4. `--resume-last-run` 和 `--resume-run` 分别适合什么场景？
5. 为什么 resume 逻辑不应该放进 CLI 层？

## 练习 3：动手验证

先运行：

```bash
python -m cli.main --input "Use LangGraph to read README.md." --trace
```

再运行：

```bash
python -m cli.main --resume-last-run
```

请记录：

1. 输出是否包含 `Checkpoint resume plan`？
2. 是否包含 `Source summary:`？
3. 是否包含 `Resume diff:`？

再运行：

```bash
python -m cli.main --resume-run <run_id>
```

请记录：

1. 是否可以按 run id 恢复？
2. 输出中是否保留了源运行和恢复运行的摘要？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么本阶段要先做 guided resume，而不是直接做 graph state 级 continue execution？
2. 为什么 `resume_mode` 和 `next_safe_action` 这类信息要进入数据模型？
3. 未来真正做分叉恢复时，最可能复用 `v38` 的哪些结构？

## 答案

### 练习 1：理解本阶段目标

1. `v38` 是 checkpoint 的自然下一步，因为 checkpoint 已经保存了运行事实，下一步就是利用这些事实指导后续执行。没有 guided resume，checkpoint 只能停留在“看”和“比”。
2. checkpoint-guided resume 指的是：读取 checkpoint 中保存的 route hints，然后按照这些提示重新进入相同的执行路径。它不是精确恢复某个中断点，而是基于历史信息重跑一条受 checkpoint 指导的路径。
3. `CheckpointResumePlan` 的职责是把恢复决策结构化，包括恢复来源、路由信息、失败类型、恢复模式和下一步安全动作，便于后续执行或人工判断。
4. `CheckpointResumeReport` 面向“恢复过程本身”，它包含恢复计划、源运行摘要、恢复后摘要和差异信息；`ReplayDiffReport` 只负责比较两次运行，二者可以配合，但不是同一层职责。
5. 本阶段还不算真正的 stateful continue execution，因为它并没有在图执行中断点上接着跑，也没有恢复具体的 graph state，只是用 checkpoint 的 route hints 重新发起一次受引导的运行。

### 练习 2：读 resume 链路

1. `WorkspaceAgent.run()` 支持 `route_override`，是为了让恢复逻辑可以跳过重新路由，直接按 checkpoint 保存的执行意图重跑同一路径。
2. `resume_checkpoint()` 会先从 checkpoint 里读出 route，再把 route 转成 `ToolRoute`，然后调用 `run()` 重新执行。这样 resume 不是靠 CLI 拼接逻辑，而是靠 agent 本身的执行能力。
3. `resume_latest_checkpoint()` 适合快速恢复最近一次运行；`resume_checkpoint(run_id)` 适合对某次历史 run 做定点恢复。
4. `--resume-last-run` 适合刚执行完一次调试，想立刻看恢复结果；`--resume-run` 适合你已经知道目标 run id，想精确恢复某次运行。
5. resume 逻辑不应该放进 CLI 层，因为 CLI 只负责参数解析和调用入口。恢复策略属于 Agent 业务能力，应该留在 `agent/` 中，方便测试、复用和后续扩展。

### 练习 3：动手验证

1. 输出应当包含 `Checkpoint resume plan`，因为这是恢复报告的主标题。
2. 输出应当包含 `Source summary:`，因为恢复必须先说明源运行是什么。
3. 输出应当包含 `Resume diff:`，因为恢复后应能看到原始运行和恢复运行的差异。
4. `python -m cli.main --resume-run <run_id>` 应当可以按 run id 恢复，只要该 checkpoint 存在。
5. 输出中应当保留源运行和恢复运行的摘要，因为恢复过程本身需要可审计、可比较。

### 练习 4：工程取舍题

1. 先做 guided resume，而不是直接做 graph state 级 continue execution，是因为前者依赖更少、边界更清晰、实现风险更低，也更适合作为下一步能力的前置层。
2. `resume_mode` 和 `next_safe_action` 需要进入数据模型，是因为恢复不是单纯执行动作，而是一个可解释的工程决策。把这些信息结构化后，后续才能做更复杂的分支恢复和人工审批。
3. 未来真正做分叉恢复时，最可能复用 `v38` 的结构包括 `CheckpointResumePlan`、`CheckpointResumeReport`、route hints、`failure_type` 和 `next_safe_action`。

## 验证

```bash
python -m unittest tests.test_persistence -v
python -m cli.main --resume-last-run
```
