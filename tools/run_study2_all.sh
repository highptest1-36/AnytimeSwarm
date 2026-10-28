#!/usr/bin/env bash
# Study 2: every pre-registered held-out experiment of docs/08_PROTOCOL_V2.md. Run ONCE after freezing (resumable).
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
cd $J
export PYTHONDONTWRITEBYTECODE=1
PY=~/venvs/atswarm/bin/python
LOG=$J/results/heldout_logs
mkdir -p $LOG
step() { echo "[study2] $(date -Is) $1" | tee -a $LOG/progress_study2.txt; }

step "freeze check"
sha256sum -c results/frozen_study2_sha256.txt >> $LOG/progress_study2.txt 2>&1 || { step "FROZEN FILES CHANGED - abort"; exit 1; }

step "tier B S2_B_main"
$PY experiments/b2_grid.py --config experiments/configs/S2_B_main.yaml --resume > $LOG/S2_B_main.log 2>&1
tail -1 $LOG/S2_B_main.log | tee -a $LOG/progress_study2.txt

step "tier B counterpart of tier C (gz scale)"
$PY experiments/b2_grid.py --config experiments/configs/S2_B_gz.yaml --resume > $LOG/S2_B_gz.log 2>&1
tail -1 $LOG/S2_B_gz.log | tee -a $LOG/progress_study2.txt

step "tier C"
for s in $(seq 6000 6009); do
  bash journal_ros/run_batch.sh s2_heldout_C "arrivals failures deadlines" "$s" \
    "proposed alns_fixed@40 alns_fixed@40~buf=60" 50 periodic:60 2 mid >> $LOG/S2_C.log 2>&1
  bash journal_ros/run_batch.sh s2_heldout_C_event "arrivals failures deadlines" "$s" \
    "alns_fixed@40" 50 event 2 mid >> $LOG/S2_C.log 2>&1
done
# pre-registered: a run whose real-time factor leaves [0.8F, 1.1F] = [1.6, 2.2] is repeated once (original kept)
for d in s2_heldout_C s2_heldout_C_event; do
  $PY - "$J/results/tier_c/$d" <<'PY'
import glob, json, os, shutil, sys
d = sys.argv[1]
os.makedirs(f"{d}/invalid_rtf", exist_ok=True)
for f in sorted(glob.glob(f"{d}/gz-*.json")):
    if not 1.6 <= json.load(open(f))["rtf"] <= 2.2 and not os.path.exists(f"{d}/invalid_rtf/{os.path.basename(f)}"):
        print("invalid RTF, repeat once:", os.path.basename(f))
        shutil.move(f, f"{d}/invalid_rtf/")
PY
done >> $LOG/S2_C.log 2>&1
for s in $(seq 6000 6009); do
  bash journal_ros/run_batch.sh s2_heldout_C "arrivals failures deadlines" "$s" \
    "proposed alns_fixed@40 alns_fixed@40~buf=60" 50 periodic:60 2 mid >> $LOG/S2_C.log 2>&1
  bash journal_ros/run_batch.sh s2_heldout_C_event "arrivals failures deadlines" "$s" \
    "alns_fixed@40" 50 event 2 mid >> $LOG/S2_C.log 2>&1
done
grep -c " ok " $LOG/S2_C.log | sed 's/^/tier C runs ok (incl. repeats): /' | tee -a $LOG/progress_study2.txt
step "done"
