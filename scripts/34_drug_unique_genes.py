"""Which genes carry the part of the signal that is unique to one drug?

scripts/33 shows that, at equal training size, a drug arm's own model beats a model trained on the other drug
arms. Here the same contrast is made gene by gene. For drug arm k, with replicate-combined Wilcoxon z-scores
from scripts/08 (pre-resistant vs pre-sensitive, within sample),

    z_unique_k = (z_k - mean(z_j, j != k)) / sqrt(1 + 1/2)

which is a standard normal under the null if the three arms' z-scores are independent (they come from
different cells). Genes are called drug-unique at FDR < 0.05 with the same sign in both replicates of arm k.
Preranked GSEA on MSigDB Hallmark uses z_unique_k.

Hypotheses fixed before looking at these results (2026-10-02):
  H1  the olaparib-unique and carboplatin-unique contrasts are enriched for HALLMARK_DNA_REPAIR (both drugs act
      through DNA damage; olaparib through PARP and homologous recombination);
  H2  the NK-unique contrast is enriched for interferon-gamma response or allograft rejection (NK killing
      depends on antigen presentation and immune ligands).
Everything else is reported as exploratory.

Run: python scripts/34_drug_unique_genes.py   (after scripts/08_interpret.py)
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.interpret import TECHNICAL, hallmark_gsea  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("drug_unique")
R = Path(cfg["paths"]["results_dir"])
I = R / "interpret"
FDR = cfg["interpret"]["fdr"]
DRUGS = ["Carboplatin", "Olaparib", "NK"]
PRESPECIFIED = {"Carboplatin": ["DNA Repair"], "Olaparib": ["DNA Repair"],
                "NK": ["Interferon Gamma Response", "Allograft Rejection"]}

de = {k: pd.read_csv(I / f"de_{k}.csv", index_col=0) for k in DRUGS}
genes = sorted(set.intersection(*(set(d.index) for d in de.values())))
summary, tests = [], []
for k in DRUGS:
    others = [j for j in DRUGS if j != k]
    d = de[k].loc[genes]
    zu = (d["z"] - np.mean([de[j].loc[genes, "z"] for j in others], axis=0)) / np.sqrt(1.5)
    reps = d[[c for c in d.columns if c.startswith("z_") and c != "z"]]
    t = pd.DataFrame({"symbol": d["symbol"], "z_drug": d["z"], "z_unique": zu,
                      "consistent": np.sign(reps).nunique(axis=1) == 1})
    t["padj_unique"] = stats.false_discovery_control(2 * stats.norm.sf(t["z_unique"].abs()))
    t = t[~t["symbol"].astype(str).str.match(TECHNICAL)]
    t["unique"] = (t["padj_unique"] < FDR) & t["consistent"] & (np.sign(t["z_unique"]) == np.sign(t["z_drug"]))
    t.sort_values("z_unique", ascending=False).to_csv(I / f"drug_unique_{k}.csv")
    g = hallmark_gsea(t, "z_unique", cfg["paths"]["ref_dir"], cfg["seed"])
    g.to_csv(I / f"gsea_hallmark_unique_{k}.csv", index=False)
    up = t[t["unique"] & (t["z_unique"] > 0)].nlargest(10, "z_unique")["symbol"].tolist()
    dn = t[t["unique"] & (t["z_unique"] < 0)].nsmallest(10, "z_unique")["symbol"].tolist()
    sig = g[g["FDR q-val"].astype(float) < 0.05]
    summary.append({"arm": k, "n_genes": len(t), "n_unique": int(t["unique"].sum()),
                    "n_unique_up": int((t["unique"] & (t["z_unique"] > 0)).sum()),
                    "n_unique_down": int((t["unique"] & (t["z_unique"] < 0)).sum()),
                    "top_up": ";".join(up), "top_down": ";".join(dn),
                    "n_hallmark_fdr05": len(sig),
                    "hallmark_up": ";".join(sig[sig["NES"].astype(float) > 0]["Term"]),
                    "hallmark_down": ";".join(sig[sig["NES"].astype(float) < 0]["Term"])})
    for term in PRESPECIFIED[k]:
        row = g[g["Term"] == term]
        tests.append({"arm": k, "term": term, "found": len(row) == 1,
                      "NES": float(row["NES"].iloc[0]) if len(row) else np.nan,
                      "nom_p": float(row["NOM p-val"].iloc[0]) if len(row) else np.nan,
                      "fdr": float(row["FDR q-val"].iloc[0]) if len(row) else np.nan})
    log.info(f"{k}: {summary[-1]['n_unique']} drug-unique genes; Hallmark FDR<0.05 up "
             f"{summary[-1]['hallmark_up'] or '-'} | down {summary[-1]['hallmark_down'] or '-'}")

S = pd.DataFrame(summary)
T = pd.DataFrame(tests)
# the pre-specified tests are corrected among themselves (Benjamini-Hochberg over the four)
T["bh_prespecified"] = stats.false_discovery_control(T["nom_p"].clip(lower=1e-4).to_numpy())
S.to_csv(R / "drug_unique_summary.csv", index=False)
T.to_csv(R / "drug_unique_prespecified.csv", index=False)
print(S.drop(columns=["top_up", "top_down"]).to_string(index=False))
print(T.round(4).to_string(index=False))
