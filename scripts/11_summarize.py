"""Collect results/*.csv into paper tables (results/summary.md) and figures (results/figures/*.png|pdf)."""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.utils import load_config  # noqa: E402

# reference categorical palette (fixed order), text inks and surface
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
INK, INK2, MUTED, SURFACE = "#0b0b0b", "#52514e", "#b5b4ad", "#fcfcfb"
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.spines.top": False, "axes.spines.right": False, "font.size": 9,
    "axes.grid": True, "grid.color": "#ecebe7", "grid.linewidth": 0.6, "axes.axisbelow": True,
})
MODEL_ORDER = ["cov_logreg", "hvg_logreg", "hvg_catboost", "pca_logreg", "pca_logreg_tuned", "pca_logreg_pooled",
               "pca_catboost", "pca_smooth_logreg",
               "mlp", "mlp_pretrain", "persist_gnn_nopretrain", "persist_gnn"]

ap = argparse.ArgumentParser()
ap.add_argument("--config")
ap.add_argument("--cc-mode", default="keep", choices=["keep", "regress", "regress_all"])
args = ap.parse_args()
cfg = load_config(args.config)
res = Path(cfg["paths"]["results_dir"])
fig_dir = res / "figures"
fig_dir.mkdir(exist_ok=True)
md = [f"# PERSIST results summary (cc_mode={args.cc_mode})\n"]


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(fig_dir / f"{name}.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)


# latest run per (model, split, train, test, seed, shuffle replicate)
R = pd.read_csv(res / "results.csv")
R = R[(R["cc_mode"] == args.cc_mode) & ((R["split"] != "within") | (R["fold"].astype(str) == "oof"))]
R["shuffled"] = R["shuffled"].astype(str).str.lower() == "true"
R = R.drop_duplicates(["model", "split", "train", "test", "seed", "shuffled", "notes"], keep="last")
real, shuf = R[~R["shuffled"]], R[R["shuffled"]]
keys = ["model", "split", "train", "test"]
T = real.groupby(keys).agg(auroc=("auroc", "mean"), auroc_sd=("auroc", "std"), lo=("auroc_lo", "mean"),
                           hi=("auroc_hi", "mean"), auprc=("auprc", "mean"), lift=("auprc_lift", "mean"),
                           wc_auroc=("within_cluster_auroc", "mean"), prevalence=("prevalence", "mean"),
                           n_seeds=("seed", "nunique"))
T = T.join(shuf.groupby(keys).agg(auroc_shuf=("auroc", "mean"), auroc_shuf_sd=("auroc", "std")))
T.round(3).to_csv(res / f"summary_table_{args.cc_mode}.csv")
for split in ["within", "rep_holdout", "cross_arm"]:
    t = T.xs(split, level="split") if split in T.index.get_level_values("split") else None
    if t is not None:
        md += [f"\n## {split}\n", t.round(3).to_markdown(), ""]

# Fig 1: within-arm AUROC per model with group-bootstrap CI; shuffled-label control as hollow grey marker
W = T.xs("within", level="split").reset_index() if "within" in T.index.get_level_values("split") else pd.DataFrame()
if len(W):
    arms = [a for a in cfg["data"]["arms"] if a in set(W["train"])]
    models = [m for m in MODEL_ORDER if m in set(W["model"])]
    fig, axes = plt.subplots(1, len(arms), figsize=(2.6 * len(arms), 0.35 * len(models) + 1.2), sharey=True)
    for ax, arm in zip(np.atleast_1d(axes), arms):
        d = W[W["train"] == arm].set_index("model").reindex(models)
        y = np.arange(len(models))
        ax.hlines(y, d["lo"], d["hi"], color=SERIES[0], lw=2)
        ax.plot(d["auroc"], y, "o", color=SERIES[0], ms=6, label="true labels")
        ax.plot(d["auroc_shuf"], y, "o", mfc="none", mec=INK2, ms=6, label="shuffled labels")
        ax.axvline(0.5, color=MUTED, lw=1, ls="--")
        ax.set_title(arm, color=INK, fontsize=10)
        ax.set_xlabel("AUROC")
        ax.set_yticks(y, models)
        ax.set_xlim(0.45, 0.85)
    np.atleast_1d(axes)[0].invert_yaxis()
    np.atleast_1d(axes)[-1].legend(loc="lower right", frameon=False, fontsize=8)
    save(fig, f"fig1_within_arm_{args.cc_mode}")

# Fig 2: cross-arm transfer matrix (train rows -> test columns), within-arm OOF on the diagonal
C = real[real["split"].isin(["cross_arm", "within"])]
for model in [m for m in ["pca_logreg", "persist_gnn"] if m in set(C.loc[C["split"] == "cross_arm", "model"])]:
    M = C[C["model"] == model].groupby(["train", "test"])["auroc"].mean().unstack()
    arms = [a for a in cfg["data"]["arms"] if a in M.index]
    M = M.reindex(index=arms, columns=arms)
    if M.isna().all().all():
        continue
    fig, ax = plt.subplots(figsize=(3.8, 3.3))
    im = ax.imshow(M.to_numpy(float), cmap="Blues", vmin=0.5, vmax=0.8)
    for i in range(len(arms)):
        for j in range(len(arms)):
            v = M.iat[i, j]
            if pd.notna(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", color="white" if v > 0.68 else INK, fontsize=8)
    ax.set_xticks(range(len(arms)), arms, rotation=30, ha="right")
    ax.set_yticks(range(len(arms)), arms)
    ax.set_xlabel("test arm")
    ax.set_ylabel("train arm")
    ax.grid(False)
    ax.set_title(f"{model}: cross-arm AUROC", fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.8, label="AUROC")
    save(fig, f"fig2_cross_arm_{model}_{args.cc_mode}")
    md += [f"\n## cross-arm matrix ({model})\n", M.round(3).to_markdown(), ""]

# Fig 3: fitness confound
fpath = res / "fitness_confound.csv"
if fpath.exists():
    F = pd.read_csv(fpath)
    F = F[(F["cc_mode"] == args.cc_mode) & (F["features"] == "pca")].drop_duplicates("drug_arm", keep="last")
    cols = [("auroc_drug_model_on_drug", "drug-arm model"), ("auroc_fitness_model_on_drug", "Control (fitness) model"),
            ("auroc_drug_residual_on_drug", "drug score | fitness")]
    fig, ax = plt.subplots(figsize=(4.8, 3))
    x = np.arange(len(F))
    w = 0.26
    for k, (col, lab) in enumerate(cols):
        ax.bar(x + (k - 1) * (w + 0.02), F[col] - 0.5, w, bottom=0.5, color=SERIES[k], label=lab)
    ax.set_xticks(x, F["drug_arm"])
    ax.set_ylabel("AUROC on drug-arm labels")
    ax.set_ylim(0.5, 0.8)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    save(fig, f"fig3_fitness_confound_{args.cc_mode}")
    md += ["\n## fitness confound\n", F.drop(columns=["config_hash"]).round(4).to_markdown(index=False), ""]

# Fig 4: ceiling decomposition (pi = 0.1)
dpath = res / f"ceiling_decomposition_{args.cc_mode}.csv"
if dpath.exists():
    D = pd.read_csv(dpath)
    D = D[(D["pi"] == 0.1) & (~D["saturated"])]
    models = [m for m in MODEL_ORDER if m in set(D["model"])]
    arms = [a for a in cfg["data"]["arms"] if a in set(D["arm"])]
    fig, axes = plt.subplots(1, len(arms), figsize=(2.6 * len(arms), 0.35 * len(models) + 1.2), sharey=True)
    for ax, arm in zip(np.atleast_1d(axes), arms):
        d = D[D["arm"] == arm].set_index("model").reindex(models)
        y = np.arange(len(models))
        ax.hlines(y, d["auroc_oof"], d["auroc_if_sister_seen"], color=MUTED, lw=2)
        ax.plot(d["auroc_oof"], y, "o", color=SERIES[0], ms=6, label="observed (sister's fate)")
        ax.plot(d["auroc_if_sister_seen"], y, "D", color=SERIES[1], ms=5, label="if treated sister were seen")
        ax.set_title(arm, fontsize=10)
        ax.set_xlabel("AUROC")
        ax.set_yticks(y, models)
        ax.set_xlim(0.5, 1.0)
    np.atleast_1d(axes)[0].invert_yaxis()
    np.atleast_1d(axes)[-1].legend(loc="lower right", frameon=False, fontsize=7)
    save(fig, f"fig4_ceiling_{args.cc_mode}")
    md += ["\n## ceiling decomposition (pi=0.1)\n", D.round(3).to_markdown(index=False), ""]
for name in [f"ceiling_{args.cc_mode}.csv", "external_validation.csv", "tcga_ov_cox.csv"]:
    if (res / name).exists():
        md += [f"\n## {name}\n", pd.read_csv(res / name).round(3).to_markdown(index=False), ""]

(res / f"summary_{args.cc_mode}.md").write_text("\n".join(md))
print(f"wrote {res / f'summary_{args.cc_mode}.md'} and {len(list(fig_dir.glob('*.png')))} figures")
