# LangGraph 条件路由与多工具编排阶段练习答案

本文档用于复盘 v13：LangGraph 条件路由与多工具编排阶段。

本阶段目标是理解 LangGraph 从“固定顺序 workflow”升级为“根据 state 做条件路由”。

当前 graph：

```text
START
  -> route
  -> conditional edge
  -> call_tool
  -> finalize
  -> END
```

当前支持三条工具分支：

```text
read_file              -> read_workspace_file
search_docs            -> search_workspace_docs
answer_docs_with_llm   -> answer_workspace_docs_with_llm
```

## 练习 1：运行三条 LangGraph 路由

依次运行：

```bash
python -m cli.langgraph_demo --question "Read README.md."
```

```bash
python -m cli.langgraph_demo --question "Search docs for MCP."
```

```bash
python -m cli.langgraph_demo --question "What does MCP mean in this project?"
```

### 1. 三条命令分别输出什么 `Route`？

第一条：

```text
Read README.md. -> Route: read_file
```

第二条：

```text
Search docs for MCP. -> Route: search_docs
```

第三条：

```text
What does MCP mean in this project? -> Route: answer_docs_with_llm
```

### 2. 三条命令分别输出什么 `Selected tool`？

第一条：

```text
read_workspace_file
```

第二条：

```text
search_workspace_docs
```

第三条：

```text
answer_workspace_docs_with_llm
```

### 3. 三条命令的 `Steps` 是否一样？

一样。

当前三条路径都会经过：

```text
route -> call_tool -> finalize
```

区别在于 `route` 节点写入的 `selected_tool` 和 `tool_input` 不同。

### 4. 哪一条会调用 deterministic RAG？

这一条：

```bash
python -m cli.langgraph_demo --question "Search docs for MCP."
```

它选择：

```text
search_workspace_docs
```

对应 deterministic RAG，只返回检索上下文，不调用 DeepSeek。

### 5. 哪一条可能调用真实 DeepSeek？

这一条：

```bash
python -m cli.langgraph_demo --question "What does MCP mean in this project?"
```

它选择：

```text
answer_workspace_docs_with_llm
```

如果本地检索命中 context，就会调用 DeepSeek 生成 grounded answer。

### 6. 哪一条是文件读取？

这一条：

```bash
python -m cli.langgraph_demo --question "Read README.md."
```

它选择：

```text
read_workspace_file
```

## 练习 2：对比 v12 和 v13

### 1. v12 的 `prepare()` 做了什么？

v12 的 `prepare()` 固定选择一个工具：

```text
answer_workspace_docs_with_llm
```

它只做：

```text
1. 追加 steps: prepare
2. 设置 selected_tool
```

### 2. 为什么 v12 固定选择 `answer_workspace_docs_with_llm` 是合理的？

因为 v12 的目标不是工具选择，而是验证：

```text
真实 LangGraph StateGraph
  -> LangChain StructuredTool
  -> DeepSeek-grounded RAG
```

为了降低复杂度，固定选择一个工具是合理的。

### 3. v13 为什么不再使用 `prepare()`？

因为 v13 的目标变成了：

```text
条件路由与多工具编排
```

固定 `prepare()` 无法根据用户问题选择不同工具。

所以 v13 用 `route()` 替代 `prepare()`。

### 4. v13 的 `route()` 比 v12 的 `prepare()` 多了哪些 state 字段？

多了：

```text
route
route_reason
tool_input
```

并且 `selected_tool` 不再固定，而是根据问题变化。

### 5. 如果 v13 继续固定选工具，会有什么问题？

会导致所有问题都走 DeepSeek RAG。

例如：

```text
Read README.md.
```

也会走：

```text
answer_workspace_docs_with_llm
```

这会带来：

- 工具选择错误
- 不必要的 LLM 调用
- 成本增加
- 响应不符合用户意图
- graph 条件路由没有实际意义

## 练习 3：阅读 `RAGGraphState`

### 1. `route` 和 `selected_tool` 有什么区别？

`route` 是 graph 的语义路由结果。

例如：

```text
read_file
search_docs
answer_docs_with_llm
```

`selected_tool` 是实际要调用的 LangChain tool 名称。

例如：

```text
read_workspace_file
search_workspace_docs
answer_workspace_docs_with_llm
```

关系：

```text
route = 决策意图
selected_tool = 具体执行工具
```

### 2. `route_reason` 的作用是什么？

