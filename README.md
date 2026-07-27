# agi_agent

这是一个面向 Agent 开发学习的工作目录。目标不是只会调用模型接口，而是系统掌握 Agent 的核心机制、工程化能力和产品化落地方式。

本文档提供一套 6 周学习路线，适合希望全面学习 Agent 开发的人。默认节奏是每周投入 8-12 小时；如果你是全职投入，可以把每周内容压缩到 3-4 天。

## 学习目标

6 周结束后，应该具备以下能力：

- 理解 Agent 和普通聊天问答程序的区别
- 能设计一个带工具调用的单 Agent 系统
- 能实现多步任务执行、状态管理和记忆
- 能接入 MCP、RAG、Skills、Subagent 等常见能力
- 能读懂大型 Agent 项目的主链路
- 能独立完成一个小型 Agent 应用并进行基本评估

## 学习原则

- 读源码不超过 40%，至少 60% 时间用于自己动手
- 每周必须产出一个可运行成果，不能只做笔记
- 每周记录失败案例，重点分析为什么失败
- 先学核心链路，再学复杂工程细节
- 不追求一次学完所有框架，而是掌握可迁移的通用能力

## 项目目录结构

当前仓库定位为 Agent 工程学习工作台。目录按“能力模块 + 工程支撑 + 学习产出”拆分，避免把 Demo、提示词、评估和配置混在一起。

```text
agi_agent/
  AGENTS.md     # 仓库级 Agent 协作规则：Teacher Agent / Coding Agent 路由
  README.md
  agent/        # 单 Agent、任务循环、状态管理、工具调用主实验
  cli/          # 命令行入口、交互式运行脚本、开发调试入口
  mcp/          # MCP Server、MCP Client、工具协议集成实验
  rag/          # 文档加载、切分、embedding、检索、问答实验
  skills/       # 可复用技能模块：任务说明、流程、工具组合、示例
  subagent/     # 多 Agent 协作、任务拆分、角色分工实验
  prompts/      # system prompt、工具 prompt、评审 prompt、版本记录
  evals/        # 评估用例、评估脚本、评估报告
  tests/        # 自动化测试：单元测试、集成测试、回归测试
  examples/     # 可直接运行的示例输入、示例输出、演示任务
  docs/         # 架构图、学习笔记、设计文档、复盘记录
  configs/      # 模型、工具、检索、日志等配置模板
  scripts/      # 一次性脚本、数据准备脚本、开发辅助脚本
  data/         # 本地实验数据。大文件和私密数据不要提交
  logs/         # 本地运行日志。默认不提交
```

### 目录设计判断

原有目录 `agent/ mcp/ rag/ skills/ subagent/ cli/` 是合理的，覆盖了 Agent 学习中的核心能力。但它更像“能力分类”，缺少工程项目必需的支撑层：

- 缺少 `evals/`：Agent 项目不能只看单次效果，必须沉淀可复现评估。
- 缺少 `tests/`：工具函数、RAG pipeline、MCP client/server 都需要最小测试。
- 缺少 `prompts/`：提示词应该单独版本化，不建议散落在代码里。
- 缺少 `configs/`：模型名、温度、工具开关、检索参数不应硬编码。
- 缺少 `docs/`：学习型项目需要保留设计理由、失败案例和复盘。
- 缺少 `examples/`：每个阶段最好都有可直接运行的输入输出样例。

`prompt/` 已调整为 `prompts/`。原因是一个 Agent 项目通常会有多类 prompt，使用复数命名更符合工程语义。

### 推荐放置规则

- 阶段 Demo 放在对应能力目录下，例如 `docs/`、`examples/` 或独立实验目录。
- 跨模块综合项目可以放在 `examples/final-project/` 或独立新仓库。
- prompt 文件统一放到 `prompts/`，代码中通过路径或配置引用。
- 评估输入、期望输出、评估报告统一放到 `evals/`。
- 运行日志、缓存、向量库索引、本地私密数据不要提交到仓库。

## 默认协作 Agent

本项目长期配备两个默认协作 Agent，用于把“学习”和“工程实现”分开处理。

