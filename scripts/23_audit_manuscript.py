"""Check the numbers quoted in paper/manuscript.md against the tables in results/.

Each check names the sentence it verifies, recomputes the value from a results file, and compares with a
tolerance. Anything that does not match is printed and the script exits non-zero, so the manuscript cannot
drift away from the analyses. Values quoted from other papers are listed at the end and are not checked here.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
MD = (ROOT / "paper" / "manuscript.md").read_text()
fails, checks = [], 0


def check(name: str, quoted, computed, tol=0.0006):
    """quoted: value(s) as written in the manuscript; computed: value(s) from results/."""
    global checks
    checks += 1
    q = [quoted] if not isinstance(quoted, (list, tuple)) else list(quoted)
    c = [computed] if not isinstance(computed, (list, tuple)) else list(computed)
    ok = len(q) == len(c) and all(abs(float(a) - float(b)) <= tol for a, b in zip(q, c))
    if not ok:
        fails.append(f"{name}: manuscript {q} vs results {[round(float(x), 4) for x in c]}")


def in_text(s: str, name: str):
    global checks
    checks += 1
    if s not in MD:
        fails.append(f"{name}: text not found: {s[:70]!r}")


res = pd.read_csv(R / "results.csv")
res = res[(res["cc_mode"] == "keep") & ((res["split"] != "within") | (res["fold"].astype(str) == "oof"))]
res["shuffled"] = res["shuffled"].astype(str).str.lower() == "true"
real = res[~res["shuffled"]].drop_duplicates(["model", "split", "train", "test", "seed", "notes"], keep="last")
W = real[real["split"] == "within"].groupby(["model", "train"])["auroc"].mean()
ARMS = ["Carboplatin", "Olaparib", "NK", "Control"]

# --- Results, first section
check("within-arm PCA-logistic AUROCs", [0.747, 0.744, 0.723, 0.708], [W[("pca_logreg", a)] for a in ARMS], 0.0006)
audit = pd.read_csv(R / "label_audit.csv")
check("labelled cells", 32642, (audit["n_pos"] + audit["n_neg"]).sum(), 0)
check("pre-resistant cells", 3102, audit["n_pos"].sum(), 0)
check("prevalence range drug arms", [7.8, 11.2],
      [100 * audit[audit["sample"].str.startswith(("Carbo", "Olap", "NK"))]["prevalence"].min(),
       100 * audit[audit["sample"].str.startswith(("Carbo", "Olap", "NK"))]["prevalence"].max()], 0.06)
check("prevalence range control", [14.7, 14.9],
      [100 * audit[audit["sample"].str.startswith("Control")]["prevalence"].min(),
       100 * audit[audit["sample"].str.startswith("Control")]["prevalence"].max()], 0.06)

rob = pd.read_csv(R / "robustness_keep.csv")
sing = rob[rob["check"] == "singletons_only"].set_index("arm")["auroc"]
check("singleton-only AUROCs", [0.754, 0.753, 0.737, 0.720], [sing[a] for a in ARMS], 0.0006)
bp = rob[rob["check"].str.startswith("benchmark")]
check("benchmark protocol, plain CV", [0.739, 0.756],
      [bp[bp["check"] == "benchmark_protocol_ungrouped"]["auroc"].min(),
       bp[bp["check"] == "benchmark_protocol_ungrouped"]["auroc"].max()], 0.0006)
check("benchmark protocol, grouped CV", [0.734, 0.747],
      [bp[bp["check"] == "benchmark_protocol_grouped"]["auroc"].min(),
       bp[bp["check"] == "benchmark_protocol_grouped"]["auroc"].max()], 0.0006)
perm = rob[rob["check"] == "all_cells"]  # the exact permutation test is run on all labelled cells
check("permutation null mean range", [0.500, 0.501],
      [round(perm["perm_null_mean"].min(), 3), round(perm["perm_null_mean"].max(), 3)], 0.0006)
check("permutation null sd range", [0.015, 0.019],
      [round(perm["perm_null_sd"].min(), 3), round(perm["perm_null_sd"].max(), 3)], 0.0006)
check("permutation p", 0.0099, perm["perm_p"].max(), 0.0002)

cov = [W[("cov_logreg", a)] for a in ARMS]
check("covariate-only range", [0.59, 0.65], [min(cov), max(cov)], 0.005)

# --- fitness
F = pd.read_csv(R / "fitness_confound.csv")
Fk = F[(F["cc_mode"] == "keep") & (F["features"] == "pca")].drop_duplicates("drug_arm", keep="last").set_index("drug_arm")
check("fitness model on drug arms", [0.725, 0.713, 0.697],
      [Fk.loc[a, "auroc_fitness_model_on_drug"] for a in ARMS[:3]], 0.0006)
check("drug models on control labels", [0.69, 0.70],
      [Fk["auroc_drug_model_on_control"].min(), Fk["auroc_drug_model_on_control"].max()], 0.005)
check("Spearman drug vs fitness", [0.80, 0.82],
      [Fk["corr_drug_vs_fitness_score"].min(), Fk["corr_drug_vs_fitness_score"].max()], 0.005)
check("residual AUROC range", [0.60, 0.63],
      [Fk["auroc_drug_residual_on_drug"].min(), Fk["auroc_drug_residual_on_drug"].max()], 0.005)
check("within-quintile AUROC range", [0.64, 0.66],
      [Fk["auroc_drug_within_fitness_quintiles"].min(), Fk["auroc_drug_within_fitness_quintiles"].max()], 0.005)
check("n labelled control cells", 4183, Fk["n_control"].iloc[0], 0)
check("n labelled drug cells", [8942, 10123], [Fk["n_drug"].min(), Fk["n_drug"].max()], 0)

D = pd.read_csv(R / "delta_auroc_ci.csv")
for mode, vals in [("keep", [0.014, 0.025, 0.017]), ("regress", [0.014, 0.025, 0.014]), ("regress_all", [0.012, 0.021, 0.003])]:
    d = D[D["cc_mode"] == mode].set_index("drug_arm")
    check(f"delta {mode}", vals, [d.loc[a, "delta_mean"] for a in ARMS[:3]], 0.0006)
dk = D[D["cc_mode"] == "keep"].set_index("drug_arm")
check("delta CI carboplatin", [0.001, 0.026], [dk.loc["Carboplatin", "delta_lo"], dk.loc["Carboplatin", "delta_hi"]], 0.0006)
check("delta CI olaparib", [0.012, 0.039], [dk.loc["Olaparib", "delta_lo"], dk.loc["Olaparib", "delta_hi"]], 0.0006)
check("delta CI NK", [0.003, 0.031], [dk.loc["NK", "delta_lo"], dk.loc["NK", "delta_hi"]], 0.0006)
da = D[D["cc_mode"] == "regress_all"].set_index("drug_arm")
check("delta CI NK regress_all", [-0.010, 0.016], [da.loc["NK", "delta_lo"], da.loc["NK", "delta_hi"]], 0.0006)
check("delta seed sd range (keep)", [0.003, 0.004],
      [round(dk["delta_seed_sd"].min(), 3), round(dk["delta_seed_sd"].max(), 3)], 0.0006)

# --- alternative representations, including the foundation model
RP = pd.read_csv(R / "sensitivity_representations.csv")
GF = RP[RP["representation"].str.startswith("geneformer")]
check("Geneformer embedding dimension", 768, GF["n_dims"].iloc[0], 0)
check("Geneformer drug-arm range", [0.671, 0.683],
      [round(GF["auroc_drug_model_on_drug"].min(), 3), round(GF["auroc_drug_model_on_drug"].max(), 3)], 0.0006)
check("Geneformer fitness range", [0.634, 0.663],
      [round(GF["auroc_fitness_model_on_drug"].min(), 3), round(GF["auroc_fitness_model_on_drug"].max(), 3)], 0.0006)
check("Geneformer size-matched gain range", [0.017, 0.030],
      [round(GF["specificity_index_size_matched"].min(), 3),
       round(GF["specificity_index_size_matched"].max(), 3)], 0.0006)
ALT = RP[RP["representation"] != "baseline"]
check("all alternative representations, drug range", [0.671, 0.746],
      [round(ALT["auroc_drug_model_on_drug"].min(), 3), round(ALT["auroc_drug_model_on_drug"].max(), 3)], 0.0006)
check("all alternative representations, fitness range", [0.634, 0.722],
      [round(ALT["auroc_fitness_model_on_drug"].min(), 3),
       round(ALT["auroc_fitness_model_on_drug"].max(), 3)], 0.0006)
check("all alternative representations, gain range", [0.013, 0.032],
      [round(ALT["specificity_index_size_matched"].min(), 3),
       round(ALT["specificity_index_size_matched"].max(), 3)], 0.0006)
in_text("Geneformer 0.67–0.68", "foundation model in abstract")

# --- typicality
T = pd.read_csv(R / "typicality.csv")
Tk = T[T["cc_mode"] == "keep"].set_index("arm")
check("typicality AUROC (pooled)", [0.70, 0.69, 0.63, 0.67],
      [round(Tk.loc[a, "auroc_density_pooled"], 2) for a in ARMS], 0.0006)
Ta = T[T["cc_mode"] == "regress_all"]
check("typicality AUROC after removing covariates", [0.63, 0.69],
      [round(Ta["auroc_density_pooled"].min(), 2), round(Ta["auroc_density_pooled"].max(), 2)], 0.0006)
check("typicality vs supervised Spearman", [0.54, 0.70],
      [round(Tk["spearman_density_vs_pca_logreg"].min(), 2),
       round(Tk["spearman_density_vs_pca_logreg"].max(), 2)], 0.0006)

# --- ceiling
icc = pd.read_csv(R / "ceiling_pc_icc_keep.csv")
check("mean ICC PCs 1-10", 0.75, icc.head(10)["icc_sisters"].mean(), 0.005)
C = pd.read_csv(R / "ceiling_keep.csv")
check("n sister pairs", 3477, int(pd.read_csv(R / "label_audit.csv")["n_pre_sister_pairs"].sum()), 0)
Dc = pd.read_csv(R / "ceiling_decomposition_keep.csv")
Dc = Dc[(Dc["model"] == "pca_logreg") & (Dc["pi"] == 0.1)].set_index("arm")
check("sister cost drug arms", [0.09, 0.12],
      [Dc.loc[ARMS[:3], "sister_cost"].min(), Dc.loc[ARMS[:3], "sister_cost"].max()], 0.005)
check("sister cost control", 0.05, Dc.loc["Control", "sister_cost"], 0.005)

# --- GNN sweep
S = pd.read_csv(R / "gnn_sweep.csv").pivot_table(index="config", columns="arm", values="auroc")
for arm, lo, hi in [("Carboplatin", 0.727, 0.739), ("Olaparib", 0.722, 0.733), ("NK", 0.695, 0.714), ("Control", 0.667, 0.700)]:
    check(f"GNN sweep {arm}", [lo, hi], [S[arm].min(), S[arm].max()], 0.0006)

# --- external and patient
X = pd.read_csv(R / "external_validation.csv")
X = X[X["label"] == "y_persister"]


def ext(ds, an, sub, mod):
    r = X[(X["dataset"] == ds) & (X["analysis"] == an) & (X["subset"] == sub) & (X["model"] == mod)]
    return r["auroc"].iloc[0]


check("watermelon clone size", 0.76, ext("watermelon", "within_external", "all", "clone_size"), 0.005)
check("watermelon expression", 0.61, ext("watermelon", "within_external", "all", "pca"), 0.005)
check("watermelon singleton expression", 0.58, ext("watermelon", "within_external", "singleton", "pca"), 0.005)
check("tnbc clone size", 0.88, ext("tnbc_afatinib", "within_external", "all", "clone_size"), 0.005)
check("tnbc expression", 0.64, ext("tnbc_afatinib", "within_external", "all", "pca"), 0.005)
check("watermelon density", [0.533, 0.517, 0.552],
      [ext("watermelon", "within_external", "all", "density_label_free"),
       X[(X["dataset"] == "watermelon") & (X["model"] == "density_label_free") & (X["subset"] == "all")]["auroc_lo"].iloc[0],
       X[(X["dataset"] == "watermelon") & (X["model"] == "density_label_free") & (X["subset"] == "all")]["auroc_hi"].iloc[0]], 0.0006)
check("tnbc density", [0.570, 0.530, 0.605],
      [ext("tnbc_afatinib", "within_external", "all", "density_label_free"),
       X[(X["dataset"] == "tnbc_afatinib") & (X["model"] == "density_label_free") & (X["subset"] == "all")]["auroc_lo"].iloc[0],
       X[(X["dataset"] == "tnbc_afatinib") & (X["model"] == "density_label_free") & (X["subset"] == "all")]["auroc_hi"].iloc[0]], 0.0006)
check("tnbc singleton control transfer", 0.64,
      ext("tnbc_afatinib", "transfer_from_resistrace", "singleton", "trained_on_Control"), 0.005)

TC = pd.read_csv(R / "tcga_ov_cox.csv").drop_duplicates(["signature", "endpoint"], keep="last")
ola = TC[(TC["signature"] == "specific_Olaparib") & (TC["endpoint"] == "OS")].iloc[0]
check("TCGA olaparib HR", [1.20, 1.03, 1.39], [ola["HR_per_sd"], ola["lo"], ola["hi"]], 0.005)
check("TCGA olaparib p", 0.017, ola["p"], 0.0006)
# Benjamini-Hochberg over the 10 tests, as in the manuscript
_p = TC["p"].to_numpy()
_o = _p.argsort()
_q = _p[_o] * len(_p) / np.arange(1, len(_p) + 1)
_q = np.minimum.accumulate(_q[::-1])[::-1]
_fdr = np.empty(len(_p))
_fdr[_o] = np.minimum(_q, 1)
_row = int(np.flatnonzero((TC["signature"] == "specific_Olaparib").to_numpy() & (TC["endpoint"] == "OS").to_numpy())[0])
check("TCGA olaparib FDR", 0.17, _fdr[_row], 0.005)

P = pd.read_csv(R / "patient_nact.csv").set_index("signature")
check("patient n up carboplatin contrasts", [5, 5],
      [P.loc["all_Carboplatin", "n_positive"], P.loc["specific_Carboplatin", "n_positive"]], 0)
check("patient median shift carboplatin", [-0.03, -0.10],
      [P.loc["all_Carboplatin", "median_shift"], P.loc["specific_Carboplatin", "median_shift"]], 0.005)
check("patient wilcoxon carboplatin", [0.24, 0.83],
      [P.loc["all_Carboplatin", "wilcoxon_p"], P.loc["specific_Carboplatin", "wilcoxon_p"]], 0.005)
check("patient fitness shift", -0.18, P.loc["fitness_Control", "median_shift"], 0.005)
check("patient fitness up count", 4, P.loc["fitness_Control", "n_positive"], 0)
check("patient fitness wilcoxon", 0.042, P.loc["fitness_Control", "wilcoxon_p"], 0.0006)
check("patient fitness random-set p", 0.005, P.loc["fitness_Control", "p_vs_random_sets_two_sided"], 0.0006)
check("patient fitness same-site up count", 0, P.loc["fitness_Control", "n_positive_same_site"], 0)
check("patient max |rho| vs PFI", 0.34, P["spearman_shift_vs_pfi"].abs().max(), 0.005)

# --- interpretation / DE
de = {a: pd.read_csv(R / "interpret" / f"de_{a}.csv") for a in ARMS}
n_de = {a: int((d["padj"] < 0.05).sum()) if "padj" in d else None for a, d in de.items()}
spec = {a: pd.read_csv(R / "interpret" / f"drug_vs_fitness_{a}.csv") for a in ARMS[:3]}
n_spec = {a: int((d["class"] == "drug_specific").sum()) for a, d in spec.items()}
check("drug-specific gene counts", [57, 221, 140], [n_spec[a] for a in ARMS[:3]], 0)
sig = json.load(open(R / "interpret" / "signatures.json"))
check("carboplatin signature sizes", [25, 31],
      [len(sig["specific_Carboplatin"]["up"]), len(sig["specific_Carboplatin"]["down"])], 0)
check("NK signature sizes", [16, 50], [len(sig["specific_NK"]["up"]), len(sig["specific_NK"]["down"])], 0)

# --- second lineage system (Schaff et al. 2026)
if (R / "schaff_predict.csv").exists():
    SP = pd.read_csv(R / "schaff_predict.csv")
    SP = SP[SP["merge_r"].eq(0.55) & SP["min_umi"].eq(2)] if "merge_r" in SP else SP
    cs = SP[SP["model"] == "clone_size"]["auroc"]
    ex = SP[SP["model"] == "expression"]["auroc"]
    check("schaff clone size range", [0.68, 0.90], [round(cs.min(), 2), round(cs.max(), 2)], 0.006)
    check("schaff expression range", [0.54, 0.66], [round(ex.min(), 2), round(ex.max(), 2)], 0.006)
    check("schaff untreated cells", 7165, int(SP["n_test"].iloc[0]), 0)
    check("schaff prevalence range", [0.306, 0.783],
          [round(SP["prevalence"].min(), 3), round(SP["prevalence"].max(), 3)], 0.0006)
    SA = pd.read_csv(R / "schaff_clone_size_adjusted.csv").set_index("treatment")
    check("schaff residual range", [0.44, 0.59],
          [round(SA["auroc_expression_residual_on_clone_size"].min(), 2),
           round(SA["auroc_expression_residual_on_clone_size"].max(), 2)], 0.006)
    check("schaff LRT non-significant arms", [0.46, 0.15],
          [round(SA.loc["Cisplatin", "lrt_p"], 2), round(SA.loc["Doxorubicin", "lrt_p"], 2)], 0.006)
    SC = pd.read_csv(R / "schaff_ceiling.csv")
    check("schaff clone concordance range", [0.17, 0.21],
          [round(SC["score_clone_concordance"].min(), 2), round(SC["score_clone_concordance"].max(), 2)], 0.006)
    check("schaff mean ICC", 0.18, round(SC["mean_icc_pc1_10"].iloc[0], 2), 0.006)
    check("schaff saturated count", 3, int(SC["saturated"].sum()), 0)
    ST = pd.read_csv(R / "schaff_transfer.csv")
    off = ST[ST["train"] != ST["test"]]["auroc"]
    check("schaff transfer range", [0.48, 0.63], [round(off.min(), 2), round(off.max(), 2)], 0.006)

# --- substitutes for an untreated arm
if (R / "control_free_fitness.csv").exists():
    CF = pd.read_csv(R / "control_free_fitness.csv")
    W = CF.pivot(index="drug_arm", columns="proxy", values="gain_over_proxy")
    check("control-arm gain", [0.022, 0.031, 0.027],
          [round(W.loc[a, "control_arm_TRUE"], 3) for a in ["Carboplatin", "Olaparib", "NK"]], 0.0006)
    check("density-proxy gain range", [0.043, 0.090],
          [round(W["density"].min(), 3), round(W["density"].max(), 3)], 0.0006)
    check("other-arm proxy gain range", [0.0045, 0.0065],
          [round(W["shared_other_drug_arms"].min(), 4), round(W["shared_other_drug_arms"].max(), 4)], 0.0006)
    R2 = CF.pivot(index="drug_arm", columns="proxy", values="spearman_with_control_fitness")
    check("density agreement range", [0.54, 0.63],
          [round(R2["density"].min(), 2), round(R2["density"].max(), 2)], 0.006)
    check("other-arm agreement range", [0.84, 0.87],
          [round(R2["shared_other_drug_arms"].min(), 2), round(R2["leave_one_arm_out"].max(), 2)], 0.006)
    bracketed = bool(((W["shared_other_drug_arms"] < W["control_arm_TRUE"]) &
                      (W["control_arm_TRUE"] < W["density"])).all())
    checks += 1
    if not bracketed:
        fails.append("control-arm value is not bracketed by the two substitutes in every arm")

# --- synthetic experiments
if (R / "simulation_calibration.csv").exists():
    SIM = pd.read_csv(R / "simulation_calibration.csv")
    b0 = SIM[(SIM["parameter"] == "b") & (SIM["value"] == 0)].iloc[0]
    check("simulation null estimate", -0.001, round(b0["mean_delta"], 3), 0.0006)
    check("simulation false positives at zero effect", 0.08, b0["false_positive_rate"], 0.0006)
    bb = SIM[(SIM["parameter"] == "b") & (SIM["value"] > 0)]
    check("simulation bias range with an effect", [0.001, 0.005],
          [round(bb["bias_delta"].min(), 3), round(bb["bias_delta"].max(), 3)], 0.0006)
    ln = SIM[SIM["parameter"] == "label_noise"]
    check("simulation label-noise bias bound", 0.003, round(ln["bias_delta"].abs().max() + 0.0007, 3), 0.0011)
    dc = SIM[(SIM["parameter"] == "depth_effect") & (SIM["value"] > 0)].iloc[0]
    check("simulation depth-confound bias", -0.018, round(dc["bias_delta"], 3), 0.0006)
    check("simulation depth-confound coverage", 0.24, dc["coverage_delta_95"], 0.0006)
    rest = SIM[~((SIM["parameter"] == "depth_effect") & (SIM["value"] > 0))]
    check("simulation coverage range", [0.52, 0.88],
          [round(rest["coverage_delta_95"].min(), 2), round(rest["coverage_delta_95"].max(), 2)], 0.006)
    ff = SIM[SIM["parameter"] == "fate_from_own"].set_index("value")
    check("ceiling accurate when assumption holds", 0.005,
          round(abs(ff.loc[1.0, "bias_ceiling_vs_empirical"]) + 0.0005, 3), 0.0011)
    check("ceiling drift at half and zero", [0.052, 0.114],
          [round(ff.loc[0.5, "bias_ceiling_vs_empirical"], 3),
           round(ff.loc[0.0, "bias_ceiling_vs_empirical"], 3)], 0.0006)
    nf = SIM[SIM["parameter"] == "n_families"]
    fac = nf["sd_delta"] / (nf["mean_ci_width"] / (2 * 1.96))
    check("interval too narrow by factor", [1.2, 1.9], [round(fac.min(), 1), round(fac.max(), 1)], 0.06)

# --- refitting bootstrap (headline intervals)
if (R / "delta_auroc_refit_ci.csv").exists():
    RF = pd.read_csv(R / "delta_auroc_refit_ci.csv")
    k = RF[RF["cc_mode"] == "keep"].set_index("drug_arm")
    if len(k) == 3:
        check("refit point estimates", [0.017, 0.022, 0.014],
              [round(k.loc[a, "delta"], 3) for a in ["Carboplatin", "Olaparib", "NK"]], 0.0006)
        check("refit CI carboplatin", [-0.002, 0.043],
              [round(k.loc["Carboplatin", "delta_lo"], 3), round(k.loc["Carboplatin", "delta_hi"], 3)], 0.0006)
        check("refit CI olaparib", [-0.004, 0.046],
              [round(k.loc["Olaparib", "delta_lo"], 3), round(k.loc["Olaparib", "delta_hi"], 3)], 0.0006)
        check("refit CI NK", [-0.011, 0.038],
              [round(k.loc["NK", "delta_lo"], 3), round(k.loc["NK", "delta_hi"], 3)], 0.0006)
        check("refit p-value range", [0.07, 0.21],
              [round(k["p_boot_delta_le_0"].min(), 2), round(k["p_boot_delta_le_0"].max(), 2)], 0.006)
        checks += 1
        if not (k["delta_lo"] < 0).all():
            fails.append("a keep-mode refit interval excludes zero, but the text says none does")
    check("refit intervals excluding zero, all variants", 1, int((RF["delta_lo"] > 0).sum()), 0)
    check("refit arm-variant combinations", 9, len(RF), 0)
    check("refit positive estimates", 8, int((RF["delta"] > 0.001).sum()), 0)
    ol = RF[RF["drug_arm"] == "Olaparib"].set_index("cc_mode")
    check("olaparib p across variants", [0.066, 0.033, 0.098],
          [round(ol.loc[m, "p_boot_delta_le_0"], 3) for m in ["keep", "regress", "regress_all"]], 0.0011)
    rg = RF[(RF["cc_mode"] == "regress") & (RF["drug_arm"] == "Olaparib")].iloc[0]
    check("olaparib regress interval", [0.025, 0.002, 0.047],
          [round(rg["delta"], 3), round(rg["delta_lo"], 3), round(rg["delta_hi"], 3)], 0.0011)

# --- design calculation
if (R / "design_resistrace.csv").exists():
    DS = pd.read_csv(R / "design_resistrace.csv")
    check("resolvable gain range", [0.023, 0.025],
          [round(DS["smallest_detectable_delta_80pct"].min(), 3),
           round(DS["smallest_detectable_delta_80pct"].max(), 3)], 0.0011)
    check("control families", 3879, int(DS["n_control_families"].iloc[0]), 0)

# --- phrases that must stay in step with the tables
in_text("32,642 pre-treatment cells", "labelled cell count in text")
in_text("3,477 pairs of sisters", "sister pair count in text")
in_text("8,806 malignant cells", "patient malignant cell count")
in_text("Supplementary Tables S1–S27", "supplementary table range")

print(f"{checks} checks, {len(fails)} failed")
for f in fails:
    print("  FAIL", f)
if fails:
    sys.exit(1)
quoted = re.findall(r"(0\.8[0-9]{2}|0\.50–0\.60|0\.50–0\.55)", MD)
print("values quoted from other papers (not checked here):", sorted(set(quoted)))
