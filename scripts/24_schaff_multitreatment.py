"""Second lineage-tracing system: six treatments in parallel (Schaff et al. 2026, GEO GSE279162).

WM989 melanoma cells carrying transcribed barcodes were profiled untreated, then split across dabrafenib,
trametinib, CoCl2, acidic medium, cisplatin and doxorubicin; survivors were sequenced after four weeks with
paired barcodes. Every untreated cell therefore carries six labels, so the same cells can be asked six
questions at once. There is no drug-free arm carried through the four weeks, so there is no fitness model as
in ReSisTrace; pre-treatment clone size takes its place as a measure of how well a lineage grows in culture.

Analyses, mirroring the ReSisTrace ones:
  predict     lineage-grouped CV of expression, clone size, both, and the label-free density score
  adjust      does expression add over clone size? (residual AUROC, likelihood-ratio test)
  transfer    train on one treatment, test on another (all 30 pairs)
  ceiling     cells sharing a lineage in the untreated sample give the clone concordance of each score,
              and the AUROC that would be reached if the treated cell itself were profiled

Run scripts/00c_download_schaff.sh first.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.neighbors import NearestNeighbors

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.ceiling import normal_scores, pair_icc, score_decomposition  # noqa: E402
from persist.external import lognorm, zscore  # noqa: E402
from persist.metrics import evaluate  # noqa: E402
from persist.models.baselines import logistic  # noqa: E402
from persist.schaff import TREATMENTS, build  # noqa: E402
from persist.utils import ROOT, get_logger, load_config  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--merge-r", type=float, default=0.55, help="merge barcodes correlating at least this much")
ap.add_argument("--min-umi", type=int, default=2)
ap.add_argument("--min-frac", type=float, default=0.5)
ap.add_argument("--n-hvg", type=int, default=2000)
ap.add_argument("--tag", default="", help="suffix for the output files (used by the threshold sensitivity runs)")
args = ap.parse_args()
cfg = load_config(args.config)
log = get_logger("schaff")
R = Path(cfg["paths"]["results_dir"])
C = cfg["baselines"]["logistic_C"]
SEED = cfg["seed"]

raw = ROOT / "data" / "external" / "schaff" / "raw"
X, genes, obs = build(raw, args.merge_r, args.min_umi, args.min_frac, log)
log.info(f"untreated cells with a lineage: {len(obs)}, lineages: {obs['lineage'].nunique()}, "
         f"median clone size {obs['clone_size'].median():.0f}")
for t in TREATMENTS:
    log.info(f"  {t}: {obs[f'y_{t}'].mean():.3f} of untreated cells are in a surviving lineage")

# ---- features: log-normalise, pick HVGs by dispersion, z-score, 50 PCs (no labels used)
Xl = lognorm(sp.csr_matrix(X))
mu = np.asarray(Xl.mean(0)).ravel()
sq = np.asarray(Xl.multiply(Xl).mean(0)).ravel()
var = np.maximum(sq - mu ** 2, 0)
ok = mu > 0
disp = np.full(len(mu), -np.inf)
disp[ok] = var[ok] / mu[ok]
hvg = np.argsort(-disp)[: args.n_hvg]
Z = zscore(Xl[:, hvg].toarray())
pcs = PCA(50, random_state=SEED).fit_transform(Z).astype(np.float32)
groups = obs["lineage"].to_numpy()
clone = np.log(obs["clone_size"].to_numpy(float))[:, None]

nn = NearestNeighbors(n_neighbors=16).fit(pcs)
dist, _ = nn.kneighbors(pcs)
density = -dist[:, 1:].mean(1)


def oof(F, y, seed=SEED):
    s = np.zeros(len(y))
    for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=seed).split(F, y, groups):
        s[te], _ = logistic(F[tr], y[tr], F[te], C, seed)
    return s


def logit(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def loglik(F, y):
    m = LogisticRegression(C=1e6, max_iter=5000).fit(F, y)
    p = np.clip(m.predict_proba(F)[:, 1], 1e-12, 1 - 1e-12)
    return float(np.sum(y * np.log(p) + (1 - y) * np.log(1 - p)))


rows, adj, scores = [], [], {}
for t in TREATMENTS:
    y = obs[f"y_{t}"].to_numpy()
    if y.sum() < 20 or (1 - y).sum() < 20:
        log.info(f"{t}: skipped, {y.sum()} positives")
        continue
    s_expr = oof(pcs, y)
    scores[t] = s_expr
    feats = {"expression": s_expr, "clone_size": oof(clone, y),
             "expression+clone_size": oof(np.hstack([pcs, clone]), y), "density_label_free": density}
    for name, s in feats.items():
        rows.append({"treatment": t, "model": name,
                     **evaluate(y, s, groups, n_boot=300, seed=SEED)})
    # does expression add over clone size, the growth-fitness proxy?
    lc, le = logit(feats["clone_size"]), logit(s_expr)
    resid = le - np.polyval(np.polyfit(lc, le, 1), lc)
    lr = 2 * (loglik(np.column_stack([lc, le]), y) - loglik(lc[:, None], y))
    adj.append({"treatment": t, "auroc_expression": roc_auc_score(y, s_expr),
                "auroc_clone_size": roc_auc_score(y, feats["clone_size"]),
                "auroc_expression_residual_on_clone_size": roc_auc_score(y, resid),
                "spearman_expr_vs_clone": stats.spearmanr(le, lc).statistic,
                "lrt_stat": lr, "lrt_p": stats.chi2.sf(lr, 1)})
    log.info(f"{t}: expression {rows[-4]['auroc']:.3f}, clone size {rows[-3]['auroc']:.3f}, "
             f"both {rows[-2]['auroc']:.3f}, density {rows[-1]['auroc']:.3f}, "
             f"residual {adj[-1]['auroc_expression_residual_on_clone_size']:.3f}")

# ---- cross-treatment transfer: does a model for one treatment predict another?
# The six labels describe the same cells, so a model fitted on all of them and scored on the same cells would
# be in-sample. We reuse each treatment's out-of-fold score instead: every cell was scored by a model that had
# never seen its lineage, and we simply ask how well that score ranks a different treatment's labels.
tr_rows = []
for a in scores:
    for b in scores:
        tr_rows.append({"train": a, "test": b, "auroc": roc_auc_score(obs[f"y_{b}"].to_numpy(), scores[a])})

# ---- ceiling from cells that share a lineage in the untreated sample
rng = np.random.default_rng(SEED)
pairs = []
for _, idx in obs.reset_index().groupby("lineage").groups.items():
    idx = np.asarray(list(idx))
    if len(idx) >= 2:
        perm = rng.permutation(idx)
        pairs += [(perm[i], perm[i + 1]) for i in range(0, len(perm) - 1, 2)]
pairs = np.asarray(pairs)
log.info(f"{len(pairs)} untreated same-lineage pairs from {obs['clone_size'].gt(1).sum()} cells in multi-cell clones")

ceil_rows = []
if len(pairs) >= 50:
    icc_pc = [pair_icc(pcs[pairs[:, 0], j], pcs[pairs[:, 1], j]) for j in range(10)]
    rand = np.asarray([(a, rng.choice(len(obs))) for a, _ in pairs])
    icc_rand = [pair_icc(pcs[rand[:, 0], j], pcs[rand[:, 1], j]) for j in range(10)]
    for t, s in scores.items():
        y = obs[f"y_{t}"].to_numpy()
        conc = pair_icc(normal_scores(pd.Series(s)).to_numpy()[pairs[:, 0]],
                        normal_scores(pd.Series(s)).to_numpy()[pairs[:, 1]])
        dec = score_decomposition(roc_auc_score(y, s), conc, y.mean(), 0.1, 200_000)
        ceil_rows.append({"treatment": t, "n_pairs": len(pairs), "score_clone_concordance": conc,
                          "mean_icc_pc1_10": float(np.mean(icc_pc)), "mean_icc_random": float(np.mean(icc_rand)),
                          "auroc_observed": roc_auc_score(y, s), **dec})
        log.info(f"{t}: clone concordance {conc:.3f}, AUROC if treated cell seen "
                 f"{dec['auroc_if_sister_seen']:.3f}, cost {dec['sister_cost']:.3f}")

tag = args.tag
pd.DataFrame(rows).assign(merge_r=args.merge_r, min_umi=args.min_umi, min_frac=args.min_frac) \
    .to_csv(R / f"schaff_predict{tag}.csv", index=False)
pd.DataFrame(adj).assign(merge_r=args.merge_r, min_umi=args.min_umi, min_frac=args.min_frac) \
    .to_csv(R / f"schaff_clone_size_adjusted{tag}.csv", index=False)
pd.DataFrame(tr_rows).to_csv(R / f"schaff_transfer{tag}.csv", index=False)
pd.DataFrame(ceil_rows).to_csv(R / f"schaff_ceiling{tag}.csv", index=False)
print(pd.DataFrame(rows)[["treatment", "model", "n_test", "prevalence", "auroc", "auroc_lo", "auroc_hi"]]
      .round(3).to_string(index=False))
print(pd.DataFrame(adj).round(4).to_string(index=False))
