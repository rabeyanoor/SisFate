"""Fate labels, lineage groups and sister pairs from the authors' cell_info columns.

Column semantics (from ReSisTrace codes/Preprocess_*.Rmd):
  drugSens      pre-resistant : pre-treatment cell with a *perfect* lineage-label match in the post sample
                pre-sensitive : no perfect match (includes partial matches -> one source of label noise)
                NA            : no lineage label detected -> unusable, excluded
  sisters       family id shared by pre-treatment cells with identical lineage labels (NA = singleton)
  prer_r_group  family id linking pre-resistant cells to their surviving sisters in the post sample
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd


def add_labels(obs: pd.DataFrame, positive: str = "pre-resistant", negative: str = "pre-sensitive") -> pd.DataFrame:
    obs = obs.copy()
    y = np.full(len(obs), -1, dtype=np.int8)
    y[(obs["drugSens"] == positive).to_numpy()] = 1
    y[(obs["drugSens"] == negative).to_numpy()] = 0
    obs["y"] = y
    obs["labeled"] = y >= 0
    obs["lineage_group"] = lineage_groups(obs)
    return obs


def lineage_groups(obs: pd.DataFrame) -> np.ndarray:
    """Connected components over shared `sisters` / `prer_r_group` ids (ids are per-sample)."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        parent[find(a)] = find(b)

    keys = []
    for cell, sample, sis, grp in zip(obs.index, obs["sample"], obs.get("sisters"), obs.get("prer_r_group")):
        node = f"cell:{cell}"
        find(node)
        if pd.notna(sis):
            union(node, f"sis:{sample}:{int(sis)}")
        if pd.notna(grp):
            union(node, f"grp:{sample}:{int(grp)}")
        keys.append(node)
    return np.array([find(k) for k in keys])


def sister_pairs(obs: pd.DataFrame, mask: np.ndarray | None = None) -> np.ndarray:
    """All within-family pairs of pre-treatment sisters, as positional indices (n_pairs x 2)."""
    pos = np.arange(len(obs))
    if mask is not None:
        pos = pos[mask]
    sub = obs.iloc[pos]
    pairs = []
    has = sub["sisters"].notna().to_numpy()
    keys = sub["sample"].astype(str).to_numpy()[has] + ":" + sub["sisters"].to_numpy()[has].astype(int).astype(str)
    for _, idx in pd.Series(pos[has]).groupby(keys):
        pairs.extend(itertools.combinations(idx.to_numpy(), 2))
    return np.asarray(pairs, dtype=np.int64).reshape(-1, 2)


def shuffle_labels_by_group(y: np.ndarray, groups: np.ndarray, strata: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Permute labels at the lineage-group level within each stratum (sample).

    Keeps sisters label-concordant, so the shuffled control has the same dependence structure.
    """
    out = y.copy()
    for s in np.unique(strata):
        m = strata == s
        g = groups[m]
        uniq, inv = np.unique(g, return_inverse=True)
        glab = np.zeros(len(uniq), dtype=y.dtype)
        glab[inv] = y[m]  # labels are constant within a family
        out[m] = rng.permutation(glab)[inv]
    return out
