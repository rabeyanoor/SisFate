"""Publication figures (results/figures/paper/Fig1-6 + supplementary), built only from files in results/.

Every number drawn here is read from a results table; nothing is typed in by hand except the
benchmark reference values of Shen et al. 2026 (Fig. 2c), which are quoted from that paper's text.
"""
import argparse
import io
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402
from matplotlib.patches import Ellipse, FancyBboxPatch, Rectangle  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from persist.utils import load_config  # noqa: E402

BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = \
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#a8a79f", "#ecebe7", "#ffffff"
ARM_COLOR = {"Carboplatin": BLUE, "Olaparib": ORANGE, "NK": AQUA, "Control": INK2}
ARMS = ["Carboplatin", "Olaparib", "NK", "Control"]
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "axes.spines.top": False, "axes.spines.right": False, "font.size": 7.5,
    "axes.titlesize": 8.5, "axes.labelsize": 7.5, "legend.fontsize": 6.5, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True, "font.family": "sans-serif", "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
    "pdf.fonttype": 42,
})
MODEL_LABEL = {
    "cov_logreg": "Covariates only", "hvg_logreg": "Logistic, 2,000 genes", "hvg_catboost": "CatBoost, 2,000 genes",
    "pca_logreg": "Logistic, 50 PCs", "pca_logreg_tuned": "Logistic, tuned", "pca_logreg_pooled": "Logistic, pooled arms",
    "pca_catboost": "CatBoost, PCs + covariates", "pca_smooth_logreg": "Logistic, graph-smoothed PCs",
    "mlp": "MLP", "mlp_pretrain": "MLP + sister pretraining", "persist_gnn_nopretrain": "GNN",
    "persist_gnn": "GNN + sister pretraining",
}

ap = argparse.ArgumentParser()
ap.add_argument("--config")
args = ap.parse_args()
cfg = load_config(args.config)
R = Path(cfg["paths"]["results_dir"])
OUT = R / "figures" / "paper"
OUT.mkdir(parents=True, exist_ok=True)


PLOS = OUT / "plos"  # submission files: RGB TIFF, LZW, 450 dpi, width <= 7.5 in (19.05 cm), named as PLOS asks
PLOS.mkdir(exist_ok=True)
MAX_W_IN = 7.5


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=450, bbox_inches="tight")
    im = Image.open(buf).convert("RGB")
    w_in = im.width / 450
    if w_in > MAX_W_IN:  # shrink to the maximum width; text stays >= 6.5 pt at the sizes used here
        im = im.resize((int(MAX_W_IN * 450), int(im.height * MAX_W_IN / w_in)), Image.LANCZOS)
    num = name.split("_")[0]
    plos = f"S{num[4:]}_Fig.tif" if num.startswith("FigS") else f"{num}.tif"
    im.save(PLOS / plos, compression="tiff_lzw", dpi=(450, 450))
    plt.close(fig)
    print(f"wrote {name} ({w_in:.2f} in wide -> {plos} {im.width}x{im.height}px)")


def tag(ax, letter):
    ax.text(-0.02, 1.04, letter, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="right")


def results(cc="keep"):
    d = pd.read_csv(R / "results.csv")
    d = d[(d["cc_mode"] == cc) & ((d["split"] != "within") | (d["fold"].astype(str) == "oof"))].copy()
    d["shuffled"] = d["shuffled"].astype(str).str.lower() == "true"
    return d.drop_duplicates(["model", "split", "train", "test", "seed", "shuffled", "notes"], keep="last")


RES = results("keep")
REAL, SHUF = RES[~RES["shuffled"]], RES[RES["shuffled"]]

# =============================================================== Fig 1: design and data
fig = plt.figure(figsize=(7.2, 4.2))
ax = fig.add_axes([0.0, 0.42, 1.0, 0.58])
ax.set_xlim(0, 100)
ax.set_ylim(0, 50)
ax.axis("off")
tag(ax, "a")


def box(x, y, w, h, text, color=INK2, fill="#f6f6f4", size=6.8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", lw=0.8,
                                edgecolor=color, facecolor=fill))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=INK, wrap=True)


ASP = (7.2 / 100) / (4.2 * 0.58 / 50)  # data units: y per x, so that cells are drawn round


def cell(x, y, r=2.2, color=BLUE, alive=True, bc=True):
    """A cell: body, nucleus and a three-stripe lineage barcode (drawn round despite unequal axis scales)."""
    ax.add_patch(Ellipse((x, y), 2 * r, 2 * r * ASP, facecolor=color if alive else "#dddcd6", edgecolor=INK2, lw=0.6,
                         alpha=0.9 if alive else 1))
    ax.add_patch(Ellipse((x - 0.35 * r, y + 0.2 * r * ASP), 0.76 * r, 0.76 * r * ASP, facecolor="white",
                         edgecolor="none", alpha=0.85))
    if bc:
        for k, c in enumerate([YELLOW, MAGENTA, GREEN]):
            ax.add_patch(Rectangle((x + 0.15 * r + k * 0.28 * r, y - 0.55 * r * ASP), 0.2 * r, 0.6 * r * ASP,
                                   facecolor=c, lw=0))
    if not alive:
        d = 0.6 * r
        ax.plot([x - d, x + d], [y - d * ASP, y + d * ASP], color=RED, lw=1.2)
        ax.plot([x - d, x + d], [y + d * ASP, y - d * ASP], color=RED, lw=1.2)


