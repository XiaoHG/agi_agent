# v30：Project Skill Registry

## 本阶段目标

把当前写死在 Python catalog 中的 Skills，升级为“built-in skills + project skills” 的合并注册表，让项目内 `.codex/skills/*/SKILL.md` 能成为 Agent 可发现能力。

本阶段重点不是引入外部 marketplace，而是先打通项目内技能闭环：

```text
.codex/skills/*/SKILL.md
-> frontmatter / step parsing
-> project SkillSpec
-> merged skill catalog
-> Agent / CLI / tests / eval
```

## 本阶段新增文件

| 文件 | 作用 |
|---|---|
| `versions/project-skill-registry_v30.md` | 本阶段版本说明 |
| `docs/project-skill-registry-exercises_v30.md` | 本阶段练习 |

## 本阶段修改文件

| 文件 | 主要变化 |
|---|---|
| `skills/catalog.py` | 新增 project skill discovery、`SKILL.md` 解析、merged catalog、显式 skill 选择 |
| `skills/execution.py` | `execute_skill()` 支持 `root` / `skill_name`，`SkillRun.to_dict()` 输出 skill source/path |
| `skills/__init__.py` | 导出 project registry 相关函数 |
| `agent/tools.py` | `list_skills` / `plan_skill` / `execute_skill` 接入项目 skill registry |
| `agent/core.py` | `WorkspaceAgent._call_tool()` 传入 workspace root 选择和规划技能 |
| `cli/collaboration_demo.py` | `--list-skills` 显示 project skills，新增 `--skill` 显式执行指定技能 |
| `integrations/langchain_tools.py` | LangChain adapter 接回 merged skill catalog |
| `tests/test_collaboration.py` | 增加 project skill discovery、merged catalog、显式执行和 CLI 测试 |
| `evals/regression_cases.json` | 增加 project skill execution 回归，并强化 skills list 断言 |
| `docs/current-learning-state.md` | 更新当前阶段和下一步建议 |

## 核心实现说明

### 1. Project skill discovery

`skills/catalog.py` 新增：

- `discover_project_skills(root)`
- `get_available_skills(root)`

行为：

- 从 `.codex/skills/*/SKILL.md` 扫描项目技能
- 解析 frontmatter 中的 `name` / `description`
- 解析 markdown 编号步骤，生成 `SkillSpec.steps`
- 解析 `## Output format`，作为 `SkillSpec.output_format`

### 2. SkillSpec 扩展

`SkillSpec` 新增：

- `source`
- `path`
- `aliases`

意义：

- `source` 区分 built-in / project
- `path` 让 trace 和 CLI 能定位技能文件
- `aliases` 允许 `professional-code-review` / `professional_code_review` / `professional code review` 这类名字互相匹配

### 3. 显式技能选择

`select_skill()` 现在支持：

- `skill_name="professional-code-review"`
- 从 task 中提取 `skill=<name>`
- 从自然语言中提取 `Execute skill professional-code-review.`

这样项目技能不需要先写进硬编码 router，就能被显式调用。

### 4. Agent / CLI 接入

项目技能现在已经进入以下入口：

- `list_skills`
- `plan_skill`
- `execute_skill`
- `python -m cli.collaboration_demo --list-skills`
- `python -m cli.collaboration_demo --execute-skill --skill professional-code-review`

### 5. Structured trace

`SkillRun.to_dict()` 现在会导出：

- `skill.source`
- `skill.path`

这让测试、eval 和后续 graph / checkpoint 分析可以区分 built-in skill 和 project skill。

## 当前可见行为

### 列出技能

```bash
python -m cli.collaboration_demo --list-skills
```

输出中现在会同时看到：

- `code_review`
- `learning_explanation`
- `research_brief`
- `professional-code-review`

### 执行项目技能

```bash
python -m cli.collaboration_demo \
  --task "Review current changes." \
  --execute-skill \
  --skill professional-code-review
```

### Agent 执行项目技能

```bash
python -m cli.main --input "Execute skill professional-code-review."
```

## 设计取舍

### 为什么先做最小 markdown parser

因为这个阶段的目标是：

- 先证明项目技能能被发现
- 先证明它能进入 Agent 能力面
- 先证明它能进入测试和 eval

而不是一开始就做完整 YAML schema、复杂 frontmatter 校验和 marketplace 协议。

### 为什么 project skill 先保持 deterministic execution

因为当前 `professional-code-review` 的核心价值是：

- 可发现
- 可选择
- 可追踪

还不是“自动执行 git diff / test plan / review findings”。

真正的工具权限和自动化执行，应放到下一阶段的 MCP / tool permission policy 中解决。

## 验证命令

已验证：

```bash
python -m unittest tests.test_collaboration tests.test_agent tests.test_tool_calling tests.test_langchain_tools -v
python -m cli.collaboration_demo --list-skills
python -m cli.collaboration_demo --task "Review current changes." --execute-skill --skill professional-code-review
python -m cli.eval_runner
python -m unittest discover -s tests -q
```

## 当前限制

- `SKILL.md` parser 目前只支持简单 frontmatter key-value。
- project skill steps 当前仍是 deterministic record steps，没有自动读取 skill 文本中的工具动作。
- built-in skills 和 project skills 还没有权限模型。
- 还没有针对 project skills 的独立版本管理和权限声明。

## 下一步建议

下一阶段建议进入：

- MCP 工具注册与权限策略

原因：

- 项目 skill 已经能被发现，但它还不能安全地自动执行更强工具能力。
- 要继续推进 professional code review 这类 skill，下一步必须先补工具权限边界和拒绝/恢复路径。
