"""Does the framework recover a drug-specific effect it is given, and are its intervals honest?

Synthetic lineage experiments (persist.simulate) fix how much of survival is generic fitness, how much is
drug-specific, and how alike sisters are. The framework is then run blind on each replicate and compared
with the population values. Two things are reported for every setting:

  bias      mean(estimate) - truth, for the size-matched drug-specific gain and for the sister ceiling
  coverage  the fraction of replicates whose 95% interval contains the truth (should be about 0.95)

Settings sweep the drug-specific strength (including zero, where the method must not invent an effect),
label noise, the number of families, sister similarity, and a sequencing-depth confound.

Run: python scripts/25_simulation.py --n-rep 40
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.fitadj import fitness_adjusted_report, grouped_oof, sister_ceiling, sister_concordance  # noqa: E402
from persist.simulate import ground_truth, simulate  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--n-rep", type=int, default=40, help="replicate experiments per setting")
ap.add_argument("--n-boot", type=int, default=400)
ap.add_argument("--n-subsamples", type=int, default=5)
ap.add_argument("--quick", action="store_true", help="a single small setting, for a smoke test")
ap.add_argument("--settings", nargs="+", help="rerun only these settings and update their rows in the existing table")
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("simulation")
R = Path(cfg["paths"]["results_dir"])

BASE = dict(n_families=4000, d=10, a=0.55, b=0.25, sister_noise=0.7, prevalence=0.1,
            label_noise=0.0, depth_effect=0.0, fate_from_own=1.0, n_control_families=1800)

SETTINGS = [("drug_specific_strength", "b", [0.0, 0.15, 0.25, 0.40]),
            ("label_noise", "label_noise", [0.0, 0.1, 0.2]),
            ("n_families", "n_families", [1000, 2000, 4000, 8000]),
            ("sister_similarity", "sister_noise", [0.4, 0.7, 1.0]),
            ("depth_confound", "depth_effect", [0.0, 0.3]),
            # the ceiling assumes the sequenced sister informs its sibling's fate only through the state
            # they share; at fate_from_own = 0 that assumption fails and the bound should break
            ("fate_driven_by_own_state", "fate_from_own", [1.0, 0.5, 0.0])]
if args.quick:
    SETTINGS = [("drug_specific_strength", "b", [0.0, 0.25])]
    args.n_rep, args.n_boot = 4, 100
if args.settings:
    SETTINGS = [s for s in SETTINGS if s[0] in args.settings]

rows = []
for setting, key, values in SETTINGS:
    for v in values:
        par = dict(BASE)
        par[key] = v
        truth = ground_truth(**{k: par[k] for k in
                                ["d", "a", "b", "sister_noise", "prevalence", "label_noise",
                                 "depth_effect", "fate_from_own"]})
        est_delta, lo_delta, hi_delta, est_ceiling, est_conc, est_truth_direct = [], [], [], [], [], []
        for rep in range(args.n_rep):
            X, y, g, arms, samples, extra = simulate(**par, seed=1000 + rep)
            rep_out = fitness_adjusted_report(X, y, g, arms, samples, control="Control",
                                              n_subsamples=args.n_subsamples, n_boot=args.n_boot, seed=rep)
            r = rep_out.iloc[0]
            est_delta.append(r["delta_size_matched"])
            lo_delta.append(r["delta_lo"])
            hi_delta.append(r["delta_hi"])
            # Ceiling, exactly as in the real analysis: one model scores both members of a pair, the
            # concordance of those two scores is measured, and the AUROC is inverted through it. The truth
            # is the AUROC reached when the treated sister's own measurement is scored instead.
            drug = arms == "Drug"
            from sklearn.base import clone as _clone

            from persist.fitadj import default_model
            s_seq = grouped_oof(X[drug], y[drug], g[drug], seed=rep)
            fitted = _clone(default_model(seed=rep)).fit(X[drug], y[drug])
            s_tre = fitted.predict_proba(extra["X_treated_sister"][drug])[:, 1]
            conc = sister_concordance(np.concatenate([s_seq, s_tre]),
                                      np.column_stack([np.arange(drug.sum()),
                                                       np.arange(drug.sum()) + drug.sum()]))
            est_conc.append(conc)
            obs = roc_auc_score(y[drug], s_seq)
            est_ceiling.append(sister_ceiling(obs, conc, y[drug].mean(), par["label_noise"],
                                              n_sim=100_000)["auroc_if_sister_seen"])
            truth_rep = roc_auc_score(y[drug], s_tre)  # same model, treated sister's own measurement
            est_truth_direct.append(truth_rep)
        est_delta, lo_delta, hi_delta = map(np.asarray, (est_delta, lo_delta, hi_delta))
        cov = float(np.mean((lo_delta <= truth["truth_delta"]) & (truth["truth_delta"] <= hi_delta)))
        rows.append({
            "setting": setting, "parameter": key, "value": v, "n_rep": args.n_rep,
            "truth_delta": truth["truth_delta"], "mean_delta": est_delta.mean(),
            "bias_delta": est_delta.mean() - truth["truth_delta"], "sd_delta": est_delta.std(ddof=1),
            "coverage_delta_95": cov, "mean_ci_width": float(np.mean(hi_delta - lo_delta)),
            "false_positive_rate": float(np.mean(lo_delta > 0)) if v == 0 and key == "b" else np.nan,
            "truth_if_sister_seen": truth["truth_if_sister_seen"],
            "truth_sister_cost": truth["truth_sister_cost"],
            "mean_ceiling": float(np.mean(est_ceiling)),
            "bias_ceiling": float(np.mean(est_ceiling)) - truth["truth_if_sister_seen"],
            "mean_score_concordance": float(np.mean(est_conc)),
            "truth_score_concordance": truth["truth_score_concordance"],
            "empirical_if_sister_seen": float(np.mean(est_truth_direct)),
            "bias_ceiling_vs_empirical": float(np.mean(est_ceiling)) - float(np.mean(est_truth_direct)),
            "truth_auroc_drug": truth["truth_auroc_drug"], "truth_auroc_fitness": truth["truth_auroc_fitness"],
        })
        log.info(f"{setting}={v}: truth Δ {truth['truth_delta']:.4f}, estimate {est_delta.mean():.4f} "
                 f"(bias {rows[-1]['bias_delta']:+.4f}), coverage {cov:.2f} | ceiling est "
                 f"{rows[-1]['mean_ceiling']:.3f} vs empirical {rows[-1]['empirical_if_sister_seen']:.3f} "
                 f"(bias {rows[-1]['bias_ceiling_vs_empirical']:+.3f}), concordance est "
                 f"{rows[-1]['mean_score_concordance']:.3f}")

df = pd.DataFrame(rows)
if args.settings and (R / "simulation_calibration.csv").exists():
    old = pd.read_csv(R / "simulation_calibration.csv")
    key = ["setting", "value"]
    new = df.set_index(key)
    old = old.set_index(key)
    old.update(new)
    df = old.reset_index()[df.columns]
df.to_csv(R / "simulation_calibration.csv", index=False)
print(df.round(4).to_string(index=False))
