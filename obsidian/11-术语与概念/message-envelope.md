# message-envelope

## 定义

`message envelope` 是多 Agent runtime 中的正式消息单元。

## 在本项目中的含义

它对应 `SubagentMessageEnvelope`，表达：

- from_role
- to_role
- message_type
- summary
- referenced_records

## 为什么重要

它是后续 async delegation queue / inbox / outbox 的直接前置结构。

## 相关代码

- [subagent/team.py](../../subagent/team.py)

## 相关版本

- [[v51-多Agent运行时基础-理解版]]

## 关联

- [[runtime-session]]
