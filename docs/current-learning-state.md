# 当前学习进度状态

此文件用于跨会话恢复学习进度。每次学习任务结束后都应更新。

## Last Updated

2026-08-03

## 当前阶段

Week 6：真实 LLM 驱动的专业 Agent 开发。

当前状态：正在进行 v27，目标是把 checkpoint 进一步升级为可浏览的 run history，并支持按 run id 查看历史记录；当前已完成本地 checkpoint persistence，正在补历史列表与单次 run 查看入口。

## 当前教师判断

项目已经从“手写规则 Agent 学习”进入“真实 LLM 驱动的专业 Agent 工程”阶段。

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

当前缺口：

- `WorkspaceAgent` direct answer 还没有默认使用 LLM。
- RAG 检索仍是关键词检索，不是 embedding/vector search。
- MCP tool result 已可通过 tool loop 进入 LLM 综合，但 MCP 协议仍是本地 in-process 学习版。
- Skills 已可通过 runner 调用部分 workspace tools，并已进入 structured trace；LangGraph 已经可以通过独立 skill node 执行 Skills，并能为失败 Skill 和失败普通 tool 生成统一 `RecoveryPlan`；但还没有外部 skill registry、动态配置和真实权限模型。
- LangGraph workflow 已接回 `WorkspaceAgent`，但还没有成为默认主执行器。
- MCP / Skills 还需要继续升级为标准化、可扩展、可观测的专业能力层。
- Runtime events 已经能随 checkpoint 一起落盘，但还没有做基于事件流的完整 replay。
- checkpoint 已可浏览，但还没有做跨 run 的自动 replay。

## 当前总目标

围绕 DeepSeek 真实 LLM 调用链路，逐步接入专业级 RAG、MCP、Skills 和 LangGraph。

后续迭代必须参考：

- `docs/professional-agent-iteration-plan.md`

基本原则：不要长期停留在局部 helper 修补；每个阶段应尽量围绕专业 Agent 能力闭环推进，包括数据模型、执行逻辑、CLI/demo、tests、eval、trace、docs 和 exercises。

当前专业 Agent 迭代链路：

```text
DeepSeek LLM -> LLM-grounded RAG -> LLM tool use -> MCP tools -> Skills -> LangGraph orchestration
```

## 当前具体任务

下一步建议：

1. 学习 v25：`agent/recovery.py` 中的 `RecoveryPlan`、`build_tool_recovery_plan()`、`build_skill_recovery_plan()` 和 `classify_failure()`。
2. 学习 `agent/events.py` 中的 `RuntimeEvent` 和 `build_runtime_events()`。
3. 复盘 `agent/persistence.py` 中的 `RunCheckpointStore`、`build_run_checkpoint()`、`build_graph_checkpoint()`、`load_run()` 和 `list_runs()`。
4. 理解 `agent/core.py` 如何在 `_persist_run()`、`load_latest_checkpoint()`、`load_checkpoint()` 和 `list_checkpoint_history()` 中落盘和浏览运行记录。
5. 理解 `cli/main.py` 的 `--show-last-run`、`--show-run`、`--list-runs` 和 `--history-dir`。
6. 理解 `cli/langgraph_demo.py` 如何把 graph state 保存为 checkpoint。
7. 阅读 `docs/project-overall-retrospective.md`，先重新把整条项目主线串起来。
8. 手动运行 `python -m unittest tests.test_persistence -v`。
9. 手动运行 `python -m unittest discover -s tests -v`。
10. 手动运行 `python -m cli.main --list-runs`。
11. 手动运行 `python -m cli.main --show-run <run_id> --trace`。
12. 手动运行 `python -m cli.langgraph_demo --question "Read README.md."`。

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
- 正在进行 v27：Run History Browsing and Checkpoint Lookup。

## 未完成

- 标准化 MCP server/client。
- 让 LangGraph 成为可配置的默认主执行器。
- MCP / Skills 标准化执行协议。
- Skills 外部 registry 与权限模型。
- Runtime events replay。
- checkpoint run history browser。

