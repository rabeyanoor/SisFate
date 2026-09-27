"""Fetch metadata, abstract and (if open access) full text for the literature review from Europe PMC.
Each paper is located by exact title so nothing is taken from memory; results go to reference/lit/."""
import json, re, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).parent
TITLES = {
 "sharma2010": "A chromatin-mediated reversible drug-tolerant state in cancer cell subpopulations",
 "shaffer2017": "Rare cell variability and drug-induced reprogramming as a mode of cancer drug resistance",
 "hata2016": "Tumor cells can follow distinct evolutionary paths to become resistant to epidermal growth factor receptor inhibition",
 "ramirez2016": "Diverse drug-resistance mechanisms can emerge from drug-tolerant cancer persister cells",
 "marine2020": "Non-genetic mechanisms of therapeutic resistance in cancer",
 "shaffer2020": "Memory Sequencing Reveals Heritable Single-Cell Gene Expression Programs Associated with Distinct Cellular Behaviors",
 "emert2021": "Variability within rare cell states enables multiple paths toward drug resistance",
 "oren2021": "Cycling cancer persister cells arise from lineages with distinct programs",
 "rehman2021": "Colorectal cancer cells enter a diapause-like DTP state to survive chemotherapy",
 "fennell2022": "Non-genetic determinants of malignant clonal fitness at single-cell resolution",
 "goyal2023": "Diverse clonal fates emerge upon drug treatment of homogeneous cancer cells",
 "dai2024": "Tracing back primed resistance in cancer via sister cells",
 "pellecchia2024": "Single cell lineage tracing reveals clonal dynamics of anti-EGFR therapy resistance in triple negative breast cancer",
 "gutierrez2021": "Multifunctional barcoding with ClonMapper enables high-resolution study of clonal dynamics during tumor evolution and treatment",
 "weinreb2020": "Lineage tracing on transcriptional landscapes links state to fate during differentiation",
 "wagner2020": "Lineage tracing meets single-cell omics: opportunities and challenges",
 "spencer2009": "Non-genetic origins of cell-to-cell variability in TRAIL-induced apoptosis",
 "paek2016": "Cell-to-Cell Variation in p53 Dynamics Leads to Fractional Killing",
 "chen2022_scdeal": "Deep transfer learning of cancer drug responses by integrating bulk and single-cell RNA-seq data",
 "zheng2023_scad": "Enabling Single-Cell Drug Response Annotations from Bulk RNA-Seq Using SCAD",
 "fustero2021_beyondcell": "Beyondcell: targeting cancer therapeutic heterogeneity in single-cell RNA-seq data",
 "suphavilai2021_cadrres": "Predicting heterogeneity in clone-specific therapeutic vulnerabilities using single-cell transcriptomic signatures",
 "shen2026": "Predicting Pre-treatment Resistance or Post-treatment Effect? A Systematic Benchmarking of Single-Cell Drug Response Models",
 "patel2014_infercnv": "Single-cell RNA-seq highlights intratumoral heterogeneity in primary glioblastoma",
 "harmange2023": "Disrupting cellular memory to overcome drug resistance",
 "wang2022_cospar": "Cospar identifies early cell fate biases from single-cell transcriptomic and lineage information",
 "hamilton2017": None,
 "tirosh2016": "Dissecting the multicellular ecosystem of metastatic melanoma by single-cell RNA-seq",
}
API = "https://www.ebi.ac.uk/europepmc/webservices/rest/"

def get(url):
    for _ in range(3):
        try:
            return urllib.request.urlopen(url, timeout=60).read()
        except Exception as e:
            err = e; time.sleep(2)
    raise err

def norm(t): return re.sub(r"[^a-z0-9]", "", t.lower())

meta = {}
for key, title in TITLES.items():
    if not title: continue
    q = urllib.parse.urlencode({"query": f'TITLE:"{title}"', "format": "json", "resultType": "core", "pageSize": 10})
    res = json.loads(get(API + "search?" + q))["resultList"]["result"]
    res = [r for r in res if norm(r.get("title", "")).startswith(norm(title)[:60]) and "corrigendum" not in r.get("title","").lower()
           and "author correction" not in r.get("title","").lower()]
    if not res:
        print(f"{key}: NOT FOUND"); continue
    r = sorted(res, key=lambda r: (r.get("source") == "PPR", r.get("pubYear", "9999")))[0]
    j = r.get("journalInfo", {})
    m = {"key": key, "title": r["title"], "authors": r.get("authorString"), "journal": j.get("journal", {}).get("isoabbreviation") or r.get("bookOrReportDetails", {}).get("publisher"),
         "year": r.get("pubYear"), "volume": j.get("volume"), "pages": r.get("pageInfo"), "doi": r.get("doi"),
         "pmid": r.get("pmid"), "pmcid": r.get("pmcid"), "source": r.get("source"), "id": r.get("id"),
         "open_access": r.get("isOpenAccess"), "abstract": re.sub("<[^>]+>", "", r.get("abstractText") or "")}
    full = ""
    ft_id = m["pmcid"] or (m["id"] if m["source"] == "PPR" else None)
    if ft_id and m["open_access"] == "Y":
        try:
            x = get(API + f"{ft_id}/fullTextXML")
            root = ET.fromstring(x)
            body = root.find(".//body")
            if body is not None:
                full = "\n".join("".join(p.itertext()).strip() for p in body.iter() if p.tag in ("title", "p"))
        except Exception as e:
            print(key, "full text failed", e)
    (OUT / f"{key}.txt").write_text(f"{m['title']}\n{m['authors']}\n{m['journal']} {m['year']};{m['volume']}:{m['pages']} doi:{m['doi']}\n\nABSTRACT\n{m['abstract']}\n\nFULL TEXT\n{full}")
    m["full_text_chars"] = len(full)
    meta[key] = m
    print(f"{key}: {m['journal']} {m['year']} | OA={m['open_access']} | full={len(full)} | {m['title'][:70]}")
    time.sleep(0.3)
json.dump(meta, open(OUT / "bibliography.json", "w"), indent=1)
