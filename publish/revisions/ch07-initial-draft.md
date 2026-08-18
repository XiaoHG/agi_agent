# ch07 初稿修订记录

日期：2026-08-18

## 本次完成内容

- 新建 `publish/drafts/ch07/README.md`
- 新建第 7 章正式正文 `publish/drafts/ch07/ch07.md`
- 新建证据笔记 `publish/research/ch07-evidence.md`
- 同步更新书稿状态文件，登记第 7 章已进入正式正文阶段
- 创建章节锚点标签 `book-ch07-anchor`，并把 tag 检出方式写回正文与索引

## 本章写作策略

1. 以 `v05-v07` 为主证据，不提前混入后续 runtime 章节的实现细节。
2. 先讲为什么“有工具仍然不够”，再解释 skill、subagent、collaboration plan 的层次差异。
3. 把 `agent/project.py` 放在章末作为应用层编排证据，避免把 `v07` 误写成基础运行时升级。
4. 继续保持 `ch03-ch06` 的章节结构：正文、代码入口、代码版本定位、阅读与验证指引。

## 后续可继续精修的点

- 为第 7 章补统一风格的 Mermaid 配图导出与 PDF 样张。
- 若后续真实 multi-agent runtime 章节继续落地，需要检查第 7 章与第 13 章之间的术语边界是否仍然清晰。