def arrow(x0, y0, x1, y1, style="-|>", ls="-", color=INK2, rad=0.0):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle=style, lw=0.8, color=color, ls=ls, connectionstyle=f"arc3,rad={rad}"))


def note(x, y, text, size=6.2, color=INK2, ha="center", **kw):
    ax.text(x, y, text, fontsize=size, color=color, ha=ha, va="center", **kw)


# 1. barcoding and one division
cell(6, 29, 2.8, INK2)
note(6, 20.5, "barcoded\nKuramochi cell\n(synchronised)")
arrow(9.5, 29, 13.5, 29)
note(11.5, 31.5, "divides\nonce", size=5.6)
cell(16.5, 33, 2.1, BLUE)
cell(16.5, 25.4, 2.1, ORANGE)
note(16.5, 19.5, "sisters share\nthe barcode", size=5.6)
# 2. sister 1: sequenced before treatment
arrow(19, 32.5, 25, 41)
cell(28, 42.5, 2.3, BLUE)
for k, h in enumerate([2.2, 3.6, 1.4, 4.4, 2.8, 1.8, 3.2]):
    ax.add_patch(Rectangle((33 + k * 0.9, 40.3), 0.65, h, facecolor=BLUE, alpha=0.75, lw=0))
note(36, 47.5, "sister 1: scRNA-seq before treatment\n→ features x", color=BLUE)
# 3. sister 2: treated
arrow(19, 25.5, 25, 17)
ax.add_patch(Ellipse((31, 14.5), 16, 10.5, facecolor="#f6f6f4", edgecolor=INK2, lw=0.7))
cell(27.5, 14.8, 1.8, ORANGE)
cell(31.5, 13.0, 1.5, ORANGE, alive=False, bc=False)
cell(35.0, 15.8, 1.5, ORANGE, alive=False, bc=False)
note(31, 6.3, "sister 2: carboplatin | olaparib |\nNK cells | no drug (control)", color=ORANGE)
# 4. survivors sequenced, barcode matched -> label for sister 1
arrow(39, 14.5, 45, 14.5)
cell(48, 14.5, 2.0, ORANGE)
note(48, 8.5, "survivors sequenced,\nbarcodes read", size=5.8)
arrow(48, 17.5, 38, 39, ls="--", color=INK, rad=0.25)
ax.text(49, 29, "label y for sister 1:\npre-resistant (barcode\nfound) or pre-sensitive", fontsize=6.2, color=INK,
        ha="left", va="center", fontweight="bold")
ax.plot([62.5, 62.5], [2, 48], color=GRID, lw=1)
box(66, 38, 33, 9, "Q1  How predictable is the sister's fate?\n(grouped CV, replicate and cross-arm tests)", INK2)
box(66, 26.5, 33, 9, "Q2  How much is generic fitness?\n(control-arm model, residual, size-matched)", INK2)
box(66, 15, 33, 9, "Q3  What is the ceiling?\n(3,477 pre-treatment sister pairs)", INK2)
box(66, 3.5, 33, 9, "External: Watermelon (PC9), TNBC (MDA-MB-468),\nTCGA-OV; confounds: depth, cell cycle, CNV", INK2)
ax.text(1, 1.5, "4 arms × 2 replicates; 37,011 pre-treatment cells,\n32,642 with a lineage label", fontsize=6.2,
        color=INK2, va="center")

audit = pd.read_csv(R / "label_audit.csv")
audit["arm"] = audit["sample"].str.split("_").str[0]
audit["rep"] = audit["sample"].str.split("_").str[1]
axb = fig.add_axes([0.07, 0.06, 0.38, 0.28])
tag(axb, "b")
audit = audit.assign(o=audit["arm"].map({a: i for i, a in enumerate(ARMS)})).sort_values(["o", "rep"])
x = np.arange(len(audit))
axb.bar(x, audit["prevalence"] * 100, color=[ARM_COLOR[a] for a in audit["arm"]], width=0.7)
axb.set_xticks(x, [f"{a[:4]}\nrep {r}" for a, r in zip(audit["arm"], audit["rep"])], fontsize=6)
axb.set_ylabel("Pre-resistant cells (%)")

import anndata as ad  # noqa: E402

obs = ad.read_h5ad(Path(cfg["paths"]["processed_dir"]) / "pre_keep.h5ad", backed="r").obs
obs = obs[obs["labeled"]]
axc = fig.add_axes([0.57, 0.06, 0.4, 0.28])
tag(axc, "c")
for i, arm in enumerate(ARMS):
    d = obs[obs["arm"] == arm]
    for j, (yv, col) in enumerate([(0, MUTED), (1, ARM_COLOR[arm])]):
        v = np.log10(d.loc[d["y"] == yv, "nCount_RNA"].astype(float))
        parts = axc.violinplot(v, positions=[i * 2.4 + j], widths=0.9, showextrema=False, showmedians=True)
        for b in parts["bodies"]:
            b.set_facecolor(col)
            b.set_alpha(0.75)
        parts["cmedians"].set_color(INK)
