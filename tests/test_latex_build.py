"""The generated LaTeX must be structurally sound: balanced environments, braces and math, no stray
specials, and no characters pdfLaTeX would choke on. Compiling needs a TeX installation; this does not."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_latex_builds_and_validates():
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build" / "build_latex.py")], check=True, cwd=ROOT)
    t = (ROOT / "new_paper" / "latex" / "main.tex").read_text()
    body = "\n".join(l for l in t.split("\n") if not l.lstrip().startswith("%"))
    for env in set(re.findall(r"\\begin\{(\w+\*?)\}", t)):
        assert len(re.findall(r"\\begin\{" + re.escape(env) + r"\}", t)) == \
               len(re.findall(r"\\end\{" + re.escape(env) + r"\}", t)), env
    nomath = re.sub(r"\$[^$]*\$", "", body)
    for ch in "&#%":
        assert not re.search(r"(?<!\\)" + re.escape(ch), nomath), ch
    assert nomath.count("$") % 2 == 0
    assert t.count("{") == t.count("}")
    assert not [c for c in t if ord(c) > 127], "non-ascii left in the LaTeX"
    assert t.rstrip().endswith(r"\end{document}")
    # every legend in the manuscript must have produced an \includegraphics, or a figure is silently
    # missing from the built paper, which is how Fig. 9 went absent from the LaTeX for several commits
    md = (ROOT / "new_paper" / "manuscript.md").read_text()
    legends = re.findall(r"^\*\*(Supplementary )?Fig\. (\d+)", md, re.M)
    included = len(re.findall(r"\\includegraphics", t))
    assert included == len(legends), f"{len(legends)} legends but {included} figures included"
    for stem in ["Fig1_design_data", "Fig7_schaff_multitreatment", "Fig9_simulation", "FigS3_gnn_ablation"]:
        assert any((ROOT / "new_paper" / "latex" / "figures").glob(stem + ".*")), stem
