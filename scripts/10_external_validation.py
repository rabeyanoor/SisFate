"""External validation on two independent lineage-tracing data sets (clone-level labels).

  watermelon  Oren et al. 2021, PC9 lung + osimertinib (GSE150949); label: lineage seen at day 14
              (any sample, or a 14_high sample for the proliferating-persister variant)
  tnbc        Pellecchia et al. 2024, MDA-MB-468 TNBC + afatinib (GSE228382; counts/metadata from figshare
              24787458 via scripts/export_seurat.R); label: lineage among day-40 tolerant expanded persisters
For each: lineage-grouped CV of clone-size / covariate / expression models, and zero-shot transfer of
ReSisTrace-trained models. Run scripts/00b_download_external.sh (and export_seurat.R) first.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.external import load_tnbc_day0, load_watermelon_day0, lognorm, run_external  # noqa: E402
from persist.runner import load_context  # noqa: E402
from persist.utils import ROOT, get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--cc-mode", choices=["keep", "regress", "regress_all"])
ap.add_argument("--datasets", nargs="+", default=["watermelon", "tnbc"])
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("external")
ctx = load_context(cfg, args.cc_mode)
ext = ROOT / "data" / "external"

frames = []
if "watermelon" in args.datasets:
    X, genes, obs = load_watermelon_day0(ext / "watermelon")
    log.info(f"watermelon day 0: {len(obs)} cells, {obs['lineage_barcode'].nunique()} lineages, "
             f"prevalence {obs['y_persister'].mean():.3f}")
    frames.append(run_external("watermelon", lognorm(X), genes, obs, ["y_persister", "y_cycling"], ctx, cfg, log))
if "tnbc" in args.datasets:
    X, genes, obs = load_tnbc_day0(ext / "scastral" / "export")
    log.info(f"tnbc day 0: {len(obs)} cells, {obs['lineage_barcode'].nunique()} lineages, "
             f"prevalence {obs['y_persister'].mean():.3f}")
    frames.append(run_external("tnbc_afatinib", lognorm(X), genes, obs, ["y_persister"], ctx, cfg, log))

df = pd.concat(frames, ignore_index=True)
df["config_hash"] = cfg["_hash"]
df.to_csv(Path(cfg["paths"]["results_dir"]) / "external_validation.csv", index=False)
print(df[["dataset", "analysis", "label", "subset", "model", "n_test", "prevalence", "auroc", "auroc_lo", "auroc_hi"]]
      .round(3).to_string(index=False))
