# 第 2 章证据笔记

## 可引用事实

- `v01` 的核心目标是先打通最小可运行 Agent 闭环：输入、路由、工具、回答。
- `route_intent()` 负责把自然语言转换成 `use_tool` / `direct_answer` 这类路由。
- `WorkspaceAgent.run()` 负责把路由结果转成实际执行流程，并产出 `AgentRun`。
- `tests/test_agent.py` 是最关键的回归入口，因为它直接验证最小闭环是否稳定。
- `v02` 在最小闭环基础上加入了状态和工作流，说明“闭环”是后续一切能力的底座。
- 现在的 `agent/core.py` 仍然保留分层：路由、工具执行、错误处理、回答渲染、trace 记录。

## 证据来源

- `versions/v01_minimal-cli-agent.md`
- `docs/v01_minimal-cli-agent-exercises.md`
- `versions/v02_state-workflow.md`
- `docs/v02_state-workflow-exercises.md`
- `agent/router.py`
- `agent/core.py`
- `tests/test_agent.py`

## 写作提醒

- 这一章要把“最小闭环”讲成方法论，不只是讲一个 demo。
- 要强调分层的必要性，而不是把重点放在代码行数。
- 不要提前展开 workflow、RAG、MCP、Skills 的细节，只做承接。
- 第 2 章完成后应补一张最小闭环图和一条 CLI 示例，增强读者的直觉。
- 章节结构要补“关键代码入口”和“验证与复盘”，让读者更容易把版本文档和代码走读串起来。
- 要用“为什么旧方案不够 -> 为什么需要分层 -> 如何验证分层有效”这样的工程链路展开。

## 当前主稿

- `publish/drafts/ch02/README.md`
