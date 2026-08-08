# LLM Tool Loop Final Synthesis v17

版本：v17  
日期：2026-07-29

## 本次目标

把 v16 的 tool loop 最终答案从“确定性汇总”升级为“LLM final synthesis”。

v16 已经实现：

```text
LLM selects tool
-> tool executes
-> observation recorded
-> LLM chooses stop
-> deterministic final answer
```

v17 改为：

```text
LLM selects tool
-> tool executes
-> observation recorded
-> LLM chooses stop
-> LLM synthesizes final answer from observations
```

核心边界：

- LLM 只能基于 tool loop observations 综合最终答案。
- 如果 final synthesis 失败，代码回退到确定性答案。

## 本次新增能力

1. 新增 tool loop final synthesis prompt。
2. 新增 `agent/tool_synthesis.py`。
3. `WorkspaceAgent` 在 tool loop 完成后调用 LLM 生成最终答案。
4. `ToolLoopResult` 新增 `final_answer_source`。
5. trace 中显示最终答案来源：
   - `llm`
   - `deterministic_fallback`
6. 新增 final synthesis 单测。
7. 新增 final synthesis fallback 测试。

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
-> step 2: LLM selects answer_directly
-> WorkspaceAgent._synthesize_tool_loop_result()
-> LLM generates final answer from observations
```

真实 demo 已验证：

```text
Final answer source: llm
README.md 文件共有 616 行。
```

## 代码改动说明

### `prompts/v17_tool-loop-synthesis.md`

新增最终综合 prompt。

要求：

- 直接输出最终答案
- 先给结论
- 只基于 observation
- 不编造工具没有返回的信息
- 保留关键数字、文件名、工具名

### `agent/tool_synthesis.py`

新增：

- `build_tool_loop_synthesis_messages()`
- `synthesize_tool_loop_answer()`

该模块只负责一件事：把 `ToolLoopResult` 转成 LLM 消息，并请求模型生成最终答案。

如果模型返回空答案，会抛出 `LLMError`，由主 Agent fallback。

### `agent/tool_loop.py`

`ToolLoopResult` 新增字段：

```python
final_answer_source: str = "deterministic"
```

用于区分最终答案来自：

- LLM synthesis
- deterministic fallback

`to_text()` 也会显示：

```text
Final answer source: llm
```

### `agent/core.py`

新增：

- `load_tool_loop_synthesis_prompt()`
- `synthesize_tool_loop_answer`
- `_synthesize_tool_loop_result()`

tool loop 分支现在是：

```text
_run_tool_loop()
->_synthesize_tool_loop_result()
-> run.answer
```

fallback 策略：

如果 final synthesis 失败，不让整个 tool loop 失败，而是返回 deterministic fallback，并记录失败原因。

### `agent/prompts.py`

新增：

- `load_tool_loop_synthesis_prompt()`

### `agent/__init__.py`

导出：

- `build_tool_loop_synthesis_messages`
- `synthesize_tool_loop_answer`

### `tests/test_tool_synthesis.py`

新增测试：

- final synthesis prompt 包含 objective、observation、stop reason
- synthesis 返回 LLM content

### `tests/test_tool_loop.py`

更新测试：

- two-step tool loop 现在验证 `final_answer_source = "llm"`
- repeated tool call 也会经过 final synthesis
- 新增 final synthesis 失败时 fallback 的测试

### 文档更新

更新：

- `agent/README.md`
- `docs/current-learning-state.md`

## 新增文件与行数

| 文件 | 行数 |
| --- | ---: |
| `agent/tool_synthesis.py` | 52 |
| `prompts/v17_tool-loop-synthesis.md` | 24 |
| `tests/test_tool_synthesis.py` | 67 |
| `versions/llm-tool-synthesis_v17.md` | 248 |

## 本次修改文件与行数

| 文件 | 行数 |
| --- | ---: |
| `agent/tool_loop.py` | 54 |
| `agent/core.py` | 630 |
| `agent/prompts.py` | 36 |
| `agent/__init__.py` | 63 |
| `agent/README.md` | 50 |
| `docs/current-learning-state.md` | 214 |
| `tests/test_tool_loop.py` | 100 |

## 验证命令

```bash
python -m unittest tests.test_tool_loop tests.test_tool_synthesis tests.test_tool_calling -v
python -m cli.tool_loop_demo --input "Use tool loop to count lines in README.md and then answer." --trace
```

## 当前验证结果

已通过：

- v17 定向测试
- 真实 DeepSeek tool loop final synthesis demo

真实 demo 关键输出：

```text
Final answer source: llm
README.md 文件共有 616 行。
```

## 本阶段学习重点

1. tool loop 和 final synthesis 是两层不同能力。
2. tool loop 负责收集 observations。
3. final synthesis 负责把 observations 变成用户可读答案。
4. final synthesis 失败不能导致整个任务失败，必须 fallback。
5. `final_answer_source` 是重要 trace 字段。

## 当前限制

v17 仍然不是完整生产级 Agent。

当前限制：

- synthesis prompt 还很简单。
- final answer 没有引用每一步 observation 的结构化来源编号。
- MCP / Skills 还没有作为 tool loop 的重点场景展开。
- LangGraph 还没有负责 tool loop 的状态编排。

## 下一阶段建议

下一阶段建议进入：

```text
MCP / Skills as first-class tool loop capabilities
```

重点：

1. 让 MCP 工具在 schema 中更专业。
2. 让 Skills 不只是说明文本，而是可执行能力。
3. 让 tool loop 能组合 RAG、MCP、Skills 完成更复杂任务。
