# v27 练习：Run History Browsing and Checkpoint Lookup

## 练习 1：历史列表能回答什么问题？

回答：

1. 为什么需要 `--list-runs`？
2. 它和 `--show-last-run` 的区别是什么？
3. 历史列表里最重要的 3 个字段是什么？

## 练习 2：按 run id 查看为什么更有价值？

回答：

1. 为什么不能只依赖 latest？
2. 指定 run id 对复盘有什么帮助？
3. 你会在什么场景下优先使用 `--show-run`？

## 练习 3：history 层和 CLI 层如何分工？

回答：

1. 哪些逻辑应该放在 `agent/persistence.py`？
2. 哪些逻辑应该放在 `agent/core.py`？
3. 哪些逻辑应该只放在 `cli/main.py`？

## 练习 4：和 replay 的关系

回答：

1. run history 浏览和 replay 有什么差别？
2. 当前实现离 replay 还差什么？
3. 如果要从 run history 继续演进到 replay，你会先做什么？

## 练习 5：结合项目举例

回答：

1. 如果一次 LangGraph run 失败了，你会怎样用 `--show-run` 分析它？
2. 如果一次 workflow run 反复出错，你会怎样比较多个 run？
3. 如果你要给别人演示这个项目，你会先展示 latest、list 还是 show-run？