axc.set_xticks([i * 2.4 + 0.5 for i in range(4)], ARMS)
axc.set_ylabel("log10 UMIs per cell")
save(fig, "Fig1_design_data")

# =============================================================== Fig 2: predictability
fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.4), gridspec_kw={"width_ratios": [1.6, 0.9, 0.9]})
ax = axes[0]
tag(ax, "a")
W = REAL[REAL["split"] == "within"].groupby(["model", "train"])[["auroc", "auroc_lo", "auroc_hi"]].mean()
Ws = SHUF[SHUF["split"] == "within"].groupby(["model", "train"])["auroc"].mean()
models = [m for m in ["cov_logreg", "hvg_logreg", "hvg_catboost", "pca_catboost", "pca_logreg", "pca_logreg_tuned",
                      "pca_logreg_pooled", "pca_smooth_logreg", "mlp", "persist_gnn"] if m in W.index.get_level_values(0)]
yy = np.arange(len(models))
for k, arm in enumerate(ARMS):
    off = (k - 1.5) * 0.17
    d = W.xs(arm, level="train").reindex(models)
    ax.errorbar(d["auroc"], yy + off, xerr=[d["auroc"] - d["auroc_lo"], d["auroc_hi"] - d["auroc"]], fmt="o",
                ms=3, lw=0.8, color=ARM_COLOR[arm], label=arm)
    s = Ws.xs(arm, level="train").reindex(models) if arm in Ws.index.get_level_values(1) else None
    if s is not None:
        ax.plot(s, yy + off, "|", color=MUTED, ms=5)
ax.axvline(0.5, color=MUTED, ls="--", lw=0.8)
ax.set_yticks(yy, [MODEL_LABEL[m] for m in models])
ax.invert_yaxis()
ax.set_xlabel("AUROC (out-of-fold, lineage-grouped)")
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.45, -0.17), ncol=4, handletextpad=0.2, columnspacing=0.8)

ax = axes[1]
tag(ax, "b")
Rh = REAL[(REAL["split"] == "rep_holdout") & (REAL["model"] == "pca_logreg")].groupby(["train", "test"])["auroc"].mean().reset_index()
Wi = W.xs("pca_logreg", level="model")["auroc"]
for k, arm in enumerate(ARMS):
    r = Rh[Rh["train"].str.startswith(arm)]
    ax.plot([k] * len(r), r["auroc"], "o", color=ARM_COLOR[arm], ms=4)
    ax.plot([k - 0.25, k + 0.25], [Wi[arm]] * 2, color=INK, lw=1)
ax.set_xticks(range(4), ["Carbo", "Olap", "NK", "Ctrl"])
ax.set_ylim(0.5, 0.8)
ax.set_ylabel("AUROC")

ax = axes[2]
tag(ax, "c")
rob = pd.read_csv(R / "robustness_keep.csv")
bp = rob[rob["check"].str.startswith("benchmark")]
vals = {"Plain\nCV": bp[bp["check"] == "benchmark_protocol_ungrouped"]["auroc"],
        "Lineage-\ngrouped CV": bp[bp["check"] == "benchmark_protocol_grouped"]["auroc"]}
for i, (lab_, v) in enumerate(vals.items()):
    ax.plot([i] * len(v), v, "o", color=ORANGE, ms=4)
ax.axhspan(0.50, 0.55, color=MUTED, alpha=0.35, lw=0)
ax.axhline(0.60, color=INK2, lw=0.8, ls=":")
ax.text(1.45, 0.525, "most benchmarked\nmethods (0.50–0.55)", fontsize=5.8, color=INK2, va="center", ha="right")
ax.text(1.45, 0.61, "scDEAL (~0.6)", fontsize=5.8, color=INK2, ha="right")
ax.set_xticks(range(2), list(vals))
ax.set_xlim(-0.5, 1.5)
ax.set_ylim(0.45, 0.8)
ax.set_ylabel("AUROC, olaparib, balanced")
fig.tight_layout()
save(fig, "Fig2_predictability")

# =============================================================== Fig 3: fitness confound
fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.0), gridspec_kw={"width_ratios": [1.1, 1.3, 1]})
ax = axes[0]
tag(ax, "a")
C = REAL[(REAL["model"] == "pca_logreg") & REAL["split"].isin(["cross_arm", "within"])]
M = C.groupby(["train", "test"])["auroc"].mean().unstack().reindex(index=ARMS, columns=ARMS)
im = ax.imshow(M.to_numpy(float), cmap="Blues", vmin=0.55, vmax=0.78)
for i in range(4):
    for j in range(4):
        v = M.iat[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.5, color="white" if v > 0.7 else INK)
