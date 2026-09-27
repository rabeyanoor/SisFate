#!/usr/bin/env bash
# Heavy experiments after preprocessing (01-03) is done. Logs go to logs/. Resume-safe: each step appends
# to results/results.csv and 11_summarize.py keeps the latest row per setting.
set -uo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
FAST="cov_logreg pca_logreg hvg_logreg pca_smooth_logreg pca_logreg_pooled"

for cc in keep regress regress_all; do
  $PY scripts/04_baselines.py --cc-mode $cc --models $FAST                          > logs/baselines_$cc.log 2>&1
  $PY scripts/04_baselines.py --cc-mode $cc --models pca_logreg_tuned --n-shuffles 1 > logs/tuned_$cc.log 2>&1
  $PY scripts/06_fitness_confound.py --cc-mode $cc                                  > logs/fitness_$cc.log 2>&1
  $PY scripts/07_ceiling.py --cc-mode $cc                                           > logs/ceiling_$cc.log 2>&1
  $PY scripts/11_summarize.py --cc-mode $cc                                         > logs/summary_$cc.log 2>&1
done
for cc in keep regress_all; do
  $PY scripts/04_baselines.py --cc-mode $cc --models hvg_catboost pca_catboost --n-shuffles 1 > logs/catboost_$cc.log 2>&1
  $PY scripts/05_gnn.py --cc-mode $cc --n-shuffles 1                                 > logs/gnn_$cc.log 2>&1
  $PY scripts/07_ceiling.py --cc-mode $cc                                            > logs/ceiling_$cc.log 2>&1
  $PY scripts/11_summarize.py --cc-mode $cc                                          > logs/summary_$cc.log 2>&1
done
for sig in specific_Carboplatin specific_Olaparib specific_NK all_Carboplatin fitness_Control; do
  $PY scripts/09_tcga_ov.py --signature $sig >> logs/tcga.log 2>&1
done
echo "ALL DONE $(date)" >> logs/done.txt
