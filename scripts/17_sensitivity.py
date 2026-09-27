"""Sensitivity of the main results to the representation: Harmony, Pearson residuals, scVI.

Each representation replaces the 50-PC input of the PCA-logistic model; the within-arm AUROC and the
fitness analysis (06) are then recomputed exactly as before. `baseline` reproduces the main text.
  harmony   Harmony on the 50 PCs, batch = sample
  pearson   analytic Pearson residuals (theta = 100) on raw counts of the 2,000 HVGs, per sample, then PCA
  scvi      scVI latent space (30 dims) on raw HVG counts, batch = sample; library size is modelled

Run: uv run --with harmonypy --with scvi-tools python scripts/17_sensitivity.py
"""
import argparse
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import scanpy as sc
import scipy.sparse as sp
from sklearn.decomposition import PCA

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.fitness import fitness_analysis  # noqa: E402
from persist.runner import load_context  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--reps", nargs="+", default=["baseline", "harmony", "pearson", "scvi"])
ap.add_argument("--scvi-epochs", type=int, default=100)
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("sensitivity")
ctx = load_context(cfg, "keep")
obs = ctx.obs
hvg = ctx.adata.var_names[ctx.adata.var["highly_variable"]]
n_pcs = cfg["preprocess"]["n_pcs"]


def raw_hvg_counts() -> ad.AnnData:
    """Raw counts of the HVGs for every modelled cell, in ctx order (missing genes = 0)."""
    parts = []
    for s in obs["sample"].unique():
        a = ad.read_h5ad(Path(cfg["paths"]["processed_dir"]) / "samples" / f"{s}.h5ad")
        a = a[obs.index[obs["sample"] == s]]
        pos = hvg.get_indexer(a.var_names)
        m = pos >= 0
        X = sp.csc_matrix(a.X)[:, np.flatnonzero(m)]
        M = sp.csr_matrix((np.ones(m.sum(), np.float32), (np.arange(m.sum()), pos[m])), shape=(m.sum(), len(hvg)))
        parts.append(ad.AnnData(X=(X @ M).tocsr().astype(np.float32), obs=a.obs[[]].assign(sample=s),
                                var=pd.DataFrame(index=hvg)))
    out = ad.concat(parts)
    return out[obs.index].copy()


def rep_harmony() -> np.ndarray:
    import harmonypy
    Z = harmonypy.run_harmony(ctx.adata.obsm["X_pca"], obs[["sample"]], "sample", random_state=cfg["seed"]).Z_corr
    Z = np.asarray(Z)
    return (Z.T if Z.shape[0] != len(obs) else Z).astype(np.float32)


def rep_pearson(counts: ad.AnnData) -> np.ndarray:
    blocks = []
    for s in obs["sample"].unique():
        a = counts[counts.obs["sample"] == s].copy()
        sc.experimental.pp.normalize_pearson_residuals(a, theta=100)
        X = np.nan_to_num(np.asarray(a.X, dtype=np.float32))
        blocks.append(pd.DataFrame(X, index=a.obs_names))
    X = pd.concat(blocks).loc[obs.index].to_numpy()
    return PCA(n_components=n_pcs, random_state=cfg["seed"], svd_solver="randomized").fit_transform(X).astype(np.float32)


def rep_scvi(counts: ad.AnnData) -> np.ndarray:
    import scvi
    scvi.settings.seed = cfg["seed"]
    a = counts.copy()
    scvi.model.SCVI.setup_anndata(a, batch_key="sample")
    model = scvi.model.SCVI(a, n_latent=30)
    model.train(max_epochs=args.scvi_epochs, accelerator="cpu", early_stopping=True, enable_progress_bar=False)
    return model.get_latent_representation().astype(np.float32)


counts = raw_hvg_counts() if {"pearson", "scvi"} & set(args.reps) else None
rows = []
base_pca = ctx.feats["pca"]
for rep in args.reps:
    Z = {"baseline": lambda: base_pca, "harmony": rep_harmony,
         "pearson": lambda: rep_pearson(counts), "scvi": lambda: rep_scvi(counts)}[rep]()
    ctx.feats["pca"] = Z
    for arm in [a for a in cfg["data"]["arms"] if a != "Control"]:
        r = fitness_analysis(ctx, arm, "Control", "pca", cfg["seed"])
        r.update(representation=rep, n_dims=Z.shape[1], config_hash=cfg["_hash"])
        rows.append(r)
        log.info(f"{rep} {arm}: drug={r['auroc_drug_model_on_drug']:.3f} fitness={r['auroc_fitness_model_on_drug']:.3f} "
                 f"control={r['auroc_control_model_on_control']:.3f} spec_matched={r['specificity_index_size_matched']:.3f}")
ctx.feats["pca"] = base_pca

df = pd.DataFrame(rows)
out = Path(cfg["paths"]["results_dir"]) / "sensitivity_representations.csv"
df.to_csv(out, index=False)
cols = ["representation", "drug_arm", "auroc_drug_model_on_drug", "auroc_fitness_model_on_drug",
        "auroc_control_model_on_control", "specificity_index_size_matched", "auroc_drug_residual_on_drug"]
print(df[cols].round(3).to_string(index=False))
