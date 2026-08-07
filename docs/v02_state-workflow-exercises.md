# v02 练习：状态与工作流

对应版本：v02  
主题：State & Workflow  
用途：理解多步任务执行、状态累积与失败中断

## 练习

1. `AgentState` 比单次函数返回值多了什么能力？
2. `build_workflow_plan()` 为什么是这一阶段的关键？
3. `_run_workflow()` 为什么要把每一步写入 `steps`？
4. 为什么 `workflow` 失败后应该尽早停止？

## 答案

1. 它能保存步骤、工具结果、错误和最终答案，支持多步任务。
2. 它把用户意图拆成可执行步骤，是工作流编排的核心。
3. 因为 trace 和调试需要知道每一步到底做了什么。
4. 尽早停止可以避免错误继续传播，也能让失败原因更清晰。

## 验证

```bash
python -m unittest tests.test_agent -v
python -m cli.main --input "Read README.md and then count lines." --trace
```
