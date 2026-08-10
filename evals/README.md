# evals/

放 Agent 评估用例、评估脚本和评估报告。

适合放：

- 固定输入样例
- 期望行为
- 人工评分标准
- 自动评估脚本
- 回归测试报告

建议每个阶段至少沉淀一组 eval：

```text
evals/
  week1-basic-agent/
  week3-rag/
  week5-regression/
```

Agent 项目的质量不能只靠“这次跑起来了”判断，必须有可重复评估。

## 当前实现

当前阶段已有 deterministic regression eval runner，并新增更接近工业交付的 eval matrix 与 failure bench。

```text
evals/
  regression_cases.json              # 固定回归用例
  industrial_eval_matrix.json        # 工业评估矩阵规格
  industrial_failure_bench.json      # 失败基准规格
  matrix/
    v44_route_cases.json             # route 类别用例
    v44_tool_cases.json              # tool 类别用例
    v44_skill_cases.json             # skill 类别用例
    v44_recovery_cases.json          # recovery 类别用例
    v44_replay_cases.json            # replay 类别用例
  failure-bench/
    v44_failure_bench_cases.json     # 失败基准集
  runner.py                          # 单 case 文件 runner
  matrix.py                          # eval matrix / failure bench 聚合执行
```

运行：

```bash
python -m cli.eval_runner
python -m cli.eval_runner --output logs/eval-report.json
python -m cli.eval_runner --matrix evals/industrial_eval_matrix.json
python -m cli.eval_runner --failure-bench evals/industrial_failure_bench.json
```

当前 regression 判断维度：

- route 是否符合预期
- tool 是否符合预期
- tool_call 分支下模型选择的实际工具是否符合预期
- answer 是否包含必要关键词

当前工业矩阵结构：

- route
- tool
- skill
- recovery
- replay

当前 failure bench 会固定覆盖已知失败路径，例如：

- missing file
- workflow failure
- MCP write denial
- LangGraph tool recovery
- failed-run replay
- failed-run resume

后续可以继续扩展：

- 人工评分维度
- 错误分类
- trace 归档
- 多轮 eval
