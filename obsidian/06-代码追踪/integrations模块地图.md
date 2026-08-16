# integrations模块地图

## 模块职责

`integrations/` 负责把项目能力接到专业框架层，重点是 LangGraph 和 LangChain 的适配。

## 主要文件

- [integrations/langgraph_workflow.py](../../integrations/langgraph_workflow.py)：默认 graph runtime、路由、tool / skill / workflow / subagent 接入
- [integrations/langchain_tools.py](../../integrations/langchain_tools.py)：工具适配层

## 当前关键职责

- 保持 classic runtime 与 graph runtime 能力对齐
- 把 tool metadata 保留给 trace / checkpoint / recovery
- 承接 route hints

## 当前复杂点

- `langgraph_workflow.py` 体量大
- 它既是适配层，也是实际主执行器的一部分

## 和 v51 的关系

`v51` 在这里的重点是：

- graph runtime 也要保留 `subagent_runtime`
- 不允许只在 classic runtime 生效

## 关联

- [[agent模块地图]]
- [[subagent模块地图]]
