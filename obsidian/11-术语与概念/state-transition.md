# state-transition

## 定义

`state transition` 表示 runtime 从一个状态进入另一个状态的正式记录。

## 在本项目中的含义

它对应 `SubagentStateTransition`，记录：

- from_state
- to_state
- actor
- reason

## 为什么重要

后续 stuck task detection、pause / resume、approval、recovery 都会依赖状态迁移证据。

## 相关代码

- [subagent/team.py](../../subagent/team.py)

## 相关版本

- [[v51-多Agent运行时基础-理解版]]

## 关联

- [[runtime-session]]
