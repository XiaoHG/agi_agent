# v28：LLM Planner 接入 LangGraph

## 本阶段目标

按照 `docs/plans/v3_professional-agent-iteration-plan.md` 的方向，把 LangGraph 从纯规则路由推进到 LLM-first planning：

```text
User question
-> DeepSeek planner
-> validated GraphPlan
-> LangGraph route
-> tool / RAG / Skill execution
-> final answer
```

当前阶段不是移除规则路由，而是在 graph route node 前面增加一层可选 LLM planner，并保留 deterministic fallback。

## 本阶段解决的专业 Agent 缺口

之前 LangGraph 的 route 主要依赖关键词判断：

- 文件读取靠 `read` / `open`
- 文档搜索靠 `search docs`
- skill 执行靠 `execute skill`

这种方式稳定，但不是专业 Agent 的主路径。专业 Agent 更合理的结构是：

- LLM 负责理解任务并生成结构化计划
- 代码负责校验计划
- LangGraph 负责执行计划
- fallback 负责保证系统可靠性

## 新增文件

| 文件 | 作用 |
|---|---|
| `agent/planner.py` | LangGraph planner 数据模型、prompt message 构建、JSON 解析和 plan 校验 |
| `prompts/v28_langgraph-planner.md` | DeepSeek planner 使用的结构化规划 prompt |
| `versions/v28_llm-planner-langgraph.md` | 本阶段版本说明 |
| `docs/v28_llm-planner-langgraph-exercises.md` | 本阶段练习 |

## 修改文件

| 文件 | 主要变化 |
|---|---|
| `agent/prompts.py` | 新增 `load_langgraph_planner_prompt()` |
| `agent/__init__.py` | 导出 planner 相关模型与函数 |
| `integrations/langgraph_workflow.py` | route node 先尝试 LLM planner，失败后 fallback |
| `agent/core.py` | LangGraph trace / metadata 增加 planner 状态 |
| `cli/main.py` | 新增 `--llm-planner`，主 Agent 运行 LangGraph 时可启用真实 DeepSeek planner |
| `cli/langgraph_demo.py` | 新增 `--llm-planner`，demo 入口可启用真实 DeepSeek planner |
| `cli/README.md` | 补充 LLM planner demo 命令 |
| `tests/test_langgraph_workflow.py` | 增加 planner parser、planner route、fallback 测试 |
| `evals/regression_cases.json` | 增加 planner status trace 回归用例 |
| `docs/current-learning-state.md` | 更新当前阶段和学习任务 |

## 核心实现说明

### 1. `GraphPlan`

`GraphPlan` 是 LLM planner 输出进入 LangGraph 前的结构化计划。

它包含：

- `route`
- `selected_tool`
- `tool_input`
- `reason`
- `raw_response`
- `status`

这个结构的价值是：LLM 不直接控制执行，只能输出受限 plan。

### 2. planner prompt

`prompts/v28_langgraph-planner.md` 明确限制 planner 只能选择四种 route：

- `read_file`
- `search_docs`
- `answer_docs_with_llm`
- `skill_execution`

每种 route 都绑定固定的 `selected_tool`。

这样可以避免模型随意编造工具名。

### 3. plan 校验

`parse_graph_plan()` 会检查：

- JSON 是否存在
- 必填字段是否存在
- route 是否受支持
- route 和 selected tool 是否匹配
- tool input 是否包含必要字段

如果校验失败，会抛出 `LLMError`。

### 4. deterministic fallback

`integrations/langgraph_workflow.py` 中的 route node 会先尝试：

```text
planner_client -> plan_graph_route() -> GraphPlan
```

如果 planner 不存在或失败，就继续使用原本的 deterministic route。

fallback 时会写入：

- `planner_status = deterministic_fallback`
- `planner_error = <error>`

没有启用 planner 时会写入：

- `planner_status = deterministic_route`

### 5. CLI 真实 LLM 入口

通过主 Agent 启用真实 DeepSeek planner：

```bash
python -m cli.main --input "Use LangGraph to read README.md." --llm-planner --trace
```

通过 LangGraph demo 启用真实 DeepSeek planner：

```bash
python -m cli.langgraph_demo --question "Read README.md." --llm-planner
```

前提是本地环境有：

```bash
export DEEPSEEK_API_KEY=...
```

## 本阶段交互流程

### 未启用 LLM planner

```text
question
-> deterministic route
-> selected tool
-> tool execution
-> final answer
```

### 启用 LLM planner 且成功

```text
question
-> DeepSeek planner
-> GraphPlan
-> plan validation
-> selected graph branch
-> tool execution
-> final answer
```

### 启用 LLM planner 但失败

```text
question
-> DeepSeek planner
-> invalid response / network error / schema error
-> deterministic fallback
-> selected graph branch
-> tool execution
-> final answer
```

## 验证命令

```bash
python -m unittest tests.test_langgraph_workflow -v
python -m unittest discover -s tests -v
python -m cli.eval_runner
```

如果本地有 DeepSeek API Key：

```bash
python -m cli.main --input "Use LangGraph to read README.md." --llm-planner --trace
python -m cli.langgraph_demo --question "Read README.md." --llm-planner
```

## 当前限制

- LLM planner 目前只覆盖 LangGraph route，不是全局 Agent route。
- planner 只支持四种 graph route。
- 默认测试路径不调用真实网络。
- `WorkspaceAgent` 只有在注入 LLM client 时才会让 graph 使用 planner；`cli.main` 和 `cli.langgraph_demo` 都可通过 `--llm-planner` 显式启用真实 DeepSeek。

## 下一步建议

下一阶段建议按原计划进入专业 RAG v1：

- embedding
- vector index
- chunk metadata
- source citation
- index rebuild CLI
- RAG eval

原因：LLM planner 解决了“如何规划执行”，专业 RAG v1 解决“如何提供高质量知识上下文”。
