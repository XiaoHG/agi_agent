# 书稿连续性机制

更新日期：2026-08-17

## 1. 机制目标

这份文件用于把书稿的长期写作机制固化到仓库中，避免后续新会话把书稿重新退回为“临时整理稿”或“零散章节补写”。

从本文件建立起，`publish/` 的所有后续工作都必须遵守以下目标：

1. 这本书是一本专业 Agent 学习书籍，而不是项目流水账。
2. 每个章节都必须同时连接正文、项目版本、代码入口、验证命令和修订记录。
3. 每次继续书稿工作时，都必须先恢复结构上下文，再进入正文撰写。
4. 后续章节新增、改写、补图、补代码引用时，都必须同步更新本机制相关文件。
5. 章节进入样张输出阶段后，必须固定通过 `publish-xelatex-book-layout` skill 生成章节级 PDF，不再采用临时导出方式。

## 2. 新会话恢复顺序

任何后续会话只要开始处理书稿，必须先按下面顺序恢复：

1. 阅读 `publish/current-book-summary.md`
2. 阅读 `publish/book-structure-spec.md`
3. 阅读 `publish/book-continuity-protocol.md`
4. 阅读 `publish/chapter-map.md`
5. 阅读 `publish/version-index.md`
6. 再进入目标章节主稿和对应研究材料

如果没有完成这六步，不应直接续写正文。

## 3. 章节与代码绑定机制

从现在开始，每个正式章节都必须建立“章节锚点”。

章节锚点至少包含以下信息：

1. 章节编号与标题
2. 主锚点版本
3. 主锚点标签名
4. 标签状态
5. 推荐检出命令
6. 推荐阅读代码文件
7. 最小验证命令
8. 补充支撑版本

这些信息统一记录在 `publish/version-index.md` 中。

## 4. 标签命名规范

为了让后续读者可以按章节切换代码状态，后续应逐步为章节锚点建立稳定标签。

统一命名规则：

- `book-ch01-anchor`
- `book-ch02-anchor`
- `book-ch03-anchor`
- `book-ch04-anchor`

如果某章后续需要多个锚点，可继续扩展：

- `book-ch05-anchor-a`
- `book-ch05-anchor-b`

在标签尚未创建前，正文和索引必须直接使用预留标签名来表达，并明确标记“待创建”，不再使用任何提交编号表达。

## 5. 每章必须同步的五个位置

每次新增章节或对现有章节进行结构性修订时，至少同步更新以下五个位置：

1. `publish/drafts/chNN/README.md`
2. `publish/version-index.md`
3. `publish/research/chNN-evidence.md` 或对应证据文件
4. `publish/revisions/chNN-*.md`
5. `publish/current-book-summary.md`

如果章节定位发生变化，还必须同步更新：

6. `publish/chapter-map.md`
7. `publish/book-structure-spec.md`

## 6. 正文章节强制新增的小节

从第 1 章起，后续每个正文章节都应逐步具备以下固定小节：

1. 本章代码入口
2. 代码版本定位
3. 本章阅读与验证指引

其中“代码版本定位”至少要说明：

- 推荐切换到哪个标签
- 为什么选择这个代码状态
- 读者切换后先看哪些文件

## 7. 写作与证据边界

为了防止后续书稿再次偏离，继续写作时必须遵守以下边界：

1. 不能把项目版本说明直接改写成正文，必须先转化为面向读者的知识表达。
2. 不能只写概念，不给代码入口。
3. 不能只写代码，不给结构解释。
4. 不能只给正文，不补索引与修订记录。
5. 技术结论必须能追溯到项目代码、版本文档、测试、练习或验证命令。
6. 打印稿排版必须能追溯到固定命令和固定 skill，而不是一次性的手工步骤。

## 8. 后续章节扩展规则

书稿仍处于持续扩展阶段，因此这套机制必须对后续章节保持兼容。

后续新增章节时，统一按下列步骤推进：

1. 在 `publish/book-outline.md` 确认章节职责
2. 在 `publish/chapter-map.md` 补版本映射
3. 在 `publish/version-index.md` 建立章节锚点
4. 在 `publish/drafts/chNN/README.md` 建立主稿
5. 在 `publish/research/` 建立证据笔记
6. 在 `publish/revisions/` 建立修订记录
7. 在 `publish/current-book-summary.md` 更新当前进度与下一步

如果新增章节已经进入排版阶段，还必须继续执行：

8. 准备章节目录内的静态配图资源
9. 使用 `publish-xelatex-book-layout` 生成 `chapter_dir/<chapter_name>.pdf`
10. 输出预览页并进行排版检查

## 9. 对 Publishing Agent 的约束

后续任何负责书稿的 agent，在开始工作时必须先确认：

1. 当前任务属于前置部分、正文还是附录
2. 当前章节是否已有正式标签或预留标签
3. 当前章节的证据文件是否完整
4. 当前章节是否已写入代码入口和验证指引
5. 当前章节是否需要进入 XeLaTeX 样张输出阶段
6. 如果需要，是否已经按固定 skill 生成 PDF 与预览页

如果其中任一项缺失，优先补机制，再补正文。
