"""The shipped example data reproduce the paper's main result for one arm."""
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

from persist.fitadj import grouped_oof

DATA = Path(__file__).resolve().parents[1] / "data" / "example" / "resistrace_pca.npz"


def test_example_data_reproduces_carboplatin_auroc():
    d = np.load(DATA)
    assert d["X_pca"].shape == (32642, 50) and d["sister_pairs"].shape == (3477, 2)
    m = d["arm"] == "Carboplatin"
    s = grouped_oof(d["X_pca"][m], d["y"][m], d["family"][m])
    assert abs(roc_auc_score(d["y"][m], s) - 0.747) < 0.001
