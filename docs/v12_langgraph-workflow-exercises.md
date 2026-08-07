# LangGraph Workflow 阶段练习答案

本文档用于复盘 v12：LangGraph Workflow 阶段。

本阶段目标是理解如何从“工具适配层”进入“专业状态图编排”。

当前 graph：

```text
prepare -> call_tool -> finalize
```

核心链路：

```text
cli.langgraph_demo
  -> run_rag_graph()
  -> build_rag_graph()
  -> StateGraph(RAGGraphState)
  -> prepare node
  -> call_tool node
  -> finalize node
  -> graph.compile()
  -> graph.invoke()
```

## 练习 1：运行 LangGraph Demo

运行无真实网络版本：

```bash
python -m cli.langgraph_demo --question "the and of"
```

### 1. 输出中的 `Selected tool` 是什么？

输出中的 `Selected tool` 是：

```text
answer_workspace_docs_with_llm
```

它来自 `prepare()` 节点：

```python
"selected_tool": "answer_workspace_docs_with_llm"
```

### 2. 输出中的 `Steps` 是什么？

输出中的 `Steps` 是：

```text
prepare -> call_tool -> finalize
```

这说明 LangGraph 依次执行了三个节点。

对应 state 字段：

```python
steps: list[str]
```

每个节点都会把自己的名字追加到 `steps` 中。

### 3. 为什么这个问题不会触发真实 DeepSeek？

因为问题是：

```text
the and of
```

这些词都是检索停用词。

在 retrieval 阶段，query 会被 tokenize，并过滤 stopwords。过滤后没有有效 query terms，因此不会命中任何本地 context。

无 context 时，`answer_question_with_llm()` 会直接返回：

```text
The local context is insufficient to answer this question.
```

它不会调用 `DeepSeekLLMClient.chat()`。

### 4. 这个命令最终调用的是普通 Python workflow，还是 LangGraph compiled graph？

调用的是 LangGraph compiled graph。

流程：

```text
run_rag_graph()
  -> build_rag_graph()
  -> graph.compile()
  -> graph.invoke(...)
```

所以它不是自定义普通 workflow，而是真实 `langgraph` 的 compiled graph。

### 5. 和 `python -m cli.rag_llm_demo --question "the and of"` 相比，v12 多了什么？

`cli.rag_llm_demo` 直接调用：

```text
answer_question_with_llm()
```

v12 的 `cli.langgraph_demo` 多了：

```text
StateGraph
state
nodes
edges
compile
invoke
steps tracking
selected_tool
```

也就是说，v12 把 RAG 能力放进了专业状态图编排框架中。

## 练习 2：阅读 `integrations/langgraph_workflow.py`

### 1. `RAGGraphState` 里有哪些字段？

当前字段：

```text
question
selected_tool
tool_output
answer
error
steps
```

定义位置：

```python
class RAGGraphState(TypedDict, total=False):
```

`total=False` 表示这些字段不要求一开始全部存在。

### 2. `question` 的作用是什么？

`question` 是用户输入的问题。

它会在 `call_tool()` 节点中传给 LangChain tool：

```python
tool.invoke({"question": state["question"]})
```

### 3. `selected_tool` 的作用是什么？

`selected_tool` 记录当前 graph 选择了哪个工具。

当前固定为：

```text
answer_workspace_docs_with_llm
```

它由 `prepare()` 节点写入，然后由 `call_tool()` 节点读取。

### 4. `tool_output` 和 `answer` 有什么区别？

`tool_output` 是工具原始输出。

`answer` 是 graph 最终输出。

当前版本中，成功时：

```python
"answer": state.get("tool_output", "")
```

所以两者内容基本一致。

但保留两个字段有工程价值：

```text
tool_output = 中间结果
answer = 最终面向用户输出
```

后续 `finalize()` 可以对多个工具结果做汇总、格式化或错误处理。

### 5. `steps` 为什么要存在？

`steps` 用于记录 graph 执行轨迹。

当前会记录：

```text
prepare
call_tool
finalize
```

价值：

- 调试 graph 流程
- 验证节点执行顺序
- 为后续 trace / observability 做基础
- 测试 graph 是否按预期执行

### 6. `error` 字段什么时候会出现？

当 `call_tool()` 调用工具失败时会出现。

代码：

```python
except Exception as error:
    return {
        **state,
        "error": str(error),
        "steps": steps,
    }
```

之后 `finalize()` 会检查：

```python
if state.get("error"):
```

然后生成：

```text
Graph failed: ...
```

## 练习 3：理解 LangGraph 的基本结构

### 1. `StateGraph(RAGGraphState)` 的作用是什么？

