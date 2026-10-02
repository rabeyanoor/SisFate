"""Export the analysed data as plain CSV files anyone can open, in data_view/.

The processed data live in .h5ad (binary HDF5) files of several hundred MB, and data/ is not in the repository
because GEO already hosts it and it is far above GitHub's file-size limit. This script writes small, readable
tables instead: one row per pre-treatment cell with its label, family, quality metrics, a 2-D map and the
scores of the main models, plus per-sample and per-family summaries and the marker genes.

Every column is copied or computed from data/processed and results/preds; nothing is re-fitted here except
the UMAP layout and the label-free density score (no labels used for either).

Run: python scripts/32_export_data_view.py   (after 02_preprocess.py and 04_baselines.py)
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scanpy as sc
from sklearn.neighbors import NearestNeighbors

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("data_view")
ROOT = Path(__file__).resolve().parents[1]
R = Path(cfg["paths"]["results_dir"])
OUT = ROOT / "data_view"
OUT.mkdir(exist_ok=True)

MARKERS = ["MKI67", "TOP2A", "CDK1", "PCNA", "MCM2", "E2F1", "CCND1", "CDKN1A", "CDKN1B", "CDKN1C", "CD44",
           "IGFBP2", "IGFBP7", "IGF2", "IGF2BP1", "MYC", "SOX2", "AXL", "NT5E", "IL6", "CXCL8", "SERPINE1"]

a = sc.read_h5ad(ROOT / "data" / "processed" / "pre_keep.h5ad")
obs = a.obs
cells = pd.DataFrame({
    "cell_id": obs.index.str.split(":").str[1],
    "sample": obs["sample"].str.replace("_pre", "", regex=False).to_numpy(),
    "arm": obs["arm"].to_numpy(),
    "replicate": obs["replicate"].to_numpy(),
    "label": obs["drugSens"].fillna("no lineage label").to_numpy(),
    "family": obs["lineage_group"].to_numpy(),
    "n_umi": obs["nCount_RNA"].to_numpy(),
    "n_genes": obs["nFeature_RNA"].to_numpy(),
    "percent_mito": obs["percent.mt"].round(3).to_numpy(),
    "s_score": obs["S_score"].round(4).to_numpy(),
    "g2m_score": obs["G2M_score"].round(4).to_numpy(),
    "phase": obs["phase"].to_numpy(),
}, index=obs.index)
fam_size = cells.loc[cells["label"] != "no lineage label"].groupby("family").size()
cells["family_size"] = cells["family"].map(fam_size).fillna(0).astype(int)

# 2-D map for looking at the data (UMAP on the same 50 principal components the models use; no labels)
log.info("UMAP")
sc.pp.neighbors(a, n_neighbors=15, use_rep="X_pca", random_state=0)
sc.tl.umap(a, random_state=0)
cells["umap_1"], cells["umap_2"] = np.round(a.obsm["X_umap"][:, 0], 3), np.round(a.obsm["X_umap"][:, 1], 3)
for k in range(5):
    cells[f"pc_{k + 1}"] = np.round(a.obsm["X_pca"][:, k], 4)

# label-free density score, exactly as in scripts/15_typicality.py
X = a.obsm["X_pca"]
dens = np.zeros(len(X))
for s in np.unique(obs["sample"]):
    m = np.flatnonzero(obs["sample"].to_numpy() == s)
    d, _ = NearestNeighbors(n_neighbors=16).fit(X[m]).kneighbors(X[m])
    dens[m] = -d[:, 1:].mean(1)
cells["density_score"] = np.round(dens, 4)

# model scores saved by scripts/04_baselines.py
within = pd.read_csv(R / "preds" / "baselines_keep_within_pca_logreg.csv.gz")
within = within[(~within["shuffled"]) & (within["seed"] == 0)].drop_duplicates("cell").set_index("cell")
cells["drug_arm_model_score"] = within["score"].reindex(cells.index).round(5)
cross = pd.read_csv(R / "preds" / "baselines_keep_cross_arm.csv.gz")
cross = cross[(cross["model"] == "pca_logreg") & (cross["train"] == "Control") & (~cross["shuffled"])]
fit = cross.drop_duplicates("cell").set_index("cell")["score"]
# control cells get their own out-of-fold score from the control model, so the column is the fitness score
cells["fitness_model_score"] = fit.reindex(cells.index).fillna(
    cells["drug_arm_model_score"].where(cells["arm"] == "Control")).round(5)
cells.loc[cells["arm"] == "Control", "drug_arm_model_score"] = np.nan

cells.to_csv(OUT / "cells.csv", index=False)
log.info(f"cells.csv: {cells.shape}")

# marker genes, log-normalised counts per 10,000
genes = [g for g in MARKERS if g in set(a.var["symbol"])]
idx = [int(np.flatnonzero(a.var["symbol"].to_numpy() == g)[0]) for g in genes]
M = a.X[:, idx]
M = M.toarray() if hasattr(M, "toarray") else np.asarray(M)
mk = pd.DataFrame(np.round(M, 4), columns=genes)
mk.insert(0, "cell_id", cells["cell_id"].to_numpy())
mk.insert(1, "sample", cells["sample"].to_numpy())
mk.to_csv(OUT / "marker_genes.csv", index=False)

lab = cells[cells["label"] != "no lineage label"]
samp = cells.groupby("sample").agg(arm=("arm", "first"), cells=("cell_id", "size"),
                                   median_umi=("n_umi", "median"), median_genes=("n_genes", "median"))
samp["no_lineage_label"] = cells[cells["label"] == "no lineage label"].groupby("sample").size()
samp["pre_sensitive"] = lab[lab["label"] == "pre-sensitive"].groupby("sample").size()
samp["pre_resistant"] = lab[lab["label"] == "pre-resistant"].groupby("sample").size()
samp["percent_pre_resistant"] = (100 * samp["pre_resistant"] / (samp["pre_resistant"] + samp["pre_sensitive"])).round(2)
samp["families"] = lab.groupby("sample")["family"].nunique()
samp.reset_index().to_csv(OUT / "samples.csv", index=False)

fam = lab.groupby("family").agg(sample=("sample", "first"), arm=("arm", "first"), n_cells=("cell_id", "size"),
                                label=("label", "first"), n_labels=("label", "nunique"))
fam.reset_index().to_csv(OUT / "families.csv", index=False)
print(samp.to_string())
print(f"families: {len(fam)}, discordant: {int((fam['n_labels'] > 1).sum())}")
