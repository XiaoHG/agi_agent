# Run Replay Diff and Comparative Analysis v37 练习

对应版本：v37  
主题：Run Replay Diff and Comparative Analysis  
用途：理解为什么 replay 的下一步不是直接 recovery，而是先做跨 run 对比分析

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v37` 要先做 replay diff，而不是直接做 recovery？
2. `ReplaySummary` 的职责是什么？
3. `ReplayDiffReport` 和 `ReplayReport` 的差别是什么？
4. 为什么这个版本只比较稳定的结构化字段，而不做 LLM 语义 diff？
5. 为什么这个版本符合“一个大功能版本”的要求？

## 练习 2：读 compare 链路

阅读：

- `agent/replay.py`
- `agent/core.py`
- `cli/main.py`
- `tests/test_persistence.py`

请回答：

1. `ReplaySummary` 包含了哪些关键字段？
2. `compare_replay_reports()` 目前比较了哪些差异？
3. `WorkspaceAgent.compare_latest_two_checkpoints()` 和 `compare_checkpoints()` 的区别是什么？
4. `--compare-last-two-runs` 和 `--compare-runs` 各适合什么场景？
5. 为什么 compare 逻辑放在 `agent/replay.py` 和 `agent/core.py`，而不是直接堆在 CLI 中？

## 练习 3：动手验证

先运行：

```bash
python -m cli.main --input "Use LangGraph to read README.md." --trace
python -m cli.main --input "Read README.md and then count lines." --trace
```

再运行：

```bash
python -m cli.main --compare-last-two-runs
```

请记录：

1. 输出是否包含 `Replay diff report`？
2. 是否能看到 `Older run:` 和 `Newer run:`？
3. 是否能看到 `Differences:`？
4. 是否能看到 `Step count delta:` 和 `Runtime event delta:`？

再运行：

```bash
python -m cli.main --compare-runs <older_run_id> <newer_run_id>
```

请记录：

1. 是否可以比较指定的两次运行？
2. 输出中能否看到 route / graph route / tool / skill 等摘要信息？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么 compare 是 recovery 的前置能力？
2. 为什么 `answer` 比较现在只做“是否变化”，而不做“质量判断”？
3. 未来如果做 `checkpoint-guided recovery`，最可能复用 `v37` 的哪些数据结构或比较视角？

## 答案

### 练习 1：理解本阶段目标

1. `v37` 先做 replay diff，是因为 recovery 之前必须先有稳定的差异证据。系统需要先回答“两次运行到底哪里不同”，才能进一步决定哪些状态可以恢复、哪些分支值得继续执行。如果没有 diff，recovery 很容易变成黑箱操作。
2. `ReplaySummary` 的职责是把原始 checkpoint 中适合比较的核心事实提炼出来，例如 route、graph route、step 数量、runtime event 数量、tool / skill 使用摘要、recovery 状态和 answer。它相当于 compare 之前的稳定中间层。
3. `ReplayReport` 面向单次运行回放，重点是把一次 run 的历史过程重新组织成可阅读报告；`ReplayDiffReport` 面向两次运行比较，重点是指出哪些执行事实发生了变化，以及变化集中在哪些维度。
4. 这个版本只比较稳定的结构化字段，是为了让结果可重复、可测试、可审计。LLM 语义 diff 会引入主观性和不确定性，不适合作为当前阶段的基础比较层。
5. 这个版本符合“一个大功能版本”的要求，因为它不是补一个参数或字段，而是把 replay 从单次阅读能力推进到跨 run 分析能力，覆盖了数据模型、Agent 入口、CLI、测试、文档和练习的完整闭环。

### 练习 2：读 compare 链路

1. `ReplaySummary` 的关键字段包括：`run_id`、`run_kind`、`created_at`、`user_input`、`route_action`、`route_tool`、`graph_route`、`answer`、`step_count`、`runtime_event_count`、`tool_names`、`skill_names`、`has_recovery` 和 `failure_type`。
2. `compare_replay_reports()` 当前比较的差异包括：`route`、`graph_route`、`step_count`、`runtime_event_count`、`answer`、`tool_usage`、`skill_usage` 和 `recovery`。这些都是相对稳定、适合自动比较的结构化维度。
3. `WorkspaceAgent.compare_latest_two_checkpoints()` 用于快速比较最近两次历史运行，适合开发和学习时立刻复盘；`compare_checkpoints()` 用于比较指定 run id，对定点分析某两次运行更合适。
4. `--compare-last-two-runs` 适合刚做完两次实验，想立即看差异；`--compare-runs` 适合你已经从 run history 中选好了两个目标 run，想做精确比较。
5. compare 逻辑放在 `agent/replay.py` 和 `agent/core.py`，是因为这属于业务能力和领域逻辑。CLI 只负责解析参数和调用能力，如果把比较逻辑堆在 CLI，中间层就会变薄，后续也不利于测试、复用和扩展。

### 练习 3：动手验证

1. 输出应当包含 `Replay diff report`，因为这是 diff 模式的主标题，用来明确当前输出是两次历史运行的比较报告。
2. 输出应当包含 `Older run:` 和 `Newer run:`，因为 diff 报告必须先明确比较双方是谁，否则后面的差异解释没有参照基线。
3. 输出应当包含 `Differences:`，因为这个部分是比较报告的核心，直接列出哪些维度发生了变化。
4. 输出应当包含 `Step count delta:` 和 `Runtime event delta:`，因为这两个量化指标能快速提示运行复杂度和执行路径是否发生明显变化。
5. `python -m cli.main --compare-runs <older_run_id> <newer_run_id>` 应当可以比较指定的两次运行，只要这两个 run id 对应的 checkpoint 存在。
6. 输出中应当能看到 route / graph route / tool / skill 等摘要信息，因为 `ReplaySummary` 和 `ReplayDiffReport` 的设计目标就是把这些工业级执行证据明确暴露出来。

### 练习 4：工程取舍题

1. compare 是 recovery 的前置能力，因为 recovery 不只是“重新跑一下”，而是要基于历史状态做有依据的继续执行。只有先知道两次运行在哪些点上分叉，系统才能讨论从哪里恢复才合理。
2. `answer` 比较现在只做“是否变化”，而不做“质量判断”，是因为质量判断往往需要更复杂的标准，甚至需要 LLM 或人工评估，而这会让当前阶段失去确定性。`v37` 的目标是建立稳定比较层，不是建立答案裁判系统。
3. 未来做 `checkpoint-guided recovery` 时，最可能复用 `v37` 的 `ReplaySummary`、`ReplayDiffReport` 以及 route / graph route / step count / recovery 状态这些比较视角。因为恢复首先要知道系统上次停在什么路径、这次和上次差在哪，再决定是否继续执行或分叉恢复。

## 验证

```bash
python -m unittest tests.test_persistence -v
python -m cli.main --compare-last-two-runs
```
