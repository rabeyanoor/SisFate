# PERSIST: lineage-supervised prediction of pre-existing drug-tolerant states

Can a cell's **pre-treatment** transcriptome predict whether its **sister** survives treatment?
Data: ReSisTrace (Dai et al., *Nat Commun* 15:1158, 2024; GEO **GSE223003**), Kuramochi HGSOC cells, arms
Carboplatin / Olaparib / NK / **Control**, two replicates each.

## Setup and running
```bash
uv sync --python 3.12          # CPU torch; no GPU needed, peak RAM ~2.5 GB (exact versions: uv.lock / requirements.lock.txt)
./scripts/run_all.sh           # reproduces every number, figure and supplementary table; or run the numbered scripts one by one
```
All randomness is seeded (`seed: 0` in `configs/default.yaml`, plus explicit `--seeds`); each row of `results/results.csv`
records the hash of the configuration that produced it. Tested with Python 3.12.14, NumPy 2.5.3, scikit-learn 1.9.1,
Scanpy 1.12.4 and PyTorch 2.14 (CPU) on Linux.
| script | step |
|---|---|
| `00_download.sh`, `00b_download_external.sh` | GEO downloads (ReSisTrace; Watermelon GSE150949; TNBC GSE228382 + figshare) |
| `export_seurat.R` | TNBC Seurat object -> plain files (R from `tools/renv`, installed with micromamba) |
| `01_build_anndata.py` | dense GEO TSVs -> sparse per-sample `.h5ad` (streamed) |
| `02_preprocess.py` | gene-union alignment, normalise, cell-cycle scores, HVGs, per-sample scaling, PCA (`keep` and `regress` cell-cycle modes) |
| `03_label_audit.py` | label counts vs paper, lineage families, phase/depth vs label |
| `04_baselines.py` | covariate-only, logistic (PCA/HVG), kNN-smoothed logistic, CatBoost |
| `05_gnn.py` | PERSIST-GNN and ablations (MLP, +pretraining, +graph) |
| `06_fitness_confound.py` | drug-specific vs generic-fitness signal (Control arm) |
| `07_ceiling.py` | sister-discordance ceiling and per-model decomposition |
| `08_interpret.py` | replicate-consistent DE, drug-specific vs fitness-shared genes, signatures |
| `09_tcga_ov.py` | signature vs OS/PFI in TCGA-OV (Cox) |
| `10_external_validation.py` | Watermelon + TNBC: lineage-grouped CV and zero-shot transfer |
| `11_summarize.py` | `results/summary_<cc>.md`, `results/figures/` |
| `12_cnv_subclones.py` | infercnvpy copy-number clusters; published subclone enrichment check; subclone confound tests |
| `13_robustness.py` | singleton-only cells, exact family-level permutation p-values, Shen et al. benchmark protocol |
| `14_figures.py` | publication figures `results/figures/paper/Fig1-6`, `FigS*` (PNG + PDF, 300 dpi) and PLOS submission TIFFs in `plos/` (450 dpi, LZW, ≤ 7.5 in wide) |
| `15_typicality.py` | label-free local-density score vs labels |
| `16_supplementary_tables.py` | `paper/supplementary/Supplementary_Tables.xlsx` (S1–S20); run with `uv run --with openpyxl` |
| `17_sensitivity.py` | main and fitness analyses on Harmony, Pearson-residual and scVI representations; `uv run --with harmonypy --with scvi-tools` |
| `18_marker_panel.py` | pre-specified proliferation/arrest/senescence/persister marker panel (Fig. S3) |
| `19_gnn_sweep.py` | one-at-a-time GNN hyperparameter sweep -> `results/gnn_sweep.csv` |
| `20_delta_auroc_ci.py` | size-matched drug-specific gain (ΔAUROC) over the fitness model, 10 subsamples, paired family bootstrap CI -> `results/delta_auroc_ci.csv` |
| `21_geneformer.py` | Geneformer V2-104M_CLcancer embeddings: `tokens` (CPU) -> `embed` (GPU; `kaggle/geneformer/`) -> `analyze` |
| `run_rest.sh` | lean version of the heavy runs actually used for the paper |
| `paper/build/build_docx.js` | `paper/manuscript.md` -> `paper/manuscript.docx` with embedded figures |

Literature: `paper/lit/` holds metadata, abstracts and (24 of 27) full texts; five further full texts (Schaff 2026, Iyer 2025, Oliveira 2025, Kronheim 2026, Soragni 2025) and Shen et al. v2 are PDFs in `read_paper_for_sitation/` fetched by `paper/lit/fetch_lit.py`; claims cited in the manuscript were checked against them.

Every metric row is appended to `results/results.csv` with the config hash; test-set predictions are saved in `results/preds/`.

## Key design decisions
* **Labels** come from the authors' `cell_info` (`drugSens`): counts match the paper exactly (29,540 / 3,102). `NA` cells (no lineage label) are excluded, not treated as negatives. `pre-sensitive` includes *partial* lineage matches, which is one source of label noise.
* **Lineage groups** are the union of `sisters` and `prer_r_group` families; every split keeps a family on one side. There are 0 discordant families.
* **Splits:** within-arm StratifiedGroupKFold, replicate hold-out, all 12 cross-arm transfers.
* **Shuffled control:** training labels are permuted *at family level within sample*, so the dependence structure is preserved.
* **Label-free steps are transductive:** HVGs, PCA and the kNN graph see all pre-treatment cells, but never labels. The graph has no cross-sample edges.
* **Fitness confound:** a Control-trained model (sister survived with *no* drug) scores drug-arm cells. We report the drug model's AUROC, the fitness model's AUROC, the residual AUROC, AUROC within fitness quintiles, and an LRT.
* **Ceiling:** 3,477 pre-treatment sister pairs estimate how shared state is between sisters (ICC). A Gaussian-liability model converts each model's AUROC and score-ICC into "AUROC if the treated sister itself were observed" (the sister cost), with a label-noise correction (π = fraction of negatives that are true positives).
* **Subclones:** InferCNV subclone calls are not on GEO, so `12_cnv_subclones.py` infers copy-number profiles with infercnvpy and clusters them (k chosen by silhouette); `within_cluster_auroc` in the model tables is a separate check inside 8 k-means expression-state clusters.

## Findings
See `paper/manuscript.md` (or `.docx`) for the full write-up; every number there comes from `results/`.

## Licence
MIT (see `LICENSE`). Cite via `CITATION.cff`.
# SisFate
