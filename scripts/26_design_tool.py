"""Planning numbers for a new sister-cell experiment.

Turns the simulation study into advice an experimentalist can use: how many families to barcode, how to split
them between the treated and untreated arms, and what size of drug-specific effect that buys. The standard
error is calibrated on `results/simulation_calibration.csv`, so these numbers come from runs of the estimator
rather than from a formula that assumes independent cells.

Run: python scripts/26_design_tool.py
"""
import argparse
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.design import calibrate, plan_table, power, required_families, se_delta  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--target-power", type=float, default=0.8)
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("design")
R = Path(cfg["paths"]["results_dir"])

cal = R / "simulation_calibration.csv"
k = calibrate(cal) if cal.exists() else None
log.info(f"calibration constant k = {k if k else 'default'} ({'from ' + str(cal) if k else 'built-in'})")

plan = plan_table(deltas=(0.01, 0.02, 0.03, 0.05), prevalences=(0.05, 0.1, 0.15),
                  target_power=args.target_power)
plan.to_csv(R / "design_plan.csv", index=False)
print("Families per arm needed to detect a drug-specific gain, at "
      f"{args.target_power:.0%} power (equal arms):")
print(plan.pivot(index="delta", columns="prevalence", values="n_drug_families").to_string())

# How the two arms trade off: the drug model is trained down to the control arm's size, so an under-powered
# control arm caps the whole comparison however many drug families are added.
rows = []
for n_ctrl in [500, 1000, 2000, 4000, 8000]:
    for n_drug in [1000, 2000, 4000, 8000, 16000]:
        rows.append({"n_control_families": n_ctrl, "n_drug_families": n_drug,
                     "se_delta": se_delta(n_drug, n_ctrl), "power_at_delta_0.02": power(0.02, n_drug, n_ctrl)})
split = pd.DataFrame(rows)
split.to_csv(R / "design_arm_split.csv", index=False)
print("\nPower at a true gain of 0.02, by arm sizes:")
print(split.pivot(index="n_drug_families", columns="n_control_families",
                  values="power_at_delta_0.02").round(2).to_string())

# What the published ReSisTrace experiment could resolve, and what it would have taken to halve that
audit = pd.read_csv(R / "label_audit.csv")
audit["arm"] = audit["sample"].str.split("_").str[0]
fam = audit.groupby("arm")["n_families"].sum()
# smallest gain whose two-sided 95% interval excludes zero with 80% probability
z_alpha, z_power = stats.norm.ppf(0.975), stats.norm.ppf(args.target_power)
obs = []
for arm in ["Carboplatin", "Olaparib", "NK"]:
    prev = float(audit[audit["arm"] == arm]["prevalence"].mean())
    se = se_delta(int(fam[arm]), int(fam["Control"]), prev)
    obs.append({"arm": arm, "n_drug_families": int(fam[arm]), "n_control_families": int(fam["Control"]),
                "prevalence": prev, "se_delta": se, "smallest_detectable_delta_80pct": (z_alpha + z_power) * se,
                "power_at_delta_0.02": power(0.02, int(fam[arm]), int(fam["Control"]), prev)})
obs = pd.DataFrame(obs)
obs.to_csv(R / "design_resistrace.csv", index=False)
print("\nWhat the published ReSisTrace design can resolve:")
print(obs.round(4).to_string(index=False))

need = required_families(0.01, args.target_power, prevalence=0.1)
print(f"\nTo resolve a gain of 0.01 at {args.target_power:.0%} power: "
      f"{need['n_drug_families']:,} families per arm ({need['total_families']:,} in total).")
