"""Contribution 3: predictability ceiling from pre-treatment sister discordance.

Uses pre-treatment sister pairs (same lineage, both sequenced before treatment) to estimate how much
transcriptional state is shared between sisters, converts that into an AUROC upper bound per arm,
and, if within-arm OOF predictions exist, compares each model with its ceiling.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist import ceiling as C  # noqa: E402
from persist.labels import sister_pairs  # noqa: E402
from persist.runner import load_context  # noqa: E402
from persist.utils import get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--cc-mode", choices=["keep", "regress", "regress_all"])
args = ap.parse_args()
cfg = load_config(args.config)
cc = cfg["ceiling"]
log = get_logger("ceiling")
ctx = load_context(cfg, args.cc_mode)
mode = ctx.adata.uns["cc_mode"]
res_dir = Path(cfg["paths"]["results_dir"])
rng = np.random.default_rng(cfg["seed"])

pairs = sister_pairs(ctx.obs)
fam = ctx.obs["sample"].astype(str).to_numpy()[pairs[:, 0]] + ":" + \
    ctx.obs["sisters"].to_numpy()[pairs[:, 0]].astype(int).astype(str)
null = C.random_pairs(ctx.samples, pairs, rng)
log.info(f"{len(pairs)} pre-treatment sister pairs from {len(np.unique(fam))} families")

# 1) how heritable is transcriptional state? per-PC ICC, sisters vs random pairs
Z = ctx.features("pca")
icc = pd.DataFrame({"pc": np.arange(1, Z.shape[1] + 1),
                    "icc_sisters": C.per_dim_icc(Z, pairs), "icc_random": C.per_dim_icc(Z, null)})
icc.to_csv(res_dir / f"ceiling_pc_icc_{mode}.csv", index=False)
log.info(f"mean ICC over top-10 PCs: sisters={icc.icc_sisters[:10].mean():.3f} random={icc.icc_random[:10].mean():.3f}")

# 2) ICC of the most heritable direction (held-out families) -> rho
rows = []
for d in cc["pca_dims"]:
    r = C.icc_max_cv(Z[:, :d], pairs, fam, cc["ridge"], seed=cfg["seed"])
    rn = C.icc_max_cv(Z[:, :d], null, np.arange(len(null)), cc["ridge"], seed=cfg["seed"])
    rows.append({"pca_dims": d, "icc_max_cv": r["icc_max_cv"], "icc_max_cv_sd": r["icc_max_cv_sd"],
                 "icc_max_insample": r["icc_max_insample"], "null_icc_max_cv": rn["icc_max_cv"]})
herit = pd.DataFrame(rows)
print(herit.round(3).to_string(index=False))
rho = float(herit["icc_max_cv"].max())

# 3) ceiling per arm (prevalence differs) under label noise pi
ceil = []
for arm in cfg["data"]["arms"]:
    m = ctx.obs["labeled"].to_numpy() & (ctx.obs["arm"] == arm).to_numpy()
    prev = ctx.y[m].mean()
    t = C.ceiling_table(rho, prev, cc["label_noise_pi"], cc["n_sim"])
    t.insert(0, "arm", arm)
    t.insert(1, "prevalence", prev)
    t.insert(2, "rho", rho)
    ceil.append(t)
ceil = pd.concat(ceil)
ceil["cc_mode"] = mode
ceil.to_csv(res_dir / f"ceiling_{mode}.csv", index=False)
print(ceil.round(3).to_string(index=False))
C.ceiling_curve(float(ceil["prevalence"].mean())).to_csv(res_dir / "ceiling_curve.csv", index=False)

# 4) models vs ceiling + cross-sister diagnostic (needs within-arm OOF predictions)
cells = ctx.obs.index.to_numpy()
pair_cells = cells[pairs]
diag = []
for f in sorted((res_dir / "preds").glob(f"*_{mode}_within*.csv.gz")):
    P = pd.read_csv(f)
    P = P[~P["shuffled"]]
    for (model, arm, seed), d in P.groupby(["model", "train", "seed"]):
        s = d.set_index("cell")["score"]
        r = C.cross_sister_diagnostic(s, d.set_index("cell")["y"], pair_cells, int(seed))
        diag.append({"model": model, "arm": arm, "seed": seed, **r})
if diag:
    D = pd.DataFrame(diag).groupby(["model", "arm"]).mean(numeric_only=True).drop(columns="seed")
    # per model: how much AUROC is lost to sister discordance vs to intrinsic fate stochasticity
    oof = pd.read_csv(res_dir / "results.csv")
    oof = oof[(oof["split"] == "within") & (oof["fold"] == "oof") & (~oof["shuffled"].astype(bool))
              & (oof["cc_mode"] == mode)]
    oof = oof.groupby(["model", "train"])[["auroc", "prevalence"]].last()
    dec = []
    for (model, arm), r in D.iterrows():
        if (model, arm) not in oof.index or np.isnan(r.get("score_icc", np.nan)):
            continue
        a, prev = oof.loc[(model, arm)]
        for pi in cc["label_noise_pi"]:
            dec.append({"model": model, "arm": arm, "pi": pi, "auroc_oof": a,
                        **C.score_decomposition(a, r["score_icc"], prev, pi)})
    D.to_csv(res_dir / f"ceiling_cross_sister_{mode}.csv")
    print(D.round(3).to_string())
    if dec:
        dec = pd.DataFrame(dec)
        dec.to_csv(res_dir / f"ceiling_decomposition_{mode}.csv", index=False)
        print(dec.round(3).to_string(index=False))
else:
    log.warning("no within-arm predictions found; run 04/05 with --splits within for the model comparison")
