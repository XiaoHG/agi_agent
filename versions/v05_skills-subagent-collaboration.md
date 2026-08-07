# Skills 与 Subagent 协作层 v5

版本：v5

日期：2026-07-25

## 本次目标

在 RAG 与 MCP 最小闭环之后，进入 Week 4：Skills 与 Subagent。

本次目标不是实现真实多 Agent 对话，而是先建立最小工程边界：

```text
User task -> Skill selection -> Subagent plan -> Agent tool output -> CLI output
```

## 新增文件

### `skills/__init__.py`

职责：

- 导出 skill catalog 的主要接口
- 让 `skills` 成为可导入包

### `skills/catalog.py`

行号范围：`1-97`

职责：

- 定义 `SkillSpec`
- 提供内置 skills
- 渲染 skills 列表
- 根据用户输入选择一个 skill

当前内置 skills：

- `research_brief`
- `code_review`
- `learning_explanation`

### `subagent/__init__.py`

职责：

- 导出 subagent collaboration 的主要接口
- 让 `subagent` 成为可导入包

### `subagent/team.py`

行号范围：`1-84`

职责：

- 定义 `SubagentSpec`
- 定义 `CollaborationPlan`
- 提供默认 subagents
- 生成确定性的协作计划

当前默认 subagents：

- `teacher_agent`
- `coding_agent`

### `cli/collaboration_demo.py`

行号范围：`1-48`

职责：

- 列出 skills
- 列出 subagents
- 对一个 task 同时输出 skill 选择和 subagent collaboration plan

### `tests/test_collaboration.py`

行号范围：`1-81`

职责：

- 测试 skill 描述
- 测试 skill 选择
- 测试 subagent 描述
- 测试 collaboration plan
- 测试 Agent 路由
- 测试 CLI demo

## 修改文件

### `agent/tools.py`

变更行号范围：`8-135`

本次改动：

- 接入 `skills`
- 接入 `subagent`
- 新增 `list_agent_skills`
- 新增 `plan_skill`
- 新增 `list_project_subagents`
- 新增 `plan_subagent_collaboration`

### `agent/router.py`

变更行号范围：`126-196`

本次改动：

- 新增 `_looks_like_skill_request`
- 新增 `_looks_like_subagent_request`
- 将 skill 请求路由到 `list_skills` 或 `plan_skill`
- 将 subagent 请求路由到 `list_subagents` 或 `plan_subagents`

### `agent/core.py`

变更行号范围：`10-164`

本次改动：

- 导入 Skills/Subagent 工具函数
- 在 `_call_tool()` 中接入 Skills/Subagent 工具分支

### `agent/__init__.py`

变更行号范围：`6-40`

本次改动：

- 导出 Skills/Subagent 相关工具函数

### `pyproject.toml`

本次改动：

- 将 `skills` 和 `subagent` 加入包列表

### `README.md`

本次改动：

- 新增 collaboration demo 命令
- 更新当前阶段说明

### `docs/current-learning-state.md`

本次改动：

- 将当前阶段更新为 Week 4
- 更新恢复指令
- 更新当前缺口和下一步建议

### `skills/README.md`

本次改动：

- 记录当前内置 skill catalog 实现
- 新增运行命令

### `subagent/README.md`

本次改动：

- 记录当前 collaboration planner 实现
- 新增运行命令

## 新增交互流程

### 独立 collaboration demo

```text
CLI task
  -> select_skill()
  -> build_collaboration_plan()
  -> render skill and collaboration plan
```

### Agent 调用 Skills/Subagent

```text
User input
  -> route_intent()
  -> list_skills / plan_skill / list_subagents / plan_subagents
  -> WorkspaceAgent._call_tool()
  -> final answer
```

## 验证命令

```bash
python -m unittest discover -s tests -v
python -m cli.collaboration_demo --list-skills
python -m cli.collaboration_demo --list-subagents
python -m cli.collaboration_demo --task "Review this code and add tests."
python -m cli.main --input "List available skills." --trace
python -m cli.main --input "Plan subagent collaboration for a code review." --trace
```

验证结果：

- 40 个测试全部通过。
- CLI demo 可以列出 skills。
- CLI demo 可以列出 subagents。
- CLI demo 可以为任务选择 skill 并生成 subagent 协作计划。
- Agent 可以通过统一入口调用 Skills/Subagent 能力。

## 当前限制

- Skills 仍是代码内置 catalog，还没有从独立 markdown skill 文件加载。
- Subagent 仍是规划层，没有真实消息传递和多 Agent 执行。
- 当前路由是规则判断，不是模型决策。
- 还没有 Skills/Subagent eval case。

## 下一步建议

先完成 Skills/Subagent 练习和 eval，再判断是否进入 Week 5：工程化、评估与稳定性。
