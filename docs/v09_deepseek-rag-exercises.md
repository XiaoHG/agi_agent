# DeepSeek 驱动的专业 RAG 阶段练习答案

本文档用于复盘 v9：DeepSeek 驱动的专业 RAG 阶段。

本阶段目标是理解专业 RAG 的基本链路：

```text
用户问题 -> 本地检索 -> 构造 grounded prompt -> 真实 LLM 推理 -> 带来源回答
```

## 练习 1：运行 DeepSeek RAG

运行命令：

```bash
python -m cli.rag_llm_demo --question "What does MCP mean in this project?"
```

### 1. 这个命令最终调用了哪个模块？

最终调用：

```text
rag/llm_qa.py
answer_question_with_llm()
```

CLI 入口在：

```text
cli/rag_llm_demo.py
```

核心调用：

```python
answer = answer_question_with_llm(Path(args.root), args.question, top_k=args.top_k)
```

### 2. 它和 `python -m cli.rag_demo --question "What does MCP mean in this project?"` 的区别是什么？

`cli.rag_demo` 是 deterministic RAG，只做本地检索并返回命中的 chunk。

链路是：

```text
question -> load documents -> chunk -> retrieve -> return context chunks
```

`cli.rag_llm_demo` 是 LLM-grounded RAG，会先检索本地 context，再把 context 交给 DeepSeek 生成自然语言答案。

链路是：

```text
question -> retrieve context -> build prompt -> DeepSeek LLM -> grounded answer with sources
```

核心区别：

```text
rag_demo 返回证据
rag_llm_demo 基于证据生成答案
```

### 3. 输出里的 `Answer` 是从哪里生成的？

`Answer` 来自真实 DeepSeek LLM。

代码路径：

```text
answer_question_with_llm()
  -> build_grounded_rag_prompt()
  -> DeepSeekLLMClient.chat()
  -> response.content
```

也就是：

```python
response = client.chat([...])
return GroundedRAGAnswer(question=question, answer=response.content, sources=sources)
```

### 4. 输出里的 `Sources` 是从哪里来的？

`Sources` 来自本地检索结果的 source label。

代码：

```python
sources = [result.chunk.source_label() for result in retrieval_answer.results]
```

source label 的格式类似：

```text
docs/mcp-local-protocol-review.md:1-40
```

它表示：

```text
文件路径:起始行-结束行
```

### 5. 如果本地没有相关 context，会不会调用 DeepSeek？为什么？

不会。

代码逻辑：

```python
if not retrieval_answer.results:
    return GroundedRAGAnswer(
        question=question,
        answer="The local context is insufficient to answer this question.",
        sources=[],
    )
```

原因：

```text
RAG 的专业边界是基于检索上下文回答。
如果没有 context，继续调用 LLM 容易产生无依据回答。
```

这是防止 hallucination 的基础做法。

## 练习 2：阅读 `rag/llm_qa.py`

### 1. `RAG_SYSTEM_PROMPT` 的核心约束是什么？

核心约束有三个：

```text
1. 只基于提供的 context 回答。
2. 如果 context 不足，要明确说明 local context insufficient。
3. 必须提到相关 source labels。
```

对应内容：

```python
"Answer only from the provided context."
"If the context is insufficient, say that the local context is insufficient."
"Always mention the most relevant source labels."
```

### 2. `GroundedRAGAnswer` 为什么要同时保存 `answer` 和 `sources`？

因为专业 RAG 不能只给答案，还要给证据来源。

`answer` 用于用户阅读。

`sources` 用于：

- 复查答案依据
- 展示引用来源
- 后续做 faithfulness eval
- 后续生成结构化 trace
- 后续调试检索命中质量

如果只有答案，没有 sources，就无法判断 LLM 是否真的基于本地上下文。

### 3. `answer_question_with_llm()` 的主流程是什么？

主流程：

```text
1. 调用 answer_question() 做本地检索。
2. 从检索结果中提取 source labels。
3. 如果没有检索结果，直接返回 insufficient。
4. 如果有检索结果，创建 DeepSeekLLMClient。
5. 调用 build_grounded_rag_prompt() 构造 prompt。
6. 调用 DeepSeekLLMClient.chat()。
7. 将 LLM 回复和 sources 封装成 GroundedRAGAnswer。
```

对应代码结构：

```python
retrieval_answer = answer_question(root, question, top_k=top_k)
sources = [...]

if not retrieval_answer.results:
    return GroundedRAGAnswer(...)

client = llm_client or DeepSeekLLMClient()
prompt = build_grounded_rag_prompt(question, retrieval_answer.results)
response = client.chat([...])
return GroundedRAGAnswer(...)
```

### 4. 为什么无检索结果时直接返回 insufficient，而不是继续调用 LLM？

