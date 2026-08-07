# LLM Tool Calling 阶段练习答案

对应版本：v15  
主题：LLM tool calling / tool schema  
用途：阶段复盘与下一阶段恢复学习

## 练习 1：读主链路

### 1. 用户输入 `Use tool calling to read README.md.` 后，最先由哪个函数识别成 `tool_call`？

最先由 `agent/router.py` 中的 `route_intent()` 处理。

具体流程是：

```text
route_intent()
-> _looks_like_tool_calling_request()
-> ToolRoute(action="tool_call", tool_name="llm_tool_selector", ...)
```

`_looks_like_tool_calling_request()` 会识别 `tool calling`、`tool call`、`select a tool`、`choose a tool` 等关键词。

### 2. `WorkspaceAgent.run()` 中，`tool_call` 分支大致做了哪 4 件事？

大致分成 4 步：

1. 提取真正要交给模型判断的任务文本。
2. 调用 `_select_tool_call()`，让 LLM 根据 tool schema 选择动作和工具。
3. 根据模型返回的 `ToolCallSelection` 执行对应分支：
   - `use_tool`：调用本地工具
   - `answer_directly`：直接回答
   - `ask_clarification`：请求补充信息
4. 写入 trace，并生成最终 `run.answer`。

### 3. 为什么 `WorkspaceAgent` 里要支持注入 `llm_client`？

因为测试不能依赖真实网络和真实 API Key。

支持注入 `llm_client` 后，测试可以传入 fake client，让模型输出固定 JSON。这样可以稳定验证：

- tool calling 分支是否被执行
- JSON 是否被正确解析
- 工具是否被正确调用
- trace 是否正确记录

这也是 Agent 工程中非常重要的边界：真实 LLM 可以参与生产运行，但测试应该尽量可重复。

### 4. `run.tool_call` 和 `run.tool_result` 分别代表什么？

`run.tool_call` 代表模型的工具选择结果。

它回答的是：

```text
模型决定做什么？
模型选择哪个工具？
模型给工具传什么参数？
模型为什么这样选？
```

`run.tool_result` 代表本地工具真正执行后的结果。

它回答的是：

```text
工具是否真的执行了？
执行的是哪个工具？
工具返回了什么内容？
```

两者不能混在一起。模型选对工具，不代表工具一定执行成功。

## 练习 2：理解 tool schema

### 1. `ToolArgumentSpec` 负责描述什么？

`ToolArgumentSpec` 负责描述工具的单个参数。

它包含：

- 参数名
- 参数类型
- 参数说明
- 是否必填

例如 `read_file` 的 `path` 参数就是一个 `ToolArgumentSpec`。

### 2. `ToolSpec` 负责描述什么？

`ToolSpec` 负责描述一个完整工具。

它包含：

- 工具名称
- 工具用途
- 工具参数列表

它是给 LLM 看的工具目录，也是后续做工具选择、工具校验、工具评估的基础结构。

### 3. `ToolSpec.to_prompt_block()` 的作用是什么？

它把工具 schema 渲染成模型容易理解的 prompt 文本。

例如一个工具会被渲染成类似：

```text
- read_file: Read a small text file from the workspace root.
  - path (string, required): Workspace-relative file path.
```

这样 LLM 才知道当前有哪些工具、每个工具适合做什么、应该传什么参数。

### 4. 为什么不直接把 Python 函数丢给 LLM，而是先定义 tool schema？

因为 LLM 不能稳定理解 Python 函数的真实执行边界。

tool schema 的价值是：

- 明确工具名称
- 明确工具用途
- 明确参数结构
- 降低模型选错工具的概率
- 为后续 eval 和 trace 提供结构化依据

专业 Agent 项目里，工具不是“随便暴露函数”，而是要先定义稳定协议。

### 5. 当前有哪些工具被加入了 schema？任选 3 个说明它们适合处理什么任务。

当前加入 schema 的工具包括：

- `read_file`
- `list_dir`
- `count_lines`
- `search_docs`
- `answer_docs_with_llm`
- `list_mcp_tools`
- `mcp_workspace_summary`
- `list_skills`
- `plan_skill`
- `list_subagents`
- `plan_subagents`

