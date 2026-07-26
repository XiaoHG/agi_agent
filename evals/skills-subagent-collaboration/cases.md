# Skills 与 Subagent 协作层评估用例

本文件用于记录 Skills/Subagent 最小协作层的可复现评估。

## Case 1：列出 skills

输入：

```bash
python -m cli.collaboration_demo --list-skills
```

期望行为：

- 输出 `Available skills`。
- 至少包含 `research_brief`。
- 至少包含 `code_review`。
- 至少包含 `learning_explanation`。

实际输出摘要：

- 成功输出 3 个内置 skill。
- 每个 skill 都包含 purpose、steps 和 output format。

是否通过：通过。

失败或不足分析：

- 当前 skills 是代码内置 catalog，还没有从独立 skill 文件加载。

## Case 2：选择 code_review skill

输入：

```bash
python -m cli.collaboration_demo --task "Review this code and add tests."
```

期望行为：

- 输出 `Skill: code_review`。
- 输出 code review 的执行步骤。
- 输出包含 `coding_agent` 的 collaboration plan。

实际输出摘要：

- 任务被路由到 `code_review` skill。
- 协作计划包含 Teacher Agent 和 Coding Agent。

是否通过：通过。

失败或不足分析：

- 当前 skill selection 依赖关键词规则，不是模型判断。

## Case 3：列出 subagents

输入：

```bash
python -m cli.collaboration_demo --list-subagents
```

期望行为：

- 输出 `Available subagents`。
- 至少包含 `teacher_agent`。
- 至少包含 `coding_agent`。
- 每个 subagent 应包含职责说明和 handoff rule。

实际输出摘要：

- 成功输出 Teacher Agent 和 Coding Agent。
- 输出包含角色职责和交接规则。

是否通过：通过。

失败或不足分析：

- 当前 subagent 只用于计划，不会真正执行独立任务。

## Case 4：为 code review 生成 subagent 协作计划

输入：

```bash
python -m cli.main --input "Plan subagent collaboration for a code review." --trace
```

期望行为：

- Agent 路由到 `plan_subagents`。
- 输出包含 `Collaboration objective`。
- 输出包含 `teacher_agent` 和 `coding_agent`。
- trace 中应显示 `Run tool: plan_subagents completed`。

实际输出摘要：

- Agent 正确进入 `use_tool / plan_subagents`。
- 输出协作目标、参与角色和工作流步骤。

是否通过：通过。

失败或不足分析：

- 当前只是生成计划，没有真实执行 Teacher/Coding Agent 的分工任务。

## Case 5：纯解释任务只使用 Teacher Agent

输入：

```python
plan = build_collaboration_plan("Explain RAG architecture.")
```

期望行为：

- 输出包含 `teacher_agent`。
- 输出不包含 `coding_agent`。

实际输出摘要：

- 纯解释任务只分配给 Teacher Agent。
- Coding Agent 不参与该计划。

是否通过：通过。

失败或不足分析：

- 当前是否使用 Coding Agent 由关键词规则决定，后续需要更可靠的任务分类。
