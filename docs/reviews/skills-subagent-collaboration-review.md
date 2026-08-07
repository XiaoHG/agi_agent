# Skills 与 Subagent 协作层阶段复盘

## Skill 和普通 prompt 有什么区别？

- 普通 prompt 通常是一次性的文本指令，用来影响某次模型回答。
- Skill 是可复用的任务能力定义，应该包含适用场景、输入要求、执行步骤、可用工具和输出格式。
- Skill 可以包含 prompt，但不等于 prompt；它更接近“可复用工作方法”。
- 当前项目里的 `SkillSpec` 用 `name`、`purpose`、`steps`、`output_format` 固定描述一个任务能力。

## Skill 和 tool 有什么区别？

- tool 是具体能力调用，通常完成一个明确动作，例如读取文件、检索文档、调用 MCP 工具。
- Skill 是任务流程，描述为了完成某类任务应该按什么步骤组织工具、判断和输出。
- 一个 skill 可以使用多个 tool，也可以完全不直接调用 tool，只定义任务方法。
- 当前项目里的 skill 还只是规划层，没有真正执行内部步骤。

## Subagent 和普通函数拆分有什么区别？

- 普通函数拆分主要解决代码复用和模块边界问题。
- Subagent 解决的是职责边界和协作流程问题，例如 Teacher Agent 负责解释，Coding Agent 负责实现和验证。
- Subagent 应该有角色目标、上下文输入、输出责任和交接规则。
- 当前项目里的 subagent 还没有真实消息传递，只生成 collaboration plan。

## 为什么当前实现还不是真正多 Agent？

- 当前没有启动多个独立 Agent 实例。
- 当前没有多 Agent 消息传递、上下文隔离、任务交接或结果合并。
- 当前 `build_collaboration_plan()` 只是确定性生成协作计划，不会真的让 Teacher Agent 和 Coding Agent 分别执行任务。
- 因此它是 Subagent 的规划骨架，不是完整多 Agent runtime。

## 当前实现最容易误解的地方是什么？

- 容易误解为“有了 `teacher_agent` 和 `coding_agent` 名字，就已经是多 Agent”。
- 实际上当前只是把角色职责结构化，还没有真实执行。
- 也容易把 Skill 误解成普通 prompt；当前 Skill 的关键是可复用流程，而不是单段提示词。
- 还容易把 Skill 和 tool 混淆：tool 是动作，skill 是组织动作的方法。

## 下一阶段是否可以进入工程化与评估？理由是什么？

可以进入 Week 5：工程化、评估与稳定性。

理由：

- Week 4 的最小闭环已经打通：可以列出 skills、选择 skill、列出 subagents、生成 subagent 协作计划。
- 当前测试覆盖了 skill 选择、subagent plan、Agent 路由和 CLI demo。
- 继续扩展真实多 Agent runtime 会显著扩大范围，适合在工程化基础更稳之后再做。
- Week 5 正好可以补日志、结构化 trace、eval runner、错误分类和稳定性能力，为后续真实多 Agent 执行打基础。

进入下一阶段前的保留结论：

```text
当前 Skills/Subagent 是最小规划层，不是完整生产级 Skills runtime 或多 Agent runtime。
```
