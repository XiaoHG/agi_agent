# 版本索引与章节锚点

更新日期：2026-08-18

## 1. 文件职责

这份文件不再只是“版本列表”，而是本书正式使用的章节锚点索引。

它的职责是把以下几类信息固定在同一个入口中：

1. 章节与版本的关系
2. 章节与代码标签的关系
3. 章节与标签创建状态的关系
4. 章节与验证命令、关键代码入口的关系

后续每次继续写书稿，都必须先检查本文件。

## 2. 使用规则

使用本文件时，遵守以下规则：

1. 正文按章节组织，代码按标签定位。
2. 每章至少有一个主锚点标签。
3. 概念章也必须给出代码标签，哪怕它同时引用多个版本。
4. 如果标签尚未创建，使用预留标签名并明确标记“待创建”。
5. 每次新增正式章节，都必须先在本文件补一行。

## 3. 当前章节锚点

| 章节 | 学习焦点 | 主锚点版本 | 主锚点标签 | 标签状态 | 推荐检出命令 | 推荐代码入口 | 最小验证命令 | 补充支撑版本 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 序章 | 为什么要系统学习 Agent 工程 | v01 | `book-prologue-anchor` | 待创建 | `待创建后执行：git checkout book-prologue-anchor` | `cli/main.py` `agent/core.py` | `python -m cli.main --help` | v01-v04 |
| 第 1 章 什么是 Agent，为什么它不是聊天机器人 | 从“回答系统”理解到“执行系统”理解 | v01 | `book-ch01-anchor` | 已创建 | `git checkout book-ch01-anchor` | `agent/router.py` `agent/core.py` `cli/main.py` | `python -m cli.main --help` | v01-v02 |
| 第 2 章 工业级 Agent 的基本结构 | 输入、路由、执行、状态与边界分层 | v04 | `book-ch02-anchor` | 已创建 | `git checkout book-ch02-anchor` | `cli/main.py` `agent/core.py` `agent/router.py` | `pytest tests/test_agent.py` | v01-v04 |
| 第 3 章 最小 Agent 执行闭环 | 最小闭环、工具分支、统一输出 | v01 | `book-ch03-anchor` | 已创建 | `git checkout book-ch03-anchor` | `cli/main.py` `agent/core.py` `agent/router.py` | `pytest tests/test_agent.py -k route` | v01 |
| 第 4 章 状态、工作流与多步执行 | 状态对象、多步任务、工作流计划 | v02 | `book-ch04-anchor` | 已创建 | `git checkout book-ch04-anchor` | `agent/workflow.py` `agent/state.py` `agent/core.py` | `pytest tests/test_agent.py -k workflow` | v01-v02 |
| 第 5 章 知识增强：RAG 如何进入 Agent 主链路 | grounded answer、本地检索、知识接入 | v03 | `book-ch05-anchor` | 待创建 | `待创建后执行：git checkout book-ch05-anchor` | `rag/` `agent/core.py` `cli/main.py` | `pytest tests/test_agent.py -k rag` | v03 |
| 第 6 章 工具边界：从本地工具到 MCP 协议 | 工具标准化、协议边界外化 | v04 | `book-ch06-anchor` | 已创建 | `git checkout book-ch06-anchor` | `mcp/` `agent/router.py` `agent/core.py` | `pytest tests/test_mcp.py` | v04 |
| 第 7 章 能力分层：Skills、Subagent 与角色协作 | 技能注册、角色拆分、委派协作、项目编排 | v05 | `book-ch07-anchor` | 已创建 | `git checkout book-ch07-anchor` | `skills/` `subagent/` `agent/project.py` | `python -m unittest tests.test_collaboration tests.test_project` | v05-v07 |
| 第 8 章 模型参与决策：tool calling 与 tool loop | LLM 决策、工具循环、结果收束 | v15 | `book-ch08-anchor` | 待创建 | `待创建后执行：git checkout book-ch08-anchor` | `agent/core.py` `agent/router.py` `integrations/` | `pytest tests/test_agent.py -k tool` | v15-v17 |
| 第 9 章 结构化运行时：LangGraph 与图式编排 | 图式工作流、节点边界、运行时结构化 | v12 | `book-ch09-anchor` | 待创建 | `待创建后执行：git checkout book-ch09-anchor` | `integrations/langgraph_workflow.py` `agent/workflow.py` | `pytest tests/test_agent.py -k graph` | v11-v14, v32-v35 |
| 第 10 章 可观测性、评估与发布门禁 | trace、eval、release gate | v06 | `book-ch10-anchor` | 待创建 | `待创建后执行：git checkout book-ch10-anchor` | `evals/` `agent/trace.py` `cli/release_gate.py` | `python -m cli.release_gate` | v06, v18-v25, v44-v45 |
| 第 11 章 恢复机制：checkpoint、run history、replay | 中断恢复、运行历史、replay 分析 | v26 | `book-ch11-anchor` | 待创建 | `待创建后执行：git checkout book-ch11-anchor` | `agent/checkpoint.py` `cli/main.py` `agent/run_history.py` | `pytest tests/test_agent.py -k checkpoint` | v26-v27, v36-v46 |
| 第 12 章 系统治理：registry、permission 与长期演进 | registry、permission、runtime policy、governance | v30 | `book-ch12-anchor` | 待创建 | `待创建后执行：git checkout book-ch12-anchor` | `skills/` `mcp/` `agent/runtime_policy.py` | `pytest tests/test_agent.py -k policy` | v28-v31, v41-v49 |
| 第 13 章 从学习项目到专业 Agent 系统 | 多智能体运行时、RAG 硬化、治理收束 | v51 | `book-ch13-anchor` | 待创建 | `待创建后执行：git checkout book-ch13-anchor` | `subagent/` `agent/` `integrations/` | `pytest` | v50-v51+ |

## 4. 章节锚点补充说明

### 关于概念章

第 1 章和第 2 章虽然不是“功能说明章”，但仍然必须绑定代码标签。原因是：

1. 本书不是纯理论书，必须让概念回到真实实现。
2. 读者在概念阶段就需要看到最小可运行结构。
3. 没有代码标签，前两章会重新退化成抽象讲义。

### 关于标签状态

当前仓库中已经创建了以下稳定章节标签：

- `book-ch01-anchor`
- `book-ch02-anchor`
- `book-ch03-anchor`
- `book-ch04-anchor`
- `book-ch07-anchor`

其余章节目前使用预留标签名表达章节锚点，待对应章节稳定后再正式创建。

## 5. 后续维护动作

后续每次处理书稿时，按下面顺序维护本文件：

1. 如果新增章节，先加锚点行
2. 如果章节改定位，先改主锚点版本和标签名
3. 如果确定了更合适的标签，更新标签状态与验证命令
4. 如果标签创建完成，将“待创建”更新为“已创建”

## 6. 与其他文件的关系

- 结构标准：`publish/book-structure-spec.md`
- 连续性机制：`publish/book-continuity-protocol.md`
- 章节映射：`publish/chapter-map.md`
- 当前恢复入口：`publish/current-book-summary.md`
