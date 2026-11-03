#!/usr/bin/env bash
# Study 8: the held-out experiments of docs/18_PROTOCOL_V8.md. Run ONCE after freezing (resumable: tier B grids skip
# finished configurations, tier C skips finished flights). Machine must be otherwise idle (timing and real-time factor).
#   1. tier B counterpart of the tier C missions (8c, seeds 17000-17019)          a few minutes
#   2. tier C flights (8c, 60 missions x 3 methods), RTF check, repeats, analysis  about 14 h
#   3. tier B 8b (emergency-response family, seeds 16000-16029)                   about 2 h
#   4. tier B 8a (planning budget, seeds 15000-15029)                             about 8 h
#   5. analysis of 8a and 8b
# SKIP_C=1 skips steps 1-2, SKIP_B=1 skips steps 3-5.
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
cd $J
export PYTHONDONTWRITEBYTECODE=1
PY=~/venvs/atswarm/bin/python
LOG=$J/results/heldout_logs
mkdir -p $LOG
step() { echo "[study8] $(date -Is) $1" | tee -a $LOG/progress_study8.txt; }

step "freeze check"
sha256sum -c results/frozen_study8_sha256.txt >> $LOG/progress_study8.txt 2>&1 || { step "FROZEN FILES CHANGED - abort"; exit 1; }

METHODS="alns_fixed@40~z=0.5,lam=1,cost=fee alns_fixed@40~z=0.5,fb=nominal alns_fixed@40~prop=0.45,fb=none"
SEEDS=$(seq -s " " 17000 17019)
fly() {
  for s in $SEEDS; do
    bash journal_ros/run_batch8.sh s8c_heldout_C "arrivals failures deadlines" "$s" "$METHODS" 50 periodic:60 2 high 0.5 \
      >> $LOG/S8_C.log 2>&1
  done
}
rtf_check() {   # pre-registered: a run with RTF outside [1.6, 2.2] is repeated once (original kept in invalid_rtf/)
  $PY - "$J/results/tier_c/s8c_heldout_C" <<'PY' >> $LOG/S8_C.log 2>&1
import glob, json, os, shutil, sys
d = sys.argv[1]
os.makedirs(f"{d}/invalid_rtf", exist_ok=True)
for f in sorted(glob.glob(f"{d}/gz-*.json")):
    if not 1.6 <= json.load(open(f))["rtf"] <= 2.2 and not os.path.exists(f"{d}/invalid_rtf/{os.path.basename(f)}"):
        print("invalid RTF, repeat once:", os.path.basename(f))
        shutil.move(f, f"{d}/invalid_rtf/")
PY
}

if [ "${SKIP_C:-0}" != 1 ]; then
  step "tier B counterpart of tier C (S8c_B_gz)"
  $PY experiments/b8c_gz.py --config experiments/configs/S8c_B_gz.yaml --split heldout --resume > $LOG/S8c_B_gz.log 2>&1
  tail -1 $LOG/S8c_B_gz.log | tee -a $LOG/progress_study8.txt
  step "tier C flights"
  fly
  rtf_check
  step "tier C repeats of invalid RTF"
  fly
  step "tier C analysis"
  OMP_NUM_THREADS=1 MPLBACKEND=Agg $PY experiments/analyze_study8c.py > $LOG/analysis_study8c.log 2>&1
  grep -A4 "## Primary" $LOG/analysis_study8c.log | tee -a $LOG/progress_study8.txt
fi

if [ "${SKIP_B:-0}" != 1 ]; then
  step "tier B S8b_B"
  $PY experiments/b8_grid.py --config experiments/configs/S8b_B.yaml --split heldout --resume > $LOG/S8b_B.log 2>&1
  tail -1 $LOG/S8b_B.log | tee -a $LOG/progress_study8.txt
  step "tier B S8a_B"
  $PY experiments/b8_grid.py --config experiments/configs/S8a_B.yaml --split heldout --resume > $LOG/S8a_B.log 2>&1
  tail -1 $LOG/S8a_B.log | tee -a $LOG/progress_study8.txt
  step "tier B analysis"
  OMP_NUM_THREADS=1 MPLBACKEND=Agg $PY experiments/analyze_study8.py > $LOG/analysis_study8.log 2>&1
fi
step "done"
