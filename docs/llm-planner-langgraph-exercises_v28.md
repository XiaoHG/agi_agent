# v28 练习：LLM Planner 接入 LangGraph

## 练习 1：为什么需要 LLM Planner？

回答：

1. 规则 route 和 LLM planner 的核心区别是什么？

   答案：规则 route 主要依赖关键词和固定条件判断，例如看到 `read` 或文件路径就走 `read_file`；LLM planner 则让模型先理解用户意图，再输出结构化 `GraphPlan`。前者稳定、可预测，但理解能力有限；后者更灵活，能处理更自然的表达，但必须经过代码校验。

2. 为什么专业 Agent 不应该长期只依赖关键词 route？

   答案：关键词 route 很容易被表达方式限制。例如用户说“帮我看一下项目入口文档”时，规则可能无法准确判断这是读取 `README.md`，但 LLM planner 更有机会理解语义。专业 Agent 需要处理真实用户输入，不能要求用户总是按固定关键词提问。

3. LLM planner 为什么不能直接执行工具？

   答案：LLM 输出不稳定，可能编造工具名、漏参数、给出危险或不符合协议的调用。正确边界是：LLM 只负责生成计划，代码负责验证计划，LangGraph 负责按受控路径执行工具。

## 练习 2：理解 `GraphPlan`

回答：

1. `GraphPlan` 中 `route` 和 `selected_tool` 的区别是什么？

   答案：`route` 表示 LangGraph 应该进入哪条执行分支，例如 `read_file`、`search_docs`、`skill_execution`；`selected_tool` 表示该分支实际调用哪个 LangChain tool，例如 `read_workspace_file`。`route` 是 graph 层决策，`selected_tool` 是工具执行层决策。

2. 为什么 `tool_input` 必须是结构化 dict？

   答案：结构化 dict 能明确表达工具参数，例如 `{"path": "README.md"}` 或 `{"question": "agent workflow"}`。如果只用一段自然语言字符串，后续节点还要再猜参数，容易产生歧义，也不利于测试、trace、checkpoint 和恢复。

3. `raw_response` 为什么要保留？

   答案：`raw_response` 用于调试 LLM planner 的原始输出。当解析失败、schema 不匹配或模型选择异常时，可以回看模型到底返回了什么，从而判断问题来自 prompt、模型输出、parser 还是校验规则。

## 练习 3：理解 planner prompt

回答：

1. `prompts/langgraph-planner.v1.md` 为什么要限制支持的 route？

   答案：限制 route 是为了把 LLM 的自由输出收敛到系统真正支持的执行路径。当前 LangGraph 只实现了 `read_file`、`search_docs`、`answer_docs_with_llm` 和 `skill_execution`，如果 prompt 不限制，模型可能返回不存在的 route，导致执行层不可控。

2. 为什么每个 route 都绑定固定 selected tool？

   答案：绑定固定 tool 可以保证 graph 分支和工具调用一致。例如 `read_file` 必须对应 `read_workspace_file`。这样代码可以做强校验，避免模型把 `read_file` route 绑定到错误工具，降低不可预测行为。

3. 如果模型返回了不存在的 route，代码应该怎么处理？

   答案：代码应该拒绝这个 plan，并抛出 `LLMError`。在当前实现中，LangGraph route node 会捕获这个错误，记录 `planner_status = deterministic_fallback` 和 `planner_error`，然后回到 deterministic route。

## 练习 4：理解 fallback

回答：

1. 什么情况下会进入 deterministic fallback？

   答案：当没有启用 planner client 时，会直接走 deterministic route；当启用了 planner client 但 LLM 请求失败、返回不是 JSON、缺字段、route 不支持、route 和 tool 不匹配、参数缺失时，会进入 deterministic fallback。

2. fallback 为什么不能只吞掉错误？

   答案：如果只吞掉错误，系统虽然可能继续运行，但 trace 中看不到 planner 曾经失败，后续就无法定位问题。专业 Agent 需要保留失败证据，否则调试、评估和恢复都会失去依据。

3. `planner_status` 和 `planner_error` 对 trace 有什么价值？

   答案：`planner_status` 说明本次 route 是 LLM planner 生成的，还是 deterministic route 或 fallback 生成的；`planner_error` 记录 planner 失败原因。它们让开发者能快速判断问题发生在规划层、校验层还是工具执行层。

## 练习 5：理解 LangGraph 集成方式

回答：

1. 为什么 planner 放在 route node，而不是 call_tool node？

   答案：planner 的职责是决定 graph 走哪条路径，所以它应该位于 route node。`call_tool` node 的职责是执行已经选定的工具，如果把 planner 放到 `call_tool`，就会混淆“规划”和“执行”的边界。

2. planner 成功后，LangGraph 的后续节点是否需要知道这个 plan 来自 LLM？

   答案：后续节点不需要依赖“来自 LLM”这个事实来决定执行逻辑，它们只需要读取标准化后的 state，例如 `route`、`selected_tool` 和 `tool_input`。但 trace 和 metadata 需要保留 `planner_status`，方便调试和复盘。

3. 这个设计如何为后续“默认 LangGraph 主执行器”打基础？

   答案：它把“理解用户意图并规划路径”的能力放进了 graph state，而不是停留在外层 if/else。后续如果要让 LangGraph 成为主执行器，就可以继续扩展 planner、state、node 和 edge，而不需要重写整个 Agent 主循环。

## 练习 6：手动验证

完成下面命令，并记录你看到的关键输出：

```bash
python -m unittest tests.test_langgraph_workflow -v
python -m cli.eval_runner
python -m cli.langgraph_demo --question "Read README.md."
```

如果你本地配置了 `DEEPSEEK_API_KEY`，再运行：

```bash
python -m cli.langgraph_demo --question "Read README.md." --llm-planner
```

回答：

1. 未启用 `--llm-planner` 时，`Planner status` 是什么？

   答案：未启用 `--llm-planner` 时，`Planner status` 通常是 `deterministic_route`，表示 graph route 由原来的规则路径产生，没有调用真实 DeepSeek planner。

2. 启用 `--llm-planner` 后，`Planner status` 是什么？

   答案：如果 DeepSeek planner 调用成功，并且模型输出通过 `GraphPlan` 校验，`Planner status` 应该是 `llm_planned`。如果 LLM 调用失败或输出不合法，则会变成 `deterministic_fallback`。

3. 如果 LLM 输出不合法，系统应该如何表现？

   答案：系统不应该崩溃，也不应该执行不合法 plan。正确表现是记录 planner 错误，设置 `planner_status = deterministic_fallback`，然后使用 deterministic route 继续完成任务。
