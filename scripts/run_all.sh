#!/usr/bin/env bash
# Full pipeline that reproduces every number, table and figure in the paper (CPU only, 8-core laptop,
# ~14 GB RAM). Approximate wall times are given per step. All randomness is seeded from configs/default.yaml
# (seed: 0) or from explicit --seeds; each metric row in results/results.csv carries the config hash.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
GNN="mlp mlp_pretrain persist_gnn_nopretrain persist_gnn"
mkdir -p logs

# ---- data and preprocessing                                                  ~10 min
./scripts/00_download.sh                                   # 462 MB from GEO
$PY scripts/01_build_anndata.py
$PY scripts/02_preprocess.py --cc-modes keep regress regress_all
$PY scripts/03_label_audit.py

# ---- main models                                                              ~1 h
for cc in keep regress regress_all; do
  $PY scripts/04_baselines.py --cc-mode $cc --models cov_logreg pca_logreg hvg_logreg pca_smooth_logreg
  $PY scripts/04_baselines.py --cc-mode $cc --models pca_logreg_pooled
  $PY scripts/04_baselines.py --cc-mode $cc --models pca_logreg_tuned --n-shuffles 1
  $PY scripts/06_fitness_confound.py --cc-mode $cc
done
$PY scripts/04_baselines.py --cc-mode keep --models pca_catboost --n-shuffles 1                     # ~2 h
$PY scripts/04_baselines.py --cc-mode keep --models hvg_catboost --splits within --n-shuffles 1     # ~1.5 h

# ---- graph network and ablations                                              ~6 h
$PY scripts/05_gnn.py --cc-mode keep --models $GNN --splits within rep_holdout --seeds 0 1 2 --n-shuffles 0
$PY scripts/05_gnn.py --cc-mode keep --models $GNN --splits within --seeds 0 --n-shuffles 1
$PY scripts/05_gnn.py --cc-mode keep --models mlp persist_gnn --splits cross_arm --seeds 0 --n-shuffles 0
$PY scripts/05_gnn.py --cc-mode regress_all --models mlp persist_gnn --splits within --seeds 0 --n-shuffles 0
$PY scripts/19_gnn_sweep.py                                                                          # ~1.5 h

# ---- ceiling, biology, confounders                                            ~1 h
for cc in keep regress regress_all; do $PY scripts/07_ceiling.py --cc-mode $cc; done
$PY scripts/08_interpret.py
$PY scripts/18_marker_panel.py
$PY scripts/12_cnv_subclones.py
for cc in keep regress_all; do $PY scripts/13_robustness.py --cc-mode $cc --n-perm 100; done
$PY scripts/15_typicality.py
$PY scripts/20_delta_auroc_ci.py                                                                     # ~15 min
$PY scripts/25_simulation.py --n-rep 25                                                               # ~4 h
$PY scripts/26_design_tool.py
$PY scripts/27_control_free_fitness.py     # substitutes for an untreated arm (Fig. S4)
for cc in keep regress regress_all; do       # the intervals quoted in the text; ~3 h per mode, run in parallel
  $PY scripts/28_delta_refit_bootstrap.py --cc-modes $cc --n-boot 200 --out delta_auroc_refit_ci_$cc.csv &
done; wait
$PY -c "import pandas as pd; pd.concat(pd.read_csv(f'results/delta_auroc_refit_ci_{m}.csv') for m in ['keep', 'regress', 'regress_all']).to_csv('results/delta_auroc_refit_ci.csv', index=False)"
for cc in keep regress_all; do               # fitness / general treatment / drug-unique; ~2 h per arm, in parallel
  for a in Carboplatin Olaparib NK; do $PY scripts/33_three_level_decomposition.py --cc-modes $cc --arms $a --n-boot 200 & done; wait
done

# ---- alternative representations                                              ~1 h (+ GPU for Geneformer)
uv run --with harmonypy --with scvi-tools python scripts/17_sensitivity.py
uv run --with transformers --with huggingface_hub python scripts/21_geneformer.py tokens
# The Geneformer forward pass ran on a Kaggle T4 GPU (kaggle/geneformer/, ~1 h); on a CPU use
#   uv run --with transformers --with huggingface_hub python scripts/21_geneformer.py embed
# and put emb_V2-104M_CLcancer.npy in data/processed/geneformer/ before:
$PY scripts/21_geneformer.py analyze
$PY scripts/29_scgpt.py export
# The scGPT forward pass ran on a Kaggle T4 GPU (kaggle/scgpt/kernel/scgpt_embed.py, ~7 min on the GPU); put its
# output emb_scgpt_human.npy in data/processed/scgpt/ before:
$PY scripts/29_scgpt.py analyze

# ---- external data and TCGA                                                   ~15 min
./scripts/00b_download_external.sh           # Watermelon, TNBC, and GSE165897 patient data
tools/renv/bin/Rscript scripts/export_seurat.R data/external/scastral/Afa.TS.Seurat.rds data/external/scastral/export
gzip -f data/external/scastral/export/counts.mtx
$PY scripts/10_external_validation.py
$PY scripts/22_patient_nact.py                # patients before/after chemotherapy (GSE165897)
$PY scripts/34_drug_unique_genes.py           # genes unique to one drug (needs 08)
uv run --with openpyxl python scripts/35_published_claims.py   # Dai et al. 2024 claims vs the untreated arm
./scripts/00c_download_schaff.sh              # second lineage system, six treatments
$PY scripts/24_schaff_multitreatment.py
$PY scripts/24_schaff_multitreatment.py --merge-r 0.70 --tag _r70                # barcode threshold sensitivity
$PY scripts/24_schaff_multitreatment.py --merge-r 0.85 --tag _r85
$PY scripts/24_schaff_multitreatment.py --min-umi 3 --min-frac 0.6 --tag _strict
rm -f results/tcga_ov_cox.csv
for sig in specific_Carboplatin specific_Olaparib specific_NK all_Carboplatin fitness_Control; do
  $PY scripts/09_tcga_ov.py --signature $sig
done

# ---- summaries, figures, tables, paper
for cc in keep regress regress_all; do $PY scripts/11_summarize.py --cc-mode $cc; done
$PY scripts/14_figures.py                   # results/figures/paper/*.png|pdf and plos/*.tif
$PY scripts/30_model_comparison_chart.py && $PY scripts/31_summary_charts.py   # plain charts in new_paper/charts/
uv run --with openpyxl python scripts/16_supplementary_tables.py
$PY scripts/23_audit_paper.py           # fails if any quoted number disagrees with results/
(cd scripts/build && npm install --silent && node build_docx.js)
uv run --with pypandoc_binary python scripts/build/docx_math.py   # equations -> native Word equations
