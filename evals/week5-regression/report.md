# Week 5 回归评估报告

## 本阶段 eval 目标

本阶段目标是让 Agent 行为具备最小可回归能力。

具体目标：

- 固定一组核心用户输入。
- 检查 Agent 是否选择正确 route。
- 检查 Agent 是否选择正确 tool。
- 检查最终回答是否包含关键内容。
- 输出 JSON report，便于后续自动化和 CI 接入。

## 当前 eval case 数量

当前共有 10 个 regression case。

来源文件：

```text
evals/regression_cases.json
```

## 覆盖能力

当前覆盖：

- 直接回答：`direct_answer`
- 文件读取：`read_file`
- RAG 检索：`search_docs`
- MCP 工具列表：`list_mcp_tools`
- MCP workspace summary：`mcp_workspace_summary`
- Skills 列表：`list_skills`
- Subagent 协作计划：`plan_subagents`
- workflow 成功路径
- workflow 失败路径
- 文件不存在错误处理

## 当前全部通过的命令和摘要

运行：

```bash
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.eval_runner --output logs/eval-report.json
```

结果摘要：

- 自动化测试：47 个测试全部通过。
- regression eval：10 个 case 全部通过。
- eval report 可以输出到 `logs/eval-report.json`。

## 当前 eval runner 的限制

- 只能检查 route、tool 和关键词。
- 不能判断答案是否真正完整。
- 不能判断答案是否有幻觉。
- 不能判断 RAG 检索来源是否最优。
- 不能做多轮对话评估。
- 不能区分失败严重程度。
- 还没有结构化错误分类。

## 后续应增加的评估维度

建议后续增加：

- trace step 是否符合预期。
- 工具错误类型分类。
- RAG source 是否命中特定文件。
- workflow 是否按指定步骤执行。
- answer quality 人工评分。
- 多轮任务状态保持。
- eval report 历史对比。
- CI 中自动运行 eval runner。