因为本阶段目标是 grounded RAG，不是普通聊天。

RAG 的可信度来自：

```text
回答必须有本地 context 支撑
```

如果没有 context 仍然调用 LLM，模型可能基于通用知识回答，看起来合理但不一定符合当前项目。

所以正确行为是：

```text
没有 context -> 不回答具体内容 -> 告诉用户本地上下文不足
```

### 5. `build_grounded_rag_prompt()` 里为什么要包含 source label？

source label 是 RAG 答案可追溯的关键。

它让模型知道每段 context 来自哪里，也让最终答案能引用来源。

例如：

```text
[Source 1] docs/mcp-local-protocol-review.md:1-40
```

这表示模型应该把该 context 和这个来源绑定起来。

后续也可以用 source label 做：

- citation 校验
- trace 记录
- 用户复查
- eval 判断

## 练习 3：完整调用流程

完整流程：

```text
python -m cli.rag_llm_demo --question "..."
  -> cli/rag_llm_demo.py main()
  -> argparse 解析 --root / --question / --top-k
  -> answer_question_with_llm(Path(args.root), args.question, top_k=args.top_k)
  -> answer_question(root, question, top_k)
  -> load_text_documents(root)
  -> chunk_documents(documents)
  -> retrieve(chunks, question, top_k)
  -> 返回 RAGAnswer(results)
  -> 从 results 提取 source labels
  -> 如果 results 为空，返回 insufficient，不调用 LLM
  -> build_grounded_rag_prompt(question, results)
  -> 构造 system message: RAG_SYSTEM_PROMPT
  -> 构造 user message: grounded RAG prompt
  -> DeepSeekLLMClient.chat(messages)
  -> DeepSeek API 返回 choices[0].message.content
  -> GroundedRAGAnswer(question, answer, sources)
  -> GroundedRAGAnswer.to_text()
  -> print answer and sources
  -> return exit code 0
```

## 练习 4：对比 deterministic RAG 和 LLM-grounded RAG

运行：

```bash
python -m cli.rag_demo --question "What does MCP mean in this project?"
```

再运行：

```bash
python -m cli.rag_llm_demo --question "What does MCP mean in this project?"
```

### 1. 两个命令输出结构有什么不同？

`rag_demo` 输出结构偏检索报告：

```text
Result: found N relevant local context chunks
Source 1
Score
Matched terms
Context
```

`rag_llm_demo` 输出结构偏最终回答：

```text
Answer:
模型生成的回答

Sources:
- source label
- source label
```

### 2. deterministic RAG 的优点是什么？

优点：

- 稳定
- 可重复
- 不需要 API Key
- 不产生调用成本
- 方便测试
- 能直接看到原始证据
- 不会产生模型幻觉

它适合做检索调试和底层回归测试。

### 3. LLM-grounded RAG 的优点是什么？

优点：

- 能把多个 chunk 综合成自然语言答案
- 用户体验更接近真实 Agent
- 能解释、归纳和压缩本地 context
- 能围绕问题生成更直接的回答
- 后续可以接入工具调用、规划和多轮交互

它更接近专业 Agent 应用中的 RAG。

### 4. LLM-grounded RAG 的风险是什么？

风险：

- 可能幻觉
- 可能忽略部分 context
- 可能引用不准确
- 网络请求可能失败
- API 调用有成本
- 输出不完全确定
- prompt 太长时可能超上下文

所以必须保留 sources、测试、eval 和 trace。

### 5. 为什么项目里还保留 deterministic RAG？

因为 deterministic RAG 是 LLM-grounded RAG 的基础。

保留它的原因：

- 用于调试检索质量
- 用于稳定测试
- 用于检查 LLM 输入的 context
- 用于无网络环境下验证 RAG 基础链路
- 用于和 LLM-grounded 输出做对比

专业项目里通常也会把 retrieval 和 generation 分开验证。

## 练习 5：理解测试文件

阅读：

```bash
tests/test_rag_llm.py
```

### 1. `StubLLMClient` 的作用是什么？

`StubLLMClient` 用于测试 `answer_question_with_llm()` 的本地逻辑。

它模拟的是 client 接口边界：

```python
def chat(self, messages):
    self.messages = messages
    return LLMResponse(...)
```

它让测试可以验证：

- prompt 是否构造正确
- messages 是否传入 LLM client
- sources 是否保留
- 无 context 时是否跳过 LLM

### 2. 它是不是 FakeLLM？为什么这里允许使用？

严格说，它是测试 stub，不是产品路线里的 FakeLLM。

区别：

```text
FakeLLM = 用假的模型行为替代真实 LLM 作为开发主线
StubLLMClient = 单元测试中替代网络边界，验证本地代码逻辑
```

