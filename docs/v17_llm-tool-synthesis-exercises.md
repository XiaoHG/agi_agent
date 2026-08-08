# LLM Tool Loop Final Synthesis 阶段练习答案

对应版本：v17  
主题：LLM Tool Loop Final Synthesis  
用途：阶段复盘与下一阶段恢复学习

## 练习 1：理解 v17 和 v16 的差异

### 1. v16 的最终答案是谁生成的？

v16 的最终答案主要由确定性代码生成。

具体是：

```text
ToolLoopResult.to_text()
_compose_tool_loop_final_answer()
```

LLM 在 v16 中负责：

- 选择工具
- 基于 observation 决定是否停止

但最终给用户看的答案不是由 LLM 综合生成的。

### 2. v17 的最终答案是谁生成的？

v17 的最终答案优先由 LLM 生成。

流程是：

```text
_run_tool_loop()
->_synthesize_tool_loop_result()
->synthesize_tool_loop_answer()
->DeepSeek final synthesis
```

如果 LLM synthesis 失败，才回退到确定性代码。

### 3. v17 比 v16 多了哪一层能力？

v17 多了 final synthesis 层。

这一层负责把 tool loop 收集到的：

- objective
- tool calls
- observations
- stop reason
- errors

综合成自然语言最终答案。

### 4. 为什么 final synthesis 不能直接编造信息？

因为 final synthesis 的职责是基于工具证据回答。

如果 LLM 编造 observation 中没有的信息，就会破坏 Agent 的可信度。

例如工具返回：

```text
Line count: 616
```

最终答案就不能说：

```text
README.md 有 9999 行
```

这属于 synthesis 层幻觉。

### 5. 为什么 final synthesis 失败时不能让整个 tool loop 失败？

因为工具循环本身可能已经成功完成。

例如：

```text
count_lines README.md -> Line count: 616
```

如果最终 LLM synthesis 失败，但 observation 已经可用，系统应该回退到确定性汇总，而不是丢掉已有结果。

这就是 v17 的 fallback 设计。

## 练习 2：读主链路

### 1. `WorkspaceAgent.run()` 中，tool loop 分支现在比 v16 多调用了哪个方法？

比 v16 多调用：

```python
_synthesize_tool_loop_result()
```

v17 的 tool loop 分支大致是：

```text
_run_tool_loop()
->_synthesize_tool_loop_result()
->run.answer
```

### 2. `_run_tool_loop()` 和 `_synthesize_tool_loop_result()` 分别负责什么？

`_run_tool_loop()` 负责执行多步工具循环：

- 让 LLM 选择工具
- 执行工具
- 记录 observation
- 判断停止条件
- 返回 `ToolLoopResult`

`_synthesize_tool_loop_result()` 负责最终答案综合：

- 把 `ToolLoopResult` 交给 LLM
- 请求 LLM 基于 observations 生成最终答案
- 如果失败，则生成 deterministic fallback

### 3. `_synthesize_tool_loop_result()` 为什么要 catch exception？

因为 final synthesis 是一次真实 LLM 调用，可能失败。

失败原因包括：

- 网络错误
- API Key 问题
- 模型返回空答案
- 响应格式异常

如果不捕获异常，整个 tool loop 会失败。  
但工程上更合理的是保留已有 observation，并给出 fallback 答案。

### 4. `ToolLoopResult.final_answer_source` 有哪些可能值？

当前主要有：

- `deterministic`
- `llm`
- `deterministic_fallback`

含义：

- `deterministic`：默认确定性答案来源。
- `llm`：最终答案来自 LLM synthesis。
- `deterministic_fallback`：LLM synthesis 失败后回退到确定性答案。

### 5. `run.answer` 最后来自哪里？

`run.answer` 来自：

```python
run.tool_loop_result.to_text()
```

而 `to_text()` 中包含：

- stop reason
- objective
- loop steps
- final answer source
- final answer

其中 `final_answer` 在 v17 中优先来自 LLM synthesis。

## 练习 3：理解 final synthesis prompt

### 1. 这个 prompt 给 LLM 定义了什么角色？

定义为：

```text
本地 Agent 的最终答案生成器
```

它不是工具选择器，也不是工具执行器，而是最终答案综合器。

### 2. prompt 要求输入包含哪些内容？

包括：

- 用户原始目标
- tool loop 停止原因
- 每一步工具选择
- 每一步工具 observation
- 错误信息

### 3. prompt 对输出有什么要求？

要求：

