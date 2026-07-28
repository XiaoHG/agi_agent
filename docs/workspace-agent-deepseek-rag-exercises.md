# WorkspaceAgent 接入 DeepSeek RAG 阶段练习答案

本文档用于复盘 v10：WorkspaceAgent 接入 DeepSeek RAG 阶段。

本阶段目标是理解“独立 RAG 能力”如何进入主 Agent 工具链。

核心链路：

```text
用户输入
  -> WorkspaceAgent.run()
  -> route_intent()
  -> answer_docs_with_llm tool
  -> answer_question_with_llm()
  -> DeepSeek
  -> Agent trace
  -> final answer
```

## 练习 1：运行主 Agent DeepSeek RAG

运行命令：

```bash
python -m cli.main --input "Answer with local docs and DeepSeek RAG: What does MCP mean in this project?" --trace
```

### 1. trace 中的 route action 是什么？

route action 是：

```text
use_tool
```

因为该请求需要调用本地工具链，而不是直接回答。

### 2. trace 中的 tool name 是什么？

tool name 是：

```text
answer_docs_with_llm
```

trace 中会看到类似：

```text
Route request: use_tool / answer_docs_with_llm
Run tool: answer_docs_with_llm completed
```

### 3. 最终调用的是 `search_docs` 还是 `answer_docs_with_llm`？

最终调用的是：

```text
answer_docs_with_llm
```

`search_docs` 只做 deterministic retrieval，返回检索 chunk。

`answer_docs_with_llm` 会继续调用 DeepSeek，生成 grounded answer。

### 4. 输出中的 `Sources` 来自哪里？

`Sources` 来自本地 RAG 检索命中的 `TextChunk.source_label()`。

路径：

```text
answer_docs_with_llm()
  -> answer_question_with_llm()
  -> answer_question()
  -> retrieve()
  -> result.chunk.source_label()
```

source label 格式类似：

```text
docs/mcp-local-protocol-review.md:1-40
```

含义是：

```text
文件路径:起始行-结束行
```

### 5. 这个命令和 `python -m cli.rag_llm_demo --question "What does MCP mean in this project?"` 的区别是什么？

`cli.rag_llm_demo` 是独立 RAG demo，直接调用：

```text
rag.answer_question_with_llm()
```

它绕过主 Agent。

`cli.main` 是主 Agent 入口，会经过：

```text
WorkspaceAgent.run()
route_intent()
_call_tool()
trace
final answer
```

区别：

```text
rag_llm_demo 验证 RAG + LLM 能力本身
cli.main 验证 RAG + LLM 是否接入 Agent 主工具链
```

## 练习 2：阅读 `agent/router.py`

### 1. `_looks_like_llm_rag_request()` 负责什么？

它负责判断用户请求是否是在要求使用 LLM-grounded RAG。

如果命中，它会让 `route_intent()` 返回：

```python
ToolRoute(
    action="use_tool",
    tool_name="answer_docs_with_llm",
    tool_input=...,
)
```

### 2. 哪些关键词会触发 LLM-grounded RAG？

当前关键词包括：

```text
answer docs
answer documentation
answer from docs
answer from documentation
answer with docs
answer with local docs
answer with local context
deepseek rag
grounded answer
grounded rag
llm rag
rag answer
use deepseek rag
```

这些关键词会触发 `answer_docs_with_llm`。

### 3. 为什么 LLM RAG 路由必须放在 `_looks_like_knowledge_search()` 之前？

因为 LLM RAG 请求通常也包含：

```text
rag
local docs
docs
knowledge
```

这些词也会命中 `_looks_like_knowledge_search()`。

如果普通 knowledge search 先判断，请求会被提前路由到：

```text
search_docs
```

而不是：

```text
answer_docs_with_llm
```

所以更具体的 LLM RAG 路由必须放在更通用的 knowledge search 路由之前。

