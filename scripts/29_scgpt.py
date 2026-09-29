"""A second single-cell foundation model: does scGPT recover more signal than 50 principal components?

scGPT (Cui et al., 2024) is used through its whole-human checkpoint, as a frozen feature extractor, exactly as
Geneformer is in scripts/21_geneformer.py. The input is the raw counts of the 5,005 genes stored for every
pre-treatment cell (the most variable genes; see scripts/02_preprocess.py). The cell embedding is scGPT's own
<cls> cell embedding. Embeddings are z-scored within each sample and then used like the principal components:
within-arm grouped CV and the fitness analysis.

Three steps, so the transformer can run on a GPU elsewhere (a Kaggle T4; see kaggle/scgpt/):
  export   raw counts + gene symbols         -> data/processed/scgpt/counts.npz        (CPU, minutes)
  embed    run the model                     -> data/processed/scgpt/emb_scgpt_human.npy (GPU; kaggle/scgpt/embed.py)
  analyze  fitness analysis on embeddings    -> results/sensitivity_representations.csv (appended)
"""
import argparse
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.fitness import fitness_analysis  # noqa: E402
from persist.runner import load_context  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("step", choices=["export", "analyze"])
ap.add_argument("--config")
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("scgpt")
proc = Path(cfg["paths"]["processed_dir"])
out_dir = proc / "scgpt"
out_dir.mkdir(exist_ok=True)
counts_path, emb_path = out_dir / "counts.npz", out_dir / "emb_scgpt_human.npy"

if args.step == "export":
    ref = ad.read_h5ad(proc / "pre_keep.h5ad", backed="r")
    obs, genes, symbols = ref.obs, ref.var_names, ref.var["symbol"].astype(str).to_numpy()
    parts, cells = [], []
    for s in obs["sample"].unique():
        a = ad.read_h5ad(proc / "samples" / f"{s}.h5ad")
        a = a[obs.index[obs["sample"] == s]]
        pos = genes.get_indexer(a.var_names)  # genes the authors dropped from this sample stay zero
        m = pos >= 0
        X = sp.csc_matrix(a.X)[:, np.flatnonzero(m)]
        M = sp.csr_matrix((np.ones(m.sum(), np.float32), (np.arange(m.sum()), pos[m])), shape=(m.sum(), len(genes)))
        parts.append((X @ M).tocsr().astype(np.float32))
        cells += list(a.obs_names)
        log.info(f"{s}: {a.n_obs} cells")
        del a
    X = sp.vstack(parts).tocsr()
    np.savez_compressed(counts_path, data=X.data, indices=X.indices, indptr=X.indptr, shape=X.shape,
                        cells=np.array(cells), symbols=symbols)
    log.info(f"wrote {counts_path}: {X.shape[0]} cells x {X.shape[1]} genes, {X.nnz:,} non-zeros")
else:
    ctx = load_context(cfg, "keep")
    cells = np.load(counts_path, allow_pickle=True)["cells"]
    E = pd.DataFrame(np.load(emb_path).astype(np.float64), index=cells).loc[ctx.obs.index].to_numpy()
    for s in np.unique(ctx.samples):  # z-score within sample, as for the PCA input
        m = ctx.samples == s
        E[m] = (E[m] - E[m].mean(0)) / (E[m].std(0) + 1e-8)
    ctx.feats["pca"] = E
    rows = []
    for arm in [a for a in cfg["data"]["arms"] if a != "Control"]:
        r = fitness_analysis(ctx, arm, "Control", "pca", cfg["seed"])
        r.update(representation="scgpt_human", n_dims=E.shape[1], config_hash=cfg["_hash"])
        rows.append(r)
        log.info(f"scGPT {arm}: drug={r['auroc_drug_model_on_drug']:.3f} fitness={r['auroc_fitness_model_on_drug']:.3f} "
                 f"control={r['auroc_control_model_on_control']:.3f} spec_matched={r['specificity_index_size_matched']:.3f}")
    res = Path(cfg["paths"]["results_dir"]) / "sensitivity_representations.csv"
    old = pd.read_csv(res)
    old = old[old["representation"] != "scgpt_human"]
    pd.concat([old, pd.DataFrame(rows)], ignore_index=True).to_csv(res, index=False)
    print(pd.DataFrame(rows)[["drug_arm", "auroc_drug_model_on_drug", "auroc_fitness_model_on_drug",
                              "auroc_control_model_on_control", "specificity_index_size_matched"]].round(3).to_string(index=False))
