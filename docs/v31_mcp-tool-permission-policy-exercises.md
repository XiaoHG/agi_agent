# v31 练习：MCP 工具注册与权限策略

## 练习目标

理解为什么专业 Agent 不能只暴露 MCP 工具名，还必须显式维护权限分类、默认策略和拒绝路径。

## 一、理解题

1. 为什么 v31 要新增 `permission_level`，而不是只靠工具描述文本说明风险？
   答：因为工具描述文本只适合给人看，不适合程序做一致的权限判断。`permission_level` 进入数据模型后，adapter、tests、eval、trace 和后续 graph state 才能统一知道一个 MCP 工具属于 `read_only`、`write`、`network` 还是 `destructive`。
2. 为什么默认策略要允许 `read_only`，但拒绝 `write`？
   答：因为当前学习项目要先建立“安全默认值”。只读工具通常风险低，适合作为 MCP 的默认可执行能力；写入工具会修改工作区内容，必须显式放行，才能体现专业 Agent 工具层的权限边界。
3. `MCPPermissionDecision` 为什么要进入 `MCPResponse.metadata`？
   答：因为权限判断结果不仅要显示给人看，还要进入结构化 trace 供测试、eval 和恢复分析使用。放进 `MCPResponse.metadata` 后，Agent wrapper 和 `WorkspaceAgent.to_trace_dict()` 都能直接拿到 `allowed`、`permission_level`、`reason` 和 `next_safe_action`。
4. 为什么 v31 要专门新增 `write_project_file`，而不是只给已有工具打上权限标签？
   答：因为如果现有工具全是 `read_only`，就无法证明策略真的在影响执行行为。新增 `write_project_file` 后，系统可以真实展示三条路径：工具已注册、默认拒绝、显式允许，这才构成完整的权限策略验证闭环。
5. 当前 refusal path 解决的是什么问题？它还没有解决什么问题？
   答：它解决的是“当工具被拒绝时，系统不再只是报错，而是能返回结构化、可解释、可测试的拒绝结果和下一步安全建议”。它还没有解决动态审批、按用户身份分配权限、跨会话策略管理、以及更细粒度的 destructive/network 工具治理。

## 二、源码定位题

1. `MCPPermissionPolicy` 和 `MCPPermissionDecision` 定义在哪个文件？
   答：定义在 `mcp/schema.py`。
2. 哪个函数构建默认 MCP 策略？
   答：`mcp/policy.py` 里的 `build_default_mcp_policy()`。
3. 哪个函数真正执行权限判断？
   答：`mcp/policy.py` 里的 `evaluate_mcp_tool_permission()`。
4. 哪个函数在调用 MCP 工具前先检查权限？
   答：`mcp/adapter.py` 里的 `call_mcp_tool_response()`。
5. `WorkspaceAgent` 是通过哪个工具 wrapper 调用 `write_project_file` 的？
   答：通过 `agent/tools.py` 里的 `mcp_write_project_file()` wrapper，再由 `WorkspaceAgent._call_tool()` 分发执行。

## 三、动手验证

运行：

```bash
python -m cli.mcp_demo --list-tools
```

回答：

1. 输出中是否包含 `write_project_file [write]`？
   答：包含。
2. 其他两个默认工具的权限标签是什么？
   答：`workspace_summary [read_only]` 和 `read_project_file [read_only]`。

再运行：

```bash
python -m cli.mcp_demo --tool write_project_file --path notes.txt --content "hello mcp"
```

回答：

1. 当前状态是 `[mcp:ok]` 还是 `[mcp:error]`？
   答：`[mcp:error]`。
2. 输出中是否包含 `Permission denied for MCP tool`？
   答：包含。
3. 输出中是否包含 `Next safe action`？
   答：包含。

最后运行：

```bash
python -m cli.mcp_demo --tool write_project_file --path notes.txt --content "hello mcp" --allow-write
```

回答：

1. 这次是否成功写入？
   答：成功写入。
2. 为什么这次和上一次行为不同？
   答：因为这次显式传入了 `--allow-write`，CLI 会构建 `MCPPermissionPolicy(allow_read_only=True, allow_write=True)`，所以 `write_project_file` 的权限判断从默认拒绝变成了允许执行。

## 四、测试题

运行：

```bash
python -m unittest tests.test_mcp tests.test_tool_calling -v
```

回答：

1. 哪个测试验证默认拒绝 write 工具？
   答：`test_adapter_denies_write_tool_by_default`。
2. 哪个测试验证显式允许 write 工具？
   答：`test_adapter_allows_write_tool_with_explicit_policy`。
3. 哪个测试验证 Agent 默认拒绝 MCP 写入？
   答：`test_agent_denies_mcp_write_by_default`。
4. 哪个测试验证 tool schema 已暴露 `mcp_write_project_file`？
   答：`tests/test_tool_calling.py` 中的 `test_tool_schema_exposes_mcp_write_tool`。

## 五、思考题

1. 如果未来有 `network` 和 `destructive` MCP 工具，当前布尔型策略是否够用？
   答：作为当前学习阶段的最小实现够用，但长期不够。后续通常需要更细粒度的策略，例如按工具名、按参数、按用户身份、按会话来源甚至按审批状态做判断，而不仅仅是四个布尔开关。
2. permission policy 更适合继续放在 adapter 层，还是应该前移到 Agent route / graph state？
   答：当前放在 adapter 层是合理的，因为它最接近 MCP 实际执行边界，能保证任何调用路径都先过同一层策略。后续如果 LangGraph 成为默认主执行器，策略结果还应同步进入 graph state，但真正的执行兜底仍应保留在 adapter 层。
3. 如果 project skill 想调用 write-capable MCP 工具，权限判断应该发生在 skill registry、tool runner，还是 MCP adapter？
   答：最可靠的判断点仍然是 MCP adapter。skill registry 可以声明意图，tool runner 可以传递上下文，但最终拒绝或允许必须发生在真正调用 MCP 工具之前，否则不同调用路径可能出现绕过策略的问题。
4. 为什么 v31 之后更适合进入“默认 LangGraph 主执行器”，而不是继续在 MCP 层再补更多工具？
   答：因为现在 RAG、Skills、MCP 都已经各自具备了较完整的结构化边界，继续再补单个 MCP 工具的收益会下降。下一步更关键的是把这些能力统一纳入主执行 runtime，让 direct answer、RAG、tool、skill、MCP 都在同一条 graph 执行链里协同工作。

## 六、验收标准

完成本练习后，你应该能说明：

- MCP 工具注册和权限策略是两个不同层次的问题。
- 工具“已注册”不代表“默认可执行”。
- refusal path 是专业 Agent 工具层的重要组成部分。

补充验证结果：

- `python -m unittest tests.test_mcp tests.test_tool_calling -v` 已通过。
- `python -m unittest discover -s tests -q` 结果为 `154` 个测试通过。
- `python -m cli.eval_runner` 结果为 `21/21` 通过。
