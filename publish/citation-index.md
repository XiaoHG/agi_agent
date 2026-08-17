# 引用索引

更新日期：2026-08-17

## 用途

这份文件用于记录书稿正文的事实来源、章节级证据入口和参考资料落点。

规则：

- 正文中的关键判断应尽量能回到这里找到依据。
- 项目代码、版本文档、测试、练习和参考资料应区分记录。
- 每次新增或重写章节后，都要同步补这里的章节引用条目。

## 第 1 章 什么是 Agent，为什么它不是聊天机器人

### 项目证据

- `agent/router.py`
  用途：支撑“Agent 不只是回答，而是先做路由判断”的论述。

- `agent/core.py`
  用途：支撑“系统围绕统一执行主线组织动作，而不是只生成文本”的论述。

- `cli/main.py`
  用途：支撑“项目入口已经面向执行系统，而不是单纯聊天界面”的论述。

- `versions/v01_minimal-cli-agent.md`
  用途：支撑“最小闭环是项目最初能力边界”的论述。

- `docs/current-learning-state.md`
  用途：支撑“项目已从最小 Agent 演进到更完整工业级主干”的背景判断。

### 参考资料

- `publish/reference-examples/framework-docs/langgraph-overview.html`
  用途：参考当前主流 Agent / graph runtime 生态中的结构化表达方式。

- `publish/reference-examples/framework-docs/autogen-docs-home.html`
  用途：参考主流 Agent 框架如何定义 agent-oriented execution。

- `publish/reference-examples/open-books/ai-agents-in-depth-introduction.html`
  用途：参考开放 Agent 书稿在概念引入阶段的叙述方式。

### 本章关键对应关系

- “Agent 不只是会说话，而是能围绕目标组织执行”
  对应：`agent/router.py`、`agent/core.py`

- “模型加工具不自动等于 Agent”
  对应：`agent/core.py`、`versions/v01_minimal-cli-agent.md`

- “项目起点已经与普通聊天程序分开”
  对应：`versions/v01_minimal-cli-agent.md`、`cli/main.py`

## 第 2 章 工业级 Agent 的基本结构

### 项目证据

- `agent/core.py`
  用途：支撑“统一执行面”和“分支执行路径”的论述。

- `agent/router.py`
  用途：支撑“路由与决策边界”的论述。

- `cli/main.py`
  用途：支撑“系统入口已经具备 runtime / replay / resume / policy 这些工业化入口”的论述。

- `tests/test_agent.py`
  用途：支撑“结构边界从早期就进入回归验证”的论述。

- `versions/v01_minimal-cli-agent.md`
  用途：支撑最小执行骨架的起点说明。

- `versions/v02_state-workflow.md`
  用途：支撑状态与工作流作为下一层结构进入系统的论述。

- `versions/v03_rag-local-search.md`
  用途：支撑知识增强进入系统边界的论述。

- `versions/v04_mcp-local-protocol.md`
  用途：支撑工具协议边界逐步外化的论述。

### 参考资料

- `publish/reference-examples/published-books/aosa-volume1-introduction.html`
  用途：参考工程书如何引入系统结构和架构视角。

- `publish/reference-examples/published-books/aosa-volume1-hdfs.html`
  用途：参考复杂系统章节如何围绕结构边界展开案例。

- `publish/reference-examples/framework-docs/langgraph-overview.html`
  用途：参考结构化 runtime 与 graph orchestration 的现代表达方式。

### 本章关键对应关系

- “工业级 Agent 的关键不是功能多，而是边界清楚”
  对应：`agent/core.py`、`agent/router.py`

- “状态、知识、协议、协作和治理都必须回到同一个系统结构”
  对应：`versions/v02_state-workflow.md`、`versions/v03_rag-local-search.md`、`versions/v04_mcp-local-protocol.md`

- “结构边界从早期就应进入测试和验证”
  对应：`tests/test_agent.py`

## 第 3 章 最小 Agent 执行闭环

### 项目证据

- `cli/main.py`
  用途：支撑“最小闭环从入口层就已建立”的论述。

- `agent/router.py`
  用途：支撑“最早的系统边界是路由判断”的论述。

- `agent/core.py`
  用途：支撑“统一执行主线”和“执行分支收束”的论述。

- `tests/test_agent.py`
  用途：支撑“最小闭环从一开始就进入回归验证”的论述。

- `versions/v01_minimal-cli-agent.md`
  用途：支撑“v01 的核心目标是打通最小闭环”的论述。

### 参考资料

- `publish/reference-examples/published-books/think-python-2e.pdf`
  用途：参考技术书如何把基础执行链路讲清楚。

- `publish/reference-examples/published-books/aosa-volume1-introduction.html`
  用途：参考工程系统章节如何从简单骨架进入更复杂结构。

### 本章关键对应关系

- “最小闭环的意义不是功能多少，而是主线是否成立”
  对应：`versions/v01_minimal-cli-agent.md`、`agent/core.py`

- “路由、执行和输出边界必须尽早分开”
  对应：`agent/router.py`、`agent/core.py`

- “测试是闭环护栏的一部分”
  对应：`tests/test_agent.py`

## 第 4 章 状态、工作流与多步执行

### 项目证据

- `agent/state.py`
  用途：支撑“状态对象作为运行中间信息正式容器”的论述。

- `agent/workflow.py`
  用途：支撑“WorkflowPlan 把目标变成多步过程”的论述。

- `agent/core.py`
  用途：支撑“workflow 分支如何进入主执行链路”的论述。

- `tests/test_agent.py`
  用途：支撑“多步执行从一开始就进入测试验证”的论述。

- `versions/v02_state-workflow.md`
  用途：支撑“v02 是最小闭环上的第一次结构升级”的论述。

- `docs/v02_state-workflow-exercises.md`
  用途：支撑学习与复盘落点。

### 参考资料

- `publish/reference-examples/published-books/aosa-volume1-hdfs.html`
  用途：参考复杂系统章节如何解释结构升级带来的组织变化。

- `publish/reference-examples/framework-docs/langgraph-overview.html`
  用途：参考状态驱动与结构化执行在现代 Agent runtime 里的表达方式。

### 本章关键对应关系

- “单步闭环不足以支撑复杂任务”
  对应：`versions/v02_state-workflow.md`、`agent/core.py`

- “AgentState 是后续 many-step execution 的基础容器”
  对应：`agent/state.py`

- “WorkflowPlan 代表系统从执行一个动作走向管理一段过程”
  对应：`agent/workflow.py`

## 使用规则

- 如果正文某个判断无法回到这里找到依据，应补证据后再定稿。
- 如果引用了外部参考资料，应同时在本索引和对应章节研究笔记中记录。
