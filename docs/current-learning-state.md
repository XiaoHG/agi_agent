# 当前学习进度状态

此文件用于跨会话恢复学习进度。每次学习任务结束后都应更新。

当前详细工作快照：

- `docs/snapshots/work-snapshot-2026-08-05.md`

## Last Updated

2026-08-14

## 当前阶段

专业级工业 Agent 主干阶段：v50 收口完成，进入下一轮规划前复盘。

当前状态：v36 runtime event replay 已提交；v37 run replay diff and comparative analysis 已提交；v38 checkpoint-guided recovery and resume 已提交；v39 LLM-first direct answer and intent entry 已提交；v40 standardized MCP execution boundary 已提交；v41 skill permissions, versioning and runtime policy 已提交；v42 multi-agent task delegation and subagent contract 已提交；v43 long-horizon memory and session continuity 已提交；v44 industrial evaluation matrix and failure bench 已提交并推送；v45 release gate and CI readiness 已提交并推送；v46 checkpoint branch resume 已提交并推送；v47 standardized MCP governance 已提交并推送；v48 skills governance and versioning 已提交并推送；v49 production RAG backend hardening 已提交并推送；v50 multi-agent delegation hardening 已提交并推送。

v29 功能基线提交：

- `597ea59 Add professional RAG vector index`

下一阶段建议：基于 `v50` 的委派协议收口结果，进入下一轮专业级规划阶段，优先扩展真实多 Agent runtime、长期任务连续性、审批治理和交付体系。

## 当前教师判断

项目已经从“最小 Agent 学习样例”进入“专业级工业 Agent 工程主干阶段”。

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
- Project Learning Assistant 最小编排层
- 综合项目 CLI demo
- DeepSeek V4 Pro 真实 LLM client
- 真实 LLM CLI demo
- DeepSeek-grounded RAG answer chain
- RAG + LLM CLI demo
- `WorkspaceAgent` DeepSeek RAG tool
- LLM-grounded RAG regression case
- LangChain `StructuredTool` adapter
- `integrations/` 框架适配层
- LangGraph `StateGraph` workflow
- LangGraph RAG demo CLI
- LangGraph conditional routing
- LangGraph multi-tool dispatch
- LangGraph 已接回 `WorkspaceAgent`
- LLM tool calling prompt
- workspace tool schema catalog
- LLM-assisted tool selection
- tool_call trace and selected-tool eval support
- bounded LLM tool loop
- tool loop observation feedback
- repeated tool call guard
- tool loop trace and structured trace support
- LLM final synthesis for tool-loop observations
- deterministic fallback for final synthesis failure
- MCP project file reading exposed through the workspace tool catalog
- MCP / Skills tool-loop regression coverage
- deterministic Skills execution records
- `execute_skill` Agent tool
- Skills execution CLI entrypoint
- tool-backed skill steps
- skill tool runner request/response boundary
- skill step failure handling
- SkillRun JSON-ready trace export
- `WorkspaceAgent.to_trace_dict()` skill run summary
- `execute_skill` regression eval case
- LangGraph `skill_execution` route
- LangGraph `call_skill` node
- LangGraph skill status conditional edge
- LangGraph skill run metadata exported through `WorkspaceAgent.to_trace_dict()`
- `langgraph-skill-execution` regression eval case
- LangGraph `recover_skill_failure` node
- LangGraph `recovery_plan` state
- Skill failure recovery plan exported through `WorkspaceAgent` metadata
- LangGraph `tool_status` / `tool_error` state
- LangGraph `recover_tool_failure` node
- Tool failure classification
- Tool recovery plan exported through `WorkspaceAgent` metadata
- `langgraph-tool-failure-recovery` regression eval case
- Unified `RecoveryPlan` model
- Tool / Skill / exception recovery plan builders
- Unified failure classification entrypoint
- Unified `RuntimeEvent` model
- Runtime events exported through `WorkspaceAgent.format_trace()`
- Runtime events exported through `WorkspaceAgent.to_trace_dict()`
- DeepSeek LangGraph planner
- LangGraph planner deterministic fallback
- RAG vector index rebuild CLI
- Professional RAG vector search tool
- 项目内 Skill Registry
- `.codex/skills/*/SKILL.md` discovery
- project skill frontmatter / step parsing
- built-in skills 与 project skills merged catalog
- `professional-code-review` Agent 可发现能力
- project skill structured trace metadata
- skill version metadata
- skill runtime policy
- skill policy decision trace
- MCP tool permission classification
- default read-only MCP policy
- MCP permission decision trace metadata
- MCP write-tool refusal path
- MCP write-tool explicit allow path
- LangGraph default main runtime
- top-level route hint -> graph state translation
- classic runtime explicit opt-out
- graph metadata preserved under classic Agent surface
- workflow graph plan/build/step/finalize nodes
- workflow route hint -> graph workflow execution
- workflow classic fallback preserved for comparison
- tool_call graph selection node
- tool_call action/status structured graph state
- tool_call classic fallback preserved for comparison
- tool_loop graph iteration node
- tool_loop observations / seen-calls / stop-reason graph state
- tool_loop graph final synthesis
- tool_loop classic fallback preserved for comparison
- replay summary / comparative diff report
- compare latest two runs / compare selected runs CLI
- LLM-first direct answer
- direct answer deterministic fallback
- direct answer structured trace metadata
- MCP execution record
- MCP structured error model
- MCP execution CLI inspection
- release gate / CI readiness 门禁模型
- checkpoint branch resume lineage

