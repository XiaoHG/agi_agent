# v06 练习：工程化、评估与可观测性

对应版本：v06  
主题：Engineering Evals & Observability  
用途：理解 trace、eval、回归和错误分类

## 练习

1. 为什么 Agent 项目不能只靠手工看输出？
2. `build_runtime_events()` 为什么重要？
3. `evals/` 和 `tests/` 的职责差异是什么？
4. 为什么要把失败案例写进可复现评估？

## 答案

1. 因为没有结构化回归就很难判断变化是变好还是变坏。
2. 它把步骤和错误转成可追踪事件，便于调试和恢复。
3. tests 验证代码行为，eval 验证 Agent 行为。
4. 这样后续每次改动都能比较同一批场景是否退化。

## 验证

```bash
python -m unittest tests.test_evals tests.test_events -v
python -m cli.eval_runner
```
