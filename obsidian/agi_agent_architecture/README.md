# agi_agent 执行架构总览

这组文档基于当前项目真实代码整理，不是通用 Agent 模板图。

主执行链路以当前实现为准：

`cli/main.py`
-> `agent/core.py`
-> `agent/router.py`
-> `integrations/langgraph_workflow.py`
-> `agent/tools.py`
-> `agent/events.py`
-> `agent/persistence.py`
-> `agent/replay.py`
-> `evals/release_gate.py`

建议阅读顺序：

1. `01-系统执行总图.md`
2. `02-CLI到Runtime时序图.md`
3. `03-路由与函数决策流.md`
4. `04-LangGraph状态机.md`
5. `05-运行证据与恢复链路.md`
6. `06-质量门禁与CI-ready流程.md`
7. `07-子Agent委派与消息流.md`

关键代码：

- [cli/main.py](../../cli/main.py)
- [agent/core.py](../../agent/core.py)
- [agent/router.py](../../agent/router.py)
- [integrations/langgraph_workflow.py](../../integrations/langgraph_workflow.py)
- [agent/tools.py](../../agent/tools.py)
- [agent/events.py](../../agent/events.py)
- [agent/persistence.py](../../agent/persistence.py)
- [agent/replay.py](../../agent/replay.py)
- [evals/release_gate.py](../../evals/release_gate.py)
- [subagent/team.py](../../subagent/team.py)