- 直接给出最终答案
- 不输出 JSON
- 先给结论
- 说明依据
- 信息不足时明确说明不足
- 不编造 observation 中没有的信息
- 保留关键数字、文件名、工具名

### 4. 为什么要求“不编造 observation 中没有的信息”？

因为 final synthesis 是基于工具结果的 grounded answer。

它必须受 observation 约束。  
否则 Agent 会产生“工具已经查过，但最终答案仍然幻觉”的问题。

### 5. 为什么要求“保留关键数字、文件名、工具名”？

因为这些是可验证信息。

例如：

- `README.md`
- `count_lines`
- `616 行`

这些信息可以帮助用户判断答案是否来自真实工具结果，而不是模型自由发挥。

## 练习 4：理解 `tool_synthesis.py`

### 1. `build_tool_loop_synthesis_messages()` 的输入是什么？

输入是：

- `ToolLoopResult`
- synthesis prompt 字符串

返回值是发给 LLM 的 `LLMMessage` 列表。

### 2. 它如何把 `ToolLoopResult.steps` 转成 prompt？

它遍历每个 `ToolLoopStep`，把每一步转换成文本块。

每个 step block 会包含本轮的 action、tool、input、reason、observation 和 error。

### 3. 每个 step 会包含哪些字段？

每个 step 包含：

- Step
- Action
- Tool
- Input
- Reason
- Observation
- Error

这些字段能让 LLM 理解每一步发生了什么。

### 4. `synthesize_tool_loop_answer()` 做了什么？

它做 3 件事：

1. 调用 `build_tool_loop_synthesis_messages()` 构造 messages。
2. 调用 `client.chat()` 请求 LLM。
3. 返回 LLM 的最终内容。

如果 LLM 返回空内容，会抛出 `LLMError`。

### 5. 为什么如果 LLM 返回空字符串，要抛出 `LLMError`？

因为空字符串不是有效最终答案。

如果不抛错，用户会看到空答案，trace 也难以判断问题。  
抛出 `LLMError` 后，主 Agent 可以触发 fallback。

## 练习 5：理解 `final_answer_source`

### 1. `final_answer_source` 记录什么？

记录最终答案来源。

它告诉我们：

```text
最终答案是 LLM 生成的，还是 fallback 生成的？
```

### 2. 为什么默认值是 `"deterministic"`？

因为 `ToolLoopResult` 在没有 final synthesis 前，本质上就是确定性代码构造的结果。

默认值表示原始来源。

### 3. 什么时候会变成 `"llm"`？

当 `_synthesize_tool_loop_result()` 成功调用 LLM，并拿到非空最终答案时，会变成：

```text
llm
```

### 4. 什么时候会变成 `"deterministic_fallback"`？

当 final synthesis 失败时，会变成：

```text
deterministic_fallback
```

例如：

- LLM 返回空答案
- 网络失败
- API 错误

### 5. trace 中显示 `Final answer source` 的价值是什么？

它让我们能快速判断最终答案来源。

如果答案质量不好，可以先看：

```text
Final answer source: llm
```

还是：

```text
Final answer source: deterministic_fallback
```

这样能判断问题是在 LLM synthesis 层，还是 fallback 汇总层。

## 练习 6：跑真实 CLI 并解释输出

运行：

```bash
python -m cli.tool_loop_demo --input "Use tool loop to count lines in README.md and then answer." --trace
```

### 1. trace 中有几步 tool loop？

通常有 2 步：

1. `use_tool`
2. `answer_directly`

### 2. 第一步工具是什么？

第一步工具是：

```text
count_lines
```

输入通常是：

```text
README.md
```

### 3. 第一步 observation 是什么？

observation 是工具返回的行数结果，例如：

```text
[count_lines] README.md Line count: 616
```

具体数字会随着 README 内容变化。

### 4. 第二步为什么停止？

因为第二轮 LLM 看到了第一轮 observation，知道已经拿到 README 的行数，不需要继续调用工具，于是选择：

```text
answer_directly
```

### 5. `Final answer source: llm` 表示什么？

表示最终答案是由 LLM 基于 observations 综合生成的。

不是确定性代码直接拼出来的。

### 6. 最终答案中的行数来自哪里？

来自第一步 `count_lines` 工具的 observation。

LLM final synthesis 只是把这个 observation 转成自然语言答案。

### 7. 如果 README 修改了，最终答案中的行数会不会变？为什么？

会变。

因为每次运行都会重新执行 `count_lines README.md`。  
最终答案中的行数来自实时工具结果，而不是写死的数字。

