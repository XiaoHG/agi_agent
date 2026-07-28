# LangChain Tool Adapter 阶段练习答案

本文档用于复盘 v11：LangChain Tool Adapter 阶段。

本阶段目标是理解如何把项目内部工具包装成专业框架可识别、可调用的 LangChain `StructuredTool`。

核心链路：

```text
agent/tools.py core tools
  -> integrations/langchain_tools.py adapter
  -> langchain_core.tools.StructuredTool
  -> future LangGraph node / tool calling agent
```

## 练习 1：运行 LangChain Tools Demo

运行命令：

```bash
python -m cli.langchain_tools_demo
```

### 1. 输出了多少个 LangChain tools？

当前输出 11 个 LangChain tools。

分别是：

```text
read_workspace_file
list_workspace_directory
count_workspace_file_lines
search_workspace_docs
answer_workspace_docs_with_llm
list_workspace_mcp_tools
summarize_workspace_with_mcp
list_workspace_skills
plan_workspace_skill
list_workspace_subagents
plan_workspace_subagents
```

### 2. 哪些工具对应文件操作？

对应文件和目录操作的工具是：

```text
read_workspace_file
list_workspace_directory
count_workspace_file_lines
```

它们分别对应 core tools：

```text
read_file
list_dir
count_lines
```

### 3. 哪些工具对应 RAG？

对应 RAG 的工具是：

```text
search_workspace_docs
answer_workspace_docs_with_llm
```

区别：

```text
search_workspace_docs = deterministic retrieval，只返回检索上下文
answer_workspace_docs_with_llm = DeepSeek-grounded RAG，返回 LLM 综合答案和 sources
```

### 4. 哪些工具对应 MCP？

对应 MCP 的工具是：

```text
list_workspace_mcp_tools
summarize_workspace_with_mcp
```

它们分别对应：

```text
list_mcp_server_tools
mcp_workspace_summary
```

### 5. 哪些工具对应 Skills / Subagents？

对应 Skills 的工具：

```text
list_workspace_skills
plan_workspace_skill
```

对应 Subagents 的工具：

```text
list_workspace_subagents
plan_workspace_subagents
```

### 6. 哪个工具可能触发真实 DeepSeek 网络请求？

可能触发真实 DeepSeek 网络请求的是：

```text
answer_workspace_docs_with_llm
```

因为它内部调用：

```text
answer_docs_with_llm
  -> answer_question_with_llm
  -> DeepSeekLLMClient.chat()
```

## 练习 2：阅读 `integrations/langchain_tools.py`

### 1. `PathInput` 的作用是什么？

`PathInput` 是文件/目录类工具的输入 schema。

它定义：

```python
path: str = Field(default=".", description="Workspace-relative file or directory path.")
```

适用于：

```text
read_workspace_file
list_workspace_directory
count_workspace_file_lines
```

它告诉 LangChain：

```text
这个工具需要一个 workspace-relative path 参数
```

### 2. `QuestionInput` 的作用是什么？

`QuestionInput` 是自然语言问题类工具的输入 schema。

它定义：

```python
question: str = Field(description="Natural-language question or task.")
```

适用于：

```text
search_workspace_docs
answer_workspace_docs_with_llm
plan_workspace_skill
plan_workspace_subagents
```

它告诉 LangChain：

```text
这个工具需要一个自然语言 question/task 参数
```

### 3. `EmptyInput` 的作用是什么？

`EmptyInput` 是无参数工具的输入 schema。

适用于：

```text
list_workspace_mcp_tools
summarize_workspace_with_mcp
list_workspace_skills
list_workspace_subagents
```

这类工具不需要用户输入参数，但 LangChain 仍然需要一个 schema 来表达工具输入结构。

### 4. 为什么 `workspace_root` 要在 adapter 层 resolve？

因为 adapter 层负责把外部框架调用转换成内部工具调用。

在这里统一执行：

```python
root = Path(workspace_root).resolve()
```

好处：

- 所有工具共享同一个绝对 workspace root
- 避免每个 wrapper 重复解析路径
- 保持工具行为一致
- 防止 CLI 工作目录变化导致路径不稳定

### 5. 为什么每个内部工具外面都包了一层函数，例如 `read_workspace_file()`？

因为 LangChain tool 需要一个明确的 callable。

内部 core tool 的签名通常是：

```python
read_file(root, path)
```

但 LangChain tool 更适合暴露成：

```python
read_workspace_file(path)
```

wrapper 的作用是：

```text
绑定 workspace root
隐藏内部 ToolResult
返回 LangChain 需要的字符串
提供清晰 docstring
```

例如：