ax.set_xticks(range(4), ARMS, rotation=35, ha="right")
ax.set_yticks(range(4), ARMS)
ax.set_xlabel("Test arm")
ax.set_ylabel("Training arm")
ax.grid(False)

F = pd.read_csv(R / "fitness_confound.csv")
F = F[(F["cc_mode"] == "keep") & (F["features"] == "pca")].drop_duplicates("drug_arm", keep="last").set_index("drug_arm")
ax = axes[1]
tag(ax, "b")
cols = [("auroc_drug_model_on_drug", "Drug-arm model", BLUE),
        ("auroc_fitness_model_on_drug", "Control-arm (fitness) model", INK2),
        ("auroc_drug_residual_on_drug", "Drug score after removing fitness", ORANGE)]
x = np.arange(3)
for k, (col, lab_, c) in enumerate(cols):
    ax.bar(x + (k - 1) * 0.27, F.loc[ARMS[:3], col] - 0.5, 0.25, bottom=0.5, color=c, label=lab_)
ax.set_xticks(x, ARMS[:3])
ax.set_ylim(0.5, 0.86)
ax.set_ylabel("AUROC on drug-arm labels")
ax.legend(frameon=False, loc="upper center", fontsize=5.6, ncol=1)

ax = axes[2]
tag(ax, "c")
DCI = pd.read_csv(R / "delta_auroc_ci.csv")
MODE_LABEL = {"keep": "as measured", "regress": "cell cycle removed", "regress_all": "cycle + depth + mito removed"}
for k, cc in enumerate(["keep", "regress", "regress_all"]):
    d = DCI[DCI["cc_mode"] == cc].set_index("drug_arm").reindex(ARMS[:3])
    xk = np.arange(3) + (k - 1) * 0.27
    ax.bar(xk, d["delta_mean"], 0.25, color=[BLUE, AQUA, VIOLET][k], label=MODE_LABEL[cc])
    ax.errorbar(xk, d["delta_mean"], yerr=[d["delta_mean"] - d["delta_lo"], d["delta_hi"] - d["delta_mean"]],
                fmt="none", ecolor=INK, lw=0.7, capsize=1.5)
ax.axhline(0, color=INK2, lw=0.6)
ax.set_xticks(range(3), ["Carbo", "Olap", "NK"])
ax.set_ylim(-0.012, 0.05)
ax.set_ylabel("Drug-specific AUROC gain\n(size-matched, 95% CI)")
ax.legend(frameon=False, fontsize=5.6, loc="upper left")
fig.tight_layout()
save(fig, "Fig3_fitness_confound")

# =============================================================== Fig 4: ceiling
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6))
ax = axes[0]
tag(ax, "a")
icc = pd.read_csv(R / "ceiling_pc_icc_keep.csv").head(20)
ax.plot(icc["pc"], icc["icc_sisters"], "o-", color=BLUE, ms=3, lw=1, label="pre-treatment sisters")
ax.plot(icc["pc"], icc["icc_random"], "o-", color=MUTED, ms=3, lw=1, label="random same-sample pairs")
ax.axhline(0, color=INK2, lw=0.5)
ax.set_xlabel("Principal component")
ax.set_ylabel("Intraclass correlation")
ax.legend(frameon=False)

ax = axes[1]
tag(ax, "b")
curve = pd.read_csv(R / "ceiling_curve.csv")
ax.plot(curve["rho"], 0.9 * curve["auroc"] + 0.05, color=INK2, lw=1)  # same label noise (pi = 0.1) as the points
D = pd.read_csv(R / "ceiling_decomposition_keep.csv")
D = D[(D["pi"] == 0.1) & (D["model"] == "pca_logreg")].set_index("arm")
for arm in ARMS:
    if arm in D.index:
        ax.plot(D.loc[arm, "rho_obs"], D.loc[arm, "auroc_oof"], "o", color=ARM_COLOR[arm], ms=4, label=arm)
        ax.plot(D.loc[arm, "rho_fate"], D.loc[arm, "auroc_if_sister_seen"], "D", mfc="none", color=ARM_COLOR[arm], ms=4)
ax.set_xlabel("Correlation of score with sister's liability")
ax.set_ylabel("AUROC")
ax.legend(frameon=False, fontsize=5.8)

ax = axes[2]
tag(ax, "c")
D2 = pd.read_csv(R / "ceiling_decomposition_keep.csv")
D2 = D2[(D2["model"] == "pca_logreg")]
for k, arm in enumerate(ARMS):
    d = D2[D2["arm"] == arm]
    ax.plot(d["pi"], d["sister_cost"], "o-", color=ARM_COLOR[arm], ms=3, lw=1, label=arm)
ax.set_xlabel("Assumed label noise, π")
ax.set_ylabel("AUROC lost to sister discordance")
ax.set_ylim(0, 0.2)
fig.tight_layout()
save(fig, "Fig5_ceiling")

