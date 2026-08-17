# 当前书稿工作摘要

更新日期：2026-08-17

## 当前判断

当前书稿最核心的问题已经确认：此前的章节组织方式更接近“项目整理稿”而不是“专业 Agent 学习书籍”。

因此，当前工作重点已经从“继续扩写旧章节”切换为“先完成出版级总纲重设，再建立新的前置部分和正文章节骨架”。

此外，书稿的连续性机制已经正式落盘，后续不再依赖会话临时说明来维持写作标准。

## 为什么要重设

此前书稿存在三个结构性问题：

1. 缺少正式技术书应有的前置部分。
2. 正文第一章错误地从作者动机开始，而不是从读者需要的领域认知开始。
3. 项目版本顺序过度主导正文结构，导致全书更像项目演进说明，而不是学习书籍。

这些问题如果不先解决，后续继续写正文只会继续返工。

## 当前正式总纲状态

以下文件已经按“专业 Agent 学习书籍”标准重设：

- `publish/book-outline.md`
- `publish/chapter-map.md`
- `publish/book-structure-spec.md`
- `publish/manuscript-status.md`
- `publish/book-continuity-protocol.md`
- `publish/version-index.md`

并且以下主稿目录已经建立：

- `publish/drafts/front-01-book-introduction/README.md`
- `publish/drafts/front-02-author-preface/README.md`
- `publish/drafts/front-03-target-readers/README.md`
- `publish/drafts/front-04-how-to-use/README.md`
- `publish/drafts/front-05-project-background/README.md`
- `publish/drafts/prologue/README.md`
- `publish/drafts/ch01/README.md`
- `publish/drafts/ch02/README.md`
- `publish/drafts/ch03/README.md`
- `publish/drafts/ch04/README.md`

## 新的正式书稿结构

### 前置部分

- 书籍简介
- 作者序
- 本书面向谁
- 如何使用本书
- 项目背景与学习路线

### 正文部分

- 序章 为什么今天要系统学习 Agent 工程
- 第 1 章 什么是 Agent，为什么它不是聊天机器人
- 第 2 章 工业级 Agent 的基本结构
- 第 3 章 最小 Agent 执行闭环
- 第 4 章 状态、工作流与多步执行
- 第 5 章 知识增强：RAG 如何进入 Agent 主链路
- 第 6 章 工具边界：从本地工具到 MCP 协议
- 第 7 章 能力分层：Skills、Subagent 与角色协作
- 第 8 章 模型参与决策：tool calling 与 tool loop
- 第 9 章 结构化运行时：LangGraph 与图式编排
- 第 10 章 可观测性、评估与发布门禁
- 第 11 章 恢复机制：checkpoint、run history、replay
- 第 12 章 系统治理：registry、permission 与长期演进
- 第 13 章 从学习项目到专业 Agent 系统

### 附录部分

- 术语表
- 版本索引
- 练习与复盘索引
- 代码阅读索引

## 现有草稿的重定位结果

| 当前草稿 | 当前判断 | 新定位 |
| --- | --- | --- |
| `publish/drafts/front-02-author-preface/README.md` | 已承接旧“为什么要把这个项目写成一本书”的一部分作用 | 作为作者序继续修订 |
| `publish/drafts/front-05-project-background/README.md` | 已承接项目来源与学习路线说明 | 作为前置部分继续修订 |
| `publish/drafts/prologue/README.md` | 已承接“为什么要系统学习 Agent 工程”的过渡职责 | 作为序章继续扩写 |
| `publish/drafts/ch01/README.md` | 已写成正式正文并补入代码入口、版本定位与图示 | 继续精修引用与表达 |
| `publish/drafts/ch02/README.md` | 已写成正式正文并补入代码入口、版本定位与图示 | 继续精修结构与术语 |
| `publish/drafts/ch03/README.md` | 已形成正式正文并补入图示、代码入口与版本定位 | 继续精修证据与引用索引 |
| `publish/drafts/ch04/README.md` | 已形成正式正文并补入图示、代码入口与版本定位 | 继续精修承接与引用索引 |

## 当前最优先任务

1. 精修第 1 章的概念边界、引用索引和措辞稳定性。
2. 精修第 2 章的结构分层表达和术语一致性。
3. 为第 3 章补更完整的引用索引与证据链路。
4. 为第 4 章补更完整的引用索引，并为后续第 5 章建立承接。

## 已建立的连续性机制

从 2026-08-17 起，书稿工作必须固定遵守以下机制：

1. 先恢复结构，再进入正文。
2. 每章都要建立章节锚点，绑定版本、提交、预留标签、代码入口和验证命令。
3. 每次结构性修订都要同步更新主稿、版本索引、证据笔记、修订记录和当前摘要。
4. 后续新会话如果要处理书稿，必须先阅读：
   - `publish/current-book-summary.md`
   - `publish/book-structure-spec.md`
   - `publish/book-continuity-protocol.md`
   - `publish/chapter-map.md`
   - `publish/version-index.md`

## 恢复工作顺序

如果后续恢复书稿工作，建议按以下顺序进入：

1. 先看本文件，确认当前阶段已经进入“新总纲落地后的持续扩写”。
2. 再看 `publish/book-outline.md`，确认正式目录。
3. 再看 `publish/chapter-map.md`，确认版本和章节的关系。
4. 再看 `publish/book-structure-spec.md`，确认书籍结构标准。
5. 再看 `publish/book-continuity-protocol.md`，确认恢复顺序和同步规则。
6. 再看 `publish/version-index.md`，确认目标章节的代码锚点。
7. 再进入对应主稿目录继续写作。
