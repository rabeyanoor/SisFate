"""Fitness-adjusted evaluation of lineage-based fate predictors.

A small, data-agnostic toolkit for any lineage-tracing experiment in which pre-treatment cells are
labelled by the fate of their relatives and at least one arm receives no drug. It answers three
questions for a fate predictor:

1. How much of its signal is generic fitness? A model trained on the untreated arm scores the drug-arm
   cells (`fitness_adjusted_report`): its AUROC, the drug score's AUROC after removing the fitness score,
   a likelihood-ratio test, and the drug-specific gain with training size matched (ΔAUROC) with a
   paired family-level bootstrap confidence interval.
2. Is the signal above chance for this model class? Labels are permuted between whole families within
   each sample, which keeps the dependence structure (`family_permutation_null`).
3. What is the best one could hope for? Pre-treatment sister pairs give the sister concordance of the
   score, and a Gaussian liability model converts AUROC and concordance into the AUROC expected if the
   treated relative itself were observed (`sister_ceiling`).

Inputs are plain arrays, so any representation (PCs, a latent space, foundation-model embeddings) and
any scikit-learn classifier with `predict_proba` can be used.

Example
-------
>>> from persist.fitadj import fitness_adjusted_report
>>> rep = fitness_adjusted_report(X, y, families, arms, samples, control="Control")
>>> rep[["arm", "auroc_drug", "auroc_fitness", "delta_size_matched", "delta_lo", "delta_hi"]]
"""
from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .ceiling import normal_scores, pair_icc, score_decomposition

__all__ = ["default_model", "grouped_oof", "fitness_adjusted_report", "family_permutation_null",
           "sister_concordance", "sister_ceiling"]


def default_model(C: float = 0.05, seed: int = 0):
    """L2 logistic regression with balanced class weights (the model used in the paper)."""
    return make_pipeline(StandardScaler(), LogisticRegression(C=C, class_weight="balanced", max_iter=2000,
                                                              random_state=seed))


def _score(model, X_tr, y_tr, X_te):
    return clone(model).fit(X_tr, y_tr).predict_proba(X_te)[:, 1]


def _logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def _loglik(X, y):
    m = LogisticRegression(C=1e6, max_iter=5000).fit(X, y)
    p = np.clip(m.predict_proba(X)[:, 1], 1e-12, 1 - 1e-12)
    return float(np.sum(y * np.log(p) + (1 - y) * np.log(1 - p)))


def _take_families(idx, fam, n, rng):
    """Random whole families from `idx` until at least `n` cells are taken."""
    order = rng.permutation(np.unique(fam))
    sizes = pd.Series(fam).value_counts().reindex(order).to_numpy()
    take = set(order[: np.searchsorted(np.cumsum(sizes), n) + 1])
    return idx[np.fromiter((f in take for f in fam), bool, len(fam))]


def grouped_oof(X, y, groups, model=None, n_folds: int = 5, seed: int = 0,
                train_cap: int | None = None, rng: np.random.Generator | None = None) -> np.ndarray:
    """Out-of-fold scores from stratified group K-fold (whole families stay on one side).

    With `train_cap`, each training fold is reduced to random whole families totalling about that many
    cells, which lets a larger arm be compared with a smaller one at equal training size.
    """
    model = default_model(seed=seed) if model is None else model
    rng = np.random.default_rng(seed) if rng is None else rng
    out = np.empty(len(y))
    for tr, te in StratifiedGroupKFold(n_folds, shuffle=True, random_state=seed).split(X, y, groups):
        if train_cap is not None and len(tr) > train_cap:
            tr = _take_families(tr, groups[tr], train_cap, rng)
        out[te] = _score(model, X[tr], y[tr], X[te])
    return out


