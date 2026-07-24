# 状态与工作流 v2

版本：v2

日期：2026-07-24

## 目标

这次迭代是在最小 Agent 闭环之上，加入第一层多步执行能力。

新增能力包括：

- 可变执行状态
- 简单工作流规划
- 顺序执行工具
- 工作流结果汇总

## 新增文件

### `agent/state.py`

新增文件。

精确行号范围：`1-53`

职责：

- 定义 `AgentStep`
- 定义 `AgentState`
- 记录 trace 步骤
- 记录工具结果
- 提供状态更新辅助方法

### `agent/workflow.py`

新增文件。

精确行号范围：`1-178`

职责：

- 定义 `WorkflowStep`
- 定义 `WorkflowPlan`
- 根据用户输入构建顺序计划
- 将工作流结果汇总成最终回答

### `versions/README.md`

新增文件。

精确行号范围：`1-19`

职责：

- 说明迭代文件的保存方式
- 约束 `*_v2.md` / `*_v3.md` 的命名规范

## 修改文件

### `agent/core.py`

变更行号范围：

- imports 和工作流接入：`11-12`、`50-63`、`85-128`
- 其余单步流程保持不变

本次改动：

- imports 中加入 `AgentState` 和工作流辅助函数
- `WorkspaceAgent.run()` 增加 `workflow` 分支
- 新增 `_run_workflow()` 执行路径
- 工作流失败单独处理
- 工作流结果会被汇总成最终回答

新增行为：

1. 接收输入
2. 加载提示词
3. 路由判断
4. 如果路由结果是 `workflow`，则构建工作流计划
5. 按顺序执行每一个工作流步骤
6. 将工具结果记录到可变状态中
7. 基于已收集的结果汇总最终回答

### `agent/router.py`

变更行号范围：

- 工作流识别辅助函数：`80-94`
- 工作流路由分支：`115-120`

本次改动：

- 新增 `_looks_like_workflow_request()`
- 新增 `workflow` 路由

新增行为：

- 如果请求中包含 `and then`、`then`、`after that`、`step by step` 等顺序型表达，就进入工作流路径

### `agent/__init__.py`

变更行号范围：

- 导出更新：`3-6`、`8-20`

本次改动：

- 导出 `AgentState`
- 从 `agent.state` 导出 `AgentStep`

### `tests/test_agent.py`

变更行号范围：

- 工作流测试：`32-42`

本次改动：

- 增加工作流路由覆盖
- 增加工作流执行测试

## 新交互流程

### 单步流程

```text
input -> route -> direct answer or one tool -> answer
```

### 工作流流程

```text
input -> route(workflow) -> plan -> step 1 -> step 2 -> synthesis -> answer
```

## 示例工作流

输入：

```text
Read README.md and then count lines.
```

期望行为：

- 路由到 `workflow`
- 先读取文件
- 再统计行数
- 最后汇总成一个统一回答

## 验证方式

运行：

```bash
python -m unittest discover -s tests -v
python -m cli.main --input "Read README.md and then count lines." --trace
```

观察结果：

- 测试通过
- workflow 路由被触发
- trace 中能看到工作流步骤
- 工具结果被收集并汇总

## 后续迭代建议

- 版本说明继续放在 `versions/`
- 后续仍然使用 `*_v2.md`、`*_v3.md` 这种命名方式
- 下一版再增加更多工作流模式，不要过早把规划器做得太复杂

## 学习检查点

- 我能解释 AgentState 的作用：保存 Agent 运行过程中的所有中间状态，以便于我们对 Agent 的历史能够进行追溯；
- 我能解释 WorkflowPlan 的作用：形成agent的工作流，使得我们能够对需求做流程化处理，实现多步骤任务拆解；
- 我能解释 workflow 和单步工具调用的区别：单步骤工具调用适合简单场景任务只有一个功能，而多步骤可以进行复杂任务拆解，细化任务流程；
- 我能解释当前 workflow 的限制：当前workflow没有上下文概念，拆解开之后还是单步骤的简单组合；
