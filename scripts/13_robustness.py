"""Robustness checks for the headline PCA-logistic result.

  singletons_only   drop cells whose sister was also sequenced before treatment (Dai et al. restricted
                    their DE to such singletons)
  benchmark_protocol  mimic Shen et al. 2026: olaparib arm, pre-resistant vs an equal-size random subset
                    of pre-sensitive cells (3 draws), plain stratified 5-fold CV without lineage groups
  grouped_balanced  same balanced draws but with lineage-grouped folds, to show the grouping effect
  permutation_p     family-level label permutations (n=200) for an exact within-arm p-value
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.labels import shuffle_labels_by_group  # noqa: E402
from persist.models.baselines import logistic  # noqa: E402
from persist.runner import load_context  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--cc-mode", choices=["keep", "regress", "regress_all"])
ap.add_argument("--n-perm", type=int, default=200)
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("robustness")
ctx = load_context(cfg, args.cc_mode)
X, y, g, obs = ctx.features("pca"), ctx.y, ctx.groups, ctx.obs
C, seed = cfg["baselines"]["logistic_C"], cfg["seed"]


def cv_auc(idx, splitter, groups=None, labels=None):
    lab = y[idx] if labels is None else labels
    s = np.zeros(len(idx))
    for tr, te in splitter.split(idx, lab, groups):
        s[te], _ = logistic(X[idx[tr]], lab[tr], X[idx[te]], C, seed)
    return roc_auc_score(y[idx], s), s


rows = []
sgkf = StratifiedGroupKFold(cfg["splits"]["n_folds"], shuffle=True, random_state=seed)
for arm in cfg["data"]["arms"]:
    lab = obs["labeled"].to_numpy() & (obs["arm"] == arm).to_numpy()
    idx_all = np.flatnonzero(lab)
    idx_single = np.flatnonzero(lab & obs["sisters"].isna().to_numpy())
    a_all, s_all = cv_auc(idx_all, sgkf, g[idx_all])
    a_single, _ = cv_auc(idx_single, sgkf, g[idx_single])
    # exact permutation p-value: refit on family-level shuffles, same folds
    rng = np.random.default_rng(seed)
    null = []
    for _ in range(args.n_perm):
        yp = shuffle_labels_by_group(y[idx_all], g[idx_all], ctx.samples[idx_all], rng)
        s = np.zeros(len(idx_all))
        for tr, te in sgkf.split(idx_all, yp, g[idx_all]):
            s[te], _ = logistic(X[idx_all[tr]], yp[tr], X[idx_all[te]], C, seed)
        null.append(roc_auc_score(yp, s))
    null = np.array(null)
    rows += [
        {"check": "all_cells", "arm": arm, "n": len(idx_all), "auroc": a_all,
         "perm_null_mean": null.mean(), "perm_null_sd": null.std(),
         "perm_p": (1 + (null >= a_all).sum()) / (1 + len(null))},
        {"check": "singletons_only", "arm": arm, "n": len(idx_single), "auroc": a_single},
    ]
    log.info(f"{arm}: all={a_all:.3f} singletons={a_single:.3f} null={null.mean():.3f}±{null.std():.3f}")

# Shen et al. protocol on olaparib: balanced draws, ungrouped vs grouped CV
lab = np.flatnonzero(obs["labeled"].to_numpy() & (obs["arm"] == "Olaparib").to_numpy())
pos, neg = lab[y[lab] == 1], lab[y[lab] == 0]
skf = StratifiedKFold(5, shuffle=True, random_state=seed)
for draw in range(3):
    rng = np.random.default_rng(seed + draw)
    idx = np.concatenate([pos, rng.choice(neg, len(pos), replace=False)])
    a_plain, _ = cv_auc(idx, skf)
    a_group, _ = cv_auc(idx, sgkf, g[idx])
    rows += [{"check": "benchmark_protocol_ungrouped", "arm": "Olaparib", "n": len(idx), "auroc": a_plain, "draw": draw},
             {"check": "benchmark_protocol_grouped", "arm": "Olaparib", "n": len(idx), "auroc": a_group, "draw": draw}]

df = pd.DataFrame(rows)
df["cc_mode"] = ctx.adata.uns["cc_mode"]
df.to_csv(Path(cfg["paths"]["results_dir"]) / f"robustness_{ctx.adata.uns['cc_mode']}.csv", index=False)
print(df.round(4).to_string(index=False))
