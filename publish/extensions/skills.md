# 推荐 Skills

## 已落地

### publish-xelatex-book-layout

位置：

- `.codex/skills/publish-xelatex-book-layout/`

用途：

- 将 `publish/drafts/` 下的章节渲染为接近正式印刷样张的 XeLaTeX PDF
- 用章节目录内已准备好的 `.png` 图替代 Mermaid
- 统一章节页尺寸、字体、页眉、图注、代码块和页码样式

典型用法：

```bash
python .codex/skills/publish-xelatex-book-layout/scripts/build_chapter_pdf.py publish/drafts/ch01
```

## 1. book-outline skill

用途：

- 根据项目版本生成章节大纲
- 调整章节顺序和层级

## 2. chapter-draft skill

用途：

- 根据大纲和证据撰写章节初稿
- 保持术语统一和叙述风格一致

## 3. citation-audit skill

用途：

- 检查章节是否有事实依据
- 核对引用是否指向真实文件和版本

## 4. revision-control skill

用途：

- 管理草稿、修订记录和冻结版本
- 追踪章节变更原因

## 5. publication-schedule skill

用途：

- 维护章节排期
- 跟踪每次项目迭代对应的写作任务
