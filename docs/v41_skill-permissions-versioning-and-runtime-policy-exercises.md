# Skill Permissions, Versioning and Runtime Policy v41 练习

对应版本：v41  
主题：Skill Permissions, Versioning and Runtime Policy  
用途：理解为什么 Skills 需要版本和运行时策略

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v41` 不能只做一个 `--allow-skill` 命令行参数？
2. `SkillSpec.version` 进入数据模型后，工程价值是什么？
3. `SkillRuntimePolicy` 和 `SkillPolicyDecision` 分别负责什么？
4. 为什么 blocked skill run 仍然是有价值的输出？
5. 为什么这一步是“治理”而不是“权限修补”？

## 练习 2：读 skills 链路

阅读：

- `skills/policy.py`
- `skills/catalog.py`
- `skills/execution.py`
- `agent/tools.py`
- `cli/collaboration_demo.py`
- `cli/main.py`

请回答：

1. `evaluate_skill_runtime_policy()` 会检查哪些条件？
2. `execute_skill()` 在什么时候会返回 `blocked`？
3. `SkillRun.to_dict()` 为什么要包含 `policy` 和 `policy_decision`？
4. `describe_skills()` 为什么要显示 policy 信息？
5. `cli.main` 和 `cli.collaboration_demo` 为什么都需要 skill policy 参数？

## 练习 3：动手验证

运行：

```bash
python -m cli.collaboration_demo --list-skills --skill-policy project-only
python -m cli.collaboration_demo --task "Execute skill professional-code-review." --execute-skill --skill professional-code-review --skill-policy builtin-only
python -m cli.main --input "Execute skill professional-code-review." --skill-policy project-only
```

请记录：

1. `professional-code-review` 是否还可见？
2. project skill 被 builtin-only 策略阻止时，输出是否包含 `Blocked skill`？
3. 输出里是否包含 `Policy decision` 和 `Next safe action`？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么技能版本信息应该写进 `SKILL.md` frontmatter，而不是只写进代码注释？
2. 为什么 allow / deny 需要同时存在？
3. 如果后续要做集中策略服务，`v41` 最重要的基础价值是什么？

## 答案

### 练习 1：理解本阶段目标

1. `v41` 不能只做一个 `--allow-skill` 参数，因为这只是表层开关。真正的目标是让技能本身带版本、执行时带策略、输出里带决策，形成完整治理闭环。
2. `SkillSpec.version` 进入数据模型后，技能就能被版本化追踪，后续可以做最小版本要求、回归分析和升级决策，而不是只看名字。
3. `SkillRuntimePolicy` 负责定义“哪些技能可以运行”，`SkillPolicyDecision` 负责记录“某个技能在当前策略下是否允许、为什么、下一步怎么做”。
4. blocked skill run 仍然有价值，因为它证明策略生效了，也给出了可审计的拒绝原因和下一步动作。
5. 这一步是治理，不只是权限修补，因为它同时覆盖版本、白名单/黑名单、来源限制、运行结果和 trace 结构，而不是只在一个 if/else 里拦一下。

### 练习 2：读 skills 链路

1. `evaluate_skill_runtime_policy()` 会检查 deny list、allow list、builtin/project 来源限制，以及 minimum version 要求。
2. `execute_skill()` 在选中 skill 后先做策略评估；如果策略不允许，直接返回 `status = blocked` 的 `SkillRun`。
3. `SkillRun.to_dict()` 要包含 `policy` 和 `policy_decision`，是为了让测试、eval、trace 和后续 graph state 都能读取同一套决策信息。
4. `describe_skills()` 要显示 policy 信息，是为了让用户在执行前就知道当前运行时边界，而不是只在失败后才看到拒绝。
5. `cli.main` 和 `cli.collaboration_demo` 都需要 skill policy 参数，因为两个入口都可能触发技能执行，治理规则必须在所有用户入口保持一致。

### 练习 3：动手验证

1. `professional-code-review` 仍然可见，因为策略控制的是运行权限，不是发现能力。
2. project skill 被 builtin-only 策略阻止时，输出应当包含 `Blocked skill`。
3. 输出里应当包含 `Policy decision` 和 `Next safe action`，因为拒绝必须同时解释原因和下一步动作。

### 练习 4：工程取舍题

1. 技能版本信息应该写进 `SKILL.md` frontmatter，因为 skill 本质上是可交付能力单元，版本和说明应当跟内容一起演进，而不是散落在代码注释里。
2. allow / deny 需要同时存在，因为真实治理既需要明确放行，也需要明确阻断；只靠 allow list 不足以表达临时禁用或风险封锁。
3. `v41` 最重要的基础价值是把技能治理的数据模型打通了。后续要做集中策略服务时，可以直接复用 version、policy、decision 和 trace 结构。

## 验证

```bash
python -m unittest tests.test_collaboration tests.test_project tests.test_evals -v
python -m cli.collaboration_demo --task "Execute skill professional-code-review." --execute-skill --skill professional-code-review --skill-policy builtin-only
```
