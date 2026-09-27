"""Pre-specified marker panel: drug-specific (beyond control) shifts of proliferation, arrest,
senescence, quiescence and reported persister genes. Reads the 08_interpret outputs; no new tests.

The panel was fixed before looking at these genes' results, to avoid picking markers after the fact.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.utils import load_config  # noqa: E402

PANEL = {
    "Proliferation / replication": ["MKI67", "TOP2A", "MCM2", "PCNA", "CCNB1", "E2F1", "CDK1"],
    "G1 arrest / CDK inhibitors": ["CDKN1A", "CDKN1B", "CDKN2A", "RB1", "TP53"],
    "Senescence / SASP": ["IL6", "CXCL8", "SERPINE1", "GLB1", "IGFBP3"],
    "Quiescence / dormancy": ["HES1", "NR2F1", "DYRK1A", "CDKN1C"],
    "Reported persister markers": ["KDM5A", "KDM5B", "ALDH1A1", "AXL", "NGFR", "CD44", "IGFBP7"],
}

ap = argparse.ArgumentParser()
ap.add_argument("--config")
args = ap.parse_args()
cfg = load_config(args.config)
d_int = Path(cfg["paths"]["results_dir"]) / "interpret"

rows = []
for arm in ["Carboplatin", "Olaparib", "NK"]:
    d = pd.read_csv(d_int / f"drug_vs_fitness_{arm}.csv").drop_duplicates("symbol").set_index("symbol")
    for cat, genes in PANEL.items():
        for g in genes:
            r = d.loc[g] if g in d.index else None
            rows.append({
                "category": cat, "gene": g, "arm": arm,
                "z_drug": None if r is None else r["z_drug"], "z_control": None if r is None else r["z_ctrl"],
                "z_diff": None if r is None else r["z_diff"], "padj_diff": None if r is None else r["padj_diff"],
                "class": "not among the 5,005 retained genes" if r is None else r["class"],
            })
df = pd.DataFrame(rows)
out = d_int / "marker_panel.csv"
df.to_csv(out, index=False)
print(out)
print(df.pivot_table(index=["category", "gene"], columns="arm", values="z_diff", sort=False).round(1).to_string())
