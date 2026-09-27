"""Step E: baselines + label-shuffled controls on within-arm CV, replicate hold-out and cross-arm transfer.

Quick decision-point run (plan step E/F):
  python scripts/04_baselines.py --models cov_logreg pca_logreg hvg_catboost --splits within --arms Olaparib
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.runner import cli  # noqa: E402

cli("baselines", ["cov_logreg", "pca_logreg", "hvg_logreg", "pca_smooth_logreg", "hvg_catboost"])
