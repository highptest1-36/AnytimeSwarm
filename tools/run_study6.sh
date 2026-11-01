#!/usr/bin/env bash
# Study 6: the pre-registered held-out experiment of docs/14_PROTOCOL_V6.md. Run ONCE after freezing (resumable).
# Tier B, seeds 12000-12029.
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
cd $J
export PYTHONDONTWRITEBYTECODE=1
PY=~/venvs/atswarm/bin/python
LOG=$J/results/heldout_logs
mkdir -p $LOG
step() { echo "[study6] $(date -Is) $1" | tee -a $LOG/progress_study6.txt; }

step "freeze check"
sha256sum -c results/frozen_study6_sha256.txt >> $LOG/progress_study6.txt 2>&1 || { step "FROZEN FILES CHANGED - abort"; exit 1; }
step "tier B S6_B"
$PY experiments/b6_grid.py --config experiments/configs/S6_B.yaml --split heldout --resume > $LOG/S6_B.log 2>&1
tail -1 $LOG/S6_B.log | tee -a $LOG/progress_study6.txt
step "tier B analysis"
OMP_NUM_THREADS=1 MPLBACKEND=Agg $PY experiments/analyze_study6.py > $LOG/analysis_study6.log 2>&1
step "done"
