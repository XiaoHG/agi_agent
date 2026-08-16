# 当前多Agent缺口

## 结论

当前多 Agent 主线最大的缺口不是“少几个角色”，而是“还没有进入真实异步协作和长期调度阶段”。

## 已解决

- role split
- task contract
- delegation / handoff / return / execution
- runtime session / message / transition / context boundary

## 未解决

- async delegation queue
- inbox / outbox
- task claim / release / fail
- blocked / pending / running 生命周期
- 审批和人工介入
- 长任务持续执行

## 为什么这是核心缺口

因为工业多 Agent 的真正难点，是任务如何在多个角色之间安全、长期、可恢复地流转。

## 当前优先级

最高优先级缺口：`v52 async delegation queue`

## 关联

- [[v51-多Agent运行时基础-理解版]]
- [[v52-异步委派队列计划]]