示例：

- `read_file`：适合读取 `README.md`、配置文件、文档文件等本地小文本文件。
- `search_docs`：适合从项目文档中搜索某个主题，例如 MCP、RAG、LangGraph。
- `mcp_workspace_summary`：适合通过本地 MCP adapter 获取工作区摘要。

## 练习 3：理解 LLM 输出解析

### 1. `ToolCallSelection` 中 5 个字段分别是什么意思？

- `action`：模型选择的动作，例如 `use_tool`、`answer_directly`、`ask_clarification`。
- `tool_name`：模型选择的工具名。
- `tool_input`：传给工具的输入参数。
- `reason`：模型选择该动作或工具的原因。
- `raw_response`：模型原始输出，保留用于 debug 和 trace。

### 2. `parse_tool_call_selection()` 为什么不直接相信模型输出？

因为真实 LLM 输出不稳定，可能出现：

- 不是 JSON
- JSON 字段缺失
- action 非法
- `use_tool` 却没有 `tool_name`
- `tool_name` 或 `tool_input` 类型不对

如果不校验，后面的工具执行就会出现难以定位的问题。

### 3. `_parse_json_object()` 为什么要先找 `{` 和 `}`？

因为模型有时会在 JSON 外面加解释文字或代码块。

例如：

```text
Here is the JSON:
{"action":"use_tool", ...}
```

先定位 `{` 和 `}` 可以尽量提取真正的 JSON 对象，提高容错能力。

### 4. 如果模型返回了非法 action，会发生什么？

`parse_tool_call_selection()` 会抛出 `LLMError`。

然后在 `WorkspaceAgent._select_tool_call()` 中被捕获，并转换成 `ToolError`。最终主 Agent 会记录：

```text
Tool calling failed
```

并返回工具调用失败的用户可读答案。

### 5. 为什么 `action != "use_tool"` 时要把 `tool_name` 和 `tool_input` 归一化成 `None`？

因为只有 `use_tool` 才应该携带工具名和工具参数。

如果模型选择 `answer_directly` 或 `ask_clarification`，但又返回了工具字段，会造成语义混乱。

归一化成 `None` 可以让后续代码判断更简单，也让 trace 更清晰。

## 练习 4：理解 tool_input 归一化

### 1. 为什么模型选对了工具，还可能需要归一化 `tool_input`？

因为模型可能选对工具，但参数不稳定。

例如：

- 选了 `read_file`，但 `tool_input` 是空
- 选了 `read_file`，但 `tool_input` 是 `read README.md`
- 选了 `count_lines`，但参数不是文件路径

工具执行需要精确参数，不能只靠模型语义。

### 2. 本阶段实际遇到过什么问题？为什么 `read_file` 会收到 `.`？

实际遇到的问题是：

模型选择了 `read_file`，但没有稳定返回 `README.md` 作为 `tool_input`。

当 `tool_input` 为空时，底层工具调用逻辑会使用默认值 `"."`。  
但 `read_file` 需要的是文件路径，`"."` 是目录，所以报错：

```text
Path is not a file: .
```

这个问题说明：模型选对工具不等于参数正确。

### 3. 对于 `read_file` 和 `count_lines`，代码如何从用户输入里提取路径？

`_infer_tool_input()` 会使用 `_FILE_PATTERN` 从原始用户输入中提取文件路径。

例如：

```text
Use tool calling to read README.md.
```

可以提取出：

```text
README.md
```

然后把它作为真正的 `tool_input`。

### 4. 对于 `list_dir`，为什么没有路径时默认返回 `"."`？

因为 `list_dir` 可以合理地作用于当前工作区根目录。

用户说“list directory”但没有指定路径时，查看当前目录是安全且符合预期的默认行为。

但 `read_file` 不能默认用 `"."`，因为读取文件必须是具体文件路径。

### 5. 这层归一化属于“模型能力”还是“工程兜底”？为什么？

属于工程兜底。

模型负责理解意图和选择工具。  
代码负责保证参数可执行、安全、稳定。

这正是专业 Agent 工程的核心边界：不能把系统可靠性完全交给模型。

## 练习 5：跑 CLI 并解释 trace

运行：

