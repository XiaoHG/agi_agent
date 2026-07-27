# 当前学习进度状态

此文件用于跨会话恢复学习进度。每次学习任务结束后都应更新。

## Last Updated

2026-07-26

## 当前阶段

Week 5：工程化、评估与稳定性。

当前状态：最小 eval runner 和结构化 trace 已开始实现。

## 当前教师判断

项目已经从“能力复用与角色协作”进入“可复现评估与可观测性”阶段。

已具备：

- Week 1 最小 CLI Agent
- Week 2 状态与工作流
- Week 3 本地 RAG 最小闭环
- Week 3 本地 MCP 最小骨架
- Week 4 Skills/Subagent 最小协作层
- 结构化 trace 导出
- JSON eval cases
- deterministic eval runner
- eval CLI
- 自动化测试

当前缺口：

- eval runner 仍是规则判断，没有人工评分维度。
- 结构化 trace 只在内存中导出，还没有统一写入日志文件。
- 还没有错误分类体系。
- 还没有 Week 5 阶段复盘。

## 当前总目标

先巩固工程化最小闭环：让 Agent 的行为可以被重复运行、结构化记录、自动判断。

最小工程化链路：

```text
Eval cases -> Agent run -> Structured trace -> Eval report -> Regression result
```

## 当前具体任务

下一步建议：

1. 由 Teacher Agent 讲解 eval runner 和结构化 trace。
2. 手动运行 `python -m cli.eval_runner`。
3. 增加更多 eval case。
4. 写 Week 5 阶段复盘。
5. 再评估是否进入 Week 6 综合项目。

## 当前学习重点

学习者需要重点理解：

- 测试验证代码行为，eval 验证 Agent 行为。
- trace 是定位 Agent 失败的核心证据。
- eval case 要可重复、可比较、可扩展。
- 工程化不是堆功能，而是让系统可调试、可回归、可维护。

## 已完成

- 初始化项目目录。
- 完成 Week 1 最小 CLI Agent。
- 完成 Week 2 状态与工作流实现。
- 完成 Week 3 本地 RAG 最小闭环。
- 完成 Week 3 本地 MCP 最小骨架。
- 完成 Week 4 Skills/Subagent 最小协作层。
- 提交 RAG 阶段代码：`03c0005 Add local RAG search stage`。
- 提交 MCP 阶段代码：`04746a4 Add local MCP protocol stage`。
- 提交 Skills/Subagent 阶段代码：`375de6f Add skills and subagent collaboration stage`。
- 开始实现 Week 5 eval runner 和结构化 trace。

## 未完成

- Week 5 评估复盘。
- 更多 eval cases。
- 日志落盘。
- 错误分类。
- 综合项目选题。

## 恢复指令

下一个会话恢复时，请先读取：

1. `AGENTS.md`
2. `docs/current-learning-state.md`
3. `docs/learning-master-plan.md`
4. `evals/README.md`
5. `evals/regression_cases.json`
6. `evals/runner.py`
7. `tests/test_evals.py`
8. `versions/engineering-evals-observability_v6.md`

然后继续执行当前具体任务。

## 下一步建议

下一步优先让 Teacher Agent 讲解这次新增代码：

- `evals/runner.py`
- `evals/regression_cases.json`
- `cli/eval_runner.py`
- `agent/core.py` 中的 `to_trace_dict()`
