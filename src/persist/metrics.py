"""AUROC / AUPRC with lineage-group bootstrap CIs, and within-cluster AUROC."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


def _safe(fn, y, s):
    return fn(y, s) if 0 < y.sum() < len(y) else np.nan


def within_cluster_auroc(y: np.ndarray, s: np.ndarray, clusters: np.ndarray, min_pos: int = 5) -> float:
    """Size-weighted mean AUROC computed inside each state cluster.

    High overall AUROC but ~0.5 within clusters means the model only separates clusters
    (e.g. subclones), not cell states inside them.
    """
    num = den = 0.0
    for c in np.unique(clusters):
        m = clusters == c
        if y[m].sum() >= min_pos and (1 - y[m]).sum() >= min_pos:
            num += roc_auc_score(y[m], s[m]) * m.sum()
            den += m.sum()
    return num / den if den else np.nan


def evaluate(y, s, groups=None, clusters=None, n_boot: int = 500, seed: int = 0) -> dict:
    y = np.asarray(y).astype(int)
    s = np.asarray(s, dtype=float)
    prev = y.mean()
    out = {
        "n_test": len(y), "n_pos": int(y.sum()), "prevalence": prev,
        "auroc": _safe(roc_auc_score, y, s), "auprc": _safe(average_precision_score, y, s),
    }
    out["auprc_lift"] = out["auprc"] / prev if prev > 0 else np.nan
    if clusters is not None:
        out["within_cluster_auroc"] = within_cluster_auroc(y, s, np.asarray(clusters))
    if n_boot and groups is not None:
        rng = np.random.default_rng(seed)
        uniq, inv = np.unique(np.asarray(groups), return_inverse=True)
        members = np.split(np.argsort(inv, kind="stable"), np.cumsum(np.bincount(inv))[:-1])
        aurocs, auprcs = [], []
        for _ in range(n_boot):
            pick = rng.integers(0, len(uniq), len(uniq))
            idx = np.concatenate([members[i] for i in pick])
            aurocs.append(_safe(roc_auc_score, y[idx], s[idx]))
            auprcs.append(_safe(average_precision_score, y[idx], s[idx]))
        out["auroc_lo"], out["auroc_hi"] = np.nanpercentile(aurocs, [2.5, 97.5])
        out["auprc_lo"], out["auprc_hi"] = np.nanpercentile(auprcs, [2.5, 97.5])
    return out
