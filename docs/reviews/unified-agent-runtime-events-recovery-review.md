# v25 阶段总结：统一 Agent 运行事件与恢复模型

## 本阶段做了什么

本阶段把 LangGraph 的失败恢复和主 Agent 的 trace 导出，统一到了两个核心抽象上：

- `RecoveryPlan`：统一描述 tool / skill / exception 的失败恢复。
- `RuntimeEvent`：统一描述 Agent 运行过程中的事件。

这一步的意义不是增加“更多功能”，而是把之前分散在 graph、core、trace、eval 里的失败和事件信息收敛成稳定结构，方便后续做 checkpoint、replay、审计和恢复策略。

## 关键改动

### 1. 统一恢复模型

新增 `agent/recovery.py`，把恢复逻辑从 `integrations/langgraph_workflow.py` 中抽出来。

效果：

- 普通 tool failure 使用同一套恢复计划。
- Skill failure 使用同一套恢复计划。
- graph exception 也能进入统一恢复路径。

### 2. 统一运行事件

新增 `agent/events.py`，从现有 trace 数据生成标准事件流。

效果：

- `WorkspaceAgent.format_trace()` 能显示 `[Runtime Events]`。
- `WorkspaceAgent.to_trace_dict()` 能输出 `runtime_events`。
- 后续可以直接基于事件做日志、回放和分析。

### 3. LangGraph 恢复路径标准化

`integrations/langgraph_workflow.py` 现在只负责 graph 编排，不再自己维护一堆局部 recovery helper。

效果：

- 逻辑边界更清晰。
- 恢复行为更容易测试。
- 未来扩展 checkpoint 时不会继续膨胀 graph 文件。

### 4. 学习材料同步更新

新增：

- `versions/v25_unified-agent-runtime-events-recovery.md`
- `docs/v25_unified-agent-runtime-events-recovery-exercises.md`

同时更新：

- `docs/current-learning-state.md`

## 本阶段验证结果

已验证：

```bash
python -m unittest discover -s tests -v
python -m cli.eval_runner
python -m cli.main --input "Use LangGraph to read not-exist.md." --trace
python -m cli.main --input "Use LangGraph to execute skill for learning explanation." --trace
```

结论：

- 全量测试通过。
- 全部 eval 通过。
- tool failure recovery 正常。
- skill execution trace 正常。
- runtime events 正常输出。

## 复盘要点

1. 失败恢复不应只写成文本说明，必须结构化。
2. graph state 应优先保存 JSON-ready 数据。
3. trace 不只是调试输出，也应是后续 eval 和持久化的输入。
4. 统一模型比在每个 node 里各写一套 helper 更适合专业 Agent 工程。

## 当前版本状态

- 本地已提交：`636af5b Add unified runtime events and recovery model`
- 已推送到远端：`origin/main`

## 下一阶段建议

下一阶段应进入：

`v26：LangGraph Checkpoint and Recoverable Run Persistence`

方向建议：

- 给 graph run 引入可恢复的 run id。
- 将 graph state 和 runtime events 落盘。
- 提供 CLI 查看最近一次运行。
- 为 checkpoint / replay 建测试和 eval。
