# LLM Tool Loop 阶段练习答案

对应版本：v16  
主题：bounded multi-step LLM tool loop  
用途：阶段复盘与下一阶段恢复学习

## 练习 1：理解 v16 和 v15 的差异

### 1. v15 的执行链路是什么？

v15 是单次 tool calling：

```text
user input
-> route_intent
-> tool_call branch
-> LLM selects one action / tool / input
-> parse and normalize
-> local tool executes once
-> final answer
```

重点是：模型只做一次工具选择。

### 2. v16 的执行链路是什么？

v16 是 bounded multi-step tool loop：

```text
user input
-> route_intent
-> tool_loop branch
-> _run_tool_loop
-> LLM selects tool
-> local tool executes
-> observation recorded
-> next LLM input includes observations
-> LLM chooses continue or stop
-> final answer
```

重点是：模型可以基于上一轮 observation 再做下一步决策。

### 3. v16 比 v15 多了哪一步核心能力？

v16 多了 observation feedback。

也就是工具执行结果不再只是直接返回给用户，而是会被整理成 observation，再交给模型决定下一步。

### 4. 为什么 v16 仍然不是完整 ReAct Agent？

因为 v16 还缺少完整 ReAct 的几个关键能力：

- 没有显式 Thought / Action / Observation 格式
- 最终答案不是由 LLM 基于全部 observations 生成
- 没有复杂任务规划
- 没有 graph 级别状态编排
- 没有跨多类工具的成熟策略

v16 只是向 ReAct loop 迈进了一步。

### 5. v16 的最终答案现在是谁生成的：LLM 还是确定性代码？

当前最终答案主要由确定性代码生成。

LLM 可以通过 `answer_directly` 表达“信息已经足够”，但最终 `ToolLoopResult.to_text()` 和 `_compose_tool_loop_final_answer()` 负责把结果组织成文本。

## 练习 2：读主链路

### 1. 用户输入 `Use tool loop to count lines in README.md and then answer.` 后，哪个函数识别出 `tool_loop`？

由 `agent/router.py` 中的 `route_intent()` 识别。

内部调用：

```text
_looks_like_tool_loop_request()
```

如果命中 `tool loop`、`multi-step tool`、`loop with tools` 等关键词，就返回 `tool_loop` 路由。

### 2. `ToolRoute` 中的 `action` 和 `tool_name` 分别是什么？

结果是：

```text
action = "tool_loop"
tool_name = "llm_tool_loop"
```

`action` 决定进入 `WorkspaceAgent.run()` 的哪个分支。  
`tool_name` 用来描述这次外层能力是 LLM tool loop。

### 3. `WorkspaceAgent.run()` 中，`tool_loop` 分支做了哪几件事？

主要做 5 件事：

1. 取出清理后的 loop 任务文本。
2. 调用 `_run_tool_loop()`。
3. 将 loop 最后一轮 selection 写入 `run.tool_call`。
4. 将 loop 总结果写入 `run.tool_loop_result`。
5. 生成 `run.answer` 并记录 trace。

### 4. `_run_tool_loop()` 中为什么要维护 `observations`？

因为每一轮工具执行结果都要影响下一轮模型决策。

例如第一轮执行：

```text
count_lines README.md
```

得到：

```text
Line count: 609
```

第二轮模型看到这个 observation 后，就可以判断“不需要继续调用工具，可以直接回答”。

### 5. `_run_tool_loop()` 中为什么要维护 `seen_tool_calls`？

为了防止模型重复调用同一个工具和同一个参数。

如果模型连续选择：

```text
read_file / README.md
read_file / README.md
```

通常说明它没有有效利用 observation，可能陷入循环。  
`seen_tool_calls` 可以让系统及时停止，避免无限调用。

## 练习 3：理解 `ToolLoopStep`

### 1. `ToolLoopStep` 代表什么？

`ToolLoopStep` 表示 tool loop 中的一轮执行记录。

它包含这一轮：

- 第几步
- 模型选择了什么
- 工具返回了什么 observation
- 是否发生错误

### 2. `index` 字段为什么从 1 开始？

因为 trace 是给人看的。

用户和开发者阅读时，`step=1` 比 `step=0` 更自然。

### 3. `selection` 字段保存的是什么？

保存本轮模型的结构化选择结果，也就是 `ToolCallSelection`。

包括：

- `action`
- `tool_name`
- `tool_input`
- `reason`
- `raw_response`

### 4. `observation` 字段保存的是什么？

保存工具执行后的摘要结果。

它不是完整工具输出，而是经过 `_preview_observation()` 压缩后的观察信息，方便传给下一轮模型。