### 4. `_extract_llm_rag_question()` 为什么要去掉 `Answer with local docs and DeepSeek RAG:` 这类前缀？

因为这个前缀是用户给 Agent 的操作指令，不是实际问题。

真正应该进入 RAG 检索的问题是：

```text
What does MCP mean in this project?
```

而不是：

```text
Answer with local docs and DeepSeek RAG: What does MCP mean in this project?
```

如果不去掉前缀，检索会受到 `DeepSeek`、`RAG`、`local docs` 等无关词影响。

### 5. 如果不去掉前缀，会导致什么问题？

会导致检索污染。

例如 eval 中的问题：

```text
Answer with local docs and DeepSeek RAG: the and of
```

如果把完整输入送进检索，系统可能命中文档里的 `DeepSeek RAG` 说明，而不是只判断真正的问题。

结果是：

```text
本来应该无 context
却因为指令前缀命中文档
从而触发真实 LLM 请求
```

这会破坏测试稳定性，也会降低 RAG 检索准确性。

## 练习 3：阅读 `agent/tools.py`

### 1. `search_docs()` 的职责是什么？

`search_docs()` 的职责是 deterministic retrieval。

它调用：

```python
answer_question(root, question)
```

然后返回检索结果：

```text
Source
Score
Matched terms
Context preview
```

它不调用 DeepSeek。

### 2. `answer_docs_with_llm()` 的职责是什么？

`answer_docs_with_llm()` 的职责是 LLM-grounded RAG。

它调用：

```python
answer_question_with_llm(root, question)
```

流程是：

```text
本地检索 -> 构造 prompt -> DeepSeek 推理 -> 返回 answer + sources
```

### 3. 为什么没有直接替换 `search_docs()`？

因为两者职责不同。

`search_docs()` 适合：

- 调试检索
- 查看原始 context
- 默认测试
- 无网络环境
- 不产生 LLM 成本

`answer_docs_with_llm()` 适合：

- 给用户生成最终答案
- 综合多个 context
- 真实 Agent 问答体验

如果直接替换，会破坏已有稳定测试和检索调试能力。

### 4. `answer_docs_with_llm()` 为什么要捕获 `LLMError` 并转换成 `ToolError`？

因为在主 Agent 工具链中，工具失败应该统一表现为：

```text
ToolError
```

`LLMError` 是 LLM client 层错误。

`ToolError` 是 Agent tool 层错误。

转换后，`WorkspaceAgent.run()` 可以用已有逻辑处理失败：

```python
except ToolError as error:
    run.tool_error = str(error)
    run.steps.append(AgentStep("Tool failed", run.tool_error))
    run.answer = self._compose_tool_error_answer(run)
```

这保持了错误边界清晰。

### 5. 这两个工具分别适合什么场景？

`search_docs` 适合：

```text
Search docs for MCP.
Show local context for workflow.
Inspect project documentation matches.
```

`answer_docs_with_llm` 适合：

```text
Answer with local docs and DeepSeek RAG: What does MCP mean in this project?
Give a grounded answer from local context.
Use DeepSeek RAG to explain workflow.
```

## 练习 4：阅读 `agent/core.py`

### 1. `_call_tool()` 在主 Agent 中负责什么？

`_call_tool()` 负责工具分发。

它根据：

```python
route.tool_name
```

调用对应工具函数。

例如：

```text
read_file -> read_file()
search_docs -> search_docs()
answer_docs_with_llm -> answer_docs_with_llm()
```

### 2. v10 新增了哪一个分支？

新增：

```python
if route.tool_name == "answer_docs_with_llm":
    return answer_docs_with_llm(self.workspace_root, route.tool_input or "")
```

### 3. 如果 router 返回 `answer_docs_with_llm`，执行链路会怎么走？

链路：

