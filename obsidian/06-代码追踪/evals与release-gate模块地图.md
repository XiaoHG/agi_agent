# evals与release-gate模块地图

## 模块职责

`evals/` 负责行为评估、failure bench、matrix、release gate 和评估执行入口。

## 主要文件

- [evals/matrix.py](../../evals/matrix.py)
- [evals/runner.py](../../evals/runner.py)
- [evals/release_gate.py](../../evals/release_gate.py)
- [evals/industrial_eval_matrix.json](../../evals/industrial_eval_matrix.json)
- [evals/industrial_failure_bench.json](../../evals/industrial_failure_bench.json)

## 关键阶段版本

- `v06`
- `v44`
- `v45`

## 当前判断

交付层已经具备正式门禁意识，但后续还要进入持续交付和 audit control 阶段。

## 关联

- [[当前缺口总览]]
- [[版本总台账]]
