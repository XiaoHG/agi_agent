# 专业 Agent 项目后续迭代计划

日期：2026-08-03

用途：此文档记录后续项目迭代的基本分析思路。之后每次进入新阶段前，都应优先参考本文件，避免继续只做局部小修补，而是围绕专业 Agent 能力闭环推进。

## 当前判断

最近几个阶段主要在补齐局部工程能力：

- `SkillRun` trace
- LangGraph skill node
- Skill failure recovery
- Tool failure recovery

这些迭代对基础质量有价值，但如果长期保持这种粒度，项目容易停留在“学习型 demo”，而不是逐步成长为“专业 Agent 工程项目”。

后续迭代应该从“修一个点”升级为“完成一个专业 Agent 能力模块”。

## 当前项目已具备的能力

项目目前已经具备：

- DeepSeek LLM client
- 本地 RAG
- DeepSeek-grounded RAG
- LangChain `StructuredTool` adapter
- LangGraph workflow
- LLM tool calling
- bounded tool loop
- MCP 本地工具雏形
- Skills 执行系统
- tool-backed Skills
- Subagent 规划
- structured trace
- regression eval
- failure recovery
- `.codex` project config
- 项目内 professional code review skill

这些能力已经不是零散代码，下一步应进入系统化整合。

## 专业 Agent 项目关键缺口

### 1. 统一运行协议

当前 `AgentRun`、`ToolResult`、`SkillRun`、LangGraph state、`recovery_plan` 都有自己的结构，但还没有统一的运行事件模型。

专业 Agent 项目通常需要统一表达：

- Run
- Step
- Event
- ToolCall
- ToolResult
- SkillRun
- Error
- RecoveryPlan
- Trace export

这会支撑后续 observability、checkpoint、debug UI、eval analysis 和多 Agent 协作。

### 2. LLM-first 路由与计划

当前很多路由仍是规则判断。

后续应该逐步演进为：

```text
User input
  -> LLM intent planner
  -> structured plan
  -> LangGraph execution
  -> tool / RAG / MCP / Skill
  -> synthesis
```

规则 router 可以继续作为 fallback，但不应该长期作为主要智能决策层。

### 3. 专业 RAG

当前 RAG 仍以关键词检索为主。

专业 RAG 至少需要：

- document loader
- chunk metadata
- embedding
- vector store
- rerank 或 scoring
- source citation
- grounded answer
- no-context handling
- RAG eval set
- index rebuild CLI

### 4. 标准 MCP

当前 MCP 仍是本地 in-process 学习版。

专业 MCP 应该具备：

- server schema
- tool registry
- tool input/output validation
- permission policy
- external tool boundary
- error model
- trace integration

### 5. Skills 系统升级

当前 Skills 是固定 catalog + 固定 step。

后续应支持：

- `.codex/skills` discovery
- `SKILL.md` frontmatter parsing
- project skill registry
- built-in skills 与 project skills 合并
- skill execution plan
- skill tool permissions
- skill trace
- skill eval
- skill versioning

项目内 `professional-code-review` skill 应作为此方向的入口。

## 后续每个阶段的能力闭环要求

未来每个阶段不应只做一个 helper，而应尽量形成完整能力闭环：

```text
数据模型
-> 执行逻辑
-> CLI/demo
-> tests
-> eval
-> trace
-> docs
-> exercises
```

如果某阶段只做很小的内部改动，需要明确说明为什么这一步必须单独做，以及它服务于哪个更大的专业能力。

## 未来 6 个推荐阶段

### v25：Unified Agent Runtime Events and Recovery Model

目标：

- 新增统一 runtime event 模型。
- 新增标准 `RecoveryPlan` 数据模型。
- 将 tool recovery plan 和 skill recovery plan 统一。
- 让 Agent、Tool、Skill、Graph 的关键执行过程进入事件流。
- 为 checkpoint、observability、debug UI 和多 Agent 协作打基础。

建议新增：

- `agent/events.py`
- `agent/recovery.py`
- `tests/test_events.py`
- `tests/test_recovery.py`
- `versions/unified-agent-runtime-events-recovery_v25.md`
- `docs/unified-agent-runtime-events-recovery-exercises_v25.md`

### v26：LLM Planner 接入 LangGraph

目标：

- 用 DeepSeek 生成结构化 plan。
- plan 包含 intent、steps、tools、risk、expected outputs。
- LangGraph 根据 plan 路由执行。
- 保留 deterministic fallback。
- 增加 planner prompt、parser、tests、eval。

重点：

- LLM 负责规划。
- 代码负责校验、执行和兜底。

### v27：专业 RAG v1

目标：

- 加 embedding。
- 加 vector index。
- 加 chunk metadata。
- 加 source citation。
- 加 grounded answer eval。
- 增加 index rebuild CLI。

重点：

- 从关键词检索升级到可扩展 RAG。
- 回答必须保留 source evidence。

### v28：项目内 Skill Registry

目标：

- 读取 `.codex/skills`。
- 解析 `SKILL.md` frontmatter。
- 合并 built-in skills 和 project skills。
- 让 `professional-code-review` 能进入项目 Agent 的 skill catalog。
- 为 project-specific skills 增加测试和 CLI。

重点：

- Skills 不再只写死在 Python catalog 中。
- 项目 skill 成为 Agent 可发现能力。

### v29：MCP 工具注册与权限策略

目标：

- 标准化 MCP tool schema。
- 加 read-only / write / network / destructive 权限分类。
- 增加 permission policy。
- trace 中记录权限判断。
- 为不安全工具调用提供 recovery / refusal path。

重点：

- 专业 Agent 必须有权限边界。
- 工具能力不能只靠名字和自然语言描述。

### v30：默认 LangGraph 主执行器

目标：

- 让 LangGraph 成为主 Agent orchestration runtime。
- direct answer、RAG、tool、Skill、MCP 都进入 graph。
- 原有 if/else 主控逐步变成 fallback 或 thin wrapper。
- trace 同时保留 runtime events 和 graph state。

重点：

- 从“Agent 调 LangGraph”升级为“Agent 运行在 LangGraph 上”。

## 每次迭代前的评估模板

进入任何新阶段前，先回答：

1. 这个阶段解决的是专业 Agent 的哪个能力缺口？
2. 它是否只是局部 helper，还是形成完整能力闭环？
3. 是否接入真实 LLM / RAG / MCP / Skills / LangGraph 之一？
4. 是否有清晰数据模型？
5. 是否有测试验证代码行为？
6. 是否有 eval 验证 Agent 行为？
7. 是否进入 trace，方便调试和恢复？
8. 是否有 CLI/demo，方便手动学习？
9. 是否有版本文档和练习？
10. 是否为下一阶段留下明确扩展点？

## 后续执行原则

- 优先做“能力模块”，少做孤立 helper。
- 每个阶段都要能解释它在专业 Agent 架构中的位置。
- 新功能必须考虑 trace、tests、eval 和 recovery。
- 真实 LLM、RAG、MCP、Skills、LangGraph 应逐步融合，而不是各自孤立。
- 保持学习友好：新增代码要有清晰注释，版本文档和练习文件必须保留。
- 新阶段代码默认不提交，等学习完成后再按用户要求提交。
