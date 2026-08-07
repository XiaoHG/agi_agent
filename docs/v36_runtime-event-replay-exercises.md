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

1. 因为 checkpoint 解决的是“保存”，replay 解决的是“重看”。
2. replay 报告基于保存的运行事实生成，而不是重新执行运行。
3. 因为 replay 需要兼顾人类阅读和结构化分析。
4. 因为 checkpoint 存的是 dict，runtime events 需要从这些稳定数据重建。
5. 因为 replay 让历史运行可审计、可比较，也更容易为后续恢复功能打底。

## 验证

```bash
python -m unittest tests.test_persistence -v
python -m cli.main --replay-last-run
```
