"""Growth-fitness confound: is a drug arm's 'pre-resistant' signal drug-specific or generic survival?

In the Control arm a cell is 'pre-resistant' when its sister simply survived and was captured
without any drug, so a model trained on Control labels learns generic fitness. For each drug arm:
  fitness score  f = Control-trained model applied to drug-arm cells
  drug score     d = drug-arm out-of-fold score
and we report how much of d's predictive value survives once f is accounted for.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from .metrics import within_cluster_auroc
from .models.baselines import logistic
from .splits import within_arm


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _loglik(X, y):
    m = LogisticRegression(C=1e6, max_iter=5000).fit(X, y)
    p = np.clip(m.predict_proba(X)[:, 1], 1e-12, 1 - 1e-12)
    return np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))


def oof_scores(ctx, arm: str, X: np.ndarray, C: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    idx_all, s_all = [], []
    for sp in within_arm(ctx.obs, arm, ctx.cfg["splits"]["n_folds"], seed):
        s, _ = logistic(X[sp.train_idx], ctx.y[sp.train_idx], X[sp.test_idx], C, seed)
        idx_all.append(sp.test_idx)
        s_all.append(s)
    idx = np.concatenate(idx_all)
    order = np.argsort(idx)
    return idx[order], np.concatenate(s_all)[order]


def fitness_analysis(ctx, drug_arm: str, control_arm: str = "Control", features: str = "pca", seed: int = 0) -> dict:
    C = ctx.cfg["baselines"]["logistic_C"]
    X = ctx.features(features)
    lab = ctx.obs["labeled"].to_numpy()
    arm = ctx.obs["arm"].to_numpy()
    d_idx = np.flatnonzero(lab & (arm == drug_arm))
    c_idx = np.flatnonzero(lab & (arm == control_arm))
    yd, yc = ctx.y[d_idx], ctx.y[c_idx]

    d_idx_oof, d_oof = oof_scores(ctx, drug_arm, X, C, seed)
    assert np.array_equal(d_idx_oof, d_idx)
    c_idx_oof, c_oof = oof_scores(ctx, control_arm, X, C, seed)
    fit_on_drug, _ = logistic(X[c_idx], yc, X[d_idx], C, seed)   # fitness model -> drug cells
    drug_on_ctrl, _ = logistic(X[d_idx], yd, X[c_idx], C, seed)  # drug model -> control cells

    # residualise drug score on fitness score within sample, then score the residual
    ld, lf = _logit(d_oof), _logit(fit_on_drug)
    resid = np.empty_like(ld)
    samples = ctx.samples[d_idx]
    for s in np.unique(samples):
        m = samples == s
        b = np.polyfit(lf[m], ld[m], 1)
        resid[m] = ld[m] - np.polyval(b, lf[m])

    # likelihood-ratio test: does the drug score add information beyond fitness?
    ll0 = _loglik(lf[:, None], yd)
    ll1 = _loglik(np.column_stack([lf, ld]), yd)
    lr = 2 * (ll1 - ll0)

    # Size-matched comparison: Control has fewer labelled cells, which handicaps the fitness model.
    # Train the drug model on a random set of drug-arm families with as many cells as Control has,
    # and score both models on the remaining drug-arm cells.
    rng = np.random.default_rng(seed)
    fam = ctx.groups[d_idx]
    matched_d, matched_f = [], []
    for _ in range(5):
        order = rng.permutation(np.unique(fam))
        sizes = pd.Series(fam).value_counts().reindex(order).to_numpy()
        take = set(order[: np.searchsorted(np.cumsum(sizes), len(c_idx)) + 1])
        tr = np.array([f in take for f in fam])
        s_d, _ = logistic(X[d_idx[tr]], yd[tr], X[d_idx[~tr]], C, seed)
        matched_d.append(roc_auc_score(yd[~tr], s_d))
        matched_f.append(roc_auc_score(yd[~tr], fit_on_drug[~tr]))

    fq = np.digitize(lf, np.quantile(lf, [0.2, 0.4, 0.6, 0.8]))
    auc_d = roc_auc_score(yd, d_oof)
    auc_f = roc_auc_score(yd, fit_on_drug)
    return {
        "drug_arm": drug_arm,
        "n_drug": len(d_idx), "prev_drug": yd.mean(), "n_control": len(c_idx), "prev_control": yc.mean(),
        "auroc_drug_model_on_drug": auc_d,                    # total predictability (OOF)
        "auroc_fitness_model_on_drug": auc_f,                 # explained by generic fitness
        "auroc_control_model_on_control": roc_auc_score(yc, c_oof),
        "auroc_drug_model_on_control": roc_auc_score(yc, drug_on_ctrl),
        "specificity_index": auc_d - auc_f,
        "auroc_drug_model_size_matched": float(np.mean(matched_d)),
        "auroc_fitness_model_same_cells": float(np.mean(matched_f)),
        "specificity_index_size_matched": float(np.mean(matched_d) - np.mean(matched_f)),
        "auroc_drug_residual_on_drug": roc_auc_score(yd, resid),
        "auroc_drug_within_fitness_quintiles": within_cluster_auroc(yd, d_oof, fq),
        "corr_drug_vs_fitness_score": stats.spearmanr(ld, lf).statistic,
        "lrt_stat": lr, "lrt_p": stats.chi2.sf(lr, 1),
    }
