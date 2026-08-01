# Skills Execution 阶段练习答案

对应版本：v19  
主题：Structured Skills Execution  
用途：阶段复盘与下一阶段恢复学习

## 练习 1：理解阶段目标

### 1. v19 和 v18 在 Skills 能力上的核心差异是什么？

v18 的 Skills 主要是“可被发现、可被选择、可进入 tool loop observation”。

v19 的 Skills 开始具备“可执行 run”的结构。

差异可以概括为：

```text
v18: list_skills / plan_skill
v19: execute_skill -> SkillRun -> SkillStepResult
```

v18 关注的是让 Skills 成为 LLM tool layer 中的一等能力。  
v19 关注的是让 Skills 有执行记录、步骤状态、最终输出和可测试边界。

### 2. 为什么当前 `execute_skill()` 仍然使用 deterministic execution？

因为本阶段目标是先建立 Skills execution 的工程边界，而不是马上接入真实外部执行。

deterministic execution 的价值是：

- 行为稳定，便于测试。
- 输出可预测，便于回归。
- 能先验证 `SkillRun`、`SkillStepResult`、Agent tool、CLI、router、tool schema 的链路。
- 避免真实 LLM、MCP、外部工具引入额外不确定性。

等结构稳定后，再把 step observation 替换为真实 runner 结果。

### 3. 为什么不能直接让 `plan_skill()` 代表 skill execution？

因为 `plan_skill()` 只负责选择和描述技能，不代表已经执行。

`plan_skill()` 输出的是：

```text
Skill name
Purpose
Steps
Output format
```

这相当于执行前的计划。

`execute_skill()` 输出的是：

```text
SkillRun
Status
Executed steps
Step observations
Final output
```

这才是执行后的记录。

如果用 `plan_skill()` 代替 execution，会混淆“计划”和“执行”，后续无法记录 step status、失败原因、trace 和真实输出。

### 4. 一个完整 Skills execution 系统至少需要记录哪些状态？

至少需要：

- skill 名称
- 用户任务
- run status
- 每个 step 的 index
- 每个 step 的 instruction
- 每个 step 的 status
- 每个 step 的 observation
- step error
- final output
- 执行开始和结束时间
- 被调用的工具或外部资源

当前 v19 已经有：

- `SkillRun.task`
- `SkillRun.skill`
- `SkillRun.status`
- `SkillRun.steps`
- `SkillRun.final_output`
- `SkillStepResult.index`
- `SkillStepResult.instruction`
- `SkillStepResult.status`
- `SkillStepResult.observation`

后续还需要补 error、时间、tool call trace 等。

### 5. 当前 v19 离“专业 Skills 系统”还缺什么？

当前还缺：

- 动态 step runner
- step action 类型
- step input / output schema
- step-level error handling
- failed / skipped / retry 状态
- 调用本地 tools、RAG、MCP、Subagent 的能力
- 权限控制
- 真实执行日志
- skill 版本管理
- skill 配置文件或外部 skill registry

所以 v19 是 Skills execution 的最小结构化版本，还不是完整专业技能系统。

## 练习 2：读 `skills/execution.py`

### 1. `SkillStepResult` 记录哪些字段？

`SkillStepResult` 记录：

```python
index: int
instruction: str
status: str
observation: str
```

含义：

- `index`：步骤序号。
- `instruction`：当前步骤说明。
- `status`：步骤状态。
- `observation`：步骤产生的观察结果。

### 2. `SkillRun` 记录哪些字段？

`SkillRun` 记录：

```python
task: str
skill: SkillSpec
status: str
steps: list[SkillStepResult]
final_output: str
```

含义：

- `task`：用户原始任务。
- `skill`：被选择的技能。
- `status`：本次执行状态。
- `steps`：所有步骤执行结果。
- `final_output`：最终输出。

### 3. `execute_skill(task)` 内部第一步调用了什么函数？

第一步调用：

```python
select_skill(task)
```

它先根据任务选择最合适的内置技能，然后再为该技能的每个标准步骤生成 `SkillStepResult`。

### 4. 当前每个 step 的 `status` 是什么？

当前每个 step 的状态都是：

```text
completed
```

这是因为 v19 仍是 deterministic execution，没有引入真实失败、跳过、重试等状态。