### Teacher Agent

位置：`subagent/teacher-agent/`

职责：

- 回答 Agent 开发相关问题
- 解释项目代码、架构和设计取舍
- 拆解学习路径和阶段目标
- 进行编程讲解、概念类比和源码导读
- 对学习成果做复盘和纠偏

默认触发场景：

- “解释一下……”
- “我为什么要这么设计？”
- “这个目录/模块/代码是什么意思？”
- “我应该怎么学？”
- “帮我复盘/总结/规划”

### Coding Agent

位置：`subagent/coding-agent/`

职责：

- 编写项目代码
- 修复 bug
- 补充测试
- 执行本地验证
- 做小范围重构
- 维护代码质量和工程边界

默认触发场景：

- “实现……”
- “修复……”
- “重构……”
- “加测试……”
- “跑一下/验证一下……”
- “把这个功能接起来”

### 协作规则

- 学习、解释、答疑、路线规划默认由 Teacher Agent 负责。
- 编码、修复、测试、验证默认由 Coding Agent 负责。
- 涉及“边学边写”的任务，先由 Teacher Agent 解释目标和设计，再由 Coding Agent 实现。
- 涉及代码评审时，Coding Agent 给出实现判断，Teacher Agent 补充学习角度的解释。
- 两个 Agent 都必须遵守项目目录规范、评估规范和安全边界。

## 当前可运行 Demo

当前已完成 Week 1 最小 CLI Agent、Week 2 状态与工作流、Week 3 本地 RAG / MCP、Week 4 Skills / Subagent，并开始 Week 5 工程化与评估。

运行直接回答：

```bash
python -m cli.main --input "Explain the difference between an agent and a chatbot."
```

运行文件读取：

```bash
python -m cli.main --input "Read README.md and summarize the project learning goals."
```

运行目录查看：

```bash
python -m cli.main --input "List the main project directories and explain what they are responsible for."
```

查看 trace：

```bash
python -m cli.main --input "Read README.md and summarize the project learning goals." --trace
```

搜索本地文档：

```bash
python -m cli.main --input "Search docs for workflow." --trace
```

运行 RAG demo：

```bash
python -m cli.rag_demo --question "What does workflow mean in this project?"
```

列出本地 MCP 工具：

```bash
python -m cli.mcp_demo --list-tools
```

通过 Agent 调用本地 MCP 工具：

```bash
python -m cli.main --input "List MCP tools." --trace
```

列出 Skills：

```bash
python -m cli.collaboration_demo --list-skills
```

规划 Subagent 协作：

```bash
python -m cli.main --input "Plan subagent collaboration for a code review." --trace
```

运行回归评估：

```bash
python -m cli.eval_runner
```

运行测试：

```bash
python -m unittest discover -s tests -v
```

## 六周总览

| 周次 | 主题 | 核心目标 | 主要产出 |
| --- | --- | --- | --- |
| 第 1 周 | Agent 基础 | 理解最小 Agent 闭环 | 一个最小 CLI Agent |
| 第 2 周 | 状态与工作流 | 学会多步任务执行 | 一个多步任务 Agent |
| 第 3 周 | RAG 与 MCP | 学会接知识和外部工具 | 一个带知识检索和外部工具的 Agent |
| 第 4 周 | Skills 与 Subagent | 学会模块化和协作式 Agent | 一个多角色协作 Demo |
| 第 5 周 | 工程化与评估 | 学会日志、测试、评估、容错 | 一套可复现评估用例 |
| 第 6 周 | 综合项目 | 独立完成一个 Agent 产品原型 | 一个完整项目 Demo |

## 第 1 周：Agent 基础

### 目标

理解 Agent 的最小工作闭环：

`用户输入 -> 模型决策 -> 工具调用 -> 工具结果回传 -> 最终回答`

### 学习内容

- 什么是 Agent，和普通聊天机器人有什么区别
- system prompt 的作用
- tool calling 的基本模式
- structured output 的价值
- 单轮上下文和短期记忆
- 日志与调试的最小实践

### 动手任务

在 `agent/` 目录下实现一个最小 CLI Agent，至少支持以下能力中的 2 个：

