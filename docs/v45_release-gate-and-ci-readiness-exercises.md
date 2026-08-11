# Release Gate and CI Readiness v45 练习

对应版本：v45  
主题：Release Gate and CI Readiness  
用途：理解为什么工业 Agent 项目需要统一发布门禁

## 练习 1：理解本阶段目标

请回答：

1. 为什么 `v45` 不能只靠 `python -m unittest discover` 作为最终验收？
2. tests 和 eval 在发布门禁中的职责差别是什么？
3. 为什么 release gate 必须输出统一 report？
4. 为什么 `release_ready` 不能只看单一检查结果？
5. 这一步为什么已经接近“可交付能力”，而不是普通开发辅助？

## 练习 2：读门禁链路

阅读：

- `evals/release_gate.py`
- `cli/release_gate.py`
- `tests/test_release_gate.py`
- `cli/README.md`
- `evals/README.md`

请回答：

1. `ReleaseCheckSpec`、`ReleaseCheckResult`、`ReleaseGateReport` 分别负责什么？
2. 默认发布门禁包含哪四项检查？
3. 为什么门禁执行要继续跑完所有检查，而不是遇到第一个失败就停止？
4. `format_release_gate_report()` 的主要作用是什么？
5. CLI 为什么还要支持 `--output`？

## 练习 3：动手验证

运行：

```bash
python -m cli.release_gate
python -m unittest tests.test_release_gate -v
```

请记录：

1. 输出里是否有 `Release gate report`？
2. `Release ready` 是否为 `yes`？
3. 门禁结果里是否同时出现 tests 和 eval 相关检查？

## 练习 4：工程取舍题

请用自己的话回答：

1. 为什么发布门禁应该同时覆盖 tests、regression eval、industrial matrix 和 failure bench？
2. 为什么门禁设计成“全部执行后再汇总”，而不是“遇错即停”？
3. 如果后续要接 GitHub Actions，`v45` 最重要的基础价值是什么？

## 答案

### 练习 1：理解本阶段目标

1. `v45` 不能只靠 `python -m unittest discover` 作为最终验收，因为 tests 只能验证代码行为，不能完整覆盖 Agent 行为与失败基准。
2. tests 负责验证实现细节，eval 负责验证 Agent 面向用户的行为。
3. release gate 必须输出统一 report，因为发布前需要一份可读、可归档、可阻断的验收结果。
4. `release_ready` 不能只看单一检查结果，因为工业交付必须同时满足多个层面的稳定性要求。
5. 这一步接近可交付能力，因为它把“验证”变成了可执行门禁，而不是人工检查。

### 练习 2：读门禁链路

1. `ReleaseCheckSpec` 描述单项检查，`ReleaseCheckResult` 描述检查结果，`ReleaseGateReport` 汇总整套门禁。
2. 默认发布门禁包含 unit tests、regression eval、industrial eval matrix、failure bench 四项检查。
3. 门禁要继续跑完所有检查，是为了给出完整失败面，而不是只暴露第一个问题。
4. `format_release_gate_report()` 的主要作用是把门禁结果渲染成可读的 CLI 报告。
5. CLI 支持 `--output` 是为了把门禁结果保存成 JSON，方便归档和 CI 读取。

### 练习 3：动手验证

1. 输出里应当有 `Release gate report`。
2. `Release ready` 应当为 `yes`。
3. 门禁结果里应当同时出现 tests 和 eval 相关检查，因为它们共同构成发布验收。

### 练习 4：工程取舍题

1. 因为这四类检查分别覆盖代码正确性、基础 Agent 行为、分层能力覆盖和已知失败路径，缺一会留下发布风险。
2. 因为遇错即停会隐藏后续问题，不利于一次性了解当前版本的完整健康状况。
3. `v45` 最重要的基础价值，是把项目从“开发时可验证”推进到“发布前可门禁”的状态。

