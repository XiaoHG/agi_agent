# ch07 证据笔记

## 章节定位

- 章节：第 7 章 能力分层：Skills、Subagent 与角色协作
- 版本主锚点：`v05`
- 补充支撑：`v06`、`v07`

## 主要证据来源

### 版本文档

- `versions/v05_skills-subagent-collaboration.md`
- `versions/v06_engineering-evals-observability.md`
- `versions/v07_project-learning-assistant.md`

### 代码入口

- `skills/catalog.py`
- `skills/policy.py`
- `skills/execution.py`
- `skills/README.md`
- `subagent/team.py`
- `subagent/README.md`
- `tests/test_collaboration.py`
- `agent/project.py`

## 本章核心论点与证据对应

1. 工具边界建立后，系统仍需向上建立能力模板层。
   - 证据：`SkillSpec` 同时定义 purpose、steps、output_format、version、declared_tools。
   - 证据：`get_available_skills()` 合并 builtin 与 project skills，说明 skill 已是正式 registry 条目。

2. Skill 在本项目里不是 prompt 别名，而是可治理能力。
   - 证据：`skills/policy.py` 中 `SkillRuntimePolicy`、`SkillGovernancePolicy`、`SkillGovernanceValidation`。
   - 证据：`skills/execution.py` 中 `execute_skill()` 先做 governance validation 和 policy decision，再进入 step execution。
   - 证据：`SkillRun` 保存 policy、governance、audit、steps、final_output。

3. 多角色协作首先被定义成边界和契约，而不是自由多 Agent 对话。
   - 证据：`subagent/team.py` 中 `SubagentSpec`、`SubagentTaskContract`、`SubagentDelegationRecord`。
   - 证据：同文件中的 `SubagentRuntimeSession`、message envelope、state transition 说明协作被建模为结构对象。
   - 证据：`subagent/README.md` 明确当前阶段是 deterministic collaboration planner + runtime session foundation。

4. `v07` 使能力分层第一次进入项目级应用编排。
   - 证据：`agent/project.py` 中 `ProjectLearningAssistant.run()` 串联 README 读取、RAG、MCP、skill 选择、subagent 规划和 regression eval。
   - 证据：`versions/v07_project-learning-assistant.md` 明确区分基础 Agent 与项目级应用编排职责。

5. 当前阶段仍然不是完全自主多智能体运行时。
   - 证据：`versions/v05_skills-subagent-collaboration.md` 中“当前限制”明确说明 subagent 仍是规划层，没有真实消息传递和多 Agent 执行。
   - 证据：`subagent/team.py` 文档字符串明确说明该模块是 runtime design notebook in code form。

## 写作注意

- 正文不写“待创建”“后续再补”等占位语。
- 要清楚区分 tool、skill、subagent、project orchestration 四层。
- 不提前展开后续真正 multi-agent runtime 章节，只保留桥接说明。