当前缺口：

- RAG 已开始接入本地 vector index，但还不是外部 embedding provider / production vector store。
- MCP tool result 已可通过 tool loop 进入 LLM 综合，并已具备最小权限分类和拒绝路径；但 MCP 协议仍是本地 in-process 学习版。
- Skills 已可通过 runner 调用部分 workspace tools，并已进入 structured trace；LangGraph 已经可以通过独立 skill node 执行 Skills，并能为失败 Skill 和失败普通 tool 生成统一 `RecoveryPlan`；项目内 Skill Registry 已经打通，并已具备 skill version 与 runtime policy，但还没有外部 registry 和集中治理服务。
- LangGraph workflow 已成为默认主执行器，workflow / tool_call / tool_loop 已并入统一 graph runtime。
- MCP / Skills 还需要继续升级为标准化、可扩展、可观测的专业能力层。
- Runtime events 已经能随 checkpoint 一起落盘，并已支持 report-level replay、跨 run diff 与 checkpoint-guided resume，但还没有做真正的恢复分叉和 continue execution。
- checkpoint 已可浏览、可回放、可比较，并已支持基于 checkpoint route hints 的 branch resume。
- 发布门禁已开始搭建，但还没有接入远程 CI 平台。
- LangGraph route 已有 DeepSeek planner 和 deterministic fallback，并已经成为默认主执行器。
- Subagent 已具备 delegation / handoff / execution / return / recovery 的正式协议，但目前仍是 deterministic execution，不是真实异步多 Agent runtime。

## 当前总目标

围绕真实 LLM 调用链路，持续推进专业级工业 Agent 的运行时、能力层、恢复层和交付层。

后续迭代必须参考：

- `docs/plans/v3_professional-agent-iteration-plan.md`

基本原则：不要长期停留在局部 helper 修补；每个阶段应尽量围绕专业 Agent 能力闭环推进，包括数据模型、执行逻辑、CLI/demo、tests、eval、trace、docs 和 exercises。

当前专业 Agent 迭代链路：

```text
LLM / Planner -> LangGraph Runtime -> RAG / MCP / Skills / Subagent -> Trace / Replay / Recovery -> Release Gate / Evals
```

## 当前具体任务

下一步建议：

1. 复盘当前整体状态：`docs/reviews/project-overall-retrospective.md`。
2. 复盘 `v50`：`versions/v50_multi-agent-delegation-hardening.md`。
3. 查看对应练习：`docs/v50_multi-agent-delegation-hardening-exercises.md`。
4. 进入下一阶段规划，围绕真实多 Agent runtime、长期任务和治理体系继续拆分版本。

## 当前学习重点

学习者需要重点理解：