## 练习 7：理解 fallback

### 1. 为什么 final synthesis 需要 fallback？

因为 final synthesis 依赖真实 LLM 调用，存在失败风险。

但 tool loop 已经拿到的 observations 仍然有价值。  
fallback 可以保证任务不会因为最后一步 LLM 失败而完全失败。

### 2. fallback 时 `final_answer_source` 是什么？

是：

```text
deterministic_fallback
```

### 3. fallback 答案基于什么生成？

基于原始 `ToolLoopResult.final_answer`，也就是确定性汇总结果。

同时会附加：

```text
Final synthesis fallback reason: ...
```

### 4. fallback 会不会重新执行工具？

不会。

fallback 只处理最终答案生成失败，不重新执行 tool loop。

### 5. `test_tool_loop_keeps_deterministic_fallback_when_synthesis_fails()` 验证了什么？

验证当 final synthesis 返回空答案时：

- 不让整个 tool loop 失败
- `final_answer_source` 变成 `deterministic_fallback`
- 最终答案包含 fallback reason

## 练习 8：理解测试设计

### 1. `test_build_tool_loop_synthesis_messages_includes_observations()` 验证了什么？

验证 synthesis prompt 中包含：

- objective
- observation
- stop reason

也就是确保 LLM final synthesis 有足够上下文。

### 2. `test_synthesize_tool_loop_answer_returns_llm_content()` 验证了什么？

验证 `synthesize_tool_loop_answer()` 会返回 fake LLM client 的内容。

这说明 synthesis 调用链路是通的。

### 3. 为什么 synthesis 测试不调用真实 DeepSeek？

因为测试要可重复、快速、低成本。

真实 DeepSeek 有：

- 网络依赖
- API Key 依赖
- 响应随机性
- 成本

所以单元测试用 fake client。

### 4. v17 为什么要更新 v16 的 tool loop 测试？

因为 v17 改变了 tool loop 的最终答案来源。

v16 测试只需要验证 deterministic final answer。  
v17 需要验证：

- LLM final synthesis 成功
- fallback 生效
- trace 中出现 `final_answer_source`

### 5. 为什么测试里 fake client 需要多返回一个最终答案字符串？

因为 v17 tool loop 多了一次 LLM 调用。

前几次调用用于：

- 选择工具
- 决定停止

最后一次调用用于：

- final synthesis

所以 fake client 需要多返回一个 synthesis answer。

## 练习 9：对比三层 LLM 能力

### 1. `DeepSeekLLMClient` 负责什么？

负责真实 LLM 通信。

它封装：

- API URL
- API Key
- model
- chat request
- response parsing
- HTTP/network error

### 2. `tool_calling.py` 负责什么？

负责单次工具选择。

它让 LLM 基于 tool schema 输出结构化 JSON：

```text
action / tool_name / tool_input / reason
```

### 3. `tool_loop.py` 负责什么？

负责多步工具循环的数据结构。

它定义：

- `ToolLoopStep`
- `ToolLoopResult`

并记录每一步 selection、observation、error 和 stop reason。

### 4. `tool_synthesis.py` 负责什么？

负责最终答案综合。

它把 `ToolLoopResult` 转成 LLM messages，并请求 LLM 基于 observations 生成最终答案。

### 5. 这四层为什么不应该写在一个文件里？

因为职责不同：

- LLM client 是模型通信层
- tool calling 是工具选择层
- tool loop 是多步执行状态层
- tool synthesis 是最终回答层

分开后更容易：

- 测试
- 替换
- debug
- 扩展
- 复用

## 练习 10：失败定位

### 场景 1

```text
Final answer source: deterministic_fallback
Final synthesis fallback reason: Tool-loop final synthesis returned an empty answer.
```

问题在 final synthesis 层。

tool loop 已经完成，但最终 LLM synthesis 返回了空答案，因此触发 fallback。

### 场景 2

```text
step=1; action=use_tool; tool=count_lines; input=README.md; ok
Final answer source: llm
最终答案说 README.md 有 9999 行
```

问题在 final synthesis 层。

因为工具 observation 已经成功，但 LLM 最终综合时编造了错误数字。

应该验证：

1. trace 中 observation 的真实 line count。
2. synthesis prompt 是否明确要求保留关键数字。
3. 是否需要在最终答案中强制引用 observation。
4. 是否需要增加 eval 检查关键数字一致性。

### 场景 3

