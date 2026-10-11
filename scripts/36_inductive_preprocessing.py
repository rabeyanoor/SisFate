"""Does fitting the label-free preprocessing on all cells inflate AUROC?

The main pipeline selects genes, scales and fits the PCA on every pre-treatment cell, test cells included. That uses
no labels, but test cells do shape the feature space. Here we redo the evaluation with the preprocessing fitted on
the training cells only and then applied unchanged to the test cells:

  global      main pipeline (stored X_pca)
  pca_train   stored scaled HVG matrix, PCA fitted on the training cells only
  inductive   gene selection (per-sample dispersion rank among the 5,005 stored genes), per-sample scaling
              (training-cell mean and SD) and PCA all fitted on the training cells only

for within-arm five-fold cross-validation (the same folds as the main analysis) and for the fitness model
(trained on the control arm, applied to each drug arm; the preprocessing then sees control cells only).
The 5,005-gene pool itself was chosen on all cells without labels; its selection is not redone.

Run: python scripts/36_inductive_preprocessing.py   (needs data/processed/pre_keep.h5ad)
"""
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import scanpy as sc
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.models.baselines import logistic  # noqa: E402
from persist.splits import within_arm  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

cfg = load_config()
log = get_logger("inductive")
pp = cfg["preprocess"]
R = Path(cfg["paths"]["results_dir"])
A = ad.read_h5ad(Path(cfg["paths"]["processed_dir"]) / "pre_keep.h5ad", backed="r")
obs = A.obs
var = A.var
bad = (var["mt"] | var["ribo"]).to_numpy()
C = cfg["baselines"]["logistic_C"]


def dense(idx):
    X = A.X[np.sort(idx)]
    X = X.toarray() if hasattr(X, "toarray") else np.asarray(X)
    order = np.argsort(np.argsort(idx))
    return X[order].astype(np.float32)


def inductive_features(X_tr, s_tr, X_te, s_te):
    """Gene selection, per-sample scaling and PCA fitted on the training rows only."""
    ranks = []
    for s in np.unique(s_tr):
        df = sc.pp.highly_variable_genes(ad.AnnData(X_tr[s_tr == s]), flavor="seurat", n_top_genes=pp["n_hvg"],
                                         inplace=False)
        disp = pd.Series(np.asarray(df["dispersions_norm"])).fillna(-np.inf)
        ranks.append(disp.rank(ascending=False, method="first").to_numpy())
    med = np.median(ranks, axis=0)
    med[bad] = np.inf
    genes = np.argsort(med, kind="stable")[: pp["n_hvg"]]
    Z_tr, Z_te = X_tr[:, genes].copy(), X_te[:, genes].copy()
    for s in np.unique(s_tr):
        m = s_tr == s
        mu, sd = Z_tr[m].mean(0), Z_tr[m].std(0)
        sd[sd == 0] = 1.0
        Z_tr[m] = (Z_tr[m] - mu) / sd
        if (s_te == s).any():
            Z_te[s_te == s] = (Z_te[s_te == s] - mu) / sd
    # test samples absent from training (fitness model: drug-arm samples) are scaled with their own statistics,
    # exactly as the main pipeline does; no label and no training information is involved
    for s in np.setdiff1d(np.unique(s_te), np.unique(s_tr)):
        m = s_te == s
        mu, sd = Z_te[m].mean(0), Z_te[m].std(0)
        sd[sd == 0] = 1.0
        Z_te[m] = (Z_te[m] - mu) / sd
    np.clip(Z_tr, -10, 10, out=Z_tr)
    np.clip(Z_te, -10, 10, out=Z_te)
    pca = PCA(n_components=pp["n_pcs"], random_state=cfg["seed"], svd_solver="randomized").fit(Z_tr)
    return pca.transform(Z_tr), pca.transform(Z_te)


def pca_train_features(H_tr, H_te):
    pca = PCA(n_components=pp["n_pcs"], random_state=cfg["seed"], svd_solver="randomized").fit(H_tr)
    return pca.transform(H_tr), pca.transform(H_te)


def predict(variant, tr, te):
    if variant == "global":
        F_tr, F_te = A.obsm["X_pca"][np.sort(tr)], A.obsm["X_pca"][np.sort(te)]
        F_tr = F_tr[np.argsort(np.argsort(tr))]
        F_te = F_te[np.argsort(np.argsort(te))]
    elif variant == "pca_train":
        H = A.obsm["X_hvg"]
        F_tr, F_te = pca_train_features(np.asarray(H[np.sort(tr)])[np.argsort(np.argsort(tr))],
                                        np.asarray(H[np.sort(te)])[np.argsort(np.argsort(te))])
    else:
        F_tr, F_te = inductive_features(dense(tr), samples[tr], dense(te), samples[te])
    return logistic(F_tr, y[tr], F_te, C, cfg["seed"])[0]


samples = obs["sample"].astype(str).to_numpy()
y = obs["y"].to_numpy()
labeled = obs["labeled"].to_numpy(bool)
arm = obs["arm"].astype(str).to_numpy()
VARIANTS = ["global", "pca_train", "inductive"]
rows = []
for a in cfg["data"]["arms"]:
    splits = within_arm(obs, a, cfg["splits"]["n_folds"], cfg["seed"])
    te_all = np.concatenate([s.test_idx for s in splits])
    for v in VARIANTS:
        score = np.empty(len(te_all))
        pos = 0
        for s in splits:
            score[pos:pos + len(s.test_idx)] = predict(v, s.train_idx, s.test_idx)
            pos += len(s.test_idx)
        auc = roc_auc_score(y[te_all], score)
        rows.append({"design": "within_arm", "train": a, "test": a, "variant": v, "auroc": round(auc, 4),
                     "n_test": len(te_all)})
        log.info(f"within {a:<11} {v:<10} AUROC {auc:.4f}")

ctrl = np.flatnonzero(labeled & (arm == "Control"))
for a in [x for x in cfg["data"]["arms"] if x != "Control"]:
    te = np.flatnonzero(labeled & (arm == a))
    for v in VARIANTS:
        auc = roc_auc_score(y[te], predict(v, ctrl, te))
        rows.append({"design": "fitness_model", "train": "Control", "test": a, "variant": v, "auroc": round(auc, 4),
                     "n_test": len(te)})
        log.info(f"fitness Control->{a:<11} {v:<10} AUROC {auc:.4f}")

df = pd.DataFrame(rows)
wide = df.pivot_table(index=["design", "train", "test"], columns="variant", values="auroc").reset_index()
wide["inductive_minus_global"] = (wide["inductive"] - wide["global"]).round(4)
wide["pca_train_minus_global"] = (wide["pca_train"] - wide["global"]).round(4)
out = R / "inductive_preprocessing.csv"
wide.to_csv(out, index=False)
log.info("\n" + wide.to_string(index=False))
log.info(f"wrote {out}")
