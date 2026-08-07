# Tool-backed Skills 阶段练习

对应版本：v20  
主题：Skill runner 接入 workspace tool layer  
用途：理解 Skills 如何从 deterministic execution 升级为 tool-backed execution

## 练习 1：理解阶段目标

请回答：

1. v20 相比 v19 解决了什么核心问题？

   答案：v19 只建立了结构化的 `SkillRun` 和 `SkillStepResult`，但 step observation 仍主要是 deterministic 文本。v20 解决的核心问题是：让 skill step 可以通过 `SkillToolRunner` 调用真实 workspace tools，并把工具输出写入 `SkillStepResult.observation`。

   简单说：

   ```text
   v19: skill step -> deterministic observation
   v20: skill step -> SkillToolRequest -> workspace tool -> SkillToolResponse -> SkillStepResult
   ```

2. 为什么 `skills/` 包不能直接导入 `agent.tools`？

   答案：因为 `skills/` 是能力定义和执行协议层，`agent.tools` 是 Agent runtime 的具体工具实现层。如果 `skills/` 直接导入 `agent.tools`，会形成反向依赖，让 Skills 包依赖 Agent 主循环和工具实现，后续很难复用、测试和迁移。

   更合理的边界是：

   ```text
   skills/ 定义 SkillToolRequest / SkillToolResponse
   agent/tools.py 提供 workspace runner
   execute_skill(..., tool_runner=runner) 通过注入调用工具
   ```

3. deterministic skill execution 和 tool-backed skill execution 的区别是什么？

   答案：deterministic skill execution 不调用真实工具，只生成可预测的 planned observation；tool-backed skill execution 会通过 runner 调用真实 workspace tools，例如 `list_dir`、`search_docs`，并把真实工具输出压缩后写入 step observation。

4. `SkillRun.status` 为什么应该由 step results 决定？

   答案：因为 `SkillRun` 是一次 skill 执行的总状态，而总状态必须来自每个 step 的执行结果。如果所有 step 都 completed，run 才能是 completed；如果某个关键 tool step failed，run 就应该变成 failed。否则 run status 会和实际执行证据不一致。

5. 为什么 runner 失败时要停止后续 step？

   答案：因为后续 step 往往依赖前面 step 的 observation。当前阶段还没有实现 retry、skip、partial recovery，所以遇到 tool error 后立即停止，可以避免基于错误或缺失上下文继续执行，保持行为简单、可测试、可解释。

## 练习 2：读 `skills/execution.py`

阅读：

- `skills/execution.py`
- `skills/__init__.py`

请回答：

1. `SkillStep` 和 `SkillStepResult` 的区别是什么？

   答案：`SkillStep` 是“计划步骤”，描述要做什么；`SkillStepResult` 是“执行结果”，记录实际执行后的状态和 observation。

   对应关系：

   ```text
   SkillStep = plan
   SkillStepResult = result
   ```

   `SkillStep` 包含 `action`、`tool_name`、`tool_input` 等计划字段；`SkillStepResult` 包含 `status`、`observation`、`error` 等执行结果字段。

2. `SkillToolRequest` 包含哪些字段？

   答案：包含：

   ```python
   tool_name: str
   tool_input: str
   ```

   它表示 skill step 要请求 runner 调用哪个工具，以及传入什么输入。

3. `SkillToolResponse` 包含哪些字段？

   答案：包含：

   ```python
   tool_name: str
   output: str
   is_error: bool = False
   ```

   它表示 runner 实际执行的工具名、工具输出，以及是否失败。

4. `execute_skill(task, tool_runner=None)` 在没有 runner 时如何处理 tool step？

   答案：没有 runner 时，tool step 不会真实调用工具，而是生成 planned-tool observation。

   例如：

   ```text
   Planned tool: list_dir; input: .
   ```

   这样可以保持 deterministic execution，便于基础测试和学习。

5. `execute_skill(task, tool_runner=runner)` 在 runner 返回 error 时如何处理？

   答案：当 runner 返回 `SkillToolResponse(is_error=True)` 时，当前 step 会生成 `SkillStepResult(status="failed")`，`error` 字段记录失败信息，`SkillRun.status` 会变成 `failed`，并停止后续 step。

## 练习 3：读 workspace runner

阅读：

- `agent/tools.py`
- `agent/core.py`
- `agent/__init__.py`

请回答：

