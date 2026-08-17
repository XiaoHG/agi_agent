---
name: publish-xelatex-book-layout
description: Use when rendering chapters under publish/drafts/ into print-style Chinese technical book PDFs with XeLaTeX, especially when replacing Mermaid with prepared images, enforcing consistent page geometry, typography, headers, captions, and chapter-level PDF QA.
---

# Publish XeLaTeX Book Layout

Use this skill when a chapter in `publish/drafts/` needs a polished PDF sample that looks like a real Chinese technical book chapter rather than a generic document export.

## When to use

- The user asks to export a chapter PDF from `publish/drafts/`
- The chapter contains prepared figure images that should replace Mermaid blocks
- The user asks for more professional printing, typography, or layout quality
- A chapter PDF needs repeatable regeneration after text edits

## Workflow

1. Read the target chapter `README.md`
2. Confirm required local assets exist in the same chapter directory
3. Run `scripts/build_chapter_pdf.py <chapter_dir>`
4. If Mermaid figures must be converted for print, render them as high-resolution PNGs with `scripts/render_mermaid_png.py`
5. If `pdftoppm` is available, render preview PNGs and visually inspect key pages
6. Fix layout issues in the chapter markdown or script parameters, then rebuild

## Rules

- Only touch the target chapter unless the user asks for a shared template change
- Prefer image figures over inline Mermaid when the user already prepared `.png` assets
- Keep output chapter-local by default: `chapter_dir/<chapter_name>.pdf`
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

High-resolution Mermaid rendering for printable figures:

```bash
python .codex/skills/publish-xelatex-book-layout/scripts/render_mermaid_png.py /tmp/figure.mmd --output-dir publish/drafts/ch01
```

## Layout standard

Read `references/layout-spec.md` before changing the script's typography or page design.
