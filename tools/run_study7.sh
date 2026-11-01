#!/usr/bin/env bash
# Study 7: the held-out experiment of docs/16_PROTOCOL_V7.md. Run ONCE after freezing (resumable).
# Tier B, seeds 13000-13029 (7a) and 14000-14029 (7b).
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
cd $J
export PYTHONDONTWRITEBYTECODE=1
PY=~/venvs/atswarm/bin/python
LOG=$J/results/heldout_logs
mkdir -p $LOG
step() { echo "[study7] $(date -Is) $1" | tee -a $LOG/progress_study7.txt; }

step "freeze check"
sha256sum -c results/frozen_study7_sha256.txt >> $LOG/progress_study7.txt 2>&1 || { step "FROZEN FILES CHANGED - abort"; exit 1; }
step "tier B S7a_B"
$PY experiments/b7_grid.py --config experiments/configs/S7a_B.yaml --split heldout --resume > $LOG/S7a_B.log 2>&1
tail -1 $LOG/S7a_B.log | tee -a $LOG/progress_study7.txt
step "tier B S7b_B"
$PY experiments/b7_grid.py --config experiments/configs/S7b_B.yaml --split heldout --resume > $LOG/S7b_B.log 2>&1
tail -1 $LOG/S7b_B.log | tee -a $LOG/progress_study7.txt
step "tier B S7b_lat_B"
$PY experiments/b7_grid.py --config experiments/configs/S7b_lat_B.yaml --split heldout --resume > $LOG/S7b_lat_B.log 2>&1
tail -1 $LOG/S7b_lat_B.log | tee -a $LOG/progress_study7.txt
step "tier B analysis"
OMP_NUM_THREADS=1 MPLBACKEND=Agg $PY experiments/analyze_study7.py > $LOG/analysis_study7.log 2>&1
step "done"
