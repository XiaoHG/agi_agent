# skills/

放可复用技能模块。

一个 Skill 不只是 prompt，通常应包含：

- 适用场景
- 输入要求
- 执行步骤
- 可调用工具
- 输出格式
- 成功/失败样例

建议每个 skill 一个目录：

```text
skills/
  research-brief/
  code-review/
  doc-summarizer/
```

## 当前实现

当前阶段已经实现内置 skill catalog、project skill registry、runtime policy 和 registry governance。

```text
skills/
  catalog.py     # SkillSpec, built-in/project registry, governance-aware listing
  policy.py      # runtime policy + governance validation
  execution.py   # structured SkillRun + governance audit
```

当前内置 skills：

- `research_brief`
- `code_review`
- `learning_explanation`

当前治理能力：

- skill version
- declared tools
- runtime policy
- registry governance validation
- governance audit trail

运行：

```bash
python -m cli.collaboration_demo --list-skills
python -m cli.collaboration_demo --task "Review this code and add tests."
python -m cli.main --input "List available skills." --trace
```
