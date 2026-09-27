# How to finish and submit this paper

The manuscript is written. `paper/manuscript.md` is the only file you edit; the Word and LaTeX versions are
built from it, so they can never disagree.

## The loop you will use for every change

```bash
# 1. edit
nano paper/manuscript.md            # or any editor

# 2. check that every number still matches the analyses
python scripts/23_audit_manuscript.py     # 112 checks; it fails and names the value if one drifts

# 3. rebuild the two output formats
python paper/build/build_latex.py         # -> paper/latex/  (Overleaf)
node paper/build/build_docx.js            # -> paper/manuscript.docx
```

Step 2 is the important one. If you change a number by hand and it no longer matches `results/`, the audit
stops you. If you legitimately reran an analysis and the number moved, update both the results and the check.

## What only you can write

Four placeholders, all near line 310 of `paper/manuscript.md`:

| Placeholder | What goes there |
|---|---|
| Author list and affiliations | Names, your lab and institution, corresponding author email, ORCIDs |
| `**Author contributions.**` | Who did what, e.g. "R.N. designed the study, wrote the analysis code and the manuscript." |
| `**Funding.**` | Grant numbers, or "This research received no specific grant." |
| `[REPOSITORY URL]` and `[ZENODO DOI]` | Fill in after the code is public (see below) |

The title page has no author block yet because I did not want to guess names. Add it above `## Abstract`.

## Making the code public

```bash
# with a GitHub token that has the `repo` scope
git push -u origin main
```

Then link the repository to Zenodo (zenodo.org → GitHub → enable the repo → cut a release on GitHub). Zenodo
mints a DOI; paste it into `[ZENODO DOI]`.

## Overleaf

`paper/overleaf_project.zip` is ready. On Overleaf: **New Project → Upload Project → choose the zip →
compile `main.tex` with pdfLaTeX**. Line numbers are on for review; delete `\linenumbers` for a clean copy.

If you edit on Overleaf instead of locally, remember that `main.tex` is generated: the next
`build_latex.py` overwrites it. Either stop regenerating, or port edits back into `manuscript.md`.

## Figures

`paper/FIGURES.md` says where each one goes and which file format to use. Journals usually want figures as
separate files at submission: use `results/figures/paper/plos/*.tif`.

## Before you submit

- Read the paper end to end once, out loud if you can. You are the author; every sentence has to be one you
  can defend in review.
- Write a cover letter: one paragraph on what the paper shows, one on why it fits that journal, and the
  AI-use statement that ICMJE asks for at submission.
- Check the target journal's own limits (word count, figure count, reference style). The manuscript is about
  13,400 words, which suits PLOS Computational Biology or Genome Biology; Nature-family formats are shorter
  and would need cutting.
- Consider posting to bioRxiv first. An independent preregistered reanalysis of one of our datasets appeared
  on 20 September 2026 (Aviv, Zenodo 22850050), so priority matters.

## The five things a reviewer will ask

Know these cold; each is a sentence in the paper with a number behind it.

1. **Is the signal real?** Yes: AUROC 0.72–0.75 with lineage-grouped folds, and no permuted-label refit ever
   reached it (p < 0.01, the smallest value 100 permutations allow).
2. **Is it drug-specific?** Mostly not. A model trained only on the untreated arm reaches 0.70–0.73 on the
   drug arms. The size-matched gain is about 0.02, and only 1 of 9 arm-by-variant intervals excludes zero.
3. **Why not significant, if the gain is consistent?** Because the experiment cannot resolve an effect that
   small: the design calculation puts its limit at 0.023–0.025, and every estimate falls below it.
4. **Could this be a technical artefact?** Depth, cell cycle, mitochondrial fraction and inferred copy-number
   clusters were each removed or tested; the picture holds, and the simulation shows a depth confound would
   bias the gain *down*, not up.
5. **Does it generalise?** Same ordering in a second lineage system with six treatments, and the fitness
   signature is depleted, not enriched, in patients after chemotherapy.
