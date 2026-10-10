"""OPTIONAL, run only after baselines show signal: is the signature associated with outcome in TCGA-OV?

Downloads UCSC Xena TCGA-OV RNA-seq (log2 RSEM, gene symbols) and curated survival (Liu et al. 2018),
scores each tumour by mean z-score of signature genes (up minus down) and fits Cox models for OS and PFI.
Bulk tumours differ from a cell line, so treat any association as hypothesis-generating.
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.utils import get_logger, load_config  # noqa: E402

XENA = "https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download/"
FILES = {"expr": "TCGA.OV.sampleMap%2FHiSeqV2.gz", "surv": "survival%2FOV_survival.txt"}

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--signature", default="specific_Carboplatin", help="key in results/interpret/signatures.json")
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("tcga")
ref = Path(cfg["paths"]["ref_dir"]) / "tcga_ov"
ref.mkdir(exist_ok=True)
for key, name in FILES.items():
    p = ref / name.replace("%2F", "_")
    if not p.exists():
        log.info(f"downloading {name}")
        urllib.request.urlretrieve(XENA + name, p)
expr = pd.read_csv(ref / FILES["expr"].replace("%2F", "_"), sep="\t", index_col=0)
surv = pd.read_csv(ref / FILES["surv"].replace("%2F", "_"), sep="\t", index_col=0)

sigs = json.load(open(Path(cfg["paths"]["results_dir"]) / "interpret" / "signatures.json"))
sig = sigs[args.signature]
z = expr.sub(expr.mean(1), axis=0).div(expr.std(1).replace(0, 1), axis=0)
up = [g for g in sig["up"] if g in z.index]
down = [g for g in sig["down"] if g in z.index]
log.info(f"{args.signature}: {len(up)}/{len(sig['up'])} up and {len(down)}/{len(sig['down'])} down genes found")
score = z.loc[up].mean() - (z.loc[down].mean() if down else 0)
tumour = [s for s in score.index if s[13:15] == "01"]  # primary tumours only
df = surv.join(score.rename("score"), how="inner").loc[lambda d: d.index.isin(tumour)]

from lifelines import CoxPHFitter  # noqa: E402

rows = []
for ep in ["OS", "PFI"]:
    d = df[[f"{ep}.time", ep, "score"]].dropna()
    d = d.assign(score=(d["score"] - d["score"].mean()) / d["score"].std())
    cph = CoxPHFitter().fit(d, f"{ep}.time", ep)
    s = cph.summary.loc["score"]
    rows.append({"signature": args.signature, "endpoint": ep, "n": len(d), "events": int(d[ep].sum()),
                 "HR_per_sd": s["exp(coef)"], "lo": s["exp(coef) lower 95%"], "hi": s["exp(coef) upper 95%"], "p": s["p"]})
res = pd.DataFrame(rows)
res.to_csv(Path(cfg["paths"]["results_dir"]) / "tcga_ov_cox.csv", mode="a", index=False,
           header=not (Path(cfg["paths"]["results_dir"]) / "tcga_ov_cox.csv").exists())
print(res.round(4).to_string(index=False))
