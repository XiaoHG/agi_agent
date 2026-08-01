# MCP / Skills Tool Loop 阶段练习

对应版本：v18  
主题：MCP / Skills as tool loop capabilities  
用途：理解 MCP / Skills 如何进入统一 LLM tool layer

## 练习 1：理解本阶段边界

请回答：

1. v18 为什么没有直接接入外部 MCP server？
2. `mcp_read_project_file` 为什么要放在 `agent/tools.py`，而不是让 `WorkspaceAgent` 直接调用 `call_mcp_tool()`？
3. 当前 Skills 为什么还不能算完整的“专业技能执行系统”？
4. MCP / Skills 进入 tool loop 后，比规则路由直接调用多了什么能力？
5. 为什么本阶段仍然需要 deterministic tests？

## 练习 2：读 MCP 文件读取链路

阅读以下文件：

- `agent/tools.py`
- `agent/core.py`
- `agent/tool_schema.py`
- `mcp/adapter.py`
- `mcp/servers/local_server.py`
- `tests/test_mcp.py`

请回答：

1. `mcp_read_project_file()` 接收什么参数？
2. 它最终调用 MCP server 的哪个 tool？
3. MCP server 如何阻止路径逃逸？
4. `_call_tool()` 中新增的分支承担什么职责？
5. `test_agent_reads_project_file_through_mcp_tool` 验证了哪些行为？

## 练习 3：读 tool input normalization

阅读：

- `agent/tool_calling.py`
- `tests/test_tool_calling.py`

请回答：

1. `_NO_ARGUMENT_TOOLS` 解决什么问题？
2. `_PATH_INPUT_TOOLS` 解决什么问题？
3. `_TASK_INPUT_TOOLS` 和 `_PATH_INPUT_TOOLS` 的差异是什么？
4. 为什么不能直接相信 LLM 返回的 `tool_input`？
5. 如果 LLM 为 `mcp_workspace_summary` 返回 `"Use MCP workspace summary."`，最终 `tool_input` 应该是什么？

## 练习 4：读 MCP / Skills tool loop

阅读：

- `agent/core.py`
- `agent/tool_loop.py`
- `agent/tool_synthesis.py`
- `tests/test_tool_loop.py`

请回答：

1. `test_tool_loop_can_use_mcp_and_skills_as_capabilities` 中 LLM 依次选择了哪些动作？
2. 为什么 `mcp_workspace_summary` 和 `list_skills` 都可以进入 observations？
3. final synthesis 看到的是原始工具完整输出，还是 `_preview_observation()` 之后的摘要？
4. 如果 LLM 重复调用同一个 MCP 工具，tool loop 会如何停止？
5. 为什么 Skills 当前可以被综合，但还没有真正“执行技能”？

## 练习 5：手动运行验证

运行：

```bash
python -m unittest tests.test_mcp tests.test_tool_calling tests.test_tool_loop -v
```

请记录：

1. 总共运行了多少个测试？
2. 是否全部通过？
3. 哪些测试是 v18 新增或直接相关？

运行：

```bash
python -m cli.tool_loop_demo --input "Use tool loop to inspect MCP workspace summary, list skills, and then answer." --trace
```

请记录：

1. route action 是什么？
2. tool loop 执行了几步？
3. 是否出现 `mcp_workspace_summary`？
4. 是否出现 `list_skills`？
5. `Final answer source` 是什么？

## 练习 6：阶段评估题

请用自己的话回答：

1. 现在项目中的 tool layer 包含哪些工具族？
2. MCP 和普通本地工具的主要边界差异是什么？
3. Skills 和 Subagent 在当前项目中的职责差异是什么？
4. 一个专业 Agent 项目为什么必须有 tool schema？
5. 下一阶段如果要做真正的 Skills execution，你认为至少需要哪些数据结构？

## 完成标准

可以进入下一阶段的标准：

- 能画出 `mcp_read_project_file` 的完整调用链。
- 能解释无参数工具为什么要清空 `tool_input`。
- 能解释 path-input tool 和 task-input tool 的差异。
- 能说明 MCP / Skills observations 如何进入 final synthesis。
- 能运行定向测试并理解新增测试的覆盖范围。
