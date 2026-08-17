# 章节映射

更新日期：2026-08-17

## 映射原则

这份文件的作用不是把每个版本机械地塞进一章，而是把项目版本材料映射到正式书稿的知识结构中。

映射规则如下：

1. 章节是表达单位，版本是证据单位。
2. 同一主题的多个版本，应合并成一条连续叙述。
3. 章节顺序服从专业书籍的知识递进，而不是服从版本时间顺序。
4. 一个版本可以支撑多个章节中的不同小节。

## 正式书稿章节总览

### 前置部分

1. 书籍简介
2. 作者序
3. 本书面向谁
4. 如何使用本书
5. 项目背景与学习路线

### 正文部分

6. 序章 为什么今天要系统学习 Agent 工程
7. 第 1 章 什么是 Agent，为什么它不是聊天机器人
8. 第 2 章 工业级 Agent 的基本结构
9. 第 3 章 最小 Agent 执行闭环
10. 第 4 章 状态、工作流与多步执行
11. 第 5 章 知识增强：RAG 如何进入 Agent 主链路
12. 第 6 章 工具边界：从本地工具到 MCP 协议
13. 第 7 章 能力分层：Skills、Subagent 与角色协作
14. 第 8 章 模型参与决策：tool calling 与 tool loop
15. 第 9 章 结构化运行时：LangGraph 与图式编排
16. 第 10 章 可观测性、评估与发布门禁
17. 第 11 章 恢复机制：checkpoint、run history、replay
18. 第 12 章 系统治理：registry、permission 与长期演进
19. 第 13 章 从学习项目到专业 Agent 系统

## 版本映射

| 项目版本 | 书稿章节 | 映射主题 |
| --- | --- | --- |
| v01 | 第 3 章 | 最小执行闭环、路由、工具、统一输出 |
| v02 | 第 4 章 | 状态对象、工作流计划、多步执行 |
| v03 | 第 5 章 | 本地 RAG 最小闭环、知识进入执行主链路 |
| v04 | 第 6 章 | MCP 本地协议骨架、工具边界外化 |
| v05-v07 | 第 7 章 | Skills、Subagent、角色协作、学习工作台 |
| v08-v10 | 第 5、8 章 | 真实 LLM、RAG 强化、模型参与执行链路 |
| v11-v14 | 第 9 章 | 工具适配、LangGraph 接入、主链路结构化 |
| v15-v17 | 第 8 章 | tool calling、tool loop、final synthesis |
| v18-v21 | 第 6、7、10 章 | MCP/Skills tool loop、skill execution、trace |
| v22-v25 | 第 10 章 | skill node、failure recovery、runtime events |
| v26-v27 | 第 11 章 | checkpoint、run history、恢复能力 |
| v28-v31 | 第 12 章 | planner、registry、permission、专业化治理 |
| v32-v35 | 第 9、11、12 章 | graph runtime、workflow/tool_call/tool_loop 图式运行、可恢复演进 |
| v36+ | 第 10-13 章 | 后续工业化能力、评估、运行治理和系统收束 |

## 当前草稿重定位

| 当前草稿 | 新定位 | 说明 |
| --- | --- | --- |
| `publish/drafts/front-01-book-introduction/README.md` | 前置部分 | 书籍简介主稿 |
| `publish/drafts/front-02-author-preface/README.md` | 前置部分 | 作者序主稿 |
| `publish/drafts/front-03-target-readers/README.md` | 前置部分 | 目标读者主稿 |
| `publish/drafts/front-04-how-to-use/README.md` | 前置部分 | 阅读与学习方式主稿 |
| `publish/drafts/front-05-project-background/README.md` | 前置部分 | 项目背景与学习路线主稿 |
| `publish/drafts/prologue/README.md` | 序章 | 为什么今天要系统学习 Agent 工程 |
| `publish/drafts/ch01/README.md` | 第 1 章主稿 | Agent 概念边界与执行系统视角 |
| `publish/drafts/ch02/README.md` | 第 2 章主稿 | 工业级 Agent 的基本结构 |
| `publish/drafts/ch03/README.md` | 第 3 章主稿 | 最小 Agent 执行闭环 |
| `publish/drafts/ch04/README.md` | 第 4 章主稿 | 状态、工作流与多步执行 |

## 写作要求

- 每章都要能回到真实代码、版本文档、测试或练习
- 版本映射用于支撑事实，不用于决定正文标题
- 章节标题要面向读者学习目标，而不是面向项目内部命名
- 前置部分和正文部分必须严格区分，避免作者动机误占正文开头