`route_reason` 解释为什么选择这条 route。

价值：

- 调试路由结果
- 让 trace 更容易理解
- 后续做 eval 时可以检查路由原因
- 用户可以理解 graph 为什么选择某个工具

### 3. `tool_input` 为什么要单独保存？

因为不同工具需要不同输入结构。

例如：

```text
read_workspace_file -> {"path": "README.md"}
search_workspace_docs -> {"question": "..."}
answer_workspace_docs_with_llm -> {"question": "..."}
```

如果只保存原始 question，`call_tool()` 就无法统一调用不同工具。

### 4. `tool_output` 和 `answer` 为什么仍然分开？

`tool_output` 是工具原始输出。

`answer` 是 graph 最终回答。

当前成功时两者基本一致，但未来 `finalize()` 可以对 `tool_output` 做：

- 格式化
- 摘要
- citation 校验
- 多工具输出合并
- 错误包装

所以分开更合理。

### 5. 哪些字段是输入？哪些字段是中间状态？哪些字段是最终输出？

输入字段：

```text
question
steps
```

中间状态：

```text
route
route_reason
selected_tool
tool_input
tool_output
error
steps
```

最终输出：

```text
answer
steps
route
route_reason
selected_tool
```

## 练习 4：理解 `route()` 节点

### 1. `route()` 当前按什么顺序判断？

当前顺序：

```text
1. 判断是否是文件读取
2. 判断是否是只搜索上下文
3. 默认走 DeepSeek-grounded RAG
```

代码逻辑：

```python
if _looks_like_file_read(question):
    ...

if _looks_like_search_only(lowered):
    ...

return answer_docs_with_llm
```

### 2. 为什么先判断文件读取，再判断搜索？

因为文件读取是更具体的操作。

例如：

```text
Show README.md.
```

既可能包含 `show`，也可能被误认为搜索/展示上下文。

先判断文件路径可以更准确地识别：

```text
用户要读取具体文件
```

### 3. `_looks_like_search_only()` 识别哪些请求？

当前关键词：

```text
find docs
find local context
search docs
search local context
show context
show sources
```

这些请求表示用户更想看检索证据，而不是要 LLM 综合答案。

### 4. `_looks_like_file_read()` 如何判断是否读文件？

它判断两个条件：

```text
1. 问题里包含 read / open / show
2. 能提取出文件路径
```

代码含义：

```python
("read" in lowered or "open" in lowered or "show" in lowered) 
and _extract_file_path(question) != "."
```

### 5. `_extract_file_path()` 当前支持哪些文件后缀？

当前支持：

```text
md
txt
py
json
toml
yaml
yml
```

对应正则：

```python
(?:md|txt|py|json|toml|yaml|yml)
```

### 6. 默认分支为什么走 `answer_docs_with_llm`？

因为如果用户不是明确读文件，也不是明确搜索上下文，那么通常是在问：

```text
解释 / 回答 / 总结 / 什么是 / 为什么
```

这类问题更适合：

```text
检索本地 context -> DeepSeek 生成 grounded answer
```

所以默认走：

```text
answer_docs_with_llm
```

## 练习 5：理解条件边

重点代码：

```python
graph.add_conditional_edges(
    "route",
    _next_after_route,
    {
        "call_tool": "call_tool",
        "finalize": "finalize",
    },
)
```

### 1. `add_conditional_edges()` 的 source node 是哪个？

source node 是：

```text
route
```

表示 `route` 节点执行后，根据条件决定下一步。

### 2. `_next_after_route()` 返回什么？

当前返回：

```text
call_tool
```

如果 state 中有 error，则返回：

```text
finalize
```

代码：

```python
if state.get("error"):
    return "finalize"
return "call_tool"
```

### 3. 什么情况下会直接进入 `finalize`？

当 `route` 节点产生错误时。

当前 v13 中 route 节点还没有主动写入 error，但这个结构为后续扩展预留了空间。

例如未来：

```text
无法识别工具
权限不允许
缺少必要输入
```

都可以直接进入 `finalize`。

### 4. 当前正常情况下会进入哪个节点？

当前正常情况下会进入：

```text
call_tool
```

### 5. 为什么这比普通 `add_edge("route", "call_tool")` 更灵活？

普通 edge 是固定路径。

conditional edge 可以根据 state 动态选择下一步。

未来可以扩展成：

```text
route -> call_tool
route -> ask_clarification
route -> permission_check
route -> finalize
```