```python
def read_workspace_file(path: str = ".") -> str:
    return read_file(root, path).output
```

## 练习 3：理解 core tools 和 adapter 的边界

### 1. `agent/tools.py` 的职责是什么？

`agent/tools.py` 是 core tool implementation。

它负责：

- 文件读取
- 目录列表
- 行数统计
- deterministic RAG
- DeepSeek-grounded RAG
- MCP adapter 调用
- Skills
- Subagents

它不应该依赖 LangChain、LangGraph 或其他框架。

### 2. `integrations/langchain_tools.py` 的职责是什么？

`integrations/langchain_tools.py` 是 framework adapter。

它负责：

```text
把 agent/tools.py 中的 core tools 包装成 LangChain StructuredTool
```

它处理：

- LangChain tool name
- description
- args_schema
- metadata
- wrapper function

### 3. 为什么不要把 LangChain 代码直接写进 `agent/tools.py`？

因为会污染 core layer。

如果把 LangChain 写进 `agent/tools.py`，会导致：

- core tools 依赖外部框架
- 测试变复杂
- 后续更换框架困难
- 工具实现和框架包装混在一起
- LangGraph、MCP、CLI 都可能被迫依赖 LangChain

正确分层：

```text
agent/tools.py = framework-independent core tools
integrations/langchain_tools.py = LangChain-specific adapter
```

### 4. 如果未来换成其他框架，这种分层有什么好处？

如果未来换成其他框架，例如 AutoGen、CrewAI、Semantic Kernel 或自定义 LangGraph node，可以继续复用：

```text
agent/tools.py
```

只需要新增：

```text
integrations/autogen_tools.py
integrations/semantic_kernel_tools.py
```

这种架构降低了框架迁移成本。

### 5. 当前哪些工具是框架无关的？哪些代码是 LangChain 专属的？

框架无关：

```text
agent/tools.py
rag/
mcp/
skills/
subagent/
agent/core.py
```

LangChain 专属：

```text
integrations/langchain_tools.py
tests/test_langchain_tools.py
cli/langchain_tools_demo.py
```

## 练习 4：理解 `StructuredTool`

示例：

```python
StructuredTool.from_function(
    func=read_workspace_file,
    name="read_workspace_file",
    description="Read a small text file from the workspace.",
    args_schema=PathInput,
)
```

### 1. `func` 是什么？

`func` 是工具真正执行时调用的 Python 函数。

在这个例子中：

```python
func=read_workspace_file
```

当 LangChain 调用该 tool 时，最终会执行：

```python
read_workspace_file(path)
```

### 2. `name` 是什么？为什么要用 snake_case？

`name` 是工具对外暴露的唯一名称。

模型或框架会根据这个名称识别和调用工具。

使用 snake_case 的原因：

- 清晰稳定
- 符合 Python 命名习惯
- 避免空格和特殊字符
- 方便模型选择和日志记录
- 符合 LangChain 工具命名建议

### 3. `description` 给谁看？

`description` 主要给：

- LLM
- tool planner
- agent executor
- 开发者

它帮助模型判断：

```text
什么时候应该调用这个工具
```

如果 description 不清楚，模型可能选错工具。

### 4. `args_schema` 的作用是什么？

`args_schema` 定义工具输入参数。

它告诉 LangChain：

```text
这个工具需要哪些参数
参数类型是什么
参数说明是什么
是否有默认值
```

例如 `PathInput` 表示工具需要：

```text
path: str
```

### 5. 如果没有 `args_schema`，会有什么问题？

如果没有明确 schema：

- LLM 不知道该传哪些参数
- 参数名可能不稳定
- 工具调用容易失败
- 自动生成 tool schema 的结果不可控
- 测试和调试更困难

专业 Agent 项目里，工具 schema 是很重要的工程边界。

## 练习 5：理解网络依赖 metadata

重点代码：

```python
metadata={"requires_network": True, "requires_api_key": "DEEPSEEK_API_KEY"}
```

### 1. 哪个工具设置了这个 metadata？

设置该 metadata 的工具是：

```text
answer_workspace_docs_with_llm
```

### 2. 为什么只有这个工具需要标记？

因为它可能调用真实 DeepSeek API。

其他工具大多是本地工具：

- 文件读取
- 目录列表
- 本地检索
- 本地 MCP adapter
- 本地 skills/subagents

这些默认不需要外部网络。

### 3. 这个 metadata 对未来 LangGraph 或 Agent planner 有什么价值？

metadata 可以帮助 planner 做决策。

例如：

- 当前环境没有 API Key，就不要选择该工具
- 当前任务要求离线运行，就不要选择 requires_network 工具
- 当前预算有限，优先使用本地 deterministic tools
- 需要真实总结时，再选择 LLM tool

