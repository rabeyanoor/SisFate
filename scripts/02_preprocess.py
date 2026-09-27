"""Pre-treatment cells -> one AnnData with labels, lineage groups, cell-cycle scores, HVG and PCA.

Two passes over the per-sample files keep peak memory low (~2-3 GB):
  pass 1  normalise, score cell cycle, rank HVGs per sample
  pass 2  re-normalise, subset to kept genes, concatenate
Writes data/processed/pre_<cc_mode>.h5ad for every cc_mode requested.
"""
import argparse
import gc
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.genes import annotate_symbols  # noqa: E402
from persist.io import align_genes  # noqa: E402
from persist.labels import add_labels  # noqa: E402
from persist.preprocess import build_feature_space, normalize_log, sample_hvg_rank, score_cell_cycle, select_genes  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--cc-modes", nargs="+", default=["keep", "regress", "regress_all"])
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("preprocess")
pp = cfg["preprocess"]

files = sorted((Path(cfg["paths"]["processed_dir"]) / "samples").glob("*_pre.h5ad"))
files = [f for f in files if f.stem.split("_")[0] in cfg["data"]["arms"]]
assert files, "run scripts/01_build_anndata.py first"

# the authors filtered genes per sample -> work on the union, missing genes = 0 counts
genes = pd.Index(sorted(set().union(*(ad.read_h5ad(f, backed="r").var_names for f in files))))
var = annotate_symbols(pd.DataFrame({"ensembl": genes}, index=genes), cfg["paths"]["ref_dir"])
log.info(f"{len(genes)} genes in the union of {len(files)} samples")

ranks, detected, obs_list = {}, None, []
for f in files:
    a = align_genes(ad.read_h5ad(f), genes)
    a.var = var.copy()
    if pp["max_pct_mt"] is not None:
        a = a[a.obs["percent.mt"] < pp["max_pct_mt"]].copy()
    det = pd.Series(np.asarray((a.X > 0).sum(0)).ravel(), index=a.var_names)
    detected = det if detected is None else detected + det
    normalize_log(a)
    score_cell_cycle(a, cfg["seed"])
    ranks[f.stem] = sample_hvg_rank(a)
    obs_list.append(a.obs)
    log.info(f"pass1 {f.stem}: {a.n_obs} cells; phase {a.obs['phase'].value_counts().to_dict()}")
    del a
    gc.collect()

hvg, keep = select_genes(pd.DataFrame(ranks), var, detected, cfg)
log.info(f"{len(hvg)} HVGs, {len(keep)} genes kept")

parts = []
for f, obs in zip(files, obs_list):
    a = align_genes(ad.read_h5ad(f), genes)
    a = a[obs.index].copy()
    a.var = var.copy()
    normalize_log(a)
    a = a[:, keep].copy()
    a.obs = obs
    parts.append(a)
    gc.collect()
adata = ad.concat(parts, merge="first")
del parts
gc.collect()
adata.var = var.loc[keep].copy()
adata.var["highly_variable"] = adata.var_names.isin(hvg)
adata.obs = add_labels(adata.obs, cfg["labels"]["positive"], cfg["labels"]["negative"])
for col in ["sample", "arm", "phase", "drugSens", "timepoint", "gsm", "orig.ident"]:
    if col in adata.obs:
        adata.obs[col] = adata.obs[col].astype(str)
adata.obs["lineage_group"] = adata.obs["lineage_group"].astype(str)
log.info(f"combined: {adata.n_obs} cells x {adata.n_vars} genes; labels {adata.obs['drugSens'].value_counts(dropna=False).to_dict()}")

for mode in args.cc_modes:
    build_feature_space(adata, cfg, mode)
    out = Path(cfg["paths"]["processed_dir"]) / f"pre_{mode}.h5ad"
    adata.write_h5ad(out, compression="gzip")
    log.info(f"wrote {out} (PC1-5 var ratio {np.round(adata.uns['pca_variance_ratio'][:5], 3).tolist()})")
