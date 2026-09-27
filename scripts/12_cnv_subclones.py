"""Subclone confound: infer CNV subclones, check the published enrichment, then test whether the
expression signal survives within subclones and beyond subclone identity.

Outputs results/cnv/: per-cell CNV cluster calls, enrichment table, confound tests, a CNV heatmap.
"""
import argparse
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score, silhouette_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.cnv import gene_positions, reference_panel, sample_cnv  # noqa: E402
from persist.fitness import _loglik  # noqa: E402
from persist.metrics import within_cluster_auroc  # noqa: E402
from persist.models.baselines import logistic  # noqa: E402
from persist.runner import load_context  # noqa: E402
from persist.splits import within_arm  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--cc-mode", choices=["keep", "regress", "regress_all"])
ap.add_argument("--k", type=int, help="number of CNV clusters (default: best silhouette in 2..8)")
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("cnv")
out = Path(cfg["paths"]["results_dir"]) / "cnv"
out.mkdir(exist_ok=True)
proc = Path(cfg["paths"]["processed_dir"])

# ---------------------------------------------------------------- 1. CNV profiles
cnv_file = proc / "cnv_profiles.npz"
files = sorted((proc / "samples").glob("*_pre.h5ad"))
if not cnv_file.exists():
    pos = gene_positions(Path(cfg["paths"]["ref_dir"]) / "gene_positions.tsv")
    common = None
    for f in files:
        a = ad.read_h5ad(f, backed="r")
        common = a.var_names if common is None else common.intersection(a.var_names)
    common = common.intersection(pos.index)
    # keep genes detected in >= 10% of cells in every sample (inferCNV-style low-expression filter)
    keep = pd.Series(True, index=common)
    for f in files:
        a = ad.read_h5ad(f)[:, common]
        keep &= np.asarray((a.X > 0).mean(0)).ravel() >= 0.10
    genes = common[keep.to_numpy()]
    genes = pos.loc[genes].assign(chr_n=lambda d: d["chromosome"].str[3:].replace("X", "23").astype(int)) \
        .sort_values(["chr_n", "start"]).index
    log.info(f"{len(genes)} genes used for CNV inference")
    ref = reference_panel(files, genes, 200, cfg["seed"])
    names, profiles = [], []
    for f in files:
        n, X, chr_pos = sample_cnv(f, ref, genes, pos)
        names.append(n)
        profiles.append(X)
        log.info(f"{f.stem}: {X.shape}")
    np.savez_compressed(cnv_file, names=np.concatenate(names), X=np.vstack(profiles),
                        chr_names=np.array(list(chr_pos.keys())), chr_starts=np.array(list(chr_pos.values())))
z = np.load(cnv_file, allow_pickle=True)
names, Xc = z["names"], z["X"]

ctx = load_context(cfg, args.cc_mode)
obs = ctx.obs
idx = pd.Index(names).get_indexer(obs.index)
assert (idx >= 0).all(), "CNV profiles missing for some cells"
Xc = Xc[idx]

# ---------------------------------------------------------------- 2. clusters
P = PCA(20, random_state=cfg["seed"]).fit_transform(Xc)
if args.k:
    k_best = args.k
    sil = {}
else:
    rng = np.random.default_rng(cfg["seed"])
    sub = rng.choice(len(P), min(8000, len(P)), replace=False)
    sil = {k: silhouette_score(P[sub], KMeans(k, n_init=10, random_state=cfg["seed"]).fit_predict(P[sub]))
           for k in range(2, 9)}
    k_best = max(sil, key=sil.get)
    log.info(f"silhouette by k: { {k: round(v, 3) for k, v in sil.items()} } -> k={k_best}")
km = KMeans(k_best, n_init=20, random_state=cfg["seed"]).fit(P)
clusters = km.labels_.astype(str)
obs = obs.assign(cnv_cluster=clusters)
obs[["sample", "arm", "drugSens", "cnv_cluster"]].to_csv(out / "cnv_clusters.csv.gz")

