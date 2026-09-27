"""Sanity-check labels against the paper and summarise lineage structure (step D of the plan)."""
import argparse
import sys
from pathlib import Path

import anndata as ad
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.labels import sister_pairs  # noqa: E402
from persist.runner import processed_path  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

PAPER = {"pre-sensitive": 29540, "pre-resistant": 3102}  # Dai et al. 2024, Fig. 2 legend

ap = argparse.ArgumentParser()
ap.add_argument("--config")
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("audit")
obs = ad.read_h5ad(processed_path(cfg), backed="r").obs.copy()

rows = []
for s, d in obs.groupby("sample", observed=True):
    fam = d.loc[d["labeled"], "lineage_group"].astype(str).value_counts()
    rows.append({
        "sample": s, "n_cells": len(d), "n_unlabeled": int((~d["labeled"]).sum()),
        "n_pos": int((d["y"] == 1).sum()), "n_neg": int((d["y"] == 0).sum()),
        "prevalence": (d["y"] == 1).sum() / d["labeled"].sum(),
        "n_families": len(fam), "n_multi_cell_families": int((fam > 1).sum()),
        "n_pre_sister_pairs": len(sister_pairs(d)),
        "pct_G2M": (d["phase"] == "G2M").mean(),
    })
tab = pd.DataFrame(rows)
tab.to_csv(Path(cfg["paths"]["results_dir"]) / "label_audit.csv", index=False)
print(tab.to_string(index=False, float_format="%.3f"))

counts = obs["drugSens"].value_counts()
for k, v in PAPER.items():
    status = "OK" if counts.get(k, 0) == v else "MISMATCH"
    log.info(f"{k}: ours={counts.get(k, 0)} paper={v} -> {status}")

# label concordance inside pre-treatment families (should be 1.0 by construction)
fam = obs[obs["labeled"]].groupby("lineage_group", observed=True)["y"].nunique()
log.info(f"families with discordant labels: {(fam > 1).sum()} / {len(fam)}")

# does labeling depend on cycle phase / depth? (first look at confounds)
lab = obs[obs["labeled"]]
print("\nprevalence by arm x phase:")
print(pd.crosstab(lab["arm"], lab["phase"], values=lab["y"], aggfunc="mean").round(3))
print("\nmedian nCount_RNA by label:")
print(lab.groupby(["arm", "y"], observed=True)["nCount_RNA"].median().unstack().round(0))