```bash
python -m cli.tool_calling_demo --input "Use tool calling to read README.md." --trace
```

### 1. trace 中 `Route request` 显示什么？

应显示类似：

```text
Route request: tool_call / llm_tool_selector
```

表示规则路由层识别出：这次请求要进入 LLM tool calling 分支。

### 2. trace 中 `[Tool Call]` 显示什么？

显示模型选择结果，例如：

```text
[Tool Call]
action=use_tool, tool=read_file, input=README.md
```

它说明模型选择了 `read_file`，并传入 `README.md`。

### 3. trace 中 `[Tool]` 显示什么？

显示本地工具真正执行后的结果。

例如：

```text
[Tool] read_file
[read_file] README.md
...
```

### 4. `[Tool Call]` 和 `[Tool]` 的区别是什么？

`[Tool Call]` 是模型决策。  
`[Tool]` 是工具执行结果。

前者回答“模型想做什么”。  
后者回答“代码实际做成了什么”。

### 5. 如果 `[Tool Call]` 选对了工具但 `[Tool]` 失败，问题更可能在哪一层？

更可能在：

- 参数归一化层
- 工具执行层
- 文件路径或工作区状态

不一定是模型选择层的问题。

## 练习 6：对比三种执行路径

运行：

```bash
python -m cli.main --input "Read README.md." --trace
python -m cli.main --input "Use LangGraph to read README.md." --trace
python -m cli.tool_calling_demo --input "Use tool calling to read README.md." --trace
```

### 1. 规则路由路径的 route 是什么？

规则路由路径是：

```text
use_tool / read_file
```

### 2. LangGraph 路径的 route 是什么？

LangGraph 路径是：

```text
graph / langgraph_workflow
```

graph 内部还会有自己的 route，例如：

```text
Graph route: read_file
Selected tool: read_workspace_file
```

### 3. tool calling 路径的 route 是什么？

tool calling 路径是：

```text
tool_call / llm_tool_selector
```

然后 LLM 再选择实际工具，例如：

```text
read_file
```

### 4. 三种路径最终都能读 README，但决策责任分别在哪里？

- 规则路由：由 `route_intent()` 的确定性规则负责。
- LangGraph：由 graph 节点和条件边负责。
- tool calling：由 LLM 根据 tool schema 负责工具选择，代码负责执行和校验。

### 5. 哪一种更容易测试？哪一种更接近真实 Agent？为什么？

规则路由最容易测试，因为结果确定。

tool calling 更接近真实 Agent，因为真实 Agent 通常需要模型根据工具说明动态选择工具和参数。

LangGraph 更适合复杂流程编排，尤其是多步骤、多分支、多状态任务。

## 练习 7：理解 eval 改动

### 1. `expected_selected_tool` 是用来检查什么的？

它用于检查 tool calling 分支中，模型最终选择的实际工具是否符合预期。

例如外层 route 是 `tool_call`，但模型实际应该选择：

```text
read_file
```

### 2. `selected_tool_name` 来自哪里？

来自：

```text
run.tool_call.tool_name
```

也就是模型结构化选择结果中的工具名。

### 3. 为什么只检查 `expected_tool` 不够？

因为 `expected_tool` 只检查外层工具：

```text
llm_tool_selector
```

但真正被执行的业务工具可能是：

```text
read_file
search_docs
count_lines
```

如果只检查外层 tool，就无法判断模型是否选对了实际工具。

### 4. `test_eval_runner_checks_selected_tool()` 为什么要用 fake LLM client？

因为 eval 测试需要稳定。

fake LLM client 可以固定返回：

```json
{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"Inspect the README."}
```

这样测试不会受网络、API Key、模型随机性的影响。

### 5. 如果模型选择了 `search_docs`，但外层 route 是 `tool_call`，eval 应该如何判断？

eval 应该分两层判断：

1. `expected_route` 是否是 `tool_call`
2. `expected_selected_tool` 是否是 `search_docs`

这样才能区分“是否进入 tool calling 分支”和“模型是否选对实际工具”。

## 练习 8：小改动练习，不提交

运行：

```bash
python -m cli.tool_calling_demo --input "Use tool calling to count lines in README.md." --trace
```

