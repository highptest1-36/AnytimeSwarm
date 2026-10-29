#!/usr/bin/env bash
# Study 3: the pre-registered held-out experiment of docs/10_PROTOCOL_V3.md. Run ONCE after freezing (resumable).
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
cd $J
export PYTHONDONTWRITEBYTECODE=1
PY=~/venvs/atswarm/bin/python
LOG=$J/results/heldout_logs
mkdir -p $LOG
step() { echo "[study3] $(date -Is) $1" | tee -a $LOG/progress_study3.txt; }

step "freeze check"
sha256sum -c results/frozen_study3_sha256.txt >> $LOG/progress_study3.txt 2>&1 || { step "FROZEN FILES CHANGED - abort"; exit 1; }

step "tier B S3_B"
$PY experiments/b3_grid.py --config experiments/configs/S3_B.yaml --split heldout --resume > $LOG/S3_B.log 2>&1
tail -1 $LOG/S3_B.log | tee -a $LOG/progress_study3.txt

step "analysis"
OMP_NUM_THREADS=1 MPLBACKEND=Agg $PY experiments/analyze_study3.py > $LOG/analysis_study3.log 2>&1
step "done"