这里允许使用，因为默认单元测试不应该依赖真实网络、API Key 和模型输出。

真实 LLM 行为通过：

```bash
python -m cli.rag_llm_demo --question "..."
```

来验证。

### 3. `test_build_grounded_rag_prompt_includes_sources` 验证什么？

验证 `build_grounded_rag_prompt()` 包含关键内容：

- `Question:`
- source label，例如 `README.md:1-1`
- context 文本
- `using only the local context` 约束

这保证 prompt 具备 grounded RAG 所需的基本结构。

### 4. `test_answer_question_with_llm_returns_no_context_without_results` 验证什么？

验证没有检索结果时：

- 返回空 sources
- answer 包含 `insufficient`
- 不需要调用真实 LLM

这是防 hallucination 的重要边界。

### 5. `test_answer_question_with_llm_preserves_sources` 验证什么？

验证有检索结果时：

- 返回的 sources 包含 source label
- LLM answer 被封装进 `GroundedRAGAnswer`
- system/user messages 被正确发送给 LLM client

核心是确认：

```text
retrieval sources 没有在 LLM 生成后丢失
```

### 6. 为什么默认测试不直接请求 DeepSeek？

原因：

- 默认测试需要快速
- 默认测试需要稳定
- 默认测试不应依赖网络
- 默认测试不应消耗 API 费用
- 默认测试不应依赖本地是否配置 API Key
- LLM 输出不完全确定，不适合普通断言

真实 DeepSeek 验证应该作为 smoke test 或集成验证单独运行。

## 练习 6：手动验证命令

### 1. `python -m unittest discover -s tests -v` 验证什么？

验证项目默认自动化测试。

当前覆盖：

- Agent 主循环
- 工具
- workflow
- RAG deterministic retrieval
- DeepSeek LLM client 边界
- DeepSeek RAG prompt 和封装逻辑
- MCP
- Skills
- Subagent
- eval runner
- project assistant

### 2. `python -m cli.eval_runner` 验证什么？

验证主 Agent 的 deterministic regression cases。

检查：

- route 是否符合预期
- tool 是否符合预期
- answer 是否包含必要关键词

它目前主要覆盖 `WorkspaceAgent` 的稳定行为。

### 3. `python -m cli.rag_llm_demo --question "What does workflow mean in this project?"` 验证什么？

验证真实 DeepSeek RAG 链路。

包括：

- 本地文档能加载
- 检索能命中 workflow 相关 context
- prompt 能正确构造
- DeepSeek API 能调用成功
- LLM 能基于 context 生成回答
- sources 能输出

### 4. 为什么真实 RAG LLM demo 不应该放进默认单元测试？

因为它依赖外部系统和真实模型。

默认单元测试应该是：

```text
无网络
低成本
稳定
快速
可重复
```

真实 LLM demo 更适合作为：

- 手动验证
- 集成测试
- smoke test
- 发布前检查

### 5. 如果第三条失败，可能是哪几类问题？

可能原因：

- `DEEPSEEK_API_KEY` 缺失或无效
- DeepSeek API 网络不可达
- 模型名配置错误
- API endpoint 配置错误
- 本地检索没有命中相关 context
- prompt 构造异常
- DeepSeek 返回异常 JSON
- 请求超时
- 账户额度或权限问题

## 练习 7：当前 v9 的限制

### 限制 1

限制：LLM-grounded RAG 还没有接入 `WorkspaceAgent`。

原因：当前只有 `cli.rag_llm_demo` 调用 `answer_question_with_llm()`，主 Agent 的 `search_docs` 仍然调用 deterministic RAG。

后续改进：新增 `search_docs_with_llm` 工具，并在 router 中识别需要 grounded answer 的请求。

### 限制 2

限制：检索仍然是关键词检索，不是 embedding/vector search。

原因：当前 `retrieve()` 基于 token overlap 和简单 score。

后续改进：引入 embedding 模型和向量库，例如 Chroma、FAISS、LanceDB 或其他专业向量检索方案。

### 限制 3

限制：没有 token-aware context packing。

原因：当前直接把 top-k chunk 放进 prompt，没有计算 token 长度。

后续改进：增加 context budget，根据模型上下文窗口选择和裁剪 chunk。

### 限制 4

限制：citation 没有结构化校验。

原因：当前 sources 单独保存，但没有验证 LLM 答案是否真的引用了这些 source labels。

后续改进：增加 citation checker，要求答案中的 citation 必须来自 retrieval sources。

### 限制 5

限制：没有 faithfulness eval。

原因：当前 eval 只检查 route/tool/关键词，没有判断答案是否忠实于 context。

后续改进：新增 RAG faithfulness eval，例如检查答案是否包含 unsupported claims。

### 限制 6

限制：不支持 streaming。

