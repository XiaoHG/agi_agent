# 书稿参考标准总结

更新日期：2026-08-17

## 1. 目的

`publish/reference-examples/README.md` 目前已经列出了书单、开放书稿和学习资料，但还缺一层“如何真正用于写书”的统一规范。

这份文件把当前已经收集到的参考资料，整理成后续书稿默认执行的写作标准。

## 2. 参考资料如何分类使用

### 2.1 开放书稿与公开样章

当前已保存的重点资料包括：

- `open-books/ai-agent-book-github-readme.md`
- `open-books/ai-agents-in-depth-home.html`
- `open-books/ai-agents-in-depth-introduction.html`
- `published-books/think-python-2e.pdf`
- `published-books/think-data-structures.pdf`
- `published-books/aosa-volume1-introduction.html`
- `published-books/aosa-volume1-hdfs.html`

这类资料主要用于参考：

- 全书学习路径如何设计
- 单章如何安排概念、代码、实验和案例
- 如何把真实工程系统写成可学习内容

### 2.2 出版规范与发布流程

当前已保存的重点资料包括：

- `publishing-standards/self-publishing-guide-bccampus.html`
- `publishing-standards/pressbooks-guide-bccampus.html`
- `publishing-standards/print-on-demand-guide-bccampus.pdf`
- `publishing-standards/leanpub-manual-about.html`

这类资料主要用于参考：

- 稳定的章节组织方式
- Git 驱动的持续写作与修订方式
- 发布前的结构、排版和流程要求

### 2.3 官方框架与课程资料

当前已保存的重点资料包括：

- `framework-docs/langgraph-overview.html`
- `framework-docs/autogen-docs-home.html`
- `framework-docs/autogen-microsoft-research.html`
- `framework-docs/crewai-docs-home.html`
- `framework-docs/huggingface-agents-course-intro.html`
- `framework-docs/dlai-autogen-course.html`

这类资料主要用于参考：

- 当前 Agent 工程主流术语与表达
- 状态流、多智能体、工具调用、运行时编排等概念的行业语境
- 后续章节里涉及外部生态时的对照表达方式

## 3. 从资料中提炼出的统一写作标准

### 3.1 全书层标准

后续这本书必须同时满足四个要求：

1. 有稳定学习路径，而不是版本流水账。
2. 每章都能回到项目代码、版本文档和验证命令。
3. 每章都同时解释原理、工程边界和设计取舍。
4. 能随着项目后续版本持续增量修订，而不是每次推倒重写。

### 3.2 单章层标准

每一章默认应包含以下结构：

1. 本章目的
2. 本章要解决的问题
3. 读者完成本章后的收获
4. 项目中的真实链路
5. 关键代码入口
6. 版本演进脉络
7. 工程取舍与常见误区
8. 验证命令 / 测试 / 练习落点
9. 本章小结
10. 下一章衔接

### 3.3 工程案例层标准

后续章节统一采用以下展开方式：

`问题 -> 为什么旧方案不够 -> 新结构引入了什么边界 -> 代码如何体现 -> 如何验证 -> 下一阶段还缺什么`

这条标准来自当前参考资料中最值得保留的共同特征：

- AOSA 强调真实系统与架构取舍
- 开放 Agent 书稿强调学习路径和实验支撑
- LangGraph / AutoGen / CrewAI 官方资料强调运行时结构和协作边界

### 3.4 教学表达层标准

后续正文默认遵守：

- 概念解释尽量短，链路解释必须清楚
- 示例尽量基于真实代码入口，而不是凭空造例子
- 章节需要明确读者完成后能获得什么
- 复杂主题按单步到多步、单体到多体、静态到运行时逐层推进

### 3.5 发布流程层标准

后续书稿维护默认遵守：

- 正文、证据、修订、发布计划必须分开
- 每次结构性修改都要有修订记录
- 每次项目版本推进后，书稿也要同步修订
- 章节目录和主稿入口尽量保持稳定

## 4. 对当前书稿的直接影响

### 第 1 章

- 强化读者视角
- 增加代码与证据入口
- 明确“这不是版本堆叠，而是工程学习路径”

### 第 2 章

- 强化最小闭环的方法论意义
- 增加关键代码入口
- 增加验证与复盘落点

### 第 3 章及以后

- 不再先写松散初稿再返工
- 直接按本文件定义的章节结构落稿

## 5. 默认执行规则

从 2026-08-17 起，`publish/` 下的后续书稿工作默认遵守以下规则：

1. 写新章前先看本文件。
2. 写新章前先补对应 `research/chNN-evidence.md`。
3. 改正文后同步补 `revisions/`、`manuscript-status.md`、`current-book-summary.md`。
4. 项目后续版本推进时，同步更新书稿章节映射、证据索引和修订记录。