`StateGraph(RAGGraphState)` 创建一个以 `RAGGraphState` 为状态结构的 LangGraph。

它表示：

```text
这个 graph 的每个节点都会接收 state，并返回 state 更新
```

### 2. `graph.add_node("prepare", prepare)` 做了什么？

它把 Python 函数 `prepare` 注册成 graph 节点。

节点名是：

```text
prepare
```

后续 edge 会通过节点名连接执行流程。

### 3. `graph.add_edge(START, "prepare")` 表示什么？

表示 graph 从 LangGraph 的起点进入 `prepare` 节点。

执行入口：

```text
START -> prepare
```

### 4. `graph.add_edge("finalize", END)` 表示什么？

表示 `finalize` 执行结束后，graph 到达终点。

执行出口：

```text
finalize -> END
```

### 5. `graph.compile()` 的作用是什么？

`compile()` 把 graph 定义编译成可执行对象。

只有 compile 后，才能调用：

```python
compiled_graph.invoke(...)
```

### 6. `graph.invoke(...)` 的输入输出是什么？

输入是初始 state：

```python
{"question": question, "steps": []}
```

输出是 graph 执行完后的最终 state。

最终 state 通常包含：

```text
question
selected_tool
tool_output
answer
steps
```

如果出错，还会包含：

```text
error
```

## 练习 4：理解三个节点

### prepare node

#### 1. `prepare()` 当前做了什么？

它做两件事：

```text
1. 把 prepare 加入 steps。
2. 设置 selected_tool = answer_workspace_docs_with_llm。
```

代码：

```python
return {
    **state,
    "selected_tool": "answer_workspace_docs_with_llm",
    "steps": steps,
}
```

#### 2. 为什么它把 `selected_tool` 固定成 `answer_workspace_docs_with_llm`？

因为 v12 是最小 LangGraph workflow。

当前目标不是多工具选择，而是先验证：

```text
LangGraph 能否调用 LangChain tool adapter
```

所以先固定工具，降低复杂度。

#### 3. 这一步以后可以如何升级？

后续可以升级为条件路由：

```text
如果问题是“搜索/查找上下文” -> search_workspace_docs
如果问题是“回答/解释” -> answer_workspace_docs_with_llm
如果问题是“读文件” -> read_workspace_file
```

也可以升级为 LLM router，让模型选择工具。

### call_tool node

#### 1. `call_tool()` 如何找到 LangChain tool？

`build_rag_graph()` 中先构建工具字典：

```python
tools = {tool.name: tool for tool in build_langchain_tools(root)}
```

`call_tool()` 读取：

```python
tool_name = state["selected_tool"]
tool = tools[tool_name]
```

### 2. 它调用 `.invoke()` 时传入了什么？

传入：

```python
{"question": state["question"]}
```

这是 `answer_workspace_docs_with_llm` 对应的 `QuestionInput` schema。

#### 3. 如果工具执行成功，state 会新增什么？

成功时新增：

```text
tool_output
steps
```

代码：

```python
return {
    **state,
    "tool_output": output,
    "steps": steps,
}
```

#### 4. 如果工具抛异常，state 会新增什么？

失败时新增：

```text
error
steps
```

代码：

```python
return {
    **state,
    "error": str(error),
    "steps": steps,
}
```

#### 5. 为什么这里要捕获异常而不是直接抛出？

因为 graph workflow 需要把错误变成 state。

这样后续 `finalize()` 可以统一处理：

```text
成功 -> 输出 tool_output
失败 -> 输出 Graph failed
```

如果直接抛出异常，graph 会中断，CLI 也难以输出结构化结果。

### finalize node

#### 1. `finalize()` 成功时做什么？

成功时把 `tool_output` 作为最终 `answer`：

```python
"answer": state.get("tool_output", "")
```

并追加：

```text
finalize
```

到 `steps`。

#### 2. `finalize()` 失败时做什么？

失败时生成：

```text
Graph failed: <error>
```

代码：

```python
"answer": f"Graph failed: {state['error']}"
```

#### 3. 为什么最终 answer 不直接在 `call_tool()` 里返回？

因为 `call_tool()` 的职责应该是执行工具。

`finalize()` 的职责是生成最终输出。

分开之后，后续可以在 `finalize()` 中做：

- 多工具结果汇总
- 格式化
- citation 校验
- 错误包装
- trace 输出

#### 4. 单独保留 `finalize()` node 有什么工程价值？

工程价值：

- 职责分离
- 易于测试
- 方便以后扩展输出逻辑
- 支持多节点结果统一收敛
- 更符合 graph workflow 结构

## 练习 5：理解测试文件

