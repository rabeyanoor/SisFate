"""Predictability ceiling set by sister-cell discordance.

Setup. The label of pre-treatment cell A is the fate of its treated sister B. Any predictor sees
only A's state, so its performance is bounded by how much fate-relevant state A and B share.

Estimate. Some families have >= 2 sisters in the *pre-treatment* sample (the `sisters` column).
Those untreated sister pairs are exchangeable with (A, B), so their similarity estimates the
A-B correlation of any state score:
  ICC(w)   = corr(w.z_a, w.z_b) over sister pairs (symmetrised)
  ICC_max  = max_w ICC(w), a generalised eigenproblem, estimated with held-out families (CV).

Bound. Latent-liability model: B survives iff its liability l_B > t (prevalence p). With
corr(l_A, l_B) <= rho = ICC_max, the best possible AUROC from A is the bivariate-normal AUROC
at rho. Label noise (a fraction pi of observed negatives are true positives) then gives
AUROC_obs = (1 - pi) * AUROC + pi / 2.
This is an upper bound: it assumes fate is fully determined by B's state and that the heritable
subspace is linear in the chosen embedding.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.linalg import eigh
from sklearn.metrics import roc_auc_score


def pair_icc(a: np.ndarray, b: np.ndarray) -> float:
    """Symmetrised Pearson correlation between paired values (intraclass correlation)."""
    x, y = np.concatenate([a, b]), np.concatenate([b, a])
    return float(np.corrcoef(x, y)[0, 1])


def per_dim_icc(Z: np.ndarray, pairs: np.ndarray) -> np.ndarray:
    return np.array([pair_icc(Z[pairs[:, 0], j], Z[pairs[:, 1], j]) for j in range(Z.shape[1])])


def _fit_direction(Z: np.ndarray, pairs: np.ndarray, ridge: float) -> np.ndarray:
    A, B = Z[pairs[:, 0]], Z[pairs[:, 1]]
    X = np.vstack([A, B])
    mu = X.mean(0)
    A, B, X = A - mu, B - mu, X - mu
    Ct = X.T @ X / len(X)
    Cb = (A.T @ B + B.T @ A) / (2 * len(A))
    Ct += ridge * np.trace(Ct) / Ct.shape[0] * np.eye(Ct.shape[0])
    _, vecs = eigh(Cb, Ct)
    return vecs[:, -1]


def icc_max_cv(Z: np.ndarray, pairs: np.ndarray, families: np.ndarray, ridge: float = 1e-2,
               n_folds: int = 5, seed: int = 0) -> dict:
    """Held-out-family estimate of the most sister-heritable linear direction's ICC."""
    rng = np.random.default_rng(seed)
    fam = np.unique(families)
    fold_of = dict(zip(fam, rng.permutation(len(fam)) % n_folds))
    f = np.array([fold_of[x] for x in families])
    held = []
    for k in range(n_folds):
        w = _fit_direction(Z, pairs[f != k], ridge)
        te = pairs[f == k]
        held.append(pair_icc(Z[te[:, 0]] @ w, Z[te[:, 1]] @ w))
    w_all = _fit_direction(Z, pairs, ridge)
    return {
        "icc_max_cv": float(np.mean(held)), "icc_max_cv_sd": float(np.std(held)),
        "icc_max_insample": pair_icc(Z[pairs[:, 0]] @ w_all, Z[pairs[:, 1]] @ w_all),
        "direction": w_all,
    }