# =============================================================== Fig 5: biology
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.3), gridspec_kw={"width_ratios": [1.6, 1]})
ax = axes[0]
tag(ax, "a")
contrasts = [("fitness_Control", "Control\n(fitness)"), ("specific_Carboplatin", "Carboplatin\nbeyond fitness"),
             ("specific_Olaparib", "Olaparib\nbeyond fitness"), ("specific_NK", "NK\nbeyond fitness")]
G = {}
for key, _ in contrasts:
    g = pd.read_csv(R / "interpret" / f"gsea_hallmark_{key}.csv")
    G[key] = g.set_index("Term")[["NES", "FDR q-val"]].astype(float)
terms = set()
for g in G.values():
    terms |= set(g.index[g["FDR q-val"] < 0.05])
terms = sorted(terms, key=lambda t: -G["fitness_Control"]["NES"].get(t, 0))
NES = pd.DataFrame({k: G[k]["NES"].reindex(terms) for k, _ in contrasts})
FDR = pd.DataFrame({k: G[k]["FDR q-val"].reindex(terms) for k, _ in contrasts})
im = ax.imshow(NES.to_numpy(float), cmap="RdBu_r", vmin=-2.6, vmax=2.6, aspect="auto")
for i in range(len(terms)):
    for j in range(len(contrasts)):
        if FDR.iat[i, j] < 0.05:
            ax.text(j, i, "*", ha="center", va="center", fontsize=7, color=INK)
ax.set_yticks(range(len(terms)), [t.replace("HALLMARK_", "") for t in terms], fontsize=5.8)
ax.set_xticks(range(len(contrasts)), [c for _, c in contrasts], fontsize=6)
ax.grid(False)
fig.colorbar(im, ax=ax, shrink=0.6, label="NES (* FDR < 0.05)")

ax = axes[1]
tag(ax, "b")
E = pd.read_csv(R / "cnv" / "cnv_enrichment.csv")
for k, arm in enumerate(ARMS):
    d = E[E["arm"] == arm].sort_values("cnv_cluster")
    ax.plot(np.log2(d["odds_ratio"]), d["cnv_cluster"].astype(int) + (k - 1.5) * 0.15, "o", ms=3.5,
            color=ARM_COLOR[arm], label=arm)
ax.axvline(0, color=INK2, lw=0.6)
ax.set_xlabel("log2 odds ratio (pre-resistant vs pre-sensitive)")
ax.set_ylabel("Inferred CNV cluster")
ax.invert_yaxis()
ax.legend(frameon=False, fontsize=5.8)
fig.tight_layout()
save(fig, "Fig4_biology")

# =============================================================== Fig 6: external and clinical
fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.6))
axes = axes.ravel()
X = pd.read_csv(R / "external_validation.csv")
X = X[(X["label"] == "y_persister")]
for ax, (ds, title), letter in zip(axes[:2], [("watermelon", "Watermelon: PC9 + osimertinib"),
                                              ("tnbc_afatinib", "TNBC: MDA-MB-468 + afatinib")], "ab"):
    tag(ax, letter)
    d = X[X["dataset"] == ds]
    rows = [("within_external", "all", "clone_size", "Clone size"), ("within_external", "all", "covariates", "Covariates"),
            ("within_external", "all", "pca", "Expression"), ("within_external", "all", "pca+clone_size", "Expr. + clone size"),
            ("within_external", "all", "density_label_free", "Label-free density"),
            ("within_external", "singleton", "pca", "Expression, singletons"),
            ("transfer_from_resistrace", "all", "trained_on_all_drugs", "ReSisTrace drugs → here"),
            ("transfer_from_resistrace", "all", "trained_on_Control", "ReSisTrace Control → here")]
    yv = np.arange(len(rows))
    for i, (an, sub, mod, lab_) in enumerate(rows):
        r = d[(d["analysis"] == an) & (d["subset"] == sub) & (d["model"] == mod)]
        if len(r):
            r = r.iloc[0]
            c = BLUE if an == "within_external" else ORANGE
            ax.errorbar(r["auroc"], i, xerr=[[r["auroc"] - r["auroc_lo"]], [r["auroc_hi"] - r["auroc"]]], fmt="o", ms=3.5, color=c, lw=0.8)
    ax.axvline(0.5, color=MUTED, ls="--", lw=0.8)
    ax.set_yticks(yv, [r[3] for r in rows], fontsize=6)
    ax.invert_yaxis()
    ax.set_xlim(0.35, 1.0)
    ax.set_xlabel("AUROC (lineage persists)")
ax = axes[2]
tag(ax, "c")
T = pd.read_csv(R / "tcga_ov_cox.csv").drop_duplicates(["signature", "endpoint"], keep="last") \
    if (R / "tcga_ov_cox.csv").exists() else pd.DataFrame(columns=["signature", "endpoint", "HR_per_sd", "lo", "hi"])
yv = np.arange(len(T))
for i, r in T.reset_index(drop=True).iterrows():
    ax.errorbar(r["HR_per_sd"], i, xerr=[[r["HR_per_sd"] - r["lo"]], [r["hi"] - r["HR_per_sd"]]], fmt="s", ms=3,
                color=BLUE if r["endpoint"] == "OS" else ORANGE, lw=0.8)