### 5. `error` 字段什么时候会有值？

当这一轮出现错误时会有值，例如：

- 工具执行失败
- 重复工具调用被拦截

### 6. `describe()` 的作用是什么？

`describe()` 用于把这一轮 loop 步骤渲染成 compact trace。

例如：

```text
step=1; action=use_tool; tool=count_lines; input=README.md; ok
```

## 练习 4：理解 `ToolLoopResult`

### 1. `ToolLoopResult` 代表什么？

`ToolLoopResult` 表示整个 tool loop 的最终结果。

它不是单步结果，而是完整 loop 的汇总。

### 2. `objective` 保存什么？

保存用户原始任务目标，也就是 loop 要完成的事情。

例如：

```text
count lines in README.md and then answer
```

### 3. `steps` 保存什么？

保存所有 `ToolLoopStep`。

它记录 loop 中每一轮模型决策和工具 observation。

### 4. `final_answer` 保存什么？

保存最终给用户看的答案主体。

当前它是确定性汇总，主要基于 objective、stop reason 和 observations 生成。

### 5. `stop_reason` 有什么作用？

`stop_reason` 说明 loop 为什么停止。

常见值：

- `model_answered_directly`
- `needs_clarification`
- `tool_error`
- `repeated_tool_call`
- `max_steps`

这个字段非常重要，因为它能说明 loop 是正常完成、遇到错误，还是被保护机制中断。

### 6. `to_text()` 为什么要存在？

因为内部结构不能直接给用户看。

`to_text()` 负责把 `ToolLoopResult` 渲染成可读文本，包括：

- 停止原因
- 任务目标
- loop steps
- final answer

## 练习 5：理解 `_run_tool_loop()`

### 1. `max_steps=3` 的作用是什么？

限制最多执行 3 轮 loop。

这是安全边界，防止模型无限调用工具。

### 2. 每一轮 loop 中，模型输入由什么构成？

由 `_build_tool_loop_input()` 构造。

第一轮通常只有 objective。  
后续轮次会包含 objective 和 previous observations。

### 3. 第一轮和第二轮的模型输入有什么不同？

第一轮：

```text
objective
```

第二轮：

```text
objective
previous observations
instruction: choose next smallest sufficient action
```

第二轮模型可以看到上一轮工具结果，因此能决定是否继续。

### 4. 如果模型返回 `use_tool`，代码会做什么？

代码会：

1. 检查是否重复调用同一个 `(tool_name, tool_input)`。
2. 构造 `ToolRoute`。
3. 调用 `_call_tool()`。
4. 将工具结果压缩成 observation。
5. 追加到 `observations` 和 `loop_steps`。
6. 进入下一轮。

### 5. 如果模型返回 `answer_directly`，代码会做什么？

代码会：

1. 创建最后一个 `ToolLoopStep`。
2. 调用 `_compose_tool_loop_final_answer()`。
3. 返回 `ToolLoopResult`。
4. `stop_reason` 设置为 `model_answered_directly`。

### 6. 如果模型返回 `ask_clarification`，代码会做什么？

代码会停止 loop，并返回：

```text
stop_reason = needs_clarification
```

最终答案会提示用户需要补充信息。

### 7. 如果工具执行失败，loop 如何停止？

如果 `_call_tool()` 抛出 `ToolError`，loop 会：

1. 记录当前 step 的 error。
2. 返回 `ToolLoopResult`。
3. `stop_reason` 设置为 `tool_error`。

### 8. 如果模型重复调用同一个工具，loop 如何停止？

如果 `(tool_name, tool_input)` 已经出现在 `seen_tool_calls` 中，loop 会：

1. 记录 `Repeated tool call detected.`
2. 返回 `ToolLoopResult`
3. `stop_reason` 设置为 `repeated_tool_call`

这是保护机制，不是普通异常。

## 练习 6：跑真实 CLI 并解释 trace

运行：

```bash
python -m cli.tool_loop_demo --input "Use tool loop to count lines in README.md and then answer." --trace
```

### 1. trace 中 `Route request` 是什么？

应该类似：

```text
Route request: tool_loop / llm_tool_loop
```

### 2. trace 中 `Run tool loop` 显示什么？

显示 loop 的摘要，例如：

```text
Run tool loop: steps=2; stop_reason=model_answered_directly
```

### 3. `[Tool Loop]` 里面有几步？

真实 demo 中通常有 2 步：

1. 调用 `count_lines`
2. `answer_directly` 停止

### 4. 第一步选择了什么工具？

第一步选择：

