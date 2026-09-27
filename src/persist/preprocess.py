"""Normalisation, cell-cycle scoring, gene selection, scaling and PCA for pre-treatment cells.

All steps here are label-free. Gene selection and PCA see every pre-treatment cell (transductive,
unsupervised); labels only enter at model-fitting time, inside each split.
"""
from __future__ import annotations

import anndata as ad
import numpy as np
import pandas as pd
import scanpy as sc
import scipy.sparse as sp
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from .genes import G2M_GENES, S_GENES


# "regress" removes cell cycle only; "regress_all" also removes sequencing depth and mitochondrial
# fraction, which differ between pre-resistant and pre-sensitive cells in every arm (label audit).
REGRESS_COVARIATES = {
    "regress": ["S_score", "G2M_score"],
    "regress_all": ["S_score", "G2M_score", "log_counts", "log_genes", "pct_mt"],
}
CC_MODES = ["keep", *REGRESS_COVARIATES]


def normalize_log(adata: ad.AnnData) -> None:
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)


def score_cell_cycle(adata: ad.AnnData, seed: int = 0) -> None:
    """Adds S_score, G2M_score, phase to obs. Expects log-normalised X and var['symbol']."""
    sym = adata.var["symbol"].values
    tmp = ad.AnnData(X=adata.X, obs=pd.DataFrame(index=adata.obs_names), var=pd.DataFrame(index=sym))
    tmp.var_names_make_unique()
    s = [g for g in S_GENES if g in tmp.var_names]
    g2m = [g for g in G2M_GENES if g in tmp.var_names]
    sc.tl.score_genes_cell_cycle(tmp, s_genes=s, g2m_genes=g2m, random_state=seed)
    for col in ["S_score", "G2M_score", "phase"]:
        adata.obs[col] = tmp.obs[col].values


def sample_hvg_rank(adata: ad.AnnData) -> pd.Series:
    """Per-sample normalised-dispersion rank (0 = most variable). Expects log-normalised X."""
    df = sc.pp.highly_variable_genes(adata, flavor="seurat", n_top_genes=2000, inplace=False)
    disp = pd.Series(np.asarray(df["dispersions_norm"]), index=adata.var_names).fillna(-np.inf)
    return disp.rank(ascending=False, method="first") - 1


def select_genes(ranks: pd.DataFrame, var: pd.DataFrame, detected: pd.Series, cfg: dict) -> tuple[list, list]:
    """Combine per-sample HVG ranks (median rank, like scanpy's batch_key logic)."""
    pp = cfg["preprocess"]
    ok = detected >= pp["min_cells_per_gene"]
    med = ranks.median(axis=1)[ok].sort_values()
    eligible = med.index
    if pp["exclude_mt_ribo_from_hvg"]:
        bad = var.loc[eligible, "mt"] | var.loc[eligible, "ribo"]
        eligible = eligible[~bad.values]
    hvg = list(eligible[: pp["n_hvg"]])
    keep = list(med.index[: pp["n_keep_genes"]])
    cc = var.index[var["symbol"].isin(S_GENES + G2M_GENES)].intersection(med.index)
    keep = list(dict.fromkeys(keep + hvg + list(cc)))
    return hvg, keep


def scale_features(X: np.ndarray, samples: np.ndarray, mode: str, clip: float = 10.0) -> np.ndarray:
    X = X.astype(np.float32, copy=True)
    groups = np.unique(samples) if mode == "per_sample" else [None]
    for g in groups:
        m = samples == g if g is not None else slice(None)
        mu = X[m].mean(0)
        sd = X[m].std(0)
        sd[sd == 0] = 1.0
        X[m] = (X[m] - mu) / sd
    np.clip(X, -clip, clip, out=X)
    return X


def regress_out(X: np.ndarray, covariates: np.ndarray, samples: np.ndarray) -> np.ndarray:
    """Residualise every feature on covariates (plus intercept) within each sample."""
    X = X.copy()
    for g in np.unique(samples):
        m = samples == g
        C = np.column_stack([np.ones(m.sum()), covariates[m]])
        beta, *_ = np.linalg.lstsq(C, X[m], rcond=None)
        X[m] -= (C @ beta).astype(np.float32)
    return X


def build_feature_space(adata: ad.AnnData, cfg: dict, cc_mode: str) -> None:
    """Fills obsm['X_hvg'] (scaled HVG expression) and obsm['X_pca'] for one cell-cycle mode."""
    pp = cfg["preprocess"]
    hvg = adata.var_names[adata.var["highly_variable"]]
    Xh = adata[:, hvg].X
    Xh = Xh.toarray() if sp.issparse(Xh) else np.asarray(Xh)
    samples = adata.obs["sample"].to_numpy()
    Xh = scale_features(Xh, samples, pp["scale"])
    if cc_mode in REGRESS_COVARIATES:
        obs = adata.obs
        cov = {
            "S_score": obs["S_score"], "G2M_score": obs["G2M_score"],
            "log_counts": np.log1p(obs["nCount_RNA"].astype(float)),
            "log_genes": np.log1p(obs["nFeature_RNA"].astype(float)), "pct_mt": obs["percent.mt"],
        }
        C = np.column_stack([np.asarray(cov[c], np.float32) for c in REGRESS_COVARIATES[cc_mode]])
        Xh = regress_out(Xh, C, samples)
    elif cc_mode != "keep":
        raise ValueError(f"unknown cc_mode {cc_mode}")
    pca = PCA(n_components=pp["n_pcs"], random_state=cfg["seed"], svd_solver="randomized")
    adata.obsm["X_hvg"] = Xh
    adata.obsm["X_pca"] = pca.fit_transform(Xh).astype(np.float32)
    adata.uns["pca_variance_ratio"] = pca.explained_variance_ratio_
    adata.uns["cc_mode"] = cc_mode
    # Coarse transcriptional-state clusters: proxy for subclone structure (InferCNV labels are not on GEO).
    km = KMeans(n_clusters=8, n_init=10, random_state=cfg["seed"])
    adata.obs["state_cluster"] = km.fit_predict(adata.obsm["X_pca"][:, :20]).astype(str)
