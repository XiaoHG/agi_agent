# LLM-First Direct Answer and Intent Entry v39 练习

对应版本：v39  
主题：LLM-First Direct Answer and Intent Entry  
用途：理解为什么 direct answer 也必须升级成专业 Agent 的一等能力

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v39` 不只是“换成 LLM 回答一下”？
2. direct answer 为什么也需要独立 prompt？
3. `DirectAnswerResult` 的职责是什么？
4. 为什么本阶段要保留 deterministic fallback？
5. 为什么这个版本只聚焦顶层 direct answer，而没有顺手改完 tool_call 里的 `answer_directly`？

## 练习 2：读 direct-answer 链路

阅读：

- `agent/direct_answer.py`
- `agent/core.py`
- `integrations/langgraph_workflow.py`
- `prompts/direct-answer.v1.md`

请回答：

1. `answer_directly()` 做了哪些事？
2. `compose_direct_answer_fallback()` 在什么情况下会被用到？
3. `WorkspaceAgent` 是如何把 direct answer 结果写进 trace 的？
4. LangGraph route-hint `direct_answer` 为什么也要走同一个 helper？
5. `direct_answer.source` 和 `direct_answer.status` 为什么重要？

## 练习 3：动手验证

运行：

```bash
python -m cli.main --input "Explain the difference between an agent and a chatbot."
python -m cli.main --input "Explain the difference between an agent and a chatbot." --trace
```

请记录：

1. 输出是否仍然能直接回答，不需要本地工具？
2. trace 中是否出现了 direct answer 相关信息？
3. 如果环境中可用 LLM，回答是否更自然；如果不可用，是否仍有 fallback？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么 direct answer 是工业 Agent 入口的一部分，而不是“随便回一句”？
2. 为什么 `llm / deterministic_fallback` 这种来源标签要进入数据模型？
3. 如果下一步继续做更强的 intent entry，`v39` 最重要的基础价值是什么？

## 答案

### 练习 1：理解本阶段目标

1. `v39` 不只是“换成 LLM 回答一下”，因为它同时引入了专用 prompt、独立数据模型、classic / graph 共用 helper、fallback 边界和 trace 落盘。也就是说，direct answer 从硬编码分支升级成了一个独立的工程模块。
2. direct answer 需要独立 prompt，是因为它有自己的边界条件。它既不能像工具选择 prompt 那样输出结构化 JSON，也不能像 RAG prompt 那样假设已有本地证据。单独 prompt 能明确约束它不要伪造文件读取结果、不要乱用本地上下文。
3. `DirectAnswerResult` 的职责是把直接回答结果结构化，包括最终 answer、回答来源、执行状态和错误信息。这样 direct answer 不再只是一个字符串，而是可追踪、可测试、可导出的运行结果。
4. 保留 deterministic fallback 是为了避免 direct answer 完全依赖外部模型。如果 LLM 不可用，Agent 入口仍然需要保持最小可用性；同时测试和学习也不能被 API 可用性绑死。
5. 本阶段只聚焦顶层 direct answer，是为了保持版本主题单一。`tool_call` 内部的 `answer_directly` 属于另一个能力层，如果一起改，会把顶层入口升级和工具调用内部升级混在一个版本里，破坏总纲要求的“一个版本只做一个大模块”。

### 练习 2：读 direct-answer 链路

1. `answer_directly()` 会先构造 direct-answer prompt 消息，再优先尝试用 LLM 生成回答；如果没有可用 client，或者模型调用失败、返回空内容，就退回 deterministic fallback，并返回一个结构化的 `DirectAnswerResult`。
2. `compose_direct_answer_fallback()` 会在模型不可用、模型报错、或者 direct answer 响应为空时被调用。它保证 direct answer 至少还有一条稳定、确定性的返回路径。
3. `WorkspaceAgent` 会把 `direct_answer_result` 保存到 `AgentRun` 中，并在 `format_trace()` 里输出 `[Direct Answer]` 区块，在 `to_trace_dict()` 里输出 `direct_answer` 字段。这样 direct answer 和 tool / skill 一样，进入了结构化 trace。
4. LangGraph route-hint `direct_answer` 也要走同一个 helper，是为了避免 classic runtime 和 graph runtime 各自维护一套 direct-answer 逻辑。复用同一 helper 可以保持行为一致，也方便测试和后续扩展。
5. `direct_answer.source` 和 `direct_answer.status` 很重要，因为它们让系统和学习者都能看出这次回答到底来自 LLM 还是 fallback，以及本次 direct answer 是正常完成还是降级执行。这是工业 Agent 可观测性的一部分。

### 练习 3：动手验证

1. 输出应当仍然能直接回答，不需要本地工具，因为 `route_intent()` 仍会把这类问题判定为 `direct_answer`。
2. `--trace` 输出中应当出现 direct answer 相关信息，例如 source、status 和可能的 error，这说明 direct answer 已经进入 trace 体系。
3. 如果环境里有可用 LLM，回答通常会更自然、更完整；如果模型不可用，系统应当回退到 deterministic fallback，而不是直接失败。这正是 `v39` 的关键边界设计。

### 练习 4：工程取舍题

1. direct answer 是工业 Agent 入口的一部分，因为很多请求并不需要工具，但仍然需要高质量、可解释、可回退的回答路径。如果这一层只是“随便回一句”，整个 Agent 的顶层体验和工程边界都会很弱。
2. `llm / deterministic_fallback` 这种来源标签要进入数据模型，是因为系统需要知道答案是怎么来的。只有保留来源标签，后续才能做分析、调试、评估和恢复边界判断。
3. 如果下一步继续做更强的 intent entry，`v39` 最重要的基础价值是：它先把“无需工具时如何回答”这条主路径工程化了。之后无论做更强的 intent planner，还是做统一入口分析，都已经有了一个可追踪、可测试、可回退的 direct-answer 能力层。

## 验证

```bash
python -m unittest tests.test_agent tests.test_langgraph_workflow tests.test_tool_calling -v
python -m cli.main --input "Explain the difference between an agent and a chatbot." --trace
```
