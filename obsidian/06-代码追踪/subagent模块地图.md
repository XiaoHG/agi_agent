# subagent模块地图

## 模块职责

`subagent/` 负责项目默认协作 Agent 的角色定义、多 Agent 委派协议、运行时基础层和学习型协作边界。

## 主要文件

- [subagent/team.py](../../subagent/team.py)：角色、契约、delegation、handoff、return、execution、runtime session
- [subagent/teacher-agent/](../../subagent/teacher-agent)：Teacher Agent 说明
- [subagent/coding-agent/](../../subagent/coding-agent)：Coding Agent 说明

## 核心对象

- `SubagentSpec`
- `SubagentTaskContract`
- `SubagentDelegationRecord`
- `SubagentHandoffRecord`
- `SubagentReturnRecord`
- `SubagentExecutionRecord`
- [[runtime-session]]
- [[message-envelope]]
- [[state-transition]]
- [[context-boundary]]

## 执行入口

- `build_collaboration_plan()`
- `execute_collaboration_plan()`
- `execute_subagents`

## 当前最值得理解的链路

```text
build_collaboration_plan
-> execute_collaboration_plan
-> build_runtime_session
-> subagent_runtime metadata
-> runtime events / checkpoint / graph runtime
```

## 当前复杂点

- `team.py` 已成为多 Agent 主线的中心文件
- 需要同时理解协议层和 runtime 层

## 当前问题

- 还没有 async queue / inbox / outbox
- 还没有 task claim / blocked lifecycle
- 还没有真实独立子 Agent 调度

## 关联

- [[多Agent主链路]]
- [[v51-多Agent运行时基础-理解版]]
