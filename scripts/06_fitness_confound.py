"""Contribution 2: separate drug-specific tolerance from generic growth/capture fitness (Control arm)."""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.fitness import fitness_analysis  # noqa: E402
from persist.runner import load_context  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--cc-mode", choices=["keep", "regress", "regress_all"])
ap.add_argument("--features", default="pca", choices=["pca", "hvg", "pca+cov", "cov"])
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("fitness")
ctx = load_context(cfg, args.cc_mode)

rows = []
for arm in [a for a in cfg["data"]["arms"] if a != "Control"]:
    r = fitness_analysis(ctx, arm, "Control", args.features, cfg["seed"])
    r.update(features=args.features, cc_mode=ctx.adata.uns["cc_mode"], config_hash=cfg["_hash"])
    rows.append(r)
    log.info(f"{arm}: drug={r['auroc_drug_model_on_drug']:.3f} fitness={r['auroc_fitness_model_on_drug']:.3f} "
             f"residual={r['auroc_drug_residual_on_drug']:.3f} LRT p={r['lrt_p']:.2g}")
df = pd.DataFrame(rows)
out = Path(cfg["paths"]["results_dir"]) / "fitness_confound.csv"
df.to_csv(out, mode="a", header=not out.exists(), index=False)
print(df.drop(columns=["config_hash"]).T.to_string())
