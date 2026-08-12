# v48：Skills Governance and Versioning

## 本阶段目标

把 Skills 从“有版本、可执行”推进为“注册表可校验、执行可审计、版本与工具声明可治理”的正式能力层。

## 本阶段在工业 Agent 中的位置

工业 Agent 的 Skills 不能只靠：

- 目录里有一个 `SKILL.md`
- 运行时临时判断允不允许
- 执行后只留普通 step trace

它还必须具备：

- 注册表条目是否合法
- 技能声明和实际执行是否一致
- 治理结果是否进入 trace
- 版本和工具声明能否形成后续审批与升级基础

`v48` 解决的是“技能层如何从可运行，升级到可治理、可审计、可演化”。

## 本阶段解决的问题

- 让 skill registry 条目在执行前先做治理校验
- 让 builtin skill 也显式声明可用工具
- 让 skill run 保留治理策略、治理校验和治理审计轨迹
- 让 `list_skills` 输出不只显示技能列表，还显示治理结果

## 本阶段新增能力

### 1. Skills registry governance

新增：

- `SkillGovernancePolicy`
- `SkillGovernanceValidation`
- `validate_skill_governance()`

默认治理规则：

- skill 必须带版本
- skill 必须带 purpose
- skill 必须带 output format
- 如果 skill 会执行 tool step，则必须显式声明对应工具

### 2. Declared tools 进入 SkillSpec

增强：

- `SkillSpec.declared_tools`

builtin skills 现在会显式声明工具，例如：

- `code_review` -> `list_dir`, `search_docs`
- `learning_explanation` -> `search_docs`, `read_file`

project skills 也可以通过 frontmatter 的 `tools:` 字段声明工具。

### 3. Governance-aware SkillRun

增强：

- `SkillRun.governance_policy`
- `SkillRun.governance_validation`
- `SkillRun.governance_audit`

治理阶段顺序：

- `registry`
- `validation`
- `policy`
- `execution`

### 4. Governance-aware skill catalog

增强：

- `describe_skills()`

现在列出技能时会同时显示：

- governance protocol
- governance validation
- governance reason
- policy decision

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `skills/catalog.py` | skill registry 增加 declared tools 与治理视图 |
| `skills/policy.py` | 增加治理策略、治理校验模型与校验逻辑 |
| `skills/execution.py` | SkillRun 增加治理元数据与治理审计轨迹 |
| `skills/__init__.py` | 导出治理模型与函数 |
| `skills/README.md` | 更新技能层当前能力说明 |
| `tests/test_collaboration.py` | 增加治理与审计测试 |
| `docs/current-learning-state.md` | 更新当前学习状态 |

## 核心实现说明

### 1. 为什么技能注册表也要做治理校验

因为 skill 不是普通文本，它是可执行能力单元。

如果 skill 没有版本、没有输出格式、没有声明工具，就无法稳定地进入：

- trace
- tests
- 审批
- 升级

### 2. 为什么 declared tools 很重要

因为 skill 的“会用什么工具”不能只藏在执行代码里。

声明出来以后，系统才能判断：

- skill 宣称的能力边界是什么
- 实际执行有没有越权
- 后续能不能做审批或风险分级

### 3. 为什么 SkillRun 要带 governance audit

因为工业 Agent 需要知道一次 skill 执行到底卡在哪一层：

- 注册表已找到
- 校验失败
- 策略阻止
- 执行失败

这样恢复、回放、测试和后续扩展都可以直接复用治理证据。

## 运行示例

查看治理后的技能目录：

```bash
python -m cli.collaboration_demo --list-skills
```

执行一个带治理审计的 skill：

```bash
python -m cli.collaboration_demo --task "Execute skill for code review." --execute-skill
```

## 验证命令

```bash
python -m unittest tests.test_collaboration -v
python -m unittest tests.test_agent tests.test_langgraph_workflow tests.test_evals -v
python -m unittest discover -s tests -q
python -m cli.collaboration_demo --list-skills
```

## 当前边界

- 这是本地 skill registry governance，不是外部集中治理服务
- declared tools 目前仍是轻量声明，不是完整权限审批模型
- project skill 目前主要做 registry 校验，还没有做真实远程 registry 同步

## 下一步建议

下一阶段建议进入 `v49`，继续做 `Production RAG Backend Hardening`，把知识底座从学习版检索推进到可替换后端架构。
