# v51-多Agent运行时基础-理解版

## 本版本结论

`v51` 把 `v50` 的可执行委派协议继续推进成真正的 runtime foundation，让多 Agent 协作第一次拥有 session、message、transition 和 context boundary。

## 正式文档

- [versions/v51_real-multi-agent-runtime-foundation.md](../版本文档/v51_real-multi-agent-runtime-foundation.md)
- [docs/v51_real-multi-agent-runtime-foundation-exercises.md](../../04-文档管理/项目文档/v51_real-multi-agent-runtime-foundation-exercises.md)

## 为什么要做这个版本

`v50` 已经有 delegation / handoff / execution / return，但仍然缺少：

- 当前运行属于哪个 session
- 当前激活角色是谁
- 消息怎么结构化表达
- 状态是怎么迁移的

## 这个版本解决的问题

- 给多 Agent 协作增加正式 runtime session
- parent / child context boundary 进入结构化数据
- 协作消息进入 message envelope
- 协作状态变化进入 state transition
- trace / graph / checkpoint 一起保留这些运行证据

## 新增核心对象

- [[runtime-session]]
- [[message-envelope]]
- [[state-transition]]
- [[context-boundary]]

## 代码入口

- [subagent/team.py](../../../subagent/team.py)
- [agent/tools.py](../../../agent/tools.py)
- [agent/events.py](../../../agent/events.py)
- [integrations/langgraph_workflow.py](../../../integrations/langgraph_workflow.py)

## 执行流程

1. 先由 `build_collaboration_plan()` 建立 delegation plan
2. 再由 `execute_collaboration_plan()` 生成 execution / return
3. 由 `build_runtime_session()` 把这些记录汇总成 session
4. 通过 `execute_subagents` 把 `subagent_delegation` 和 `subagent_runtime` 一起暴露给 runtime
5. graph / checkpoint / runtime events 一起保留 session 证据

## 和上一版的关系

- `v50`：协议完整性
- `v51`：运行时基础层

## 给下一版留下的基础

现在已经有了：

- session
- messages
- transitions
- context boundary

这使得 [[v52-异步委派队列计划]] 可以直接继续做 queue / inbox / claim。

## 我的理解

`v51` 最重要的不是“又加了几个结构体”，而是第一次把多 Agent 协作变成了会话级运行对象。

## 验证方式

- `python -m unittest discover -s tests -q`
- `python -m cli.collaboration_demo --task "Implement a bug fix and test it." --execute-subagents --runtime-json`
- `python -m cli.main --input "Execute subagent collaboration for a code review." --trace`

## 关联

- [[v50-委派协议硬化-理解版]]
- [[v52-异步委派队列计划]]
- [[subagent模块地图]]