这就是 LangGraph 的核心价值之一。

## 练习 6：理解 `call_tool()` 变化

### 1. v12 中 `call_tool()` 的 `.invoke()` 输入是什么？

v12 固定传入：

```python
{"question": state["question"]}
```

因为 v12 固定调用：

```text
answer_workspace_docs_with_llm
```

它只需要 `question`。

### 2. v13 中 `.invoke()` 输入变成了什么？

v13 变成：

```python
tool.invoke(state["tool_input"])
```

### 3. 为什么 v13 需要 `state["tool_input"]`？

因为不同工具需要不同参数。

例如：

```text
read_workspace_file -> {"path": "README.md"}
search_workspace_docs -> {"question": "..."}
answer_workspace_docs_with_llm -> {"question": "..."}
```

所以必须让 route 节点同时决定：

```text
selected_tool
tool_input
```

### 4. `read_workspace_file` 需要什么输入？

需要：

```python
{"path": "README.md"}
```

### 5. `search_workspace_docs` 和 `answer_workspace_docs_with_llm` 需要什么输入？

都需要：

```python
{"question": "..."}
```

区别在于：

```text
search_workspace_docs 只检索
answer_workspace_docs_with_llm 会调用 DeepSeek 生成 grounded answer
```

## 练习 7：理解测试文件

阅读：

```text
tests/test_langgraph_workflow.py
```

### 1. `test_rag_graph_routes_to_search_docs` 验证什么？

验证问题：

```text
Search docs for agent workflow.
```

会被路由到：

```text
route = search_docs
selected_tool = search_workspace_docs
```

并返回：

```text
relevant local context
```

### 2. `test_rag_graph_routes_to_read_file` 验证什么？

验证问题：

```text
Read README.md.
```

会被路由到：

```text
route = read_file
selected_tool = read_workspace_file
```

并返回：

```text
[read_file] README.md
```

### 3. `test_rag_graph_records_route_reason` 为什么重要？

因为 route 结果不应该只是一个工具名。

还应该记录：

```text
为什么选择这个工具
```

这对调试、trace、eval 和学习都重要。

### 4. `test_rag_graph_handles_no_context_without_network` 为什么仍然重要？

因为默认分支会走：

```text
answer_workspace_docs_with_llm
```

这可能触发真实 DeepSeek。

测试使用：

```text
the and of
```

确保无有效 query terms，从而不触发真实网络。

### 5. 这些测试有没有调用真实 DeepSeek？为什么？

没有。

原因：

- 测试使用临时目录
- no-context case 不触发 LLM
- search/read file 都是本地工具

默认测试必须保持：

```text
快速
稳定
无网络
无 API 成本
```

## 练习 8：画出当前 v13 graph

当前 graph：

```text
START
  -> route
     -> if file read
        route: read_file
        selected_tool: read_workspace_file
        tool_input: {"path": "..."}
        适用场景: 读取具体文件

     -> if search only
        route: search_docs
        selected_tool: search_workspace_docs
        tool_input: {"question": "..."}
        适用场景: 查看本地检索上下文和 sources

     -> default
        route: answer_docs_with_llm
        selected_tool: answer_workspace_docs_with_llm
        tool_input: {"question": "..."}
        适用场景: 基于本地 context 生成 DeepSeek grounded answer

  -> conditional edge
     -> call_tool
     -> finalize
  -> END
```

更完整的流程：

```text
START
  -> route
      writes: route, route_reason, selected_tool, tool_input, steps
  -> _next_after_route
      if error -> finalize
      else -> call_tool
  -> call_tool
      invokes selected_tool with tool_input
      writes: tool_output or error
  -> finalize
      writes: answer
  -> END
```

## 练习 9：评估当前 v13 的限制

### 限制 1

限制：路由仍然是规则判断。

原因：当前通过关键词和文件路径正则判断。

后续改进：引入 LLM router，输出结构化 route。

### 限制 2

限制：没有 LLM router。

原因：当前 `route()` 不调用 DeepSeek，只用规则分支。

后续改进：让 DeepSeek 根据工具描述和用户问题选择 route。

### 限制 3

限制：没有 graph-level eval。

原因：当前 eval 主要覆盖 `WorkspaceAgent`，没有专门评估 LangGraph route。

后续改进：新增 graph eval cases，例如 read/search/answer 三类 case。

### 限制 4