ax.axvline(1, color=INK2, lw=0.6)
SIG_LABEL = {"fitness_Control": "Fitness (control)", "all_Carboplatin": "Carboplatin, whole contrast",
             "specific_Carboplatin": "Carboplatin-specific", "specific_Olaparib": "Olaparib-specific",
             "specific_NK": "NK-specific"}
ax.set_yticks(yv, [f"{SIG_LABEL.get(s, s)} ({e})" for s, e in zip(T["signature"], T["endpoint"])], fontsize=5.8)
ax.invert_yaxis()
ax.set_xlabel("Hazard ratio per s.d. (95% CI)")

ax = axes[3]
tag(ax, "d")
PS = pd.read_csv(R / "patient_nact.csv").set_index("signature")
PP = pd.read_csv(R / "patient_nact_per_patient.csv")
order = ["fitness_Control", "all_Carboplatin", "specific_Carboplatin", "specific_Olaparib", "specific_NK"]
for i, sg in enumerate(order):
    d = PP[PP["signature"] == sg]
    same = d["location_tn"] == d["location_pn"]
    jit = np.linspace(-0.18, 0.18, len(d))
    ax.plot(d["shift_pn_minus_tn"][~same], i + jit[~same.to_numpy()], "o", mfc="none", color=INK2, ms=3.5)
    ax.plot(d["shift_pn_minus_tn"][same], i + jit[same.to_numpy()], "o", color=INK2, ms=3.5)
    lo = PS.at[sg, "null_median_shift_mean"] - 2 * PS.at[sg, "null_median_shift_sd"]
    hi = PS.at[sg, "null_median_shift_mean"] + 2 * PS.at[sg, "null_median_shift_sd"]
    ax.fill_betweenx([i - 0.3, i + 0.3], lo, hi, color=MUTED, alpha=0.35, lw=0)
    ax.plot([PS.at[sg, "median_shift"]] * 2, [i - 0.3, i + 0.3], color=RED if sg == "fitness_Control" else INK, lw=1.6)
ax.axvline(0, color=INK2, lw=0.6)
ax.set_yticks(range(len(order)), [SIG_LABEL[o] for o in order], fontsize=5.8)
ax.invert_yaxis()
ax.set_xlabel("Post-NACT − treatment-naive score (within-patient z)")
fig.tight_layout()
save(fig, "Fig6_external_clinical")

# =============================================================== Fig 7: second lineage system (Schaff 2026)
if (R / "schaff_predict.csv").exists():
    SP = pd.read_csv(R / "schaff_predict.csv")
    SA = pd.read_csv(R / "schaff_clone_size_adjusted.csv")
    ST = pd.read_csv(R / "schaff_transfer.csv")
    TREAT = ["Dabrafenib", "Trametinib", "CoCl2", "Acid", "Cisplatin", "Doxorubicin"]
    order = [t for t in TREAT if t in set(SP["treatment"])]
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.9), gridspec_kw={"width_ratios": [1.5, 1.1, 1.0]})

    ax = axes[0]
    tag(ax, "a")
    MODELS = [("clone_size", "Clone size before treatment", INK2), ("expression", "Expression", BLUE),
              ("expression+clone_size", "Expression + clone size", VIOLET),
              ("density_label_free", "Label-free density", AQUA)]
    yy = np.arange(len(order))
    for k, (m, lab_, c) in enumerate(MODELS):
        d = SP[SP["model"] == m].set_index("treatment").reindex(order)
        off = (k - 1.5) * 0.18
        ax.errorbar(d["auroc"], yy + off, xerr=[d["auroc"] - d["auroc_lo"], d["auroc_hi"] - d["auroc"]],
                    fmt="o", ms=3, lw=0.8, color=c, label=lab_)
    ax.axvline(0.5, color=MUTED, ls="--", lw=0.8)
    ax.set_yticks(yy, order, fontsize=6.5)
    ax.invert_yaxis()
    ax.set_xlabel("AUROC (lineage detected again)")
    ax.legend(frameon=False, fontsize=5.6, loc="upper center", bbox_to_anchor=(0.45, -0.19), ncol=2,
              handletextpad=0.2, columnspacing=0.8)

    ax = axes[1]
    tag(ax, "b")
    M = ST.pivot(index="train", columns="test", values="auroc").reindex(index=order, columns=order)
    im = ax.imshow(M.to_numpy(float), cmap="Blues", vmin=0.47, vmax=0.67)
    for i in range(len(order)):
        for j in range(len(order)):
            v = M.iat[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=5,
                    color="white" if v > 0.60 else INK)
    ax.set_xticks(range(len(order)), order, rotation=40, ha="right", fontsize=5.8)
    ax.set_yticks(range(len(order)), order, fontsize=5.8)
    ax.set_xlabel("Labels being ranked")
    ax.set_ylabel("Score trained on")
    ax.grid(False)

    ax = axes[2]
    tag(ax, "c")
    A = SA.set_index("treatment").reindex(order)
    x = np.arange(len(order))
    ax.bar(x - 0.2, A["auroc_expression"] - 0.5, 0.38, bottom=0.5, color=BLUE, label="Expression")
    ax.bar(x + 0.2, A["auroc_expression_residual_on_clone_size"] - 0.5, 0.38, bottom=0.5, color=MUTED,
           label="After removing clone size")
    for i, t in enumerate(order):
        if A.loc[t, "lrt_p"] < 0.05:
            ax.text(i, max(A.loc[t, "auroc_expression"], 0.5) + 0.006, "*", ha="center", fontsize=7, color=INK)
    ax.axhline(0.5, color=INK2, lw=0.6)
    ax.set_xticks(x, order, rotation=40, ha="right", fontsize=5.8)
    ax.set_ylim(0.42, 0.76)
    ax.set_ylabel("AUROC")
    ax.legend(frameon=False, fontsize=5.6, loc="upper right")
    fig.tight_layout()
    save(fig, "Fig7_schaff_multitreatment")