1. `run_skill_with_workspace(root, task)` 的职责是什么？

   答案：它负责把 Agent 当前 workspace root 注入到 skill execution 中，让 `execute_skill()` 可以通过 workspace runner 调用真实工具。

   调用链是：

   ```text
   run_skill_with_workspace(root, task)
   -> _build_skill_tool_runner(root)
   -> execute_skill(task, tool_runner=runner)
   -> ToolResult("execute_skill", SkillRun.to_text())
   ```

2. `_build_skill_tool_runner(root)` 当前支持哪些工具？

   答案：当前支持：

   - `list_dir`
   - `read_file`
   - `search_docs`
   - `list_mcp_tools`
   - `mcp_workspace_summary`

3. 不支持的 tool name 会如何处理？

   答案：会返回一个 error response：

   ```python
   SkillToolResponse(request.tool_name, f"Unsupported skill tool: {request.tool_name}", True)
   ```

   然后 `execute_skill()` 会把当前 step 标记为 failed，并让整个 `SkillRun.status` 变成 `failed`。

4. `WorkspaceAgent._call_tool()` 为什么要调用 `run_skill_with_workspace()` 而不是 `execute_skill()`？

   答案：因为 `WorkspaceAgent` 持有真实的 `workspace_root`。调用 `run_skill_with_workspace(self.workspace_root, task)` 可以让 skill runner 在正确工作区内执行 `list_dir`、`read_file`、`search_docs` 等工具。

   如果直接调用 `execute_skill()`，就没有 workspace runner，tool step 只会生成 planned observation，不会真实调用工具。

5. `run_skill()` 和 `run_skill_with_workspace()` 的差异是什么？

   答案：`run_skill()` 是普通工具包装，内部使用 `Path(".")` 构建 runner；`run_skill_with_workspace(root, task)` 显式接收 workspace root，更适合 `WorkspaceAgent` 使用。

   当前 Agent 主流程应该优先使用 `run_skill_with_workspace()`，因为它能保证工具运行在 Agent 的 workspace root 内。

## 练习 4：读 CLI 和测试

阅读：

- `cli/collaboration_demo.py`
- `tests/test_collaboration.py`

请回答：

1. CLI 新增了哪个参数？

   答案：新增了：

   ```bash
   --tool-backed
   ```

2. `--tool-backed` 必须配合哪个参数使用？

   答案：必须配合：

   ```bash
   --execute-skill
   ```

   典型命令是：

   ```bash
   python -m cli.collaboration_demo --task "Review this code and add tests." --execute-skill --tool-backed
   ```

3. `test_build_skill_steps_marks_tool_backed_steps` 验证了什么？

   答案：它验证 `build_skill_steps()` 会把 `code_review` skill 的部分步骤标记为 tool-backed step。

   例如：

   - 第 1 步调用 `list_dir`
   - 第 2 步调用 `search_docs`
   - 第 3 步调用 `search_docs`
   - 最后一步保持 record-only

4. `test_execute_skill_uses_tool_runner` 验证了什么？

   答案：它验证当传入 fake runner 时，`execute_skill()` 会真实调用 runner，并把 runner 返回的 output 写入 `SkillStepResult.observation`。

   这证明 `execute_skill(task, tool_runner=runner)` 已经不是单纯 deterministic 文本生成。

5. `test_execute_skill_stops_on_tool_error` 验证了什么？

   答案：它验证 runner 返回 error 时：

   - `SkillRun.status` 变成 `failed`
   - 只执行到失败 step
   - 失败 step 的 `status` 是 `failed`
   - final output 中包含 failed step 统计

## 练习 5：手动运行验证

运行：

```bash
python -m unittest tests.test_collaboration -v
```

请记录：

1. 总共运行了多少个测试？

   答案：当前运行：

   ```bash
   python -m unittest tests.test_collaboration -v
   ```

   结果是：

   ```text
   Ran 20 tests
   OK
   ```

   所以总共运行 20 个测试。

2. 是否全部通过？

   答案：是，全部通过，结果为 `OK`。

3. 哪些测试是 v20 新增或直接相关？

   答案：v20 新增或直接相关测试包括：

   - `test_build_skill_steps_marks_tool_backed_steps`
   - `test_execute_skill_uses_tool_runner`
   - `test_execute_skill_stops_on_tool_error`
   - `test_collaboration_demo_executes_tool_backed_skill`
   - `test_agent_executes_skill`

   其中 `test_agent_executes_skill` 在 v20 中加强了断言，验证输出包含真实 tool-backed 信息。

运行：

```bash
python -m cli.collaboration_demo --task "Review this code and add tests." --execute-skill --tool-backed
```

请记录：

