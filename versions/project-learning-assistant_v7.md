# 综合项目学习助手 v7

版本：v7

日期：2026-07-27

## 本次目标

进入 Week 6：综合项目。

本次实现一个最小可运行的 Project Learning Assistant，用于把前面阶段的能力组合成一个完整项目原型：

```text
文件读取 -> 本地 RAG -> MCP 工具 -> Skill 选择 -> Subagent 协作规划 -> 回归评估 -> 项目报告
```

## 新增文件

### `agent/project.py`

行号范围：`1-102`

职责：

- 定义 `ProjectLearningReport`
- 定义 `ProjectLearningAssistant`
- 复用 `WorkspaceAgent` 完成综合项目能力编排
- 复用 `evals.runner` 执行 deterministic regression eval
- 输出可读的项目报告

核心新增逻辑：

- `ProjectLearningAssistant.run()` 是综合项目主流程。
- `_run_regression_eval()` 负责运行现有回归用例。
- `_preview_run()` 负责压缩每一步 Agent 输出，避免报告过长。

### `cli/project_demo.py`

行号范围：`1-37`

职责：

- 提供 Week 6 综合项目命令行入口。
- 支持 `--root` 指定工作区。
- 支持 `--objective` 指定本次项目演示目标。
- 当回归评估失败时返回非 0 exit code。

### `tests/test_project.py`

行号范围：`1-47`

职责：

- 验证综合项目能力链路可以运行。
- 验证报告文本包含关键部分。
- 验证 CLI demo 返回成功状态码。

### `examples/project-learning-assistant/README.md`

行号范围：`1-45`

职责：

- 记录综合项目示例的运行方式。
- 说明本阶段能力链路。
- 说明本阶段学习重点。

## 修改文件

### `README.md`

新增变更：

- 当前 Demo 列表新增综合项目运行命令。
- 当前阶段更新为 Week 6 综合项目。
- 第 6 周章节补充本仓库当前选题。
- 下一步建议更新为理解和练习综合项目链路。

### `docs/current-learning-state.md`

新增变更：

- 当前阶段更新为 Week 6。
- 当前总目标更新为完成 Project Learning Assistant。
- 当前任务更新为理解综合项目代码、运行 demo、补充真实示例。
- 恢复指令新增 Week 6 文件。

## 新增交互流程

### 综合项目主流程

```text
python -m cli.project_demo
  -> ProjectLearningAssistant.run()
  -> WorkspaceAgent reads README.md
  -> WorkspaceAgent searches local docs
  -> WorkspaceAgent calls MCP workspace summary
  -> WorkspaceAgent selects a skill
  -> WorkspaceAgent plans subagent collaboration
  -> eval runner validates regression cases
  -> ProjectLearningReport.to_text()
```

### 为什么不直接改 `WorkspaceAgent.run()`

当前综合项目是应用层原型，不是新的基础路由能力。

如果把综合项目逻辑直接写进 `WorkspaceAgent.run()`，主 Agent 会很快变成混杂了基础能力和具体业务流程的代码。现在单独新增 `agent/project.py`，可以保持：

- `WorkspaceAgent` 继续负责基础 Agent loop。
- `ProjectLearningAssistant` 负责综合项目编排。
- 后续如果要做真实产品，可以继续在项目层扩展。

## 验证命令

```bash
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.project_demo
```

## 当前限制

- 当前综合项目仍是固定流程，不是模型自主规划。
- 报告摘要使用规则截断，不是语义总结。
- eval 仍是关键词级规则判断。
- 还没有保存项目报告到文件。

## 下一步建议

下一步应围绕 Week 6 做三件事：

1. 理解 `agent/project.py` 的应用层编排方式。
2. 运行 `python -m cli.project_demo`，逐段对照输出。
3. 为综合项目补充真实用户场景和更严格 eval case。
