# 阶段二-真实LLM与LangGraph-v08-v18

## 阶段结论

这个阶段的目标是让项目从“本地学习 Agent”进入“真实 LLM + LangGraph + tool execution”的主执行链。

## 版本链

- `v08` -> [正式版本](版本文档/v08_deepseek-llm-provider.md) -> [练习](../04-文档管理/项目文档/v08_deepseek-llm-provider-exercises.md)
- `v09` -> [正式版本](版本文档/v09_deepseek-rag.md) -> [练习](../04-文档管理/项目文档/v09_deepseek-rag-exercises.md)
- `v10` -> [正式版本](版本文档/v10_workspace-agent-deepseek-rag.md) -> [练习](../04-文档管理/项目文档/v10_workspace-agent-deepseek-rag-exercises.md)
- `v11` -> [正式版本](版本文档/v11_langchain-tool-adapter.md) -> [练习](../04-文档管理/项目文档/v11_langchain-tool-adapter-exercises.md)
- `v12` -> [正式版本](版本文档/v12_langgraph-workflow.md) -> [练习](../04-文档管理/项目文档/v12_langgraph-workflow-exercises.md)
- `v13` -> [正式版本](版本文档/v13_langgraph-conditional-routing.md) -> [练习](../04-文档管理/项目文档/v13_langgraph-conditional-routing-exercises.md)
- `v14` -> [正式版本](版本文档/v14_workspace-agent-langgraph.md) -> [练习](../04-文档管理/项目文档/v14_workspace-agent-langgraph-exercises.md)
- `v15` -> [正式版本](版本文档/v15_llm-tool-calling.md) -> [练习](../04-文档管理/项目文档/v15_llm-tool-calling-exercises.md)
- `v16` -> [正式版本](版本文档/v16_llm-tool-loop.md) -> [练习](../04-文档管理/项目文档/v16_llm-tool-loop-exercises.md)
- `v17` -> [正式版本](版本文档/v17_llm-tool-synthesis.md) -> [练习](../04-文档管理/项目文档/v17_llm-tool-synthesis-exercises.md)
- `v18` -> [正式版本](版本文档/v18_mcp-skills-tool-loop.md) -> [练习](../04-文档管理/项目文档/v18_mcp-skills-tool-loop-exercises.md)

## 关键关系

- `v08-v10`：真实 LLM 接入并和 RAG 结合
- `v11-v14`：LangChain / LangGraph 基础接入
- `v15-v18`：tool calling、tool loop、MCP、skills 全部接回执行主链

## 关联

- [[阶段三-Skills与运行证据-v19-v28]]
