"""Replace the @@MATHn@@ placeholders written by build_docx.js with native Word equations (OMML).

pandoc converts every TeX snippet in one pass; each snippet sits in its own paragraph of a scratch document,
so the n-th paragraph's equation belongs to placeholder n. Inline snippets become <m:oMath>, displayed ones
<m:oMathPara>, which Word shows as ordinary, editable equations.

Run: uv run --with pypandoc_binary python scripts/build/docx_math.py [name]     (default name: hi)
"""
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import pypandoc

ROOT = Path(__file__).resolve().parents[2]
name = sys.argv[1] if len(sys.argv) > 1 else "hi"
docx = ROOT / "new_paper" / f"{name}.docx"
spec = docx.with_suffix(".math.json")
math = json.loads(spec.read_text())

with tempfile.TemporaryDirectory() as tmp:
    md = "\n\n".join(f"$${m['tex']}$$" if m["display"] else f"${m['tex']}$" for m in math)
    scratch = Path(tmp) / "math.docx"
    pypandoc.convert_text(md, "docx", format="markdown", outputfile=str(scratch))
    body = zipfile.ZipFile(scratch).read("word/document.xml").decode("utf8")

paras = re.findall(r"<w:p>.*?</w:p>|<w:p .*?</w:p>", body, flags=re.S)
omml = []
for p in paras:
    eq = re.search(r"<m:oMathPara>.*</m:oMathPara>|<m:oMath>.*</m:oMath>", p, flags=re.S)
    if eq:
        omml.append(eq.group(0))
if len(omml) != len(math):
    sys.exit(f"pandoc returned {len(omml)} equations for {len(math)} snippets; nothing changed")

with zipfile.ZipFile(docx) as z:
    items = {i.filename: z.read(i.filename) for i in z.infolist()}
xml = items["word/document.xml"].decode("utf8")
done = 0


def swap(m):
    global done
    k = int(m.group(1))
    eq = omml[k]
    if math[k]["display"] and eq.startswith("<m:oMath>"):
        eq = f"<m:oMathPara>{eq}</m:oMathPara>"
    if not math[k]["display"] and eq.startswith("<m:oMathPara>"):
        eq = re.sub(r"^<m:oMathPara>(?:<m:oMathParaPr>.*?</m:oMathParaPr>)?|</m:oMathPara>$", "", eq, flags=re.S)
    done += 1
    return eq


# a placeholder is always a whole run of its own: <w:r>[<w:rPr>..</w:rPr>]<w:t ...>@@MATHn@@</w:t></w:r>
xml = re.sub(r"<w:r>(?:<w:rPr>(?:(?!</w:r>).)*?</w:rPr>)?<w:t[^>]*>@@MATH(\d+)@@</w:t></w:r>", swap, xml, flags=re.S)
if done != len(math) or "@@MATH" in xml:
    sys.exit(f"replaced {done} of {len(math)} placeholders; leftover placeholders remain; nothing written")
items["word/document.xml"] = xml.encode("utf8")

tmp_out = docx.with_suffix(".tmp.docx")
with zipfile.ZipFile(tmp_out, "w", zipfile.ZIP_DEFLATED) as z:
    for k, v in items.items():
        z.writestr(k, v)
shutil.move(tmp_out, docx)
spec.unlink()
print(f"{docx}: {done} equations converted ({sum(m['display'] for m in math)} displayed)")
