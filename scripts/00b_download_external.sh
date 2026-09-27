#!/usr/bin/env bash
# External validation data (download only after ReSisTrace baselines show signal).
#   Watermelon: Oren et al. Nature 2021 (PMID 34381210), GEO GSE150949 -- PC9 + osimertinib, clone-level lineage
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/external/watermelon
base=https://ftp.ncbi.nlm.nih.gov/geo/series/GSE150nnn/GSE150949/suppl
for f in GSE150949_metaData_with_lineage.txt.gz GSE150949_pc9_count_matrix.csv.gz \
         GSE150949_pooled_watermelon.metadata.matrix.csv.gz GSE150949_pooled_watermelon.count.matrix.csv.gz; do
  [ -s data/external/watermelon/$f ] || wget -q -O data/external/watermelon/$f "$base/$f"
done
ls -lh data/external/watermelon

#   TNBC afatinib lineage tracing: Pellecchia et al. (PMID 38605363), GEO SuperSeries GSE228382
#   GSE228154 = MDA-MB-468 day 0/3/6/9 afatinib (10x + lineage); GSE228275 = five other TNBC lines
mkdir -p data/external/scastral
for pair in GSE228154:TS_barcodes.tsv.gz GSE228154:TS_features.tsv.gz GSE228154:TS_matrix.mtx.gz \
            GSE228275:scAstral_barcodes.tsv.gz GSE228275:scAstral_features.tsv.gz GSE228275:scAstral_matrix.mtx.gz; do
  gse=${pair%%:*}; f=${gse}_${pair#*:}
  [ -s data/external/scastral/$f ] || wget -q -O data/external/scastral/$f \
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE228nnn/$gse/suppl/$f"
done
ls -lh data/external/scastral

#   HGSOC patients before/after neoadjuvant chemotherapy: Zhang et al. 2022 Sci Adv, GEO GSE165897.
#   Clinical data (platinum-free interval, chemotherapy response score) are typed from that paper's Table 1
#   into data/external/zhang2022/clinical_table1.csv, which is kept in the repository.
mkdir -p data/external/zhang2022
for f in GSE165897_UMIcounts_HGSOC.tsv.gz GSE165897_cellInfo_HGSOC.tsv.gz; do
  [ -s data/external/zhang2022/$f ] || wget -q -O data/external/zhang2022/$f \
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE165nnn/GSE165897/suppl/$f"
done
ls -lh data/external/zhang2022