# =============================================================== Fig 8: substitutes for an untreated arm
if (R / "control_free_fitness.csv").exists():
    CF = pd.read_csv(R / "control_free_fitness.csv")
    PROXY = [("shared_other_drug_arms", "Other drug arms", BLUE),
             ("control_arm_TRUE", "Untreated control arm", INK),
             ("density", "Label-free density", GREEN)]
    fig, ax = plt.subplots(figsize=(4.6, 2.7))
    arms3 = [a for a in ARMS[:3] if a in set(CF["drug_arm"])]
    yy = np.arange(len(arms3))
    for k, (name, lab_, c) in enumerate(PROXY):
        d = CF[CF["proxy"] == name].set_index("drug_arm").reindex(arms3)
        off = (k - 1) * 0.22
        ax.errorbar(d["gain_over_proxy"], yy + off,
                    xerr=[d["gain_over_proxy"] - d["gain_lo"], d["gain_hi"] - d["gain_over_proxy"]],
                    fmt="o", ms=4, lw=0.9, color=c, label=lab_)
    ax.axvline(0, color=INK2, lw=0.6)
    ax.set_yticks(yy, arms3)
    ax.invert_yaxis()
    ax.set_xlabel("Drug-specific gain over the baseline (AUROC)")
    ax.legend(frameon=False, fontsize=6, loc="lower right")
    fig.tight_layout()
    save(fig, "Fig8_control_free")

# =============================================================== Fig 9: estimators against a known answer
if (R / "simulation_calibration.csv").exists():
    SIM = pd.read_csv(R / "simulation_calibration.csv")
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.6))

    ax = axes[0]
    tag(ax, "a")
    lim = [-0.005, 0.062]
    ax.plot(lim, lim, color=MUTED, ls="--", lw=0.8, zorder=0)
    ax.errorbar(SIM["truth_delta"], SIM["mean_delta"], yerr=SIM["sd_delta"], fmt="o", ms=3.5, lw=0.8,
                color=BLUE, ecolor=MUTED)
    dc = SIM[SIM["parameter"] == "depth_effect"]
    dc = dc[dc["value"] > 0]
    ax.plot(dc["truth_delta"], dc["mean_delta"], "o", ms=5, mfc="none", color=RED, label="depth confound")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("True drug-specific gain")
    ax.set_ylabel("Estimated gain")
    ax.legend(frameon=False, fontsize=5.8, loc="upper left")

    ax = axes[1]
    tag(ax, "b")
    lbl = {"drug_specific_strength": "effect size", "label_noise": "label noise", "n_families": "experiment size",
           "sister_similarity": "sister similarity", "depth_confound": "depth confound",
           "fate_driven_by_own_state": "fate source"}
    groups = [g for g in lbl if g in set(SIM["setting"])]
    for i, g in enumerate(groups):
        d = SIM[SIM["setting"] == g]
        # only the setting that actually has a confound is marked, not its zero baseline
        hot = (d["parameter"] == "depth_effect") & (d["value"] > 0)
        ax.plot([i] * (~hot).sum(), d.loc[~hot, "coverage_delta_95"], "o", ms=3.5, color=INK2)
        ax.plot([i] * hot.sum(), d.loc[hot, "coverage_delta_95"], "o", ms=3.5, color=RED)
    ax.axhline(0.95, color=MUTED, ls="--", lw=0.8)
    ax.set_xticks(range(len(groups)), [lbl[g] for g in groups], rotation=35, ha="right", fontsize=5.6)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Coverage of the 95% interval")

    ax = axes[2]
    tag(ax, "c")
    f = SIM[SIM["parameter"] == "fate_from_own"].sort_values("value", ascending=False)
    if len(f):
        ax.plot(f["value"], f["bias_ceiling_vs_empirical"], "o-", ms=4, lw=1, color=VIOLET)
        ax.axhline(0, color=INK2, lw=0.6)
        ax.set_xlabel("Fate driven by the cell's own state")
        ax.set_ylabel("Ceiling error (estimate $-$ actual)")
        ax.invert_xaxis()
    fig.tight_layout(w_pad=2.5)
    save(fig, "Fig9_simulation")

