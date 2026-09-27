"""Synthetic checks for persist.fitadj: known fitness vs drug-specific structure is recovered."""
import numpy as np

from persist.fitadj import family_permutation_null, fitness_adjusted_report, sister_ceiling, sister_concordance


def simulate(n_fam=1500, specific=0.0, seed=0):
    """Families of two sisters share a state; fate = fitness axis (+ drug axis in drug arms) + noise."""
    rng = np.random.default_rng(seed)
    rows = []
    for arm in ["Control", "DrugA"]:
        for f in range(n_fam):
            z = rng.standard_normal(5)
            liab = z[0] + (specific * z[1] if arm == "DrugA" else 0) + rng.standard_normal()
            for _ in range(2):
                x = z + 0.5 * rng.standard_normal(5)
                rows.append((x, liab, f"{arm}_{f}", arm))
    X = np.array([r[0] for r in rows])
    liab = np.array([r[1] for r in rows])
    arms = np.array([r[3] for r in rows])
    y = np.zeros(len(rows), int)
    for a in ["Control", "DrugA"]:
        m = arms == a
        y[m] = liab[m] > np.quantile(liab[m], 0.85)
    return X, y, np.array([r[2] for r in rows]), arms


def test_pure_fitness_gives_no_drug_specific_gain():
    X, y, g, arms = simulate(specific=0.0)
    r = fitness_adjusted_report(X, y, g, arms, n_subsamples=3, n_boot=200).iloc[0]
    assert r["auroc_drug"] > 0.7
    assert abs(r["delta_size_matched"]) < 0.02
    assert r["delta_lo"] < 0 < r["delta_hi"]


def test_drug_specific_axis_is_detected():
    X, y, g, arms = simulate(specific=1.0)
    r = fitness_adjusted_report(X, y, g, arms, n_subsamples=3, n_boot=200).iloc[0]
    assert r["delta_size_matched"] > 0.05
    assert r["delta_lo"] > 0
    assert r["lrt_p"] < 1e-6


def test_permutation_null_is_centred_and_significant():
    X, y, g, arms = simulate(n_fam=600)
    m = arms == "Control"
    res = family_permutation_null(X[m], y[m], g[m], arms[m], n_perm=20)
    # in 5 dimensions a model fitted to permuted labels picks a random direction, so the null is wide;
    # its mean must still be 0.5 within sampling error
    assert abs(res["null_mean"] - 0.5) < 3 * res["null_sd"] / np.sqrt(20)
    assert res["p"] <= 1 / 21 + 1e-9


def test_sister_ceiling_is_above_observed():
    rng = np.random.default_rng(1)
    s = rng.standard_normal(4000)
    pairs = np.arange(4000).reshape(-1, 2)
    s[pairs[:, 1]] = 0.8 * s[pairs[:, 0]] + 0.6 * rng.standard_normal(2000)
    rho = sister_concordance(s, pairs)
    assert 0.7 < rho < 0.9
    out = sister_ceiling(0.72, rho, 0.1, 0.1, n_sim=100_000)
    assert out["auroc_if_sister_seen"] > 0.72 and out["sister_cost"] > 0
