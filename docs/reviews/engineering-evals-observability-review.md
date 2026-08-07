# 工程化评估与可观测性阶段复盘

## 测试和 eval 有什么区别？

- 测试主要验证代码行为是否正确，例如函数返回值、异常处理、路由分支是否符合预期。
- eval 主要验证 Agent 行为是否符合产品目标，例如是否选对工具、是否回答到关键点、是否保持稳定。
- 测试通常更细、更靠近代码；eval 通常更贴近用户输入和端到端行为。
- 当前项目中，`tests/` 负责自动化单元/集成测试，`evals/regression_cases.json` 负责固定 Agent 行为回归。

## 为什么 Agent 项目必须有 trace？

- Agent 的失败经常不是单点错误，而是路由、工具、状态、检索、汇总中的某一步出错。
- trace 能记录每一步发生了什么，帮助判断问题属于 routing、tool、workflow、RAG、MCP 还是输出合成。
- 没有 trace 时，只能看到最终答案，很难定位为什么答错。
- 当前项目已经有纯文本 trace 和结构化 trace 两种形式。

## 结构化 trace 和纯文本 trace 有什么区别？

- 纯文本 trace 适合人直接阅读，便于调试单次运行。
- 结构化 trace 适合程序处理，可以用于日志落盘、自动分析、评估报告和后续可视化。
- 结构化 trace 中 route、steps、tool_result、tool_error 等字段可以被稳定读取。
- 当前 `to_trace_dict()` 只保存 preview，避免把过长工具输出直接写入报告。

## 当前 eval runner 能发现什么问题？

- 能发现 route 是否和预期不一致。
- 能发现 tool 选择是否错误。
- 能发现最终答案是否缺少关键关键词。
- 能发现关键能力是否发生回归，例如 RAG、MCP、Skills、Subagent、workflow 和错误处理。
- 能通过非 0 exit code 让 CI 或脚本感知评估失败。

## 当前 eval runner 发现不了什么问题？

- 不能判断答案是否真正高质量。
- 不能判断上下文引用是否最佳。
- 不能发现细微幻觉，只能检查关键词。
- 不能评价回答风格、完整性、推理质量。
- 不能做人工评分，也不能区分严重错误和轻微问题。
- 不能自动分类失败原因，目前只输出规则失败信息。

## 下一阶段是否可以进入综合项目？理由是什么？

可以进入 Week 6 综合项目，但需要保留两个前提：

1. Week 5 的 eval runner 是最小工程化版本，不是完整评估平台。
2. 综合项目必须继续沿用 eval、trace、测试和版本记录，而不是只做新功能。

理由：

- 当前项目已经具备 Agent 主循环、工具、工作流、RAG、MCP、Skills、Subagent 和 eval runner。
- 关键路径已有自动化测试和 regression eval。
- 下一阶段的重点应该从“继续堆单点能力”转为“组合成一个明确应用原型”。
- Week 6 可以把前面能力整合成一个可运行的 Agent 产品雏形。

建议综合项目方向：

```text
Project Learning Assistant
  -> 读取项目文件
  -> 检索本地知识
  -> 调用 MCP 工具
  -> 选择 Skill
  -> 生成 Subagent 协作计划
  -> 通过 eval runner 做回归验证
```
