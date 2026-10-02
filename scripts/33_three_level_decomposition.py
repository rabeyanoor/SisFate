"""Split the drug-arm signal three ways: growth fitness, treatment in general, and the particular drug.

The size-matched gain (scripts/20, 28) compares a drug arm's own model with the untreated-arm model. What it
counts as drug-specific can still be shared between treatments: a cell that copes with being treated at all,
whatever the agent. Three models of equal training size, all scored on the same drug-arm cells, separate the
two:

    fitness     trained on the untreated control arm
    treatment   trained on the *other* drug arms (pooled), never on this arm
    own         trained on this arm's labels (lineage-grouped out-of-fold scores)

Each is trained on random whole families totalling as many cells as the labelled control arm, so no model
has more data than another. Then

    general-treatment gain = AUROC(treatment) - AUROC(fitness)
    drug-unique gain       = AUROC(own)       - AUROC(treatment)

and the two add up to the size-matched drug-specific gain of scripts/20 and 28. "Treatment in general" means
whatever the treated arms share and the control arm lacks, which includes any difference in how the arms
were handled, not only biology.

An earlier version fitted one multi-task logistic model with a shared, a treated-arm and a per-arm block of
weights. Its full-model AUROC hardly moved across block penalties (0.7285-0.7299) while the split between the
treated-arm and per-arm blocks swung from one extreme to the other, so the penalties, not the data, decided
that split (logs/three_level_penalty_grid_partial.log). The comparison above has no such free choice.

Intervals refit everything on family-bootstrap resamples (control, this arm and the other arms resampled
separately) and use the basic bootstrap interval, as in scripts/28.

Run: python scripts/33_three_level_decomposition.py --cc-modes keep regress_all --n-boot 200
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
ap.add_argument("--n-subsamples", type=int, default=5, help="training subsamples averaged for the point estimate")
ap.add_argument("--n-subsamples-boot", type=int, default=3, help="the same inside each bootstrap replicate")
ap.add_argument("--arms", nargs="+", default=["Carboplatin", "Olaparib", "NK"],
                help="drug arms to run; separate processes can share the output tables")
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("three_level")
C = cfg["baselines"]["logistic_C"]
SEED = cfg["seed"]
R = Path(cfg["paths"]["results_dir"])
DRUGS = ["Carboplatin", "Olaparib", "NK"]


def take_families(idx, fam, n, rng):
    """Random whole families from `idx` until at least `n` cells are taken (as in scripts/20 and 28)."""
    order = rng.permutation(np.unique(fam))
    sizes = pd.Series(fam).value_counts().reindex(order).to_numpy()
    take = set(order[: np.searchsorted(np.cumsum(sizes), n) + 1])
    return idx[np.fromiter((f in take for f in fam), bool, len(fam))]


def three_aurocs(X, y, fam, d, o, c, rng, n_sub):
    """AUROC of the fitness, other-arm and own-arm models on the cells `d`, at the control arm's size."""
    n_cap = len(c)
    yd, gd = y[d], fam[d]
    fit, _ = logistic(X[c], y[c], X[d], C, SEED)
    a_o, a_d = [], []
    for k in range(n_sub):
        tr = take_families(o, fam[o], n_cap, rng)
        a_o.append(roc_auc_score(yd, logistic(X[tr], y[tr], X[d], C, SEED)[0]))
        s = np.empty(len(d))
        for tr_i, te_i in StratifiedGroupKFold(cfg["splits"]["n_folds"], shuffle=True, random_state=k).split(X[d], yd, gd):
            tr = d[take_families(tr_i, gd[tr_i], n_cap, rng)]
            s[te_i], _ = logistic(X[tr], y[tr], X[d[te_i]], C, SEED)
        a_d.append(roc_auc_score(yd, s))
    return roc_auc_score(yd, fit), float(np.mean(a_o)), float(np.mean(a_d))


def resample(idx, fam, rng, tag):
    """Families drawn with replacement; copies of a family keep one id so they never straddle a split."""
    members = pd.Series(idx).groupby(fam[idx]).apply(np.asarray)
    pick = rng.integers(0, len(members), len(members))
    parts = [members.iloc[j] for j in pick]
    return np.concatenate(parts), np.repeat([f"{tag}{j}" for j in pick], [len(p) for p in parts])


