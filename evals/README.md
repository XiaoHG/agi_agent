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

当前阶段新增 deterministic regression eval runner。

```text
evals/
  regression_cases.json   # 固定回归用例
  runner.py               # 加载、运行、判断、生成报告
```

运行：

```bash
python -m cli.eval_runner
python -m cli.eval_runner --output logs/eval-report.json
```

当前判断维度：

- route 是否符合预期
- tool 是否符合预期
- answer 是否包含必要关键词

当前 regression cases 已包含一个 LLM-grounded RAG 工具接线用例。该用例使用无本地上下文的问题，因此不会触发真实 DeepSeek 网络请求；它只验证主 Agent 能正确路由到 `answer_docs_with_llm` 并返回 insufficient 边界结果。

后续可以继续扩展：

- 人工评分维度
- 错误分类
- trace 归档
- 多轮 eval
