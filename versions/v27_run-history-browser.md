# v27：Run History Browsing and Checkpoint Lookup

## 本阶段目标

把已有的 checkpoint 进一步升级成可浏览的 run history，并支持按 run id 精确查看单次运行。

## 本阶段已完成的实现

### `agent/persistence.py`

新增：

- `RunCheckpointStore.load_run()`
- `RunCheckpointStore.list_runs()`
- `format_checkpoint_history()`

作用：

- 支持按 run id 读取 checkpoint
- 支持列出最近的 checkpoint
- 支持把历史记录整理成可读摘要

### `agent/core.py`

新增：

- `load_checkpoint(run_id)`
- `list_checkpoint_history(limit=10)`

作用：

- 让 Agent 自己具备 run history 读取能力
- CLI 不再直接操作文件细节

### `cli/main.py`

新增：

- `--list-runs`
- `--show-run <run_id>`

作用：

- 可列出最近保存的运行
- 可按 run id 查看任意一次运行

### `cli/README.md`

补充了新 CLI 命令说明。

### `tests/test_persistence.py`

新增测试覆盖：

- 历史列表
- 按 run id 查看

## 运行行为

### 列出最近运行

```bash
python -m cli.main --list-runs
```

输出会显示：

- run id
- run kind
- created at
- route

### 查看指定运行

```bash
python -m cli.main --show-run <run_id> --trace
```

这个命令适合做单次运行复盘，不需要先猜 latest。

## 设计取舍

### 为什么不直接做完整 replay

因为当前阶段更重要的是把“能找回记录”先做稳。

run history 浏览解决的是：

- 这次都跑过什么
- 哪个 run 是最新的
- 哪个 run 值得重点复盘

replay 解决的是：

- 能不能重建状态
- 能不能继续执行
- 能不能复现中间过程

先把浏览入口做稳，再往 replay 走更合理。

## 验证结果

已验证：

```bash
python -m unittest tests.test_persistence -v
python -m unittest discover -s tests -v
python -m cli.main --list-runs
python -m cli.main --show-run <run_id> --trace
```

## 下一步建议

v27 后续可以继续往两个方向走：

1. 从 checkpoint 做 replay preview。
2. 把 run history 接成一个更完整的学习复盘入口。
