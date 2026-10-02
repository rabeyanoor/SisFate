"""An honest interval for the drug-specific gain: refit everything inside each bootstrap replicate.

The interval reported by `scripts/20_delta_auroc_ci.py` resamples families to re-evaluate scores that were
fitted once. It therefore describes how much the *evaluation* would move, not how much the whole procedure
would move, and the simulation study shows it covers the truth only about 52-88% of the time instead of 95%.

Here each replicate resamples families with replacement and then repeats the entire procedure on that
resample: the control-arm fitness model is refitted, the drug arm's out-of-fold scores are recomputed with
training folds capped at the control arm's size, and the gain is recalculated. That is slower by the number
of replicates, but it is the quantity the paper should quote.

Run: python scripts/28_delta_refit_bootstrap.py --cc-modes keep --n-boot 200
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.models.baselines import logistic  # noqa: E402
from persist.runner import load_context  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--cc-modes", nargs="+", default=["keep"])
ap.add_argument("--n-boot", type=int, default=200)
ap.add_argument("--n-subsamples", type=int, default=3)
ap.add_argument("--out", default="delta_auroc_refit_ci.csv",
                help="output table in results/; rows for the modes run here replace their old rows")
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("delta_refit")
C = cfg["baselines"]["logistic_C"]
R = Path(cfg["paths"]["results_dir"])


def take_families(idx, fam, n, rng):
    order = rng.permutation(np.unique(fam))
    sizes = pd.Series(fam).value_counts().reindex(order).to_numpy()
    take = set(order[: np.searchsorted(np.cumsum(sizes), n) + 1])
    return idx[np.fromiter((f in take for f in fam), bool, len(fam))]


def delta_once(Xd, yd, gd, Xc, yc, n_cap, rng, n_sub):
    """One full pass: fitness model on the control cells, capped out-of-fold drug model, difference."""
    fit, _ = logistic(Xc, yc, Xd, C, cfg["seed"])
    a_f = roc_auc_score(yd, fit)
    acc = []
    for k in range(n_sub):
        s = np.empty(len(yd))
        skf = StratifiedGroupKFold(cfg["splits"]["n_folds"], shuffle=True, random_state=k)
        for tr_i, te_i in skf.split(Xd, yd, gd):
            tr = take_families(tr_i, gd[tr_i], n_cap, rng)
            s[te_i], _ = logistic(Xd[tr], yd[tr], Xd[te_i], C, cfg["seed"])
        acc.append(roc_auc_score(yd, s))
    return float(np.mean(acc) - a_f)


rows = []
for mode in args.cc_modes:
    ctx = load_context(cfg, mode)
    X = ctx.features("pca")
    lab, arm_all = ctx.obs["labeled"].to_numpy(), ctx.obs["arm"].to_numpy()
    c_idx = np.flatnonzero(lab & (arm_all == "Control"))
    for arm in [a for a in cfg["data"]["arms"] if a != "Control"]:
        d_idx = np.flatnonzero(lab & (arm_all == arm))
        Xd, yd, gd = X[d_idx], ctx.y[d_idx], ctx.groups[d_idx]
        Xc, yc, gc = X[c_idx], ctx.y[c_idx], ctx.groups[c_idx]
        rng = np.random.default_rng(cfg["seed"])
        point = delta_once(Xd, yd, gd, Xc, yc, len(c_idx), rng, args.n_subsamples)

        # member lists once, via groupby, so resampling is cheap
        d_members = pd.Series(np.arange(len(gd))).groupby(gd).apply(np.asarray).to_dict()
        c_members = pd.Series(np.arange(len(gc))).groupby(gc).apply(np.asarray).to_dict()
        d_fams = np.array(list(d_members), dtype=object)
        c_fams = np.array(list(c_members), dtype=object)
        boot = []
        for b in range(args.n_boot):
            pick_d = rng.integers(0, len(d_fams), len(d_fams))
            pick_c = rng.integers(0, len(c_fams), len(c_fams))
            parts = [d_members[d_fams[j]] for j in pick_d]
            di = np.concatenate(parts)
            # Copies of a family keep that family's id: giving each copy its own id would let one copy
            # train while an identical copy tests, which leaks and inflates every replicate.
            gb = np.repeat(pick_d, [len(x) for x in parts])
            ci = np.concatenate([c_members[c_fams[j]] for j in pick_c])
            if yd[di].sum() < 20 or yc[ci].sum() < 20 or len(np.unique(yd[di])) < 2:
                continue
            try:
                boot.append(delta_once(Xd[di], yd[di], gb, Xc[ci], yc[ci], len(ci), rng, args.n_subsamples))
            except ValueError:
                continue
            if (b + 1) % 25 == 0:
                log.info(f"  {mode} {arm}: {b + 1}/{args.n_boot}, running CI "
                         f"[{np.quantile(boot, 0.025):+.4f}, {np.quantile(boot, 0.975):+.4f}]")
        boot = np.asarray(boot)
        # Resampling families with replacement leaves fewer distinct families to train on, which shifts the
        # replicate distribution away from the point estimate. The basic (pivotal) interval reflects that
        # shift back onto the estimate instead of taking the replicate percentiles at face value.
        lo_p, hi_p = float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))
        rows.append({"cc_mode": mode, "drug_arm": arm, "n_boot": len(boot), "delta": point,
                     "delta_lo_percentile": lo_p, "delta_hi_percentile": hi_p,
                     "delta_lo": 2 * point - hi_p, "delta_hi": 2 * point - lo_p,
                     "boot_mean": float(boot.mean()), "boot_sd": float(boot.std(ddof=1)),
                     "p_boot_delta_le_0": float((np.sum(boot <= 0) + 1) / (len(boot) + 1))})
        log.info(f"{mode} {arm}: Δ {point:+.4f} 95% CI [{rows[-1]['delta_lo']:+.4f}, "
                 f"{rows[-1]['delta_hi']:+.4f}] p {rows[-1]['p_boot_delta_le_0']:.3f}")

df = pd.DataFrame(rows)
out = R / args.out
if out.exists():  # several modes can run as separate processes and share one table
    old = pd.read_csv(out)
    df = pd.concat([old[~old["cc_mode"].isin(args.cc_modes)], df], ignore_index=True)
df.to_csv(out, index=False)
print(df.round(4).to_string(index=False))
