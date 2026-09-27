"""External validation on Watermelon (Oren et al. Nature 2021; GEO GSE150949; PC9 + osimertinib).

Labels are clone-level: a day-0 cell is 'persister-lineage' if its lineage barcode is observed in any
day-14 sample ('cycling' variant: in a 14_high sample, the actively-proliferating persisters).
Large clones are more likely to be re-sampled at day 14 by chance, so day-0 clone size is reported
as its own baseline and a singleton-only subset is evaluated too.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

WM_META = "GSE150949_metaData_with_lineage.txt.gz"
WM_COUNTS = "GSE150949_pc9_count_matrix.csv.gz"


def load_watermelon_day0(wm_dir: Path, chunk: int = 2000):
    """Returns (counts cells x genes CSR, genes, obs) for barcoded day-0 cells, with labels."""
    meta = pd.read_csv(Path(wm_dir) / WM_META, sep="\t")
    meta.index = meta.index.astype(str)
    has = meta["lineage_barcode"].notna()
    d14 = meta[(meta["time_point"] == 14) & has]
    persist_bc = set(d14["lineage_barcode"])
    cycling_bc = set(d14.loc[d14["sample_type"].astype(str).str.endswith("high"), "lineage_barcode"])

    obs = meta[(meta["time_point"] == 0) & has].copy()
    obs["clone_size_d0"] = obs.groupby("lineage_barcode")["lineage_barcode"].transform("size")
    obs["y_persister"] = obs["lineage_barcode"].isin(persist_bc).astype(int)
    obs["y_cycling"] = obs["lineage_barcode"].isin(cycling_bc).astype(int)

    path = Path(wm_dir) / WM_COUNTS
    header = pd.read_csv(path, nrows=0).columns[1:]
    pos = header.get_indexer(obs.index)
    if (pos < 0).any():
        raise ValueError(f"{(pos < 0).sum()} day-0 cells missing from the count matrix")
    blocks, genes = [], []
    # positional selection: column 0 holds gene symbols, cell j sits at column j + 1
    for part in pd.read_csv(path, usecols=[0, *(pos + 1)], index_col=0, chunksize=chunk):
        part = part[list(obs.index)]
        genes.extend(part.index.astype(str))
        blocks.append(sp.csr_matrix(part.to_numpy(np.float32)))
    X = sp.vstack(blocks).T.tocsr()
    return X, pd.Index(genes), obs


def lognorm(X: sp.csr_matrix) -> sp.csr_matrix:
    lib = np.asarray(X.sum(1)).ravel()
    lib[lib == 0] = 1
    Y = sp.diags(1e4 / lib) @ X
    Y.data = np.log1p(Y.data)
    return Y.tocsr()


def zscore(X: np.ndarray) -> np.ndarray:
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1
    return np.clip((X - mu) / sd, -10, 10).astype(np.float32)


def load_tnbc_day0(export_dir: Path):
    """Pellecchia et al. 2024 (GSE228382 / figshare 24787458) MDA-MB-468 + afatinib, exported by export_seurat.R.

    Day-0 cells are the untreated CTR01/CTR02 samples. `DTPE_lineages` marks lineages found among the
    drug-tolerant expanded persisters after 40 days of afatinib (the authors' retrospective label).
    """
    import scipy.io

    d = Path(export_dir)
    meta = pd.read_csv(d / "meta.csv.gz")
    meta = meta.loc[:, ~meta.columns.duplicated()].set_index("cell")
    genes = pd.Index(pd.read_csv(d / "genes.csv")["gene"].astype(str))
    cells = pd.read_csv(d / "cells.csv")["cell"].astype(str).to_numpy()
    X = scipy.io.mmread(d / "counts.mtx.gz").T.tocsr().astype(np.float32)
    keep = meta.loc[cells, "condition"].eq("CTRL").to_numpy() & meta.loc[cells, "linageBC"].notna().to_numpy()
    obs = meta.loc[cells[keep]].copy()
    obs["lineage_barcode"] = obs["linageBC"].astype(str)
    obs["clone_size_d0"] = obs.groupby("lineage_barcode")["lineage_barcode"].transform("size")
    obs["y_persister"] = obs["DTPE_lineages"].astype(str).str.upper().eq("TRUE").astype(int)
    obs["nUMI"], obs["nGene"], obs["percent.mito"] = obs["nCount_RNA"], obs["nFeature_RNA"], obs["percent.mt"]
    return X[keep], genes, obs


def run_external(name: str, Xl: sp.csr_matrix, genes: pd.Index, obs: pd.DataFrame, labels: list[str],
                 ctx, cfg: dict, log) -> pd.DataFrame:
    """(a) lineage-grouped CV inside the external set; (b) zero-shot transfer of ReSisTrace models."""
    from sklearn.decomposition import PCA
    from sklearn.model_selection import StratifiedGroupKFold

    from .metrics import evaluate
    from .models.baselines import logistic
    from .preprocess import scale_features

    C = cfg["baselines"]["logistic_C"]
    var = ctx.adata.var
    hvg = var[var["highly_variable"]]
    # external matrices come keyed either by Ensembl id (TNBC) or by symbol (Watermelon)
    key = pd.Series(hvg.index, index=hvg.index) if str(genes[0]).startswith("ENSG") else hvg["symbol"]
    ok = key.isin(genes) & ~key.duplicated()
    hvg, key = hvg[ok.to_numpy()], key[ok]
    log.info(f"{name}: {len(hvg)} of {int(var['highly_variable'].sum())} ReSisTrace HVGs present")
    X_ext = zscore(Xl[:, genes.get_indexer(key)].toarray())
    rs = ctx.adata[:, hvg.index].X
    X_rs = scale_features(rs.toarray() if hasattr(rs, "toarray") else np.asarray(rs), ctx.samples, "per_sample")

    groups = obs["lineage_barcode"].to_numpy()
    cov = np.column_stack([np.log1p(obs["nUMI"]), np.log1p(obs["nGene"]), obs["percent.mito"]]).astype(np.float32)
    clone = np.log(obs["clone_size_d0"].to_numpy(float))[:, None]
    pca = PCA(min(50, X_ext.shape[1] - 1), random_state=cfg["seed"]).fit_transform(X_ext).astype(np.float32)
    feature_sets = {"clone_size": clone, "covariates": cov, "pca": pca, "pca+clone_size": np.hstack([pca, clone])}
    subsets = {"all": np.ones(len(obs), bool), "singleton": obs["clone_size_d0"].to_numpy() == 1}

    rows = []
    for label in labels:
        y = obs[label].to_numpy()
        for sub_name, m in subsets.items():
            idx = np.flatnonzero(m)
            if y[idx].sum() < 10 or (1 - y[idx]).sum() < 10:
                continue
            for fname, F in feature_sets.items():
                if sub_name == "singleton" and "clone" in fname:  # clone size is constant there
                    continue
                oof = np.zeros(len(idx))
                skf = StratifiedGroupKFold(cfg["splits"]["n_folds"], shuffle=True, random_state=cfg["seed"])
                for tr, te in skf.split(idx, y[idx], groups[idx]):
                    oof[te], _ = logistic(F[idx[tr]], y[idx[tr]], F[idx[te]], C, cfg["seed"])
                rows.append({"dataset": name, "analysis": "within_external", "label": label, "subset": sub_name,
                             "model": fname, **evaluate(y[idx], oof, groups[idx], n_boot=300, seed=cfg["seed"])})
            for arm in cfg["data"]["arms"] + ["all_drugs"]:
                arms = [a for a in cfg["data"]["arms"] if a != "Control"] if arm == "all_drugs" else [arm]
                tr = ctx.obs["labeled"].to_numpy() & ctx.obs["arm"].isin(arms).to_numpy()
                s, _ = logistic(X_rs[tr], ctx.y[tr], X_ext[idx], C, cfg["seed"])
                rows.append({"dataset": name, "analysis": "transfer_from_resistrace", "label": label,
                             "subset": sub_name, "model": f"trained_on_{arm}",
                             **evaluate(y[idx], s, groups[idx], n_boot=300, seed=cfg["seed"])})
    return pd.DataFrame(rows)