```text
tool=count_lines
input=README.md
```

### 5. 第一步 observation 是什么？

observation 是 `count_lines` 工具返回的行数摘要，例如：

```text
count_lines: [count_lines] README.md Line count: 609
```

具体行数会随着 README 修改而变化。

### 6. 第二步为什么可以停止？

因为第二轮模型已经看到了第一轮 observation，知道 README 的行数已经拿到，不需要继续调用工具。

### 7. `stop_reason=model_answered_directly` 表示什么？

表示模型判断已有信息足够，选择了 `answer_directly`，loop 正常停止。

## 练习 7：对比 tool calling 和 tool loop

### 1. tool calling 最多会调用几次工具？

v15 tool calling 最多调用 1 次工具。

### 2. tool loop 最多会调用几次工具？当前代码限制是多少？

v16 tool loop 最多运行 3 轮。

代码默认：

```python
max_steps = 3
```

注意：不是每一轮都一定调用工具，因为某一轮可能是 `answer_directly` 或 `ask_clarification`。

### 3. tool calling 会不会把工具结果再次交给模型？

不会。

tool calling 执行一次工具后就直接生成最终答案。

### 4. tool loop 会不会把 observation 再交给模型？

会。

这是 v16 的核心新增能力。

### 5. 哪个更适合处理“先做 A，再根据 A 的结果决定 B”的任务？

tool loop 更适合。

因为它可以根据 A 的 observation 决定是否继续做 B。

## 练习 8：理解重复调用保护

### 1. `seen_tool_calls` 记录什么？

记录已经执行过的工具调用组合。

格式是：

```python
(tool_name, tool_input)
```

### 2. 为什么 key 用 `(tool_name, tool_input)`？

因为是否重复，不能只看工具名。

例如：

```text
read_file README.md
read_file agent/core.py
```

这两个不是重复调用，因为参数不同。

但：

```text
read_file README.md
read_file README.md
```

就是重复调用。

### 3. 如果模型连续两次选择 `read_file / README.md`，会发生什么？

第二次会被拦截。

loop 返回：

```text
stop_reason = repeated_tool_call
error = Repeated tool call detected.
```

### 4. 为什么重复调用保护很重要？

因为真实 LLM 可能没有正确利用 observation，反复选择同一个工具。

没有保护会导致：

- 浪费 token
- 浪费 API 调用
- trace 变长
- 用户等待时间变长
- 可能进入无限循环

### 5. 如果没有这个保护，真实 LLM 可能出现什么问题？

可能反复执行同一个工具，例如：

```text
read_file README.md
read_file README.md
read_file README.md
...
```

这类问题在 Agent 系统里很常见，所以 loop 必须有边界。

## 练习 9：理解测试设计

### 1. `SequenceToolLoopClient` 的作用是什么？

它是 fake LLM client，用来按顺序返回固定模型响应。

### 2. 为什么它要按顺序返回多个 fake LLM response？

因为 tool loop 有多轮模型调用。

第一轮可能返回 `use_tool`，第二轮可能返回 `answer_directly`。

如果 fake client 只能返回一个响应，就无法测试多步行为。

### 3. `test_workspace_agent_runs_two_step_tool_loop()` 验证了什么？

验证正常两步 loop：

1. 第一轮模型选择 `read_file`
2. 工具成功执行
3. 第二轮模型选择 `answer_directly`
4. loop 正常停止

### 4. `test_tool_loop_stops_on_repeated_tool_call()` 验证了什么？

验证重复调用保护。

当模型连续两次选择相同的工具和参数时，loop 应停止，并返回 `repeated_tool_call`。

### 5. `test_tool_loop_trace_dict_contains_steps()` 验证了什么？

验证结构化 trace 中包含：

- `tool_loop`
- `step_count`
- `stop_reason`
- loop steps

### 6. 为什么这些测试不应该调用真实 DeepSeek？

因为单元测试必须稳定、快速、可重复。

真实 DeepSeek 会引入：

- 网络依赖
- API Key 依赖
- 响应随机性
- 成本
- 速度波动

所以测试用 fake client 是正确做法。

## 练习 10：失败定位

### 场景 1

```text
Route request: direct_answer / none
```

但你希望进入 tool loop。

问题在路由层。

说明 `route_intent()` 没有识别出 tool loop 意图，可能是输入没有包含 `tool loop`、`multi-step tool` 等触发词。

### 场景 2

```text
Route request: tool_loop / llm_tool_loop
step=1; action=use_tool; tool=read_file; input=none
Tool loop failed
```

问题更可能在模型选择层或参数归一化层。