def random_pairs(samples: np.ndarray, pairs: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Null: same number of pairs, same samples, random partners."""
    out = []
    for a, _ in pairs:
        pool = np.flatnonzero(samples == samples[a])
        b = rng.choice(pool)
        while b == a:
            b = rng.choice(pool)
        out.append((a, b))
    return np.asarray(out)


def binormal_auroc(rho: float, prevalence: float, n: int = 400_000, seed: int = 0) -> float:
    rng = np.random.default_rng(seed)
    lb = rng.standard_normal(n)
    la = rho * lb + np.sqrt(max(1 - rho**2, 0.0)) * rng.standard_normal(n)
    y = lb > np.quantile(lb, 1 - prevalence)
    return float(roc_auc_score(y, la))


def noisy(auroc: float, pi: float) -> float:
    return (1 - pi) * auroc + pi / 2


def ceiling_table(rho: float, prevalence: float, pis: list[float], n_sim: int) -> pd.DataFrame:
    base = binormal_auroc(max(rho, 0.0), prevalence, n_sim)
    return pd.DataFrame({"pi": pis, "auroc_ceiling": [noisy(base, p) for p in pis]})


def ceiling_curve(prevalence: float, n_sim: int = 200_000) -> pd.DataFrame:
    rhos = np.linspace(0, 1, 21)
    return pd.DataFrame({"rho": rhos, "auroc": [binormal_auroc(r, prevalence, n_sim) for r in rhos]})


def cross_sister_diagnostic(scores: pd.Series, y: pd.Series, pairs_cells: np.ndarray, seed: int = 0) -> dict:
    """Own-score vs sister-score AUROC for the same labels, one random orientation per pair.

    Sisters share the label. If a model's signal is heritable state, predicting a cell's label from
    its sister's score works almost as well as from its own; a large gap means the model uses
    cell-specific (non-heritable) variation.
    """
    ok = np.array([(a, b) for a, b in pairs_cells if a in scores.index and b in scores.index])
    if len(ok) < 20:
        return {"n_pairs": len(ok)}
    rng = np.random.default_rng(seed)
    flip = rng.random(len(ok)) < 0.5
    ok = np.where(flip[:, None], ok[:, ::-1], ok)
    a, b = ok[:, 0], ok[:, 1]
    yy = y.loc[a].to_numpy()
    if not 0 < yy.sum() < len(yy):
        return {"n_pairs": len(ok)}
    return {
        "n_pairs": len(ok),
        "auroc_own_score": roc_auc_score(yy, scores.loc[a].to_numpy()),
        "auroc_sister_score": roc_auc_score(yy, scores.loc[b].to_numpy()),
        "score_icc": pair_icc(normal_scores(scores).loc[a].to_numpy(), normal_scores(scores).loc[b].to_numpy()),
    }


def normal_scores(s: pd.Series) -> pd.Series:
    """Rank-based inverse-normal transform, so scores fit the Gaussian liability model."""
    from scipy.stats import norm

    r = s.rank(method="average")
    return pd.Series(norm.ppf((r - 0.5) / len(s)), index=s.index)


def invert_binormal(auroc: float, prevalence: float, n: int = 200_000) -> float:
    """rho such that binormal_auroc(rho) == auroc (bisection; monotone in rho)."""
    lo, hi = 0.0, 1.0
    for _ in range(25):
        mid = (lo + hi) / 2
        if binormal_auroc(mid, prevalence, n) < auroc:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def score_decomposition(auroc_obs: float, score_icc: float, prevalence: float, pi: float, n: int = 200_000) -> dict:
    """Split a model's AUROC into sister discordance vs fate stochasticity (Gaussian liability model).

    corr(score_A, liability_B) = rho_obs, recovered from the noise-corrected AUROC. Since the score is
    shared between sisters only up to score_icc, corr(score_B, liability_B) = rho_obs / score_icc = rho_fate.
      auroc_if_sister_seen : AUROC if the *treated* sister's own state were observed (no sister gap)
      sister_cost          : AUROC lost purely because the label belongs to a different cell
    """
    a_clean = (auroc_obs - pi / 2) / (1 - pi)
    rho_obs = invert_binormal(min(max(a_clean, 0.5), 0.9999), prevalence, n)
    rho_fate = min(rho_obs / max(score_icc, 1e-6), 1.0)
    a_sis = binormal_auroc(rho_fate, prevalence, n)
    return {"rho_obs": rho_obs, "rho_fate": rho_fate, "saturated": rho_obs >= score_icc,  # unreliable if True
            "auroc_if_sister_seen": noisy(a_sis, pi), "sister_cost": noisy(a_sis, pi) - auroc_obs}
