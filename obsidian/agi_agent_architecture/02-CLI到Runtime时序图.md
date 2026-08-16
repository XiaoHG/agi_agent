# CLI 到 Runtime 时序图

## 结论

用户输入不是直接打到工具层，而是先进入 CLI 参数解析，再构造 `WorkspaceAgent`，然后通过 `run()` 进入路由、图执行、结果回填、trace 持久化这条主链路。

## 主执行时序

```mermaid
sequenceDiagram
    participant User
    participant CLI as cli/main.py
    participant Agent as WorkspaceAgent
    participant Router as route_intent
    participant Graph as run_rag_graph
    participant Tools as agent/tools.py
    participant Memory as AgentMemoryStore
    participant Checkpoint as RunCheckpointStore

    User->>CLI: python -m cli.main --input "..."
    CLI->>CLI: parse args / build skill policy
    CLI->>Agent: WorkspaceAgent(...)
    CLI->>Agent: run(user_input)
    Agent->>Router: route_intent(user_input)
    Router-->>Agent: ToolRoute

    alt use_graph_runtime = true
        Agent->>Graph: _run_langgraph(question, route_hints)
        Graph->>Tools: call selected tool / skill / subagent / workflow step
        Tools-->>Graph: ToolResult
        Graph-->>Agent: graph_state
        Agent->>Agent: _apply_graph_runtime_result(run, graph_state)
    else classic fallback
        Agent->>Agent: _run_classic_route / _run_classic_tool_call / _run_classic_tool_loop
        Agent->>Tools: _call_tool(route)
        Tools-->>Agent: ToolResult
    end

    Agent->>Memory: update_from_trace(session_id, task_id, trace)
    Memory-->>Agent: MemorySnapshot
    Agent->>Checkpoint: save(build_run_checkpoint(...))
    Checkpoint-->>Agent: latest.json + run_id.json
    Agent-->>CLI: AgentRun
    CLI-->>User: answer or trace
```

## 相关函数

- 入口构造：[main()](../../cli/main.py)
- 单次执行：[WorkspaceAgent.run()](../../agent/core.py)
- 图执行封装：[WorkspaceAgent._run_langgraph()](../../agent/core.py)
- 持久化：[WorkspaceAgent._persist_run()](../../agent/core.py)

## 学习重点

- CLI 负责参数、入口和展示，不负责编排逻辑。
- `WorkspaceAgent.run()` 是当前项目最重要的 orchestration 函数。
- LangGraph 返回的是 `graph_state`，不是直接面向用户的最终对象；`WorkspaceAgent` 还会做一次回填和标准化。
