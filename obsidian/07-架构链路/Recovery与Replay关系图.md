# Recovery与Replay关系图

## 结论

Recovery 和 Replay 是当前项目中最重要的“工程证据链”之一，它们决定系统失败后能不能解释和继续推进。

## 关系图

```text
Runtime execution
-> Trace / Runtime Events
-> Checkpoint
-> Replay
-> Replay Diff
-> Recovery Plan
-> Resume / Branch Resume
```

## 当前作用

- Replay：回看发生了什么
- Replay Diff：比较不同 run 的差异
- Recovery：把失败转成下一步行动计划
- Resume：从历史节点继续

## 现阶段限制

- 对 subagent runtime session 已能保留数据
- 但还不能基于 session 做异步挂起和恢复执行

## 关联

- [[工业Agent主链路]]
- [[当前长期任务缺口]]
