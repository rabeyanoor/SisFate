"""Build the Genome Biology submission from the master text (paper/paper.md, supplementary_information.md).

Genome Biology (Research article) wants: Vancouver references numbered in square brackets in order of citation;
web links and public data sets cited in the reference list rather than written in the text; a structured
'Availability of data and materials' with a software block; figures uploaded separately with titles and
legends in the main text; the supplement as a separate Additional file; double spacing, line and page
numbers and no page breaks (set by build_docx.js when GB=1).

Outputs (paper/genomebiology/): Main_text.md and Additional_file_1.md.

Run: python scripts/build/make_genomebiology.py
     GB=1 NOFIG=1 node scripts/build/build_docx.js genomebiology/Main_text               (file to submit)
     GB=1 node scripts/build/build_docx.js genomebiology/Additional_file_1
     uv run --with pypandoc_binary python scripts/build/docx_math.py genomebiology/Main_text    (and the other)
"""
import json
import re
from pathlib import Path

from make_ncomms import AUTH, CITE, MANUAL_AUTHORS, NAME, REFS, SPECIAL_TAIL, key_of

ROOT = Path(__file__).resolve().parents[2]
NP = ROOT / "paper"
OUT = NP / "genomebiology"
ACCESSED = "Accessed 10 Oct 2026."
GEO = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc="

# data sets and web resources, cited as {{D:key}} (titles and release years from GEO, DataCite and GitHub)
DATA = {
    "resistrace": f"Tracing back primed resistance in cancer via sister cells. Gene Expression Omnibus. 2023. {GEO}GSE223003. {ACCESSED}",
    "watermelon": f"Cycling cancer persisters arise from lineages with distinct transcriptional and metabolic programs. Gene Expression Omnibus. 2020. {GEO}GSE150949. {ACCESSED}",
    "tnbc": f"Single cell lineage tracing reveals clonal dynamics of anti-EGFR therapy resistance in triple negative breast cancer. Gene Expression Omnibus. 2024. {GEO}GSE228382. {ACCESSED}",
    "figshare": "Gambardella G, Franchini M. Single cell lineage tracing reveals clonal dynamics of anti-EGFR therapy resistance in triple negative breast cancer. figshare. 2024. https://doi.org/10.6084/m9.figshare.24787458.",
    "schaff": f"Pre-existing cell states predict resistance to multiple treatments. Gene Expression Omnibus. 2024. {GEO}GSE279162. {ACCESSED}",
    "patients": f"Longitudinal single-cell RNA-seq data of metastatic ovarian cancer. Gene Expression Omnibus. 2021. {GEO}GSE165897. {ACCESSED}",
    "xena": f"UCSC Xena. TCGA Ovarian Cancer (OV): gene expression (HiSeqV2) and curated survival data. https://xenabrowser.net/datapages/?cohort=TCGA%20Ovarian%20Cancer%20(OV). {ACCESSED}",
    "infercnvpy": f"infercnvpy: infer copy number variation (CNV) from scRNA-seq data. https://github.com/icbi-lab/infercnvpy. {ACCESSED}",
    "repo": "Noor R. SisFate: fitness-adjusted evaluation of pre-treatment cell fate prediction. GitHub. 2026. https://github.com/rabeyanoor/SisFate.",
}
VANCOUVER_MANUAL = {
    ("Aviv", 2026): "Aviv H",
    ("Pedregosa", 2011): "Pedregosa F, Varoquaux G, Gramfort A, Michel V, Thirion B, Grisel O, et al",
    ("Prokhorenkova", 2018): "Prokhorenkova L, Gusev G, Vorobev A, Dorogush AV, Gulin A",
    ("Hamilton", 2017): "Hamilton WL, Ying R, Leskovec J",
    ("ChenT", 2020): "Chen T, Kornblith S, Norouzi M, Hinton G",
}
assert set(VANCOUVER_MANUAL) == set(MANUAL_AUTHORS)
VANCOUVER_TAIL = {
    ("Aviv", 2026): "Zenodo. 2026. https://doi.org/10.5281/zenodo.22850050.",
    ("Shen", 2026): "bioRxiv. 2026. https://doi.org/10.64898/2026.04.10.717709.",
    ("Prokhorenkova", 2018): "In: Advances in Neural Information Processing Systems 31. 2018. https://arxiv.org/abs/1706.09516.",
    ("Hamilton", 2017): "In: Advances in Neural Information Processing Systems 30. 2017. https://arxiv.org/abs/1706.02216.",
    ("ChenT", 2020): "In: Proceedings of the 37th International Conference on Machine Learning. 2020. https://arxiv.org/abs/2002.05709.",
}
assert set(VANCOUVER_TAIL) == set(SPECIAL_TAIL)


