"""Confidence intervals for the drug-specific gain over the fitness model (size-matched ΔAUROC).

For each drug arm, every labelled cell gets an out-of-fold drug score from lineage-grouped 5-fold CV in
which each training fold is subsampled (whole families) to the number of labelled control cells, so the
drug model never has more training data than the fitness model. The fitness score is the control-trained
model applied to the same cells. ΔAUROC = AUROC(drug) − AUROC(fitness) on all drug-arm cells, averaged over
subsampling seeds. The 95% CI comes from a paired family-level bootstrap: each resample reweights whole
families, and the seed-averaged ΔAUROC is recomputed with both scores on the same resampled cells, so the
interval covers sampling of families as well as the subsampling of training data. (A DeLong test would
treat cells as independent, which sisters are not.)
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.models.baselines import logistic  # noqa: E402
from persist.runner import load_context  # noqa: E402
from persist.splits import within_arm  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--cc-modes", nargs="+", default=["keep", "regress", "regress_all"])
ap.add_argument("--n-seeds", type=int, default=10)
ap.add_argument("--n-boot", type=int, default=1000)
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("delta_ci")
C = cfg["baselines"]["logistic_C"]


def subsample_families(idx, fam, n, rng):
    order = rng.permutation(np.unique(fam))
    sizes = pd.Series(fam).value_counts().reindex(order).to_numpy()
    take = set(order[: np.searchsorted(np.cumsum(sizes), n) + 1])
    return idx[np.array([f in take for f in fam])]


rows, draws = [], []
for mode in args.cc_modes:
    ctx = load_context(cfg, mode)
    X = ctx.features("pca")
    lab, arm_all = ctx.obs["labeled"].to_numpy(), ctx.obs["arm"].to_numpy()
    c_idx = np.flatnonzero(lab & (arm_all == "Control"))
    for arm in [a for a in cfg["data"]["arms"] if a != "Control"]:
        d_idx = np.flatnonzero(lab & (arm_all == arm))
        y = ctx.y[d_idx]
        fit, _ = logistic(X[c_idx], ctx.y[c_idx], X[d_idx], C, cfg["seed"])
        pos = pd.Series(np.arange(len(d_idx)), index=d_idx)
        fam = ctx.groups[d_idx]
        fam_codes, fam_inv = np.unique(fam, return_inverse=True)
        drugs = np.empty((args.n_seeds, len(d_idx)))
        for s in range(args.n_seeds):
            rng = np.random.default_rng(1000 + s)
            for sp in within_arm(ctx.obs, arm, cfg["splits"]["n_folds"], s):
                tr = subsample_families(sp.train_idx, ctx.groups[sp.train_idx], len(c_idx), rng)
                drugs[s, pos[sp.test_idx].to_numpy()], _ = logistic(X[tr], ctx.y[tr], X[sp.test_idx], C, cfg["seed"])
        a_f = roc_auc_score(y, fit)
        a_d = np.array([roc_auc_score(y, d) for d in drugs])
        rng = np.random.default_rng(cfg["seed"])
        boot = np.empty(args.n_boot)
        for b in range(args.n_boot):
            w = rng.multinomial(len(fam_codes), np.full(len(fam_codes), 1 / len(fam_codes)))[fam_inv]
            f_b = roc_auc_score(y, fit, sample_weight=w)
            boot[b] = np.mean([roc_auc_score(y, d, sample_weight=w) for d in drugs]) - f_b
        delta = a_d - a_f
        rows.append({"cc_mode": mode, "drug_arm": arm, "n_seeds": args.n_seeds, "n_boot": args.n_boot,
                     "n_train_cap": len(c_idx), "n_families": len(fam_codes),
                     "auroc_drug_size_matched": a_d.mean(), "auroc_fitness": a_f, "delta_mean": delta.mean(),
                     "delta_seed_sd": delta.std(ddof=1), "delta_seed_min": delta.min(), "delta_seed_max": delta.max(),
                     "delta_lo": np.quantile(boot, 0.025), "delta_hi": np.quantile(boot, 0.975),
                     "p_boot_delta_le_0": (np.sum(boot <= 0) + 1) / (args.n_boot + 1)})
        draws += [{"cc_mode": mode, "drug_arm": arm, "seed": s, "auroc_drug_size_matched": a_d[s], "delta": delta[s]}
                  for s in range(args.n_seeds)]
        r = rows[-1]
        log.info(f"{mode} {arm}: drug {r['auroc_drug_size_matched']:.3f} fitness {a_f:.3f} Δ {r['delta_mean']:.4f} "
                 f"(seed s.d. {r['delta_seed_sd']:.4f}) 95% CI [{r['delta_lo']:.4f}, {r['delta_hi']:.4f}] p {r['p_boot_delta_le_0']:.4f}")

res = Path(cfg["paths"]["results_dir"])
pd.DataFrame(draws).to_csv(res / "delta_auroc_ci_seeds.csv", index=False)
summ = pd.DataFrame(rows)
summ.to_csv(res / "delta_auroc_ci.csv", index=False)
print(summ.round(4).to_string(index=False))