阅读：

```text
tests/test_langgraph_workflow.py
```

### 1. `test_build_rag_graph_returns_invokable_graph` 验证什么？

验证 `build_rag_graph()` 返回的是可执行 graph。

检查：

```python
self.assertTrue(hasattr(graph, "invoke"))
```

这说明 graph 已经 compile 成可 invoke 的对象。

### 2. `test_rag_graph_handles_no_context_without_network` 为什么使用 `"the and of"`？

因为 `"the and of"` 都是 stopwords。

检索时会被过滤，没有有效 query terms，因此不会命中 context，也不会调用 DeepSeek。

这样测试可以验证 graph 流程，同时保持：

```text
无网络
无 API 成本
稳定可重复
```

### 3. 它验证了哪些 state 字段？

它验证：

```text
selected_tool
steps
answer
error
```

具体：

```python
self.assertEqual(result["selected_tool"], "answer_workspace_docs_with_llm")
self.assertEqual(result["steps"], ["prepare", "call_tool", "finalize"])
self.assertIn("insufficient", result["answer"])
self.assertNotIn("error", result)
```

### 4. `test_rag_graph_records_tool_errors` 当前验证什么？

它验证 graph 在某些边界情况下仍然返回 state，并包含：

```text
selected_tool
answer
```

当前这个测试还比较弱，后续可以通过注入错误工具或错误 tool name 来更明确地测试 error 分支。

### 5. 为什么这些测试不应该默认调用真实 DeepSeek？

因为默认测试应该：

```text
快速
稳定
无网络依赖
无 API 成本
不依赖 API Key
```

真实 DeepSeek 调用应该通过手动 smoke test 或独立 integration test 验证。

## 练习 6：对比三种调用方式

运行：

```bash
python -m cli.rag_llm_demo --question "the and of"
```

```bash
python -m cli.main --input "Answer with local docs and DeepSeek RAG: the and of" --trace
```

```bash
python -m cli.langgraph_demo --question "the and of"
```

### 1. 三个命令分别经过哪些层？

`cli.rag_llm_demo`：

```text
CLI -> rag.answer_question_with_llm -> retrieval -> answer
```

`cli.main`：

```text
CLI -> WorkspaceAgent -> router -> tool dispatch -> answer_docs_with_llm -> retrieval -> answer -> trace
```

`cli.langgraph_demo`：

```text
CLI -> run_rag_graph -> LangGraph StateGraph -> LangChain tool -> answer_docs_with_llm -> retrieval -> answer
```

### 2. 哪个命令最接近底层 RAG 能力？

最接近底层 RAG 能力的是：

```bash
python -m cli.rag_llm_demo --question "the and of"
```

它直接调用 RAG + LLM 能力，不经过 Agent router 或 graph。

### 3. 哪个命令经过 `WorkspaceAgent`？

经过 `WorkspaceAgent` 的是：

```bash
python -m cli.main --input "Answer with local docs and DeepSeek RAG: the and of" --trace
```

### 4. 哪个命令经过 LangGraph？

经过 LangGraph 的是：

```bash
python -m cli.langgraph_demo --question "the and of"
```

### 5. 三者分别适合什么调试场景？

`cli.rag_llm_demo` 适合：

```text
调试 RAG + LLM 能力本身
```

`cli.main` 适合：

```text
调试主 Agent 路由、工具调用、trace
```

`cli.langgraph_demo` 适合：

```text
调试 LangGraph state、node、edge、graph execution
```

## 练习 7：手动画出 v12 graph

当前 graph：

```text
START
  -> prepare
  -> call_tool
  -> finalize
  -> END
```

### START

输入字段：

```text
question
steps
```

输出字段：

```text
不直接输出，由 LangGraph 进入 prepare
```

主要职责：

```text
graph 起点
```

### prepare

输入字段：

```text
question
steps
```

输出字段：

```text
selected_tool
steps
```

主要职责：

```text
选择当前要调用的工具
记录 prepare step
```

### call_tool

输入字段：

```text
question
selected_tool
steps
```

输出字段：

成功：

```text
tool_output
steps
```

失败：

```text
error
steps
```

主要职责：

```text
调用 LangChain StructuredTool
保存工具输出或错误
```

### finalize

输入字段：

```text
tool_output
error
steps
```

输出字段：

```text
answer
steps
```

主要职责：

```text
将中间结果整理成最终答案
```

### END

输入字段：

```text
最终 state
```

输出字段：

```text
graph.invoke() 返回最终 state
```

主要职责：

```text
graph 终点
```

## 练习 8：评估当前 v12 的限制

### 限制 1

