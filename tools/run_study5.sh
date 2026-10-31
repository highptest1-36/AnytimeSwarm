#!/usr/bin/env bash
# Study 5: the pre-registered held-out experiment of docs/13_PROTOCOL_V5.md. Run ONCE after freezing (resumable).
# Tier B, seeds 10000-10029.
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
cd $J
export PYTHONDONTWRITEBYTECODE=1
PY=~/venvs/atswarm/bin/python
LOG=$J/results/heldout_logs
mkdir -p $LOG
step() { echo "[study5] $(date -Is) $1" | tee -a $LOG/progress_study5.txt; }

step "freeze check"
sha256sum -c results/frozen_study5_sha256.txt >> $LOG/progress_study5.txt 2>&1 || { step "FROZEN FILES CHANGED - abort"; exit 1; }
step "tier B S5_B"
$PY experiments/b5_grid.py --config experiments/configs/S5_B.yaml --split heldout --resume > $LOG/S5_B.log 2>&1
tail -1 $LOG/S5_B.log | tee -a $LOG/progress_study5.txt
step "tier B analysis"
OMP_NUM_THREADS=1 MPLBACKEND=Agg $PY experiments/analyze_study5.py > $LOG/analysis_study5.log 2>&1
step "done"
