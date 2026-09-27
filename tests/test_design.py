"""Checks on the experiment-design calculator: the numbers must move the way a planner expects."""
import numpy as np

from persist.design import plan_table, power, required_families, se_delta


def test_se_shrinks_with_size_and_rarer_labels_cost_more():
    assert se_delta(4000, 4000) < se_delta(1000, 1000)
    # four times the families halves the standard error
    assert np.isclose(se_delta(4000, 4000) / se_delta(1000, 1000), 0.5, atol=0.02)
    assert se_delta(4000, 4000, prevalence=0.05) > se_delta(4000, 4000, prevalence=0.1)


def test_adding_only_drug_families_saturates():
    """The drug model is trained down to the control arm, so a small control arm caps precision."""
    small_control = se_delta(4000, 200)
    much_more_drug = se_delta(40000, 200)
    assert much_more_drug > 0.9 * small_control  # barely improves
    assert se_delta(4000, 4000) < 0.5 * small_control  # growing the control arm does improve


def test_power_is_monotone_and_bounded():
    assert power(0.0, 4000, 4000) < 0.06          # no effect: at most the false-positive rate
    assert power(0.05, 4000, 4000) > power(0.02, 4000, 4000)
    assert power(0.02, 8000, 8000) > power(0.02, 2000, 2000)
    assert 0 <= power(0.02, 4000, 4000) <= 1


def test_required_families_matches_its_own_power():
    r = required_families(delta=0.02, target_power=0.8)
    assert r["achieved_power"] >= 0.8
    assert power(0.02, r["n_drug_families"] - 1, r["n_control_families"] - 1) < 0.8 + 1e-6
    # a smaller effect needs more cells
    assert required_families(0.01)["n_drug_families"] > required_families(0.03)["n_drug_families"]


def test_plan_table_shape():
    t = plan_table(deltas=(0.01, 0.02), prevalences=(0.05, 0.1))
    assert len(t) == 4 and {"n_drug_families", "achieved_power"} <= set(t.columns)
