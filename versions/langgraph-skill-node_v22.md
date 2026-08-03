# LangGraph Skill Node v22

版本：v22

日期：2026-08-02

## 本次目标

本阶段把 `Skills` 执行接入 `LangGraph` 编排层。

在 v21 中，`SkillRun` 已经可以导出 JSON-ready trace；v22 的重点是让 `LangGraph` 不只是调用 RAG / read file / search docs，而是可以把 `execute_skill` 作为一个独立 graph node 执行，并把 `SkillRun` 留存在 graph state 和主 Agent trace 中。

这一步的工程意义是：

- `Skill` 不再只是普通工具输出文本。
- `LangGraph` 可以根据 state 路由到不同节点。
- `SkillRun.status` 可以作为 graph 条件边的判断依据。
- `WorkspaceAgent.to_trace_dict()` 可以继续拿到 graph 内部产生的 `skill_run`。

## 本次新增能力

1. `RAGGraphState` 新增 `skill_run` 和 `skill_status`。
2. `LangGraph` 新增 `skill_execution` 路由。
3. `LangGraph` 新增 `call_skill` node。
4. `call_skill` 通过 `run_skill_with_workspace()` 执行项目 Skills。
5. `call_skill` 将 `SkillRun.to_dict()` 结果写入 graph state。
6. graph 通过 `_next_after_skill()` 按 `skill_status` 进入成功或失败分支。
7. `WorkspaceAgent` 的 graph tool metadata 新增 `skill_run`。
8. regression eval 新增 `langgraph-skill-execution` 用例。

## 修改文件与关键行号

### `integrations/langgraph_workflow.py`

当前文件行数：`238`

关键新增区域：

- `6`：引入 `Any`，用于描述 `skill_run` 结构化数据。
- `10`：引入 `run_skill_with_workspace()`，让 graph node 可以执行项目 Skills。
- `24-25`：`RAGGraphState` 新增 `skill_run` 和 `skill_status`。
- `55-63`：新增 `skill_execution` 路由分支。
- `104-124`：新增 `call_skill()` node，执行 skill 并写入结构化 state。
- `146`：注册 `call_skill` node。
- `150-157`：`route` 节点的条件边新增 `call_skill` 分支。
- `160-167`：`call_skill` 后新增基于 skill status 的条件边。
- `185-186`：`_next_after_route()` 支持进入 `call_skill`。
- `190-195`：新增 `_next_after_skill()`，基于 `skill_status` 判断分支。
- `198-208`：新增 `_looks_like_skill_execution()`。

### `agent/core.py`

当前文件行数：`658`

关键新增区域：

- `101-105`：graph 分支构造 `ToolResult` 时写入 metadata。
- `420-425`：graph answer 新增 `Skill status`。
- `430-440`：新增 `_build_langgraph_metadata()`，把 graph route、graph steps 和 skill run 交给主 trace。

### `tests/test_langgraph_workflow.py`

当前文件行数：`102`

关键新增区域：

- `53-64`：验证 graph 可以路由到 `skill_execution` 并执行 `code_review` skill。
- `66-77`：验证 graph state 保留 `skill_run` 结构化 trace。
- `79-88`：验证 `skill_status` 控制后续 graph edge。

### `tests/test_agent.py`

当前文件行数：`181`

关键新增区域：

- `157-167`：验证 `WorkspaceAgent.to_trace_dict()` 可以拿到 LangGraph 内部产生的 `skill_run`。

### `evals/regression_cases.json`

当前文件行数：`114`

关键新增区域：

- `107-113`：新增 `langgraph-skill-execution` 回归用例。

## 新增文件

| 文件 | 行数 | 说明 |
| --- | ---: | --- |
| `versions/langgraph-skill-node_v22.md` | 184 | v22 迭代说明 |
| `docs/langgraph-skill-node-exercises_v22.md` | 80 | 本阶段练习，文件名带版本号 |

## 新增交互流程

本阶段新增的主流程如下：

```text
User input
  -> WorkspaceAgent.route_intent()
  -> action = graph
  -> WorkspaceAgent._run_langgraph()
  -> run_rag_graph()
  -> route node
  -> route = skill_execution
  -> call_skill node
  -> run_skill_with_workspace()
  -> execute_skill()
  -> SkillRun.to_dict()
  -> graph state["skill_run"]
  -> _next_after_skill()
  -> finalize node
  -> WorkspaceAgent ToolResult.metadata
  -> WorkspaceAgent.to_trace_dict()["skill_run"]
```

手动运行示例：

```bash
python -m cli.main --input "Use LangGraph to execute skill for code review." --trace
```

你应该重点观察：

- `Graph route: skill_execution`
- `Selected tool: execute_workspace_skill`
- `Skill status: completed`
- `Graph steps: route -> call_skill -> finalize`
- `Skill run: code_review`

## 当前设计判断

本阶段没有把 `execute_skill` 做成普通 LangChain `StructuredTool` 再由 `call_tool` 调用，而是单独新增 `call_skill` node。

原因是：

- Skill 执行不只是返回文本，还会返回 `SkillRun` 结构化 trace。
- graph state 需要保存 `skill_run`，不能只保存 tool output。
- 后续要基于 `SkillRun.status` 增加 retry、human review、approval gate 等节点。

也就是说，本阶段的重点不是“把 skill 当一个工具塞进去”，而是让 skill 成为 graph 中可观察、可分支、可扩展的执行节点。

## 当前限制

- skill 路由仍是规则判断，不是 LLM router。
- `SkillRun.status == failed` 当前仍进入 `finalize`，还没有单独的错误恢复节点。
- skill registry 仍是本地静态定义。
- skill 权限、参数 schema、外部配置还没有标准化。
- LangGraph 还没有 checkpoint / persistence。
- LangGraph 仍不是默认主执行器，需要用户显式输入 `Use LangGraph ...`。

## 验证命令

```bash
python -m unittest tests.test_langgraph_workflow tests.test_agent tests.test_evals -v
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.main --input "Use LangGraph to execute skill for code review." --trace
```

## 本阶段学习重点

你需要掌握：

1. graph state 是节点之间传递信息的核心载体。
2. node 的职责应该单一，`call_skill` 只负责执行 skill 和写入结果。
3. 条件边不一定只看 route，也可以看运行结果，比如 `skill_status`。
4. 文本输出是给人看的，`skill_run` 结构化数据是给系统、测试、eval 和恢复用的。
5. 专业 Agent 工程中，RAG、MCP、Skills 不应该全部挤在一个函数里，而应该通过 graph node / state / edge 明确表达执行结构。

## 下一步建议

下一阶段建议进入：

```text
v23：LangGraph Skill Failure Recovery
```

目标：

- 为 `skill_status == failed` 增加独立 failure node。
- 把失败原因转换成明确的 recovery plan。
- 让 graph trace 区分 normal finalize 和 failure finalize。
- 为失败 skill 增加测试用例。