这为后续 tool selection、权限控制、成本控制打基础。

### 4. 默认测试为什么只检查 metadata，而不直接 invoke 这个工具？

因为直接 invoke 可能触发真实 DeepSeek 请求。

默认测试应该：

```text
快速
稳定
不依赖网络
不消耗 API 费用
不依赖 API Key
```

所以测试只验证：

```python
metadata["requires_network"] == True
metadata["requires_api_key"] == "DEEPSEEK_API_KEY"
```

真实调用应该通过单独 smoke test 验证。

### 5. 如果未来要让 planner 自动选择工具，这些 metadata 可以如何使用？

planner 可以根据 metadata 做过滤。

例如：

```text
如果 no_network=True，则排除 requires_network 工具
如果 DEEPSEEK_API_KEY 不存在，则排除需要该 key 的工具
如果任务只是查原始 context，优先 search_workspace_docs
如果任务需要最终自然语言答案，选择 answer_workspace_docs_with_llm
```

## 练习 6：理解测试文件

阅读：

```text
tests/test_langchain_tools.py
```

### 1. `test_build_langchain_tools_returns_structured_tools` 验证什么？

验证 `build_langchain_tools()` 返回的是 LangChain 的真实 `StructuredTool` 对象。

测试：

```python
self.assertTrue(all(isinstance(tool, StructuredTool) for tool in tools))
```

说明当前不是自定义假 schema，而是真实 LangChain adapter。

### 2. `test_tool_specs_include_expected_tools` 验证什么？

验证工具集合中包含关键工具名称。

例如：

```text
read_workspace_file
search_workspace_docs
answer_workspace_docs_with_llm
plan_workspace_subagents
```

这保证 adapter 没有漏掉关键工具。

### 3. `test_read_file_tool_invokes_core_tool` 为什么使用临时目录？

因为测试需要稳定、隔离、可控。

它创建临时目录：

```python
with tempfile.TemporaryDirectory() as tmp:
```

然后写入：

```python
README.md
```

这样不依赖真实仓库文件内容，也不会被后续文档变化影响。

### 4. `test_llm_rag_tool_marks_network_dependency` 验证什么？

验证 `answer_workspace_docs_with_llm` 被正确标记为网络依赖工具：

```python
metadata["requires_network"] == True
metadata["requires_api_key"] == "DEEPSEEK_API_KEY"
```

这对后续 planner 和 workflow 很重要。

### 5. `test_no_argument_tool_invokes_without_arguments` 验证什么？

验证无参数工具可以通过 LangChain `.invoke({})` 调用。

当前测试使用：

```python
tools["list_workspace_skills"].invoke({})
```

并检查输出包含：

```text
Available skills
```

### 6. 这些测试为什么不调用真实 DeepSeek？

因为默认测试不应该依赖真实网络。

特别是：

```text
answer_workspace_docs_with_llm
```

可能触发 DeepSeek API。

所以默认测试只验证 metadata，不 invoke 该工具。

## 练习 7：手动调用某个 LangChain Tool

运行：

```bash
python - <<'PY'
from pathlib import Path
from integrations import build_langchain_tools

tools = {tool.name: tool for tool in build_langchain_tools(Path("."))}
output = tools["read_workspace_file"].invoke({"path": "README.md"})
print(output[:500])
PY
```

### 1. `.invoke()` 的输入是什么格式？

输入是一个字典：

```python
{"path": "README.md"}
```

它对应 `PathInput`：

```python
path: str
```

### 2. 输出是不是来自 `agent/tools.py` 的 `read_file()`？

是。

调用链路：

```text
StructuredTool.invoke()
  -> read_workspace_file(path)
  -> read_file(root, path)
  -> ToolResult.output
```

所以输出中会有：

```text
[read_file] README.md
```

### 3. 如果把 path 改成不存在的文件，会发生什么？

core tool 会抛出：

```text
ToolError
```

例如：

```text
File does not exist: not-exist.md
```

LangChain tool 调用会把这个异常暴露出来，后续 LangGraph 或 Agent executor 需要处理该错误。

### 4. 这说明 LangChain tool adapter 和 core tool 是什么关系？

说明 adapter 不是重新实现工具。

它只是把 core tool 包装成框架可调用形式。

关系是：

```text
LangChain StructuredTool = external framework interface
agent/tools.py core tool = actual implementation
```

## 练习 8：当前 v11 的限制

### 限制 1

限制：还没有 LangGraph。

原因：当前只完成 tool adapter，还没有状态图和节点编排。

