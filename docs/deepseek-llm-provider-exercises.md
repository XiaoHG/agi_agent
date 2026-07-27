# DeepSeek 真实 LLM 接入阶段练习答案

本文档用于复盘 v8：DeepSeek 真实 LLM 接入阶段。

本阶段目标不是学习 FakeLLM 或模拟调用，而是理解真实 LLM 如何进入 Agent 工程主链路，并为后续专业 RAG、MCP、Skills、LangGraph 开发打基础。

## 练习 1：运行真实 LLM 推理

运行命令：

```bash
python -m cli.llm_demo --input "Explain in two sentences why agents need tools."
```

### 1. 这个命令最终调用了哪个文件里的哪个类？

调用链路最终进入：

```text
agent/llm.py
DeepSeekLLMClient
```

CLI 入口在：

```text
cli/llm_demo.py
```

核心调用是：

```python
client = DeepSeekLLMClient()
response = client.complete(args.input, system_prompt=args.system)
```

### 2. API Key 是从哪里读取的？

API Key 从环境变量读取：

```text
DEEPSEEK_API_KEY
```

对应代码：

```python
api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
```

### 3. 默认模型名是什么？

默认模型名是：

```text
deepseek-v4-pro
```

对应常量：

```python
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-pro"
```

### 4. DeepSeek API endpoint 是什么？

默认 endpoint 是：

```text
https://api.deepseek.com/chat/completions
```

对应常量：

```python
DEFAULT_DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
```

### 5. 如果 API Key 缺失，代码会抛出什么异常？

会抛出：

```text
LLMError
```

错误信息：

```text
Missing DEEPSEEK_API_KEY environment variable.
```

## 练习 2：阅读 `agent/llm.py`

### 1. `LLMMessage.to_dict()` 为什么要返回 `{"role": ..., "content": ...}`？

因为 DeepSeek API 使用 OpenAI-compatible Chat Completions 格式。

Chat message 的标准结构是：

```json
{
  "role": "user",
  "content": "Explain agents."
}
```

这样 `LLMMessage` 可以转换成 DeepSeek API 能直接接收的消息结构。

### 2. `LLMResponse.raw` 为什么要保留原始响应？

保留原始响应是为了后续调试和工程扩展。

后续可以从 `raw` 中提取：

- token usage
- finish reason
- request id
- reasoning metadata
- provider-specific 字段

如果只保留最终文本，后续做 trace、成本统计、错误定位会缺少证据。

### 3. `DeepSeekConfig.from_env()` 的职责是什么？

职责是从环境变量构建 DeepSeek 运行配置。

它负责读取：

```text
DEEPSEEK_API_KEY
DEEPSEEK_MODEL
DEEPSEEK_API_URL
DEEPSEEK_TEMPERATURE
DEEPSEEK_MAX_TOKENS
DEEPSEEK_TIMEOUT_SECONDS
```

这样业务代码不需要直接关心环境变量。

### 4. 为什么 API Key 不能写进代码或配置文件？

因为 API Key 是敏感凭证。

如果写进代码或提交到仓库，会导致：

- 密钥泄露
- 账户被滥用
- 产生非预期费用
- 仓库安全风险

正确方式是：

```text
真实密钥只存在本地环境变量或安全密钥管理系统中
仓库只提交 .env.example 模板
```

### 5. `DeepSeekLLMClient.complete()` 和 `DeepSeekLLMClient.chat()` 有什么区别？

`complete()` 是单轮便捷接口。

它接收：

```python
user_input: str
system_prompt: str | None
```

然后内部构造 messages，再调用 `chat()`。

`chat()` 是更底层、更通用的接口。

它接收：

```python
list[LLMMessage]
```

适合后续多轮对话、RAG context、tool result 综合等场景。

关系是：

```text
complete() -> 构造 messages -> chat()
```

## 练习 3：真实 LLM 调用流程

完整流程：

```text
python -m cli.llm_demo --input "..."
  -> cli/llm_demo.py main()
  -> argparse 解析 --input 和 --system
  -> DeepSeekLLMClient()
  -> DeepSeekConfig.from_env()
  -> 读取 DEEPSEEK_API_KEY / model / api_url / temperature / max_tokens / timeout
  -> DeepSeekLLMClient.complete()
  -> 构造 LLMMessage(role="system", content=...)
  -> 构造 LLMMessage(role="user", content=...)
  -> DeepSeekLLMClient.chat()
  -> LLMMessage.to_dict()
  -> 构造 OpenAI-compatible JSON payload
  -> DeepSeekLLMClient._post_json()
  -> HTTP POST https://api.deepseek.com/chat/completions
  -> DeepSeek API 返回 JSON
  -> DeepSeekLLMClient._extract_content()
  -> 读取 choices[0].message.content
  -> 返回 LLMResponse
  -> cli/llm_demo.py print(response.content)
  -> 返回 exit code 0
```