def v_authors(key) -> str:
    if key in VANCOUVER_MANUAL:
        return VANCOUVER_MANUAL[key]
    a = json.loads(AUTH.read_text())[REFS[key][0]]["authors"]
    names = [fam + " " + "".join(p[0] for p in re.split(r"[\s.\-]+", giv) if p) for fam, giv in a]
    return ", ".join(names[:6]) + (", et al" if len(names) > 6 else "")


def v_entry(key) -> str:
    if isinstance(key, str):
        return DATA[key]
    doi, title, jour, vol, pages = REFS[key]
    head = f"{v_authors(key)}. {title}."
    if key in VANCOUVER_TAIL:
        return f"{head} {VANCOUVER_TAIL[key]}"
    jour = jour.replace(".", "")
    tail = f" https://doi.org/{doi}." if doi else ""
    if key == ("Pedregosa", 2011):
        tail = " https://jmlr.org/papers/v12/pedregosa11a.html."
    return f"{head} {jour}. {key[1]};{vol}:{pages.replace('–', '-')}.{tail}"


class Vancouver:
    """Numbers literature ((Name, year) citations) and data sets ({{D:key}}) together in order of first
    citation, and writes them as [n] in square brackets."""

    def __init__(self):
        self.order = []

    def num(self, k):
        if k not in self.order:
            self.order.append(k)
        return self.order.index(k) + 1

    def brackets(self, keys):
        ns = sorted({self.num(k) for k in keys})
        parts, i = [], 0
        while i < len(ns):
            j = i
            while j + 1 < len(ns) and ns[j + 1] == ns[j] + 1:
                j += 1
            parts.append(f"{ns[i]}–{ns[j]}" if j - i >= 2 else ", ".join(map(str, ns[i:j + 1])))
            i = j + 1
        return "[" + ", ".join(parts) + "]"

    def data(self, text):
        return re.sub(r"\{\{D:(\w+)\}\}", lambda m: self.brackets([m.group(1)]), text)

    def convert(self, text: str) -> str:
        def paren(inner):
            keys, rest = [], []
            for part in inner.split("; "):
                keys += [key_of(n, int(y)) for n, y in CITE.findall(part)]
                left = CITE.sub("", part).strip().rstrip(",").strip()
                if left:
                    rest.append(self.data(left))
            s = self.brackets(keys)
            return f"({'; '.join(rest)} {s})" if rest else s

        def repl(m):
            if m.group(1):  # data set or web resource
                return " " * bool(m.group(1).startswith(" ")) + self.brackets([m.group(2)])
            if m.group(3):  # narrative: Sharma et al. (2010) -> Sharma et al. [1]
                return f"{m.group(3)} {self.brackets([key_of(m.group(3), int(m.group(4)))])}"
            inner = m.group(6)
            if not CITE.search(inner):
                return self.data(m.group(0))
            s = paren(inner)
            return m.group(5) + s
        pat = rf"( ?\{{\{{D:(\w+)\}}\}})|({NAME}) \((\d{{4}})\)|( ?)\(([^()]*\d{{4}}[^()]*)\)"
        return re.sub(pat, repl, text)


def number(md: str, conv: Vancouver) -> str:
    return "\n\n".join(conv.convert(p) for p in md.split("\n\n"))


