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


## 参考答案

## 练习 1：理解本阶段边界

### 1. v18 为什么没有直接接入外部 MCP server？

因为 v18 的核心目标不是扩展外部系统，而是先打通工程边界。

本阶段优先验证：

- MCP 能力如何进入 `WorkspaceAgent` 的统一工具层。
- MCP 工具如何暴露到 `tool_schema`。
- LLM 如何选择 MCP 工具。
- MCP 工具结果如何进入 tool loop observations。
- final synthesis 如何基于 MCP / Skills observations 生成答案。

如果直接接入外部 MCP server，会同时引入网络、权限、认证、协议兼容、服务生命周期等变量，学习重点会被分散。

### 2. `mcp_read_project_file` 为什么要放在 `agent/tools.py`，而不是让 `WorkspaceAgent` 直接调用 `call_mcp_tool()`？

因为 `agent/tools.py` 是 Agent 的统一工具边界。

这样设计有几个好处：

- `WorkspaceAgent` 只负责调度，不直接关心 MCP adapter 细节。
- 所有工具都统一返回 `ToolResult`。
- MCP 工具和本地工具可以走同一套 `_call_tool()` 分发逻辑。
- 测试、trace、错误处理和后续扩展更一致。

如果 `WorkspaceAgent` 直接调用 `call_mcp_tool()`，MCP 细节会泄漏到核心编排层，后续工具体系会变得混乱。

### 3. 当前 Skills 为什么还不能算完整的“专业技能执行系统”？

因为当前 Skills 主要还是静态能力描述和计划选择。

当前已经有：

- `list_skills`
- `plan_skill`
- skill description
- skill selection

但还缺少：

- 标准化 skill input schema
- 标准化 skill output schema
- skill 执行状态
- skill 执行 trace
- skill step runner
- 错误恢复
- 权限控制
- 外部资源或工具调用能力

所以当前 Skills 是“可被 Agent 发现和选择的能力描述层”，还不是完整的“可执行技能系统”。

### 4. MCP / Skills 进入 tool loop 后，比规则路由直接调用多了什么能力？

规则路由直接调用通常是一次性动作：

```text
user input -> route_intent -> call one tool -> answer
```

进入 tool loop 后，MCP / Skills 可以参与多步推理：

```text
LLM selects MCP tool
-> observe MCP result
-> LLM selects Skills tool
-> observe Skills result
-> LLM decides whether enough
-> final synthesis
```

新增能力包括：

- LLM 可以根据前一步 observation 继续选择下一步工具。
- MCP / Skills 结果可以共同进入最终答案综合。
- trace 能记录每一步工具选择和观察结果。
- 系统可以检测重复工具调用，避免无限循环。
- 多个工具族可以组合完成一个目标。

### 5. 为什么本阶段仍然需要 deterministic tests？

因为真实 LLM 输出不稳定，不能作为基础回归测试的唯一依据。

deterministic tests 的作用是验证工程边界：

- tool schema 是否包含正确工具。
- tool input normalization 是否正确。
- `_call_tool()` 是否能分发到正确工具。
- MCP adapter 是否返回预期格式。
- tool loop 是否能记录 MCP / Skills observations。

这些能力必须稳定可重复，才能支撑真实 LLM 层的开发。

## 练习 2：读 MCP 文件读取链路

### 1. `mcp_read_project_file()` 接收什么参数？

它接收：

```python
root: Path
raw_path: str
```

含义：

- `root`：当前 workspace 根目录。
- `raw_path`：workspace-relative file path，例如 `README.md`。

### 2. 它最终调用 MCP server 的哪个 tool？

它通过 adapter 调用 MCP server 的：

```text
read_project_file
```

代码链路是：

```text
mcp_read_project_file()
-> call_mcp_tool(root, "read_project_file", {"path": raw_path})
-> LocalMCPClient.call_tool()
-> LocalMCPServer.call_tool()
-> LocalMCPServer._read_project_file()
```

### 3. MCP server 如何阻止路径逃逸？

`LocalMCPServer._read_project_file()` 会把请求路径解析成绝对路径，然后检查解析后的路径是否仍然在 workspace root 内。

核心逻辑是：

```python
path = (self.workspace_root / raw_path).resolve()
if self.workspace_root not in path.parents and path != self.workspace_root:
    return MCPResponse(request.tool_name, f"Path escapes workspace root: {raw_path}", is_error=True)
```

如果用户传入类似 `../outside.md` 的路径，解析后不在 workspace root 内，就会返回 MCP error。

### 4. `_call_tool()` 中新增的分支承担什么职责？

新增分支：

```python
if route.tool_name == "mcp_read_project_file":
    return mcp_read_project_file(self.workspace_root, route.tool_input or "")
```

职责是把 LLM 或 router 选出的工具名映射到真实工具函数。

它让 `WorkspaceAgent` 可以通过统一工具调度层调用 MCP 文件读取能力。

### 5. `test_agent_reads_project_file_through_mcp_tool` 验证了哪些行为？

它验证：

