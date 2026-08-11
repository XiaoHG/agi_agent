# v46：Checkpoint Branch Resume

## 本阶段目标

把项目从“checkpoint-guided rerun”升级为“可追踪的 branch resume”，让恢复后的运行成为历史 checkpoint 的正式分支。

## 本阶段在工业 Agent 中的位置

工业 Agent 的恢复能力不能只停留在：

- 重新打印恢复计划
- 按原输入再跑一次
- 让开发者自己猜这次运行和哪次历史运行有关

它必须具备：

- 明确的分支来源
- 持久化的 branch lineage
- 恢复前后可比较
- 嵌套 resume 的深度信息

`v46` 解决的是“checkpoint 恢复如何成为正式的可续跑分支，而不是一次无来源的重试”。

## 本阶段解决的问题

- 让 resume 后的新运行显式挂接到源 checkpoint
- 让 checkpoint summary / history / replay summary 看得见 branch parent 和 branch depth
- 让连续 resume 形成稳定的分支深度
- 让恢复报告不再只有计划，还能显示分支化后的结果

## 本阶段新增能力

### 1. Branch resume 数据模型

新增或增强：

- `CheckpointResumePlan` 增加 branch session / task / depth
- `ReplaySummary` 增加 branch parent / branch depth
- `build_checkpoint_branch_record()` 生成分支 lineage 元数据

### 2. Checkpoint 持久化分支元数据

增强：

- `build_run_checkpoint()` 现在支持 `resume`
- checkpoint summary / history 会显示 branch parent 和 branch depth
- structured trace 会同步写入 `resume`

### 3. Resume 变成正式 branch run

增强：

- `WorkspaceAgent.resume_latest_checkpoint()`
- `WorkspaceAgent.resume_checkpoint()`

现在 resume 后的新 checkpoint 会带上：

- `source_run_id`
- `source_run_kind`
- `source_created_at`
- `resume_mode`
- `branch_depth`
- `session_id`
- `task_id`

### 4. 嵌套 resume 验证

新增测试覆盖：

- 首次 branch resume
- 嵌套 branch resume 深度递增
- CLI resume 输出包含 branch depth

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `agent/persistence.py` | 为 checkpoint 增加 branch resume 元数据 |
| `agent/replay.py` | 增加 branch lineage summary / resume plan |
| `agent/core.py` | 让 resume 生成正式 branch run |
| `tests/test_persistence.py` | 增加 branch resume 测试 |
| `evals/matrix/v44_replay_cases.json` | 恢复类 eval 增加 branch 信息断言 |
| `docs/current-learning-state.md` | 更新当前学习状态 |
| `docs/plans/v3_professional-agent-iteration-plan.md` | 补充 v46 规划 |

## 核心实现说明

### 1. 为什么 branch lineage 必须持久化

因为恢复后的运行如果没有来源关系，就无法回答：

- 这是从哪次失败恢复出来的？
- 这是第几层恢复分支？
- 这次恢复和原始运行差在哪里？

工业系统需要把这些关系变成正式数据，而不是靠人肉记忆。

### 2. 为什么 branch depth 很重要

因为一次恢复和多次连续恢复在工程意义上不同。

`branch_depth` 可以帮助系统和学习者判断：

- 当前运行离原始任务已经偏了多远
- 是否进入了过深的恢复链
- 是否需要人工干预而不是继续自动恢复

### 3. 为什么不新开一套 resume CLI

因为本项目已有 `resume-last-run` / `resume-run` 入口。

`v46` 的重点不是“再加一个命令”，而是把现有恢复入口升级成真正的 branch resume。

## 运行示例

恢复最新 checkpoint，并生成 branch run：

```bash
python -m cli.main --resume-last-run
```

恢复指定 checkpoint，并生成 branch run：

```bash
python -m cli.main --resume-run abc12345
```

查看最近运行列表中的 branch parent / depth：

```bash
python -m cli.main --list-runs
```

## 验证命令

```bash
python -m unittest tests.test_persistence -v
python -m unittest tests.test_evals -v
python -m unittest discover -s tests -v
python -m cli.main --resume-last-run
```

## 当前边界

- 这是本地 branch resume，不是多副本分布式恢复系统
- 还没有做自动的“分支过深阻断”策略
- 还没有做恢复树可视化，只提供文本和结构化 lineage

## 下一步建议

下一阶段建议进入 `v47`，继续做标准化 MCP 治理，把工具协议和权限边界推进到更接近可交付状态。