后续改进：新增 LangGraph workflow，把 LangChain tools 放进 graph node。

### 限制 2

限制：还没有 LangChain ChatModel。

原因：DeepSeek 当前通过自定义 `DeepSeekLLMClient` 调用，没有封装成 LangChain ChatModel。

后续改进：新增 DeepSeek ChatModel adapter 或使用兼容 OpenAI 的 LangChain provider。

### 限制 3

限制：还没有 tool calling agent。

原因：当前只是工具列表，没有让 LLM 自动选择工具。

后续改进：结合 ChatModel 和 tools，实现 tool selection / tool calling。

### 限制 4

限制：tool metadata 还没有统一规范。

原因：当前只有 `answer_workspace_docs_with_llm` 标记了 `requires_network` 和 `requires_api_key`。

后续改进：为所有工具建立统一 metadata，例如：

```text
category
risk_level
requires_network
requires_api_key
side_effects
cost_level
```

### 限制 5

限制：不支持 async tools。

原因：当前全部使用同步函数。

后续改进：为网络型工具增加 async coroutine，支持 LangChain / LangGraph 异步执行。

### 限制 6

限制：没有统一 tool error schema。

原因：当前 core tools 抛出 `ToolError`，但 adapter 没有结构化错误输出。

后续改进：定义统一错误格式，例如：

```text
tool_name
error_type
message
retryable
```

### 限制 7

限制：没有 permission / risk 分类。

原因：当前工具都被同等暴露，没有区分只读、网络、潜在副作用。

后续改进：在 metadata 中增加：

```text
permission_scope
risk_level
side_effects
```

### 限制 8

限制：没有工具级 eval。

原因：当前 eval 主要验证 `WorkspaceAgent` 行为，还没有针对 LangChain tool adapter 的 eval cases。

后续改进：新增 tool-level eval 或 adapter smoke tests。

## 练习 9：设计下一阶段 v12

下一阶段建议：

```text
v12：LangGraph Workflow
```

### 1. 为什么 v11 之后适合进入 LangGraph？

因为 v11 已经把 core tools 包装成 LangChain `StructuredTool`。

LangGraph 可以基于这些 tools 构建状态图。

合理顺序是：

```text
core tools
  -> LangChain tool adapter
  -> LangGraph workflow
```

现在工具层已经准备好，可以进入 graph 编排。

### 2. LangGraph 应该先编排哪个最小流程？

建议先编排最小 RAG workflow：

```text
receive question
  -> route
  -> retrieve / answer docs with LLM
  -> final answer
```

或者更具体：

```text
question -> answer_workspace_docs_with_llm -> final response
```

先不要做复杂多分支。

### 3. 当前哪些 LangChain tools 可以放进 graph node？

可以放：

```text
search_workspace_docs
answer_workspace_docs_with_llm
read_workspace_file
list_workspace_directory
plan_workspace_subagents
```

最小 v12 推荐先用：

```text
answer_workspace_docs_with_llm
```

### 4. graph state 至少应该包含哪些字段？

至少包含：

```text
question
selected_tool
tool_output
answer
error
steps
```

如果要更专业，可以继续增加：

```text
sources
trace_id
model
metadata
```

### 5. 应该新增哪些文件？

建议新增：

```text
integrations/langgraph_workflow.py
cli/langgraph_demo.py
tests/test_langgraph_workflow.py
versions/langgraph-workflow_v12.md
```

### 6. 应该修改哪些文件？

建议修改：

```text
pyproject.toml
README.md
docs/current-learning-state.md
```

如果引入真实 LangGraph，需要增加依赖：

```text
langgraph
```

### 7. 应该新增哪些测试？

建议新增：

```text
test_build_langgraph_workflow
test_langgraph_state_contains_question
test_langgraph_invokes_expected_tool
test_langgraph_returns_final_answer
test_langgraph_handles_tool_error
```

### 8. 应该新增哪些验证命令？

建议新增：

```bash
python -m cli.langgraph_demo --question "What does MCP mean in this project?"
```

继续保留：

```bash
python -m unittest discover -s tests -v
python -m cli.langchain_tools_demo
python -m cli.eval_runner
```

## 本阶段最低通过标准

完成 v11 后，你应该能讲清：

1. `agent/tools.py` 和 `integrations/langchain_tools.py` 的边界。
2. `StructuredTool.from_function()` 的基本作用。
3. `args_schema` 为什么重要。
4. 为什么 DeepSeek RAG tool 要标记 `requires_network` 和 `requires_api_key`。
5. 为什么 v11 还不是 LangGraph，只是为 LangGraph 做工具准备。
6. 下一阶段为什么进入 LangGraph。
