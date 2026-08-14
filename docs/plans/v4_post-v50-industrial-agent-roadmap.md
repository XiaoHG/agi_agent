# v4：v50 之后的工业级 Agent 迭代总纲

日期：2026-08-14

用途：本文件用于承接 `v50` 之后的新一轮版本规划。`v3` 总纲已经完成从基础运行时到委派协议收口的主线推进；从本文件开始，项目进入“把协议做成真实工业运行体系”的下一阶段。

若后续版本规划与本文件冲突，以本文件为准。

## 1. 当前项目判断

截至 `v50`，项目已经具备以下主干能力：

- LLM-first 入口
- LangGraph 默认主执行器
- RAG / MCP / Skills / Subagent 能力层
- structured trace / runtime events
- checkpoint / replay / replay diff / guided resume
- recovery plan / release gate / evaluation matrix
- multi-agent delegation / handoff / execution / return / recovery protocol

当前项目已经不缺“功能点”，而是进入了“工业运行体系深化”阶段。

当前最主要缺口有四个：

1. 多 Agent 仍是 deterministic protocol execution，不是真实 runtime。
2. 长任务还没有生命周期管理、暂停、续跑、审批闭环。
3. MCP / Skills 治理还偏本地，缺少外部化 registry 和环境治理。
4. 交付体系已有 release gate，但距离持续发布和审计闭环还有距离。

## 2. 新阶段总目标

`v50` 之后的目标，不再是继续补齐基础能力，而是把现有协议和治理骨架推进成更接近生产化的 Agent 运行体系。

新的总目标是：

- 让多 Agent 从“可执行协议”升级为“真实运行系统”
- 让长任务从“可恢复 run”升级为“可管理生命周期”
- 让治理从“本地策略”升级为“外部化、可审计、可审批”
- 让交付从“本地验证”升级为“持续化质量门禁”

## 3. 本阶段开发原则

后续版本继续遵守 `v3` 中的大功能原则，但要额外强化下面四点。

### 3.1 真实运行原则

- 后续版本优先解决 runtime 真问题，而不是继续补静态结构。
- 不能只新增数据模型而没有对应执行路径。
- 不能只新增 trace 字段而没有实际运行价值。

### 3.2 生命周期原则

- 后续版本要更多围绕任务生命周期建设。
- 每个大功能都要说明：
  - 如何开始
  - 如何执行
  - 如何暂停
  - 如何恢复
  - 如何结束

### 3.3 人工介入原则

- 后续工业级版本不能假设系统永远自动完成。
- 对高风险写操作、多 Agent 冲突、长任务关键节点，要开始引入审批、确认或人工接管边界。

### 3.4 外部化原则

- 本地学习版能力已经足够多，后续要优先考虑如何外部化和标准化。
- 包括：
  - registry
  - policy
  - environment
  - audit

## 4. 后续版本立项硬要求

从 `v51` 开始，每个版本在立项前必须回答：

1. 这个版本解决的是哪一个工业运行缺口？
2. 它对多 Agent、长任务、治理、交付中的哪一条主线有直接推进？
3. 它的运行入口是什么？
4. 它的失败边界、审批边界和恢复边界是什么？
5. 它完成后，下一版本能在什么基础上继续推进？

如果这五个问题回答不清，版本不立项。

## 5. 后续版本交付要求

每个版本必须尽量形成完整闭环：

```text
问题定义
-> 数据模型
-> runtime integration
-> CLI/demo
-> tests
-> eval / gate
-> trace / replay / recovery / audit 至少一项
-> 版本文档
-> 练习与答案
```

对于 `v50` 之后的新阶段，额外要求：

- 至少一个“失败路径”验证
- 至少一个“恢复或审批路径”验证
- 至少一个“跨模块集成”验证

## 6. v50 之后的主线排序

基于当前复盘结果，后续版本优先级应按下面顺序推进：

```text
真实多 Agent runtime
-> 异步委派与任务收发
-> 审批与人工接管
-> 长任务生命周期管理
-> 外部化 registry / policy / environment
-> 持续交付与审计闭环
```

原因是：

- `v50` 已经把协议结构准备好了
- 当前最自然的放大方向是把协议变成真实运行系统
- 真实运行系统建立后，审批、长任务、治理和交付才能真正落地

## 7. 新阶段版本规划

下面是 `v51` 之后的新阶段推荐版本安排。

### v51：Real Multi-Agent Runtime Foundation

主目标：

