# 当前学习进度状态

此文件用于跨会话恢复学习进度。每次学习任务结束后都应更新。

## Last Updated

2026-07-27

## 当前阶段

Week 6：真实 LLM 驱动的专业 Agent 开发。

当前状态：已开始真实 LangGraph workflow，并把 LangChain Tool Adapter 放入 graph node。

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

当前缺口：

- `WorkspaceAgent` direct answer 还没有默认使用 LLM。
- RAG 检索仍是关键词检索，不是 embedding/vector search。
- MCP tool result 还没有进入 LLM 综合。
- Skills 还没有成为 LLM 可选择的专业能力。
- LangGraph workflow 目前还是固定流程，没有条件路由。

## 当前总目标

围绕 DeepSeek 真实 LLM 调用链路，逐步接入专业级 RAG、MCP、Skills 和 LangGraph。

当前专业 Agent 迭代链路：

```text
DeepSeek LLM -> LLM-grounded RAG -> LLM tool use -> MCP tools -> Skills -> LangGraph orchestration
```

## 当前具体任务

下一步建议：

1. 由 Teacher Agent 讲解 `agent/llm.py` 的真实 LLM 接入方式。
2. 手动运行 `python -m cli.llm_demo --input "Explain why agents need tools."`。
3. 手动运行 `python -m cli.main --input "Answer with local docs and DeepSeek RAG: What does MCP mean in this project?" --trace`。
4. 手动运行 `python -m cli.langchain_tools_demo`。
5. 手动运行 `python -m cli.langgraph_demo --question "What does MCP mean in this project?"`。

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
- 开始实现 Week 6 Project Learning Assistant。
- 开始实现 DeepSeek V4 Pro 真实 LLM 接入。

## 未完成

- RAG + LLM 真实回答链路。
- LLM tool calling / tool schema。
- LangGraph conditional routing。
- 标准化 MCP server/client。
- 专业 Skills 执行系统。
- LangChain tool adapter。
- LangGraph workflow。

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
9. `agent/project.py`
10. `cli/project_demo.py`
11. `tests/test_project.py`
12. `versions/project-learning-assistant_v7.md`
13. `agent/llm.py`
14. `cli/llm_demo.py`
15. `tests/test_llm.py`
16. `versions/deepseek-llm-provider_v8.md`
17. `rag/llm_qa.py`
18. `cli/rag_llm_demo.py`
19. `tests/test_rag_llm.py`
20. `versions/deepseek-rag_v9.md`
21. `versions/workspace-agent-deepseek-rag_v10.md`
22. `integrations/langchain_tools.py`
23. `cli/langchain_tools_demo.py`
24. `tests/test_langchain_tools.py`
25. `versions/langchain-tool-adapter_v11.md`
26. `integrations/langgraph_workflow.py`
27. `cli/langgraph_demo.py`
28. `tests/test_langgraph_workflow.py`
29. `versions/langgraph-workflow_v12.md`

然后继续执行当前具体任务。

## 下一步建议

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
