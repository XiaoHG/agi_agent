# 当前学习进度状态

此文件用于跨会话恢复学习进度。每次学习任务结束后都应更新。

## Last Updated

2026-07-24

## 当前阶段

Week 3：RAG 与 MCP。

当前状态：RAG 最小闭环已开始实现。

## 当前教师判断

项目已经从“状态与工作流实验”进入“本地知识检索实验”阶段。

已具备：

- 核心能力目录：`agent/ mcp/ rag/ skills/ subagent/`
- 工程支撑目录：`prompts/ evals/ tests/ examples/ docs/ configs/ scripts/`
- 默认协作 Agent：Teacher Agent 和 Coding Agent
- Week 1 最小 CLI Agent
- Week 2 状态与工作流
- 本地工具：`read_file`、`list_dir`、`count_lines`
- trace 输出
- 工具失败处理
- 自动化测试
- 本地 RAG 最小闭环

当前缺口：

- RAG 评估用例还不完整。
- MCP 还没有实现。
- 还没有完成 RAG 与 Agent 的更完整联调验证。

## 当前总目标

先巩固 Week 3：确认你理解本地 RAG 最小闭环，然后再进入 MCP。

最小闭环：

```text
用户输入 -> 路由判断 -> 工具调用或直接回答 -> 工具结果/错误 -> 最终回答
```

## 当前具体任务

下一步建议：

1. 由 Teacher Agent 讲解 RAG 代码结构。
2. 你手动运行 3-4 个 RAG CLI 示例，观察检索结果。
3. 补一份 RAG 复盘。
4. 再进入 MCP：统一协议接入。

## 当前学习重点

学习者需要重点理解：

- RAG 不是简单检索关键词，而是“文档加载 + 切分 + 检索 + 上下文组装”的流程。
- 检索层必须可解释，否则后续很难做评估和调优。
- 错误处理仍然是最小闭环的一部分，不是后期再补的细节。
- eval case 是学习 RAG 的核心资产，用于判断系统是否真的命中正确上下文。

## 已完成

- 初始化项目目录。
- 创建 README 学习路线。
- 创建 Teacher Agent / Coding Agent 定义。
- 创建仓库级 `AGENTS.md` 协作规则。
- 创建学习总任务大纲：`docs/learning-master-plan.md`。
- 创建 Week 1 任务计划：`docs/week1-task-plan.md`。
- 实现 Week 1 最小 CLI Agent。
- 实现 `read_file` 和 `list_dir` 两个本地安全工具。
- 实现输入路由、trace 和失败处理。
- 补充自动化测试并通过验证。
- 补充 Week 1 架构图：`docs/week1-architecture.md`。
- 补充 Week 1 示例运行记录：`examples/week1-basic-agent/sample-runs.md`。
- 更新 Week 1 eval case 实际结果：`evals/week1-basic-agent/cases.md`。
- 完成 Week 2 状态与工作流实现。
- 补充 Week 2 流程图：`docs/state-workflow-flow.md`。
- 开始实现 Week 3 本地 RAG 最小闭环。

## 未完成

- RAG 评估用例。
- MCP 最小接入。
- 后续接入真实 LLM 决策层。

## 恢复指令

下一个会话恢复时，请先读取：

1. `AGENTS.md`
2. `docs/current-learning-state.md`
3. `docs/learning-master-plan.md`
4. `docs/state-workflow-flow.md`
5. `rag/README.md`
6. `tests/test_rag.py`

然后继续执行当前具体任务。

## 下一步建议

下一步优先让 Teacher Agent 讲解这次新增代码：

- `rag/documents.py`
- `rag/chunking.py`
- `rag/retrieval.py`
- `rag/qa.py`
- `agent/tools.py`
- `agent/router.py`