# ---------------------------------------------------------------- 3. published enrichment?
lab = obs[obs["labeled"]]
rows = []
for arm in cfg["data"]["arms"]:
    d = lab[lab["arm"] == arm]
    for c in sorted(d["cnv_cluster"].unique()):
        a = ((d["cnv_cluster"] == c) & (d["y"] == 1)).sum()
        b = ((d["cnv_cluster"] == c) & (d["y"] == 0)).sum()
        cc = ((d["cnv_cluster"] != c) & (d["y"] == 1)).sum()
        dd = ((d["cnv_cluster"] != c) & (d["y"] == 0)).sum()
        orr, p = stats.fisher_exact([[a, b], [cc, dd]])
        rows.append({"arm": arm, "cnv_cluster": c, "n_cells": a + b, "frac_in_pre_resistant": a / max(a + cc, 1),
                     "frac_in_pre_sensitive": b / max(b + dd, 1), "odds_ratio": orr, "p": p})
enr = pd.DataFrame(rows)
enr["padj"] = stats.false_discovery_control(enr["p"])
enr.to_csv(out / "cnv_enrichment.csv", index=False)
print(enr.round(4).to_string(index=False))

# ---------------------------------------------------------------- 4. confound tests
C = cfg["baselines"]["logistic_C"]
X = ctx.features("pca")
onehot = pd.get_dummies(obs["cnv_cluster"]).to_numpy(np.float32)
res = []
for arm in cfg["data"]["arms"]:
    folds = within_arm(obs, arm, cfg["splits"]["n_folds"], cfg["seed"])
    te_all = np.concatenate([f.test_idx for f in folds])
    s_expr, s_cnv, s_both = (np.zeros(len(obs)) for _ in range(3))
    for f in folds:
        s_expr[f.test_idx], _ = logistic(X[f.train_idx], ctx.y[f.train_idx], X[f.test_idx], C, cfg["seed"])
        s_cnv[f.test_idx], _ = logistic(onehot[f.train_idx], ctx.y[f.train_idx], onehot[f.test_idx], C, cfg["seed"])
        Xb = np.hstack([X, onehot])
        s_both[f.test_idx], _ = logistic(Xb[f.train_idx], ctx.y[f.train_idx], Xb[f.test_idx], C, cfg["seed"])
    y = ctx.y[te_all]
    cl = obs["cnv_cluster"].to_numpy()[te_all]
    lr = 2 * (_loglik(np.column_stack([onehot[te_all], np.log(s_expr[te_all] / (1 - s_expr[te_all]))]), y)
              - _loglik(onehot[te_all], y))
    res.append({
        "arm": arm, "auroc_cnv_cluster_only": roc_auc_score(y, s_cnv[te_all]),
        "auroc_expression": roc_auc_score(y, s_expr[te_all]),
        "auroc_expression_plus_cnv": roc_auc_score(y, s_both[te_all]),
        "auroc_expression_within_cnv_clusters": within_cluster_auroc(y, s_expr[te_all], cl, min_pos=10),
        "lrt_expression_beyond_cnv": lr, "lrt_p": stats.chi2.sf(lr, 1),
    })
res = pd.DataFrame(res)
res.to_csv(out / "cnv_confound.csv", index=False)
print(res.round(4).to_string(index=False))

# ---------------------------------------------------------------- 5. heatmap for the supplement
try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    order = np.argsort(clusters, kind="stable")
    step = max(1, len(order) // 3000)
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.imshow(Xc[order[::step]], aspect="auto", cmap="RdBu_r", vmin=-0.3, vmax=0.3, interpolation="nearest")
    for name, start in zip(z["chr_names"], z["chr_starts"]):
        ax.axvline(start, color="#52514e", lw=0.4)
        ax.text(start, -5, str(name).replace("chr", ""), fontsize=6)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_ylabel(f"cells ordered by CNV cluster (k={k_best})")
    fig.savefig(Path(cfg["paths"]["results_dir"]) / "figures" / "figS_cnv_heatmap.png", dpi=200, bbox_inches="tight")
except Exception as exc:  # the figure is optional
    log.warning(f"heatmap skipped: {exc}")
