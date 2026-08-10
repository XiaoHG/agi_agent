# Industrial Evaluation Matrix and Failure Bench v44 练习

对应版本：v44  
主题：Industrial Evaluation Matrix and Failure Bench  
用途：理解 Agent 如何从单一回归用例升级到分层评估矩阵

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v44` 不能继续只维护 `evals/regression_cases.json`？
2. eval matrix 和 failure bench 的职责差别是什么？
3. 为什么 `operation` 必须进入 `EvalCase` 数据模型？
4. 为什么 recovery 和 replay 也应该进入工业评估矩阵？
5. 这一步为什么是“可发布工程能力”，而不是单纯测试增强？

## 练习 2：读 eval 链路

阅读：

- `evals/runner.py`
- `evals/matrix.py`
- `evals/industrial_eval_matrix.json`
- `evals/industrial_failure_bench.json`
- `cli/eval_runner.py`

请回答：

1. `EvalCase` 相比旧版本新增了哪些关键字段？
2. `run_eval_matrix()` 为什么要为每个 suite 创建独立的 history/memory 目录？
3. 当前 industrial eval matrix 分成了哪些类别？
4. failure bench 当前覆盖了哪些典型失败场景？
5. `format_eval_matrix_report()` 的主要作用是什么？

## 练习 3：动手验证

运行：

```bash
python -m cli.eval_runner --matrix evals/industrial_eval_matrix.json
python -m cli.eval_runner --failure-bench evals/industrial_failure_bench.json
```

请记录：

1. 输出里是否包含 `Industrial eval matrix report`？
2. suite breakdown 里是否出现 `route`、`tool`、`skill`、`recovery`、`replay`？
3. failure bench 输出里是否能看到失败路径仍然被判定为通过 benchmark？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么要把 replay / resume 评估成独立 operation，而不是把它们混进普通 route 用例？
2. 为什么 failure bench 不等于“这些 case 必须失败”？
3. 如果后续要接 CI 和 release gate，`v44` 最重要的基础价值是什么？

## 答案

### 练习 1：理解本阶段目标

1. `v44` 不能只维护 `evals/regression_cases.json`，因为平铺列表无法表达工业级分层验证结构，也不利于按能力层定位回归。
2. eval matrix 负责分层覆盖关键能力，failure bench 负责固定覆盖已知失败与恢复路径。
3. `operation` 必须进入 `EvalCase`，因为 replay / compare / resume 不是普通 `agent.run(input)`，必须被统一建模。
4. recovery 和 replay 应进入工业评估矩阵，因为它们已经是 Agent 的正式能力，不只是调试附属功能。
5. 这一步是可发布工程能力，因为它定义了按层验收 Agent 行为的标准入口和结果汇总结构。

### 练习 2：读 eval 链路

1. `EvalCase` 新增了 `category`、`operation`、`setup_inputs`。
2. `run_eval_matrix()` 为每个 suite 创建独立 history/memory 目录，是为了避免不同 suite 之间互相污染 checkpoint 和记忆状态。
3. 当前 industrial eval matrix 分成 `route`、`tool`、`skill`、`recovery`、`replay` 五类。
4. failure bench 当前覆盖了 missing file、workflow failure、MCP write denial、LangGraph tool recovery、failed-run replay、failed-run resume。
5. `format_eval_matrix_report()` 的主要作用是把 suite 级统计结果渲染成适合 CLI 阅读的汇总报告。

### 练习 3：动手验证

1. 输出里应当包含 `Industrial eval matrix report`。
2. suite breakdown 里应当出现 `route`、`tool`、`skill`、`recovery`、`replay`。
3. failure bench 输出里应能看到失败路径仍然被 benchmark 判定通过，因为这里验证的是失败处理是否稳定，而不是是否成功完成任务。

### 练习 4：工程取舍题

1. replay / resume 要评估成独立 operation，因为它们依赖 checkpoint 历史和专门入口，不属于普通 route 执行。
2. failure bench 不等于“这些 case 必须失败”，而是“这些已知失败场景必须稳定输出正确的拒绝/恢复结果”。
3. `v44` 最重要的基础价值是把工业级行为验证分层、汇总和失败基准都规范化了，后续才能直接接到 CI 和 release gate。

## 验证

```bash
python -m unittest tests.test_evals -v
python -m cli.eval_runner --matrix evals/industrial_eval_matrix.json
python -m cli.eval_runner --failure-bench evals/industrial_failure_bench.json
```
