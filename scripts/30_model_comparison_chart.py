"""Summary chart: for each representation of the cells, how well the drug-arm model and the untreated-arm
(fitness) model predict the drug-arm labels. Values are read from results/sensitivity_representations.csv and
averaged over the three drug arms; the thin bar behind each dot spans the three arms.

Run: python scripts/30_model_comparison_chart.py   -> paper/charts/model_comparison.png
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RP = pd.read_csv(ROOT / "results" / "sensitivity_representations.csv")
NAMES = {  # display order, top to bottom
    "baseline": "Principal components\n(main model)",
    "harmony": "Harmony",
    "pearson": "Pearson residuals",
    "scvi": "scVI",
    "geneformer_V2-104M_CLcancer": "Geneformer",
    "scgpt_human": "scGPT",
}
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
DRUG, FIT = "#2a78d6", "#eb6834"  # categorical slots 1 and 2 (validated)

rows = []
for key, label in NAMES.items():
    d = RP[RP["representation"] == key]
    assert len(d) == 3, f"{key}: expected three drug arms, found {len(d)}"
    for col, name in [("auroc_drug_model_on_drug", "drug"), ("auroc_fitness_model_on_drug", "fitness")]:
        rows.append({"rep": label, "model": name, "mean": d[col].mean(), "lo": d[col].min(), "hi": d[col].max()})
T = pd.DataFrame(rows)

plt.rcParams.update({"font.family": "sans-serif", "font.size": 9, "text.color": INK, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK})
fig, ax = plt.subplots(figsize=(7.2, 4.0), facecolor=SURFACE)
ax.set_facecolor(SURFACE)
labels = list(NAMES.values())
for i, rep in enumerate(labels):
    y = len(labels) - 1 - i
    d = T[T["rep"] == rep].set_index("model")
    ax.plot([d.loc["fitness", "mean"], d.loc["drug", "mean"]], [y, y], color=GRID, lw=2, zorder=1)
    for model, color, dy in [("drug", DRUG, 0.12), ("fitness", FIT, -0.12)]:
        r = d.loc[model]
        ax.plot([r["lo"], r["hi"]], [y + dy, y + dy], color=color, lw=1.2, alpha=0.45, solid_capstyle="round", zorder=2)
        ax.scatter(r["mean"], y + dy, s=64, color=color, edgecolor=SURFACE, linewidth=2, zorder=3)
    ax.text(0.768, y, f"{d.loc['drug', 'mean']:.3f}", color=INK, va="center", ha="left", fontsize=8.5)
    ax.text(0.803, y, f"{d.loc['fitness', 'mean']:.3f}", color=INK, va="center", ha="left", fontsize=8.5)
ax.text(0.768, len(labels) - 0.35, "Drug-arm\nmodel", color=INK2, fontsize=7.5, va="bottom")
ax.text(0.803, len(labels) - 0.35, "Fitness\nmodel", color=INK2, fontsize=7.5, va="bottom")

ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels[::-1])
ax.set_xlim(0.60, 0.835)
ax.set_xticks([0.60, 0.65, 0.70, 0.75])
ax.set_ylim(-0.6, len(labels) - 0.1)
ax.set_xlabel("AUROC on the drug-arm labels (mean of carboplatin, olaparib and NK; bar = range over the three)")
ax.grid(axis="x", color=GRID, lw=0.8)
ax.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(GRID)
ax.tick_params(axis="y", length=0)
ax.scatter([], [], s=64, color=DRUG, label="Drug-arm model (trained on the drug arm's own labels)")
ax.scatter([], [], s=64, color=FIT, label="Fitness model (trained only on the untreated arm)")
ax.legend(loc="upper left", bbox_to_anchor=(0, 1.13), ncol=1, frameon=False, fontsize=8, handletextpad=0.3)
fig.suptitle("The untreated-arm model predicts drug-arm fates almost as well, in every representation",
             x=0.01, ha="left", fontsize=10.5, fontweight="bold", y=1.03)
out = ROOT / "paper" / "charts" / "model_comparison.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=300, bbox_inches="tight", facecolor=SURFACE)
print("wrote", out)
print(T.pivot(index="rep", columns="model", values="mean").loc[labels].round(3).to_string())
