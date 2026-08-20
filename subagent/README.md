# subagent/

放多 Agent 协作实验和项目默认协作 Agent 定义。

当前默认 Agent：

- `teacher-agent/`：负责学习答疑、代码讲解、架构解释、学习规划和复盘。
- `coding-agent/`：负责代码编写、bug 修复、测试、验证和工程质量维护。

建议新增 Subagent 时至少包含：

- `README.md`：说明职责、适用场景、不适用场景、协作边界。
- `agent.md`：可直接复用的角色定义和行为规则。

## 默认路由规则

- 学习、解释、答疑、路线规划：优先 Teacher Agent。
- 编码、修复、测试、验证：优先 Coding Agent。
- 同时包含学习和实现：Teacher Agent 先说明设计，Coding Agent 再实现。

## 当前实现

当前阶段已经实现 deterministic collaboration planner + delegation contract + handoff / return / execution trace + runtime session foundation，并在 `v52` 进一步补上 async-ready delegation queue、agent inbox / outbox 和 task claim evidence。

```text
subagent/
  team.py        # SubagentSpec, delegation contract, runtime session, message envelope, state transition, queue/inbox/outbox/claim
```

运行：

```bash
python -m cli.collaboration_demo --list-subagents
python -m cli.collaboration_demo --task "Review this code and add tests."
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --runtime-json
python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --queue-json
python -m cli.collaboration_demo --task "Implement a blocked offline code change." --execute-subagents --inbox-role coding_agent --outbox-role coding_agent
python -m cli.main --input "Plan subagent collaboration for a code review." --trace

当前协作计划会同时输出：

- 角色职责
- 输入边界
- 输出边界
- 子任务契约
- delegation record
- handoff record
- return record
- execution record
- runtime session
- message envelopes
- state transitions
- queue items
- inbox entries
- outbox entries
- claim records
```
