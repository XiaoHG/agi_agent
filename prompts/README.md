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
  agent-system.v1.md
  tool-router.v1.md
  rag-answer.v1.md
  reviewer.v1.md
```

prompt 应尽量通过配置加载，避免硬编码在业务代码里。

