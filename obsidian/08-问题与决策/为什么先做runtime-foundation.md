# 为什么先做runtime-foundation

## 结论

在多 Agent 主线上，先做 runtime foundation 比直接做 async queue 更稳，因为没有 session / message / transition，后续异步机制会缺少正式数据边界。

## 背景

`v50` 已经有 delegation protocol，但仍然没有：

- session
- message envelope
- state transition

## 备选方案

### 方案 A：直接上 async queue

优点：

- 看起来更接近工业系统

问题：

- 数据边界不稳
- 很难回放和验证
- 容易把协议层和调度层混在一起

### 方案 B：先补 runtime foundation

优点：

- 先稳定运行对象
- 更容易接入 trace / graph / checkpoint
- 更适合学习和拆分版本

## 为什么选择当前方案

- 工程上更稳
- 学习上更清晰
- 验证上更容易形成闭环

## 后续升级点

- [[v52-异步委派队列计划]]

## 关联

- [[v51-多Agent运行时基础-理解版]]