### 5. `SkillRun.to_text()` 为什么比直接返回一段字符串更好？

因为 `SkillRun` 先保留结构化状态，再负责渲染文本。

好处：

- 测试可以检查结构化字段。
- trace 可以复用 run 信息。
- 后续可以导出 JSON。
- 可以支持 step-level 状态和错误。
- final output 和 executed steps 不会混在一段不可解析文本里。

直接返回字符串短期简单，但后续难以测试、追踪和扩展。

## 练习 3：读 Agent 工具接入链路

### 1. `run_skill(task)` 的职责是什么？

`run_skill(task)` 是 Agent 工具层的包装函数。

它负责：

```text
task
-> execute_skill(task)
-> SkillRun.to_text()
-> ToolResult("execute_skill", output)
```

它让 Skills execution 通过统一 `ToolResult` 接入 Agent。

### 2. `_call_tool()` 如何分发 `execute_skill`？

`WorkspaceAgent._call_tool()` 中新增分支：

```python
if route.tool_name == "execute_skill":
    return run_skill(route.tool_input or "")
```

当 router 或 LLM tool calling 选择 `execute_skill` 时，Agent 会通过这个分支执行 skill。

### 3. `tool_schema` 中 `execute_skill` 的参数是什么？

参数是：

```text
task: string
```

描述是：

```text
Task description.
```

因为执行 skill 需要完整任务描述，而不是文件路径或无参数调用。

### 4. 为什么 `execute_skill` 属于 `_TASK_INPUT_TOOLS`？

因为 `execute_skill` 需要自然语言任务上下文。

例如：

```text
Review this code and add tests.
Explain RAG architecture.
Research MCP adoption patterns.
```

这些任务不能被简化成路径。  
所以它属于 `_TASK_INPUT_TOOLS`，应该保留完整任务输入。

### 5. router 如何识别 skill execution 请求？

router 新增了：

```python
_looks_like_skill_execution_request()
```

它识别这些关键词：

- `execute skill`
- `run skill`
- `use skill`
- `perform skill`
- `skill execution`

当用户输入命中这些表达，并且属于 skill 请求时，会路由到：

```text
action=use_tool
tool_name=execute_skill
```

## 练习 4：读 CLI 和测试

### 1. CLI 新增了哪个参数？

新增参数：

```bash
--execute-skill
```

### 2. `--execute-skill` 必须和哪个参数一起使用？

必须和：

```bash
--task
```

一起使用。

示例：

```bash
python -m cli.collaboration_demo --task "Review this code and add tests." --execute-skill
```

### 3. `test_execute_skill_returns_structured_run` 验证了什么？

它验证：

- `execute_skill()` 能返回结构化 `SkillRun`。
- 对代码评审任务会选择 `code_review` skill。
- run 状态是 `completed`。
- step 数量等于 skill 定义里的步骤数量。
- final output 包含已执行技能的信息。

### 4. `test_agent_executes_skill` 验证了什么？

它验证：

- `WorkspaceAgent` 能把 `Execute skill for code review.` 路由到 `execute_skill`。
- Agent 能通过 `_call_tool()` 执行 skill。
- 最终答案包含 `Skill run: code_review`。
- 最终答案包含 `Executed steps`。

### 5. `test_tool_schema_exposes_skill_execution` 验证了什么？

它验证 `execute_skill` 已经进入 workspace tool schema。

也就是说，LLM tool calling 可以看到这个工具，并有机会选择它。

## 练习 5：手动运行验证

### 1. 定向测试总共运行了多少个测试？

命令：

```bash
python -m unittest tests.test_collaboration tests.test_tool_calling -v
```

当前结果：

```text
Ran 24 tests
OK
```

所以总共运行 24 个测试。

### 2. 是否全部通过？

是，全部通过。

结果：

```text
OK
```

### 3. 哪些测试是 v19 新增或直接相关？

v19 新增或直接相关测试：

- `test_execute_skill_returns_structured_run`
- `test_route_to_execute_skill`
- `test_agent_executes_skill`
- `test_collaboration_demo_executes_skill`
- `test_tool_schema_exposes_skill_execution`

### 4. CLI demo 输出的 skill 名称是什么？

命令：

```bash
python -m cli.collaboration_demo --task "Review this code and add tests." --execute-skill
```

输出的 skill 名称是：

```text
code_review
```

