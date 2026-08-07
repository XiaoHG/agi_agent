# 项目总复盘：从最小 Agent 到专业 Agent 学习工作台

这份复盘不是按“每次改了什么”写的，而是按“整个项目是怎么一步步长出来的”写的。

如果你要重新理解这个仓库，先抓住一句话：

> 这个项目的主线，是把一个只能回答问题的程序，逐步升级成一个可路由、可调用工具、可接 RAG / MCP / Skills / Subagent、可测试、可评估、可复盘的 Agent 学习工作台。

## 一、先看总路线

整个项目其实分成四层。

### 1. 最小闭环层

先解决最基本的问题：

- 用户输入怎么进入系统
- 系统怎么决定要不要调用工具
- 工具结果怎么回到模型或最终输出

这一层的目标不是“聪明”，而是“能跑通”。

例子：

- 问 “Read README.md”
- 系统判断要读文件
- 调用 `read_file`
- 把文件内容返回给用户

这一步完成后，Agent 和普通聊天程序的区别就开始出现了。

### 2. 能力扩展层

在能跑通之后，开始加能力：

- 状态管理
- 工作流
- RAG
- MCP
- Skills
- Subagent

这一层的目标不是堆框架，而是让 Agent 能处理更复杂的任务。

例子：

- 不是只读一个文件
- 而是“先找资料，再总结，再解释，再给下一步建议”

### 3. 专业编排层

当能力变多后，重点就变成“怎么组织能力”。

所以后面引入了：

- LangChain adapter
- LangGraph workflow
- tool calling
- tool loop
- synthesis

这一层的目标是让系统不只是“有工具”，而是“会按流程用工具”。

### 4. 工程化与可观测性层

最后不是再加一个新能力，而是把系统变得可调试、可评估、可恢复。

所以你又加了：

- tests
- evals
- structured trace
- recovery plan
- runtime events
- version docs
- learning state

这一层决定了这个项目是不是一个真正可长期迭代的 Agent 工程项目。

## 二、按阶段看你到底学到了什么

| 阶段 | 重点 | 真正学到的东西 | 例子 |
|---|---|---|---|
| Week 1 | 最小 CLI Agent | Agent 的最小闭环 | 输入一句话，决定直接答还是读文件 |
| Week 2 | 状态与工作流 | Agent 可以分步骤做事 | 先读 README，再整理摘要 |
| Week 3 | RAG / MCP | Agent 能用本地知识和外部协议 | 搜索 docs、读 MCP 工具 |
| Week 4 | Skills / Subagent | 高频任务可以封装，复杂任务可以分工 | 解释技能、规划协作 |
| Week 5 | 工程化 / eval / project assistant | 不能只看输出，要看回归与可观测性 | trace、eval、demo |
| Week 6 | 真实 LLM / Tool Calling / LangGraph | 专业 Agent 不是一个函数，而是一条执行链 | DeepSeek、tool loop、graph、recovery |

## 三、几个关键转折点

### 转折 1：从“聊天程序”变成“工具程序”

最开始你要理解的是：

- 不是所有问题都该直接回答
- 有些问题应该交给工具

例如：

- “Read README.md”
- “List the main directories”

这类问题如果直接靠模型猜，风险高、答案不稳定。
正确做法是让 Agent 调工具，再根据工具结果回答。

这一步的本质是：

> 模型负责决策，代码负责执行。

### 转折 2：从“单步工具”变成“多步任务”

有了工具之后，下一步不是继续加新工具，而是让 Agent 会分步骤做事。

例如：

1. 先读 README
2. 再看目录结构
3. 再总结当前项目目标

这就是状态和工作流的意义。

你学到的不是 workflow 这个词，而是：

> 复杂任务不能一次性做完，必须把中间状态留下来。

### 转折 3：从“本地能力”变成“专业能力接入”

后面你引入了 RAG、MCP、Skills、Subagent。

这一步的意义是：

- RAG 解决“知识从哪里来”
- MCP 解决“外部工具怎么接”
- Skills 解决“高频任务怎么封装”
- Subagent 解决“复杂任务怎么分工”

这四个方向不是并列炫技，而是四种不同的工程问题。

### 转折 4：从“能运行”变成“能复盘、能恢复”

这是最关键的一步。

因为 Agent 项目真正难的地方不是“跑一次”，而是：

- 出错后知道错在哪里
- 失败后能不能恢复
- 下次能不能复现

所以你后来补了：

- structured trace
- eval
- recovery plan
- runtime events

这一步让项目从 demo 变成了工程。

## 四、最重要的几个设计原则

### 1. 先简单闭环，再升级框架

不要一开始就上复杂编排框架。

正确顺序是：

