#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def esc_text(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def fmt_inline(text: str) -> str:
    parts = re.split(r"(`[^`]+`)", text)
    out: list[str] = []
    for part in parts:
        if part.startswith("`") and part.endswith("`"):
            out.append(r"\inlinecode{" + part[1:-1] + "}")
        else:
            out.append(esc_text(part))
    return "".join(out)


def figure_block(chapter_dir: Path, rel_path: str, caption: str) -> str:
    abs_path = (chapter_dir / rel_path).resolve().as_posix()
    if not Path(abs_path).exists():
        raise FileNotFoundError(f"Missing figure asset: {abs_path}")
    return figure_from_path(Path(abs_path), caption)


def figure_from_path(image_path: Path, caption: str) -> str:
    abs_path = image_path.resolve().as_posix()
    return "\n".join(
        [
            r"\begin{figure}[htbp]",
            r"  \centering",
            rf"  \includegraphics[width=0.96\textwidth,height=0.34\textheight,keepaspectratio]{{{abs_path}}}",
            rf"  \caption{{{esc_text(caption)}}}",
            r"\end{figure}",
        ]
    )


def render_mermaid_block(mermaid_text: str, output_dir: Path) -> Path:
    if not shutil.which("npx"):
        raise RuntimeError("Missing `npx`; install Node.js tooling first.")
    output_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(mermaid_text.encode("utf-8")).hexdigest()[:12]
    source = output_dir / f"mermaid-{digest}.mmd"
    output = output_dir / f"mermaid-{digest}.png"
    source.write_text(mermaid_text, encoding="utf-8")
    cmd = [
        "npx",
        "-y",
        "@mermaid-js/mermaid-cli",
        "-i",
        str(source),
        "-o",
        str(output),
        "-s",
        "4",
        "-w",
        "2400",
        "-b",
        "white",
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return output


def resolve_manuscript_path(chapter_dir: Path) -> Path:
    candidates = sorted(
        path
        for path in chapter_dir.glob("*.md")
        if path.name != "README.md"
    )
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        fallback = chapter_dir / "README.md"
        if fallback.exists():
            return fallback
        raise FileNotFoundError(f"Missing chapter manuscript in {chapter_dir}")
    raise ValueError(
        f"Expected exactly one non-README markdown manuscript in {chapter_dir}, found: "
        + ", ".join(path.name for path in candidates)
    )


def parse_markdown(md_path: Path, mermaid_dir: Path) -> tuple[int | None, str, str]:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    body: list[str] = []
    paragraph_buf: list[str] = []
    list_buf: list[str] = []
    code_buf: list[str] = []
    code_kind: str | None = None
    list_kind: str | None = None
    in_code = False
    chapter_title_full: str | None = None

    def flush_paragraph() -> None:
        nonlocal paragraph_buf
        if paragraph_buf:
            text = " ".join(x.strip() for x in paragraph_buf).strip()
            if text:
                body.append(fmt_inline(text))
                body.append("")
            paragraph_buf = []

    def flush_list() -> None:
        nonlocal list_buf, list_kind
        if list_buf:
            env = "enumerate" if list_kind == "ol" else "itemize"
            body.append(r"\begin{" + env + "}")
            for item in list_buf:
                body.append(r"\item " + fmt_inline(item))
            body.append(r"\end{" + env + "}")
            body.append("")
            list_buf = []
            list_kind = None

    def flush_code() -> None:
        nonlocal code_buf, code_kind
        if code_buf:
            if code_kind == "mermaid":
                mermaid_text = "\n".join(code_buf).strip()
                if mermaid_text:
                    rendered = render_mermaid_block(mermaid_text, mermaid_dir)
                    body.append(figure_from_path(rendered, "Mermaid 图示"))
            else:
                body.append(r"\begin{codeblock}")
                body.extend(code_buf)
                body.append(r"\end{codeblock}")
            body.append("")
            code_buf = []
            code_kind = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
                code_kind = stripped[3:].strip().lower() or None
            continue
        if in_code:
            code_buf.append(line.rstrip())
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            flush_list()
            chapter_title_full = stripped[2:].strip()
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            flush_list()
            body.append(r"\section*{" + esc_text(stripped[3:].strip()) + "}")
            body.append("")
            continue
        img = re.match(r"!\[(.*?)\]\((.*?)\)", stripped)
        if img:
            flush_paragraph()
            flush_list()
            body.append(figure_block(md_path.parent, img.group(2), img.group(1)))
            body.append("")
            continue
        if re.match(r"-\s+", stripped):
            flush_paragraph()
            if list_kind not in (None, "ul"):
                flush_list()
            list_kind = "ul"
            list_buf.append(re.sub(r"^-\s+", "", stripped))
            continue
        if re.match(r"\d+\.\s+", stripped):
            flush_paragraph()
            if list_kind not in (None, "ol"):
                flush_list()
            list_kind = "ol"
            list_buf.append(re.sub(r"^\d+\.\s+", "", stripped))
            continue
        if not stripped:
            flush_paragraph()
            flush_list()
            continue
        paragraph_buf.append(line)

    flush_paragraph()
    flush_list()
    flush_code()

    if not chapter_title_full:
        raise ValueError(f"No chapter title found in {md_path}")
    chapter_no: int | None = None
    chapter_title = chapter_title_full
    match = re.match(r"^第\s*(\d+)\s*章\s*(.*)$", chapter_title_full)
    if match:
        chapter_no = int(match.group(1))
        chapter_title = match.group(2).strip() or chapter_title_full
    return chapter_no, chapter_title, "\n".join(body)


def build_tex(chapter_no: int | None, chapter_title: str, body_tex: str) -> str:
    title = esc_text(chapter_title)
    chapter_counter = rf"\setcounter{{chapter}}{{{chapter_no - 1}}}" if chapter_no else ""
    return f"""
\\documentclass[UTF8,zihao=-4,oneside,openany]{{ctexbook}}
\\usepackage[paperwidth=185mm,paperheight=260mm,left=23mm,right=23mm,top=22mm,bottom=20mm,headheight=14pt,headsep=6mm,footskip=11mm]{{geometry}}
\\usepackage{{fontspec}}
\\usepackage{{xeCJK}}
\\usepackage{{graphicx}}
\\usepackage{{caption}}
\\usepackage{{float}}
\\usepackage{{xcolor}}
\\usepackage{{fancyhdr}}
\\usepackage{{enumitem}}
\\usepackage{{xurl}}
\\usepackage{{titlesec}}
\\usepackage{{setspace}}
\\usepackage{{listings}}
\\usepackage{{microtype}}

\\setmainfont{{Times New Roman}}
\\setsansfont{{Helvetica Neue}}
\\setmonofont{{Menlo}}
\\setCJKmainfont{{Songti SC}}
\\setCJKsansfont{{PingFang SC}}
\\setCJKmonofont{{Menlo}}
\\xeCJKsetup{{CJKecglue=\\hskip 0pt plus 0.08\\baselineskip}}
\\XeTeXlinebreaklocale "zh"
\\XeTeXlinebreakskip = 0pt plus 1pt

\\setlength{{\\parindent}}{{2em}}
\\setlength{{\\parskip}}{{0pt}}
\\setstretch{{1.58}}
\\emergencystretch=2em
\\flushbottom
\\clubpenalty=10000
\\widowpenalty=10000
\\displaywidowpenalty=10000

\\ctexset{{
  chapter={{
    name={{第,章}},
    number=\\arabic{{chapter}},
    format+=\\raggedright\\sffamily\\bfseries\\zihao{{2}},
    nameformat+=\\sffamily\\bfseries\\zihao{{2}},
    titleformat+=\\sffamily\\bfseries\\zihao{{2}},
    aftername=\\hspace{{0.6em}},
    beforeskip=0pt,
    afterskip=20pt,
  }}
}}

\\titleformat{{\\section}}[block]{{\\sffamily\\bfseries\\zihao{{-3}}\\color[HTML]{{1F2937}}}}{{}}{{0pt}}{{}}
\\captionsetup[figure]{{font={{small}},labelfont={{bf}},labelsep=quad,name=图,skip=6pt}}
\\setlist[itemize]{{leftmargin=2.4em,itemsep=4pt,topsep=4pt,label=\\textopenbullet}}
\\setlist[enumerate]{{leftmargin=2.8em,itemsep=4pt,topsep=4pt}}

\\lstdefinestyle{{bookcode}}{{
  basicstyle=\\ttfamily\\small,
  backgroundcolor=\\color[HTML]{{F5F3EF}},
  frame=single,
  rulecolor=\\color[HTML]{{D8D2C7}},
  framerule=0.4pt,
  xleftmargin=0.8em,
  xrightmargin=0.8em,
  aboveskip=8pt,
  belowskip=8pt,
  columns=fullflexible,
  keepspaces=true,
  breaklines=true,
  breakatwhitespace=false,
  showstringspaces=false
}}
\\lstnewenvironment{{codeblock}}{{\\lstset{{style=bookcode}}}}{{}}
\\urlstyle{{tt}}
\\newcommand{{\\inlinecode}}[1]{{{{\\small\\path{{#1}}}}}}

\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyhead[R]{{\\small\\thepage}}
\\fancyhead[L]{{\\small\\nouppercase{{{title}}}}}
\\renewcommand{{\\headrulewidth}}{{0.35pt}}
\\renewcommand{{\\footrulewidth}}{{0pt}}
\\fancypagestyle{{plain}}{{\\fancyhf{{}}\\fancyfoot[C]{{\\small\\thepage}}\\renewcommand{{\\headrulewidth}}{{0pt}}}}

\\begin{{document}}
\\mainmatter
{chapter_counter}
\\chapter{{{title}}}
{body_tex}
\\end{{document}}
"""


def render_preview(pdf_path: Path, preview_dir: Path) -> None:
    preview_dir.mkdir(parents=True, exist_ok=True)
    if shutil.which("pdftoppm"):
        subprocess.run(
            ["pdftoppm", "-png", str(pdf_path), str(preview_dir / pdf_path.stem)],
            check=True,
            capture_output=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("chapter_dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()

    chapter_dir = args.chapter_dir.resolve()
    md_path = resolve_manuscript_path(chapter_dir)

    output = args.output.resolve() if args.output else chapter_dir / f"{chapter_dir.name}.pdf"
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        chapter_no, title, body_tex = parse_markdown(md_path, tmp / "mermaid")
        tex = build_tex(chapter_no, title, body_tex)
        tex_path = tmp / "chapter.tex"
        tex_path.write_text(tex, encoding="utf-8")
        cmd = ["/Library/TeX/texbin/xelatex", "-interaction=nonstopmode", "-halt-on-error", str(tex_path)]
        for _ in range(2):
            result = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)
            if result.returncode != 0:
                sys.stderr.write(result.stdout)
                sys.stderr.write(result.stderr)
                return result.returncode
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(tmp / "chapter.pdf", output)

    if args.preview_dir:
        render_preview(output, args.preview_dir.resolve())

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
