"""Label-free 'typicality' check: how well does local density in PCA space alone separate the classes?

Found while investigating why gradient boosting trained on shuffled labels scored above 0.5.
Density = negative mean distance to the 15 nearest neighbours within the same sample (no labels used).
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
from persist.runner import load_context  # noqa: E402
from persist.utils import load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
args = ap.parse_args()
cfg = load_config(args.config)
R = Path(cfg["paths"]["results_dir"])
rows = []
for cc in ["keep", "regress_all"]:
    ctx = load_context(cfg, cc)
    X = ctx.features("pca")
    dens = np.zeros(len(X))
    for s in np.unique(ctx.samples):
        m = np.flatnonzero(ctx.samples == s)
        d, _ = NearestNeighbors(n_neighbors=16).fit(X[m]).kneighbors(X[m])
        dens[m] = -d[:, 1:].mean(1)
    oof = pd.concat(pd.read_csv(f) for f in (R / "preds").glob(f"baselines_{cc}_within*.csv.gz"))
    oof = oof[(oof["model"] == "pca_logreg") & (oof["shuffle_rep"] == 0)].drop_duplicates("cell").set_index("cell")["score"] \
        if cc == "keep" else None
    for arm in cfg["data"]["arms"]:
        m = np.flatnonzero(ctx.obs["labeled"].to_numpy() & (ctx.obs["arm"] == arm).to_numpy())
        within = np.mean([roc_auc_score(ctx.y[m][ctx.samples[m] == s], dens[m][ctx.samples[m] == s])
                          for s in np.unique(ctx.samples[m])])
        r = {"cc_mode": cc, "arm": arm, "auroc_density_pooled": roc_auc_score(ctx.y[m], dens[m]),
             "auroc_density_within_sample": within}
        if oof is not None:
            sc = oof.reindex(ctx.obs.index[m]).to_numpy()
            r["spearman_density_vs_pca_logreg"] = stats.spearmanr(dens[m], sc).statistic
        rows.append(r)
df = pd.DataFrame(rows)
df.to_csv(R / "typicality.csv", index=False)
print(df.round(3).to_string(index=False))