1. 最小 Agent 闭环
2. 工具调用
3. 状态与工作流
4. RAG / MCP / Skills
5. LangGraph / observability / recovery

原因很简单：

如果你连“为什么要调用工具”都没想清楚，上框架只会增加理解负担。

### 2. 输出给人看的，和输出给程序看的，必须分开

例子：

- `ToolResult.output`：给人看
- `ToolResult.metadata`：给程序看

后面 `RecoveryPlan.to_text()` / `to_dict()`、`RuntimeEvent.to_text()` / `to_dict()` 也是一样。

这不是重复设计，而是工程上必要的分层。

### 3. 失败不是垃圾，失败是数据

你这次项目逐步把失败变成了结构化对象：

- tool failure -> `RecoveryPlan`
- skill failure -> `RecoveryPlan`
- runtime trace -> `RuntimeEvent`

这意味着失败不再只是“报错退出”，而是可以：

- 测试
- 评估
- 记录
- 恢复
- 复盘

### 4. 代码和学习材料要同步

这个仓库不是只写代码，而是代码、练习、版本文档、学习状态一起维护。

这很重要，因为你学的不是“一个功能”，而是“一个演进过程”。

## 五、几个具体例子，帮你把主线串起来

### 例子 1：读 README

问题：

> Read README.md and summarize the project learning goals.

系统会做什么：

1. 路由到 `read_file`
2. 读取 README
3. 摘要关键内容

你学到的是：

- agent 不只是回答
- agent 可以先执行，再总结

### 例子 2：搜索本地资料

问题：

> Search docs for MCP.

系统会做什么：

1. 路由到 `search_docs`
2. 搜索本地文档
3. 返回相关上下文

你学到的是：

- RAG 的核心不是“模型会不会记”
- 而是“先找证据，再回答”

### 例子 3：Skill 执行

问题：

> Execute skill for learning explanation.

系统会做什么：

1. 选择一个 skill
2. 按步骤执行
3. 记录 step、observation、status

你学到的是：

- 高频任务适合封装成 skill
- 不是每次都重新写流程

### 例子 4：工具失败恢复

问题：

> Use LangGraph to read not-exist.md.

系统会做什么：

1. 进入 graph
2. 调用读文件工具
3. 失败后进入 recovery node
4. 生成 `RecoveryPlan`

你学到的是：

- 失败路径也应该是主流程的一部分
- 失败不是中断，而是输入给下一步的结构化信息

### 例子 5：运行事件

同样一次 run，系统现在能输出：

- 原始 step
- graph route
- recovery plan
- skill run
- error

这意味着以后你可以把一次运行当成一个“可回放事件序列”来看，而不是只看最终答案。

## 六、到现在为止，你已经真正建立起来的能力

不是“写了很多文件”，而是这些能力：

1. 能搭一个最小 Agent 闭环
2. 能给 Agent 加工具
3. 能让 Agent 分步骤工作
4. 能让 Agent 接 RAG、MCP、Skills、Subagent
5. 能把真实 LLM 接进来
6. 能用 LangGraph 组织执行链
7. 能对失败做结构化恢复
8. 能用 tests 和 eval 保证回归
9. 能用 trace 解释 Agent 为什么这么做
10. 能把学习过程变成可恢复的项目状态

## 七、现在最容易犯的理解误区

### 误区 1：以为加框架就是进步

不是。

如果没有清晰的输入、输出、状态和验证，加框架只会让系统更难看懂。

### 误区 2：以为 trace 只是调试日志

不是。

trace 是后续评估、恢复、回放、复盘的基础材料。

### 误区 3：以为失败只需要打印错误

不是。

失败最好是结构化数据，不然你只能“看见报错”，看不见“失败类型、来源和下一步动作”。

### 误区 4：以为学习 Agent 就是学 prompt

不是。

真正的 Agent 学习包括：

- 路由
- 工具
- 状态
- 工作流
- RAG
- 协议
- skills
- 协作
- eval
- trace
- recovery

## 八、你接下来复盘时应该怎么读

建议顺序：

1. 先读这份总复盘
2. 再读 `docs/current-learning-state.md`
3. 再看 `versions/` 里每个阶段的版本文档
4. 最后回到代码和练习题

这样你会从“功能片段”重新拼回“整条主线”。

## 九、下一步怎么学

如果你要继续往下学，我建议下一阶段重点看：

- checkpoint / persistence
- runtime replay
- 更专业的 MCP / Skills 体系
- LangGraph 默认执行器化

因为到 v25 为止，你已经有了：

- 事件
- 恢复
- trace
- eval
- 真实 LLM
- tool loop
- graph

下一步最自然的升级，就是把这些运行信息真正持久化并可恢复。
