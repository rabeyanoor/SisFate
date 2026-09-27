"""The sister-ceiling estimator assumes the sequenced sister informs its sibling's fate only through the
state the two share. This checks the consequence: when that assumption holds the estimate is tight, and when
it fails the estimate errs upward, so the reported ceiling is an upper bound and the sister cost is not
understated."""
import numpy as np
from sklearn.metrics import roc_auc_score

from persist.fitadj import sister_ceiling, sister_concordance
from persist.simulate import ground_truth


def _estimate(fate_from_own, n=120_000, seed=7):
    """Run the estimator on population quantities, so only its assumption is being tested, not sampling."""
    t = ground_truth(n=n, fate_from_own=fate_from_own, seed=seed)
    est = sister_ceiling(t["truth_auroc_drug"], t["truth_score_concordance"],
                         0.1, label_noise=0.0, n_sim=120_000)
    return est["auroc_if_sister_seen"], t["truth_if_sister_seen"]


def test_tight_when_assumption_holds():
    est, truth = _estimate(1.0)
    assert abs(est - truth) < 0.02, (est, truth)


def test_upper_bound_when_assumption_fails():
    for f in [0.75, 0.5, 0.25, 0.0]:
        est, truth = _estimate(f)
        assert est >= truth - 0.02, (f, est, truth)
    # and the failure is substantial at the extreme, which is why the assumption must be stated
    est0, truth0 = _estimate(0.0)
    assert est0 - truth0 > 0.05, (est0, truth0)


def test_sister_cost_is_not_understated():
    for f in [1.0, 0.5, 0.0]:
        t = ground_truth(n=120_000, fate_from_own=f, seed=11)
        est = sister_ceiling(t["truth_auroc_drug"], t["truth_score_concordance"], 0.1, 0.0, n_sim=120_000)
        assert est["sister_cost"] >= t["truth_sister_cost"] - 0.02, (f, est["sister_cost"], t["truth_sister_cost"])
