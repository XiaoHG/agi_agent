# v39：LLM-First Direct Answer and Intent Entry

## 本阶段目标

把顶层 `direct_answer` 从固定模板回答升级为真正的 LLM-first 直接回答入口，同时保留 deterministic fallback，让项目的“无需工具时如何回答”也进入专业 Agent 主链。

## 本阶段在工业 Agent 中的位置

工业 Agent 的顶层入口不能长期停留在硬编码模板。

即使请求不需要本地工具，系统仍然需要：

- 统一的直接回答能力
- 清晰的失败边界
- 可追踪的回答来源
- 与 graph runtime 一致的执行路径

`v39` 解决的是“Agent 在不调用工具时，如何以专业方式回答并保留工程边界”。

## 本阶段解决的问题

- 让 direct answer 不再只依赖 `_compose_direct_answer()` 的固定规则文本
- 让 classic runtime 和 graph runtime 共享同一套 direct-answer 能力
- 让 direct answer 具备 `llm / deterministic_fallback` 的来源标记
- 让直接回答也进入 structured trace

## 本阶段新增能力

### 1. direct-answer 独立模块

新增 `agent/direct_answer.py`，集中管理：

- `DirectAnswerResult`
- direct-answer prompt message 构建
- LLM-first 直接回答逻辑
- deterministic fallback

### 2. direct-answer 专用 prompt

新增：

- `prompts/v39_direct-answer.md`

这让 direct answer 不再借用别的 prompt，而是有自己的输出边界和风格约束。

### 3. classic / graph 共用 direct-answer 能力

`WorkspaceAgent` 顶层 direct answer 和 LangGraph 中的 route-hint `direct_answer` 现在都走同一套 helper：

- LLM 可用时优先用 LLM
- LLM 不可用时退回 deterministic fallback

### 4. direct-answer trace 数据

`AgentRun` 新增 `direct_answer_result`，并进入：

- `format_trace()`
- `to_trace_dict()`

因此这个版本不只是“回答更像 LLM”，而是 direct answer 正式进入工程化 trace。

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `agent/direct_answer.py` | direct answer 数据模型与执行逻辑 |
| `agent/core.py` | 接入 LLM-first direct answer 与 trace |
| `integrations/langgraph_workflow.py` | graph route-hint direct answer 接入同一能力 |
| `agent/prompts.py` | 增加 direct-answer prompt loader |
| `prompts/v39_direct-answer.md` | direct answer prompt |
| `tests/test_agent.py` | direct answer 的 LLM / fallback 测试 |
| `tests/test_langgraph_workflow.py` | graph direct answer 测试 |
| `cli/README.md` | direct answer 行为说明 |

## 核心实现说明

### 1. 为什么这是一个大功能版本

因为这不是把固定模板换成一条 API 调用，而是把顶层 direct answer 从“硬编码示例回复”升级成一套独立的工业能力模块：

- 有专用 prompt
- 有统一 helper
- 有 classic / graph 共用逻辑
- 有 fallback 边界
- 有 trace 数据
- 有测试

### 2. 为什么要保留 deterministic fallback

因为 direct answer 虽然更适合用 LLM，但 Agent 入口不能在模型不可用时直接瘫痪。

保留 fallback 的意义是：

- 保证 CLI 基本可用
- 保证测试可控
- 保证学习过程不完全依赖外部 API

### 3. 为什么 tool_call 的 `answer_directly` 暂时没有一起改

本阶段只聚焦“顶层 direct answer and intent entry”。

`tool_call` 内部的 `answer_directly` 属于另一个能力层，它发生在“模型已经先进入工具选择流程之后”。如果把那条链也一起重构，会让本版本的主题从一个大模块变成两个交叉模块。

## 运行示例

直接回答：

```bash
python -m cli.main --input "Explain the difference between an agent and a chatbot."
```

查看 trace：

```bash
python -m cli.main --input "Explain the difference between an agent and a chatbot." --trace
```

## 验证命令

```bash
python -m unittest tests.test_agent tests.test_langgraph_workflow tests.test_tool_calling -v
python -m unittest tests.test_persistence -v
```

## 当前边界

- `tool_call` 路径内部的 `answer_directly` 仍然保留原行为
- 还没有做真正的 LLM-first intent planner 入口
- direct answer 还没有纳入专门的 eval case 分层

## 下一步建议

下一阶段应进入：

`v40：Standardized MCP Execution Boundary`

重点是把当前学习版 MCP 提升为更标准化的外部工具执行边界。
