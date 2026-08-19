# 章节版本边界与索引回修记录

日期：2026-08-18

## 本次回修范围

- `publish/drafts/ch01/ch01.md`
- `publish/drafts/ch02/ch02.md`
- `publish/drafts/ch03/ch03.md`
- `publish/drafts/ch04/ch04.md`
- `publish/drafts/ch05/ch05.md`
- `publish/drafts/ch06/ch06.md`
- `publish/drafts/ch07/ch07.md`
- `publish/editorial-workflow.md`

## 本次回修目标

1. 给正文中出现的明确版本号补上可查阅的版本资料索引。
2. 修正低版本章节中混入高版本结构的问题。
3. 把章节学习入口统一收束到版本索引、版本文档和稳定标签三类可追溯入口。
4. 删除已生成的章节 PDF，暂时只保留 Markdown 正文与配图素材。

## 关键处理

### 1. 统一补入版本资料索引

在各章 `代码版本定位` 小节中补入：

- `publish/version-index.md`
- `versions/` 目录下的对应正式版本文档

这样读者在看到 `v01`、`v03`、`v07` 等版本号时，可以直接回到确定材料，不再依赖会话说明。

### 2. 回修低版本章节的越界内容

- 第 5 章不再把后续向量索引、LLM RAG、图式运行时等高版本内容写成当前章主体。
- 第 7 章不再把 `SubagentTaskContract`、`SubagentHandoffRecord`、`SubagentReturnRecord`、`SubagentExecutionRecord`、`SubagentRuntimeSession` 等后期结构写成当前连续版本区间的主体内容。

### 3. 删除 PDF 输出物

已删除：

- `publish/drafts/ch01/ch01.pdf`
- `publish/drafts/ch02/ch02.pdf`
- `publish/drafts/ch03/ch03.pdf`
- `publish/drafts/ch04/ch04.pdf`

## 后续要求

1. 后续章节如果出现版本号，必须同步给出确定索引。
2. 后续低版本章节不得再直接吸收高版本结构作为主体讲解。
3. 在正文边界没有修正前，不再进入新的 PDF 排版输出。