- 读取本地文件
- 执行 shell 命令
- 调用网页搜索
- 调用一个自定义函数工具

### 交付物

- 一个可运行的 `README` 或启动脚本
- 一份最小架构图
- 3 个测试输入和输出样例

### 验收标准

- 能解释 Agent 和普通 prompt app 的差异
- Agent 能根据任务选择不同工具
- 工具失败时不会直接崩溃，至少有错误提示

## 第 2 周：状态、记忆与工作流

### 目标

让 Agent 从“一次性回答”升级为“能分步骤完成任务”。

### 学习内容

- state 和 workflow 的基本概念
- 任务拆解与 step loop
- retry、fallback、reflection
- 短期记忆和长期记忆的区别
- 会话状态持久化

### 动手任务

在 `agent/` 目录下扩展第 1 周项目，让 Agent 能执行多步任务，例如：

- 先搜索资料
- 再提取要点
- 再生成总结
- 再输出待办事项

### 推荐练习题

- “帮我调研一个技术主题并生成 5 条结论”
- “帮我读取一个目录下的文档并整理摘要”
- “先检查信息，再决定是否执行命令”

### 交付物

- 在 `agent/` 中扩展状态和工作流模块
- 一个状态流转图
- 5 个失败案例记录
- 一份你自己总结的“什么时候需要工作流”的笔记

### 验收标准

- Agent 支持至少 3 步串行执行
- 中间结果可被后续步骤使用
- 对失败场景有 retry 或中断逻辑

## 第 3 周：RAG 与 MCP

### 目标

让 Agent 同时具备“知识访问能力”和“外部工具接入能力”。

### 学习内容

#### RAG

- 文档切分
- embedding 和向量检索
- 检索召回与上下文拼接
- RAG 常见问题：召回不准、上下文污染、答案幻觉

#### MCP

- MCP 的定位和作用
- MCP Client / Server 的基本结构
- 把外部工具通过统一协议暴露给 Agent
- 如何设计稳定的工具输入输出

### 动手任务

在对应目录中完成两个小实验：

- `rag/`：做一个本地文档问答 Demo
- `mcp/`：接一个简单 MCP Server，例如文件、搜索、数据库或自定义工具

然后把两者接入你的 Agent，让它能：

- 针对知识问题先检索文档
- 针对操作问题调用 MCP 工具

### 交付物

- 在 `rag/` 中实现本地文档问答能力
- 在 `mcp/` 中实现 MCP 接入能力
- 一个统一入口的 Agent Demo
- 一份“什么时候该用 RAG，什么时候该直接用工具”的总结

### 验收标准

- Agent 能根据问题类型选择 RAG 或工具
- 至少接通一个 MCP 工具
- 能清楚说明检索质量问题出现在哪里

## 第 4 周：Skills 与 Subagent

### 目标

学习如何把 Agent 做成可复用、可拆分、可协作的系统。

### 学习内容

#### Skills

- 什么是 Skill
- 如何封装常用任务
- 如何把 prompt、工具和流程组合成复用模块

#### Subagent

- 什么情况下需要多 Agent
- 任务拆分与角色设计
- Planner / Researcher / Executor / Reviewer 常见角色
- 多 Agent 的成本与收益

### 动手任务

在 `skills/` 和 `subagent/` 中完成以下内容：

- 封装 2-3 个可复用 Skills
- 做一个多角色协作 Demo，例如：
  - Planner 负责拆解任务
  - Researcher 负责找资料
  - Writer 负责写结果
  - Reviewer 负责检查问题

### 推荐练习题

- 写一份技术调研报告
- 为一个需求文档生成开发任务拆解
- 对一个代码仓库生成模块分析报告

### 交付物

- 在 `skills/` 中沉淀可复用技能
- 在 `subagent/` 中实现多 Agent 协作实验
- `subagent/teacher-agent/`
- `subagent/coding-agent/`
- 一份多 Agent 协作流程图
- 一份“什么时候不该用多 Agent”的反思笔记

### 验收标准

