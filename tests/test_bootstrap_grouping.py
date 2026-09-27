"""A cluster bootstrap must keep every drawn copy of a family in the same cross-validation group.

If each copy is given its own group id, one copy can train while an identical copy tests, which leaks and
inflates every replicate. This reproduces that on families of identical cells, where any AUROC above the
no-bootstrap value can only come from leakage. Correct grouping instead sits slightly below that value,
because resampling with replacement leaves fewer distinct families to train on.
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold


def _oof(X, y, g):
    s = np.empty(len(y))
    for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=0).split(X, y, g):
        s[te] = LogisticRegression(max_iter=2000).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return roc_auc_score(y, s)


def test_family_ids_do_not_leak_but_per_copy_ids_do():
    rng = np.random.default_rng(0)
    n_fam, per = 200, 3
    X = np.repeat(rng.standard_normal((n_fam, 5)), per, axis=0)  # identical cells within a family
    y = np.repeat(rng.integers(0, 2, n_fam), per)
    fam = np.repeat(np.arange(n_fam), per)
    members = {f: np.flatnonzero(fam == f) for f in range(n_fam)}
    truth = _oof(X, y, fam)

    per_copy, family = [], []
    for _ in range(12):
        pick = rng.integers(0, n_fam, n_fam)
        parts = [members[j] for j in pick]
        idx = np.concatenate(parts)
        sizes = [len(p) for p in parts]
        per_copy.append(_oof(X[idx], y[idx], np.repeat(np.arange(len(parts)), sizes)))
        family.append(_oof(X[idx], y[idx], np.repeat(pick, sizes)))

    # Leakage pushes the per-copy version above the unbootstrapped value.
    assert np.mean(per_copy) > truth + 0.01, "per-copy ids should leak and inflate"
    # Correct grouping does not inflate. It sits slightly below, because resampling with replacement
    # leaves fewer distinct families to train on; that is a property of the bootstrap, not leakage.
    assert np.mean(family) <= truth + 0.005, "family ids should not inflate"
    assert np.mean(per_copy) - np.mean(family) > 0.02, "the two groupings should differ clearly"
