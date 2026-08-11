# Checkpoint Branch Resume v46 练习

对应版本：v46  
主题：Checkpoint Branch Resume  
用途：理解为什么恢复后的运行必须成为正式的分支运行

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v46` 不能继续停留在“checkpoint-guided rerun”？
2. branch parent 和 branch depth 分别解决什么问题？
3. 为什么恢复后的新运行必须写回 checkpoint？
4. 为什么 resume 报告里既要有 plan，也要有 source / resumed summary？
5. 这一步为什么是恢复能力升级，而不是普通 trace 增强？

## 练习 2：读 branch resume 链路

阅读：

- `agent/persistence.py`
- `agent/replay.py`
- `agent/core.py`
- `tests/test_persistence.py`

请回答：

1. `build_run_checkpoint()` 新增了什么关键字段？
2. `build_checkpoint_resume_plan()` 现在比旧版本多提供了哪些 branch 信息？
3. `build_checkpoint_branch_record()` 的职责是什么？
4. `ReplaySummary` 为什么要纳入 branch parent / branch depth？
5. `WorkspaceAgent._resume_from_checkpoint_record()` 现在和旧版本最大的区别是什么？

## 练习 3：动手验证

运行：

```bash
python -m unittest tests.test_persistence -v
python -m cli.main --resume-last-run
python -m cli.main --list-runs
```

请记录：

1. resume 输出里是否出现 `Branch depth`？
2. `list-runs` 输出里是否能看到 `branch_parent=` 和 `depth=`？
3. 连续 resume 后，branch depth 是否递增？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么恢复后的运行应该被看成“新分支”，而不是“覆盖原运行”？
2. 为什么 branch lineage 应该进入 replay summary，而不只出现在 trace 文本里？
3. 如果后续要做恢复树和人工审批，`v46` 最重要的基础价值是什么？

## 答案

### 练习 1：理解本阶段目标

1. `v46` 不能继续停留在 checkpoint-guided rerun，因为那种方式只能重跑，不能清楚说明新运行来自哪个历史 checkpoint。
2. branch parent 解决“来源是谁”，branch depth 解决“已经是第几层恢复分支”。
3. 恢复后的新运行必须写回 checkpoint，因为它本身也是后续 replay、diff、再恢复的正式历史记录。
4. resume 报告既要有 plan，也要有 source / resumed summary，因为恢复既是“准备怎么做”，也是“实际做完后发生了什么”。
5. 这一步是恢复能力升级，因为它改变的是恢复链路的正式数据关系，而不是仅仅多打印一点信息。

### 练习 2：读 branch resume 链路

1. `build_run_checkpoint()` 新增了 `resume` 字段，用来持久化 branch lineage。
2. `build_checkpoint_resume_plan()` 现在多提供了 branch session、branch task 和 branch depth。
3. `build_checkpoint_branch_record()` 的职责是把源 checkpoint 转成恢复后的分支 lineage 元数据。
4. `ReplaySummary` 要纳入 branch parent / branch depth，因为 replay 和 diff 需要知道运行之间的恢复关系。
5. `WorkspaceAgent._resume_from_checkpoint_record()` 和旧版本最大的区别，是现在 resume 后的新运行会被显式标记为某个历史 checkpoint 的分支。

### 练习 3：动手验证

1. resume 输出里应出现 `Branch depth`。
2. `list-runs` 输出里应能看到 `branch_parent=` 和 `depth=`。
3. 连续 resume 后，branch depth 应递增，例如从 `1` 变成 `2`。

### 练习 4：工程取舍题

1. 因为覆盖原运行会破坏审计历史，而新分支能保留“原始运行”和“恢复后的运行”两条证据链。
2. 因为 replay summary 是后续 diff、报告和自动化检查的结构化基础，不能只依赖文本 trace。
3. `v46` 最重要的基础价值，是把恢复运行正式纳入可追踪、可比较、可继续恢复的 branch lineage 体系。
