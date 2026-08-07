# v05 练习：Skills 与 Subagent 协作

对应版本：v05  
主题：Skills / Subagent  
用途：理解可复用能力与角色协作的边界

## 练习

1. Skills 和 Subagent 的差别是什么？
2. 为什么 `plan_skill()` 还不等于真正的执行？
3. `professional-code-review` 为什么适合作为项目内技能入口？
4. `tests/test_collaboration.py` 为什么重要？

## 答案

1. Skills 是能力模块，Subagent 是角色协作模块。
2. 它只给出计划和描述，没有执行状态与真实输出。
3. 因为它是可复用的项目级技能，适合演示技能注册与选择。
4. 它验证 skill 选择、协作规划和输出边界。

## 验证

```bash
python -m unittest tests.test_collaboration -v
python -m cli.collaboration_demo --list-skills
```
