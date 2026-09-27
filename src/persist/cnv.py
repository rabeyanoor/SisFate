"""Copy-number subclones inferred from expression (infercnvpy), as a check on the subclone confound.

Dai et al. (2024) reported that InferCNV subclone A was enriched among pre-resistant cells in every
arm, but per-cell subclone calls are not public. We re-derive CNV profiles with infercnvpy:
  * each sample is run separately (memory) against one fixed reference panel of cells drawn from all
    pre-treatment samples, so profiles are on a common scale;
  * profiles are pooled, reduced with PCA and clustered with k-means.
The clusters are then tested for the published enrichment before being used as a confound.
"""
from __future__ import annotations

from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import scanpy as sc


def gene_positions(path: Path) -> pd.DataFrame:
    pos = pd.read_csv(path, sep="\t", header=None, names=["ensembl", "chromosome", "start", "end"])
    pos = pos[pos["chromosome"].isin([f"chr{c}" for c in list(range(1, 23)) + ["X"]])]
    return pos.drop_duplicates("ensembl").set_index("ensembl")


def reference_panel(files: list[Path], genes: pd.Index, n_per_sample: int, seed: int) -> ad.AnnData:
    rng = np.random.default_rng(seed)
    parts = []
    for f in files:
        a = ad.read_h5ad(f)
        a = a[rng.choice(a.n_obs, min(n_per_sample, a.n_obs), replace=False), genes].copy()
        parts.append(a)
    ref = ad.concat(parts)
    ref.obs_names = [f"ref:{c}" for c in ref.obs_names]
    return ref


def sample_cnv(sample_file: Path, ref: ad.AnnData, genes: pd.Index, pos: pd.DataFrame,
               window: int = 100, step: int = 10) -> tuple[pd.Index, np.ndarray, dict]:
    import infercnvpy as cnv

    a = ad.read_h5ad(sample_file)[:, genes].copy()
    a.obs_names = a.obs_names.astype(str)
    both = ad.concat([a, ref], label="group", keys=["query", "ref"])
    both.var = pos.loc[genes].copy()
    both.var["chromosome"] = both.var["chromosome"].astype(str)
    sc.pp.normalize_total(both, target_sum=1e4)
    sc.pp.log1p(both)
    cnv.tl.infercnv(both, reference_key="group", reference_cat=["ref"], window_size=window, step=step,
                    exclude_chromosomes=None, n_jobs=2)
    X = both.obsm["X_cnv"]
    X = X.toarray() if hasattr(X, "toarray") else np.asarray(X)
    q = (both.obs["group"] == "query").to_numpy()
    return both.obs_names[q], X[q].astype(np.float32), both.uns["cnv"]["chr_pos"]