- 输入会进入 `tool_call` 路由。
- fake LLM 会选择 `mcp_read_project_file`。
- `tool_input` 会从指令文本归一化为 `README.md`。
- `WorkspaceAgent` 能执行 MCP 文件读取工具。
- 返回内容包含 `[mcp:ok]`。
- 返回内容包含 `[read_project_file] README.md`。

## 练习 3：读 tool input normalization

### 1. `_NO_ARGUMENT_TOOLS` 解决什么问题？

它解决“无参数工具被 LLM 错误传入自然语言 tool_input”的问题。

例如 LLM 可能返回：

```json
{
  "action": "use_tool",
  "tool_name": "mcp_workspace_summary",
  "tool_input": "Use MCP workspace summary.",
  "reason": "The task asks for workspace summary."
}
```

但 `mcp_workspace_summary` 不需要参数。  
归一化后，`tool_input` 应该变成 `None`。

### 2. `_PATH_INPUT_TOOLS` 解决什么问题？

它解决文件路径型工具的参数提取问题。

例如 LLM 可能返回：

```text
Use MCP to read README.md
```

这不是安全、干净的文件路径。  
代码会从原始用户请求中提取：

```text
README.md
```

当前 path-input tools 包括：

- `read_file`
- `count_lines`
- `mcp_read_project_file`

### 3. `_TASK_INPUT_TOOLS` 和 `_PATH_INPUT_TOOLS` 的差异是什么？

`_PATH_INPUT_TOOLS` 需要的是具体路径。

例如：

```text
README.md
docs/current-learning-state.md
```

`_TASK_INPUT_TOOLS` 需要的是完整任务或问题。

例如：

```text
Search docs for MCP tool loop design.
Plan a skill for code review.
```

区别是：

- path-input tool 要尽可能提取干净路径。
- task-input tool 要保留自然语言上下文。

### 4. 为什么不能直接相信 LLM 返回的 `tool_input`？

因为 LLM 返回的是文本生成结果，不是可信的程序参数。

可能的问题包括：

- 把完整指令当成路径。
- 给无参数工具传入多余文本。
- 漏掉必要参数。
- 返回格式接近正确但不能直接执行。
- 未来可能产生危险路径或无效参数。

所以代码必须做归一化和校验。

### 5. 如果 LLM 为 `mcp_workspace_summary` 返回 `"Use MCP workspace summary."`，最终 `tool_input` 应该是什么？

最终应该是：

```python
None
```

因为 `mcp_workspace_summary` 属于 `_NO_ARGUMENT_TOOLS`，不需要输入参数。

## 练习 4：读 MCP / Skills tool loop

### 1. `test_tool_loop_can_use_mcp_and_skills_as_capabilities` 中 LLM 依次选择了哪些动作？

依次选择：

1. `use_tool` -> `mcp_workspace_summary`
2. `use_tool` -> `list_skills`
3. `answer_directly`
4. final synthesis 返回最终答案文本

前 3 次是 tool loop 内部决策。  
第 4 次是 v17 引入的 final synthesis 调用。

### 2. 为什么 `mcp_workspace_summary` 和 `list_skills` 都可以进入 observations？

因为它们都通过 `_call_tool()` 返回统一的 `ToolResult`。

tool loop 执行工具后，会统一处理结果：

```text
observation = _preview_observation(result.output)
observations.append(f"{result.tool_name}: {observation}")
```

所以只要工具能返回 `ToolResult`，就可以进入 observations。

### 3. final synthesis 看到的是原始工具完整输出，还是 `_preview_observation()` 之后的摘要？

final synthesis 看到的是 `_preview_observation()` 之后的摘要。

原因是 `_run_tool_loop()` 存入 observations 的内容已经是 preview 后的结果。

这能避免把过长工具输出直接塞入下一轮 LLM 和 final synthesis prompt。

### 4. 如果 LLM 重复调用同一个 MCP 工具，tool loop 会如何停止？

tool loop 会记录重复工具调用并停止。

判断依据是：

```python
tool_key = (selection.tool_name, selection.tool_input)
```

如果同一个 `(tool_name, tool_input)` 已经出现过，就返回：

```text
stop_reason = "repeated_tool_call"
```

然后 final synthesis 会基于已有 observations 和停止原因生成最终答案；如果 synthesis 失败，则回退到 deterministic fallback。

### 5. 为什么 Skills 当前可以被综合，但还没有真正“执行技能”？

因为当前 Skills 工具返回的是技能描述或技能计划。

例如：

- `list_skills` 返回可用技能列表。
- `plan_skill` 返回某个任务适合的技能和步骤。

这些结果可以作为 observation 被 LLM 综合。  
但系统还没有真正执行 skill steps，也没有 skill runner、skill state、skill output schema 和 execution trace。

所以当前是“Skills planning / description”，不是完整的“Skills execution”。

## 练习 5：手动运行验证

### 1. 定向测试总共运行了多少个测试？

当前定向命令：

```bash
python -m unittest tests.test_mcp tests.test_tool_calling tests.test_tool_loop -v
```

