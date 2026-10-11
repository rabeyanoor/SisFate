# Run logs

The original logs of the analysis runs behind the paper (September–October 2026), kept so that each step can be
traced. Times are local; paths were shortened to be relative to the repository. Steps without a log here printed
only to the terminal; their outputs are in `results/`. Each metric in `results/results.csv` also carries the hash of
the configuration that produced it.

| Log | Script | What it ran |
|---|---|---|
| `baselines_keep.log`, `baselines_regress.log`, `baselines_regress_all.log` | `04_baselines.py` | logistic, covariate-only, gene-level and graph-smoothed models, for the three preprocessing variants |
| `tuned_keep.log`, `tuned_regress.log`, `tuned_regress_all.log` | `04_baselines.py` | logistic regression with tuned regularisation and number of components |
| `catboost_keep.log`, `catboost_pca_keep.log`, `catboost_hvg_keep.log` | `04_baselines.py` | gradient boosting (CatBoost) |
| `gnn_keep_seeds.log`, `gnn_keep_shuffle.log`, `gnn_keep_cross.log`, `gnn_regress_all.log` | `05_gnn.py` | MLP and graph network, three seeds, shuffled labels, cross-arm transfer |
| `gnn_sweep.log` | `19_gnn_sweep.py` | graph-network hyperparameter sweep |
| `fitness_keep.log`, `fitness_regress.log`, `fitness_regress_all.log` | `06_fitness_confound.py` | fitness model against each drug arm |
| `ceiling_keep.log`, `ceiling_regress.log`, `ceiling_regress_all.log` | `07_ceiling.py` | sister ceiling |
| `tcga.log` | `09_tcga_ov.py` | survival analysis in TCGA-OV |
| `summary_keep.log`, `summary_regress.log`, `summary_regress_all.log` | `11_summarize.py` | summary tables |
| `robustness_regress_all.log` | `13_robustness.py` | permutation tests and benchmark protocol |
| `fig_final.log` | `14_figures.py` | figures |
| `tab_final.log` | `16_supplementary_tables.py` | Supplementary Tables S1–S31 |
| `sensitivity.log` | `17_sensitivity.py` | Harmony, Pearson-residual and scVI representations |
| `delta_ci.log` | `20_delta_auroc_ci.py` | size-matched drug-specific gain with the evaluation-only interval |
| `geneformer_tokens.log` | `21_geneformer.py tokens` | Geneformer input tokens |
| `patient_nact.log` | `22_patient_nact.py` | patients before and after chemotherapy |
| `schaff.log`, `schaff_sensitivity.log` | `24_schaff_multitreatment.py` | second lineage system and barcode-threshold sensitivity |
| `simulation.log`, `simulation_depth.log` | `25_simulation.py` | synthetic experiments, including the depth-confound settings |
| `refit200_keep.log`, `refit200_regress.log`, `refit200_regress_all.log` | `28_delta_refit_bootstrap.py` | refitting bootstrap, 200 replicates (the intervals quoted in the paper) |
| `scgpt_kaggle.log` | `kaggle/scgpt/kernel/scgpt_embed.py` | scGPT forward pass on a Kaggle T4 GPU |
| `three_level_keep_Carboplatin.log`, `three_level_keep_NK.log`, `three_level_keep_Olaparib.log` | `33_three_level_decomposition.py` | fitness, general-treatment and drug-unique parts |
| `published_claims.log` | `35_published_claims.py` | the original study's pathway and HRD findings, re-scored |
| `inductive_preprocessing.log` | `36_inductive_preprocessing.py` | preprocessing fitted on training cells only, against the main pipeline |
| `three_level_multitask_abandoned.log`, `three_level_penalty_grid_partial.log` | `33_three_level_decomposition.py` (earlier version) | the multi-task model described in Methods and not used, because its penalties rather than the data set the split |
