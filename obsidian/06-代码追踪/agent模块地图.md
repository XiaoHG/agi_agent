# agent模块地图

## 模块职责

`agent/` 负责主 Agent runtime、路由、工具调用、trace、memory、checkpoint、replay、recovery 和最终答案整合。

## 主要文件

- [agent/core.py](../../agent/core.py)：主运行入口与 trace 导出
- [agent/router.py](../../agent/router.py)：意图路由
- [agent/tools.py](../../agent/tools.py)：工具能力入口
- [agent/events.py](../../agent/events.py)：runtime events
- [agent/persistence.py](../../agent/persistence.py)：checkpoint 持久化
- [agent/replay.py](../../agent/replay.py)：run replay 与 diff

## 核心对象

- `WorkspaceAgent`
- `ToolRoute`
- `RuntimeEvent`
- `RecoveryPlan`

## 执行入口

- `python -m cli.main`
- LangGraph wrapper 最终也回到 `WorkspaceAgent` 的外层语义

## 当前复杂点

- [agent/core.py](../../agent/core.py) 较大
- trace / runtime events / graph metadata 之间的关系需要系统理解

## 当前问题

- 未来随着多 Agent、审批、长任务继续增强，`agent/` 的 orchestration 边界可能还要进一步梳理

## 关联

- [[工业Agent主链路]]
- [[subagent模块地图]]
