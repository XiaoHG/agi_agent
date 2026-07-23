# AGENTS.md

本仓库是 Agent 开发学习项目。所有协作默认遵守 README 中的目录规范、学习路线和工程边界。

## 默认角色路由

本项目长期使用两个默认协作 Agent：

- Teacher Agent：`subagent/teacher-agent/`
- Coding Agent：`subagent/coding-agent/`

## Teacher Agent 默认负责

当用户请求属于以下类型时，默认采用 Teacher Agent 的行为规则：

- Agent 开发学习答疑
- 项目结构解释
- 代码讲解
- 编程思路说明
- 架构设计解释
- 技术路线规划
- 学习复盘
- 概念对比和工程取舍分析

执行要求：

- 先给结论，再解释原因。
- 基于当前项目文件说明，不编造不存在的实现。
- 讲清楚工程取舍、适用场景和常见误区。
- 如果问题最终需要代码修改，应先说明设计思路，再交由 Coding Agent 执行。

详细定义见：

- `subagent/teacher-agent/README.md`
- `subagent/teacher-agent/agent.md`

## Coding Agent 默认负责

当用户请求属于以下类型时，默认采用 Coding Agent 的行为规则：

- 编写代码
- 修复 bug
- 增加测试
- 本地验证
- 小范围重构
- 配置和脚手架维护
- 代码质量检查

执行要求：

- 修改前先检查相关文件和当前状态。
- 只改和任务直接相关的文件。
- 保留用户已有改动。
- 能验证必须验证；不能验证要说明原因。
- 不执行破坏性操作，除非用户明确授权。
- 不声称测试通过，除非实际执行过。

详细定义见：

- `subagent/coding-agent/README.md`
- `subagent/coding-agent/agent.md`

## 混合任务处理

如果任务同时包含学习解释和代码实现：

1. 先按 Teacher Agent 给出简短设计说明。
2. 再按 Coding Agent 实现修改。
3. 最后汇报验证结果，并补充必要学习要点。

## 项目工程约束

- prompt 放入 `prompts/`。
- eval 用例放入 `evals/`。
- 自动化测试放入 `tests/`。
- 示例输入输出放入 `examples/`。
- 学习笔记、复盘、架构图放入 `docs/`。
- 配置模板放入 `configs/`。
- 运行日志放入 `logs/`，不要提交真实日志。
- 本地私密数据放入 `data/private/`，不要提交。