### 5. status 是什么？

状态是：

```text
completed
```

### 6. 执行了多少个 step？

执行了 4 个 step：

1. Inspect changed files.
2. Check behavior and edge cases.
3. Run relevant tests.
4. Report issues and safe fixes.

### 7. final output 包含什么核心信息？

final output 包含：

- 执行了哪个 skill。
- 针对哪个 task。
- 期望输出格式是什么。

示例核心内容：

```text
Executed skill 'code_review' for task 'Review this code and add tests.'.
Expected output format: Review notes with issues, evidence, and recommended fixes.
```

### 8. `cli.main` demo 的 route action 是什么？

命令：

```bash
python -m cli.main --input "Execute skill for code review." --trace
```

route action 是：

```text
use_tool
```

### 9. tool name 是什么？

tool name 是：

```text
execute_skill
```

### 10. final answer 是否包含 `Skill run`？

是。

final answer 包含：

```text
Skill run: code_review
```

### 11. trace 中是否能看到 tool execution？

能看到。

trace 中包含：

```text
Run tool: execute_skill completed
[Tool] execute_skill
```

## 练习 6：阶段评估题

### 1. 为什么 `SkillRun` 是后续专业 Skills 系统的核心对象？

因为 `SkillRun` 是一次 skill 执行的状态载体。

后续专业系统需要围绕它扩展：

- 执行状态
- 每一步结果
- 错误信息
- 工具调用记录
- 输出结果
- trace
- 持久化
- 复盘

如果没有 `SkillRun`，skill execution 只会变成一段文本，无法可靠测试和恢复。

### 2. 如果未来 skill step 要调用 MCP tool，应该改哪一层，而不是改哪一层？

应该改 Skills execution / skill runner 层。

具体是扩展：

- `skills/execution.py`
- 未来的 `SkillStep`
- 未来的 step runner

不应该改 `WorkspaceAgent` 主循环。

原因是 Agent 主循环只负责调度工具，不应该知道每个 skill step 内部如何执行。

### 3. 当前 `SkillStepResult.observation` 的来源是什么？未来应该如何升级？

当前来源是：

```python
_build_step_observation(skill, task, instruction)
```

它生成 deterministic 文本。

未来应该升级为真实 step runner 的输出，例如：

- 本地工具调用结果
- RAG 检索结果
- MCP tool response
- Subagent 输出
- LLM 综合结果

同时 observation 应该配套 error、metadata、tool name、input、output 等结构化信息。

### 4. Skills execution 和 Subagent collaboration 的边界是什么？

Skills execution 关注“任务能力如何执行”。

例如：

```text
code_review skill
-> inspect changed files
-> check edge cases
-> run tests
-> report issues
```

Subagent collaboration 关注“角色如何协作”。

例如：

```text
teacher_agent explains
coding_agent implements
```

简单区分：

```text
Skills = capability / procedure
Subagents = role / responsibility
```

### 5. 下一阶段做 skill runner 时，你认为最小可行设计是什么？

最小可行设计：

1. 增加 `SkillStep` 数据结构。
2. 给每个 step 定义：
   - action
   - tool_name
   - input_template
   - required
3. 增加 `run_skill_step()`。
4. 让 step runner 可以调用现有 Agent tools。
5. `SkillStepResult` 增加：
   - error
   - tool_name
   - tool_input
   - raw_output
6. `SkillRun.status` 支持：
   - completed
   - failed
   - partial
7. 增加测试：
   - 成功执行
   - 工具失败
   - step 停止
   - trace 输出

这样可以在不重写 Agent 主循环的前提下，让 Skills 从 deterministic execution 升级为真实 tool-backed execution。

## 阶段结论

v19 的重点是建立 Skills execution 的最小工程结构。

本阶段核心链路是：

```text
SkillSpec
-> select_skill(task)
-> execute_skill(task)
-> SkillStepResult
-> SkillRun
-> ToolResult("execute_skill")
-> WorkspaceAgent answer / trace
```

需要重点理解：

- `plan_skill` 是规划。
- `execute_skill` 是执行。
- `SkillRun` 是执行状态。
- `SkillStepResult` 是步骤证据。
- 当前 deterministic execution 是为了稳定测试。
- 下一阶段应该扩展 skill runner，而不是污染 Agent 主循环。
