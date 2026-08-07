# v36：Runtime Event Replay

## 本阶段目标

把已经存在的 checkpoint、trace 和 runtime events 进一步整合成可回放的运行历史报告，让项目从“能保存运行”推进到“能回放运行”。

## 本阶段解决的问题

- 让 checkpoint 不只是存档。
- 让 runtime events 不只是导出。
- 让历史运行可以被重新阅读、比较和复盘。

## 本阶段新增文件

| 文件 | 作用 |
| --- | --- |
| `agent/replay.py` | replay 报告构建与格式化 |
| `versions/v36_runtime-event-replay.md` | 本阶段版本说明 |
| `docs/v36_runtime-event-replay-exercises.md` | 本阶段练习 |

## 本阶段修改文件

| 文件 | 主要变化 |
| --- | --- |
| `agent/events.py` | runtime events 支持从 checkpoint dict steps 回放 |
| `agent/core.py` | 增加 replay 最新 checkpoint / 指定 checkpoint 的能力 |
| `cli/main.py` | 增加 `--replay-last-run` 和 `--replay-run` |
| `tests/test_persistence.py` | 增加 replay 相关测试 |
| `agent/__init__.py` | 导出 replay 相关函数 |

## 核心实现说明

### 1. replay 不是重新执行模型

本阶段的 replay 不是重新调用 LLM 重新生成结果，而是基于 checkpoint 里的 trace、steps、answer 和 runtime events 生成一份结构化回放报告。

### 2. runtime events 从 checkpoint 重建

`build_runtime_events()` 现在可以直接读取 checkpoint 里的 dict 形式 steps，这样 replay 不必依赖内存对象。

### 3. CLI 支持 replay

新增命令：

```bash
python -m cli.main --replay-last-run
python -m cli.main --replay-run abc12345
```

## 当前限制

- 这还是报告级 replay，不是完整的“跨版本确定性重放”。
- 没有做事件流 diff，也没有做运行恢复分叉。

## 下一步建议

- 给 replay 增加事件对比。
- 给 replay 增加 checkpoint 路径和摘要。
- 让 runtime events replay 和 graph state recovery 更紧密地结合。