```text
WorkspaceAgent.run()
  -> route_intent()
  -> ToolRoute(tool_name="answer_docs_with_llm")
  -> WorkspaceAgent._call_tool()
  -> agent.tools.answer_docs_with_llm()
  -> rag.answer_question_with_llm()
  -> DeepSeekLLMClient.chat()
  -> ToolResult("answer_docs_with_llm", output)
  -> WorkspaceAgent._compose_tool_answer()
  -> final answer
```

### 4. 如果工具抛出 `ToolError`，`WorkspaceAgent.run()` 会如何处理？

会进入：

```python
except ToolError as error:
```

然后：

```text
1. 记录 run.tool_error
2. 追加 Tool failed step
3. 调用 _compose_tool_error_answer()
4. 返回用户可读错误信息
```

最终不会让异常直接崩掉 CLI。

### 5. 为什么工具结果最终能出现在 `--trace` 输出里？

因为成功调用工具后，结果保存在：

```python
run.tool_result
```

`format_trace()` 会输出：

```python
if run.tool_result is not None:
    parts.append("\n[Tool] " + run.tool_result.tool_name)
    parts.append(run.tool_result.output)
```

所以 `--trace` 中会显示工具名和工具输出。

## 练习 5：理解 v10 的测试变更

### 1. `test_route_to_answer_docs_with_llm` 验证什么？

它验证 LLM RAG 请求会被正确路由到：

```text
answer_docs_with_llm
```

并且 route action 是：

```text
use_tool
```

### 2. 它为什么要检查 `route.tool_input`？

因为 v10 的一个关键修复是：

```text
去掉操作前缀，只保留真实问题
```

测试期望：

```python
route.tool_input == "What does workflow mean?"
```

这可以防止再次出现“指令前缀污染检索”的问题。

### 3. `test_answer_docs_with_llm_tool_handles_no_context` 为什么不会调用真实 DeepSeek？

因为它使用临时目录，并写入一个不相关的 README：

```python
(root / "README.md").write_text("agent workflow", encoding="utf-8")
```

然后查询：

```text
qa-no-context-token-928374
```

没有检索结果时，`answer_question_with_llm()` 会直接返回 insufficient，不调用 LLM。

### 4. `test_agent_answers_docs_with_llm_without_context` 验证的是工具层还是 Agent 主链路？

验证的是 Agent 主链路。

它创建：

```python
agent = WorkspaceAgent(root)
```

然后调用：

```python
agent.run("Answer with local docs and DeepSeek RAG: qa-no-context-token-928374")
```

这覆盖：

```text
route_intent()
_call_tool()
answer_docs_with_llm()
final answer
```

所以它不是单独测工具函数，而是测主 Agent 接线。

### 5. 为什么 `test_rag_returns_empty_result_for_unknown_keyword` 要改成临时目录测试？

因为项目文档会不断增加。

之前测试直接用当前仓库：

```python
answer_question(Path("."), "zzzz-not-existing-keyword")
```

后来复盘文档里写入了这个关键词，导致检索命中，测试失败。

改成临时目录后，测试数据完全可控，不会被新增文档污染。

这是更专业的测试隔离方式。

## 练习 6：理解新增 eval case

### 1. `llm-rag-no-context` 这个 eval case 验证什么？

它验证主 Agent 可以把 LLM RAG 请求路由到：

```text
answer_docs_with_llm
```

并返回无上下文时的稳定边界结果：

```text
Answer:
The local context is insufficient...

Sources:
- none
```

### 2. 为什么它选择无本地上下文问题？

因为默认 eval 不应该触发真实 DeepSeek 网络请求。

该 eval 使用的真实问题只包含检索停用词，没有有效 query terms，因此 `answer_question_with_llm()` 会提前返回：

```text
The local context is insufficient to answer this question.
```

这样 eval 可以验证接线边界，同时保持稳定、快速、无成本。

### 3. 为什么默认 eval 不应该触发真实 DeepSeek？

原因：

- 默认 eval 要稳定
- 默认 eval 要快速
- 默认 eval 不应该产生 API 成本
- 默认 eval 不应该依赖 API Key
- LLM 输出有不确定性，不适合简单关键词断言

