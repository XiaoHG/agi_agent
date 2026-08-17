# assets/

这里存放书稿配图、结构图、流程图、表格草图和后续出版素材说明。

## 使用原则

- 配图服务于章节理解，不做无意义装饰。
- 每张图应能对应具体章节和具体叙述目标。
- 图示应尽量能回到真实代码或真实运行链路。
- 当前统一格式：优先使用 `mermaid` 代码块。
- 后续如进入正式出版排版阶段，再从 `mermaid` 转 SVG 或静态图。

## 当前章节配图规划

### 第 1 章 什么是 Agent，为什么它不是聊天机器人

当前已落地 2 张 `mermaid` 图。

#### 图 1：Chatbot 与 Agent 的最小差异图

目标：

- 帮助读者直观看到“回答系统”和“执行系统”的区别

建议内容：

```text
Chatbot:
  input -> model -> answer

Agent:
  input -> route -> decide -> act -> collect -> answer
```

建议放置位置：

- 第 1 章中段，在解释“模型加工具不自动等于 Agent”之后

#### 图 2：Agent 能力如何逐步生长

目标：

- 帮助读者理解 Agent 不是静态定义，而是逐步长出状态、知识、协议和治理层

建议内容：

```text
direct answer
  -> route
  -> tool use
  -> state
  -> knowledge
  -> protocol
  -> collaboration
  -> runtime / governance
```

建议放置位置：

- 第 1 章后段，在解释“Agent 是不断扩展的系统结构”之后

### 第 2 章 工业级 Agent 的基本结构

当前已落地 3 张 `mermaid` 图。

#### 图 1：工业级 Agent 的结构层次图

目标：

- 帮助读者建立输入、路由、执行、状态、输出、治理这些边界的整体视图

建议内容：

```text
user input
  -> input boundary
  -> routing
  -> execution
       -> tools
       -> knowledge
       -> roles
  -> state / workflow
  -> answer synthesis
  -> observability / recovery / governance
```

建议放置位置：

- 第 2 章中段，在解释结构层次时

#### 图 2：从原型到工业级 Agent 的结构增长图

目标：

- 帮助读者理解结构不是一次性设计完成，而是随复杂度逐步进入系统

建议内容：

```text
prototype
  -> route
  -> tool
  -> workflow
  -> rag
  -> protocol
  -> collaboration
  -> runtime
  -> recovery / governance
```

建议放置位置：

- 第 2 章后段，在解释项目演进路径时

#### 图 3：代码入口与结构边界对应图

目标：

- 帮助读者把概念层结构对应到实际代码入口

建议内容：

```text
cli/main.py        -> system entry
agent/router.py    -> routing boundary
agent/core.py      -> orchestration boundary
tests/test_agent.py -> regression boundary
```

建议放置位置：

- 第 2 章章末，在代码入口说明之前或之后

### 第 3 章 最小 Agent 执行闭环

当前已落地 2 张 `mermaid` 图。

#### 图 1：最小执行主线图

目标：

- 帮助读者建立“输入 -> 路由 -> 执行 -> 输出”的最短主线感

建议内容：

```text
cli input -> route -> branch -> answer
```

建议放置位置：

- 第 3 章中段，在解释最小闭环主线时

#### 图 2：代码职责分布图

目标：

- 帮助读者把最小闭环的职责边界映射到实际文件入口

建议内容：

```text
cli/main.py -> input boundary
agent/router.py -> route boundary
agent/core.py -> execution boundary
tests/test_agent.py -> regression boundary
```

建议放置位置：

- 第 3 章后段，在解释职责拆分和测试护栏时

### 第 4 章 状态、工作流与多步执行

当前已落地 3 张 `mermaid` 图。

#### 图 1：单步闭环与多步执行对比图

目标：

- 帮助读者直观看到为什么 workflow 比单步闭环多出状态与计划层

建议内容：

```text
single-step: input -> route -> execute -> output
multi-step: input -> workflow route -> plan -> step -> state -> step -> summary -> output
```

建议放置位置：

- 第 4 章前段，在解释“为什么单步闭环不够”时

#### 图 2：AgentState 信息承载图

目标：

- 帮助读者理解状态对象并不是简单变量集合，而是运行事实容器

建议内容：

```text
input -> route -> steps -> tool results -> errors -> summary -> answer
```

建议放置位置：

- 第 4 章中段，在解释 `AgentState` 时

#### 图 3：WorkflowPlan 目标到过程的转化图

目标：

- 帮助读者理解 workflow 规划如何把目标拆成可执行步骤

建议内容：

```text
objective -> plan -> step1/step2/synthesize -> write back state
```

建议放置位置：

- 第 4 章后段，在解释 `WorkflowPlan` 时

## 后续建议

- 等第 3、4 章正文稳定后，再继续补对应章节配图规划。
- 后续新增图示继续统一使用 `mermaid`，不要混用 ASCII 和其他格式。
