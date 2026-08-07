# 书籍大纲

## 目标读者

- Agent 开发初学者
- 想系统学习工程化 Agent 的开发者
- 需要从项目实践理解 RAG、MCP、Skills、LangGraph 的读者

## 推荐结构

1. 引言：为什么要从学习项目写成一本书。
2. 最小 Agent 闭环：输入、路由、工具、输出。
3. 状态与工作流：为什么 Agent 不能只靠一个函数。
4. 本地 RAG：从检索到 grounded answer。
5. MCP：从本地工具到协议边界。
6. Skills 与 Subagent：能力与角色的分层。
7. 工具调用与 tool loop：让模型参与多步决策。
8. LangGraph 编排：把执行路径结构化。
9. 可观测性、评估与恢复：让 Agent 可调试、可回归、可恢复。
10. 进阶能力：registry、permission、checkpoint、replay。
11. 总结：从 demo 到专业 Agent 工程。

## 版本到章节的落点

- v01-v02：最小闭环与状态工作流
- v03-v04：本地 RAG 与本地 MCP
- v05-v07：Skills、Subagent、学习工作台
- v08-v10：真实 LLM、DeepSeek RAG、WorkspaceAgent RAG
- v11-v14：工具适配、LangGraph、主链路接回
- v15-v17：tool calling、tool loop、final synthesis
- v18-v21：MCP / Skills tool loop、skill execution、trace
- v22-v25：skill node、failure recovery、runtime events
- v26-v27：checkpoint、run history、可恢复运行
- v28-v31：planner、registry、permission
- v32-v35：默认 graph runtime、workflow/tool_call/tool_loop graph 化

## 写作原则

- 每章先讲“解决什么问题”。
- 每章至少保留一个来自本项目的真实链路。
- 每章都要有验证命令或复盘入口。
- 每章结尾要说明下一章的承接点。
