"""How big does a sister-cell experiment need to be?

Planning a lineage-tracing experiment means choosing three numbers: how many families to barcode, how many
of them to put in the untreated control arm, and how small a drug-specific effect is worth detecting. This
module answers that from the width of the confidence interval the framework actually produces, rather than
from a formula assuming independent cells.

The standard error of the size-matched drug-specific gain behaves like

    se(delta) ~ k / sqrt(n_effective),    n_effective = harmonic mean of the drug and control family counts

because the comparison is limited by whichever arm is smaller: the drug model is trained down to the control
arm's size, so adding drug families alone stops helping. `k` is calibrated once from the simulation study
(`results/simulation_calibration.csv`), so the numbers here are grounded in runs of the real estimator.

    >>> from persist.design import required_families, power
    >>> required_families(delta=0.02)            # families per arm for 80% power at delta = 0.02
    >>> power(delta=0.02, n_drug=4000, n_control=1800)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

__all__ = ["calibrate", "se_delta", "power", "required_families", "plan_table"]

# Fallback calibration, overwritten by calibrate() when the simulation table is present.
# Fitted on the simulation study: prevalence 0.1, sister correlation ~0.67, 10 latent dimensions.
_K = 0.60
_REF_PREVALENCE = 0.1


def calibrate(path: str | Path = "results/simulation_calibration.csv") -> float:
    """Refit the constant k from the n_families sweep of the simulation study.

    Uses the mean 95% interval width w at each family count: se = w / (2 * 1.96), and k = se * sqrt(n_eff).
    """
    global _K
    d = pd.read_csv(path)
    d = d[d["parameter"] == "n_families"]
    if d.empty:
        return _K
    n_ctrl = 1800  # the control arm held fixed in that sweep
    n_eff = 2 / (1 / d["value"].to_numpy(float) + 1 / n_ctrl)
    se = d["mean_ci_width"].to_numpy() / (2 * 1.96)
    _K = float(np.mean(se * np.sqrt(n_eff)))
    return _K


def se_delta(n_drug: int, n_control: int, prevalence: float = 0.1, k: float | None = None) -> float:
    """Standard error of the size-matched drug-specific gain, in AUROC units.

    Rarer positives mean fewer informative comparisons, so the error grows as the prevalence falls; the
    scaling is taken as 1/sqrt(prevalence * (1 - prevalence)) relative to the calibration prevalence.
    """
    k = _K if k is None else k
    n_eff = 2 / (1 / max(n_drug, 1) + 1 / max(n_control, 1))
    ref = np.sqrt(_REF_PREVALENCE * (1 - _REF_PREVALENCE))
    return float(k / np.sqrt(n_eff) * ref / np.sqrt(max(prevalence * (1 - prevalence), 1e-9)))


def power(delta: float, n_drug: int, n_control: int, prevalence: float = 0.1, alpha: float = 0.05,
          k: float | None = None) -> float:
    """Probability that the 95% interval for a true gain of `delta` excludes zero (one-sided)."""
    se = se_delta(n_drug, n_control, prevalence, k)
    return float(stats.norm.cdf(abs(delta) / se - stats.norm.ppf(1 - alpha)))


def required_families(delta: float, target_power: float = 0.8, prevalence: float = 0.1, ratio: float = 1.0,
                      alpha: float = 0.05, k: float | None = None, max_n: int = 2_000_000) -> dict:
    """Families needed per arm to detect a gain of `delta`.

    `ratio` is control families divided by drug families. Because the drug model is trained down to the
    control arm's size, a ratio far below 1 wastes drug-arm cells; 1 is the efficient choice.
    """
    lo, hi = 10, max_n
    while lo < hi:
        mid = (lo + hi) // 2
        if power(delta, mid, int(mid * ratio), prevalence, alpha, k) >= target_power:
            hi = mid
        else:
            lo = mid + 1
    return {"delta": delta, "target_power": target_power, "prevalence": prevalence, "ratio": ratio,
            "n_drug_families": lo, "n_control_families": int(lo * ratio), "total_families": int(lo * (1 + ratio)),
            "achieved_power": power(delta, lo, int(lo * ratio), prevalence, alpha, k),
            "se_delta": se_delta(lo, int(lo * ratio), prevalence, k)}


def plan_table(deltas=(0.01, 0.02, 0.03, 0.05), prevalences=(0.05, 0.1, 0.15), target_power: float = 0.8,
               ratio: float = 1.0) -> pd.DataFrame:
    """A planning grid: families per arm for each effect size and label prevalence."""
    rows = [required_families(d, target_power, p, ratio) for d in deltas for p in prevalences]
    return pd.DataFrame(rows)
