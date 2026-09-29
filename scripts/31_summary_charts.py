"""Four summary charts, one per main finding, in the style of scripts/30_model_comparison_chart.py.
Every value is read from results/; nothing is typed in by hand.

  drug_specific_gain.png         refitting-bootstrap gain per drug arm, with the smallest gain the design resolves
  clone_size_vs_expression.png   second lineage system: clone size vs expression, per treatment
  patients_after_chemo.png       per-patient change of three signatures after neoadjuvant chemotherapy
  sister_ceiling.png             observed AUROC vs AUROC if the treated sister itself were scored

Run: python scripts/31_summary_charts.py   -> new_paper/charts/
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
OUT = ROOT / "new_paper" / "charts"
OUT.mkdir(parents=True, exist_ok=True)
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE = "#2a78d6", "#eb6834"  # categorical slots 1 and 2 (validated)
plt.rcParams.update({"font.family": "sans-serif", "font.size": 9, "text.color": INK, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK})


def frame(title, size=(7.2, 3.6)):
    fig, ax = plt.subplots(figsize=size, facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="y", length=0)
    fig.suptitle(title, x=0.01, ha="left", fontsize=10.5, fontweight="bold", y=1.02)
    return fig, ax


def save(fig, name):
    fig.savefig(OUT / name, dpi=300, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print("wrote", OUT / name)


ARMS = ["Carboplatin", "Olaparib", "NK"]

# ---- 1. drug-specific gain
D = pd.read_csv(R / "delta_auroc_refit_ci.csv").query("cc_mode == 'keep'").set_index("drug_arm").loc[ARMS]
DS = pd.read_csv(R / "design_resistrace.csv").set_index("arm").loc[ARMS]
fig, ax = frame("The drug-specific gain is about 0.02 AUROC, and no arm can separate it from zero")
for i, arm in enumerate(ARMS):
    y = len(ARMS) - 1 - i
    r = D.loc[arm]
    ax.plot([r["delta_lo"], r["delta_hi"]], [y, y], color=BLUE, lw=2, solid_capstyle="round", zorder=2)
    ax.scatter(r["delta"], y, s=70, color=BLUE, edgecolor=SURFACE, linewidth=2, zorder=3)
    lim = DS.loc[arm, "smallest_detectable_delta_80pct"]
    ax.plot([lim, lim], [y - 0.28, y + 0.28], color=INK2, lw=1.2, ls=(0, (2, 2)), zorder=2)
    ax.text(r["delta_hi"] + 0.002, y, f"{r['delta']:.3f}  [{r['delta_lo']:.3f}, {r['delta_hi']:.3f}]",
            va="center", fontsize=8.5)
ax.axvline(0, color=INK2, lw=1)
ax.set_yticks(range(len(ARMS)))
ax.set_yticklabels([a if a != "NK" else "NK cells" for a in ARMS][::-1])
ax.set_xlim(-0.02, 0.085)
ax.set_ylim(-0.6, len(ARMS) - 0.3)
ax.set_xlabel("Drug-specific gain in AUROC over the fitness model (training size matched)")
ax.scatter([], [], s=70, color=BLUE, label="Estimate with 95% interval (whole procedure refitted, 60 bootstrap samples)")
ax.plot([], [], color=INK2, lw=1.2, ls=(0, (2, 2)), label="Smallest gain this experiment can detect (80% power)")
ax.legend(loc="upper left", bbox_to_anchor=(0, -0.22), frameon=False, fontsize=8)
save(fig, "drug_specific_gain.png")

# ---- 2. second lineage system
S = pd.read_csv(R / "schaff_predict.csv")
TR = ["Dabrafenib", "Trametinib", "CoCl2", "Acid", "Cisplatin", "Doxorubicin"]
LAB = {"CoCl2": "CoCl2 (hypoxia mimic)", "Acid": "Acidic medium"}
fig, ax = frame("Second lineage system: clone size before treatment predicts better than gene expression",
                size=(7.2, 4.0))
for i, t in enumerate(TR):
    y = len(TR) - 1 - i
    d = S[S["treatment"] == t].set_index("model")
    e, c = d.loc["expression"], d.loc["clone_size"]
    ax.plot([e["auroc"], c["auroc"]], [y, y], color=GRID, lw=2, zorder=1)
    for r, color, dy in [(c, ORANGE, 0.12), (e, BLUE, -0.12)]:
        ax.plot([r["auroc_lo"], r["auroc_hi"]], [y + dy, y + dy], color=color, lw=1.2, alpha=0.45, zorder=2)
        ax.scatter(r["auroc"], y + dy, s=64, color=color, edgecolor=SURFACE, linewidth=2, zorder=3)
    ax.text(0.965, y, f"{c['auroc']:.2f}", va="center", fontsize=8.5)
    ax.text(1.005, y, f"{e['auroc']:.2f}", va="center", fontsize=8.5)
ax.text(0.965, len(TR) - 0.4, "Clone\nsize", color=INK2, fontsize=7.5, va="bottom")
ax.text(1.005, len(TR) - 0.4, "Expres-\nsion", color=INK2, fontsize=7.5, va="bottom")
ax.set_yticks(range(len(TR)))
ax.set_yticklabels([LAB.get(t, t) for t in TR][::-1])
ax.set_xlim(0.5, 1.04)
ax.set_xticks([0.5, 0.6, 0.7, 0.8, 0.9])
ax.set_ylim(-0.6, len(TR) - 0.1)
ax.set_xlabel("AUROC for whether a lineage is detected again after treatment (bar = 95% interval)")
ax.scatter([], [], s=64, color=ORANGE, label="Clone size before treatment")
ax.scatter([], [], s=64, color=BLUE, label="Gene expression (50 principal components)")
ax.legend(loc="upper left", bbox_to_anchor=(0, 1.14), ncol=2, frameon=False, fontsize=8)
save(fig, "clone_size_vs_expression.png")

# ---- 3. patients after chemotherapy
PP = pd.read_csv(R / "patient_nact_per_patient.csv")
PS = pd.read_csv(R / "patient_nact.csv").set_index("signature")
SIG = [("fitness_Control", "Fitness signature"), ("all_Carboplatin", "Carboplatin signature\n(whole contrast)"),
       ("specific_Carboplatin", "Carboplatin-specific\nsignature")]
fig, ax = frame("After chemotherapy in 11 patients, the fitness state goes down; the drug signatures do not go up",
                size=(7.2, 3.6))
rng = np.random.default_rng(0)
for i, (key, label) in enumerate(SIG):
    y = len(SIG) - 1 - i
    d = PP[PP["signature"] == key]
    mu, sd = PS.loc[key, "null_median_shift_mean"], PS.loc[key, "null_median_shift_sd"]
    ax.fill_betweenx([y - 0.32, y + 0.32], mu - 2 * sd, mu + 2 * sd, color=GRID, lw=0, zorder=1)
    same = (d["location_tn"] == d["location_pn"]).to_numpy()
    jit = rng.uniform(-0.18, 0.18, len(d))
    ax.scatter(d["shift_pn_minus_tn"][same], y + jit[same], s=46, color=BLUE, edgecolor=SURFACE, lw=1.5, zorder=3)
    ax.scatter(d["shift_pn_minus_tn"][~same], y + jit[~same], s=46, facecolor=SURFACE, edgecolor=BLUE, lw=1.5, zorder=3)
    med = PS.loc[key, "median_shift"]
    ax.plot([med, med], [y - 0.3, y + 0.3], color=INK, lw=2, zorder=4)
    ax.text(0.62, y, f"median {med:+.2f}\nWilcoxon p = {PS.loc[key, 'wilcoxon_p']:.3f}", va="center", fontsize=8)
ax.axvline(0, color=INK2, lw=1)
ax.set_yticks(range(len(SIG)))
ax.set_yticklabels([s[1] for s in SIG][::-1])
ax.set_xlim(-0.9, 0.95)
ax.set_ylim(-0.6, len(SIG) - 0.3)
ax.set_xlabel("Change after chemotherapy (post minus pre, in within-patient s.d.); < 0 means lower after treatment")
ax.scatter([], [], s=46, color=BLUE, label="Patient, both samples from the same site")
ax.scatter([], [], s=46, facecolor=SURFACE, edgecolor=BLUE, lw=1.5, label="Patient, different sites")
ax.plot([], [], color=INK, lw=2, label="Median")
ax.fill_between([], [], color=GRID, label="Random gene sets (mean ± 2 s.d.)")
ax.legend(loc="upper left", bbox_to_anchor=(0, -0.22), ncol=2, frameon=False, fontsize=8)
save(fig, "patients_after_chemo.png")

# ---- 4. sister ceiling
C = pd.read_csv(R / "ceiling_decomposition_keep.csv").query("model == 'pca_logreg' and pi == 0.1").set_index("arm")
AR = ARMS + ["Control"]
fig, ax = frame("Sisters are not identical, so even a perfect model of the sequenced cell loses up to ~0.1 AUROC")
for i, arm in enumerate(AR):
    y = len(AR) - 1 - i
    r = C.loc[arm]
    ax.plot([r["auroc_oof"], r["auroc_if_sister_seen"]], [y, y], color=GRID, lw=3, zorder=1)
    ax.scatter(r["auroc_oof"], y, s=70, color=BLUE, edgecolor=SURFACE, linewidth=2, zorder=3)
    ax.scatter(r["auroc_if_sister_seen"], y, s=70, color=ORANGE, edgecolor=SURFACE, linewidth=2, zorder=3)
    ax.text(r["auroc_if_sister_seen"] + 0.006, y, f"cost {r['sister_cost']:.2f}", va="center", fontsize=8.5)
ax.set_yticks(range(len(AR)))
ax.set_yticklabels([{"NK": "NK cells", "Control": "Control (no drug)"}.get(a, a) for a in AR][::-1])
ax.set_xlim(0.68, 0.90)
ax.set_ylim(-0.6, len(AR) - 0.3)
ax.set_xlabel("AUROC (label noise 10%); the right-hand value is an upper bound")
ax.scatter([], [], s=70, color=BLUE, label="Observed (score of the sequenced sister)")
ax.scatter([], [], s=70, color=ORANGE, label="Expected if the treated sister itself were scored")
ax.legend(loc="upper left", bbox_to_anchor=(0, -0.22), ncol=1, frameon=False, fontsize=8)
save(fig, "sister_ceiling.png")
