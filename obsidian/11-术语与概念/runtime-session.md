# runtime-session

## 定义

`runtime session` 是一次多 Agent 协作在运行期的正式会话对象。

## 在本项目中的含义

它对应 `SubagentRuntimeSession`，用于保存：

- session_id
- parent role
- child roles
- active role
- current delegation
- context boundary
- messages
- transitions

## 为什么重要

因为后续 async queue、approval、long-horizon lifecycle 都需要以会话对象为基础。

## 相关代码

- [subagent/team.py](../../subagent/team.py)

## 相关版本

- [[v51-多Agent运行时基础-理解版]]

## 关联

- [[message-envelope]]
- [[state-transition]]
- [[context-boundary]]
