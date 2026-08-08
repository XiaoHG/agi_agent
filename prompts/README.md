# prompts/

放 prompt 文件和版本记录。

适合放：

- system prompt
- tool selection prompt
- reviewer prompt
- RAG answer prompt
- subagent role prompt
- prompt 变更记录

建议命名方式：

```text
prompts/
  v1_agent-system.md
  v2_tool-router.md
  v15_tool-calling.md
  v17_tool-loop-synthesis.md
  v28_langgraph-planner.md
  v39_direct-answer.md
```

prompt 应尽量通过配置加载，避免硬编码在业务代码里。