模型选了 `read_file`，但没有给出有效文件路径。  
如果归一化层也没能从用户输入中提取路径，最终工具执行会失败。

### 场景 3

```text
step=1; action=use_tool; tool=count_lines; input=README.md; ok
step=2; action=use_tool; tool=count_lines; input=README.md; error=Repeated tool call detected.
```

这是 loop 控制层的保护机制生效。

不是普通 bug。

说明模型第二轮没有利用第一轮 observation，而是重复选择同一个工具调用。

### 场景 4

```text
step=1; action=use_tool; tool=count_lines; input=README.md; ok
stop_reason=max_steps
```

说明 loop 到达最大步数限制。

可能原因：

- 模型一直没有选择 `answer_directly`
- 任务需要更多步骤
- `max_steps` 设置过低
- prompt 没有清楚要求信息足够时停止

## 练习 11：设计题

### 1. v16 为什么要设置 `max_steps`？

为了限制成本和风险。

没有最大步数，模型可能无限循环调用工具。

### 2. 如果将来支持更多工具，`max_steps` 应该固定还是可配置？

应该可配置。

不同任务复杂度不同：

- 简单文件任务：2-3 步足够
- 代码分析任务：可能需要 5-8 步
- 多文档调研任务：可能需要更多步骤

但无论如何都应该有上限。

### 3. 现在的 `final_answer` 为什么还不够自然？

因为它主要由确定性代码拼接。

它适合调试和学习，但不像真实 LLM synthesis 那样自然、完整、有总结能力。

### 4. 如果下一阶段加入 LLM final synthesis，需要把哪些内容传给模型？

至少需要：

- 原始 objective
- 每一步 tool call
- 每一步 observation
- stop_reason
- 错误信息
- 输出格式要求

模型再基于这些内容生成最终自然语言回答。

### 5. tool loop 和 LangGraph 应该怎么结合？

合理关系是：

```text
LangGraph controls state and nodes.
Tool loop runs inside a graph node.
```

或者：

```text
LangGraph node: select tool
LangGraph node: execute tool
LangGraph node: observe
LangGraph conditional edge: continue or finish
```

LangGraph 更适合管理复杂状态和条件流转。

### 6. MCP 和 Skills 接入 tool loop 后，可以支持哪些更复杂的任务？

可以支持：

- 先用 MCP 获取 workspace summary，再决定读哪个文件
- 先搜索 docs，再选择 skill 生成复盘
- 先列出 subagents，再规划协作任务
- 先读取代码文件，再调用 code review skill
- 先检索 RAG，再用 LLM synthesis 输出最终报告

## 练习 12：阶段验收

### 1. 能画出 v16 链路

```text
user input
-> route_intent
-> tool_loop branch
-> _run_tool_loop
-> LLM selects tool
-> local tool executes
-> observation recorded
-> LLM sees observations
-> answer_directly / continue / stop
-> trace and eval
```

### 2. 能解释核心概念

- `ToolLoopStep`：loop 中一轮模型选择和工具观察。
- `ToolLoopResult`：整个 loop 的最终汇总。
- `observations`：上一轮工具执行结果，作为下一轮模型输入。
- `seen_tool_calls`：已执行工具调用集合，用于防止重复。
- `stop_reason`：loop 停止原因。

### 3. 能跑通验证命令

```bash
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.tool_loop_demo --input "Use tool loop to count lines in README.md and then answer." --trace
```

### 4. 能判断失败发生在哪一层

需要能区分：

- 路由层：是否进入 `tool_loop`
- 模型选择层：是否选对 action 和 tool
- 工具参数层：`tool_input` 是否正确
- 工具执行层：工具是否成功返回
- loop 控制层：是否触发 max steps 或 repeated tool call
- 最终答案层：回答是否清楚表达结果

### 5. 能说明为什么 v16 是向 ReAct / 专业 Agent loop 迈进，但还不是完整 ReAct

v16 已经具备：

- Action
- Tool execution
- Observation
- Continue / stop

但还缺少：

- 显式 reasoning trace
- LLM final synthesis
- 更成熟的 graph orchestration
- 更完整的工具协议和多工具任务规划

## 阶段结论

v16 的核心价值是让 Agent 从“一次工具选择”进入“多步工具循环”。

当前边界是：

```text
LLM chooses next action.
Code executes and observes.
Loop controls risk.
Trace exposes every step.
```

下一阶段建议继续做：

1. LLM final synthesis。
2. MCP / Skills 接入统一 tool loop。
3. 将 tool loop 编排迁移或嵌入 LangGraph。

