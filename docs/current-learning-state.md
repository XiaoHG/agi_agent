# 当前学习进度状态

此文件用于跨会话恢复学习进度。每次学习任务结束后都应更新。

## Last Updated

2026-07-25

## 当前阶段

Week 4：Skills 与 Subagent。

当前状态：Skills/Subagent 最小协作层已开始实现。

## 当前教师判断

项目已经从“RAG 与 MCP 工具接入”进入“能力复用与角色协作”阶段。

已具备：

- Week 1 最小 CLI Agent
- Week 2 状态与工作流
- Week 3 本地 RAG 最小闭环
- Week 3 本地 MCP 最小骨架
- 本地工具：`read_file`、`list_dir`、`count_lines`、`search_docs`
- MCP 工具：`workspace_summary`、`read_project_file`
- Skills catalog：`research_brief`、`code_review`、`learning_explanation`
- Subagent planning：`teacher_agent`、`coding_agent`
- Agent 可列出 skills、选择 skill、列出 subagents、生成 subagent 协作计划
- 自动化测试

当前缺口：

- Skills 还只是内置 catalog，没有从独立 skill 文件加载。
- Subagent 还只是规划层，没有真实多 Agent 消息执行。
- 还没有 Skills/Subagent eval case。
- 还没有阶段复盘。

## 当前总目标

先巩固 Skills 与 Subagent 的最小边界：理解“可复用任务能力”和“角色协作计划”的区别。

最小协作链路：

```text
User task -> Skill selection -> Subagent plan -> Agent tool output -> CLI output
```

## 当前具体任务

下一步建议：

1. 由 Teacher Agent 讲解 Skills/Subagent 最小骨架。
2. 手动运行 collaboration demo，观察 skill 选择和 subagent 协作计划。
3. 补 Skills/Subagent eval case。
4. 写阶段复盘，再评估是否进入 Week 5。

## 当前学习重点

学习者需要重点理解：

- Skill 是可复用任务能力，不只是 prompt。
- Subagent 是职责边界，不只是换一个名字继续调用同一个逻辑。
- 当前实现只做选择和规划，没有真实多 Agent 对话执行。
- 进入工程化阶段前，需要先把能力边界讲清楚。

## 已完成

- 初始化项目目录。
- 创建 README 学习路线。
- 创建 Teacher Agent / Coding Agent 定义。
- 创建仓库级 `AGENTS.md` 协作规则。
- 完成 Week 1 最小 CLI Agent。
- 完成 Week 2 状态与工作流实现。
- 完成 Week 3 本地 RAG 最小闭环。
- 完成 Week 3 本地 MCP 最小骨架。
- 提交 RAG 阶段代码：`03c0005 Add local RAG search stage`。
- 提交 MCP 阶段代码：`04746a4 Add local MCP protocol stage`。
- 开始实现 Week 4 Skills/Subagent 最小协作层。

## 未完成

- Skills/Subagent 评估用例。
- Skills/Subagent 阶段复盘。
- 从 markdown skill 文件加载 skill。
- 真实多 Agent 消息执行。

## 恢复指令

下一个会话恢复时，请先读取：

1. `AGENTS.md`
2. `docs/current-learning-state.md`
3. `docs/learning-master-plan.md`
4. `skills/README.md`
5. `subagent/README.md`
6. `tests/test_collaboration.py`
7. `versions/skills-subagent-collaboration_v5.md`

然后继续执行当前具体任务。

## 下一步建议

下一步优先让 Teacher Agent 讲解这次新增代码：

- `skills/catalog.py`
- `subagent/team.py`
- `cli/collaboration_demo.py`
- `agent/tools.py`
- `agent/router.py`
