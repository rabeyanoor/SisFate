# PERSIST: lineage-supervised prediction of pre-existing drug-tolerant states

[![tests](https://github.com/rabeyanoor/SisFate/actions/workflows/tests.yml/badge.svg)](https://github.com/rabeyanoor/SisFate/actions/workflows/tests.yml)

Code for: Noor R, Roza KJ. *Growth fitness, not drug tolerance, explains most pre-treatment prediction of cancer
cell fate* (submitted). The reusable evaluation is `persist.fitadj` (see `tests/test_fitadj.py` for usage).

Can a cell's **pre-treatment** transcriptome predict whether its **sister** survives treatment?
Data: ReSisTrace (Dai et al., *Nat Commun* 15:1158, 2024; GEO **GSE223003**), Kuramochi HGSOC cells, arms
Carboplatin / Olaparib / NK / **Control**, two replicates each.

## How to reproduce

You need Linux or macOS, [uv](https://docs.astral.sh/uv/) and about 10 GB of free disk. Everything runs on a CPU.

**1. Install (about 2 minutes).** The exact package versions are locked in `uv.lock` (also exported as `requirements.lock.txt`).
```bash
git clone https://github.com/rabeyanoor/SisFate.git && cd SisFate
uv sync --frozen --python 3.12
```

**2. Check the code (about 2 minutes, no data needed).** Runs the unit tests of the package, including the
synthetic checks of the estimators.
```bash
uv run --with pytest pytest -q
```

**3. Check the paper against the saved results (seconds).** `results/` is part of the repository, so every number
quoted in the paper can be checked without rerunning anything.
```bash
uv run python scripts/23_audit_paper.py      # over 150 checks; names any number that does not match results/
```

**4. Rerun everything from the public data (about a day on an 8-core laptop with 14 GB RAM).** Downloads the
data from GEO and figshare and regenerates every result, figure and supplementary table; approximate times are
given per step inside the script. The Geneformer and scGPT forward passes ran on a free Kaggle T4 GPU
(`kaggle/`); the script says where to put their output, or how to run them on a CPU instead.
```bash
./scripts/run_all.sh
```

All randomness is seeded (`seed: 0` in `configs/default.yaml`, plus explicit `--seeds`); each row of `results/results.csv`
records the hash of the configuration that produced it. Tested with Python 3.12.14, NumPy 2.5.3, scikit-learn 1.9.1,
Scanpy 1.12.4 and PyTorch 2.14 (CPU) on Linux.

## Repository layout

```
configs/default.yaml   every setting and the random seed
src/persist/           the Python package: data loading, labels, splits, models, metrics, fitness-adjusted
                       evaluation (fitadj.py), sister ceiling, simulation, design calculator
scripts/               the analysis, one numbered script per step (00-35), run in order by run_all.sh
scripts/build/         turns paper/paper.md into Word, LaTeX and the journal submission
kaggle/                GPU kernels for the Geneformer and scGPT embeddings (run on a free Kaggle T4)
tests/                 unit tests of the package (pytest)
data/                  downloaded data, not in git; see data/README.md for every data set and its source
results/               every result table (CSV) and the paper figures (results/figures/paper/)
paper/                 the paper text (paper.md) and Supplementary Tables S1-S30
```

## Scripts

| script | step |
|---|---|
| `00_download.sh`, `00b_download_external.sh`, `00c_download_schaff.sh` | GEO downloads (ReSisTrace; Watermelon GSE150949; TNBC GSE228382 + figshare; Schaff GSE279162) |
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
| `14_figures.py` | publication figures `results/figures/paper/Fig1-7`, `FigS1-5` (PNG + PDF, 300 dpi) and PLOS submission TIFFs in `plos/` (450 dpi, LZW, ≤ 7.5 in wide) |
| `15_typicality.py` | label-free local-density score vs labels |
| `16_supplementary_tables.py` | `paper/Supplementary_Tables.xlsx` (S1–S30); run with `uv run --with openpyxl` |
| `17_sensitivity.py` | main and fitness analyses on Harmony, Pearson-residual and scVI representations; `uv run --with harmonypy --with scvi-tools` |
| `18_marker_panel.py` | pre-specified proliferation/arrest/senescence/persister marker panel (Fig. S3) |
| `19_gnn_sweep.py` | one-at-a-time GNN hyperparameter sweep -> `results/gnn_sweep.csv` |
| `20_delta_auroc_ci.py` | size-matched drug-specific gain (ΔAUROC) over the fitness model, 10 subsamples, paired family bootstrap CI -> `results/delta_auroc_ci.csv` |
| `21_geneformer.py` | Geneformer V2-104M_CLcancer embeddings: `tokens` (CPU) -> `embed` (GPU; `kaggle/geneformer/`) -> `analyze` |
| `22_patient_nact.py` | ReSisTrace signatures in 11 HGSOC patients before/after neoadjuvant chemotherapy (GSE165897) -> `results/patient_nact.csv` |
| `23_audit_paper.py` | re-checks every number quoted in `paper/paper.md` against `results/` (156 checks) |
| `24_schaff_multitreatment.py` | second lineage system: six treatments in parallel (Schaff et al. 2026, GSE279162); clone size as the fitness proxy, cross-treatment transfer, clone ceiling |
| `25_simulation.py` | synthetic lineage experiments with a known answer: bias and interval coverage of the drug-specific gain, and when the sister ceiling is valid |
| `26_design_tool.py` | how many families and control cells a new experiment needs -> `results/design_*.csv` |
| `27_control_free_fitness.py` | substitutes for an untreated arm, checked against the real one -> `results/control_free_fitness.csv` |
| `28_delta_refit_bootstrap.py` | slower interval for the drug-specific gain that refits the whole procedure inside each bootstrap replicate |
| `29_scgpt.py` | scGPT whole-human embeddings: `export` (CPU) -> embed (GPU; `kaggle/scgpt/`) -> `analyze` |
| `30_model_comparison_chart.py`, `31_summary_charts.py` | plain summary charts in `paper/charts/` (not journal figures) |
| `32_export_data_view.py` | the analysed cells as small readable CSV files in `data_view/` |
| `33_three_level_decomposition.py` | fitness vs general-treatment vs drug-unique signal: untreated-arm, other-drug-arm and own-arm models at equal training size, refitting bootstrap -> `results/three_level_decomposition.csv` |
| `34_drug_unique_genes.py` | genes and Hallmark sets unique to one drug (vs the other drug arms), with pre-specified pathway tests |
| `35_published_claims.py` | the pathway and HRD claims of Dai et al. (2024) re-scored in every arm incl. the untreated control, from their own supplementary data |
| `scripts/build/build_latex.py` | `paper/paper.md` -> LaTeX in `results/latex/` (on demand) |
| `run_rest.sh` | lean version of the heavy runs actually used for the paper |
| `scripts/build/build_docx.js` | `paper/paper.md` + `supplementary_information.md` -> `paper/hi.docx` (the whole paper, figures embedded) |
| `scripts/build/make_genomebiology.py` | Genome Biology submission in `paper/genomebiology/`: Vancouver references, data sets and links cited in the reference list, separate Additional file 1; the whole submission is built by `scripts/build/build_genomebiology.sh` |
| `scripts/build/docx_math.py` | turns the equations in `hi.docx` into native Word equations (run after `build_docx.js`; needs `uv run --with pypandoc_binary`) |

Literature: `reference/lit/` holds metadata, abstracts and (24 of 27) full texts; five further full texts (Schaff 2026, Iyer 2025, Oliveira 2025, Kronheim 2026, Soragni 2025) and Shen et al. v2 are PDFs in `read_paper_for_sitation/` fetched by `reference/lit/fetch_lit.py`; claims cited in the paper were checked against them.

Every metric row is appended to `results/results.csv` with the config hash; test-set predictions are saved in `results/preds/`.

## Using the evaluation on your own data (`persist.fitadj`)

Any lineage-tracing experiment in which pre-treatment cells are labelled by the fate of their relatives, and
one arm receives no drug, can be checked with three calls. Inputs are plain arrays: `X` (cells x features, any
representation), `y` (1 = the relative survived), `families` (lineage of each cell), `arms` (arm of each cell).

```python
from persist.fitadj import fitness_adjusted_report, family_permutation_null, sister_concordance, sister_ceiling

# 1. How much of each drug arm's signal is generic fitness?
rep = fitness_adjusted_report(X, y, families, arms, samples, control="Control")
rep[["arm", "auroc_drug", "auroc_fitness", "delta_size_matched", "delta_lo", "delta_hi"]]

# 2. Is the signal above chance? (labels permuted between whole families within each sample)
family_permutation_null(X[drug], y[drug], families[drug], samples[drug], n_perm=100)

# 3. What is the best one could hope for, given that relatives are not identical?
c = sister_concordance(scores, sister_pairs)          # scores of pre-treatment sister pairs
sister_ceiling(auroc=0.74, concordance=c, prevalence=0.09)
```

`delta_lo`/`delta_hi` are the fast interval that resamples families around models fitted once; our simulations
show it is too narrow, so for the numbers you report use the refitting interval of
`scripts/28_delta_refit_bootstrap.py`. `persist.simulate` generates synthetic experiments with a known answer, and
`persist.design` says how many families an experiment needs to resolve a given gain. Tests: `tests/test_fitadj.py`.

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
See `paper/paper.md` (or `.docx`) for the full write-up; every number there comes from `results/`.

## Licence
MIT (see `LICENSE`). Cite via `CITATION.cff`.
# SisFate
