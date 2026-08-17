# 第 2 章初稿修订记录

## 日期

2026-08-07

## 修订对象

`publish/drafts/ch02/README.md`

## 修订原因

建立书稿第二章主线，说明最小 Agent 闭环为什么是后续所有能力的底座。

## 涉及证据

- `versions/v01_minimal-cli-agent.md`
- `docs/v01_minimal-cli-agent-exercises.md`
- `versions/v02_state-workflow.md`
- `docs/v02_state-workflow-exercises.md`
- `agent/router.py`
- `agent/core.py`
- `tests/test_agent.py`

## 修改摘要

- 解释为什么先做闭环，而不是先做框架。
- 解释路由层、工具层、输出层、测试层的分工。
- 用 v02 引出状态与工作流的下一阶段。

## 待办

- 补一张最小 Agent 闭环图。
- 增加几个来自实际 CLI 输出的短例子。
- 开始第 3 章草稿。

## 2026-08-17 结构整理补记

- 将第 2 章草稿从扁平文件迁移到 `publish/drafts/ch02/README.md`。
- 保持章节主稿路径稳定，便于后续继续扩写和审校。

## 2026-08-17 参考资料驱动修订补记

- 依据 `publish/reference-examples/writing-standards-summary.md` 对第 2 章做结构修订。
- 新增“本章要解决的问题”“读者完成本章后的收获”“关键代码入口”“验证与复盘”。
- 修订目标是让本章更符合工程案例型章节写法，而不是只停留在版本说明。