## 练习 4：理解错误处理

### 1. API Key 缺失时，在哪里报错？

在：

```python
DeepSeekConfig.from_env()
```

具体逻辑：

```python
if not api_key:
    raise LLMError("Missing DEEPSEEK_API_KEY environment variable.")
```

### 2. DeepSeek 返回 HTTP 错误时，在哪里处理？

在：

```python
DeepSeekLLMClient._post_json()
```

处理：

```python
except HTTPError as error:
    error_body = error.read().decode("utf-8", errors="replace")
    raise LLMError(f"DeepSeek API HTTP {error.code}: {error_body}") from error
```

### 3. 网络错误在哪里处理？

同样在：

```python
DeepSeekLLMClient._post_json()
```

处理：

```python
except URLError as error:
    raise LLMError(f"DeepSeek API network error: {error.reason}") from error
```

### 4. 返回 JSON 格式异常在哪里处理？

在：

```python
DeepSeekLLMClient._post_json()
```

处理：

```python
except json.JSONDecodeError as error:
    raise LLMError("DeepSeek API returned invalid JSON.") from error
```

### 5. 返回结构没有 `choices` 时，在哪里处理？

在：

```python
DeepSeekLLMClient._extract_content()
```

处理：

```python
choices = raw.get("choices")
if not isinstance(choices, list) or not choices:
    raise LLMError("DeepSeek API response does not contain choices.")
```

### 6. CLI 为什么返回 `1`？

因为真实 LLM 请求失败时，CLI 应该给自动化系统一个失败信号。

对应代码：

```python
except LLMError as error:
    print(f"LLM request failed: {error}")
    return 1
```

工程约定：

```text
exit code 0 = 成功
exit code 非 0 = 失败
```

## 练习 5：为什么测试不调用真实网络

### 1. `test_message_exports_openai_compatible_shape` 验证什么？

验证 `LLMMessage.to_dict()` 能输出 DeepSeek / OpenAI-compatible 的标准消息格式：

```python
{"role": "user", "content": "Explain agents."}
```

### 2. `test_extract_content_from_response` 验证什么？

验证 `_extract_content()` 能从标准 API 响应中提取：

```text
choices[0].message.content
```

### 3. `test_extract_content_rejects_invalid_response` 验证什么？

验证响应结构异常时会抛出 `LLMError`，而不是静默失败或返回错误内容。

### 4. 为什么单元测试不直接请求 DeepSeek？

原因：

- 网络请求不稳定
- API 调用有成本
- API Key 不应该成为默认测试依赖
- 模型输出具有不确定性
- 默认测试应该快速、稳定、可重复

这不是 FakeLLM 路线，而是专业测试分层：

```text
单元测试验证本地边界逻辑
真实 LLM CLI 验证真实模型调用
后续集成测试可单独标记和运行
```

### 5. 真实请求应该用什么命令验证？

使用：

```bash
python -m cli.llm_demo --input "Explain in two sentences why agents need tools."
```

## 练习 6：手动验证命令

### 1. `python -m unittest discover -s tests -v` 验证什么？

验证项目所有默认自动化测试。

覆盖范围包括：

- Agent 路由
- tools
- workflow
- RAG
- MCP
- skills
- subagent
- eval runner
- project assistant
- DeepSeek LLM 边界逻辑

### 2. `python -m cli.eval_runner` 验证什么？

验证当前 Agent 行为是否符合固定 eval case。

它检查：

- route 是否符合预期
- tool 是否符合预期
- answer 是否包含必要关键词

### 3. `python -m cli.llm_demo --input "Explain the difference between RAG and tool calling in agent systems."` 验证什么？

验证真实 DeepSeek LLM 推理链路。

它检查：

- 环境变量是否正确
- DeepSeek endpoint 是否可访问
- 模型名是否可用
- HTTP 请求是否成功
- 响应解析是否正常
- CLI 是否能输出真实模型回答

### 4. 为什么真实 LLM demo 不适合放进默认单元测试？

因为它依赖外部系统。

默认单元测试应该满足：

```text
快速
稳定
无网络依赖
无费用
结果可重复
```

真实 LLM 请求更适合：

```text
手动验证
集成测试
CI 中的可选测试
上线前 smoke test
```

## 练习 7：当前 LLM 接入的限制

### 限制 1

限制：`WorkspaceAgent` 还没有默认使用真实 LLM。

原因：当前真实 LLM 只接入了 `cli.llm_demo.py`，主 Agent loop 仍然以规则路由和固定回答为主。