限制：还没有接入 WorkspaceAgent。

原因：LangGraph 当前是独立 CLI demo，没有成为主 Agent 的执行后端。

后续改进：新增 `WorkspaceAgent.run_with_graph()` 或 graph tool。

### 限制 5

限制：没有 checkpoint。

原因：当前 graph 没有持久化状态。

后续改进：引入 LangGraph checkpointer。

### 限制 6

限制：没有 streaming。

原因：当前使用同步 `.invoke()`。

后续改进：使用 LangGraph streaming 输出节点事件。

### 限制 7

限制：没有工具错误分类。

原因：当前 error 只是字符串。

后续改进：定义 `error_type`、`retryable`、`tool_name` 等结构化错误字段。

### 限制 8

限制：没有权限 / 成本 / 网络策略。

原因：虽然 LangChain tool metadata 已经标记了部分网络依赖，但 graph route 还没有使用这些 metadata。

后续改进：route 时根据 metadata 判断是否允许调用网络工具。

### 限制 9

限制：没有多轮 state。

原因：当前 state 只有单轮 `question`。

后续改进：增加 messages、history、thread_id。

### 限制 10

限制：工具分支还较少。

原因：当前只支持 read、search、answer 三类。

后续改进：加入 MCP、Skills、Subagents 分支。

## 练习 10：设计下一阶段 v14

下一阶段建议：

```text
v14：LangGraph 与 WorkspaceAgent 集成
```

### 1. 为什么 v13 之后要把 LangGraph 接回 `WorkspaceAgent`？

因为当前 LangGraph 仍然是独立 demo。

主 Agent 入口仍然是：

```text
cli.main -> WorkspaceAgent.run()
```

如果 LangGraph 不接回主 Agent，它只是旁路能力。

接回后才能进入：

- 主路由
- trace
- eval
- project assistant
- 统一 CLI

### 2. 应该新增一个 `run_with_graph()`，还是替换 `WorkspaceAgent.run()`？为什么？

建议新增：

```python
WorkspaceAgent.run_with_graph()
```

不要直接替换 `run()`。

原因：

- 保留原 deterministic path
- 避免破坏已有测试和 eval
- 便于对比普通 Agent 和 LangGraph Agent
- 符合渐进式工程迭代

### 3. 路由中应该如何识别“使用 LangGraph 执行”的请求？

可以先用明确触发词：

```text
Use LangGraph ...
Run with LangGraph ...
Use graph ...
Graph answer ...
```

例如：

```text
Use LangGraph to search docs for MCP.
Use LangGraph to read README.md.
Use LangGraph to answer what MCP means in this project.
```

### 4. trace 应该记录哪些 graph 信息？

建议记录：

```text
graph name
route
route_reason
selected_tool
tool_input
steps
answer preview
error
```

### 5. eval 应该新增哪些 graph case？

建议新增：

```text
langgraph-read-readme
langgraph-search-mcp
langgraph-answer-no-context
```

默认 eval 仍然应避免真实 DeepSeek。

真实 DeepSeek graph eval 可以单独运行。

### 6. 应该修改哪些文件？

建议修改：

```text
agent/router.py
agent/core.py
tests/test_agent.py
evals/regression_cases.json
README.md
docs/current-learning-state.md
```

### 7. 应该新增哪些测试？

建议新增：

```text
test_route_to_langgraph
test_agent_runs_langgraph_search
test_agent_runs_langgraph_read_file
test_agent_runs_langgraph_no_context
test_trace_includes_graph_steps
```

### 8. 应该新增哪些验证命令？

建议新增：

```bash
python -m cli.main --input "Use LangGraph to search docs for MCP." --trace
python -m cli.main --input "Use LangGraph to read README.md." --trace
python -m cli.main --input "Use LangGraph to answer: the and of" --trace
```

继续保留：

```bash
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.langgraph_demo --question "Search docs for MCP."
```

## 本阶段最低通过标准

完成 v13 后，你应该能讲清：

1. v12 固定 `prepare()` 和 v13 条件 `route()` 的区别。
2. `route`、`selected_tool`、`tool_input` 三者的关系。
3. `add_conditional_edges()` 为什么是 LangGraph 的关键能力。
4. 三条工具分支分别适合什么场景。
5. 当前 v13 仍然只是规则路由，不是 LLM router。
6. 下一阶段为什么要把 LangGraph 接入 `WorkspaceAgent`。
