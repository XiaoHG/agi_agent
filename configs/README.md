# configs/

放配置模板。

适合放：

- 模型配置
- 工具开关
- RAG 参数
- 日志配置
- 权限策略
- 外部 registry / catalog 配置

不要提交真实密钥。密钥放 `.env`，并提供 `.env.example` 说明需要哪些环境变量。

当前学习项目支持：

- `AGI_AGENT_SKILL_REGISTRY_PATH`
- `AGI_AGENT_SKILL_POLICY_PROFILE`
- `AGI_AGENT_SKILL_GOVERNANCE_PROFILE`
- `AGI_AGENT_MCP_CATALOG_PATH`
- `AGI_AGENT_MCP_POLICY_PROFILE`
- `AGI_AGENT_MCP_GOVERNANCE_PROFILE`