- 把 `v50` 的 deterministic delegation protocol 升级为真实多 Agent runtime 基础层。

应覆盖：

- subagent runtime session model
- agent message envelope
- parent / child context boundary
- execution state machine
- runtime event integration
- CLI/demo、tests、文档和练习

本版本不做：

- 分布式队列
- 真正并发调度
- 人工审批全链路

为什么它是大功能：

- 没有真实 runtime，多 Agent 仍只是“结构化示意图”。

### v52：Async Delegation Queue and Agent Inbox

主目标：

- 把多 Agent runtime 从同步调用推进到异步收发模型。

应覆盖：

- delegation queue
- agent inbox / outbox
- task claim / complete / fail
- pending / running / blocked 状态
- replay / checkpoint / audit 联动
- CLI/demo、tests、文档和练习

本版本不做：

- 外部消息中间件
- 横向扩展调度集群

为什么它是大功能：

- 多 Agent 一旦进入真实协作，就必须先解决“任务如何挂起、接收和回传”。

### v53：Human Approval and Risk-Control Workflow

主目标：

- 为高风险任务、多 Agent 关键切换和外部写操作建立正式审批流。

应覆盖：

- approval request model
- approval decision record
- risk classification
- guarded tool / MCP / skill / subagent handoff
- reject / revise / resume path
- CLI/demo、tests、eval、文档和练习

本版本不做：

- 完整 web 审批平台
- 企业级权限系统

为什么它是大功能：

- 工业 Agent 不能只考虑“能不能自动做”，还要考虑“什么时候必须停下来等人确认”。

### v54：Long-Horizon Task Lifecycle Management

主目标：

- 建立长期任务的生命周期管理模型。

应覆盖：

- task lifecycle state
- pause / resume / expire / abandon
- checkpoint lineage on long tasks
- milestone record
- task health / watchdog signal
- CLI/demo、tests、文档和练习

本版本不做：

- 多租户任务运营后台
- 分布式任务系统

为什么它是大功能：

- 只有把“任务”做成一等对象，项目才算真正进入长期运行阶段。

### v55：Externalized Registry and Runtime Governance

主目标：

- 把本地 MCP / Skills 治理推进到外部化 registry 和统一运行治理。

应覆盖：

- externalized skill registry abstraction
- externalized MCP catalog abstraction
- environment-aware policy loading
- runtime governance audit record
- version / permission / policy resolution
- CLI/demo、tests、文档和练习

本版本不做：

- 完整远程控制台
- 真实 SaaS registry 服务

为什么它是大功能：

- 没有外部化 registry 和统一治理，项目很难进一步逼近生产环境。

### v56：Continuous Release Audit and Delivery Control

主目标：

- 把 release gate 升级为持续化交付与审计控制链路。

应覆盖：

- delivery audit report
- version readiness summary
- regression / eval / gate aggregation
- release policy profile
- CI-oriented output contract
- CLI/demo、tests、文档和练习

本版本不做：

- 完整云端 CI 平台集成
- 自动化发布平台

为什么它是大功能：

- 工业 Agent 项目最终必须回答“当前版本是否可交付”，而不只是“本地能跑”。

## 8. 推荐的实现节奏

建议按两个阶段推进：

### 第一阶段：把多 Agent 做成真实运行系统

- `v51`
- `v52`
- `v53`

这一阶段的核心目标是：

- 真正运行
- 真正挂起
- 真正审批

### 第二阶段：把长期运行与治理做成体系

- `v54`
- `v55`
- `v56`

这一阶段的核心目标是：

- 真正长期执行
- 真正统一治理
- 真正形成持续交付判断

## 9. 新阶段学习要求

从 `v51` 开始，学习重点也要升级。

后续每个版本的文档必须讲清楚：

- 这个版本在工业运行系统中的位置
- 它和 `v50` 的关系
- 它新增了什么运行对象和状态流转
- 它的失败路径和人工介入点在哪里
- 它如何和 checkpoint / replay / recovery / audit 联动

练习题必须继续覆盖：

- 概念理解题
- 代码阅读题
- 手动验证题
- 工程取舍题

并且答案必须直接写回练习文件。

## 10. 执行结论

从现在开始：

- `v3` 视为上一阶段总纲。
- 本文件作为 `v50` 之后的新阶段总纲。
- 后续版本优先按 `v51 -> v56` 的顺序推进。
- 如果中途调整顺序，必须先说明调整原因，并证明没有偏离“真实 runtime、长任务、治理、交付”这四条主线。
