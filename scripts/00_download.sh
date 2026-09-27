#!/usr/bin/env bash
# Download the ReSisTrace GEO archive (GSE223003_RAW.tar, 462 MB; 16 samples x {UMIcounts, cell_info}).
# The separate GSE223003_drug_perturbed_* files are a different experiment (no lineage labels) and are not needed.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/raw
TAR=data/GSE223003_RAW.tar
if [ ! -s "$TAR" ]; then
  wget -O "$TAR" "https://www.ncbi.nlm.nih.gov/geo/download/?acc=GSE223003&format=file"
fi
tar -xf "$TAR" -C data/raw
n=$(ls data/raw/GSM*_ReSisTrace_*.tsv.gz | wc -l)
echo "extracted $n ReSisTrace files (expected 32)"
[ "$n" -eq 32 ]