- 至少有 2 个 Skill 被多个任务复用
- Subagent 分工明确，不只是换个 prompt 重复调用
- 你能说清楚单 Agent 和多 Agent 的权衡

## 第 5 周：工程化、评估与稳定性

### 目标

把 Demo 升级成更接近真实可维护系统的 Agent。

### 学习内容

- 日志、trace、步骤记录
- prompt 版本管理
- 工具超时、重试、熔断
- 权限边界与安全控制
- eval case 设计
- 人工 review 和自动评估

### 动手任务

给前几周的 Agent 补上工程化能力：

- 增加结构化日志
- 增加至少 10 个 eval case
- 对工具调用增加超时和错误分类
- 增加简单权限控制，例如限制危险命令

### 交付物

- `evals/` 中的阶段性评估用例
- `agent/` 中的日志、trace、错误处理能力
- `tests/` 中的回归测试
- 一份评估报告
- 一份问题清单，列出最容易失败的 5 类场景

### 验收标准

- 能稳定复现评估结果
- 能区分 prompt 问题、检索问题、工具问题、流程问题
- 出错时日志足够定位问题

## 第 6 周：综合项目

### 目标

独立完成一个完整的 Agent 原型项目。

### 选题建议

可以从下面选一个，也可以自拟：

- 研究助理 Agent
- 代码库分析 Agent
- 个人知识库问答 Agent
- 自动化办公 Agent
- 多步骤信息采集与总结 Agent

### 强制要求

项目至少要包含：

- 2 个以上工具
- RAG 或 MCP 至少 1 项
- 至少 1 个 Skill
- 至少 1 个 Subagent 或明确说明为什么不需要
- 评估样例
- 日志和错误处理

### 推荐项目结构

```text
project/
  README.md
  agent/
  cli/
  mcp/
  rag/
  skills/
  subagent/
  prompts/
  evals/
  tests/
  configs/
  examples/
  docs/
```

### 交付物

- 一个完整可运行项目
- 项目介绍文档
- 运行说明
- 5 个真实示例
- 已知限制与下一步计划

### 验收标准

- 陌生人能按 README 跑起来
- 能稳定完成一类明确任务
- 你能讲清系统设计而不只是展示效果

## 每周固定复盘模板

每周结束时，建议写一份简短复盘，至少回答下面这些问题：

1. 这周我做成了什么？
2. 这周我的 Agent 最常失败在哪？
3. 这些失败分别属于 prompt、工具、检索、状态还是架构问题？
4. 我为了修复失败做了什么？
5. 下周我最应该加强哪一项能力？

## 推荐学习顺序

如果你还想结合大型开源项目源码一起学，建议顺序如下：

1. 先用自己的小 Demo 学基础
2. 再学习 LangGraph 这类工作流/状态编排框架
3. 再学习 OpenHands 这类代码型 Agent
4. 再深入 OpenClaw 这种产品化、多渠道 Agent 系统

这样效率比一开始就硬啃超大项目更高。

## 和 OpenClaw 的结合方式

如果你准备继续学习 `openclaw/openclaw`，建议把它放在第 4-6 周穿插学习，重点关注这些模块：

- `gateway`
- `agents`
- `channels`
- `memory`
- `plugins`
- `web`

不建议第一阶段追求读完所有渠道、所有平台端和所有边缘功能。先吃透主链路更重要。

## 最终成果定义

完成这 6 周后，理想状态不是“看过很多概念”，而是你已经拥有：

- 一个自己的 Agent 实验仓库
- 至少 4 个阶段性 Demo
- 一套评估和复盘方法
- 一份可以继续演进成真实项目的综合 Agent 原型

## 下一步

可以继续在这个仓库中按周推进：

- 当前阶段先巩固 Week 5：工程化、评估、稳定性
- 第 6 周把所有内容整合成一个完整项目

当前建议优先做下面三件事：

1. 先理解当前 eval runner：`evals/runner.py`、`evals/regression_cases.json`、`cli/eval_runner.py`。
2. 补 Week 5 工程化复盘，记录 eval、trace、稳定性边界。
3. 再评估是否进入 Week 6：综合项目。
