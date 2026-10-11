"""Collect result tables into results/Supplementary_Tables.xlsx (one sheet per table).

Run: uv run --with openpyxl python scripts/16_supplementary_tables.py
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
OUT = ROOT / "results"
OUT.mkdir(parents=True, exist_ok=True)


def cat(files, key="cc_mode"):
    frames = []
    for f in files:
        d = pd.read_csv(RES / f)
        if key not in d.columns:
            mode = f.removesuffix(".csv")
            mode = "regress_all" if mode.endswith("regress_all") else mode.rsplit("_", 1)[-1]
            d.insert(0, key, mode)
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def per_arm(pattern, arms):
    frames = []
    for a in arms:
        d = pd.read_csv(RES / "interpret" / pattern.format(a))
        d.insert(0, "arm", a)
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


drugs = ["Carboplatin", "Olaparib", "NK"]

# Olaparib pre-treatment task: published benchmark values (quoted from Shen et al. 2026, v2, Results) next to ours
rob = pd.read_csv(RES / "robustness_keep.csv")
ours = {k: rob[rob["check"] == f"benchmark_protocol_{k}"]["auroc"] for k in ["ungrouped", "grouped"]}
bench = pd.DataFrame([
    {"method": "scDEAL", "source": "Shen et al. 2026", "input": "pre-treatment scRNA-seq",
     "training_signal": "bulk cell-line drug response (GDSC/CCLE) transferred to single cells",
     "label_evaluated": "sister-derived pre-resistant / pre-sensitive (olaparib)",
     "protocol": "balanced subsets, 3 draws, 5-fold CV", "auroc": "~0.6 (reported as approximately 0.6)"},
    {"method": "Other benchmarked methods (most of Beyondcell, CaDRReS-Sc, DREEP, DrugFormer, Precily, SCAD, scDr, scIDUC)",
     "source": "Shen et al. 2026", "input": "pre-treatment scRNA-seq",
     "training_signal": "bulk drug-response data or drug signatures, depending on the method",
     "label_evaluated": "sister-derived pre-resistant / pre-sensitive (olaparib)",
     "protocol": "balanced subsets, 3 draws, 5-fold CV where training is needed", "auroc": "0.50-0.55 (most methods)"},
    {"method": "scDEAL (different task, for context)", "source": "Shen et al. 2026",
     "input": "pre-treatment cells vs post-treatment survivors",
     "training_signal": "bulk cell-line drug response", "label_evaluated": "treatment time point (pre = sensitive, post = resistant)",
     "protocol": "balanced subsets, 3 draws", "auroc": "0.869 (mean)"},
    {"method": "PCA-logistic (this study)", "source": "this study", "input": "pre-treatment scRNA-seq, 50 PCs",
     "training_signal": "sister-derived lineage labels of the same arm",
     "label_evaluated": "sister-derived pre-resistant / pre-sensitive (olaparib)",
     "protocol": "balanced (all pre-resistant + equal random pre-sensitive), 3 draws, plain 5-fold CV",
     "auroc": f"{ours['ungrouped'].min():.3f}-{ours['ungrouped'].max():.3f}"},
    {"method": "PCA-logistic (this study)", "source": "this study", "input": "pre-treatment scRNA-seq, 50 PCs",
     "training_signal": "sister-derived lineage labels of the same arm",
     "label_evaluated": "sister-derived pre-resistant / pre-sensitive (olaparib)",
     "protocol": "as above, lineage-grouped 5-fold CV", "auroc": f"{ours['grouped'].min():.3f}-{ours['grouped'].max():.3f}"},
])
sig = json.load(open(RES / "interpret" / "signatures.json"))
sig_rows = [
    {"signature": k, "direction": d, "genes": ", ".join(v[d])}
    for k, v in sig.items() for d in v
]

tables = {
    "S1_model_performance": (
        cat(["summary_table_keep.csv", "summary_table_regress.csv", "summary_table_regress_all.csv"]),
        "Out-of-fold AUROC/AUPRC for all models, splits (within-arm, replicate hold-out, cross-arm) and "
        "preprocessing variants (keep, regress = cell cycle removed, regress_all = cell cycle, depth and "
        "mitochondrial fraction removed). lo/hi: 95% family-bootstrap CI; auroc_shuf: family-level shuffled-label control.",
    ),
    "S2_robustness": (
        cat(["robustness_keep.csv", "robustness_regress_all.csv"]),
        "Singleton-only cells, exact permutation test (100 refits) and the Shen et al. (2026) benchmark protocol.",
    ),
    "S3_fitness_confound": (
        pd.read_csv(RES / "fitness_confound.csv"),
        "Drug-arm model versus control-arm (fitness) model for each drug arm and preprocessing variant.",
    ),
    "S4_typicality": (
        pd.read_csv(RES / "typicality.csv"),
        "Label-free local-density score (negative mean distance to 15 nearest neighbours within sample).",
    ),
    "S5_ceiling": (
        cat(["ceiling_decomposition_keep.csv", "ceiling_decomposition_regress.csv",
             "ceiling_decomposition_regress_all.csv"]),
        "Sister-discordance decomposition per model; pi = assumed fraction of observed negatives that are true positives.",
    ),
    "S6_sister_pc_icc": (
        cat(["ceiling_pc_icc_keep.csv", "ceiling_pc_icc_regress.csv", "ceiling_pc_icc_regress_all.csv"]),
        "Intraclass correlation of principal components between pre-treatment sisters and random same-sample pairs.",
    ),
    "S7_DE_all_arms": (
        per_arm("de_{}.csv", drugs + ["Control"]),
        "Pre-resistant versus pre-sensitive Wilcoxon tests within sample, replicates combined by Stouffer's method.",
    ),
    "S8_DE_drug_vs_fitness": (
        per_arm("drug_vs_fitness_{}.csv", drugs),
        "Drug contrast versus control contrast; z_diff = (z_drug - z_control)/sqrt(2); class as defined in Methods.",
    ),
    "S9_GSEA_hallmark": (
        pd.concat(
            [per_arm("gsea_hallmark_specific_{}.csv", drugs).assign(contrast="drug_specific"),
             per_arm("gsea_hallmark_all_{}.csv", drugs).assign(contrast="drug_all"),
             per_arm("gsea_hallmark_fitness_{}.csv", ["Control"]).assign(contrast="fitness")],
            ignore_index=True,
        ),
        "Preranked GSEA on MSigDB Hallmark gene sets (1,000 permutations).",
    ),
    "S10_signatures": (
        pd.DataFrame(sig_rows),
        "Signature gene lists used for TCGA-OV scoring (top 50 per direction, mitochondrial and ribosomal genes removed).",
    ),
    "S11_CNV_enrichment": (
        pd.read_csv(RES / "cnv" / "cnv_enrichment.csv"),
        "Inferred copy-number cluster enrichment among pre-resistant cells (Fisher's exact test, BH-corrected).",
    ),
    "S12_CNV_confound": (
        pd.read_csv(RES / "cnv" / "cnv_confound.csv"),
        "Cluster identity versus expression: AUROCs and likelihood-ratio test for expression beyond cluster.",
    ),
    "S13_external": (
        pd.read_csv(RES / "external_validation.csv"),
        "Watermelon (GSE150949) and TNBC afatinib (GSE228382) lineage-grouped CV and zero-shot ReSisTrace transfer.",
    ),
    "S14_TCGA_OV_Cox": (
        pd.read_csv(RES / "tcga_ov_cox.csv"),
        "Cox models per s.d. of signature score in 303 TCGA-OV primary tumours.",
    ),
    "S15_label_audit": (
        pd.read_csv(RES / "label_audit.csv"),
        "Label counts per sample compared with Dai et al. (2024).",
    ),
    "S16_marker_panel": (
        pd.read_csv(RES / "interpret" / "marker_panel.csv"),
        "Pre-specified marker panel (Fig. S3): drug contrast, control contrast and their difference.",
    ),
    "S17_representations": (
        reps := pd.read_csv(RES / "sensitivity_representations.csv"),
        "Main and fitness analyses repeated on alternative representations of the same cells: "
        + ", ".join(sorted(reps["representation"].unique())) + ".",
    ),
    "S18_GNN_sweep": (
        pd.read_csv(RES / "gnn_sweep.csv"),
        "One-at-a-time hyperparameter sweep of the graph network (within-arm pooled out-of-fold AUROC, seed 0).",
    ),
    "S19_delta_auroc_ci": (
        pd.read_csv(RES / "delta_auroc_ci.csv"),
        "Size-matched drug-specific gain over the fitness model (ΔAUROC), mean over 10 training subsamples, with "
        "95% CI from 1,000 paired family-level bootstrap resamples and a one-sided bootstrap p-value (Δ <= 0).",
    ),
    "S20_benchmark_comparison": (
        bench,
        "Olaparib pre-treatment task: methods benchmarked by Shen et al. (2026) and the logistic model of this study. "
        "Published values are quoted from Shen et al.; those methods were not rerun here.",
    ),
    "S21_patient_nact": (
        pd.read_csv(RES / "patient_nact.csv").merge(
            pd.read_csv(RES / "patient_nact_per_patient.csv"), on="signature", suffixes=("", "_patient")),
        "ReSisTrace signature scores in malignant cells of 11 HGSOC patients before and after neoadjuvant "
        "chemotherapy (Zhang et al. 2022, GSE165897): per-patient change, Wilcoxon test over patients, comparison "
        "with 200 expression-matched random gene sets, same-anatomical-site subset, and platinum-free interval.",
    ),
}


# Tables that only exist once the corresponding analysis has been run
_optional = {
    "S22_schaff_prediction": (
        ["schaff_predict.csv", "schaff_clone_size_adjusted.csv"],
        "Second lineage system (Schaff et al. 2026, GSE279162): lineage-grouped AUROC for clone size, "
        "expression, both and the label-free density score in six treatments, and whether expression adds "
        "over clone size (residual AUROC and likelihood-ratio test). Rows tagged with the barcode-assignment "
        "thresholds; untagged rows are the default (merge 0.55, 2 UMIs, 50%).",
    ),
    "S23_schaff_transfer_ceiling": (
        ["schaff_transfer.csv", "schaff_ceiling.csv"],
        "Cross-treatment transfer of out-of-fold scores, and the clone-concordance ceiling. `saturated` marks "
        "treatments where the implied correlation exceeded one, so no ceiling can be estimated.",
    ),
    "S24_simulation_calibration": (
        ["simulation_calibration.csv"],
        "Synthetic experiments with a known answer: bias of the drug-specific gain, coverage of its 95% "
        "interval, and bias of the sister ceiling, across effect size, label noise, experiment size, sister "
        "similarity, a depth confound, and whether fate is driven by the cell's own state or the shared one.",
    ),
    "S25_design": (
        ["design_plan.csv", "design_arm_split.csv", "design_resistrace.csv"],
        "Experiment planning: families per arm needed for a given drug-specific gain and label prevalence, "
        "how the two arms trade off, and what the published ReSisTrace design can resolve.",
    ),
    "S26_control_free_fitness": (
        ["control_free_fitness.csv"],
        "Substitutes for an untreated arm in ReSisTrace: the drug-specific gain measured against the real "
        "control-arm model and against two baselines that use no control-arm labels (other drug arms, and the "
        "label-free density score), with their agreement with the control score.",
    ),
    "S27_delta_refit_bootstrap": (
        ["delta_auroc_refit_ci.csv"],
        "Drug-specific gain with an interval from refitting the whole procedure inside each bootstrap "
        "replicate: percentile and basic (pivotal) limits, the spread of the replicates, and the one-sided "
        "bootstrap p-value. This is the interval quoted in the text.",
    ),
    "S28_three_level": (
        ["three_level_decomposition.csv"],
        "Fitness, general-treatment and drug-unique parts of each drug arm's signal: AUROC of models trained on "
        "the untreated arm, on the other drug arms and on the arm itself, all at the control arm's training "
        "size, with refitting family-bootstrap (basic) 95% intervals for the two gains.",
    ),
    "S29_drug_unique_genes": (
        ["drug_unique_summary.csv", "drug_unique_prespecified.csv"],
        "Genes and Hallmark gene sets unique to one drug (drug-arm z-score minus the mean of the other two drug "
        "arms), and the four pre-specified pathway tests.",
    ),
    "S30_published_claims": (
        ["published_claims.csv"],
        "The pathway and HRD claims of Dai et al. (2024) re-scored in every arm, including the untreated control, "
        "from their published fold changes (Supplementary Data 2 and 4 of that study) and from our z-scores; "
        "preranked GSEA NES and nominal p, and HRD connectivity (NES_up - NES_down) / 2.",
    ),
    "S31_inductive_preprocessing": (
        ["inductive_preprocessing.csv"],
        "AUROC with the label-free preprocessing fitted on all pre-treatment cells (global, main analysis), with "
        "the PCA fitted on training cells only (pca_train), and with gene selection, per-sample scaling and PCA "
        "all fitted on training cells only (inductive); within-arm five-fold cross-validation (same folds) and "
        "the fitness model (control arm -> each drug arm).",
    ),
}
for name, (files, desc) in _optional.items():
    frames = []
    for f in files:
        if (RES / f).exists():
            d = pd.read_csv(RES / f)
            if len(files) > 1:
                d.insert(0, "source", f.removesuffix(".csv"))
            frames.append(d)
    if frames:
        tables[name] = (pd.concat(frames, ignore_index=True), desc)

index = pd.DataFrame(
    [{"sheet": k, "description": v[1], "rows": len(v[0])} for k, v in tables.items()]
)
path = OUT / "Supplementary_Tables.xlsx"
with pd.ExcelWriter(path) as xw:
    index.to_excel(xw, sheet_name="index", index=False)
    for name, (df, _) in tables.items():
        df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")], errors="ignore")
        df.to_excel(xw, sheet_name=name[:31], index=False)
print(path)
print(index.to_string())
