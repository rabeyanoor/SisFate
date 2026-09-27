#!/usr/bin/env bash
# Leaner finish of the heavy experiments (replaces the remainder of run_long.sh, which would take ~20 h).
# CatBoost on 2,000 genes is kept to within-arm CV; GNN seeds are spent where variance matters.
set -uo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
GNN="mlp mlp_pretrain persist_gnn_nopretrain persist_gnn"

$PY scripts/04_baselines.py --cc-mode keep --models pca_catboost --n-shuffles 1                    > logs/catboost_pca_keep.log 2>&1
$PY scripts/04_baselines.py --cc-mode keep --models hvg_catboost --splits within --n-shuffles 1    > logs/catboost_hvg_keep.log 2>&1
$PY scripts/05_gnn.py --cc-mode keep --models $GNN --splits within rep_holdout --seeds 0 1 2 --n-shuffles 0 > logs/gnn_keep_seeds.log 2>&1
$PY scripts/05_gnn.py --cc-mode keep --models $GNN --splits within --seeds 0 --n-shuffles 1        > logs/gnn_keep_shuffle.log 2>&1
$PY scripts/05_gnn.py --cc-mode keep --models mlp persist_gnn --splits cross_arm --seeds 0 --n-shuffles 0 > logs/gnn_keep_cross.log 2>&1
$PY scripts/05_gnn.py --cc-mode regress_all --models mlp persist_gnn --splits within --seeds 0 --n-shuffles 0 > logs/gnn_regress_all.log 2>&1
for cc in keep regress_all; do
  $PY scripts/07_ceiling.py --cc-mode $cc   > logs/ceiling_$cc.log 2>&1
done
$PY scripts/13_robustness.py --cc-mode regress_all --n-perm 100 > logs/robustness_regress_all.log 2>&1
for cc in keep regress regress_all; do
  $PY scripts/11_summarize.py --cc-mode $cc > logs/summary_$cc.log 2>&1
done
rm -f results/tcga_ov_cox.csv
for sig in specific_Carboplatin specific_Olaparib specific_NK all_Carboplatin fitness_Control; do
  $PY scripts/09_tcga_ov.py --signature $sig >> logs/tcga.log 2>&1
done
echo "ALL DONE $(date)" > logs/done.txt