rows, boot_rows = [], []
for cc in args.cc_modes:
    ctx = load_context(cfg, cc)
    lab = ctx.obs["labeled"].to_numpy()
    arm = ctx.obs["arm"].astype(str).to_numpy()
    X, y, fam = ctx.features("pca"), ctx.y, ctx.groups
    c_idx = np.flatnonzero(lab & (arm == "Control"))
    for k in args.arms:
        d_idx = np.flatnonzero(lab & (arm == k))
        o_idx = np.flatnonzero(lab & np.isin(arm, [a for a in DRUGS if a != k]))
        rng = np.random.default_rng(SEED)
        a_f, a_o, a_d = three_aurocs(X, y, fam, d_idx, o_idx, c_idx, rng, args.n_subsamples)
        log.info(f"{cc} {k}: fitness {a_f:.4f}, other drug arms {a_o:.4f}, own arm {a_d:.4f} "
                 f"(n_cap {len(c_idx)})")

        boot = []
        for b in range(args.n_boot):
            # resampled indices into the full arrays; family ids rewritten so copies stay together
            d_b, gd_b = resample(d_idx, fam, rng, "d")
            o_b, go_b = resample(o_idx, fam, rng, "o")
            c_b, gc_b = resample(c_idx, fam, rng, "c")
            Xb = np.concatenate([X[d_b], X[o_b], X[c_b]])
            yb = np.concatenate([y[d_b], y[o_b], y[c_b]])
            fb = np.concatenate([gd_b, go_b, gc_b])
            nd, no = len(d_b), len(o_b)
            pos = np.arange(len(yb))
            try:
                boot.append(three_aurocs(Xb, yb, fb, pos[:nd], pos[nd:nd + no], pos[nd + no:], rng,
                                         args.n_subsamples_boot))
            except ValueError:  # a resample without both classes in some fold
                continue
            boot_rows.append({"cc_mode": cc, "arm": k, "boot": b, "auroc_fitness": boot[-1][0],
                              "auroc_other_arms": boot[-1][1], "auroc_own": boot[-1][2]})
            if (b + 1) % 50 == 0:
                log.info(f"  {cc} {k}: {b + 1}/{args.n_boot}")
        B = np.asarray(boot)
        point = {"general": a_o - a_f, "unique": a_d - a_o, "total": a_d - a_f}
        reps = {"general": B[:, 1] - B[:, 0], "unique": B[:, 2] - B[:, 1], "total": B[:, 2] - B[:, 0]}
        row = {"cc_mode": cc, "arm": k, "n_cap": len(c_idx), "n_boot": len(B),
               "auroc_fitness": a_f, "auroc_other_drug_arms": a_o, "auroc_own_arm": a_d}
        for name, v in point.items():
            lo_p, hi_p = np.quantile(reps[name], [0.025, 0.975])
            row[f"gain_{name}"] = v
            row[f"gain_{name}_lo"] = 2 * v - hi_p   # basic (pivotal) interval, as in scripts/28
            row[f"gain_{name}_hi"] = 2 * v - lo_p
            row[f"gain_{name}_p_le_0"] = float((np.sum(reps[name] <= 0) + 1) / (len(B) + 1))
        row["share_of_total_from_general"] = point["general"] / point["total"] if point["total"] > 0 else np.nan
        rows.append(row)
        log.info(f"{cc} {k}: general {point['general']:+.4f} [{row['gain_general_lo']:+.4f}, "
                 f"{row['gain_general_hi']:+.4f}], unique {point['unique']:+.4f} [{row['gain_unique_lo']:+.4f}, "
                 f"{row['gain_unique_hi']:+.4f}], total {point['total']:+.4f}")

def save(df, name):
    """Replace this run's (cc_mode, arm) rows and keep the rest, so per-arm processes can share a table."""
    path = R / name
    if path.exists():
        old = pd.read_csv(path)
        done = set(zip(df["cc_mode"], df["arm"]))
        old = old[[(m, a) not in done for m, a in zip(old["cc_mode"], old["arm"])]]
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv(path, index=False)
    return df


out = pd.DataFrame(rows)
save(out, "three_level_decomposition.csv")
save(pd.DataFrame(boot_rows), "three_level_bootstrap.csv")
print(out.round(4).to_string(index=False))
