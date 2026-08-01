# Skills Execution 阶段练习

对应版本：v19  
主题：Structured Skills Execution  
用途：理解 Skills 如何从描述/规划升级为可执行 run

## 练习 1：理解阶段目标

请回答：

1. v19 和 v18 在 Skills 能力上的核心差异是什么？
2. 为什么当前 `execute_skill()` 仍然使用 deterministic execution？
3. 为什么不能直接让 `plan_skill()` 代表 skill execution？
4. 一个完整 Skills execution 系统至少需要记录哪些状态？
5. 当前 v19 离“专业 Skills 系统”还缺什么？

## 练习 2：读 `skills/execution.py`

阅读：

- `skills/execution.py`
- `skills/catalog.py`
- `skills/__init__.py`

请回答：

1. `SkillStepResult` 记录哪些字段？
2. `SkillRun` 记录哪些字段？
3. `execute_skill(task)` 内部第一步调用了什么函数？
4. 当前每个 step 的 `status` 是什么？
5. `SkillRun.to_text()` 为什么比直接返回一段字符串更好？

## 练习 3：读 Agent 工具接入链路

阅读：

- `agent/tools.py`
- `agent/core.py`
- `agent/tool_schema.py`
- `agent/tool_calling.py`
- `agent/router.py`

请回答：

1. `run_skill(task)` 的职责是什么？
2. `_call_tool()` 如何分发 `execute_skill`？
3. `tool_schema` 中 `execute_skill` 的参数是什么？
4. 为什么 `execute_skill` 属于 `_TASK_INPUT_TOOLS`？
5. router 如何识别 skill execution 请求？

## 练习 4：读 CLI 和测试

阅读：

- `cli/collaboration_demo.py`
- `tests/test_collaboration.py`
- `tests/test_tool_calling.py`

请回答：

1. CLI 新增了哪个参数？
2. `--execute-skill` 必须和哪个参数一起使用？
3. `test_execute_skill_returns_structured_run` 验证了什么？
4. `test_agent_executes_skill` 验证了什么？
5. `test_tool_schema_exposes_skill_execution` 验证了什么？

## 练习 5：手动运行验证

运行：

```bash
python -m unittest tests.test_collaboration tests.test_tool_calling -v
```

请记录：

1. 总共运行了多少个测试？
2. 是否全部通过？
3. 哪些测试是 v19 新增或直接相关？

运行：

```bash
python -m cli.collaboration_demo --task "Review this code and add tests." --execute-skill
```

请记录：

1. 输出的 skill 名称是什么？
2. status 是什么？
3. 执行了多少个 step？
4. final output 包含什么核心信息？

运行：

```bash
python -m cli.main --input "Execute skill for code review." --trace
```

请记录：

1. route action 是什么？
2. tool name 是什么？
3. final answer 是否包含 `Skill run`？
4. trace 中是否能看到 tool execution？

## 练习 6：阶段评估题

请用自己的话回答：

1. 为什么 `SkillRun` 是后续专业 Skills 系统的核心对象？
2. 如果未来 skill step 要调用 MCP tool，应该改哪一层，而不是改哪一层？
3. 当前 `SkillStepResult.observation` 的来源是什么？未来应该如何升级？
4. Skills execution 和 Subagent collaboration 的边界是什么？
5. 下一阶段做 skill runner 时，你认为最小可行设计是什么？

## 完成标准

可以进入下一阶段的标准：

- 能解释 `SkillSpec`、`SkillRun`、`SkillStepResult` 的关系。
- 能画出 `Execute skill for code review.` 的 Agent 调用链。
- 能说明 `plan_skill` 和 `execute_skill` 的差异。
- 能运行 CLI demo 并解释输出结构。
- 能指出下一阶段 skill runner 应该扩展的位置。