## 恢复指令

下一个会话恢复时，请先读取：

1. `AGENTS.md`
2. `docs/current-learning-state.md`
3. `docs/learning-master-plan.md`
4. `evals/README.md`
5. `evals/regression_cases.json`
6. `docs/professional-agent-iteration-plan.md`
7. `evals/runner.py`
8. `tests/test_evals.py`
9. `versions/engineering-evals-observability_v6.md`
10. `agent/project.py`
11. `cli/project_demo.py`
12. `tests/test_project.py`
13. `versions/project-learning-assistant_v7.md`
14. `agent/llm.py`
15. `cli/llm_demo.py`
16. `tests/test_llm.py`
17. `versions/deepseek-llm-provider_v8.md`
18. `rag/llm_qa.py`
19. `cli/rag_llm_demo.py`
20. `tests/test_rag_llm.py`
21. `versions/deepseek-rag_v9.md`
22. `versions/workspace-agent-deepseek-rag_v10.md`
23. `integrations/langchain_tools.py`
24. `cli/langchain_tools_demo.py`
25. `tests/test_langchain_tools.py`
26. `versions/langchain-tool-adapter_v11.md`
27. `integrations/langgraph_workflow.py`
28. `cli/langgraph_demo.py`
29. `tests/test_langgraph_workflow.py`
30. `versions/langgraph-workflow_v12.md`
31. `versions/langgraph-conditional-routing_v13.md`
32. `versions/workspace-agent-langgraph_v14.md`
33. `agent/tool_schema.py`
34. `agent/tool_calling.py`
35. `prompts/tool-calling.v1.md`
36. `cli/tool_calling_demo.py`
37. `tests/test_tool_calling.py`
38. `versions/llm-tool-calling_v15.md`
39. `agent/tool_loop.py`
40. `cli/tool_loop_demo.py`
41. `tests/test_tool_loop.py`
42. `versions/llm-tool-loop_v16.md`
43. `agent/tool_synthesis.py`
44. `prompts/tool-loop-synthesis.v1.md`
45. `tests/test_tool_synthesis.py`
46. `versions/llm-tool-synthesis_v17.md`
47. `versions/mcp-skills-tool-loop_v18.md`
48. `docs/mcp-skills-tool-loop-exercises.md`
49. `skills/execution.py`
50. `versions/skills-execution_v19.md`
51. `docs/skills-execution-exercises.md`
52. `versions/tool-backed-skills_v20.md`
53. `docs/tool-backed-skills-exercises.md`
54. `versions/skill-trace-export_v21.md`
55. `docs/skill-trace-export-exercises_v21.md`
56. `versions/langgraph-skill-node_v22.md`
57. `docs/langgraph-skill-node-exercises_v22.md`
58. `versions/langgraph-skill-failure-recovery_v23.md`
59. `docs/langgraph-skill-failure-recovery-exercises_v23.md`
60. `versions/langgraph-tool-failure-recovery_v24.md`
61. `docs/langgraph-tool-failure-recovery-exercises_v24.md`
62. `agent/recovery.py`
63. `agent/events.py`
64. `tests/test_recovery.py`
65. `tests/test_events.py`
66. `versions/unified-agent-runtime-events-recovery_v25.md`
67. `docs/unified-agent-runtime-events-recovery-exercises_v25.md`
68. `docs/project-overall-retrospective.md`
69. `versions/langgraph-checkpoint-persistence_v26.md`
70. `docs/langgraph-checkpoint-persistence-exercises_v26.md`

然后继续执行当前具体任务。

## 下一步建议

下一阶段规划必须先参考：

- `docs/professional-agent-iteration-plan.md`

建议优先进入：

- v26：LangGraph Checkpoint and Recoverable Run Persistence

下一步优先让 Teacher Agent 讲解这次新增代码：

