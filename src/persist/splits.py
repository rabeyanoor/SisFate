"""Evaluation designs. Every split keeps whole lineage families on one side.

  within        StratifiedGroupKFold inside one arm (both replicates pooled)
  rep_holdout   train on replicate r, test on the other replicate of the same arm
  cross_arm     train on arm A (both replicates), test on arm B; Control -> drug = fitness transfer
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold


@dataclass
class Split:
    split: str
    train: str
    test: str
    fold: int
    train_idx: np.ndarray
    test_idx: np.ndarray

    @property
    def tag(self) -> str:
        return f"{self.split}:{self.train}->{self.test}:f{self.fold}"


def _labeled(obs: pd.DataFrame, **eq) -> np.ndarray:
    m = obs["labeled"].to_numpy().copy()
    for col, val in eq.items():
        m &= (obs[col] == val).to_numpy()
    return np.flatnonzero(m)


def within_arm(obs: pd.DataFrame, arm: str, n_folds: int, seed: int) -> list[Split]:
    idx = _labeled(obs, arm=arm)
    y = obs["y"].to_numpy()[idx]
    g = obs["lineage_group"].to_numpy()[idx]
    skf = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    return [
        Split("within", arm, arm, k, idx[tr], idx[te])
        for k, (tr, te) in enumerate(skf.split(idx, y, g))
    ]


def replicate_holdout(obs: pd.DataFrame, arm: str, replicates=(1, 2)) -> list[Split]:
    out = []
    for r_tr in replicates:
        for r_te in replicates:
            if r_tr == r_te:
                continue
            out.append(
                Split("rep_holdout", f"{arm}_{r_tr}", f"{arm}_{r_te}", 0,
                      _labeled(obs, arm=arm, replicate=r_tr), _labeled(obs, arm=arm, replicate=r_te))
            )
    return out


def cross_arm(obs: pd.DataFrame, arms: list[str]) -> list[Split]:
    return [
        Split("cross_arm", a, b, 0, _labeled(obs, arm=a), _labeled(obs, arm=b))
        for a in arms for b in arms if a != b
    ]


def all_splits(obs: pd.DataFrame, cfg: dict, kinds=("within", "rep_holdout", "cross_arm")) -> list[Split]:
    arms = cfg["data"]["arms"]
    out: list[Split] = []
    if "within" in kinds:
        for a in arms:
            out += within_arm(obs, a, cfg["splits"]["n_folds"], cfg["seed"])
    if "rep_holdout" in kinds:
        for a in arms:
            out += replicate_holdout(obs, a, cfg["data"]["replicates"])
    if "cross_arm" in kinds:
        out += cross_arm(obs, arms)
    return out


def inner_validation(obs: pd.DataFrame, train_idx: np.ndarray, frac: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Group-aware hold-out from the training cells (for early stopping only)."""
    g = obs["lineage_group"].to_numpy()[train_idx]
    gss = GroupShuffleSplit(n_splits=1, test_size=frac, random_state=seed)
    tr, va = next(gss.split(train_idx, groups=g))
    return train_idx[tr], train_idx[va]
