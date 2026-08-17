# 第 1 章证据笔记

## 可引用事实

- 项目学习路线已经从最小 CLI Agent 发展到默认 LangGraph 主执行器。
- 当前学习进度明确要求后续围绕 replay、checkpoint、恢复和可观测性继续推进。
- 迭代计划强调不要只做局部 helper，而要围绕专业 Agent 能力闭环推进。
- `v01` 解决的是最小闭环；`v29` 已经进入 Professional RAG v1。
- `agent/core.py` 负责统一调度，`agent/router.py` 负责意图路由，说明项目已经不是单点脚本，而是分层 Agent 系统。

## 证据来源

- `docs/current-learning-state.md`
- `docs/plans/v1_learning-master-plan.md`
- `docs/plans/v3_professional-agent-iteration-plan.md`
- `versions/v01_minimal-cli-agent.md`
- `versions/v02_state-workflow.md`
- `versions/v03_rag-local-search.md`
- `versions/v29_professional-rag-v1.md`
- `agent/core.py`
- `agent/router.py`

## 写作提醒

- 这章应先说明“为什么要写书”，再说明“书写什么”。
- 避免过早展开 RAG、MCP、Skills 的技术细节。
- 重点是把项目演进本身写成书的理由讲清楚。
- 应补“读者完成本章后的收获”和“代码与证据入口”，避免章节只停留在作者叙述。
- 写法上要参考开放 Agent 书稿和 AOSA 的思路，把“项目为什么值得写成书”讲成工程学习路径，而不是版本列表。

## 当前主稿

- `publish/drafts/ch01/README.md`