```text
step=1; action=use_tool; tool=count_lines; input=README.md; ok
step=2; action=answer_directly; tool=none; input=none; ok
Final answer source: llm
最终答案没有提到行数
```

问题更可能在 final synthesis prompt 或 synthesis 输出质量。

工具结果已经有行数，但最终答案没有保留关键数字，说明 synthesis 没有充分使用 observation。

### 场景 4

```text
Route request: tool_loop / llm_tool_loop
Tool loop failed before final synthesis
```

问题不在 synthesis 层。

因为 final synthesis 发生在 tool loop 成功返回 `ToolLoopResult` 之后。  
如果 tool loop 在此之前失败，问题更可能在：

- 工具选择层
- 工具参数层
- 工具执行层
- loop 控制层

## 练习 11：设计题

### 1. 如果 final synthesis 要支持引用来源，应该怎么改 `ToolLoopStep` 或 synthesis prompt？

可以给 `ToolLoopStep` 增加结构化来源字段，例如：

- `source_label`
- `tool_result_id`
- `observation_id`
- `artifact_path`

也可以在 synthesis prompt 中要求：

```text
When citing evidence, reference Step N and tool name.
```

例如：

```text
依据 Step 1 的 count_lines 结果，README.md 有 616 行。
```

### 2. 如果工具 observation 很长，应该如何控制 token？

可以：

- 限制 `_preview_observation()` 长度
- 对长工具结果做摘要
- 只保留关键字段
- 给 observation 做 source id
- 必要时把原文放在 artifact，prompt 只传引用

### 3. final synthesis 是否应该能再次调用工具？为什么？

一般不应该。

final synthesis 的职责是生成最终答案，不应该再执行工具。  
如果它发现信息不足，应该返回“不足”，或者由上游 loop 决定继续工具调用。

否则职责会混乱：

```text
tool loop controls actions
final synthesis writes answer
```

### 4. LangGraph 中 final synthesis 适合作为一个独立 node 吗？

适合。

合理结构：

```text
select_tool
-> execute_tool
-> observe
-> should_continue
-> final_synthesis
```

`final_synthesis` 是明确的终止节点。

### 5. 如果 MCP / Skills 进入 tool loop，final synthesis 需要额外说明什么？

需要说明：

- 哪些 observation 来自 MCP
- 哪些 observation 来自 Skill
- MCP 或 Skill 的可信边界
- 工具失败是否影响最终结论
- 是否有外部 side effect

例如 MCP 工具可能代表外部系统信息，Skill 可能代表可复用流程结果，这些都应该在 final answer 中透明表达。

## 练习 12：阶段验收

### 1. 能画出 v17 链路

```text
user input
-> route_intent
-> tool_loop branch
-> _run_tool_loop
-> LLM selects tool
-> local tool executes
-> observations collected
-> LLM decides stop
-> _synthesize_tool_loop_result
-> LLM final synthesis
-> fallback if needed
-> trace / final answer
```

### 2. 能解释核心概念

- `ToolLoopResult.final_answer`：最终答案正文。
- `ToolLoopResult.final_answer_source`：最终答案来源。
- `tool_synthesis.py`：把 tool loop observations 转成最终答案。
- `v17_tool-loop-synthesis.md`：约束 final synthesis 行为的 prompt。
- deterministic fallback：final synthesis 失败时的确定性回退。

### 3. 能跑通验证命令

```bash
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.tool_loop_demo --input "Use tool loop to count lines in README.md and then answer." --trace
```

### 4. 能判断失败发生在哪一层

需要能区分：

- tool selection
- tool execution
- observation compression
- final synthesis
- fallback
- final answer rendering

### 5. 能说明为什么 v17 比 v16 更接近真实 Agent，但仍然需要 MCP / Skills / LangGraph 的进一步整合

v17 更接近真实 Agent，因为它已经具备：

- 多步工具循环
- observation feedback
- LLM final synthesis
- fallback
- trace

但仍然需要继续整合：

- MCP：让外部协议工具进入 loop
- Skills：让可复用能力真正可执行
- LangGraph：让 loop 由图状态编排，而不是只放在 `WorkspaceAgent` 方法里

## 阶段结论

v17 的核心价值是把 tool loop 从“能跑工具”推进到“能基于工具证据生成最终答案”。

当前可靠边界是：

```text
Tools produce observations.
LLM synthesizes from observations.
Code provides fallback.
Trace exposes answer source.
```

下一阶段建议进入：

```text
MCP / Skills as first-class tool loop capabilities
```
