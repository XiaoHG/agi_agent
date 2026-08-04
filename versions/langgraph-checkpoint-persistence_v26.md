# v26：LangGraph Checkpoint and Recoverable Run Persistence

## 本阶段目标

把 LangGraph 运行结果从“只存在于一次内存执行中”升级为“可持久化、可恢复、可回放”的运行记录。

## 本阶段已完成的实现

### `agent/persistence.py`

160 行。

关键内容：

- 第 12-36 行：`RunCheckpointStore`，负责保存和读取最近一次 checkpoint。
- 第 39-67 行：`build_run_checkpoint()`，把 `WorkspaceAgent` 运行结果整理成 JSON-ready 记录。
- 第 70-104 行：`build_graph_checkpoint()`，把 LangGraph 原始 state 整理成可落盘记录。
- 第 107-130 行：`load_checkpoint()` 和 `format_checkpoint_summary()`，支持读取最近 checkpoint 和输出摘要。
- 第 133-160 行：内部辅助函数，处理 run id、时间戳和摘要预览。

### `agent/core.py`

719 行。

关键内容：

- 第 15-16 行：引入 runtime events 和 checkpoint persistence helper。
- 第 60-74 行：`WorkspaceAgent.__init__()` 新增 `history_dir`，默认写入 `logs/agent-runs`。
- 第 91-103 行：workflow 分支执行结束后持久化运行记录。
- 第 105-120 行：LangGraph 分支执行结束后持久化运行记录。
- 第 458-490 行：新增 `_persist_run()`、`load_latest_checkpoint()` 和 `format_checkpoint_summary()`。
- 第 639-718 行：`format_trace()` 和 `to_trace_dict()` 继续导出 runtime events，为 checkpoint 提供结构化 trace。

### `cli/main.py`

83 行。

关键内容：

- 第 15-23 行：新增 `--history-dir` 和 `--show-last-run`。
- 第 34-45 行：新增 `show_last_run()`，可查看最近一次 checkpoint。
- 第 66-79 行：main 入口支持输入运行和查看最近运行两种模式。

### `cli/langgraph_demo.py`

69 行。

关键内容：

- 第 19-23 行：新增 `--history-dir`。
- 第 33-43 行：LangGraph 运行结束后自动保存 graph checkpoint。
- 第 55-65 行：新增 graph 输出格式化函数，用于保存 checkpoint 文本。

### `tests/test_persistence.py`

124 行。

覆盖内容：

- checkpoint store 的保存与读取。
- `WorkspaceAgent` graph run 的持久化。
- `WorkspaceAgent` workflow run 的持久化。
- `cli.main --show-last-run` 的查看逻辑。
- `cli.langgraph_demo` 的 graph checkpoint 落盘。

## 运行行为

### 1. Agent run 会被持久化

当 `WorkspaceAgent.run()` 完成一次运行后，会把以下信息保存为 checkpoint。对于 graph 路径，checkpoint 里还会包含 graph route、graph steps、tool status、recovery plan 等 metadata。

- run id
- run kind
- user input
- route
- steps
- tool result
- tool error
- answer
- trace
- trace text

默认路径：

```text
<workspace_root>/logs/agent-runs/
```

### 2. CLI 可以查看最近一次运行

```bash
python -m cli.main --show-last-run
```

如果加上 `--trace`，会直接输出最近一次 checkpoint 的完整 trace 文本。

### 3. LangGraph demo 也会保存 checkpoint

```bash
python -m cli.langgraph_demo --question "Read README.md."
```

如果不显式传 `--history-dir`，会保存到：

```text
<root>/logs/graph-runs/
```

## 设计取舍

### 为什么先做本地 JSON checkpoint

因为当前阶段最重要的不是分布式，而是：

- 能保存
- 能读取
- 能复盘
- 能继续扩展成 replay / 审计 / 恢复

本地 JSON 足够支撑下一阶段学习，不会过早引入复杂基础设施。

### 为什么 checkpoint 继续保存 JSON-ready dict

因为后续要做：

- replay
- eval
- 人工复盘
- 可能的外部持久化

这些都更适合使用稳定的 JSON-ready 结构，而不是 Python 对象。

## 验证结果

已运行：

```bash
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.main --show-last-run --trace
python -m cli.langgraph_demo --question "Read README.md."
```

结果：

- 全量 126 个测试通过。
- 17 个 eval case 全部通过。
- 最近运行查看可用。
- LangGraph demo 可正常保存 checkpoint。

## 下阶段建议

v26 的下一步不是继续堆功能，而是把 checkpoint 演进成 replay：

- 从 checkpoint 恢复 state
- 基于 runtime events 回放 run
- 为失败 run 提供更明确的恢复入口
