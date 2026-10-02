"""Two biological claims of the original ReSisTrace study, re-examined against the untreated arm.

Dai et al. (2024) reported that (i) pre-resistant cells are marked by proteostatic and mRNA-surveillance
programmes (nonsense-mediated decay, translation, protein targeting to the ER, the unfolded protein response),
and (ii) pre-resistance signatures are negatively connected to a homologous-recombination-deficiency (HRD)
signature, which they read as HRD-like states priming sensitivity to olaparib and carboplatin; the NK arm
showed the strongest connection. Their own published tables are used here, unchanged:

  Supplementary Data 2 (41467_2024_45478_MOESM5_ESM.xlsx): per-gene log2 fold change, pre-resistant vs
      pre-sensitive, for each arm *including the untreated control*
  Supplementary Data 4 (41467_2024_45478_MOESM7_ESM.xlsx): HRD-vs-HRP log fold changes from TCGA and from the
      isogenic COV362 pair

For every arm, including the control, we compute
  (a) preranked GSEA (GSEApy, 1,000 permutations) of the GO terms named in their claim, on the log2 fold change;
  (b) the connectivity of the HRD signature: up- and down-sets (the 100 genes with the largest and smallest
      HRD-vs-HRP log fold change, adjusted p < 0.05, separately for TCGA and COV362), scored by preranked GSEA,
      connectivity = (NES_up - NES_down) / 2 when the two move in opposite directions and 0 otherwise,
      as in PharmacoGx connectivityScore(method = "fgsea"), which the original study used;
and the same after subtracting the control arm's fold change (their own "contrast" signature, variant 3).
A claim that holds as strongly in the control arm as in a drug arm describes growth fitness, not the drug.
The same analysis is repeated on our replicate-combined z-scores (scripts/08) as an independent pipeline.

Run: uv run --with openpyxl python scripts/35_published_claims.py
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.utils import ROOT, get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--n-top", type=int, default=100)
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("published_claims")
R = Path(cfg["paths"]["results_dir"])
SUPP = ROOT / "data" / "ref" / "dai2024_supp"
ARMS = {"Carboplatin": "Carbo", "Olaparib": "Olaparib", "NK": "NK", "Control": "Control"}
TERMS = ["nuclear-transcribed mRNA catabolic process, nonsense-mediated decay", "cytoplasmic translation",
         "protein targeting to ER", "translational initiation", "PERK-mediated unfolded protein response",
         "ribosome biogenesis"]


def go_sets():
    """GO Biological Process sets for the named terms (Enrichr library, cached)."""
    import json

    import gseapy as gp
    cache = Path(cfg["paths"]["ref_dir"]) / "GO_Biological_Process_2021.json"
    if cache.exists():
        lib = json.loads(cache.read_text())
    else:
        lib = gp.get_library("GO_Biological_Process_2021", organism="Human")
        cache.write_text(json.dumps(lib))
    out = {}
    for t in TERMS:
        hits = [k for k in lib if k.split(" (GO:")[0].lower() == t.lower()]
        if hits:
            out[t] = lib[hits[0]]
        else:
            log.warning(f"GO term not found: {t}")
    return out


def prerank(rnk: pd.Series, sets: dict, seed: int = 0) -> pd.DataFrame:
    import gseapy as gp
    rnk = rnk.dropna()
    rnk = rnk[~rnk.index.duplicated()].sort_values(ascending=False)
    res = gp.prerank(rnk=rnk, gene_sets=sets, permutation_num=1000, min_size=10, max_size=1000, seed=seed,
                     threads=4, outdir=None, verbose=False).res2d
    return res.set_index("Term")[["NES", "NOM p-val", "FDR q-val"]].astype(float)


def hrd_sets(hrd: pd.DataFrame, source: str) -> dict:
    d = hrd[[f"{source} HRD-HRP logFC", f"{source} HRD-HRP adjusted P value", "Gene symbol"]].dropna()
    d = d[d[f"{source} HRD-HRP adjusted P value"] < 0.05].drop_duplicates("Gene symbol")
    fc = d.set_index("Gene symbol")[f"{source} HRD-HRP logFC"]
    return {f"HRD_{source}_up": fc[fc > 0].nlargest(args.n_top).index.tolist(),
            f"HRD_{source}_down": fc[fc < 0].nsmallest(args.n_top).index.tolist()}


dai = pd.read_excel(SUPP / "41467_2024_45478_MOESM5_ESM.xlsx", sheet_name="Sheet1")
hrd = pd.read_excel(SUPP / "41467_2024_45478_MOESM7_ESM.xlsx", sheet_name="Sheet1")
sets = go_sets()
for src in ["TCGA", "COV362"]:
    s = hrd_sets(hrd, src)
    log.info(f"HRD {src}: {len(s[f'HRD_{src}_up'])} up, {len(s[f'HRD_{src}_down'])} down genes")
    sets.update(s)

# ranked lists: their log2FC per arm, their control-subtracted contrast, and our replicate-combined z-scores
ranks = {}
lfc = dai.drop_duplicates("symbol").set_index("symbol")
for arm, key in ARMS.items():
    ranks[("published_log2FC", arm)] = lfc[f"{key}_log2FC_preR_preS"]
    if arm != "Control":
        ranks[("published_minus_control", arm)] = lfc[f"{key}_log2FC_preR_preS"] - lfc["Control_log2FC_preR_preS"]
for arm in ARMS:
    z = pd.read_csv(R / "interpret" / f"de_{arm}.csv", index_col=0).drop_duplicates("symbol").set_index("symbol")["z"]
    ranks[("our_z", arm)] = z
    if arm != "Control":
        zc = pd.read_csv(R / "interpret" / "de_Control.csv", index_col=0).drop_duplicates("symbol").set_index("symbol")["z"]
        g = z.index.intersection(zc.index)
        ranks[("our_z_minus_control", arm)] = (z[g] - zc[g]) / np.sqrt(2)

rows = []
for (source, arm), rnk in ranks.items():
    res = prerank(rnk, sets, cfg["seed"])
    for term in res.index:
        rows.append({"source": source, "arm": arm, "gene_set": term, **res.loc[term].to_dict()})
    for src in ["TCGA", "COV362"]:
        up, dn = f"HRD_{src}_up", f"HRD_{src}_down"
        if up in res.index and dn in res.index:
            nu, nd = res.loc[up, "NES"], res.loc[dn, "NES"]
            # as in CoreGx/PharmacoGx connectivityScore(method = "fgsea"), which the original study used:
            # (NES_up - NES_down) / 2 when the two sets move in opposite directions, otherwise 0
            rows.append({"source": source, "arm": arm, "gene_set": f"HRD_{src}_connectivity",
                         "NES": (nu - nd) / 2 if np.sign(nu) != np.sign(nd) else 0.0,
                         "NOM p-val": np.nan, "FDR q-val": np.nan})
    log.info(f"{source} {arm}: done")

T = pd.DataFrame(rows)
T.to_csv(R / "published_claims.csv", index=False)
wide = T.pivot_table(index=["source", "gene_set"], columns="arm", values="NES")[list(ARMS)]
print(wide.round(2).to_string())
