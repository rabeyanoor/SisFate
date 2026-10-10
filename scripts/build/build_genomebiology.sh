#!/usr/bin/env bash
# Build the complete Genome Biology submission in new_paper/genomebiology/ and reading PDFs in new_paper/pdf/.
# Needs node (npm install in scripts/build), uv and LibreOffice (soffice) for the PDFs.
set -euo pipefail
cd "$(dirname "$0")/../.."
G=new_paper/genomebiology
python3 scripts/build/make_genomebiology.py
cp $G/Manuscript.md $G/Manuscript_with_figures.md
(cd scripts/build && GB=1 NOFIG=1 node build_docx.js genomebiology/Manuscript >/dev/null \
  && GB=1 node build_docx.js genomebiology/Manuscript_with_figures >/dev/null \
  && GB=1 node build_docx.js genomebiology/Additional_file_1 >/dev/null)
for n in Manuscript Manuscript_with_figures Additional_file_1; do
  uv run --offline --with pypandoc_binary python scripts/build/docx_math.py genomebiology/$n >/dev/null
done
mkdir -p $G/figures
for f in Fig1_design_data Fig2_predictability Fig3_fitness_confound Fig4_biology Fig5_ceiling \
         Fig6_schaff_multitreatment Fig7_external_clinical; do cp results/figures/paper/$f.pdf $G/figures/; done
cp new_paper/Supplementary_Tables.xlsx $G/Additional_file_2.xlsx
rm -f $G/*.math.json
if command -v soffice >/dev/null; then
  (cd $G && rm -f *.pdf && soffice --headless --convert-to pdf Manuscript_with_figures.docx Additional_file_1.docx >/dev/null 2>&1)
  mkdir -p new_paper/pdf
  cp $G/Manuscript_with_figures.pdf new_paper/pdf/SisFate_GenomeBiology_paper.pdf
  cp $G/Additional_file_1.pdf new_paper/pdf/SisFate_GenomeBiology_Additional_file_1.pdf
fi
echo "Genome Biology submission built in $G"