- 测试验证代码行为，eval 验证 Agent 行为。
- trace 是定位 Agent 失败的核心证据。
- eval case 要可重复、可比较、可扩展。
- 工程化不是堆功能，而是让系统可调试、可回归、可维护。
- 综合项目层应该组合能力，而不是污染基础 Agent loop。
- 一个可交付 Agent 原型必须有运行入口、测试、示例、文档和验证命令。
- 真实 LLM client 应该独立封装，业务代码不能到处直接写 HTTP/API 调用。
- API Key 必须只从环境变量读取，不能写入仓库。
- 专业 Agent 框架接入应围绕统一 LLM client、tool schema 和 workflow state 展开。
- 主 Agent 接入 LangGraph 后，trace 需要同时保留 Agent route 和 graph route，方便定位失败发生在哪一层。
- LLM tool calling 必须拆成两层：模型负责选择工具和参数，代码负责校验、兜底和执行。
- 多步 tool loop 必须有最大步数和重复调用保护，避免模型陷入无限工具调用。
- final synthesis 应该只基于 tool observations 生成答案，不能编造工具没有返回的信息。
- 专业 tool layer 不能只把工具名字暴露给 LLM，还要明确参数边界、无参数工具行为、失败兜底和 trace 证据。
- Skills execution 必须有 run、step、status、observation 和 final output，不能只返回一段不可追踪文本。
- Skill runner 应该通过清晰 request/response 边界调用工具，不能让 Skills 包直接依赖 Agent 主循环。
- Agent 可观测性不能只靠文本 trace；关键 run object 应该能导出结构化 dict，服务测试、eval、恢复和后续 LangGraph state。
- LangGraph node 应该有清晰职责边界；当某类能力需要结构化 state 和独立分支时，应该优先建独立 node，而不是挤进通用 tool node。
- 条件边可以基于运行结果，而不只是基于用户意图；`skill_status` 是后续 failure recovery 的分支依据。
- 失败路径也应该是 graph 的一等路径；失败不应该只变成错误字符串，而应该变成可观察、可测试、可恢复的结构化状态。
- recovery node 的核心职责是把失败事实转换成下一步行动计划，而不是隐藏失败或自动冒险重试。
- 普通 tool failure 和 Skill failure 都需要结构化恢复，但二者的上下文不同：tool failure 主要看 tool name / input / error，Skill failure 还要看 SkillRun step trace。
- `failure_type` 是后续专业恢复策略的入口，它可以帮助 graph 决定是提示用户修正路径、检查权限、补 API key，还是进入人工审批。
- 恢复计划应该作为独立数据模型维护，而不是散落在 graph node 内部。
- Runtime events 是后续 checkpoint、replay、审计和长期任务监控的基础。
- Graph state 中应优先保存 JSON-ready 数据，避免未来持久化和跨进程传输时出现不可序列化对象。
- LLM Planner 的职责是产生结构化 plan；代码的职责是校验 plan、执行 plan，并在 LLM 不可用或输出不合格时 fallback。
- 专业 RAG 不只是“能搜到文本”，还需要 index rebuild、chunk metadata、source citation、可测试检索行为和可替换的 embedding 层。
- 发布门禁必须同时覆盖 tests、eval、matrix 和 failure bench，才能接近可交付标准。
- 恢复后的运行必须成为正式的 branch run，而不是没有来源关系的匿名重跑。
- 多 Agent 的真正难点不在“多几个角色名”，而在执行协议、失败回退、上下文隔离和长期协作状态。

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
- 提交工程化评估阶段代码：`2cc93c1 Add engineering evals and observability stage`。
- 完成 Week 6 Project Learning Assistant 最小版本。
- 完成 DeepSeek V4 Pro 真实 LLM 接入。
- 完成 DeepSeek-grounded RAG 真实回答链路。
- 完成 v14：LangGraph 接回 `WorkspaceAgent`，并补充 graph regression cases。
- 完成 v15：LLM tool calling / tool schema 接回 `WorkspaceAgent`。
- 完成 v16：bounded multi-step LLM tool loop 接回 `WorkspaceAgent`。
- 完成 v17：LLM final synthesis 接入 tool loop。
- 完成 v18：MCP / Skills 作为 tool loop 一等能力。
- 完成 v19：标准化 Skills execution run。
- 完成 v20：tool-backed skill runner。
- 完成 v21：SkillRun trace / JSON export。
- 完成 v22：LangGraph skill node。
- 完成 v23：LangGraph skill failure recovery。
- 完成 v24：LangGraph tool failure recovery。
- 完成 v25：Unified Agent Runtime Events and Recovery Model。
- 完成 v26 核心实现：LangGraph Checkpoint and Recoverable Run Persistence。
- 完成 v27：Run History Browsing and Checkpoint Lookup。
- 完成 v28：LLM Planner for LangGraph。
- 完成 v29：Professional RAG v1。
- 完成 v30：Project Skill Registry。
- 完成 v31：MCP 工具注册与权限策略。
- 完成 v32：默认 LangGraph 主执行器。
- 完成 v33：workflow 并入默认 LangGraph orchestration。
- 完成 v34：tool_call 并入默认 LangGraph orchestration。
- 完成 v35：tool_loop 并入默认 LangGraph orchestration。
- 开始 v36：Runtime Event Replay。
- 完成 v36：Runtime Event Replay。
- 完成 v37：Run Replay Diff and Comparative Analysis。
- 完成 v38：Checkpoint-Guided Recovery and Resume。
- 完成 v39：LLM-First Direct Answer and Intent Entry。
- 完成 v40：Standardized MCP Execution Boundary。
- 完成 v41：Skill Permissions, Versioning and Runtime Policy。
- 完成 v42：Multi-Agent Task Delegation and Subagent Contract。
- 完成 v43：Long-Horizon Memory and Session Continuity。
- 完成 v44：Industrial Evaluation Matrix and Failure Bench。
- 完成 v45：Release Gate and CI Readiness。
- 完成 v46：Checkpoint Branch Resume。
- 完成 v47：Standardized MCP Governance。
- 完成 v48：Skills Governance and Versioning。
- 完成 v49：Production RAG Backend Hardening。
- 完成 v50：Multi-Agent Delegation Hardening。

