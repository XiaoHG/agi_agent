# v37：Run Replay Diff and Comparative Analysis

## 本阶段目标

把 `v36` 的单次 replay 能力升级为跨 run 的对比分析能力，让项目从“能回放一次运行”推进到“能比较两次运行为什么不同”。

## 本阶段在工业 Agent 中的位置

在工业 Agent 工程里，checkpoint 和 replay 只有在能支持比较时，才真正进入可审计、可回归、可复盘阶段。

单次 replay 解决的是：

- 这次运行发生了什么

跨 run diff 解决的是：

- 这次运行和上次有什么不同
- 差异发生在 route、graph route、steps、runtime events，还是 answer
- 哪些工具、技能或恢复路径发生了变化

这一步是后续 `checkpoint-guided recovery and resume` 的前置能力。

## 本阶段解决的问题

- 让 replay 不再只是一份历史报告
- 让 run history 从“能看”升级为“能比”
- 让后续 recovery 有差异证据基础
- 让学习者能直接观察多次运行在执行路径上的变化

## 本阶段新增能力

### 1. replay summary

新增 `ReplaySummary`，把单次 run 提炼为稳定、可比较的摘要视图，包含：

- run id
- run kind
- user input
- route action / route tool
- graph route
- answer
- step count
- runtime event count
- tool names
- skill names
- recovery / failure type 摘要

### 2. replay diff report

新增 `ReplayDiffReport`，用于比较两次历史 run 的差异，重点覆盖：

- route 是否变化
- graph route 是否变化
- step count 是否变化
- runtime event count 是否变化
- answer 是否变化
- tool usage 是否变化
- skill usage 是否变化
- recovery 状态是否变化

### 3. Agent compare 入口

`WorkspaceAgent` 新增：

- `compare_latest_two_checkpoints()`
- `compare_checkpoints(older_run_id, newer_run_id)`

这样比较逻辑由 `agent/` 负责，而不是散落在 CLI。

### 4. CLI compare 入口

新增命令：

```bash
python -m cli.main --compare-last-two-runs
python -m cli.main --compare-runs <older_run_id> <newer_run_id>
```

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `agent/replay.py` | 增加 replay summary、diff report 和 compare helpers |
| `agent/core.py` | 暴露 compare latest two / compare selected runs |
| `cli/main.py` | 增加 compare CLI 参数与入口 |
| `cli/README.md` | 增加 compare 命令说明 |
| `tests/test_persistence.py` | 增加 replay diff 和 compare CLI 测试 |
| `docs/current-learning-state.md` | 更新当前学习阶段状态 |

## 核心实现说明

### 1. 为什么先做 diff，而不是直接做 recovery

因为 recovery 之前必须先有稳定的“差异证据”。

如果系统连下面这些问题都回答不了：

- 两次 run 的 route 为什么不同
- graph route 为什么变了
- 哪次用了更多 step
- 哪次进入了 recovery

那后续就很难做 resume 边界判断，也很难解释“为什么从这里恢复”。

### 2. 为什么使用 summary 而不是直接比较原始 checkpoint

原始 checkpoint 信息很多，也不是每个字段都适合直接比较。

`ReplaySummary` 的作用是先把可稳定比较的工业证据提取出来，再做 diff。这样：

- 比较逻辑更稳定
- 输出更容易阅读
- 未来更容易扩展到 UI、审计或 eval 分析

### 3. 当前 diff 的边界

本阶段只做稳定、结构化、低风险的比较，不做：

- LLM 语义 diff
- 自动判断“哪个答案更好”
- 自动 recovery continuation
- graph state 分叉恢复

也就是说，这仍然是分析层能力，不是恢复执行层能力。

## 运行示例

先产生两次运行：

```bash
python -m cli.main --input "Use LangGraph to read README.md." --trace
python -m cli.main --input "Read README.md and then count lines." --trace
```

比较最近两次运行：

```bash
python -m cli.main --compare-last-two-runs
```

比较指定运行：

```bash
python -m cli.main --compare-runs abc12345 def67890
```

## 验证命令

```bash
python -m unittest tests.test_persistence -v
python -m unittest tests.test_agent tests.test_langgraph_workflow -v
```

## 当前限制

- 还没有做真正的 checkpoint-guided resume
- 还没有做跨 run 的 graph state 级 diff
- 还没有做 answer 语义比较
- 还没有把 diff 纳入 eval summary 输出

## 下一步建议

下一阶段应进入：

`v38：Checkpoint-Guided Recovery and Resume`

重点是让 checkpoint、replay 和 recovery 从“能看、能比”推进到“能从历史状态继续执行”。