- `agent/project.py`
- `cli/project_demo.py`
- `tests/test_project.py`
- `examples/project-learning-assistant/README.md`
- `agent/llm.py`
- `cli/llm_demo.py`
- `rag/llm_qa.py`
- `cli/rag_llm_demo.py`
- `agent/tools.py` 中的 `answer_docs_with_llm`
- `agent/router.py` 中的 LLM RAG 路由
- `integrations/langchain_tools.py`
- `cli/langchain_tools_demo.py`
- `integrations/langgraph_workflow.py`
- `cli/langgraph_demo.py`
- `versions/langgraph-conditional-routing_v13.md`
- `versions/workspace-agent-langgraph_v14.md`
- `agent/tool_schema.py`
- `agent/tool_calling.py`
- `prompts/tool-calling.v1.md`
- `cli/tool_calling_demo.py`
- `versions/llm-tool-calling_v15.md`
- `agent/tool_loop.py`
- `cli/tool_loop_demo.py`
- `tests/test_tool_loop.py`
- `versions/llm-tool-loop_v16.md`
- `agent/tool_synthesis.py`
- `prompts/tool-loop-synthesis.v1.md`
- `tests/test_tool_synthesis.py`
- `versions/llm-tool-synthesis_v17.md`
- `agent/tools.py` 中的 `mcp_read_project_file`
- `agent/tool_schema.py` 中的 MCP / Skills tool specs
- `agent/tool_calling.py` 中的 tool input normalization
- `tests/test_mcp.py` 中的 MCP 文件读取 agent 测试
- `tests/test_tool_loop.py` 中的 MCP / Skills tool loop 测试
- `versions/mcp-skills-tool-loop_v18.md`
- `skills/execution.py`
- `agent/tools.py` 中的 `run_skill`
- `agent/tool_schema.py` 中的 `execute_skill`
- `cli/collaboration_demo.py` 中的 `--execute-skill`
- `tests/test_collaboration.py` 中的 skill execution 测试
- `versions/skills-execution_v19.md`
- `skills/execution.py` 中的 tool-backed step runner
- `agent/tools.py` 中的 `_build_skill_tool_runner`
- `cli/collaboration_demo.py` 中的 `--tool-backed`
- `integrations/langgraph_workflow.py` 中的 `call_skill`
- `integrations/langgraph_workflow.py` 中的 `_next_after_skill`
- `agent/core.py` 中的 `_build_langgraph_metadata`
- `tests/test_langgraph_workflow.py` 中的 LangGraph skill node 测试
- `versions/langgraph-skill-node_v22.md`
- `integrations/langgraph_workflow.py` 中的 `recover_skill_failure`
- `integrations/langgraph_workflow.py` 中的 recovery plan helper
- `agent/core.py` 中的 recovery plan metadata 透传
- `tests/test_langgraph_workflow.py` 中的 failure recovery 测试
- `tests/test_agent.py` 中的 recovery plan metadata 测试
- `versions/langgraph-skill-failure-recovery_v23.md`
- `integrations/langgraph_workflow.py` 中的 `recover_tool_failure`
- `integrations/langgraph_workflow.py` 中的 `_next_after_tool`
- `integrations/langgraph_workflow.py` 中的 tool recovery helper
- `tests/test_langgraph_workflow.py` 中的 tool failure recovery 测试
- `tests/test_agent.py` 中的 tool recovery metadata 测试
- `evals/regression_cases.json` 中的 `langgraph-tool-failure-recovery`
- `versions/langgraph-tool-failure-recovery_v24.md`
- `agent/recovery.py`
- `agent/events.py`
- `tests/test_recovery.py`
- `tests/test_events.py`
- `versions/unified-agent-runtime-events-recovery_v25.md`
- `docs/unified-agent-runtime-events-recovery-exercises_v25.md`
- `versions/tool-backed-skills_v20.md`
- `skills/execution.py` 中的 `to_dict()` 方法
- `agent/tools.py` 中的 `ToolResult.metadata`
- `agent/core.py` 中的 `skill_run` trace 字段
- `evals/regression_cases.json` 中的 `skills-execution`
- `versions/skill-trace-export_v21.md`