def ref_list(conv: Vancouver) -> str:
    return "\n\n".join(f"{i + 1}. {v_entry(k)}" for i, k in enumerate(conv.order))


def legends(md: str, supp=False) -> str:
    # "**Fig. 1 | Title.**" -> "**Fig. 1** **Title.**", the journal's style; supplementary figures become Fig. S1
    md = re.sub(r"\*\*Fig\. (\d+) \| ", r"**Fig. \1** **", md)
    md = re.sub(r"\*\*Supplementary Fig\. (\d+) \| ", r"**Fig. S\1** **", md)
    return md


SUP = str.maketrans("⁻⁰¹²³⁴⁵⁶⁷⁸⁹", "−0123456789")


def superscripts(md: str) -> str:
    """10⁻²⁵ (Unicode superscript characters, which many fonts lack) -> 10^−25^ (a real superscript)."""
    return re.sub(r"10([⁻⁰¹²³⁴⁵⁶⁷⁸⁹]+)", lambda m: "10^" + m.group(1).translate(SUP) + "^", md)


def name_files(md: str) -> str:
    """The journal wants supplementary material referred to by file name: 'Additional file 2: Table S19'."""
    md = re.sub(r"(?<!: )\b(Tables? S\d)", r"Additional file 2: \1", md)
    md = re.sub(r"(?<!: )\b(Figs?\. S\d)", r"Additional file 1: \1", md)
    md = re.sub(r"(?<!: )\b(Supplementary Notes? \d)", r"Additional file 1: \1", md)
    return md


def sub1(t, a, b, n=1):
    assert t.count(a) == n, (a, t.count(a))
    return t.replace(a, b)


def main_text() -> str:
    pm = (NP / "paper.md").read_text()
    body = pm[:pm.index("## References")].rstrip()
    extra = pm[pm.index("## Additional files"):]
    # web links and data sets go to the reference list
    body = sub1(body, "downloaded from GEO (GSE223003;", "downloaded from GEO (GSE223003 {{D:resistrace}};")
    body = re.sub(r"taken from GEO\s+\(GSE279162\)\.", "taken from GEO (GSE279162 {{D:schaff}}).", body)
    body = sub1(body, "obtained from GEO (GSE165897; Zhang et al., 2022)", "obtained from GEO (GSE165897 {{D:patients}}; Zhang et al. (2022))")
    body = sub1(body, "For Watermelon (GEO GSE150949)", "For Watermelon (GEO GSE150949 {{D:watermelon}})")
    body = sub1(body, "(GEO GSE228382)", "(GEO GSE228382 {{D:tnbc}})")
    body = sub1(body, "Seurat object (figshare, doi:10.6084/m9.figshare.24787458)", "Seurat object from figshare {{D:figshare}}")
    body = sub1(body, "were obtained from UCSC Xena.", "were obtained from UCSC Xena {{D:xena}}.")
    body = sub1(body, "with infercnvpy (https://github.com/icbi-lab/infercnvpy; window", "with infercnvpy {{D:infercnvpy}} (window")
    body = sub1(body, "Preranked GSEA (Subramanian et al., 2005; GSEApy, Fang et al., 2023)",
                "Preranked GSEA (Subramanian et al., 2005) with GSEApy (Fang et al., 2023)")
    body = superscripts(name_files(body))
    a0 = body.index("**Availability of data and materials.**")
    a1 = body.index("**Competing interests.**")
    body = body[:a0] + AVAILABILITY + "\n\n" + body[a1:]
    assert "http" not in re.sub(r"\*\*Project home page:\*\* \S+", "", body), "URL left in the text"
    extra = ADDITIONAL_FILES
    conv = Vancouver()
    body = number(legends(body), conv)
    return body + "\n\n## References\n\n" + ref_list(conv) + "\n\n" + extra.strip() + "\n"


