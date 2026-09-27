"""Convert GEO TSVs to per-sample sparse .h5ad (pre-treatment) and a post-treatment metadata table."""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.io import discover_samples, load_sample  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--force", action="store_true")
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("build")

out_dir = Path(cfg["paths"]["processed_dir"]) / "samples"
out_dir.mkdir(parents=True, exist_ok=True)
post_meta = []
for s in discover_samples(cfg["paths"]["raw_dir"]):
    if s.arm not in cfg["data"]["arms"]:
        continue
    with_expr = s.timepoint == "pre" or cfg["data"]["include_post_expression"]
    path = out_dir / f"{s.name}.h5ad"
    if with_expr and path.exists() and not args.force:
        log.info(f"{s.name}: exists, skipping")
        continue
    adata = load_sample(s, with_expression=with_expr)
    if s.timepoint == "post":
        post_meta.append(adata.obs)
    if with_expr:
        adata.write_h5ad(path, compression="gzip")
    log.info(f"{s.name}: {adata.n_obs} cells x {adata.n_vars} genes")
if post_meta:
    pd.concat(post_meta).to_csv(Path(cfg["paths"]["processed_dir"]) / "post_obs.csv.gz")
