#!/usr/bin/env bash
# Multi-treatment clonal tracing: Schaff et al. 2026 Cell Genomics, GEO GSE279162.
# Nine samples (three untreated lanes + six treatments). Lineage barcodes are stored inside the same
# matrices as the genes, as features of type "Custom", so no separate barcode file is needed.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/external/schaff/raw
tar=data/external/schaff/GSE279162_RAW.tar
[ -s "$tar" ] || wget -q -O "$tar" \
  "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE279nnn/GSE279162/suppl/GSE279162_RAW.tar"
tar -xf "$tar" -C data/external/schaff/raw
ls -lh data/external/schaff/raw | head