真实 LLM eval 后续应该单独设计。

### 4. 它验证的是“真实 LLM 回答质量”还是“主 Agent 接线边界”？

它验证的是：

```text
主 Agent 接线边界
```

包括：

- route 是否正确
- tool 是否正确
- 无 context 行为是否稳定

它不验证真实 LLM 回答质量。

### 5. 如果要评估真实 RAG 答案质量，应该另起什么类型的 eval？

应该另起：

```text
RAG answer quality eval
RAG faithfulness eval
LLM integration smoke eval
citation correctness eval
```

这些 eval 可以单独运行，不放进默认快速回归。

## 练习 7：手动验证命令

### 1. `python -m unittest discover -s tests -v` 验证什么？

验证项目默认自动化测试。

覆盖：

- Agent routing
- tools
- workflow
- deterministic RAG
- DeepSeek LLM client 边界
- LLM-grounded RAG 边界
- WorkspaceAgent 接入 LLM RAG
- MCP
- Skills
- Subagent
- eval runner

### 2. `python -m cli.eval_runner` 验证什么？

验证主 Agent 的 deterministic regression cases。

当前包括：

- direct answer
- file reading
- deterministic RAG
- MCP
- Skills
- Subagent
- workflow
- LLM RAG no-context 接线边界

### 3. `python -m cli.main --input "Answer with local docs and DeepSeek RAG: What does workflow mean in this project?" --trace` 验证什么？

验证真实主 Agent + DeepSeek RAG 链路。

覆盖：

```text
CLI
WorkspaceAgent.run()
router
answer_docs_with_llm tool
local retrieval
DeepSeek API
trace output
final answer
sources
```

### 4. 第三条命令失败时，可能是哪几类问题？

可能原因：

- `DEEPSEEK_API_KEY` 缺失
- DeepSeek API 网络失败
- 模型名配置错误
- DeepSeek endpoint 配置错误
- 检索没有命中相关 context
- prompt 构造异常
- LLM 返回空内容
- API quota / permission 问题
- router 没有正确识别请求
- tool dispatch 没有接上

### 5. 为什么前两条命令不应该依赖真实 DeepSeek 网络请求？

因为它们是默认验证命令。

默认验证应该：

```text
稳定
快速
低成本
不依赖外部服务
适合频繁运行
```

真实 DeepSeek 请求应该作为单独 smoke test 运行。

## 练习 8：当前 v10 的限制

### 限制 1

限制：路由仍然是规则路由。

原因：当前依赖关键词识别，例如 `deepseek rag`、`answer with local docs`。

后续改进：引入 LLM router 或 LangGraph conditional routing。

### 限制 2

限制：`WorkspaceAgent` direct answer 还没有使用真实 LLM。

原因：当前 direct answer 仍然是 `_compose_direct_answer()` 中的固定规则回答。

后续改进：让 direct answer 可以调用 DeepSeek，但保留可测试边界。

### 限制 3

限制：RAG 检索仍然不是向量检索。

原因：当前 `retrieve()` 使用关键词 overlap。

后续改进：接入 embedding 模型和向量数据库。

### 限制 4

限制：还没有 LangChain tool schema。

原因：当前工具只是普通 Python 函数和内部 `ToolResult`。

后续改进：新增 adapter，把本地工具包装成标准 tool schema。

### 限制 5

限制：还没有 LangGraph workflow。

原因：当前 workflow 仍然是自定义简单流程。

后续改进：用 LangGraph 表达状态、节点、边和条件流转。

### 限制 6

限制：没有真实 RAG answer quality eval。

原因：当前 eval 只验证接线边界，不判断 LLM 回答是否忠实。

后续改进：新增 faithfulness eval、citation eval、answer relevance eval。

### 限制 7

限制：没有 citation checker。

