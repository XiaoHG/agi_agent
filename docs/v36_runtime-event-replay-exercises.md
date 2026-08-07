# Runtime Event Replay v36 练习

对应版本：v36  
主题：Runtime Event Replay  
用途：理解如何把 checkpoint 转成可阅读、可比较的 replay 报告

## 练习 1：理解本阶段目标

请回答：

1. v36 为什么不是“再做一个 checkpoint”，而是“做 replay”？
2. replay 报告和原始 checkpoint 的关系是什么？
3. 为什么 replay 不应该重新调用 LLM？
4. `build_runtime_events()` 为什么要支持 checkpoint dict steps？
5. 为什么 replay 对后续恢复和审计有价值？

## 练习 2：读 replay 链路

阅读：

- `agent/replay.py`
- `agent/events.py`
- `agent/persistence.py`
- `agent/core.py`
- `cli/main.py`

请回答：

1. `ReplayReport` 记录了哪些字段？
2. `build_replay_report()` 做了什么？
3. `format_replay_report()` 输出了哪些关键部分？
4. `WorkspaceAgent.replay_latest_checkpoint()` 和 `replay_checkpoint()` 的差异是什么？
5. `--replay-last-run` 和 `--replay-run` 分别适合什么场景？

## 练习 3：动手验证

运行：

```bash
python -m cli.main --input "Use LangGraph to read README.md." --trace
python -m cli.main --replay-last-run
```

请记录：

1. replay 报告是否包含 `Replay report`？
2. 是否包含 `Runtime events:`？
3. 是否能看到 `Graph route:`？

再运行：

```bash
python -m cli.main --replay-run <run_id>
```

请记录：

1. 是否能回放指定 run id？
2. 输出中是否保留了原始 trace 的主要信息？

## 练习 4：阶段评估题

请用自己的话回答：

1. 为什么 replay 是 checkpoint 的自然下一步？
2. 报告级 replay 和真正的 runtime recovery 有什么区别？
3. replay 功能为什么必须保留 trace_text？

## 答案

### 练习 1：理解本阶段目标

1. v36 的重点不是继续增加一个新的 checkpoint 存储点，而是把已经落盘的数据真正利用起来。checkpoint 负责保存运行事实，replay 负责把这些事实重新组织成可阅读、可复盘的报告，所以它是持久化能力向审计能力的自然推进。
2. replay 报告和原始 checkpoint 的关系是“基于事实的派生视图”。checkpoint 是原始结构化记录，replay 报告是在不改动原始记录的前提下，把 trace、steps、runtime events、answer 和 route 信息整理成一份适合人类阅读和后续分析的输出。
3. replay 不应该重新调用 LLM，因为 replay 的目标是复现历史运行事实，而不是再生成一次“可能不同”的新结果。只要重新调模型，就会引入不确定性，也会让 replay 失去审计价值。
4. `build_runtime_events()` 需要支持 checkpoint dict steps，是因为 checkpoint 落盘后的 step 数据本来就是 JSON-ready 的 dict 结构。只有支持从 dict 重建事件，replay 才能脱离内存对象独立工作，真正从持久化记录回放。
5. replay 对后续恢复和审计有价值，因为它让历史 run 变成可查看、可比较、可定位问题的证据。后面不管是做恢复策略、差异分析，还是人工排查失败点，都需要先可靠地“看见”过去发生了什么。

### 练习 2：读 replay 链路

1. `ReplayReport` 记录的是一次回放所需的核心信息，包括 run 标识、时间、route 信息、graph route 信息、原始 answer、原始 trace text、checkpoint 中已有的 runtime events，以及基于 steps 重建出的 runtime events。
2. `build_replay_report()` 的职责是读取 checkpoint record，提取基础元数据，优先使用 trace 里的 steps 或 record 里的 steps 重建 runtime events，再把 recorded events、rebuilt events、trace text、answer 等内容组装成一个 `ReplayReport`。
3. `format_replay_report()` 输出的关键部分包括：回放标题、run 元数据、route 摘要、graph route、recorded 与 rebuilt runtime event 数量、runtime events 明细、answer，以及原始 trace 文本。
4. `WorkspaceAgent.replay_latest_checkpoint()` 是读取最近一次保存的 run 并生成回放；`replay_checkpoint(run_id)` 是按指定 run id 精确回放。前者适合快速查看刚刚发生的运行，后者适合针对某一次历史记录做定点复盘。
5. `--replay-last-run` 适合开发时立即复盘上一条运行结果，比如刚执行完一次 CLI demo 想直接查看回放；`--replay-run` 适合你已经知道目标 run id，想回看某次特定历史运行。

### 练习 3：动手验证

1. replay 报告应当包含 `Replay report`，因为这是 `ReplayReport.to_text()` / 格式化输出的标题，用来明确当前输出不是实时执行结果，而是一次历史回放报告。
2. 输出应当包含 `Runtime events:`，因为 v36 的核心就是把 checkpoint 中已有事件和重建事件整理成可阅读的事件列表。
3. 如果这次运行是走 graph 路由，并且 route 里带有 tool 或 graph 目标信息，那么输出中应当看到 `Graph route:`。这说明 replay 不只保留了最终答案，也保留了主执行路径。
4. `python -m cli.main --replay-run <run_id>` 应当可以回放指定 run id，只要该 run 已经被 checkpoint store 持久化。
5. 输出中应当保留原始 trace 的主要信息，因为 replay 不是只展示摘要，它还要把原始 trace text 作为人工排查和学习复盘的重要证据保留下来。

### 练习 4：阶段评估题

1. replay 是 checkpoint 的自然下一步，因为“先保存、再回看”是最基本的工程闭环。只有把保存下来的运行记录重新读出来，checkpoint 才真正从存档能力升级为调试、审计和复盘能力。
2. 报告级 replay 和真正 runtime recovery 的区别在于：报告级 replay 只是根据保存的数据重建事件和文本报告，不会继续执行图、工具或模型；runtime recovery 则需要在某个中断点恢复状态并继续往后跑，这对状态完整性、确定性和恢复边界要求更高。
3. replay 功能必须保留 `trace_text`，因为结构化事件虽然便于程序处理，但人类排查问题时仍然需要原始运行叙事。`trace_text` 能补足上下文、保留当时的说明信息，也方便学习者把结构化事件和真实运行过程对应起来。

## 验证

```bash
python -m unittest tests.test_persistence -v
python -m cli.main --replay-last-run
```
