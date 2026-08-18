---
name: publish-xelatex-book-layout
description: Use when rendering chapters under publish/drafts/ into print-style Chinese technical book PDFs with XeLaTeX, especially when the formal manuscript is kept in chNN.md with Mermaid preserved in Markdown, enforcing consistent page geometry, typography, headers, captions, and chapter-level PDF QA.
---

# Publish XeLaTeX Book Layout

Use this skill when a chapter in `publish/drafts/` needs a polished PDF sample that looks like a real Chinese technical book chapter rather than a generic document export.

## When to use

- The user asks to export a chapter PDF from `publish/drafts/`
- The chapter contains Mermaid blocks that should remain in Markdown but be rendered for print
- The chapter contains prepared figure images that should be included directly
- The user asks for more professional printing, typography, or layout quality
- A chapter PDF needs repeatable regeneration after text edits

## Workflow

1. Read the target chapter directory and locate the formal manuscript markdown file
2. Confirm required local assets exist in the same chapter directory
3. Run `scripts/build_chapter_pdf.py <chapter_dir>`
4. If the manuscript contains Mermaid, let the builder render them into temporary high-resolution PNGs for print
5. If `pdftoppm` is available, render preview PNGs and visually inspect key pages
6. Fix layout issues in the chapter markdown or script parameters, then rebuild

## Rules

- Only touch the target chapter unless the user asks for a shared template change
- Keep the formal manuscript in `chNN.md`; `README.md` is only the directory note
- Keep Mermaid in the Markdown manuscript for editor readability; do not replace Mermaid in the source manuscript with PNG links unless the user explicitly asks for that conversion
- Prefer explicit image figures when the chapter intentionally references prepared local `.png` assets
- Keep output chapter-local by default: `chapter_dir/<chapter_name>.pdf`
- Treat `README.md` as a directory note, not the formal manuscript, when `chNN.md` exists
- Treat chapter title, page geometry, headers, captions, and code blocks as part of the skill contract
- Do not claim print quality until preview pages have been checked

## Script

Primary builder:

- `scripts/build_chapter_pdf.py`
- `scripts/render_mermaid_png.py`

Basic usage:

```bash
python .codex/skills/publish-xelatex-book-layout/scripts/build_chapter_pdf.py publish/drafts/ch01
```

Optional preview rendering:

```bash
python .codex/skills/publish-xelatex-book-layout/scripts/build_chapter_pdf.py publish/drafts/ch01 --preview-dir /tmp/ch01_preview
```

Standalone Mermaid rendering for printable figures:

```bash
python .codex/skills/publish-xelatex-book-layout/scripts/render_mermaid_png.py /tmp/figure.mmd --output-dir publish/drafts/ch01
```

## Layout standard

Read `references/layout-spec.md` before changing the script's typography or page design.
