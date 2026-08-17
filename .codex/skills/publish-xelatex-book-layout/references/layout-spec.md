# Layout Spec

This skill targets a Chinese technical book sample, not a plain report.

## Page model

- Page size: `185mm x 260mm`
- Left and right margins should remain visually symmetric for standalone chapter PDFs
- Chapter sample should feel like a trade technical book page, not office A4

## Typography

- Chinese body: Song style serif
- Chinese headings: sans / black style hierarchy
- Latin body: serif
- Monospace: stable code font
- Body text should prioritize readable line length and moderate leading

## Fixed expectations

- Chapter opening page uses a large chapter title
- Running pages use header + page number
- Figures use centered image + caption
- Code blocks use a light background box
- Inline code stays monospace and must not break XeLaTeX compilation

## QA focus

- No duplicated chapter numbering
- Standalone chapter PDFs must preserve the source chapter number, not reset to "第1章"
- No broken inline code
- No clipped figures
- No text overflow beyond page bounds
- No oversized blank areas around figures
- Header style and page number placement remain consistent
