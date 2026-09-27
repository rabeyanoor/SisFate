"""Can the fitness axis be estimated without an untreated arm?

The framework's central comparison needs a control arm, and almost no lineage-tracing study has one. If a
proxy built from the treated arms alone reproduces what the control arm gives, the comparison becomes
possible wherever such data exist. ReSisTrace is the one data set where a proxy can be checked against the
real thing, because it has both.

Three proxies, none of which uses control-arm labels:
  density        the label-free typicality score (negative mean distance to the 15 nearest neighbours in
                 principal-component space within a sample). No labels at all.
  shared         the part of the signal common to the drug arms: out-of-fold scores from each drug arm are
                 rank-normalised and averaged over the *other* arms, so an arm is never its own proxy. This
                 is the proxy available whenever several treatments were run in parallel.
  leave_one_arm  a model trained on the pooled labels of the other drug arms, scored on this arm.

For each drug arm we report the proxy's own AUROC, its agreement with the control-arm fitness score, and the
drug-specific gain measured against the proxy instead of against the control model. A proxy is useful if that
gain lands near the control-arm answer; it is misleading if it makes the gain look larger.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score
from sklearn.neighbors import NearestNeighbors

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.ceiling import normal_scores  # noqa: E402
from persist.fitness import oof_scores  # noqa: E402
from persist.models.baselines import logistic  # noqa: E402
from persist.runner import load_context  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--cc-mode", default="keep")
ap.add_argument("--n-boot", type=int, default=500)
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("control_free")
R = Path(cfg["paths"]["results_dir"])
C = cfg["baselines"]["logistic_C"]
SEED = cfg["seed"]

ctx = load_context(cfg, args.cc_mode)
X = ctx.features("pca")
lab = ctx.obs["labeled"].to_numpy()
arm = ctx.obs["arm"].to_numpy()
drugs = [a for a in cfg["data"]["arms"] if a != "Control"]
c_idx = np.flatnonzero(lab & (arm == "Control"))

# label-free density within each sample
density = np.empty(len(ctx.y))
for smp in np.unique(ctx.samples):
    m = np.flatnonzero(ctx.samples == smp)
    nn = NearestNeighbors(n_neighbors=16).fit(X[m])
    d, _ = nn.kneighbors(X[m])
    density[m] = -d[:, 1:].mean(1)

# out-of-fold drug scores, needed for the "shared" proxy
oof = {}
for a in drugs:
    idx, s = oof_scores(ctx, a, X, C, SEED)
    oof[a] = pd.Series(normal_scores(pd.Series(s, index=idx)), index=idx)

rows = []
for a in drugs:
    d_idx = np.flatnonzero(lab & (arm == a))
    y = ctx.y[d_idx]
    fam = ctx.groups[d_idx]
    codes, inv = np.unique(fam, return_inverse=True)

    # the real thing: a model trained on the untreated arm
    fitness, _ = logistic(X[c_idx], ctx.y[c_idx], X[d_idx], C, SEED)
    drug_oof = oof[a].reindex(d_idx).to_numpy()

    # proxies
    others = [o for o in drugs if o != a]
    shared = np.mean([logistic(X[np.flatnonzero(lab & (arm == o))], ctx.y[np.flatnonzero(lab & (arm == o))],
                               X[d_idx], C, SEED)[0] for o in others], axis=0)
    pooled_idx = np.flatnonzero(lab & np.isin(arm, others))
    leave_one, _ = logistic(X[pooled_idx], ctx.y[pooled_idx], X[d_idx], C, SEED)
    proxies = {"control_arm_TRUE": fitness, "density": density[d_idx], "shared_other_drug_arms": shared,
               "leave_one_arm_out": leave_one}

    rng = np.random.default_rng(SEED)
    boot_idx = [rng.multinomial(len(codes), np.full(len(codes), 1 / len(codes)))[inv]
                for _ in range(args.n_boot)]
    for name, s in proxies.items():
        gain = roc_auc_score(y, drug_oof) - roc_auc_score(y, s)
        bg = [roc_auc_score(y, drug_oof, sample_weight=w) - roc_auc_score(y, s, sample_weight=w) for w in boot_idx]
        rows.append({
            "drug_arm": a, "proxy": name, "auroc_drug": roc_auc_score(y, drug_oof),
            "auroc_proxy": roc_auc_score(y, s), "gain_over_proxy": gain,
            "gain_lo": float(np.quantile(bg, 0.025)), "gain_hi": float(np.quantile(bg, 0.975)),
            "spearman_with_control_fitness": stats.spearmanr(s, fitness).statistic,
            "cc_mode": args.cc_mode,
        })
        log.info(f"{a:12s} {name:22s} AUROC {rows[-1]['auroc_proxy']:.3f}  gain {gain:+.4f} "
                 f"[{rows[-1]['gain_lo']:+.4f}, {rows[-1]['gain_hi']:+.4f}]  "
                 f"rho with control {rows[-1]['spearman_with_control_fitness']:.3f}")

df = pd.DataFrame(rows)
df.to_csv(R / "control_free_fitness.csv", index=False)
wide = df.pivot(index="drug_arm", columns="proxy", values="gain_over_proxy").round(4)
print(wide.to_string())
print("\nagreement with the control-arm fitness score (Spearman):")
print(df.pivot(index="drug_arm", columns="proxy", values="spearman_with_control_fitness").round(3).to_string())
