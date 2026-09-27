# Where each figure goes

Figures are cited in order (1, 2, 3, S1, 4, S2, 5, S3, 6, 7, 8, 9). In the LaTeX build each one is placed
immediately after its legend in the *Figure legends* section, which is what most journals want at submission.
For a typeset version, place each figure at the first mention of it listed below.

Source files live in `results/figures/paper/`: `.pdf` (vector, use for LaTeX), `.png` (for Word), and
`plos/*.tif` (450 dpi LZW, sized to PLOS limits, for final submission).

| Figure | File | Place at | What it shows |
|---|---|---|---|
| 1 | `Fig1_design_data` | Results, *The pre-treatment state predicts a sister's fate* | Design schematic, label prevalence per sample, sequencing depth by class |
| 2 | `Fig2_predictability` | Same section, after the model comparison | Within-arm AUROC per model, replicate hold-out, the published benchmark protocol |
| 3 | `Fig3_fitness_confound` | *Most of the signal is shared with the untreated control* | Cross-arm transfer matrix, drug vs fitness vs residual, size-matched gain with intervals |
| S1 | `FigS1_typicality` | *A label-free measure of typicality* | Density score against the supervised and control-arm models |
| 4 | `Fig4_biology` | *What distinguishes the shared and drug-specific components* | Hallmark enrichment; copy-number cluster odds ratios |
| S2 | `FigS2_marker_panel` | Same section, at the marker-panel paragraph | Pre-specified 28-gene panel, control contrast and beyond-control |
| 5 | `Fig5_ceiling` | *Sister discordance caps predictability* | Sister ICC by component, observed vs treated-sister-seen, cost against label noise |
| S3 | `FigS3_gnn_ablation` | *A graph model adds nothing over a linear model* | Logistic, MLP, pretraining, graph network across seeds |
| 6 | `Fig6_external_clinical` | *Little transfer to other systems* | Watermelon, TNBC, TCGA-OV hazard ratios, and the 11-patient chemotherapy cohort |
| 7 | `Fig7_schaff_multitreatment` | *A second lineage system, six treatments* | Clone size vs expression per treatment, cross-treatment transfer, expression beyond growth |
| 8 | `Fig8_control_free` | *Without an untreated arm* | Drug-specific gain against the real control arm and two substitutes |
| 9 | `Fig9_simulation` | *The estimators, checked against a known answer* | Recovery of a known effect, interval coverage, when the ceiling is an upper bound |

## Sizing

All panels are drawn at final size: 7.2–7.4 in wide for full-width figures (1–9), 3.9–4.6 in for the
supplementary ones. Fonts are Arial at 5.6–8.5 pt, which stays above the 6 pt floor most journals set once
the figure is placed at 100%. Do not rescale; if a journal needs a narrower column, change `figsize` in
`scripts/14_figures.py` and rebuild so the text scales with it.

## Rebuilding

```bash
python scripts/14_figures.py        # all figures, PNG + PDF + PLOS TIFF
python paper/build/build_latex.py   # Overleaf project in paper/latex/
node paper/build/build_docx.js      # Word version with figures embedded
```