ADDITIONAL_FILES = """## Additional files

**Additional file 1** (.docx). **Supplementary Notes and Figures.** Supplementary Note 1 (graph model and hyperparameter sweep), Supplementary Note 2 (pre-specified marker panel and the insulin-like growth factor axis) and Supplementary Note 3 (inferred copy-number subclones), followed by Supplementary Figures S1–S5 with their legends.

**Additional file 2** (.xlsx). **Supplementary Tables S1–S30.** All result tables underlying the figures and text, one table per sheet, including full differential expression and gene-set enrichment results. The first sheet lists every table with a short description."""

AVAILABILITY = """**Availability of data and materials.** All data sets analysed during the current study are publicly available: the ReSisTrace data in the Gene Expression Omnibus (GEO) repository, GSE223003 {{D:resistrace}}; the PC9 osimertinib (Watermelon) lineage data, GSE150949 {{D:watermelon}}; the triple-negative breast cancer lineage data, GSE228382 {{D:tnbc}}, with per-cell lineage annotations on figshare {{D:figshare}}; the second lineage system, GSE279162 {{D:schaff}}; the patient cohort, GSE165897 {{D:patients}}; and TCGA-OV through UCSC Xena {{D:xena}}. All result tables underlying the figures and text, including full differential expression and gene-set enrichment results, are included in this published article (Additional file 2, Tables S1–S30). The code that regenerates every result, figure and table from the public data is available on GitHub {{D:repo}}.

**Project name:** SisFate (analysis code and the Python package `persist`, with the evaluation module `persist.fitadj`)

**Project home page:** https://github.com/rabeyanoor/SisFate

**Archived version:** a release will be archived at Zenodo with a DOI on acceptance

**Operating system(s):** platform independent (tested on Linux)

**Programming language:** Python 3.12; one R script exports a Seurat object

**Other requirements:** dependencies are pinned in `uv.lock` (NumPy 2.5, scikit-learn 1.9, Scanpy 1.12, PyTorch 2.14 CPU); the Geneformer and scGPT forward passes used one NVIDIA T4 GPU (Kaggle), and their kernel scripts are included

**License:** MIT

**Any restrictions to use by non-academics:** none

The module `persist.fitadj` takes plain arrays and any scikit-learn classifier, so the fitness-adjusted evaluation (control-arm baseline, size-matched ΔAUROC with a family-level bootstrap interval, family permutation null and sister ceiling) can be applied to other lineage-tracing designs that include an untreated arm. The configuration file (`configs/default.yaml`) fixes the random seed and all hyperparameters, a single script (`scripts/run_all.sh`) regenerates all results on a laptop CPU, and every metric is stored together with a hash of the configuration that produced it."""


def additional_file_1() -> str:
    sm = (NP / "supplementary_information.md").read_text()
    sm = sm[:sm.index("## References")].rstrip()
    sm = sub1(sm, "# Supplementary Information\n\nAdditional file 1 for:",
              "# Additional file 1\n\nSupplementary Notes 1–3 and Supplementary Figures S1–S5 for:")
    sm = sm.replace("\n\n## Supplementary Notes", "\n\nRabeya Noor and Khairum Jahan Roza\n\n## Supplementary Notes", 1)
    conv = Vancouver()
    sm = superscripts(re.sub(r"(?<!: )\b(Tables? S\d)", r"Additional file 2: \1", sm))
    sm = number(legends(sm, supp=True), conv)
    return sm + "\n\n## References\n\n" + ref_list(conv) + "\n"


def main():
    OUT.mkdir(exist_ok=True)
    ms, af = main_text(), additional_file_1()
    for name, text in (("Main_text", ms), ("Additional_file_1", af)):
        left = CITE.findall(re.sub(r"^\d+\. .*$", "", text, flags=re.M)) + re.findall(r"\{\{D:", text)
        assert not left, (name, left[:5])
        (OUT / f"{name}.md").write_text(text)
    n = len(re.findall(r"^\d+\. ", ms.split("## References")[1], flags=re.M))
    print(f"Main_text.md: {n} references; Additional_file_1.md written to {OUT}")


if __name__ == "__main__":
    main()
