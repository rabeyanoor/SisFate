"""Turn paper/paper.md into an Overleaf-ready LaTeX project in results/latex/.

The markdown is the single source of truth: it is what `scripts/23_audit_paper.py` checks, and both the
.docx and this .tex are generated from it, so the three cannot drift apart. Figures are copied as PDFs where
they exist (vector) and PNG otherwise.

Each figure is placed where its legend sits in the markdown, which is right after the paragraph that first
cites it, with the legend as its caption. The supplementary information is built the same way into its own file.

Run: python scripts/build/build_latex.py                      (paper.md -> main.tex)
     python scripts/build/build_latex.py supplementary_information  (-> supplementary_information.tex)
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAME = sys.argv[1] if len(sys.argv) > 1 else "paper"
MD = (ROOT / "paper" / f"{NAME}.md").read_text()
TEXNAME = "main.tex" if NAME == "paper" else f"{NAME}.tex"
OUT = ROOT / "results" / "latex"
FIGDIR = ROOT / "results" / "figures" / "paper"
(OUT / "figures").mkdir(parents=True, exist_ok=True)

FIGMAP = {
    "1": "Fig1_design_data", "2": "Fig2_predictability", "3": "Fig3_fitness_confound",
    "4": "Fig4_biology", "5": "Fig5_ceiling", "6": "Fig6_schaff_multitreatment",
    "7": "Fig7_external_clinical",
    "S1": "FigS1_gnn_ablation", "S2": "FigS2_typicality", "S3": "FigS3_marker_panel",
    "S4": "FigS4_control_free", "S5": "FigS5_simulation",
}

SPECIALS = {"−": "$-$", "–": "--", "—": "---", "×": "$\\times$", "≤": "$\\leq$", "≥": "$\\geq$",
            "≈": "$\\approx$", "→": "$\\rightarrow$", "π": "$\\pi$", "Δ": "$\\Delta$", "α": "$\\alpha$",
            "β": "$\\beta$", "γ": "$\\gamma$", "κ": "$\\kappa$", "θ": "$\\theta$", "ρ": "$\\rho$",
            "σ": "$\\sigma$", "μ": "$\\mu$", "λ": "$\\lambda$", "χ": "$\\chi$", "Σ": "$\\Sigma$",
            "’": "'", "‘": "'", "“": "``", "”": "''", "…": "\\ldots{}", "✓": "", "°": "$^\\circ$",
            "⁻": "$^-$", "¹": "$^1$", "²": "$^2$", "³": "$^3$", "⁰": "$^0$", "⁵": "$^5$", "⁸": "$^8$",
            "\u00a0": "~", "±": "$\\pm$", "·": "$\\cdot$", "⁴": "$^4$", "⁶": "$^6$",
            "₁": "$_1$", "₂": "$_2$", "₃": "$_3$", "₀": "$_0$", "⁷": "$^7$", "⁹": "$^9$", "É": "\\'E", "ó": "\\'o", "ö": "\\\"o", "ä": "\\\"a",
            "ü": "\\\"u", "é": "\\'e", "è": "\\`e", "í": "\\'i", "á": "\\'a", "ñ": "\\~n", "ç": "\\c{c}",
            "ø": "\\o{}", "å": "\\aa{}", "Ö": "\\\"O", "Ä": "\\\"A", "Ü": "\\\"U"}


MATH_TOKEN = "\x00MATH%d\x00"


def protect_math(t: str):
    """Pull $...$ and $$...$$ spans out before escaping, so their LaTeX is passed through untouched."""
    spans = []

    def grab(m):
        spans.append(m.group(0))
        return MATH_TOKEN % (len(spans) - 1)

    return re.sub(r"\$\$.+?\$\$|\$[^$]+\$", grab, t, flags=re.S), spans


def restore_math(t: str, spans) -> str:
    for i, sp in enumerate(spans):
        t = t.replace(MATH_TOKEN % i, sp)
    return t


def esc(t: str) -> str:
    """Escape LaTeX specials, then translate unicode, leaving markdown emphasis for later."""
    t = t.replace("\\", "\\textbackslash{}")
    for ch in "&%$#_{}":
        t = t.replace(ch, "\\" + ch)
    t = t.replace("^", "\\textasciicircum{}").replace("~", "\\textasciitilde{}")
    t = t.replace("<", "$<$").replace(">", "$>$")
    # straight quotes -> TeX quotes (pairs, left to right)
    out, open_q = [], True
    for ch in t:
        if ch == '"':
            out.append("``" if open_q else "''")
            open_q = not open_q
        else:
            out.append(ch)
    t = "".join(out)
    t = re.sub(r"√\s*(\d+)", lambda m: "$\\sqrt{" + m.group(1) + "}$", t)
    for k, v in SPECIALS.items():
        t = t.replace(k, v)
    t = t.replace("√", "$\\surd$")
    return t


def inline(t: str) -> str:
    """^superscript^, **bold**, *italic*, `code` -> LaTeX, after escaping. Math spans pass through verbatim."""
    t, spans = protect_math(t)
    out, last = [], 0
    for m in re.finditer(r"(\^[^\s^]+\^|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)", t):
        out.append(esc(t[last:m.start()]))
        tok = m.group(0)
        if tok.startswith("^"):
            out.append(r"\textsuperscript{" + esc(tok[1:-1]) + "}")
        elif tok.startswith("**"):
            out.append(r"\textbf{" + esc(tok[2:-2]) + "}")
        elif tok.startswith("*"):
            out.append(r"\emph{" + esc(tok[1:-1]) + "}")
        else:
            out.append(r"\texttt{" + esc(tok[1:-1]) + "}")
        last = m.end()
    out.append(esc(t[last:]))
    return restore_math("".join(out), spans)


def figure_for(label: str, legend: str) -> str:
    stem = FIGMAP.get(label)
    if not stem:
        return ""
    for ext in (".pdf", ".png"):
        src = FIGDIR / f"{stem}{ext}"
        if src.exists():
            shutil.copy(src, OUT / "figures" / src.name)
            return ("\\begin{figure}[!htbp]\n  \\centering\n"
                    f"  \\includegraphics[width=\\linewidth]{{figures/{src.name}}}\n"
                    f"  \\caption*{{{legend}}}\n\\end{{figure}}\n\n")
    return ""


body, in_refs = [], False
for block in [b.strip() for b in MD.split("\n\n") if b.strip()]:
    line = " ".join(block.split("\n"))
    if line.startswith("# "):
        body.append("\\title{" + inline(line[2:]) + "}\n\\maketitle\n")
        continue
    if line.startswith("## "):
        h = line[3:]
        in_refs = h == "References"
        body.append("\\section*{" + inline(h) + "}\n")
        continue
    if line.startswith("### "):
        body.append("\\subsection*{" + inline(line[4:]) + "}\n")
        continue
    if block.startswith("$$") and block.endswith("$$"):
        body.append("\\begin{equation}\n" + block[2:-2].strip() + "\n\\end{equation}\n")
        continue
    m = re.match(r"^\*\*(Supplementary )?Fig\. (\d+) \|", line)
    if m:
        fig = figure_for(("S" if m.group(1) else "") + m.group(2), inline(line))
        if fig:
            body.append(fig)
            continue
    if in_refs:
        body.append("\\noindent " + inline(line) + "\\par\\vspace{2pt}\n")
    else:
        body.append(inline(line) + "\n")

TEX = r"""\documentclass[11pt,a4paper]{article}
% Generated from paper/paper.md by scripts/build/build_latex.py -- edit the markdown, not this file.
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=2.5cm]{geometry}
\usepackage{amsmath}
\usepackage{graphicx}
\usepackage{microtype}
\usepackage[hidelinks]{hyperref}
\usepackage{setspace}
\usepackage{lineno}
\usepackage{caption}
\captionsetup{labelformat=empty,skip=2pt}
\setlength{\parskip}{6pt}
\setlength{\parindent}{0pt}
\date{}
\onehalfspacing
\linenumbers
\begin{document}
""" + "\n".join(body) + "\n\\end{document}\n"

(OUT / TEXNAME).write_text(TEX)
(OUT / "README.md").write_text(
    "# Overleaf project\n\n"
    "Generated from `paper/paper.md`. Upload this folder to Overleaf (New Project -> Upload Project,\n"
    "after zipping it) and compile `main.tex` with pdfLaTeX.\n\n"
    "Do not edit `main.tex` by hand: it is overwritten by `python scripts/build/build_latex.py`. Edit the\n"
    "markdown, then rerun `scripts/23_audit_paper.py` and the build.\n\n"
    "Line numbers are on for review; remove `\\linenumbers` for a clean copy.\n")
print(f"wrote {OUT/TEXNAME} ({len(TEX):,} chars, {len(list((OUT/'figures').iterdir()))} figures)")
