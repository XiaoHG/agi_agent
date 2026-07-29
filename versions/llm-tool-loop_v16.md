# LLM Tool Loop v16

版本：v16  
日期：2026-07-29

## 本次目标

把 v15 的“单次 LLM tool calling”升级为“有边界的多步 LLM tool loop”。

v15 的链路是：

```text
LLM selects one tool -> code executes one tool -> final answer
```

v16 的链路是：

```text
LLM selects tool
-> code executes tool
-> observation is fed back
-> LLM chooses next action
-> stop or continue
```

本次仍然保持工程边界：

- LLM 负责选择下一步动作。
- 代码负责执行工具、记录 observation、限制最大步数、防止重复调用。

## 本次新增能力

1. 新增 `tool_loop` 路由。
2. 新增 bounded multi-step tool loop。
3. loop 每一步记录 LLM selection 和 tool observation。
4. 支持模型在观察结果足够时选择 `answer_directly` 停止。
5. 支持重复工具调用保护，避免无限循环。
6. trace 新增 `[Tool Loop]`。
7. 结构化 trace 新增 `tool_loop` 字段。
8. 新增真实 CLI demo。

## 交互流程

示例命令：

```bash
python -m cli.tool_loop_demo --input "Use tool loop to count lines in README.md and then answer." --trace
```

实际流程：

```text
route_intent
-> action=tool_loop
-> WorkspaceAgent._run_tool_loop()
-> step 1: LLM selects count_lines / README.md
-> code executes count_lines
-> observation: README.md line count
-> step 2: LLM sees observation and selects answer_directly
-> loop stops by model_answered_directly
```

## 代码改动说明

### `agent/tool_loop.py`

新增两个数据结构：

- `ToolLoopStep`
- `ToolLoopResult`

`ToolLoopStep` 记录一次 loop 内部决策：

- 第几步
- LLM 选择结果
- 工具 observation
- 错误信息

`ToolLoopResult` 记录整个 loop 的最终结果：

- 原始目标
- 全部步骤
- 最终答案
- 停止原因

### `agent/router.py`

新增显式 tool loop 路由。

支持关键词：

- `tool loop`
- `multi-step tool`
- `multi step tool`
- `multiple tool steps`
- `iterate tools`
- `tool iteration`
- `loop with tools`

路由结果：

```text
action=tool_loop
tool_name=llm_tool_loop
```

### `agent/core.py`

`WorkspaceAgent` 新增：

- `tool_loop_result`
- `tool_loop` 分支
- `_run_tool_loop()`
- `_build_tool_loop_input()`
- `_compose_tool_loop_final_answer()`
- `_describe_tool_loop()`
- `_preview_observation()`

关键保护：

- `max_steps=3`
- `seen_tool_calls`
- repeated tool call stop
- tool error stop

这几个保护是必须的，否则真实 LLM 可能进入重复工具调用。

### `agent/__init__.py`

导出：

- `ToolLoopStep`
- `ToolLoopResult`

### `cli/tool_loop_demo.py`

新增 tool loop CLI：

```bash
python -m cli.tool_loop_demo --input "Use tool loop to count lines in README.md and then answer." --trace
```

### `tests/test_tool_loop.py`

新增测试：

- 两步 tool loop 成功停止
- 重复工具调用保护
- 结构化 trace 包含 tool loop steps

测试使用 fake LLM client，不依赖真实网络。

### 文档更新

更新：

- `README.md`
- `agent/README.md`
- `cli/README.md`
- `docs/current-learning-state.md`

## 新增文件与行数

| 文件 | 行数 |
| --- | ---: |
| `agent/tool_loop.py` | 53 |
| `cli/tool_loop_demo.py` | 35 |
| `tests/test_tool_loop.py` | 77 |
| `versions/llm-tool-loop_v16.md` | 224 |

## 本次修改文件与行数

| 文件 | 行数 |
| --- | ---: |
| `agent/core.py` | 587 |
| `agent/router.py` | 435 |
| `agent/__init__.py` | 60 |
| `README.md` | 616 |
| `agent/README.md` | 48 |
| `cli/README.md` | 38 |
| `docs/current-learning-state.md` | 202 |
| `tests/test_agent.py` | 169 |

## 验证命令

```bash
python -m unittest tests.test_tool_loop tests.test_tool_calling tests.test_agent -v
python -m cli.tool_loop_demo --input "Use tool loop to count lines in README.md and then answer." --trace
```

## 当前验证结果

已通过：

- v16 定向测试
- 真实 DeepSeek tool loop demo

真实 demo 结果：

```text
step=1; action=use_tool; tool=count_lines; input=README.md; ok
step=2; action=answer_directly; tool=none; input=none; ok
stop_reason=model_answered_directly
```

## 本阶段学习重点

1. 单次 tool calling 和多步 tool loop 的区别。
2. observation 如何影响下一轮模型决策。
3. 为什么必须限制最大步数。
4. 为什么必须检测重复工具调用。
5. trace 如何帮助判断失败发生在哪一步。

## 当前限制

v16 还不是完整 ReAct Agent。

当前最终答案是确定性汇总，不是让 LLM 基于 observations 再生成自然语言最终回答。

下一阶段可以继续做：

1. LLM final synthesis。
2. MCP / Skills 接入统一 tool loop。
3. 把 tool loop 做成 LangGraph 节点。
