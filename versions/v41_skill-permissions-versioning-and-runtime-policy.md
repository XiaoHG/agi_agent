# v41：Skill Permissions, Versioning and Runtime Policy

## 本阶段目标

把 Skills 从“可发现、可运行”升级为“可治理、可约束、可演化”，让技能不仅能被调用，还能被版本化、被策略控制、被运行时审计。

## 本阶段在工业 Agent 中的位置

工业 Agent 的 Skills 不能只是一个目录里的脚本集合。

它们需要具备：

- 可识别的版本
- 可配置的运行时策略
- 可解释的允许 / 拒绝决策
- 可进入 trace 和测试的结构化政策信息

`v41` 解决的是“技能层如何从能力集合变成可治理能力单元”。

## 本阶段解决的问题

- 让 SkillSpec 具备显式版本信息
- 让技能执行可以受 runtime policy 控制
- 让 project skills 可以被单独允许、单独拒绝
- 让技能执行结果包含 policy decision 和 next safe action
- 让 CLI / Agent / tests 使用同一套策略

## 本阶段新增能力

### 1. Skill versioning

`SkillSpec` 新增 `version` 字段，并从 project skill frontmatter 中解析。

这样技能不再只是“名字 + 步骤”，而是可追踪版本的能力单元。

### 2. SkillRuntimePolicy

新增 `SkillRuntimePolicy`，用于控制：

- builtin skills 是否允许
- project skills 是否允许
- allowed / denied skill lists
- minimum version requirement

### 3. SkillPolicyDecision

新增 `SkillPolicyDecision`，用于输出：

- policy name
- skill name
- skill version
- allowed / blocked
- reason
- next safe action

### 4. Policy-aware execution

`execute_skill()` 现在先做策略评估，再决定是否执行。

被策略阻止的 skill run 会返回：

- `status = blocked`
- `final_output` 中包含 reason 和 next safe action
- `policy_decision` 进入 trace

### 5. CLI policy controls

`cli.main` 与 `cli.collaboration_demo` 都可以通过 runtime policy 运行技能。

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `skills/policy.py` | 技能运行时策略与决策模型 |
| `skills/catalog.py` | skill versioning、policy-aware catalog |
| `skills/execution.py` | policy-aware skill run |
| `skills/__init__.py` | 导出 policy 类型 |
| `agent/core.py` | WorkspaceAgent 接入 skill policy |
| `agent/tools.py` | skill list / plan / execute 接入 policy |
| `cli/main.py` | 主 CLI 接入 skill policy |
| `cli/collaboration_demo.py` | 技能 demo 接入 skill policy |
| `.codex/skills/*/SKILL.md` | project skills 增加 version frontmatter |
| `tests/test_collaboration.py` | 增加 policy / version 测试 |
| `docs/current-learning-state.md` | 更新学习状态 |

## 核心实现说明

### 1. 为什么版本信息必须进入 SkillSpec

因为没有版本，技能只能算“当前内容”，不能算“可演化能力”。

version 进入 `SkillSpec` 之后，后续才可以做：

- minimum version policy
- version comparison
- trace / eval 中的技能回归判断

### 2. 为什么 runtime policy 要先于执行

因为工业 Agent 不应该默认把所有能力都暴露给任何任务。

先评估 policy，再执行 skill，可以把：

- 允许
- 拒绝
- 升级要求
- 人工介入

变成明确的运行时决策。

### 3. 为什么 blocked 也是有效结果

因为技能治理的目标不是“永远执行成功”，而是“知道为什么不能执行，以及下一步怎么做”。

`blocked` 结果仍然有工程价值：

- 可测试
- 可审计
- 可提示
- 可扩展到审批流程

## 运行示例

查看技能和策略：

```bash
python -m cli.collaboration_demo --list-skills --skill-policy project-only
```

阻止 project skill：

```bash
python -m cli.collaboration_demo \
  --task "Execute skill professional-code-review." \
  --execute-skill \
  --skill professional-code-review \
  --skill-policy builtin-only
```

主 CLI 也可使用策略：

```bash
python -m cli.main --input "Execute skill professional-code-review." --skill-policy project-only
```

## 验证命令

```bash
python -m unittest tests.test_collaboration tests.test_project tests.test_evals -v
python -m unittest discover -s tests -v
```

## 当前边界

- 这是运行时策略层，不是完整的权限审批平台
- version 目前主要来自 skill frontmatter 与默认值
- policy 先覆盖 builtin / project / allow / deny / minimum version
- 还没有接入外部 registry 或集中策略服务

## 下一步建议

下一阶段建议进入：

`v42：Multi-Agent Task Delegation and Subagent Contract`

重点是把主 Agent 与 subagent 的协作协议结构化，继续把能力层从“可治理”推进到“可分工”。