# =============================================================== Supplementary: GNN ablation
G = REAL[(REAL["split"].isin(["within", "rep_holdout"])) & REAL["model"].isin(["pca_logreg", "mlp", "mlp_pretrain",
                                                                                "persist_gnn_nopretrain", "persist_gnn"])]
if G["model"].nunique() > 1:
    fig, ax = plt.subplots(figsize=(4.5, 2.6))
    order = ["pca_logreg", "mlp", "mlp_pretrain", "persist_gnn_nopretrain", "persist_gnn"]
    s = G[G["split"] == "within"].groupby(["model", "train"])["auroc"].agg(["mean", "std"]).reset_index()
    for k, arm in enumerate(ARMS):
        d = s[s["train"] == arm].set_index("model").reindex(order)
        ax.errorbar(np.arange(len(order)) + (k - 1.5) * 0.12, d["mean"], yerr=d["std"].fillna(0), fmt="o", ms=3,
                    color=ARM_COLOR[arm], label=arm, lw=0.8)
    ax.set_xticks(range(len(order)), [MODEL_LABEL[m] for m in order], rotation=25, ha="right")
    ax.set_ylabel("Within-arm AUROC (mean ± s.d. over seeds)")
    ax.legend(frameon=False, ncol=2)
    save(fig, "FigS3_gnn_ablation")

# =============================================================== Supplementary: typicality
T2 = pd.read_csv(R / "typicality.csv")
T2 = T2[T2["cc_mode"] == "keep"].set_index("arm").reindex(ARMS)
Wl = REAL[(REAL["split"] == "within") & (REAL["model"] == "pca_logreg")].groupby("train")["auroc"].mean().reindex(ARMS)
Ff = pd.read_csv(R / "fitness_confound.csv")
Ff = Ff[(Ff["cc_mode"] == "keep") & (Ff["features"] == "pca")].drop_duplicates("drug_arm", keep="last").set_index("drug_arm")
fit = Ff["auroc_fitness_model_on_drug"].reindex(ARMS)
fit["Control"] = Ff["auroc_control_model_on_control"].iloc[0]
fig, ax = plt.subplots(figsize=(4.2, 2.6))
x = np.arange(4)
for k, (vals, lab_, c) in enumerate([(Wl, "Supervised (PCA-logistic)", BLUE), (fit, "Control-arm model", INK2),
                                     (T2["auroc_density_within_sample"], "Label-free density", AQUA)]):
    ax.bar(x + (k - 1) * 0.27, vals - 0.5, 0.25, bottom=0.5, color=c, label=lab_)
ax.set_xticks(x, ARMS)
ax.set_ylim(0.5, 0.82)
ax.set_ylabel("AUROC")
ax.legend(frameon=False, fontsize=6, loc="upper right", ncol=1)
save(fig, "FigS1_typicality")

# =============================================================== Supplementary: marker panel
MP = pd.read_csv(R / "interpret" / "marker_panel.csv")
MP = MP[MP["z_diff"].notna()]
genes = MP.drop_duplicates("gene")[["category", "gene"]]
cols = [("Control", "Control"), ("Carboplatin", "Carboplatin"), ("Olaparib", "Olaparib"), ("NK", "NK")]
piv = MP.pivot_table(index="gene", columns="arm", values="z_diff").reindex(genes["gene"])
padj = MP.pivot_table(index="gene", columns="arm", values="padj_diff").reindex(genes["gene"])
ctrl = MP.drop_duplicates("gene").set_index("gene")["z_control"].reindex(genes["gene"])
Zm = np.column_stack([ctrl.to_numpy()] + [piv[a].to_numpy() for a, _ in cols[1:]])
fig, ax = plt.subplots(figsize=(3.9, 5.6))
im = ax.imshow(Zm, cmap="RdBu_r", vmin=-5, vmax=5, aspect="auto")
for i, g in enumerate(genes["gene"]):
    for j, (a, _) in enumerate(cols[1:], start=1):
        if padj.at[g, a] < 0.05:
            ax.text(j, i, "*", ha="center", va="center", fontsize=7, color=INK)
ax.set_yticks(range(len(genes)), genes["gene"], fontsize=6)
ax.set_xticks(range(len(cols)), [c for _, c in cols], fontsize=6, rotation=40, ha="left")
ax.xaxis.tick_top()
ax.grid(False)
cats = genes["category"].tolist()
for i in range(1, len(cats)):
    if cats[i] != cats[i - 1]:
        ax.axhline(i - 0.5, color=SURFACE, lw=2)
for c in dict.fromkeys(cats):
    idx = [i for i, x in enumerate(cats) if x == c]
    ax.text(len(cols) - 0.4, np.mean(idx), c, fontsize=6, color=INK2, va="center", ha="left")
fig.colorbar(im, ax=ax, shrink=0.5, pad=0.42, label="z, pre-resistant vs pre-sensitive\n(drug columns: beyond control; * FDR < 0.05)")
save(fig, "FigS2_marker_panel")
