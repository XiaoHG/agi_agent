#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    return "\n".join(
        [
            r"\begin{figure}[htbp]",
            r"  \centering",
            rf"  \includegraphics[width=0.96\textwidth,height=0.34\textheight,keepaspectratio]{{{abs_path}}}",
            rf"  \caption{{{esc_text(caption)}}}",
            r"\end{figure}",
        ]
    )


def parse_markdown(md_path: Path) -> tuple[int | None, str, str]:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    body: list[str] = []
    paragraph_buf: list[str] = []
    list_buf: list[str] = []
    code_buf: list[str] = []
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
        nonlocal code_buf
        if code_buf:
            body.append(r"\begin{codeblock}")
            body.extend(code_buf)
            body.append(r"\end{codeblock}")
            body.append("")
            code_buf = []

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
    md_path = chapter_dir / "README.md"
    if not md_path.exists():
        raise FileNotFoundError(f"Missing chapter markdown: {md_path}")

    output = args.output.resolve() if args.output else chapter_dir / f"{chapter_dir.name}.pdf"
    chapter_no, title, body_tex = parse_markdown(md_path)
    tex = build_tex(chapter_no, title, body_tex)

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
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
