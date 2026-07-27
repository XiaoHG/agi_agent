# 工程化评估与可观测性 v6

版本：v6

日期：2026-07-26

## 本次目标

进入 Week 5：工程化、评估与稳定性。

本次先实现最小工程化闭环：

```text
Eval cases -> Agent run -> Structured trace -> Eval report -> Regression result
```

## 新增文件

### `evals/regression_cases.json`

行号范围：`1-51`

职责：

- 保存固定回归评估用例
- 记录输入、期望 route、期望 tool、答案关键词
- 让 Agent 行为可以重复验证

当前包含 7 个 case：

- direct answer
- read README
- RAG search
- MCP tools
- skills list
- subagent plan
- missing file

### `evals/runner.py`

行号范围：`1-97`

职责：

- 定义 `EvalCase`
- 定义 `EvalResult`
- 加载 JSON eval case
- 运行 WorkspaceAgent
- 判断 route/tool/answer terms
- 生成 JSON report

### `cli/eval_runner.py`

行号范围：`1-44`

职责：

- 提供命令行 eval runner
- 支持指定 case 文件
- 支持输出 JSON report 到文件
- eval 失败时返回非 0 exit code

### `tests/test_evals.py`

行号范围：`1-29`

职责：

- 测试 eval case 加载
- 测试 eval runner 执行
- 确保当前 regression cases 全部通过

## 修改文件

### `agent/core.py`

新增变更：

- 新增 `to_trace_dict()`
- 将 `AgentRun` 转为结构化 trace 字典
- 输出 route、steps、tool_result、tool_error、answer_preview

### `tests/test_agent.py`

新增变更：

- 新增 `test_agent_exports_structured_trace`
- 验证结构化 trace 至少包含 route、steps、answer_preview

### `README.md`

新增变更：

- 新增 eval runner 命令
- 更新当前阶段说明

### `docs/current-learning-state.md`

新增变更：

- 将当前阶段更新为 Week 5
- 更新恢复指令
- 更新当前缺口和下一步建议

### `evals/README.md`

新增变更：

- 记录当前 eval runner 结构
- 新增运行命令
- 说明当前判断维度和后续扩展方向

## 新增交互流程

### eval runner 流程

```text
load regression_cases.json
  -> build WorkspaceAgent
  -> run each case
  -> check route / tool / answer terms
  -> build JSON report
  -> exit 0 or 1
```

### structured trace 流程

```text
AgentRun
  -> WorkspaceAgent.to_trace_dict()
  -> route / steps / tool result / error / answer preview
  -> debugging and future log storage
```

## 验证命令

```bash
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.eval_runner --output logs/eval-report.json
```

验证结果：

- 46 个测试全部通过。
- 7 个 regression eval case 全部通过。
- eval runner 可以输出 JSON report。

## 当前限制

- eval 判断仍是确定性规则，没有人工评分。
- answer terms 只能检查关键词，不能判断答案质量。
- trace 还没有统一写入日志文件。
- 错误还没有结构化分类。

## 下一步建议

先完成 Week 5 练习、补充更多 eval case 和阶段复盘，再评估是否进入 Week 6 综合项目。
