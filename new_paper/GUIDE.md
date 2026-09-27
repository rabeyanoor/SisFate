# Working on this paper

**The paper is `manuscript.md`. That is the only file you edit.**

Everything else in this folder is either built from it or supports it:

| File | What it is |
|---|---|
| `manuscript.md` | **the paper** — the single source of truth |
| `manuscript.docx` | built from it, for Word users and most journal portals |
| `overleaf_project.zip` | built from it, for Overleaf |
| `supplementary/Supplementary_Tables.xlsx` | 27 result tables, built by `scripts/16_supplementary_tables.py` |
| `GUIDE.md` | this file |
| `drafts/`, `lit/`, `sources/`, `build/`, `latex/` | old versions, literature, and build machinery — ignore them |

## The loop for every change

```bash
nano new_paper/manuscript.md                  # 1. edit
python scripts/23_audit_manuscript.py     # 2. verify: 112 checks, names any number that drifted
python scripts/build/build_latex.py         # 3. rebuild Overleaf version
node scripts/build/build_docx.js            # 3. rebuild Word version
```

Step 2 is the point of the whole setup. If you change a number by hand and it no longer matches `results/`,
the audit fails and tells you which one. If you reran an analysis and the number legitimately moved, update
the check too.

## What only you can write

| Where | What goes there |
|---|---|
| above `## Abstract` | author names, affiliation, corresponding email, ORCIDs — there is no author block yet |
| `**Author contributions.**` | who did what |
| `**Funding.**` | grant numbers, or "received no specific grant" |
| `[REPOSITORY URL]`, `[ZENODO DOI]` | after the code is public |

To make the code public: `git push -u origin main` with a token that has the `repo` scope, then connect the
repository on zenodo.org and cut a release there to mint the DOI.

## Overleaf

Upload `overleaf_project.zip`: **New Project → Upload Project → compile `main.tex` with pdfLaTeX**. Line
numbers are on for review; delete `\linenumbers` for a clean copy.

`main.tex` is generated, so the next `build_latex.py` overwrites it. Either keep editing the markdown and
re-upload, or switch to Overleaf entirely and stop regenerating.

## Figures

Cited in order 1, 2, 3, S1, 4, S2, 5, S3, 6, 7, 8, 9. In the built versions each sits under its legend,
which is what journals want at submission. Files are in `results/figures/paper/`: `.pdf` for LaTeX, `.png`
for Word, `plos/*.tif` (450 dpi) for final submission. Panels are drawn at final size in Arial 5.6–8.5 pt —
do not rescale; change `figsize` in `scripts/14_figures.py` and rebuild instead.

| Fig | File | Goes with the section |
|---|---|---|
| 1 | `Fig1_design_data` | The pre-treatment state predicts a sister's fate |
| 2 | `Fig2_predictability` | same section, model comparison |
| 3 | `Fig3_fitness_confound` | Most of the signal is shared with the untreated control |
| S1 | `FigS1_typicality` | A label-free measure of typicality |
| 4 | `Fig4_biology` | What distinguishes the shared and drug-specific components |
| S2 | `FigS2_marker_panel` | same section, marker panel |
| 5 | `Fig5_ceiling` | Sister discordance caps predictability |
| S3 | `FigS3_gnn_ablation` | A graph model adds nothing over a linear model |
| 6 | `Fig6_external_clinical` | Little transfer to other systems |
| 7 | `Fig7_schaff_multitreatment` | A second lineage system, six treatments |
| 8 | `Fig8_control_free` | Without an untreated arm |
| 9 | `Fig9_simulation` | The estimators, checked against a known answer |

## Before submitting

- Read it end to end, out loud. You defend every sentence in review.
- Write a cover letter: what the paper shows, why it fits that journal, and the AI-use statement ICMJE asks
  for at submission.
- Check the journal's limits. About 13,400 words suits PLOS Computational Biology or Genome Biology;
  Nature-family formats are shorter and need cutting.
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