### 1. 模型是否选择了 `count_lines`？

理想情况下应该选择 `count_lines`。

如果模型选择了 `read_file`，说明 tool schema 或 prompt 对“count lines”的引导还不够强。

### 2. `tool_input` 是否是 `README.md`？

理想情况下应该是：

```text
README.md
```

如果模型返回了空值或 `count lines in README.md`，归一化层应该从原始输入中提取出 `README.md`。

### 3. 最终是否输出 `Line count`？

如果工具执行成功，应输出：

```text
Line count: ...
```

### 4. 如果失败，如何判断原因？

- 模型选错工具：问题在 tool schema 或 prompt。
- `tool_input` 错了：问题在模型参数输出或归一化层。
- 工具执行失败：问题在工具参数、文件路径或工具实现。
- trace 不清楚：问题在观测层，需要增强 trace。

## 练习 9：设计题

### 1. 现在的 tool calling 为什么还不是完整的多步 agent loop？

因为当前 v15 只支持一次模型选择和一次工具执行。

完整多步 agent loop 通常需要：

```text
模型选择工具
-> 执行工具
-> 模型读取工具结果
-> 决定是否继续调用工具
-> 最终综合回答
```

当前还没有“工具结果回传给模型继续推理”的循环。

### 2. 如果用户问：“先搜索 MCP，再总结 README 中和 MCP 相关的内容”，当前 v15 能不能很好处理？

不能很好处理。

原因是这是一个多步任务：

1. 搜索 MCP
2. 读取或检索 README
3. 综合总结

v15 当前更适合单次工具选择，不适合多步工具链。

### 3. 下一阶段如果做多步 tool loop，需要新增哪些状态字段？

可能需要：

- 当前轮次
- 最大工具调用次数
- tool call history
- tool result history
- intermediate observations
- final answer
- stop reason
- error state

### 4. tool calling 和 LangGraph 应该是什么关系？

tool calling 负责“模型如何选工具”。  
LangGraph 负责“多步骤流程如何编排”。

更合理的后续结构是：

```text
LangGraph node
-> LLM tool selector
-> tool execution
-> observation
-> next graph node
```

### 5. MCP 和 Skills 接入 tool schema 后，会带来什么好处？

好处是工具层会统一。

模型可以在同一套 schema 中选择：

- 本地文件工具
- RAG 工具
- MCP 工具
- Skill 工具
- Subagent 工具

这比在代码里为每类能力写独立规则更接近专业 Agent 项目。

## 练习 10：阶段验收

### 1. 能画出主链路

```text
user input
-> route_intent
-> tool_call branch
-> tool schema prompt
-> DeepSeek JSON decision
-> parse / normalize
-> local tool execution
-> trace / eval
```

### 2. 能解释 `tool_call`、`tool_result`、`selected_tool_name` 三者区别

- `tool_call`：模型选择结果。
- `tool_result`：本地工具执行结果。
- `selected_tool_name`：eval 中记录的模型实际选择工具名。

### 3. 能说明为什么真实 LLM 输出必须做 JSON 校验和参数兜底

因为真实 LLM 输出不稳定。  
它可能格式错误、字段缺失、工具选对但参数不准。

没有校验和兜底，Agent 会很难调试，也很难做稳定评估。

### 4. 能跑通验证命令

```bash
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.tool_calling_demo --input "Use tool calling to read README.md." --trace
```

### 5. 能判断失败发生在哪一层

需要能区分：

- 路由层：是否进入了正确 action。
- 模型选择层：是否选对工具。
- 参数归一化层：参数是否变成可执行输入。
- 工具执行层：工具是否成功返回结果。
- 最终回答层：结果是否被正确组织给用户。

## 阶段结论

v15 的核心价值是把真实 LLM 从“只负责生成答案”推进到“可以参与工具选择”。

但工程边界仍然清晰：

```text
LLM decides.
Code validates.
Tool executes.
Trace records.
Eval checks.
```

下一阶段应该继续把单次 tool calling 扩展为更专业的工具层，优先方向是：

1. 多步 tool loop。
2. MCP / Skills 接入统一 tool schema。
3. LangGraph 编排 tool calling 节点。