限制：没有条件路由。

原因：当前 graph 固定执行 `prepare -> call_tool -> finalize`。

后续改进：使用 conditional edges，根据问题类型选择不同分支。

### 限制 2

限制：没有多个工具选择。

原因：`prepare()` 固定选择 `answer_workspace_docs_with_llm`。

后续改进：根据问题选择：

```text
search_workspace_docs
answer_workspace_docs_with_llm
read_workspace_file
```

### 限制 3

限制：没有 LLM router。

原因：当前不调用模型判断工具选择。

后续改进：引入 DeepSeek 作为 router，输出结构化 selected_tool。

### 限制 4

限制：没有 checkpoint。

原因：当前 graph 没有配置 checkpointer。

后续改进：使用 LangGraph checkpoint 机制保存中间状态。

### 限制 5

限制：没有 persistence。

原因：graph 执行结果只在内存中返回，没有写入存储。

后续改进：将 graph state 保存到 logs 或数据库。

### 限制 6

限制：没有 streaming。

原因：当前使用同步 `.invoke()`，没有 stream graph events。

后续改进：使用 LangGraph streaming 能力，逐步输出节点结果。

### 限制 7

限制：没有真实 tool error 分类。

原因：当前只是 `str(error)`。

后续改进：定义 error type，例如 network_error、tool_error、validation_error。

### 限制 8

限制：没有 graph-level eval。

原因：当前 eval 主要覆盖 `WorkspaceAgent`，没有专门评估 LangGraph workflow。

后续改进：新增 graph eval cases。

### 限制 9

限制：没有多轮状态。

原因：当前 state 只包含单轮 question。

后续改进：增加 messages/history/thread_id。

### 限制 10

限制：还没有接入 `WorkspaceAgent`。

原因：当前 LangGraph 是独立 integration demo。

后续改进：让 `WorkspaceAgent` 可以选择 LangGraph workflow 作为执行后端。

## 练习 9：设计下一阶段 v13

下一阶段建议：

```text
v13：LangGraph 条件路由与多工具编排
```

### 1. 为什么 v12 之后应该做条件路由？

因为 v12 只是固定流程。

LangGraph 的核心价值在于：

```text
根据状态决定下一步走哪个节点
```

如果不做条件路由，graph 只是普通顺序 workflow。

### 2. 当前 graph 应该新增哪些工具分支？

建议新增：

```text
search_workspace_docs
answer_workspace_docs_with_llm
read_workspace_file
```

后续再加：

```text
list_workspace_directory
plan_workspace_subagents
```

### 3. 应该如何决定走 `search_workspace_docs` 还是 `answer_workspace_docs_with_llm`？

初始可以用规则：

```text
如果问题包含 search / find / context / sources -> search_workspace_docs
如果问题包含 answer / explain / what does / why -> answer_workspace_docs_with_llm
```

后续可以用 LLM router。

### 4. graph state 应该新增哪些字段？

建议新增：

```text
route
route_reason
available_tools
tool_input
sources
metadata
```

### 5. 应该新增哪些文件？

建议新增：

```text
versions/v13_langgraph-conditional-routing.md
```

如果 v13 内容较大，也可以新增：

```text
integrations/langgraph_routing.py
```

但优先可以在 `integrations/langgraph_workflow.py` 内小步迭代。

### 6. 应该修改哪些文件？

建议修改：

```text
integrations/langgraph_workflow.py
cli/langgraph_demo.py
tests/test_langgraph_workflow.py
README.md
docs/current-learning-state.md
```

### 7. 应该新增哪些测试？

建议新增：

```text
test_langgraph_routes_to_search_docs
test_langgraph_routes_to_llm_rag
test_langgraph_routes_to_read_file
test_langgraph_records_route_reason
test_langgraph_handles_unknown_route
```

### 8. 应该新增哪些验证命令？

建议新增或继续使用：

```bash
python -m cli.langgraph_demo --question "Search docs for MCP."
python -m cli.langgraph_demo --question "What does MCP mean in this project?"
python -m cli.langgraph_demo --question "Read README.md."
```

继续保留：

```bash
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.langgraph_demo --question "the and of"
```

## 本阶段最低通过标准

完成 v12 后，你应该能讲清：

1. LangGraph 的 state / node / edge / compile / invoke。
2. 当前 `prepare -> call_tool -> finalize` 的职责。
3. 为什么 v12 是真实 LangGraph，而不是自定义 workflow。
4. v12 和 `WorkspaceAgent` workflow 的区别。
5. 为什么 `"the and of"` 不会触发真实 DeepSeek。
6. 下一阶段为什么要做条件路由和多工具编排。