## 未完成

- 标准化 MCP server/client。
- 基于统一 LangGraph 主执行器，继续增强恢复分叉和可观测性。
- MCP / Skills 标准化执行协议。
- 真实异步多 Agent runtime。
- 长期任务生命周期与人工审批治理。
- Skills 外部 registry 与权限模型。
- Runtime events replay 已进入 report-level、comparative diff 与 checkpoint-guided resume 版本。
- checkpoint 已支持 guided resume，但还没有真正的分叉恢复与状态级 continue execution。

## 恢复指令

新会话中输入：

```text
恢复项目
```

恢复含义：恢复到 `main` 分支最新状态；`597ea59 Add professional RAG vector index` 是 v29 功能基线提交。

下一个会话恢复时，请先读取：

1. `AGENTS.md`
2. `docs/current-learning-state.md`
3. `docs/snapshots/work-snapshot-2026-08-05.md`
4. `docs/plans/v3_professional-agent-iteration-plan.md`
5. `versions/v32_default-langgraph-main-runtime.md`
6. `docs/v32_default-langgraph-main-runtime-exercises.md`
7. `versions/v33_graph-workflow-orchestration.md`
8. `docs/v33_graph-workflow-orchestration-exercises.md`
9. `versions/v34_graph-tool-call-orchestration.md`
10. `docs/v34_graph-tool-call-orchestration-exercises.md`
11. `versions/v35_graph-tool-loop-orchestration.md`
12. `docs/v35_graph-tool-loop-orchestration-exercises.md`
13. `versions/v38_checkpoint-guided-recovery-and-resume.md`
14. `docs/v38_checkpoint-guided-recovery-and-resume-exercises.md`
15. `versions/v39_llm-first-direct-answer-and-intent-entry.md`
16. `docs/v39_llm-first-direct-answer-and-intent-entry-exercises.md`
17. `versions/v40_standardized-mcp-execution-boundary.md`
18. `docs/v40_standardized-mcp-execution-boundary-exercises.md`
19. `versions/v41_skill-permissions-versioning-and-runtime-policy.md`
20. `docs/v41_skill-permissions-versioning-and-runtime-policy-exercises.md`
21. `agent/core.py`
22. `agent/tools.py`
23. `integrations/langgraph_workflow.py`
24. `skills/policy.py`
25. `skills/catalog.py`
26. `skills/execution.py`
27. `cli/collaboration_demo.py`
28. `cli/main.py`
29. `tests/test_collaboration.py`
30. `cli/README.md`
然后继续执行当前具体任务。

## 下一步建议

下一阶段规划必须先参考：

- `docs/plans/v3_professional-agent-iteration-plan.md`

建议优先进入：

- Skills runtime policy 已进入可运行状态；下一步应更多转向 subagent contract、任务委派和多 Agent trace，而不是继续停留在单 Agent 内部能力拼接。
