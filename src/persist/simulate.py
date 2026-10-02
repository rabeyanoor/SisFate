"""A generative model of sister-cell lineage tracing in which the right answer is known.

Every quantity the framework estimates has a closed-form counterpart here, so the estimates can be checked
for bias and the confidence intervals for coverage.

Model. A family f has a latent state z_f ~ N(0, I_d). Its two sisters each have their own state
    x_a = z_f + s * e_a,   x_b = z_f + s * e_b,    e ~ N(0, I_d),
so `s` sets how alike sisters are: corr(x_a, x_b) = 1 / (1 + s^2) per dimension. One sister is sequenced (we
keep x_a) and the other is treated. Whether the treated sister survives follows a latent liability built from

    u_b = fate_from_own * x_b + (1 - fate_from_own) * z_f

so `fate_from_own` decides whether fate is driven by the treated cell's own realised state (1) or only by the
state the sisters share (0). This matters: the ceiling estimator assumes the sequenced sister is informative
about its sibling's fate *only* through the state the two share, which is exactly the fate_from_own = 1 case.
At fate_from_own = 0 the sequenced sister is just as good a measurement of what drives fate as the treated
sister is, there is no cost to reading the wrong cell, and the estimator has nothing to recover.

    control arm : l = a * u_b[0]                + sqrt(1 - a^2) * eps
    drug arm    : l = a * u_b[0] + b * u_b[1]   + sqrt(max(1 - a^2 - b^2, 0)) * eps

Dimension 0 is a generic fitness axis shared by both arms, dimension 1 is drug-specific. A cell is a positive
when l exceeds the (1 - prevalence) quantile; a fraction `label_noise` of true positives is then flipped to
negative, which is how ReSisTrace loses a sister.

Ground truth. Everything is jointly Gaussian, so the best possible score of the sequenced sister is the linear
predictor E[l | x_seq], available in closed form (`optimal_weights`). Without the depth confound it is
a * x[0] + b * x[1] for the drug arm and x[0] for the fitness model; with it, both also read depth from the
remaining dimensions. The population value of everything the framework reports then follows from one large draw.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score

__all__ = ["simulate", "ground_truth"]


def _draw(rng, n, d, sister_noise, depth_effect):
    z = rng.standard_normal((n, d))
    x_seq = z + sister_noise * rng.standard_normal((n, d))
    x_tre = z + sister_noise * rng.standard_normal((n, d))
    depth = rng.standard_normal(n) if depth_effect else None
    if depth_effect:
        x_seq = x_seq + depth_effect * depth[:, None]
        x_tre = x_tre + depth_effect * depth[:, None]
    return z, x_seq, x_tre, depth


def _liability(z, x_tre, is_drug, a, b, fate_from_own, depth, depth_effect, rng):
    u = fate_from_own * x_tre + (1 - fate_from_own) * z
    share = a * u[:, 0] + (b * u[:, 1] if is_drug else 0.0)
    resid = 1 - a ** 2 - (b ** 2 if is_drug else 0.0)
    l = share + np.sqrt(max(resid, 1e-12)) * rng.standard_normal(len(u))
    if depth_effect:
        l = l + depth_effect * depth
    return l


def _label(l, prevalence, label_noise, rng):
    y = (l > np.quantile(l, 1 - prevalence)).astype(int)
    pos = np.flatnonzero(y == 1)
    drop = rng.random(len(pos)) < label_noise
    y[pos[drop]] = 0  # a surviving sister that was not recovered looks like a negative
    return y


def simulate(n_families: int = 4000, d: int = 10, a: float = 0.55, b: float = 0.25, sister_noise: float = 0.7,
             prevalence: float = 0.1, label_noise: float = 0.0, depth_effect: float = 0.0,
             fate_from_own: float = 1.0, n_control_families: int | None = None, seed: int = 0):
    """One synthetic experiment: a drug arm and a control arm of sequenced/treated sister pairs.

    Returns (X, y, groups, arms, samples, extras); `extras` carries the treated sisters' own measurements so
    the ceiling can be checked against what a model would actually achieve on them.
    """
    rng = np.random.default_rng(seed)
    n_ctrl = n_control_families if n_control_families is not None else n_families
    X, y, groups, arms, X_treated = [], [], [], [], []
    for arm, n in [("Drug", n_families), ("Control", n_ctrl)]:
        z, x_seq, x_tre, depth = _draw(rng, n, d, sister_noise, depth_effect)
        l = _liability(z, x_tre, arm == "Drug", a, b, fate_from_own, depth, depth_effect, rng)
        X.append(x_seq)
        X_treated.append(x_tre)
        y.append(_label(l, prevalence, label_noise, rng))
        groups.append(np.array([f"{arm}_{i}" for i in range(n)]))
        arms.append(np.repeat(arm, n))
    extras = {"X_treated_sister": np.vstack(X_treated)}
    return (np.vstack(X), np.concatenate(y), np.concatenate(groups), np.concatenate(arms),
            np.concatenate(arms), extras)


def optimal_weights(d: int, a: float, b: float, sister_noise: float, depth_effect: float, fate_from_own: float,
                    is_drug: bool) -> np.ndarray:
    """Weights of E[l | x_seq], the best possible linear score of the sequenced sister, in closed form.

    x_seq and l are jointly Gaussian, and labels threshold l plus independent noise, so P(y = 1 | x_seq) is
    monotone in E[l | x_seq] = x_seq @ beta with beta = Cov(x_seq)^-1 Cov(x_seq, l). Without the depth confound
    beta is proportional to (a, b, 0, ...) for the drug arm and to (1, 0, ...) for the control arm. With it,
    depth is shared by every dimension, both sisters and the liability, so the best score also reads depth
    from the other dimensions and no longer has that simple form.
    """
    s2, dl, f = sister_noise ** 2, depth_effect ** 2, fate_from_own
    w = np.zeros(d)
    w[0] = a
    if is_drug:
        w[1] = b
    one = np.ones(d)
    cov_x = (1 + s2) * np.eye(d) + dl * np.outer(one, one)
    cov_xl = w + (f * dl * w.sum() + dl) * one   # Cov(x_seq, u) = I + f * depth^2 * 11', plus depth's direct term
    return np.linalg.solve(cov_x, cov_xl)


def ground_truth(n: int = 400_000, d: int = 10, a: float = 0.55, b: float = 0.25, sister_noise: float = 0.7,
                 prevalence: float = 0.1, label_noise: float = 0.0, depth_effect: float = 0.0,
                 fate_from_own: float = 1.0, seed: int = 12345) -> dict:
    """Population values from one very large draw of the same model; no fitting involved."""
    rng = np.random.default_rng(seed)
    z, x_seq, x_tre, depth = _draw(rng, n, d, sister_noise, depth_effect)
    l = _liability(z, x_tre, True, a, b, fate_from_own, depth, depth_effect, rng)
    y = _label(l, prevalence, label_noise, rng)
    w_drug = optimal_weights(d, a, b, sister_noise, depth_effect, fate_from_own, True)
    w_fit = optimal_weights(d, a, b, sister_noise, depth_effect, fate_from_own, False)
    s_seq = x_seq @ w_drug                              # optimal score from the sequenced sister
    s_tre = x_tre @ w_drug                              # the same score on the treated sister itself
    s_fit = x_seq @ w_fit                               # optimal score learnt from the untreated arm
    return {"truth_auroc_drug": roc_auc_score(y, s_seq), "truth_auroc_fitness": roc_auc_score(y, s_fit),
            "truth_delta": roc_auc_score(y, s_seq) - roc_auc_score(y, s_fit),
            "truth_if_sister_seen": roc_auc_score(y, s_tre),
            "truth_sister_cost": roc_auc_score(y, s_tre) - roc_auc_score(y, s_seq),
            "truth_score_concordance": float(np.corrcoef(s_seq, s_tre)[0, 1]),
            "prevalence_observed": float(y.mean())}
