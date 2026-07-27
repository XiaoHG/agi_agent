# DeepSeek 真实 LLM 接入 v8

版本：v8

日期：2026-07-27

## 本次目标

本次路线调整为直接接入真实 LLM 推理，不再使用 FakeLLM 作为主线。

当前使用 DeepSeek V4 Pro，目标是让后续 RAG、MCP、Skills、LangGraph 等专业 Agent 能力都围绕真实 LLM 调用链路继续开发。

## 新增文件

### `agent/llm.py`

职责：

- 定义 `LLMMessage`
- 定义 `LLMResponse`
- 定义 `DeepSeekConfig`
- 定义 `DeepSeekLLMClient`
- 通过 OpenAI-compatible HTTP API 调用真实 DeepSeek 模型
- 统一处理 API Key、模型名、endpoint、temperature、max tokens 和 timeout
- 将 DeepSeek 原始响应转换为项目内部统一响应对象

设计重点：

- API Key 只从环境变量读取，不写入仓库。
- 默认模型为 `deepseek-v4-pro`。
- 使用真实网络请求，不使用 FakeLLM。
- 当前使用 Python 标准库 HTTP 请求，避免在学习阶段引入额外 SDK 依赖。

### `cli/llm_demo.py`

职责：

- 提供真实 LLM 推理命令行入口。
- 从环境变量读取 DeepSeek 配置。
- 接收用户输入并调用真实 DeepSeek 模型。
- 请求失败时返回非 0 exit code。

运行示例：

```bash
python -m cli.llm_demo --input "Explain why agents need tools."
```

### `tests/test_llm.py`

职责：

- 验证 message 是否符合 OpenAI-compatible shape。
- 验证 DeepSeek 响应解析逻辑。
- 验证异常响应会被转换成 `LLMError`。

说明：

测试不调用真实网络。原因不是使用 FakeLLM，而是单元测试只验证边界逻辑。真实推理通过 `cli/llm_demo.py` 手动或集成验证。

## 修改文件

### `agent/__init__.py`

新增导出：

- `DeepSeekConfig`
- `DeepSeekLLMClient`
- `LLMError`
- `LLMMessage`
- `LLMResponse`

### `configs/.env.example`

新增 DeepSeek 配置模板：

```text
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-v4-pro
DEEPSEEK_API_URL=https://api.deepseek.com/chat/completions
DEEPSEEK_TEMPERATURE=0.2
DEEPSEEK_MAX_TOKENS=1000
DEEPSEEK_TIMEOUT_SECONDS=60
```

## 新增交互流程

```text
python -m cli.llm_demo --input "..."
  -> DeepSeekLLMClient.from environment
  -> build OpenAI-compatible messages
  -> POST DeepSeek chat completions endpoint
  -> parse choices[0].message.content
  -> print real LLM answer
```

## 当前限制

- `WorkspaceAgent` 还没有默认改为 LLM 路由。
- RAG 还没有把检索上下文交给 LLM 生成最终答案。
- MCP tool result 还没有交给 LLM 做自然语言综合。
- Skills 还没有成为 LLM 可选择的结构化能力。
- 当前还没有 LangChain / LangGraph 适配层。

## 下一步建议

下一步进入专业 Agent 框架栈：

1. 让 RAG 检索结果进入 DeepSeek LLM，生成真实回答。
2. 把本地 tools 包装成专业 tool schema。
3. 再接 LangGraph，用图编排替代固定流程。
4. 将 MCP server/client 向标准协议实现推进。
5. 将 skills 从静态 catalog 升级为可加载、可选择、可执行的专业 skill system。
