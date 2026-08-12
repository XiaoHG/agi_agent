# Skills Governance and Versioning v48 练习

对应版本：v48  
主题：Skills Governance and Versioning  
用途：理解为什么技能注册表也必须被治理，而不只是运行时临时放行

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v48` 不能只停留在 `SkillRuntimePolicy`？
2. `declared_tools` 进入 `SkillSpec` 后解决了什么问题？
3. 为什么 skill registry 也要做 validation？
4. 为什么 `SkillRun` 需要增加 `governance_audit`？
5. 这一步为什么是“能力层治理升级”，而不是简单补字段？

## 练习 2：读 skills 治理链路

阅读：

- `skills/catalog.py`
- `skills/policy.py`
- `skills/execution.py`
- `tests/test_collaboration.py`

请回答：

1. `SkillGovernancePolicy` 默认约束了哪些规则？
2. `validate_skill_governance()` 会检查哪些问题？
3. 为什么 builtin skill 也要声明 `declared_tools`？
4. `execute_skill()` 的治理顺序为什么是 `registry -> validation -> policy -> execution`？
5. `describe_skills()` 现在比旧版本多显示了哪些治理信息？

## 练习 3：动手验证

运行：

```bash
python -m unittest tests.test_collaboration -v
python -m cli.collaboration_demo --list-skills
python -m cli.collaboration_demo --task "Execute skill for code review." --execute-skill
```

请记录：

1. `list-skills` 输出里是否出现 `Governance protocol: v2`？
2. `code_review` 的 `declared_tools` 是否可见？
3. 执行 skill 时输出里是否出现 `Governance validation`？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么 skill 的工具声明不能只藏在 `build_skill_steps()` 里？
2. 为什么治理校验应该早于 runtime policy？
3. 如果后续要接集中式 skill registry，`v48` 最重要的基础价值是什么？

## 答案

### 练习 1：理解本阶段目标

1. 因为 `SkillRuntimePolicy` 只解决“允不允许执行”，不能判断 skill registry 条目本身是否完整、是否声明了实际会使用的工具。
2. `declared_tools` 解决的是技能声明边界和实际执行边界之间的一致性问题。
3. 因为 skill 是可执行能力单元，不是普通文本；没有治理校验就无法稳定进入 trace、审批和升级流程。
4. 因为一次 skill 执行如果没有治理审计，系统只能看到结果，看不到问题发生在注册表、校验、策略还是执行阶段。
5. 因为 `v48` 改的是技能层正式边界、注册表数据质量和审计结构，而不是只补一个展示字段。

### 练习 2：读 skills 治理链路

1. `SkillGovernancePolicy` 默认要求 skill 带版本、带 purpose、带 output format，并且 tool step 必须有对应的 `declared_tools`。
2. `validate_skill_governance()` 会检查缺失字段和未声明却会执行的工具。
3. 因为 builtin skill 同样是正式能力单元，也必须接受和 project skill 一致的治理要求。
4. 因为先知道“条目是否合法”，再判断“当前策略允不允许”，最后才值得执行，这是更稳定的治理顺序。
5. `describe_skills()` 现在会多显示 governance protocol、governance validation 和 governance reason。

### 练习 3：动手验证

1. 是，`list-skills` 输出里应出现 `Governance protocol: v2`。
2. 是，`code_review` 应显示 `Declared tools: list_dir, search_docs`。
3. 是，执行 skill 时输出里应出现 `Governance validation`。

### 练习 4：工程取舍题

1. 因为只藏在 `build_skill_steps()` 里，外部无法在执行前审计 skill 的能力边界。
2. 因为 skill 条目本身不合法时，不应该继续进入策略放行流程。
3. `v48` 最重要的基础价值，是把 skill registry、治理规则和 skill run 审计结构打通了，后续可以继续接集中治理和审批系统。