def fitness_adjusted_report(X, y, groups, arms, samples=None, control: str = "Control", model=None,
                            n_folds: int = 5, n_subsamples: int = 10, n_boot: int = 1000,
                            seed: int = 0) -> pd.DataFrame:
    """Compare each drug arm's predictor with a fitness model trained on the untreated arm.

    Parameters
    ----------
    X : (n_cells, n_features) array; y : 0/1 fate labels (1 = relative survived);
    groups : lineage family of each cell (families never straddle a split);
    arms : arm of each cell; `control` names the untreated arm;
    samples : sample of each cell, used to residualise within sample (defaults to `arms`).

    Returns one row per drug arm with
      auroc_drug          out-of-fold AUROC of the drug-arm model (grouped CV)
      auroc_fitness       AUROC of the control-trained model on the same drug-arm labels
      auroc_residual      AUROC of the drug logit after within-sample regression on the fitness logit
      rho_drug_fitness    Spearman correlation of the two scores
      lrt_p               likelihood-ratio test for adding the drug logit to the fitness logit
      delta_size_matched  AUROC(drug, training capped at the control arm's size) − AUROC(fitness),
                          mean over `n_subsamples`; delta_lo / delta_hi: 95% paired family bootstrap;
                          p_boot: one-sided bootstrap p for delta <= 0
    """
    X, y, groups, arms = map(np.asarray, (X, y, groups, arms))
    samples = arms if samples is None else np.asarray(samples)
    model = default_model(seed=seed) if model is None else model
    c = np.flatnonzero(arms == control)
    rows = []
    for arm in [a for a in pd.unique(arms) if a != control]:
        d = np.flatnonzero(arms == arm)
        yd, gd = y[d], groups[d]
        f = _score(model, X[c], y[c], X[d])
        full = grouped_oof(X[d], yd, gd, model, n_folds, seed)
        lf, ld = _logit(f), _logit(full)
        resid = np.empty_like(ld)
        for s in np.unique(samples[d]):
            m = samples[d] == s
            resid[m] = ld[m] - np.polyval(np.polyfit(lf[m], ld[m], 1), lf[m])
        lr = 2 * (_loglik(np.column_stack([lf, ld]), yd) - _loglik(lf[:, None], yd))

        rng = np.random.default_rng(seed + 1)
        capped = np.array([grouped_oof(X[d], yd, gd, model, n_folds, seed + k, train_cap=len(c), rng=rng)
                           for k in range(n_subsamples)])
        a_f = roc_auc_score(yd, f)
        delta = np.array([roc_auc_score(yd, s) for s in capped]) - a_f
        codes, inv = np.unique(gd, return_inverse=True)
        boot = np.empty(n_boot)
        for b in range(n_boot):
            w = rng.multinomial(len(codes), np.full(len(codes), 1 / len(codes)))[inv]
            boot[b] = np.mean([roc_auc_score(yd, s, sample_weight=w) for s in capped]) \
                - roc_auc_score(yd, f, sample_weight=w)
        rows.append({
            "arm": arm, "n_cells": len(d), "n_families": len(codes), "prevalence": yd.mean(),
            "n_control": len(c), "auroc_drug": roc_auc_score(yd, full), "auroc_fitness": a_f,
            "auroc_residual": roc_auc_score(yd, resid), "rho_drug_fitness": stats.spearmanr(ld, lf).statistic,
            "lrt_stat": lr, "lrt_p": stats.chi2.sf(lr, 1),
            "delta_size_matched": delta.mean(), "delta_seed_sd": delta.std(ddof=1) if len(delta) > 1 else np.nan,
            "delta_lo": np.quantile(boot, 0.025), "delta_hi": np.quantile(boot, 0.975),
            "p_boot": (np.sum(boot <= 0) + 1) / (n_boot + 1),
        })
    return pd.DataFrame(rows)


def family_permutation_null(X, y, groups, samples, model=None, n_perm: int = 100, n_folds: int = 5,
                            seed: int = 0, fit: Callable | None = None) -> dict:
    """Exact permutation test: labels are reassigned between whole families within each sample.

    Each family keeps its size and its sample, so clustering and sample composition are preserved.
    Families are concordant by construction in sister designs; a discordant family gets its majority label.
    """
    X, y, groups, samples = map(np.asarray, (X, y, groups, samples))
    fit = fit or (lambda yy, s: grouped_oof(X, yy, groups, model, n_folds, s))
    obs = roc_auc_score(y, fit(y, seed))
    fam = pd.DataFrame({"g": groups, "s": samples, "y": y}).groupby("g").agg(s=("s", "first"), y=("y", "mean"))
    fam["y"] = (fam["y"] >= 0.5).astype(int)
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm)
    for k in range(n_perm):
        perm = fam.groupby("s")["y"].transform(lambda v: rng.permutation(v.to_numpy()))
        yp = perm.reindex(groups).to_numpy()
        null[k] = roc_auc_score(y, fit(yp, seed))  # model trained on permuted labels, scored on true ones
    return {"auroc": obs, "null_mean": null.mean(), "null_sd": null.std(ddof=1),
            "p": (np.sum(null >= obs) + 1) / (n_perm + 1)}


def sister_concordance(scores, pairs) -> float:
    """Sister concordance of a score: symmetrised Pearson correlation of rank-normalised scores over
    pre-treatment sister pairs (`pairs`: (n_pairs, 2) integer indices into `scores`)."""
    z = normal_scores(pd.Series(np.asarray(scores, float))).to_numpy()
    pairs = np.asarray(pairs)
    return pair_icc(z[pairs[:, 0]], z[pairs[:, 1]])


def sister_ceiling(auroc: float, concordance: float, prevalence: float, label_noise: float = 0.1,
                   n_sim: int = 200_000) -> dict:
    """AUROC expected if the treated relative's own state were scored, and the AUROC lost to sister
    discordance, under a Gaussian liability model with a fraction `label_noise` of observed negatives
    being true positives. `saturated` flags cases where the bound is not identifiable."""
    return score_decomposition(auroc, concordance, prevalence, label_noise, n_sim)
