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
    for stem in ["Fig1_design_data", "Fig7_schaff_multitreatment", "Fig8_control_free"]:
        assert any((ROOT / "new_paper" / "latex" / "figures").glob(stem + ".*")), stem