原因：`DeepSeekLLMClient` 当前使用一次性 HTTP 响应。

后续改进：增加 streaming client，支持边生成边输出。

### 限制 7

限制：没有 retry。

原因：当前 DeepSeek 请求失败后直接抛出 `LLMError`。

后续改进：增加有限重试、指数退避和错误分类。

### 限制 8

限制：没有 token usage / cost 记录。

原因：`LLMResponse.raw` 保留了原始响应，但还没有解析 usage 字段。

后续改进：在 `LLMResponse` 中增加 usage 字段，并写入 trace/logs。

### 限制 9

限制：不支持不同文档集合。

原因：`load_text_documents()` 默认加载 `README.md`、`docs`、`versions`。

后续改进：允许用户指定文档集合、索引名称或知识库路径。

## 练习 8：设计下一阶段 v10

下一阶段建议：

```text
v10：将 DeepSeek RAG 接入 WorkspaceAgent 工具链
```

### 1. 为什么下一阶段应该把 RAG + LLM 接回 `WorkspaceAgent`？

因为当前 LLM-grounded RAG 只是独立 CLI 能力。

真正的 Agent 项目应该让用户通过主 Agent 入口调用专业 RAG：

```bash
python -m cli.main --input "Answer with DeepSeek RAG: What does MCP mean in this project?"
```

接回 `WorkspaceAgent` 后，RAG + LLM 才进入：

- 路由
- 工具调用
- trace
- eval
- workflow

这才是 Agent 工程主链路。

### 2. 当前 `search_docs` 工具和新的 `answer_question_with_llm()` 应该如何区分？

建议区分为：

```text
search_docs = deterministic retrieval，返回 context chunks
answer_docs_with_llm = LLM-grounded RAG，返回最终答案和 sources
```

二者职责不同：

```text
search_docs 用于检索调试和证据查看
answer_docs_with_llm 用于面向用户生成最终回答
```

### 3. 应该新增一个新工具，还是替换原有 `search_docs`？为什么？

应该新增新工具，不应该直接替换。

原因：

- 保留 deterministic RAG 便于调试
- 避免破坏现有 eval case
- 两者工程职责不同
- 用户有时只想看检索结果，不想调用 LLM
- 新工具可以单独做 eval 和 trace

建议工具名：

```text
answer_docs_with_llm
```

或：

```text
search_docs_with_llm
```

### 4. 路由应该如何识别“需要 LLM-grounded RAG”的请求？

可以先用规则关键词识别：

```text
answer docs
answer with docs
answer from docs
grounded answer
rag answer
use deepseek rag
answer with local context
```

路由结果：

```python
ToolRoute(
    action="use_tool",
    tool_name="answer_docs_with_llm",
    tool_input=text,
    reason="The user is asking for a grounded answer from local documents."
)
```

后续可以用 LLM router 替换规则 router。

### 5. trace 应该记录哪些新增信息？

应该记录：

- route action
- tool name
- original question
- retrieval source labels
- top_k
- whether LLM was called
- model name
- answer preview
- error type
- token usage
- latency

当前可以先记录 sources 和 answer preview。

### 6. 应该新增哪些测试？

建议新增：

```text
test_route_to_answer_docs_with_llm
test_answer_docs_with_llm_tool
test_agent_answers_docs_with_llm
test_agent_llm_rag_handles_no_context
test_trace_includes_llm_rag_tool
```

默认测试仍不请求真实 DeepSeek，可以用 client injection 或边界 stub 验证 Agent 工具接线。

真实请求继续用 CLI smoke test。

### 7. 应该新增哪些 eval case？

建议新增：

```text
llm-rag-answer-mcp
```

输入：

```text
Answer with local docs and DeepSeek RAG: What does MCP mean in this project?
```

期望：

```text
route = use_tool
tool = answer_docs_with_llm
required terms = Answer, Sources, MCP
```

也可以新增：

```text
llm-rag-no-context
```

输入：

```text
Answer with local docs and DeepSeek RAG: zzzz-not-existing-keyword
```

期望：

```text
local context is insufficient
```

### 8. 应该新增哪些验证命令？

建议保留：

```bash
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.rag_llm_demo --question "What does MCP mean in this project?"
```

v10 新增后应增加：

```bash
python -m cli.main --input "Answer with local docs and DeepSeek RAG: What does MCP mean in this project?" --trace
```

## 本阶段最低通过标准

完成 v9 后，应该能讲清：

1. v9 和原始 RAG 的区别。
2. `rag/llm_qa.py` 的主流程。
3. 为什么无 context 时不调用 LLM。
4. source label 在专业 RAG 中的作用。
5. 为什么默认测试不请求真实 DeepSeek。
6. 下一阶段为什么要接回 `WorkspaceAgent`。
