# v44：Industrial Evaluation Matrix and Failure Bench

## 本阶段目标

把项目从“有回归用例”升级到“有分层评估矩阵和失败基准”，让 Agent 的关键能力可以按类别稳定验证、汇总和比较。

## 本阶段在工业 Agent 中的位置

工业 Agent 不能只依赖：

- 单个 regression 文件
- 零散测试
- 临时手工验证

它必须具备：

- 分层 eval 结构
- 失败基准集
- 统一结果汇总入口
- 可持续扩展的评估规格

`v44` 解决的是“Agent 如何形成可发布级的行为验证矩阵”。

## 本阶段解决的问题

- 让 eval 不再只有一份平铺的 regression case 列表
- 让 route / tool / skill / recovery / replay 拥有独立类别
- 让失败路径成为稳定的 benchmark，而不是偶发手工检查
- 让 CLI 直接支持 matrix 和 failure bench 执行

## 本阶段新增能力

### 1. 分层 eval case 模型

`EvalCase` 现在支持：

- `category`
- `operation`
- `setup_inputs`

这让 case 不再只能表达“输入 -> route/tool/answer”，还可以表达：

- replay latest checkpoint
- compare latest two checkpoints
- resume latest checkpoint

### 2. Eval matrix 规格

新增：

- `evals/industrial_eval_matrix.json`
- `evals/matrix/*.json`
- `evals/matrix.py`

当前 matrix 分为五层：

- route
- tool
- skill
- recovery
- replay

### 3. Failure bench

新增：

- `evals/industrial_failure_bench.json`
- `evals/failure-bench/v44_failure_bench_cases.json`

这让已知失败路径能被固定回归验证。

### 4. CLI 汇总入口

`cli.eval_runner` 现在支持：

- `--matrix`
- `--failure-bench`

并输出 suite 级别的汇总报告。

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `evals/runner.py` | 升级 case 执行模型，支持 operation / category / setup |
| `evals/matrix.py` | 新增 matrix / suite 聚合执行与报告 |
| `evals/industrial_eval_matrix.json` | 工业评估矩阵规格 |
| `evals/matrix/*.json` | route / tool / skill / recovery / replay 分类用例 |
| `evals/industrial_failure_bench.json` | failure bench 规格 |
| `evals/failure-bench/*.json` | 失败基准用例 |
| `cli/eval_runner.py` | 新增 matrix / failure bench CLI |
| `tests/test_evals.py` | 增加 matrix / failure bench 测试 |
| `evals/README.md` | 更新 eval 结构说明 |
| `docs/current-learning-state.md` | 更新当前学习状态 |

## 核心实现说明

### 1. 为什么 eval matrix 要按层拆开

因为 route、tool、skill、recovery、replay 代表的是不同工程层面的行为。

如果全部混在一个列表里：

- 不利于定位回归来源
- 不利于扩展新类别
- 不利于发布前做分层检查

### 2. 为什么 failure bench 需要独立存在

因为失败路径不是“异常情况可以忽略”，而是工业 Agent 必须稳定处理的正式能力。

failure bench 的价值是把：

- 拒绝路径
- 恢复路径
- 缺失资源路径
- 回放/恢复失败链路

都变成固定基准。

### 3. 为什么 operation 要进入 case 模型

因为 replay / compare / resume 这些能力不是普通 `agent.run(input)`。

如果 operation 不进入数据模型，评估系统就无法统一覆盖这些入口。

## 运行示例

运行传统 regression：

```bash
python -m cli.eval_runner
```

运行工业 eval matrix：

```bash
python -m cli.eval_runner --matrix evals/industrial_eval_matrix.json
```

运行 failure bench：

```bash
python -m cli.eval_runner --failure-bench evals/industrial_failure_bench.json
```

## 验证命令

```bash
python -m unittest tests.test_evals -v
python -m unittest discover -s tests -v
python -m cli.eval_runner --matrix evals/industrial_eval_matrix.json
python -m cli.eval_runner --failure-bench evals/industrial_failure_bench.json
```

## 当前边界

- 这是本地 deterministic 工业评估矩阵，不是完整线上评测平台
- failure bench 先覆盖固定失败路径，不做统计型 flaky 分析
- 还没有引入人工评分、faithfulness judge 或外部 benchmark service

## 下一步建议

下一阶段建议进入更高一级的工业化交付主题，例如：

- 更强的发布审计流程
- CI / release readiness 集成
- 更细粒度的线上/离线评测分层
