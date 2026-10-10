#!/usr/bin/env bash
# Build the complete Genome Biology submission in paper/genomebiology/ and reading PDFs in paper/pdf/.
# Needs node (npm install in scripts/build), uv and LibreOffice (soffice) for the PDFs.
set -euo pipefail
cd "$(dirname "$0")/../.."
G=paper/genomebiology
python3 scripts/build/make_genomebiology.py
cp $G/Main_text.md $G/Main_text_with_figures.md
(cd scripts/build && GB=1 NOFIG=1 node build_docx.js genomebiology/Main_text >/dev/null \
  && GB=1 node build_docx.js genomebiology/Main_text_with_figures >/dev/null \
  && GB=1 node build_docx.js genomebiology/Additional_file_1 >/dev/null)
for n in Main_text Main_text_with_figures Additional_file_1; do
  uv run --offline --with pypandoc_binary python scripts/build/docx_math.py genomebiology/$n >/dev/null
done
mkdir -p $G/figures
for f in Fig1_design_data Fig2_predictability Fig3_fitness_confound Fig4_biology Fig5_ceiling \
         Fig6_schaff_multitreatment Fig7_external_clinical; do cp results/figures/paper/$f.pdf $G/figures/; done
cp paper/Supplementary_Tables.xlsx $G/Additional_file_2.xlsx
(cd scripts/build && node build_docx.js cover_letter >/dev/null)
cp paper/cover_letter.docx $G/Cover_letter.docx
rm -f $G/*.math.json
if command -v soffice >/dev/null; then
  (cd $G && rm -f *.pdf && soffice --headless --convert-to pdf Main_text_with_figures.docx Additional_file_1.docx Cover_letter.docx >/dev/null 2>&1)
  mkdir -p paper/pdf
  cp $G/Main_text_with_figures.pdf paper/pdf/SisFate_GenomeBiology_paper.pdf
  cp $G/Additional_file_1.pdf paper/pdf/SisFate_GenomeBiology_Additional_file_1.pdf
  cp $G/Cover_letter.pdf paper/pdf/CoverLetter_GenomeBiology.pdf
fi
echo "Genome Biology submission built in $G"