原因：当前只展示 sources，没有验证答案中的引用是否来自 sources。

后续改进：结构化 citations，并校验引用合法性。

### 限制 8

限制：没有 token usage / cost tracking。

原因：虽然 LLM raw response 被保留，但还没有解析 usage。

后续改进：在 `LLMResponse` 中增加 usage，并写入 trace。

### 限制 9

限制：没有 retry / timeout 分类。

原因：当前 LLM 请求失败后直接转换为错误。

后续改进：增加错误类型、重试策略和退避机制。

### 限制 10

限制：不支持 streaming。

原因：当前 HTTP client 一次性读取响应。

后续改进：增加流式输出能力。

## 练习 9：设计下一阶段 v11

下一阶段建议：

```text
v11：LangChain Tool Adapter
```

### 1. 为什么下一阶段应该做 tool adapter，而不是马上做 LangGraph？

LangGraph 是 workflow 编排框架。

但 LangGraph 节点通常需要调用标准化工具。

当前项目已有很多本地工具，但还没有统一 schema。

如果现在直接做 LangGraph，会出现：

```text
图结构有了，但节点里仍然是直接调用内部函数
```

所以更合理顺序是：

```text
本地工具 -> tool schema adapter -> LangGraph workflow
```

### 2. 当前项目已有哪些本地工具可以被包装成专业 tool schema？

可以包装：

```text
read_file
list_dir
count_lines
search_docs
answer_docs_with_llm
list_mcp_tools
mcp_workspace_summary
list_skills
plan_skill
list_subagents
plan_subagents
```

### 3. Tool schema 至少应该包含哪些字段？

至少包含：

```text
name
description
args_schema
return_schema
side_effects
requires_network
requires_api_key
```

简单版本可以先包含：

```text
name
description
input_description
callable
```

### 4. 为什么 adapter 层不能污染 `agent/tools.py`？

因为 `agent/tools.py` 是项目内部工具实现层。

LangChain adapter 是框架适配层。

如果把 LangChain 代码直接写进 `agent/tools.py`，会导致：

- core tools 依赖外部框架
- 测试变复杂
- 后续换框架困难
- 工具实现和框架包装混杂

正确做法：

```text
agent/tools.py = core tool implementation
integrations/langchain_tools.py = framework adapter
```

### 5. 建议新增哪些文件？

建议新增：

```text
integrations/__init__.py
integrations/langchain_tools.py
tests/test_langchain_tools.py
versions/langchain-tool-adapter_v11.md
```

如果暂时不安装 LangChain，也可以先实现兼容 LangChain 结构的轻量 adapter，再接真实依赖。

### 6. 建议修改哪些文件？

建议修改：

```text
pyproject.toml
README.md
docs/current-learning-state.md
```

如果接真实 LangChain，需要在 `pyproject.toml` 增加依赖。

### 7. 应该新增哪些测试？

建议新增：

```text
test_build_langchain_tool_specs
test_tool_spec_contains_name_description_args
test_read_file_tool_adapter_invokes_core_tool
test_answer_docs_with_llm_tool_marks_network_dependency
```

### 8. 应该新增哪些验证命令？

建议新增：

```bash
python -m unittest discover -s tests -v
```

如果新增 CLI：

```bash
python -m cli.langchain_tools_demo
```

后续 LangGraph 阶段再验证：

```bash
python -m cli.langgraph_demo
```

## 本阶段最低通过标准

完成 v10 后，你应该能讲清：

1. `cli.main` 如何通过主 Agent 调用 DeepSeek RAG。
2. `search_docs` 和 `answer_docs_with_llm` 的职责差异。
3. 为什么路由阶段要清洗真实问题。
4. 为什么 eval 里的 LLM RAG case 不触发真实 DeepSeek。
5. v10 还不是完整专业 Agent 框架，只是把 LLM RAG 接入了主工具链。
6. 下一阶段为什么应该做 LangChain Tool Adapter。
