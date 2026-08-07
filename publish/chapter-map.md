# 章节映射

## 章节总览

1. 导论：为什么要把学习项目写成书
2. 最小 Agent 闭环
3. 状态与工作流
4. 本地 RAG 与本地 MCP
5. Skills 与 Subagent
6. 真实 LLM、tool calling 与 tool loop
7. LangGraph 编排
8. 可观测性、评估与恢复
9. 专业化能力：registry、permission、checkpoint、replay
10. 总结与实践方法

## 版本映射

| 版本 | 书稿章节 | 主题 |
| --- | --- | --- |
| v01-v02 | 第 2-3 章 | 最小闭环、状态与工作流 |
| v03-v04 | 第 4 章 | 本地 RAG、MCP 协议骨架 |
| v05-v07 | 第 5 章 | Skills、Subagent、学习工作台 |
| v08-v10 | 第 6 章 | 真实 LLM、DeepSeek RAG、WorkspaceAgent RAG |
| v11-v14 | 第 7 章 | 工具适配、LangGraph、主链路接回 |
| v15-v17 | 第 6-7 章 | tool calling、tool loop、final synthesis |
| v18-v21 | 第 5-8 章 | MCP/Skills tool loop、skill execution、trace |
| v22-v25 | 第 8 章 | skill node、failure recovery、runtime events |
| v26-v27 | 第 8 章 | checkpoint、run history、可恢复运行 |
| v28-v31 | 第 9 章 | planner、RAG v1、skill registry、权限策略 |
| v32-v35 | 第 7-9 章 | 默认 graph runtime、workflow/tool_call/tool_loop graph 化 |

## 写作原则

- 一章对应一组版本，而不是一版对应一章。
- 版本是素材，章节是表达。
- 同一主题的版本迭代应合并成连续叙述。
- 每个版本都要能落到章节中的一个小节或案例。
