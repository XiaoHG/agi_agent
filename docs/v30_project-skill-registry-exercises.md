# v30 练习：Project Skill Registry

## 练习目标

理解项目技能为什么不能继续只写死在 `skills/catalog.py`，以及本阶段是如何把 `.codex/skills/professional-code-review/SKILL.md` 接入 Agent 能力面的。

## 一、理解题

1. 为什么 v30 要先做项目内 Skill Registry，而不是直接升级 MCP 权限系统？
   答：因为当前最直接的结构缺口不是权限分类不够细，而是项目技能已经存在，但 Agent 还发现不了它们。仓库里已经有 `.codex/skills/professional-code-review/SKILL.md`，但 v29 之前 `skills/catalog.py` 只有硬编码 built-in skills，`list_skills` 和 `execute_skill` 都还不能把 project skill 当成一等能力。所以 v30 先补“发现和注册”，下一阶段再补“权限和执行边界”才合理。
2. `SkillSpec.source` 和 `SkillSpec.path` 为什么要进入结构化 trace，而不只是显示在 CLI 文本里？
   答：因为 CLI 文本只适合人看，不适合测试、eval、checkpoint 和 graph state 做程序化判断。进入结构化 trace 之后，系统可以明确知道当前执行的是 `builtin` 还是 `project` skill，也能直接定位对应的 `SKILL.md` 路径。
3. 为什么当前 project skill parser 先只支持简单 frontmatter 和编号步骤？
   答：因为 v30 的目标是先打通最小闭环：`SKILL.md -> 解析 -> 注册 -> Agent 可发现 -> tests/eval`。如果一开始就做复杂 schema、权限字段和工具动作声明，会让阶段目标发散，测试复杂度也会明显上升。
4. `professional-code-review` 为什么现在可以被发现，但还没有自动执行 `git diff`？
   答：因为 v30 解决的是 registry，不是 automation。它现在已经能被扫描、选择、执行并进入 trace，但真实执行 `git diff`、测试命令或更强工具动作会立刻碰到权限、审批和失败恢复边界，这些更适合放到下一阶段的 MCP / tool permission policy 中统一处理。
5. `select_skill()` 和 `execute_skill()` 在 v30 中分别承担什么职责？
   答：`select_skill()` 负责选择技能，核心是合并 built-in 和 project skills，并根据 task 或显式 skill 名称返回 `SkillSpec`。`execute_skill()` 负责执行技能，核心是构建步骤、执行步骤并生成 `SkillRun`。可以概括为：`select_skill = 规划`，`execute_skill = 执行`。

## 二、源码定位题

1. 在哪个文件里扫描 `.codex/skills/*/SKILL.md`？
   答：在 `skills/catalog.py`，对应函数是 `discover_project_skills(root)`。
2. 哪个函数负责把 built-in skills 和 project skills 合并？
   答：`get_available_skills(root)`。
3. 哪个函数负责从 task 中抽取显式 skill 名称？
   答：有两层。`skills/catalog.py` 里的 `_extract_explicit_skill_name(user_input)` 负责从自然语言里提取；`agent/tools.py` 里的 `_extract_skill_name(task)` 负责从工具层 task 中提取 `skill=<name>` 这种显式提示。
4. `SkillRun.to_dict()` 在哪里把 `skill.source` 和 `skill.path` 导出？
   答：在 `skills/execution.py` 的 `SkillRun.to_dict()` 中。
5. `cli.collaboration_demo` 是如何支持 `--skill professional-code-review` 的？
   答：在 `cli/collaboration_demo.py` 里新增了 `--skill` 参数。非 tool-backed 路径会把 `skill_name=args.skill` 传给 `execute_skill()`；tool-backed 路径会先通过 `_inject_skill_hint()` 把 skill 名称注入 task，再交给 Agent 的工具执行链路。

## 三、动手验证

运行：

```bash
python -m cli.collaboration_demo --list-skills
```

回答：

1. 输出里是否出现 `professional-code-review`？
   答：出现了。
2. 输出里是否出现 `Source: project`？
   答：出现了。
3. 输出里是否包含 project skill 对应的 `Path:`？
   答：包含，当前输出里会显示 `.codex/skills/professional-code-review/SKILL.md`。

再运行：

```bash
python -m cli.collaboration_demo \
  --task "Review current changes." \
  --execute-skill \
  --skill professional-code-review
```

回答：

1. `Skill run` 名称是什么？
   答：`professional-code-review`。
2. 当前 step 是真实工具调用，还是 deterministic record？
   答：当前仍是 deterministic record，不是真实工具调用。
3. `Final output` 里暴露了什么 output format 提示？
   答：暴露了 review skill 的结构化输出格式提示，核心部分是 `Findings`、`Verification`、`Residual risks`。

## 四、测试题

运行：

```bash
python -m unittest tests.test_collaboration -v
```

回答：

1. 哪个测试验证 project skill discovery？
   答：`test_discover_project_skills`。
2. 哪个测试验证 merged catalog？
   答：`test_get_available_skills_merges_builtin_and_project`。
3. 哪个测试验证 Agent 可以执行 project skill？
   答：`test_agent_executes_project_skill`。
4. 哪个测试验证 CLI 可以显式执行 project skill？
   答：`test_collaboration_demo_executes_project_skill`。

## 五、思考题

1. 如果未来 `.codex/skills` 下出现多个 project skills，当前按名称去重是否足够？
   答：短期够用，长期不够。当前按名称去重适合 v30 的最小阶段，但未来如果出现同名不同版本、built-in 与 project skill 同名、别名冲突等情况，就需要更稳定的唯一标识，比如 `skill_id`、`namespace`、`version`。
2. 如果 `SKILL.md` frontmatter 增加 `permissions` 字段，应该接到哪里最合适？
   答：最合适的路径是先在 `skills/catalog.py` 解析到 `SkillSpec` 或 metadata，再让后续的工具执行层或 MCP permission policy 去消费。不要把权限逻辑只放在 CLI 层。
3. project skill 的步骤里如果要声明工具动作，应该放进 markdown 结构、frontmatter，还是单独 schema 文件？
   答：学习阶段可以先放在 markdown 结构里，但如果要进入专业执行系统，更合理的是逐步演进到结构化 schema，因为工具动作通常需要明确声明 action type、tool name、input schema、permissions 和 failure policy。
4. 下一阶段为什么适合进入 MCP 工具注册与权限策略，而不是先把 project skill 直接接成自动化 review agent？
   答：因为现在 skill registry 已经打通，但 project skill 还不能安全地执行更强动作。要继续增强执行力，先补工具注册、权限判断、拒绝路径和恢复路径，比直接做自动化 review agent 更稳。

## 六、验收标准

完成本练习后，你应该能说明：

- v30 解决的是“项目技能发现和注册”问题，而不是“技能自动执行”问题。
- built-in skill 和 project skill 的差别已经进入结构化数据层，而不只是文本显示。
- 下一阶段要做权限模型，是因为 skill registry 已经打通，继续增强执行力前必须先补安全边界。

补充验证结果：

- `python -m cli.collaboration_demo --list-skills` 已能看到 `professional-code-review`、`Source: project` 和 skill 路径。
- `python -m cli.collaboration_demo --task "Review current changes." --execute-skill --skill professional-code-review` 已能显式执行 project skill。
- `python -m unittest discover -s tests -q` 结果为 `147` 个测试通过。
- `python -m cli.eval_runner` 结果为 `20/20` 通过。