运行结果：

```text
Ran 23 tests
OK
```

所以总共运行了 23 个测试。

### 2. 是否全部通过？

是，全部通过。

结果是：

```text
OK
```

### 3. 哪些测试是 v18 新增或直接相关？

v18 新增或直接相关测试包括：

- `tests.test_mcp.LocalMCPTests.test_agent_reads_project_file_through_mcp_tool`
- `tests.test_tool_calling.ToolCallingTests.test_tool_schema_exposes_mcp_file_reader`
- `tests.test_tool_calling.ToolCallingTests.test_select_tool_call_normalizes_mcp_file_path`
- `tests.test_tool_calling.ToolCallingTests.test_select_tool_call_removes_input_for_no_argument_mcp_tool`
- `tests.test_tool_loop.ToolLoopTests.test_tool_loop_can_use_mcp_and_skills_as_capabilities`

### 4. demo 的 route action 是什么？

命令：

```bash
python -m cli.tool_loop_demo --input "Use tool loop to inspect MCP workspace summary, list skills, and then answer." --trace
```

预期 route action 是：

```text
tool_loop
```

因为输入明确包含 `Use tool loop`。

### 5. tool loop 执行了几步？

在 deterministic test 中执行了 3 个 loop decision steps：

1. `mcp_workspace_summary`
2. `list_skills`
3. `answer_directly`

真实 LLM demo 中步数可能受模型选择影响，但理想路径也是 3 步。

### 6. 是否出现 `mcp_workspace_summary`？

预期应该出现。

它代表模型调用了 MCP workspace summary 工具。

### 7. 是否出现 `list_skills`？

预期应该出现。

它代表模型调用了 Skills 列表工具。

### 8. `Final answer source` 是什么？

如果真实 LLM final synthesis 成功，应该是：

```text
llm
```

如果 final synthesis 失败，应该是：

```text
deterministic_fallback
```

## 练习 6：阶段评估题

### 1. 现在项目中的 tool layer 包含哪些工具族？

当前包括：

- File tools
  - `read_file`
  - `list_dir`
  - `count_lines`
- RAG tools
  - `search_docs`
  - `answer_docs_with_llm`
- MCP tools
  - `list_mcp_tools`
  - `mcp_workspace_summary`
  - `mcp_read_project_file`
- Skills tools
  - `list_skills`
  - `plan_skill`
- Subagent tools
  - `list_subagents`
  - `plan_subagents`

### 2. MCP 和普通本地工具的主要边界差异是什么？

普通本地工具是 Agent 进程内直接执行的函数。

MCP 工具通过 MCP-like client / server / adapter 边界调用。

当前项目中 MCP 仍然是 in-process 学习实现，但已经体现了协议边界：

```text
agent tool wrapper
-> MCP adapter
-> LocalMCPClient
-> LocalMCPServer
-> MCPResponse
```

这个边界让未来接入外部 MCP server 更自然。

### 3. Skills 和 Subagent 在当前项目中的职责差异是什么？

Skills 关注“可复用任务能力”。

例如：

- research brief
- code review
- explanation

Subagent 关注“角色协作分工”。

例如：

- teacher agent
- coding agent
- 多 agent 协作计划

简单说：

```text
Skills = 能力模块
Subagents = 角色模块
```

### 4. 一个专业 Agent 项目为什么必须有 tool schema？

因为 LLM 需要明确知道：

- 有哪些工具可用。
- 每个工具做什么。
- 每个工具需要哪些参数。
- 参数类型和约束是什么。
- 什么情况下应该选择哪个工具。

没有 tool schema，LLM 只能凭自然语言猜工具，容易出现：

- 工具名错误
- 参数缺失
- 参数类型错误
- 多余参数
- 选错工具
- 无法稳定测试

tool schema 是专业 Agent tool layer 的基础契约。

### 5. 下一阶段如果要做真正的 Skills execution，你认为至少需要哪些数据结构？

至少需要：

- `SkillSpec`
  - skill name
  - purpose
  - input schema
  - output schema
  - required tools
- `SkillStep`
  - step index
  - action
  - tool name
  - input mapping
  - expected output
- `SkillRun`
  - run id
  - skill name
  - user task
  - status
  - steps
  - final output
- `SkillStepResult`
  - step index
  - status
  - observation
  - error
- `SkillExecutionTrace`
  - selected skill
  - input
  - executed steps
  - outputs
  - failures

这些结构能让 Skills 从“描述和计划”升级为“可执行、可测试、可追踪”的能力系统。

## 阶段结论

v18 的重点不是增加很多新工具，而是把 MCP / Skills 接入统一的 LLM tool layer。

本阶段完成后，需要理解的核心是：

```text
tool schema 定义模型可见能力
-> tool input normalization 修正模型参数
-> WorkspaceAgent._call_tool 执行工具
-> ToolResult 进入 observations
-> final synthesis 基于 observations 回答
```

这条链路是后续接入标准 MCP、可执行 Skills、LangGraph 默认主执行器的基础。
