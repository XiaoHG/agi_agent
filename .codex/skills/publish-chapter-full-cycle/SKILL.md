---
name: publish-chapter-full-cycle
description: Use when building or revising a `publish/drafts/chNN/` chapter from scratch into a complete formal chapter, including chapter README, `chNN.md`正文, code-version定位, evidence, revision notes, and handoff to XeLaTeX layout when stable.
---

# Publish Chapter Full Cycle

Use this skill when a chapter must be taken from initial plan to polished正文.

## When to use

- The user wants to start a new chapter from project/version evidence
- The user wants to turn a chapter plan into a formal manuscript
- The user wants the chapter structure aligned with the rest of the book
- The user wants the chapter to end in a layout-ready state

## Workflow

1. Read `publish/current-book-summary.md`, `publish/chapter-map.md`, `publish/version-index.md`, and the relevant project version docs.
2. Identify the chapter number, learning goal, and code anchor.
3. Create or update the chapter directory:
   - `README.md` for plan, notes, and writing reminders
   - `chNN.md` for formal正文
4. Write the chapter正文 in `chNN.md` with the same chapter shape used across the book:
   - opening problem
   - conceptual boundary
   - project evidence
   - code entry points
   - engineering tradeoffs
   - code-version定位
   - reading and validation guide
5. Keep Mermaid in the Markdown正文 unless the user explicitly asks for print replacement.
6. Record evidence gaps in `publish/research/chNN-evidence.md`.
7. Record structural changes in `publish/revisions/chNN-*.md`.
8. Update `publish/chapter-map.md`, `publish/version-index.md`, and `publish/current-book-summary.md` when the chapter status changes.
9. When the chapter becomes content-stable, create or refresh the chapter anchor git tag (for example `book-ch07-anchor`) at the intended reading commit, then sync that tag into `publish/version-index.md` and the chapter's `代码版本定位` section.
10. When the chapter is content-stable, hand off to `publish-xelatex-book-layout` for PDF sample generation and preview QA.

## Rules

- Do not leave 草稿语气 in the formal正文.
- Do not put planning bullets or status placeholders inside the正文.
- The `代码版本定位` section must include the actual chapter anchor tag once it exists, not a placeholder.
- Use `README.md` for chapter planning, not for formal prose.
- Use `chNN.md` as the only formal chapter manuscript file.
- Keep the chapter style consistent with existing chapters.
- Do not claim the chapter is publish-ready until PDF preview QA is done.
- If a stable chapter is delivered without creating or syncing its chapter tag, the workflow is incomplete.

## Output

- chapter README update
- chapter正文 draft
- evidence note
- revision note
- version and status updates
- layout handoff, if needed
