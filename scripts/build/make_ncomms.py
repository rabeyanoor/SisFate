"""Build the Nature Communications version of the paper from the Genome Biology master.

Inputs (new_paper/): ncomms_draft.md (title, abstract, Introduction, Results, Discussion, written for this
journal), ncomms_supp_draft.md (Supplementary Notes and Figures), paper.md (Methods are taken from here, so the
two versions never disagree), Supplementary_Tables.xlsx.

Outputs (new_paper/): ncomms_paper.md, ncomms_supplementary.md, and ncomms_supplementary_data/ with one
Supplementary Data file per table, numbered in order of first citation, plus the legends for the cover letter.
Nature style: numbered superscript citations in order of first citation (text first, then figure legends),
"Supplementary Fig. N", numbered display equations, gene symbols in italics.

Run: uv run --with openpyxl python scripts/build/make_ncomms.py
     node scripts/build/build_docx.js ncomms_paper && node scripts/build/build_docx.js ncomms_supplementary
     uv run --with pypandoc_binary python scripts/build/docx_math.py ncomms_paper   (and ncomms_supplementary)
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NP = ROOT / "new_paper"
AUTH = Path(__file__).with_name("ncomms_authors.json")  # Crossref author lists, fetched once

# key: (in-text surname as written, year, doi, title in sentence case, journal abbreviation, volume, pages)
REFS = {
    ("Ashburner", 2000): ("10.1038/75556", "Gene Ontology: tool for the unification of biology", "Nat. Genet.", "25", "25–29"),
    ("Aviv", 2026): (None, "Pretreatment transcriptional state carries condition-specific information about future clonal detection in a lineage-traced melanoma line", None, None, None),
    ("Chen", 2026): ("10.1038/s43588-026-00972-4", "Scaling and quantization of large-scale foundation model enables resource-efficient predictions in network biology", "Nat. Comput. Sci.", "6", "450–463"),
    ("Chen", 2022): ("10.1038/s41467-022-34277-7", "Deep transfer learning of cancer drug responses by integrating bulk and single-cell RNA-seq data", "Nat. Commun.", "13", "6494"),
    ("Cui", 2024): ("10.1038/s41592-024-02201-0", "scGPT: toward building a foundation model for single-cell multi-omics using generative AI", "Nat. Methods", "21", "1470–1480"),
    ("Dai", 2024): ("10.1038/s41467-024-45478-7", "Tracing back primed resistance in cancer via sister cells", "Nat. Commun.", "15", "1158"),
    ("Davidson-Pilon", 2019): ("10.21105/joss.01317", "lifelines: survival analysis in Python", "J. Open Source Softw.", "4", "1317"),
    ("Emert", 2021): ("10.1038/s41587-021-00837-3", "Variability within rare cell states enables multiple paths toward drug resistance", "Nat. Biotechnol.", "39", "865–876"),
    ("Fang", 2023): ("10.1093/bioinformatics/btac757", "GSEApy: a comprehensive package for performing gene set enrichment analysis in Python", "Bioinformatics", "39", "btac757"),
    ("Fennell", 2022): ("10.1038/s41586-021-04206-7", "Non-genetic determinants of malignant clonal fitness at single-cell resolution", "Nature", "601", "125–131"),
    ("Fustero-Torre", 2021): ("10.1186/s13073-021-01001-x", "Beyondcell: targeting cancer therapeutic heterogeneity in single-cell RNA-seq data", "Genome Med.", "13", "187"),
    ("Goyal", 2023): ("10.1038/s41586-023-06342-8", "Diverse clonal fates emerge upon drug treatment of homogeneous cancer cells", "Nature", "620", "651–659"),
    ("Gutierrez", 2021): ("10.1038/s43018-021-00222-8", "Multifunctional barcoding with ClonMapper enables high-resolution study of clonal dynamics during tumor evolution and treatment", "Nat. Cancer", "2", "758–772"),
    ("Harmange", 2023): ("10.1038/s41467-023-41811-8", "Disrupting cellular memory to overcome drug resistance", "Nat. Commun.", "14", "7130"),
    ("Hata", 2016): ("10.1038/nm.4040", "Tumor cells can follow distinct evolutionary paths to become resistant to epidermal growth factor receptor inhibition", "Nat. Med.", "22", "262–269"),
    ("Iyer", 2025): ("10.1371/journal.pcbi.1013446", "Inheritable cell-states shape drug-persister correlations and population dynamics in cancer cells", "PLoS Comput. Biol.", "21", "e1013446"),
    ("Korsunsky", 2019): ("10.1038/s41592-019-0619-0", "Fast, sensitive and accurate integration of single-cell data with Harmony", "Nat. Methods", "16", "1289–1296"),
    ("Kuleshov", 2016): ("10.1093/nar/gkw377", "Enrichr: a comprehensive gene set enrichment analysis web server 2016 update", "Nucleic Acids Res.", "44", "W90–W97"),
    ("Lamb", 2006): ("10.1126/science.1132939", "The Connectivity Map: using gene-expression signatures to connect small molecules, genes, and disease", "Science", "313", "1929–1935"),
    ("Lause", 2021): ("10.1186/s13059-021-02451-7", "Analytic Pearson residuals for normalization of single-cell RNA-seq UMI data", "Genome Biol.", "22", "258"),
    ("Liberzon", 2015): ("10.1016/j.cels.2015.12.004", "The Molecular Signatures Database hallmark gene set collection", "Cell Syst.", "1", "417–425"),
    ("Liu", 2018): ("10.1016/j.cell.2018.02.052", "An integrated TCGA pan-cancer clinical data resource to drive high-quality survival outcome analytics", "Cell", "173", "400–416"),
    ("Lopez", 2018): ("10.1038/s41592-018-0229-2", "Deep generative modeling for single-cell transcriptomics", "Nat. Methods", "15", "1053–1058"),
    ("Marine", 2020): ("10.1038/s41568-020-00302-4", "Non-genetic mechanisms of therapeutic resistance in cancer", "Nat. Rev. Cancer", "20", "743–756"),
    ("Oliveira", 2025): ("10.1158/0008-5472.CAN-25-0999", "Epigenetic heritability of cell plasticity drives cancer drug resistance through a one-to-many genotype-to-phenotype paradigm", "Cancer Res.", "85", "2921–2938"),
    ("Oren", 2021): ("10.1038/s41586-021-03796-6", "Cycling cancer persister cells arise from lineages with distinct programs", "Nature", "596", "576–582"),
    ("Paek", 2016): ("10.1016/j.cell.2016.03.025", "Cell-to-cell variation in p53 dynamics leads to fractional killing", "Cell", "165", "631–642"),
    ("Patel", 2014): ("10.1126/science.1254257", "Single-cell RNA-seq highlights intratumoral heterogeneity in primary glioblastoma", "Science", "344", "1396–1401"),
    ("Pedregosa", 2011): (None, "Scikit-learn: machine learning in Python", "J. Mach. Learn. Res.", "12", "2825–2830"),
    ("Pellecchia", 2024): ("10.1186/s13073-024-01327-2", "Single cell lineage tracing reveals clonal dynamics of anti-EGFR therapy resistance in triple negative breast cancer", "Genome Med.", "16", "55"),
    ("Prokhorenkova", 2018): (None, "CatBoost: unbiased boosting with categorical features", None, None, None),
    ("Ramirez", 2016): ("10.1038/ncomms10690", "Diverse drug-resistance mechanisms can emerge from drug-tolerant cancer persister cells", "Nat. Commun.", "7", "10690"),
    ("Rehman", 2021): ("10.1016/j.cell.2020.11.018", "Colorectal cancer cells enter a diapause-like DTP state to survive chemotherapy", "Cell", "184", "226–242"),
    ("Schaff", 2026): ("10.1016/j.xgen.2026.101191", "Pre-existing cell states predict resistance to multiple treatments", "Cell Genom.", "6", "101191"),
    ("Shaffer", 2017): ("10.1038/nature22794", "Rare cell variability and drug-induced reprogramming as a mode of cancer drug resistance", "Nature", "546", "431–435"),
    ("Shaffer", 2020): ("10.1016/j.cell.2020.07.003", "Memory sequencing reveals heritable single-cell gene expression programs associated with distinct cellular behaviors", "Cell", "182", "947–959"),
    ("Sharma", 2010): ("10.1016/j.cell.2010.02.027", "A chromatin-mediated reversible drug-tolerant state in cancer cell subpopulations", "Cell", "141", "69–80"),
    ("Shen", 2026): ("10.64898/2026.04.10.717709", "Predicting pre-treatment resistance or post-treatment effect? A systematic benchmarking of single-cell drug response models", None, None, None),
    ("Smirnov", 2016): ("10.1093/bioinformatics/btv723", "PharmacoGx: an R package for analysis of large pharmacogenomic datasets", "Bioinformatics", "32", "1244–1246"),
    ("Soragni", 2025): ("10.1038/s41568-025-00824-9", "Acquired resistance in cancer: towards targeted therapeutic strategies", "Nat. Rev. Cancer", "25", "613–633"),
    ("Spencer", 2009): ("10.1038/nature08012", "Non-genetic origins of cell-to-cell variability in TRAIL-induced apoptosis", "Nature", "459", "428–432"),
    ("Subramanian", 2005): ("10.1073/pnas.0506580102", "Gene set enrichment analysis: a knowledge-based approach for interpreting genome-wide expression profiles", "Proc. Natl Acad. Sci. USA", "102", "15545–15550"),
    ("Suphavilai", 2021): ("10.1186/s13073-021-01000-y", "Predicting heterogeneity in clone-specific therapeutic vulnerabilities using single-cell transcriptomic signatures", "Genome Med.", "13", "189"),
    ("Theodoris", 2023): ("10.1038/s41586-023-06139-9", "Transfer learning enables predictions in network biology", "Nature", "618", "616–624"),
    ("Tirosh", 2016): ("10.1126/science.aad0501", "Dissecting the multicellular ecosystem of metastatic melanoma by single-cell RNA-seq", "Science", "352", "189–196"),
    ("Wagner", 2020): ("10.1038/s41576-020-0223-2", "Lineage tracing meets single-cell omics: opportunities and challenges", "Nat. Rev. Genet.", "21", "410–427"),
    ("Wang", 2022): ("10.1038/s41587-022-01209-1", "CoSpar identifies early cell fate biases from single-cell transcriptomic and lineage information", "Nat. Biotechnol.", "40", "1066–1074"),
    ("Weinreb", 2020): ("10.1126/science.aaw3381", "Lineage tracing on transcriptional landscapes links state to fate during differentiation", "Science", "367", "eaaw3381"),
    ("Wolf", 2018): ("10.1186/s13059-017-1382-0", "SCANPY: large-scale single-cell gene expression data analysis", "Genome Biol.", "19", "15"),
    ("Zhang", 2022): ("10.1126/sciadv.abm1831", "Longitudinal single-cell RNA-seq analysis reveals stress-promoted chemoresistance in metastatic ovarian cancer", "Sci. Adv.", "8", "eabm1831"),
    ("Zheng", 2023): ("10.1002/advs.202204113", "Enabling single-cell drug response annotations from bulk RNA-seq using SCAD", "Adv. Sci.", "10", "2204113"),
    # supplementary only
    ("Hamilton", 2017): (None, "Inductive representation learning on large graphs", None, None, None),
    ("ChenT", 2020): (None, "A simple framework for contrastive learning of visual representations", None, None, None),
}
# references without a Crossref author list (or not on Crossref), written out by hand from the master list
MANUAL_AUTHORS = {
    ("Aviv", 2026): "Aviv, H.",
    ("Pedregosa", 2011): "Pedregosa, F. et al.",
    ("Prokhorenkova", 2018): "Prokhorenkova, L., Gusev, G., Vorobev, A., Dorogush, A. V. & Gulin, A.",
    ("Hamilton", 2017): "Hamilton, W. L., Ying, R. & Leskovec, J.",
    ("ChenT", 2020): "Chen, T., Kornblith, S., Norouzi, M. & Hinton, G.",
}
SPECIAL_TAIL = {
    ("Aviv", 2026): "Preprint at https://doi.org/10.5281/zenodo.22850050 (2026).",
    ("Shen", 2026): "Preprint at https://doi.org/10.64898/2026.04.10.717709 (2026).",
    ("Prokhorenkova", 2018): "In Advances in Neural Information Processing Systems 31 (2018).",
    ("Hamilton", 2017): "Preprint at https://arxiv.org/abs/1706.02216 (2017).",
    ("ChenT", 2020): "Preprint at https://arxiv.org/abs/2002.05709 (2020).",
}


def initials(given: str) -> str:
    out = []
    for part in given.replace("\xa0", " ").split():
        sub = [s for s in part.split("-") if s]
        out.append("-".join(s[0] + "." for s in sub))
    return " ".join(out)


def authors(key) -> str:
    if key in MANUAL_AUTHORS:
        return MANUAL_AUTHORS[key]
    a = json.loads(AUTH.read_text())[REFS[key][0]]["authors"]
    names = [f"{fam}, {initials(giv)}" for fam, giv in a]
    if len(names) > 5:
        return names[0] + " et al."
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " & " + names[-1]


def entry(key) -> str:
    doi, title, jour, vol, pages = REFS[key]
    head = f"{authors(key)} {title}."
    if key in SPECIAL_TAIL:
        return f"{head} {SPECIAL_TAIL[key]}"
    return f"{head} *{jour}* **{vol}**, {pages} ({key[1]})."


NAME = r"[A-Z][A-Za-z'\-]+(?: et al\.| and [A-Z][A-Za-z\-]+)?"
CITE = re.compile(rf"({NAME}), (\d{{4}})")


def key_of(name: str, year: int):
    sur = name.split(" et al.")[0].split(" and ")[0]
    if sur == "Chen" and year == 2020:
        sur = "ChenT"
    k = (sur, year)
    if k not in REFS:
        raise KeyError(f"no reference for {name} ({year})")
    return k


class Numberer:
    """Assigns numbers in order of first citation, then rewrites citations as ^n^ superscripts."""

    def __init__(self):
        self.order = []

    def num(self, k):
        if k not in self.order:
            self.order.append(k)
        return self.order.index(k) + 1

    def sup(self, keys):
        ns = sorted({self.num(k) for k in keys})
        parts, i = [], 0
        while i < len(ns):
            j = i
            while j + 1 < len(ns) and ns[j + 1] == ns[j] + 1:
                j += 1
            parts.append(f"{ns[i]}–{ns[j]}" if j - i >= 2 else ",".join(map(str, ns[i:j + 1])))
            i = j + 1
        return "^" + ",".join(parts) + "^"

    def convert(self, text: str) -> str:
        # parenthetical: (A et al., 2020; B, 2021) or (some text; A et al., 2020)
        def paren(m):
            inner = m.group(1)
            if not CITE.search(inner):
                return m.group(0)
            keys, rest = [], []
            for part in inner.split("; "):
                found = CITE.findall(part)
                keys += [key_of(n, int(y)) for n, y in found]
                left = CITE.sub("", part).strip().rstrip(",").strip()
                if left:
                    rest.append(left)
            s = self.sup(keys)
            return f"({'; '.join(rest)}){s}" if rest else s
        def repl(m):
            if m.group(1):  # narrative: Sharma et al. (2010) -> Sharma et al.^1^
                return m.group(1) + self.sup([key_of(m.group(1), int(m.group(2)))])
            if not CITE.search(m.group(4)):
                return m.group(0)
            s = paren(re.match(r"\((.*)\)$", m.group(0)[len(m.group(3)):]))
            return s if s.startswith("^") else m.group(3) + s  # a bare citation attaches to the preceding word
        # one left-to-right pass, so numbers follow the order of first citation
        text = re.sub(rf"({NAME}) \((\d{{4}})\)|( ?)\(([^()]*\d{{4}}[^()]*)\)", repl, text)
        return text


def number_in_order(md: str, conv: Numberer) -> str:
    """Text paragraphs first, then figure legends, as the journal requires."""
    paras = md.split("\n\n")
    legend = [p.startswith("**Fig.") or p.startswith("**Supplementary Fig.") for p in paras]
    for i, p in enumerate(paras):
        if not legend[i]:
            paras[i] = conv.convert(p)
    for i, p in enumerate(paras):
        if legend[i]:
            paras[i] = conv.convert(p)
    return "\n\n".join(paras)


def methods_from_master() -> str:
    pm = (NP / "paper.md").read_text()
    m = pm[pm.index("## Methods") + len("## Methods"):pm.index("## Declarations")].strip()
    m = m.replace("**Use of AI tools.**", "**Use of large language models.**")
    m = m.replace("For Watermelon (GEO GSE150949)", "For the PC9 osimertinib data (Watermelon system; GEO GSE150949)")
    m = m.replace("were taken unchanged from Supplementary Data 2 and 4 of Dai et al. (2024)",
                  "were taken unchanged from the files Supplementary Data 2 and 4 of the original study (Dai et al., 2024)")
    m = m.replace("Preranked GSEA (Subramanian et al., 2005; GSEApy, Fang et al., 2023)",
                  "Preranked GSEA (Subramanian et al., 2005) with GSEApy (Fang et al., 2023)")
    out = []
    for para in m.split("\n\n"):
        h = re.match(r"\*\*([^*]+?)\.\*\* ", para)
        if h:
            out.append(f"### {h.group(1)}")
            para = para[h.end():]
        out.append(para)
    m = "\n\n".join(out)
    m = m.replace("### Data\n\n", "### Data\n\nOnly publicly available, previously published data were analysed, so no ethics "
                  "approval or consent was required. ", 1)
    # statistics section required by the journal; every value below is stated elsewhere in Methods
    stats = ("### Statistics and reproducibility\n\nTests were two-sided unless stated otherwise. Classifier performance "
             "was summarised by AUROC on pooled out-of-fold predictions, and 95% confidence intervals came from "
             "family-level bootstrap resamples (500 for a single AUROC, 1,000 for the evaluation-only ΔAUROC interval "
             "and 200 refitting replicates for the intervals quoted in Results), so that sisters were never treated as "
             "independent observations. Label-shuffled nulls used 100 family-level permutations. Nested logistic "
             "models were compared with one-degree-of-freedom likelihood-ratio tests. Differential expression used "
             "Wilcoxon rank-sum tests within each sample, combined across the two replicates by Stouffer's method, "
             "with Benjamini–Hochberg correction; gene-set enrichment used 1,000 permutations. Copy-number "
             "enrichment used Fisher's exact test with Benjamini–Hochberg correction, survival associations Cox "
             "models with Benjamini–Hochberg correction over the 10 tests, and the patient cohort the Wilcoxon "
             "signed-rank test over 11 patients together with 200 expression-matched random gene sets. The "
             "bootstrap p-values for ΔAUROC are one-sided, as stated. No cells were excluded beyond those without a "
             "lineage label, and the random seed and all hyperparameters are fixed in the configuration file.")
    m = m.replace("### Software", stats + "\n\n### Software", 1)
    # number display equations
    n = [0]

    def eq(mm):
        n[0] += 1
        return f"$${mm.group(1).rstrip()} \\qquad ({n[0]})$$"
    m = re.sub(r"\$\$(.+?)\$\$", eq, m, flags=re.S)
    return m


END = """## Data availability

