# Working on this paper

**The paper to read and submit is `hi.docx`.** It holds the whole paper in one file: the main text with its
seven figures, then the supplement (Supplementary Notes 1–3 and Supplementary Figs. S1–S5) on a new page.

| File | What it is |
|---|---|
| `hi.docx` | **the paper** — built from the two `.md` files below; do not edit it in Word |
| `paper.md` | source of the main text — the single source of truth, checked by the audit |
| `supplementary_information.md` | source of the supplement |
| `Supplementary_Tables.xlsx` | Tables S1–S30 (Additional file 2), built by `scripts/16_supplementary_tables.py` |
| `figures/` | every figure as a separate file: vector `.pdf` (upload these to the journal) and `.png` (for viewing and slides); 450 dpi TIFFs, if a journal asks, are in `results/figures/paper/plos/`; copies of `results/figures/paper/`, refresh after rerunning `scripts/14_figures.py` |
| `charts/` | summary charts for talks and slides (not in the paper), built by `scripts/30`–`31` |
| `GUIDE.md` | this file |

## The loop for every change

```bash
nano new_paper/paper.md                  # 1. edit (or supplementary_information.md)
python scripts/23_audit_paper.py         # 2. verify: 148 checks, names any number that drifted
node scripts/build/build_docx.js              # 3. rebuild new_paper/hi.docx
uv run --with pypandoc_binary python scripts/build/docx_math.py   #    then make its equations native Word equations
```

Step 2 is the point of the whole setup. If you change a number by hand and it no longer matches `results/`,
the audit fails and tells you which one. If you reran an analysis and the number legitimately moved, update
the check too. An Overleaf/LaTeX version can be built on demand with `python scripts/build/build_latex.py`
(writes `results/latex/main.tex`).

## What only you can write

| Where | What goes there |
|---|---|
| the `[Author names]` block under the title | author names, affiliations, corresponding email, ORCIDs |
| `**Authors' contributions.**`, `**Acknowledgements.**` (under Declarations) | who did what, and thanks |
| `**Funding.**` | grant numbers, or "received no specific grant" |
| `[REPOSITORY URL]`, `[ZENODO DOI]` | after the code is public |

To make the code public: `git push -u origin main` with a token that has the `repo` scope, then connect the
repository on zenodo.org and cut a release there to mint the DOI.

## Structure (Genome Biology research article)

Title and authors → Abstract (Background / Results / Conclusions, 349 words; limit about 350) → Keywords →
Background → Results → Discussion → Conclusions → Methods → Declarations → References → Additional files.

## Figures

Every figure sits directly after the paragraph that first cites it, with its legend underneath, and they are
cited in order: 1, 2, S1, 3, S2, 4, S3, 5, 6, 7, 8, 9. The builders place a figure wherever a paragraph starts
with `**Fig. N |` or `**Supplementary Fig. N |`, so to move a figure, move its legend paragraph. Files are in
`results/figures/paper/`: `.pdf` for LaTeX, `.png` for Word, `plos/*.tif` (450 dpi) for upload at submission,
when journals usually want each figure as a separate file as well. Panels are drawn at final size in Arial
5.6–8.5 pt — do not rescale; change `figsize` in `scripts/14_figures.py` and rebuild instead.

| Fig | File | Results section |
|---|---|---|
| 1 | `Fig1_design_data` | The pre-treatment state predicts a sister's fate |
| 2 | `Fig2_predictability` | same section, model comparison |
| S1 | `FigS1_gnn_ablation` | same section, graph network (Supplementary Note 1) |
| 3 | `Fig3_fitness_confound` | Most of the signal is growth fitness |
| S2 | `FigS2_typicality` | same section, label-free typicality |
| 4 | `Fig4_biology` | What distinguishes the shared and drug-specific components |
| S3 | `FigS3_marker_panel` | same section, marker panel (Supplementary Note 2) |
| 5 | `Fig5_ceiling` | Sister discordance caps predictability |
| 6 | `Fig6_schaff_multitreatment` | Clone size, not state, dominates a second lineage system |
| 7 | `Fig7_external_clinical` | same section, clone-level data sets, TCGA and patients |
| S4 | `FigS4_control_free` | Without an untreated arm |
| S5 | `FigS5_simulation` | The estimators, checked against a known answer |

## Before submitting

- Read it end to end, out loud. You defend every sentence in review.
- Write a cover letter: what the paper shows, why it fits that journal, and the AI-use statement ICMJE asks
  for at submission.
- The format follows Genome Biology. Check its live guidelines once more when you submit; Nature-family
  formats are much shorter and would need cutting.
- Consider bioRxiv first. An independent preregistered reanalysis of one of our datasets appeared on
  20 September 2026 (Aviv, Zenodo 22850050), so priority matters.

## The five questions a reviewer will ask

1. **Is the signal real?** AUROC 0.72–0.75 with lineage-grouped folds; no permuted-label refit reached it
   (p < 0.01, the smallest value 100 permutations allow).
2. **Is it drug-specific?** Mostly not. A model trained only on the untreated arm reaches 0.70–0.73 on the
   drug arms. The size-matched gain is about 0.02, and 1 of 9 arm-by-variant intervals excludes zero.
3. **Then why not significant, if the gain is consistent?** The experiment cannot resolve an effect that
   small: the design calculation puts its limit at 0.023–0.025 and every estimate falls below it.
4. **Could it be a technical artefact?** Depth, cell cycle, mitochondrial fraction and inferred copy-number
   clusters were each removed or tested. A depth confound would bias the gain *down*, not up.
5. **Does it generalise?** Same ordering across six treatments of a second lineage system, and the fitness
   signature is depleted, not enriched, in patients after chemotherapy.
