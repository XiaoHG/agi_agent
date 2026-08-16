# context-boundary

## 定义

`context boundary` 是父角色与当前活跃子角色之间允许输入、禁止输入和期望输出的边界定义。

## 在本项目中的含义

它对应 `SubagentContextBoundary`。

## 为什么重要

多 Agent 工程不只是任务切换，还要明确：

- 什么可以进
- 什么不能进
- 输出必须长成什么样

## 相关代码

- [subagent/team.py](../../subagent/team.py)

## 相关版本

- [[v51-多Agent运行时基础-理解版]]

## 关联

- [[runtime-session]]
