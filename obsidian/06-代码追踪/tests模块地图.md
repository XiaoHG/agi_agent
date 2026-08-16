# tests模块地图

## 模块职责

`tests/` 负责单元测试、集成测试、回归测试和主执行链验证。

## 主要文件

- [tests/test_agent.py](../../tests/test_agent.py)
- [tests/test_langgraph_workflow.py](../../tests/test_langgraph_workflow.py)
- [tests/test_replay.py](../../tests/test_replay.py)
- [tests/test_collaboration.py](../../tests/test_collaboration.py)
- [tests/test_release_gate.py](../../tests/test_release_gate.py)

## 当前判断

当前测试层已经足够支撑“版本闭环验证”，也是学习代码行为的高价值入口。

## 关联

- [[代码入口总览]]
- [[工业Agent主链路]]
