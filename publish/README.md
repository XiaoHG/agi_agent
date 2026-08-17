# publish/

这里存放本项目学习过程沉淀出来的书稿材料、章节草案、研究笔记、修订记录、插图素材和发布计划。

## 目标

1. 把项目学习过程整理成一本可持续迭代的专业书。
2. 让书稿结构跟随项目版本演进，而不是临时拼接。
3. 为书稿建立专门的子 agent、技能和扩展能力。
4. 让写作流程具备研究、提纲、写作、审校、排期、发布的完整闭环。

## 目录约定

- `agent/`：书稿专属子 agent 定义。
- `research/`：资料、论据、引用和问题清单。
- `drafts/`：章节草稿，按 `chNN/README.md` 组织主稿。
- `revisions/`：审校意见、修改记录、差异说明。
- `assets/`：插图、表格、图示和封面素材。
- `extensions/`：为书稿 agent 设计的 skills、插件和能力清单。
- `chapter-map.md`：版本到章节的映射。
- `version-index.md`：章节锚点、版本、提交、标签与验证索引。
- `manuscript-status.md`：当前书稿状态。
- `current-book-summary.md`：当前书稿整体进度、恢复入口和下一步摘要。
- `book-structure-spec.md`：书稿完整结构规范，是后续长期执行标准。
- `book-continuity-protocol.md`：书稿连续性机制与新会话恢复标准。

## 工作原则

- 先结构，后正文。
- 先研究，后下笔。
- 先章节骨架，后段落扩写。
- 所有书稿变更都要可追溯到项目版本和证据来源。
- 写作节奏要和项目迭代同步，避免内容脱节。
- 后续新会话必须先按连续性机制恢复，再继续正文写作。

## 当前主稿入口

- 第 1 章：`publish/drafts/ch01/README.md`
- 第 2 章：`publish/drafts/ch02/README.md`
- 第 3 章：`publish/drafts/ch03/README.md`（待写）

## 恢复工作入口

- 优先查看：`publish/current-book-summary.md`
- 结构标准：`publish/book-structure-spec.md`
- 连续性机制：`publish/book-continuity-protocol.md`
- 章节锚点：`publish/version-index.md`
