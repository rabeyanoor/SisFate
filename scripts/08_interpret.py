"""Genes/pathways behind the pre-resistant state; drug-specific vs fitness-shared signatures."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist import interpret as I  # noqa: E402
from persist.runner import load_context  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--cc-mode", choices=["keep", "regress", "regress_all"])
args = ap.parse_args()
cfg = load_config(args.config)
ic = cfg["interpret"]
log = get_logger("interpret")
ctx = load_context(cfg, args.cc_mode)
out = Path(cfg["paths"]["results_dir"]) / "interpret"
out.mkdir(exist_ok=True)

de = {}
for arm in cfg["data"]["arms"]:
    de[arm] = I.de_arm(ctx.adata, arm)
    de[arm].to_csv(out / f"de_{arm}.csv")
    n_sig = ((de[arm]["padj"] < ic["fdr"]) & de[arm]["consistent"]).sum()
    log.info(f"{arm}: {n_sig} replicate-consistent DE genes; top up: {de[arm]['symbol'].head(8).tolist()}")

signatures = {"fitness_Control": I.signature(de["Control"], ic["top_n_signature"], "z", "padj", ic["fdr"])}
for arm in [a for a in cfg["data"]["arms"] if a != "Control"]:
    t = I.drug_specific(de[arm], de["Control"], ic["fdr"])
    t.to_csv(out / f"drug_vs_fitness_{arm}.csv")
    log.info(f"{arm}: {t['class'].value_counts().to_dict()}")
    signatures[f"all_{arm}"] = I.signature(de[arm], ic["top_n_signature"], "z", "padj", ic["fdr"])
    signatures[f"specific_{arm}"] = I.signature(t, ic["top_n_signature"], "z_diff", "padj_diff", ic["fdr"], "drug_specific")
    I.model_gene_weights(ctx, arm, cfg["seed"]).to_csv(out / f"logreg_weights_{arm}.csv")

# pathways: fitness axis (Control) and drug-beyond-fitness contrast for each drug arm
gsea = {"fitness_Control": I.hallmark_gsea(de["Control"], "z", cfg["paths"]["ref_dir"], cfg["seed"])}
for arm in [a for a in cfg["data"]["arms"] if a != "Control"]:
    gsea[f"all_{arm}"] = I.hallmark_gsea(de[arm], "z", cfg["paths"]["ref_dir"], cfg["seed"])
    t = I.drug_specific(de[arm], de["Control"], ic["fdr"])
    gsea[f"specific_{arm}"] = I.hallmark_gsea(t, "z_diff", cfg["paths"]["ref_dir"], cfg["seed"])
for name, g in gsea.items():
    g.to_csv(out / f"gsea_hallmark_{name}.csv", index=False)
    sig = g[g["FDR q-val"].astype(float) < 0.05]
    log.info(f"GSEA {name}: {len(sig)} Hallmark sets at FDR<0.05; "
             f"up {sig[sig['NES'].astype(float) > 0]['Term'].head(4).tolist()} "
             f"down {sig[sig['NES'].astype(float) < 0]['Term'].tail(4).tolist()}")

with open(out / "signatures.json", "w") as fh:
    json.dump(signatures, fh, indent=1)
for k, v in signatures.items():
    print(f"{k:22s} up={len(v['up']):3d} down={len(v['down']):3d}  {v['up'][:10]}")
