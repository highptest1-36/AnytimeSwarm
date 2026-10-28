#!/usr/bin/env bash
# Every pre-registered held-out experiment, in the order of docs/05_PROTOCOL_JOURNAL.md. Run ONCE after freezing.
#   bash tools/run_heldout_all.sh            (resumable: finished configurations / missions are skipped)
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
cd $J
export PYTHONDONTWRITEBYTECODE=1
PY=~/venvs/atswarm/bin/python
LOG=$J/results/heldout_logs
mkdir -p $LOG
step() { echo "[heldout] $(date -Is) $1" | tee -a $LOG/progress.txt; }

step "freeze check"
sha256sum -c results/frozen_journal_sha256.txt >> $LOG/progress.txt 2>&1 || { step "FROZEN FILES CHANGED - abort"; exit 1; }

for c in B_main B_xl B_sens_high_k1_dev B_sens_misspec B_gz; do
  step "tier B $c"
  $PY experiments/b_grid.py --config experiments/configs/$c.yaml --resume > $LOG/$c.log 2>&1
  tail -1 $LOG/$c.log | tee -a $LOG/progress.txt
done

step "tier C heldout_C"
bash journal_ros/run_batch.sh heldout_C "arrivals failures deadlines" "$(seq -s ' ' 4000 4009)" \
  "alns_fixed alns_fixed@40 anytime anytime_risk" 50 event 2 mid > $LOG/C_main.log 2>&1
grep -c " ok " $LOG/C_main.log | sed 's/^/tier C missions ok: /' | tee -a $LOG/progress.txt
grep -c "FAIL" $LOG/C_main.log | sed 's/^/tier C failed attempts: /' | tee -a $LOG/progress.txt

step "analysis"
$PY experiments/analyze_heldout.py > $LOG/analysis.log 2>&1
step "done"
