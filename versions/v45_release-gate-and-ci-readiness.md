# v45：Release Gate and CI Readiness

## 本阶段目标

把项目从“有测试和 eval”升级为“有可执行的发布门禁”，让每次提交都能被统一验收。

## 本阶段在工业 Agent 中的位置

工业 Agent 项目做到这里，不能只依赖开发者手动记得跑测试。

它必须具备：

- 一键验证入口
- 统一发布门禁
- 可重复的验收顺序
- 失败时的明确阻断信号

`v45` 解决的是“项目如何从学习型迭代进入可交付前的稳定验收”。

## 本阶段解决的问题

- 让 unit tests、regression eval、industrial matrix、failure bench 形成统一门禁
- 让发布前验证不再依赖人工记忆
- 让失败结果可读、可追踪、可作为 CI 阻断依据
- 让 release readiness 成为一个可执行命令，而不是口头要求

## 本阶段新增能力

### 1. Release gate 数据模型

新增：

- `ReleaseCheckSpec`
- `ReleaseCheckResult`
- `ReleaseGateReport`

### 2. 发布门禁执行器

新增：

- `evals/release_gate.py`

默认检查顺序：

- unit tests
- regression eval
- industrial eval matrix
- failure bench

### 3. CLI 门禁入口

新增：

- `cli/release_gate.py`

支持：

- 默认执行全部检查
- 可选输出 JSON 报告

### 4. 测试覆盖

新增：

- `tests/test_release_gate.py`

覆盖：

- 默认门禁 spec
- 门禁汇总逻辑
- CLI 入口

## 本阶段主要修改文件

| 文件 | 作用 |
| --- | --- |
| `evals/release_gate.py` | 发布门禁模型与执行逻辑 |
| `cli/release_gate.py` | 发布门禁 CLI |
| `tests/test_release_gate.py` | 门禁测试 |
| `README.md` | 补充 release gate 入口 |
| `cli/README.md` | 补充 release gate CLI |
| `evals/README.md` | 补充门禁与 eval 的关系 |
| `docs/current-learning-state.md` | 更新当前学习状态 |
| `docs/plans/v3_professional-agent-iteration-plan.md` | 补充 v45 规划 |

## 核心实现说明

### 1. 为什么 release gate 要独立成版本

因为“能跑”不等于“能交付”。

工业项目需要明确的发布门槛，避免把测试、评估和 smoke check 留给人工记忆。

### 2. 为什么门禁要同时包含 tests 和 eval

tests 验证代码行为，eval 验证 Agent 行为。

两者缺一不可：

- 只有 tests，可能代码没坏但 Agent 行为回退
- 只有 eval，可能行为没变但底层代码已经不稳

### 3. 为什么用统一 report

因为发布门禁本质上是一份可读、可归档、可阻断的验收结果。

统一 report 方便：

- 本地查看
- CI 输出
- 失败定位
- 版本复盘

## 运行示例

运行发布门禁：

```bash
python -m cli.release_gate
```

保存 JSON 报告：

```bash
python -m cli.release_gate --output logs/release-gate-report.json
```

## 验证命令

```bash
python -m unittest tests.test_release_gate -v
python -m unittest discover -s tests -v
python -m cli.release_gate
```

## 当前边界

- 这是本地发布门禁，不是完整云端 CI 系统
- 还没有接入 GitHub Actions 或其他远程流水线
- 当前目标是先把“可执行门禁”做稳，再接外部 CI

## 下一步建议

下一阶段建议进入 `v46`，补真正的 checkpoint branch resume，让恢复能力从“可读”推进到“可继续执行”。