All data analysed are public: ReSisTrace (GEO GSE223003), the PC9 osimertinib lineage data (GSE150949), the triple-negative breast cancer study (GSE228382, with figshare https://doi.org/10.6084/m9.figshare.24787458), the second lineage system (GSE279162), the patient cohort (GSE165897) and TCGA-OV through UCSC Xena. All result tables underlying the figures and text, including full differential expression and gene-set enrichment results, are provided as Supplementary Data SDRANGE.

## Code availability

The code is available at https://github.com/rabeyanoor/SisFate under the MIT licence, and a release will be archived at Zenodo with a DOI on acceptance. The fitness-adjusted evaluation (control-arm baseline, size-matched ΔAUROC with a family-level bootstrap interval, family permutation null and sister ceiling) is packaged as a module, `persist.fitadj`, that takes plain arrays and any scikit-learn classifier. The repository contains one numbered script per analysis step, the configuration file (`configs/default.yaml`, which fixes the random seed and all hyperparameters), a locked Python environment (`uv.lock`; Python 3.12, NumPy 2.5, scikit-learn 1.9, Scanpy 1.12, PyTorch 2.14 CPU) and a single script (`scripts/run_all.sh`) that regenerates every result, figure and supplementary table from the public data on a laptop CPU; only the Geneformer and scGPT forward passes used a GPU (a Kaggle T4; the kernel scripts are included).

## References

REFLIST

## Acknowledgements

We thank the authors of the ReSisTrace, PC9 osimertinib, triple-negative breast cancer, multi-treatment melanoma and ovarian cancer patient studies for making their data publicly available, and The Cancer Genome Atlas Research Network. This research received no specific grant from any funding agency in the public, commercial or not-for-profit sectors.

## Author contributions

R.N. conceived the study, carried out all analyses and wrote the manuscript. K.J.R. contributed to the biological interpretation of the results. Both authors read and approved the final manuscript.

## Competing interests

The authors declare no competing interests.
"""


def main():
    draft = (NP / "ncomms_draft.md").read_text().strip()
    paper = draft + "\n\n## Methods\n\n" + methods_from_master() + "\n\n" + END
    # supplementary tables -> Supplementary Data N, numbered by first citation (main text, then supplement)
    paper = re.sub(r"Tables? S(\d+)", r"SD:S\1", paper)
    supp = (NP / "ncomms_supp_draft.md").read_text()
    supp = re.sub(r"Tables? S(\d+)", r"SD:S\1", supp)
    sd = []
    for s in re.findall(r"SD:S(\d+)", paper + "\n" + supp):
        if s not in sd:
            sd.append(s)
    remap = lambda t: re.sub(r"SD:S(\d+)", lambda m: f"Supplementary Data {sd.index(m.group(1)) + 1}", t)
    paper = paper.replace("SDRANGE", f"1–{len(sd)}")
    paper, supp = remap(paper), remap(supp)
    for t in ("paper", "supp"):
        v = paper if t == "paper" else supp
        v = re.sub(r"Fig\. S(\d)", r"Supplementary Fig. \1", v)
        v = v.replace("Supplementary Supplementary", "Supplementary")
        if t == "paper":
            paper = v
        else:
            supp = v

    conv = Numberer()
    body, end = paper.split("## References")
    body = number_in_order(body, conv)
    refs = "\n\n".join(f"{i + 1}. {entry(k)}" for i, k in enumerate(conv.order))
    paper = body + "## References" + end.replace("REFLIST", refs)
    assert len(conv.order) <= 70, len(conv.order)

    sconv = Numberer()
    supp = number_in_order(supp, sconv).rstrip() + "\n\n## Supplementary References\n\n" + \
        "\n\n".join(f"{i + 1}. {entry(k)}" for i, k in enumerate(sconv.order)) + "\n"
    leftover = CITE.findall(paper) + CITE.findall(supp)
    assert not leftover, leftover
    (NP / "ncomms_paper.md").write_text(paper)
    (NP / "ncomms_supplementary.md").write_text(supp)

    import pandas as pd
    src = NP / "Supplementary_Tables.xlsx"
    idx = pd.read_excel(src, sheet_name="index").set_index("sheet")
    names = {s.split("_")[0][1:]: s for s in idx.index}
    out = NP / "ncomms_supplementary_data"
    out.mkdir(exist_ok=True)
    legends = ["# Supplementary Data legends (for the cover letter)\n"]
    for i, s in enumerate(sd, 1):
        sheet = names[s]
        df = pd.read_excel(src, sheet_name=sheet)
        title = sheet.split("_", 1)[1]
        df.to_excel(out / f"Supplementary_Data_{i}.xlsx", sheet_name=title[:31], index=False)
        desc = re.sub(r"Fig\. S(\d)", r"Supplementary Fig. \1", idx.at[sheet, "description"])
        legends.append(f"**Supplementary Data {i}.** {desc}\n")
    missing = sorted(set(names) - set(sd), key=int)
    (out / "legends.md").write_text("\n".join(legends))
    print(f"{len(conv.order)} references, {len(sconv.order)} supplementary references, "
          f"{len(sd)} Supplementary Data files; tables never cited: {missing}")


if __name__ == "__main__":
    main()