1. 输出的 skill 名称是什么？

   答案：输出的 skill 名称是：

   ```text
   code_review
   ```

2. status 是什么？

   答案：status 是：

   ```text
   completed
   ```

3. 哪些 step 调用了 tool？

   答案：前三个 step 调用了 tool：

   1. `Inspect changed files.` -> `list_dir`
   2. `Check behavior and edge cases.` -> `search_docs`
   3. `Run relevant tests.` -> `search_docs`

   第四个 step：

   ```text
   Report issues and safe fixes.
   ```

   是 record-only step。

4. final output 中 completed / failed / tool-backed step 数量分别是多少？

   答案：当前 demo 的 final output 中：

   ```text
   Completed steps: 4; failed steps: 0; tool-backed steps: 3.
   ```

运行：

```bash
python -m cli.main --input "Execute skill for code review." --trace
```

请记录：

1. route action 是什么？

   答案：route action 是：

   ```text
   use_tool
   ```

2. tool name 是什么？

   答案：tool name 是：

   ```text
   execute_skill
   ```

3. trace 中是否包含 `execute_skill completed`？

   答案：包含。

   trace 中会出现：

   ```text
   Run tool: execute_skill completed
   ```

4. final answer 是否包含 `tool-backed steps`？

   答案：包含。

   final answer 中会出现类似：

   ```text
   Completed steps: 4; failed steps: 0; tool-backed steps: 3.
   ```

## 练习 6：阶段评估题

请用自己的话回答：

1. 为什么 `SkillToolRequest` / `SkillToolResponse` 是专业 Skills 系统的重要边界？

   答案：因为它们把 Skills execution 和具体工具实现解耦。

   `SkillToolRequest` 表示 skill step 想调用什么工具；`SkillToolResponse` 表示 runner 返回了什么结果。Skills 包只依赖这个协议，不需要知道工具实际来自本地函数、MCP、RAG、Subagent 还是 LangGraph。

   这让后续扩展更清晰：

   ```text
   skills/ -> request/response protocol
   agent/ -> concrete tool runner
   mcp/ -> external protocol tools
   rag/ -> knowledge tools
   ```

2. 如果未来某个 skill step 要调用 MCP read_project_file，应该在哪里扩展？

   答案：应该主要扩展两处：

   1. `skills/execution.py` 的 `build_skill_steps()`：为某个 step 配置 `tool_name="mcp_read_project_file"` 和对应 `tool_input`。
   2. `agent/tools.py` 的 `_build_skill_tool_runner()`：增加对 `mcp_read_project_file` 的分发支持。

   不应该让 `skills/` 直接调用 MCP adapter 或 Agent tools。

3. 如果未来要让 Skills 支持重试，你会扩展哪些字段和逻辑？

   答案：至少需要扩展：

   - `SkillStep` 增加 `max_retries`
   - `SkillStepResult` 增加 `attempts`
   - `SkillStepResult` 增加每次尝试的 error / observation
   - `_run_step()` 增加 retry loop
   - `SkillRun.status` 支持 `partial` 或 `failed_after_retries`
   - 测试覆盖首次失败后重试成功、全部重试失败两种场景

4. 当前 tool-backed execution 和 LangGraph node 有什么关系？

   答案：当前 tool-backed execution 已经具备成为 LangGraph node 的基础。

   原因是它有清晰输入、输出和状态：

   ```text
   input: task
   process: execute_skill with runner
   output: SkillRun
   status: completed / failed
   steps: SkillStepResult list
   ```

   后续可以把 `execute_skill` 包装成 LangGraph 的一个 node，让图负责决定什么时候执行 skill、失败后走哪条边、是否进入 fallback。

5. 下一阶段如果做 skill trace / JSON export，应该优先导出哪些字段？

   答案：应该优先导出：

   - `task`
   - `skill.name`
   - `skill.purpose`
   - `SkillRun.status`
   - `final_output`
   - 每个 step 的：
     - `index`
     - `instruction`
     - `action`
     - `tool_name`
     - `tool_input`
     - `status`
     - `observation`
     - `error`

   这些字段足够支持调试、测试、eval 和跨会话复盘。

## 完成标准

可以进入下一阶段的标准：

- 能解释 deterministic execution 和 tool-backed execution 的差异。
- 能画出 `execute_skill -> SkillToolRunner -> workspace tool -> SkillRun` 的链路。
- 能解释为什么 Skills 包不直接依赖 Agent 包。
- 能说明 tool step 失败时 `SkillRun.status` 如何变化。
- 能运行 CLI tool-backed demo 并解释输出。
