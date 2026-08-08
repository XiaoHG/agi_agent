# v38：Checkpoint-Guided Recovery and Resume

## 本阶段目标

把 `v37` 的 replay diff 和 checkpoint 浏览能力，推进为基于 checkpoint route hints 的 guided resume 能力，让项目从“能比较历史运行”继续迈向“能根据历史 checkpoint 重新进入同一条执行路径”。

## 本阶段在工业 Agent 中的位置

工业级 Agent 的 checkpoint 不能只用于存档、回放和比较，还要能指导后续执行。

这一阶段的重点是：

- 从 checkpoint 提取可执行的 route hints
- 基于这些 hints 重新进入同一条执行路径
- 把 resume 过程结构化地报告出来
- 让恢复不再只是静态说明，而是可执行的重新进入

## 本阶段解决的问题

- 让 checkpoint 不只是历史记录
- 让 replay / diff 继续向 recovery 过渡
- 让 Agent 具备 guided resume 的最小工业闭环
- 让学习者看到“比较历史”如何走向“重新进入历史路径”

## 本阶段新增能力

### 1. checkpoint resume plan

新增 `CheckpointResumePlan`，用于从 checkpoint 中提取：

- source run id
- source run kind
- route action / route tool
- graph route
- failure type
- recovery presence
- resume mode
- next safe action

### 2. checkpoint resume report

新增 `CheckpointResumeReport`，用于把：

- resume plan
- source summary
- resumed summary
- resumed diff

组织成一份可读、可比较的恢复报告。

### 3. guided resume CLI

新增命令：

```bash
python -m cli.main --resume-last-run
python -m cli.main --resume-run abc12345
```

### 4. route-guided rerun

`WorkspaceAgent.run()` 现在支持 route override，`resume_checkpoint()` 会根据 checkpoint 的 route hints 重新进入执行路径。

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `agent/replay.py` | 增加 resume plan / resume report |
| `agent/core.py` | 增加 checkpoint-guided resume 入口 |
| `agent/__init__.py` | 导出 resume 相关函数 |
| `cli/main.py` | 增加 resume CLI 参数与入口 |
| `cli/README.md` | 增加 resume 命令说明 |
| `tests/test_persistence.py` | 增加 resume 相关测试 |
| `docs/current-learning-state.md` | 更新当前学习状态 |

## 核心实现说明

### 1. 为什么这一步不是完整 recovery

因为真正的 recovery 需要更完整的状态分叉、继续执行边界和失败恢复策略。

本阶段先做的是：

- 从 checkpoint 提取稳定 route hints
- 用这些 hints 重新进入执行路径

这属于 guided resume，不是状态机级完整恢复。

### 2. 为什么要保留 resume plan

resume plan 的作用是把“能不能恢复、为什么这样恢复、下一步怎么做”写成结构化数据。

这样后续可以继续扩展：

- 自动分叉恢复
- 人工审批恢复
- 失败类型分流
- resume 回归测试

### 3. 当前边界

本阶段暂时不做：

- 真正的状态级 continue execution
- 图执行中断点续跑
- 自动重试策略优化
- LLM 语义 resume 决策

## 运行示例

先产生一次 checkpoint：

```bash
python -m cli.main --input "Use LangGraph to read README.md." --trace
```

再从最新 checkpoint 恢复：

```bash
python -m cli.main --resume-last-run
```

或者按 run id 恢复：

```bash
python -m cli.main --resume-run abc12345
```

## 验证命令

```bash
python -m unittest tests.test_persistence -v
python -m unittest tests.test_agent tests.test_langgraph_workflow -v
```

## 下一步建议

下一阶段应进入：

`v39：LLM-First Direct Answer and Intent Entry`

重点是把顶层 direct answer 入口升级为真正的 LLM-first 路由与回答入口。