后续改进：让 `WorkspaceAgent` 支持 LLM-driven direct answer 或 LLM-driven routing。

### 限制 2

限制：RAG 检索结果还没有交给 LLM 生成最终答案。

原因：当前 `search_docs` 仍然返回检索 chunk，而不是基于上下文生成 grounded answer。

后续改进：新增 DeepSeek-powered RAG answer chain。

### 限制 3

限制：MCP tool result 还没有进入 LLM 综合。

原因：当前 MCP 工具结果直接返回，没有交给 LLM 做解释、总结或下一步决策。

后续改进：让 LLM 接收 tool result，并生成面向用户的综合回答。

### 限制 4

限制：Skills 还没有成为 LLM 可选择的专业能力。

原因：当前 `skills/catalog.py` 是规则选择，不是 LLM 根据任务和 skill metadata 进行选择。

后续改进：定义 skill schema，让 LLM 根据 task 和 skill descriptions 选择合适 skill。

### 限制 5

限制：还没有 LangChain / LangGraph。

原因：当前只完成真实 LLM client，尚未接入专业编排框架。

后续改进：先做 RAG + LLM，再做 LangChain tool adapter，最后引入 LangGraph workflow。

### 限制 6

限制：不支持流式输出。

原因：当前 `_post_json()` 使用一次性 HTTP 响应读取。

后续改进：增加 streaming endpoint 处理，支持 token-by-token 输出。

### 限制 7

限制：没有重试机制。

原因：当前网络错误或 HTTP 错误直接失败。

后续改进：增加有限重试、退避策略和可恢复错误分类。

### 限制 8

限制：没有 token usage 和成本记录。

原因：虽然保留了 `raw`，但还没有解析 usage 字段。

后续改进：在 `LLMResponse` 中增加 usage 字段，并记录到 trace 或 logs。

## 练习 8：设计下一阶段 v9

下一阶段建议：

```text
v9：DeepSeek 驱动的专业 RAG
```

### 1. 为什么下一阶段应该先做 RAG + LLM，而不是 LangGraph？

因为 LangGraph 是编排框架，解决的是流程控制问题。

但当前项目最关键的缺口是：

```text
检索结果还没有进入真实 LLM 推理
```

如果现在直接上 LangGraph，只是把已有规则流程画成图，智能能力并没有提升。

更合理的顺序是：

```text
真实 LLM client
  -> RAG + LLM
  -> tool schema
  -> LangGraph workflow
```

### 2. 当前 `rag/` 模块已经提供了哪些基础能力？

当前已有：

- 文档加载
- 文档切分
- 本地检索
- 简单问题回答封装
- RAG demo CLI

对应目录：

```text
rag/documents.py
rag/chunking.py
rag/retrieval.py
rag/qa.py
cli/rag_demo.py
tests/test_rag.py
```

### 3. 要让 RAG 变成专业 RAG，还缺什么？

缺少：

- 将检索 context 注入 prompt
- 调用 DeepSeek 生成 grounded answer
- 返回引用来源
- 控制上下文长度
- 防止无依据回答
- 对无检索结果进行明确处理
- RAG 专用测试和验证命令

### 4. 应该新增哪些文件？

建议新增：

```text
rag/llm_qa.py
cli/rag_llm_demo.py
tests/test_rag_llm.py
versions/deepseek-rag_v9.md
```

### 5. 应该修改哪些文件？

建议修改：

```text
rag/__init__.py
README.md
docs/current-learning-state.md
```

后续可选修改：

```text
agent/tools.py
agent/core.py
```

用于让 `WorkspaceAgent` 可以调用 LLM-grounded RAG。

### 6. 应该新增哪些测试？

建议新增：

```text
test_build_grounded_rag_prompt
test_rag_llm_returns_no_context_without_results
test_rag_llm_preserves_sources
test_rag_llm_demo_cli_requires_question
```

默认测试仍不直接请求真实 DeepSeek，真实请求用 CLI smoke test 验证。

### 7. 应该新增哪些验证命令？

建议新增：

```bash
python -m cli.rag_llm_demo --question "What does MCP mean in this project?"
```

继续保留：

```bash
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.llm_demo --input "Explain why agents need tools."
```

## 本阶段最低通过标准

完成本阶段后，你应该能讲清：

1. `cli.llm_demo` 如何调用 DeepSeek。
2. `agent/llm.py` 中每个核心类的职责。
3. API Key 为什么必须从环境变量读取。
4. 为什么真实 LLM 请求不进默认单元测试。
5. 当前 LLM 接入还没有真正进入 Agent/RAG/MCP/Skills 主链路。
6. 下一阶段为什么应该做 DeepSeek 驱动的 RAG。
