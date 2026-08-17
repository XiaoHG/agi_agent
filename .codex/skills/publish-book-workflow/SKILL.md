---
name: publish-book-workflow
version: v1
description: Book writing workflow for the project publication track. Use when organizing, drafting, revising, or scheduling the book version of the project learning process under publish/.
---

# Publish Book Workflow

## Overview

Use this skill to turn the project learning process into a structured book-writing workflow. Focus on evidence-backed chapter planning, consistent terminology, and iterative publication quality.

## Workflow

1. Read the relevant `publish/` materials and the current project version docs.
2. Identify the book chapter being updated.
3. Extract factual material from version notes, docs, tests, evals, and traces.
4. Draft or revise the chapter in `publish/drafts/`.
5. If the task includes PDF sample output, print-quality layout adjustment, or chapter figure replacement, switch to `publish-xelatex-book-layout` after the markdown draft is stable.
6. Render the chapter-local PDF and preview pages, then use the preview result as the layout QA baseline.
7. Record open questions and citation gaps in `publish/research/`.
8. Log revision notes in `publish/revisions/`.
9. Keep the schedule aligned with project iteration cadence.

## Rules

- Do not invent technical details.
- Prefer project evidence over generic book-writing advice.
- Keep chapter structure stable across iterations.
- Separate research, draft, revision, and release materials.
- Use concise, professional language suitable for publication.
- Treat markdown draft and PDF sample as two linked deliverables: content first, layout second.
- When chapter images already exist, prefer static `.png` figures over inline Mermaid in the printable draft.
- Do not claim a chapter has reached print-quality layout until the XeLaTeX PDF and preview pages have been checked.

## Output expectations

- chapter outline
- draft text
- citation checklist
- revision notes
- next writing action
- optional chapter-local PDF sample and preview images

## Skill handoff

Use `publish-xelatex-book-layout` when any of the following is true:

- the user asks to export or regenerate a chapter PDF
- the chapter needs professional Chinese book typography rather than plain markdown export
- Mermaid content has already been replaced with prepared chapter images
- the writing task has reached a "content stable, layout review" stage
