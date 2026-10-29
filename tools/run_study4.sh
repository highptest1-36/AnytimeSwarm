#!/usr/bin/env bash
# Study 4: the pre-registered held-out experiments of docs/12_PROTOCOL_V4.md. Run ONCE after freezing (resumable).
# Tier B (seeds 8000-8029), tier B counterpart of tier C, then tier C (seeds 9000-9011) with one interim analysis.
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
cd $J
export PYTHONDONTWRITEBYTECODE=1
PY=~/venvs/atswarm/bin/python
LOG=$J/results/heldout_logs
mkdir -p $LOG
step() { echo "[study4] $(date -Is) $1" | tee -a $LOG/progress_study4.txt; }

step "freeze check"
sha256sum -c results/frozen_study4_sha256.txt >> $LOG/progress_study4.txt 2>&1 || { step "FROZEN FILES CHANGED - abort"; exit 1; }

if [ "${SKIP_B:-0}" != 1 ]; then
  step "tier B S4_B"
  $PY experiments/b4_grid.py --config experiments/configs/S4_B.yaml --split heldout --resume > $LOG/S4_B.log 2>&1
  tail -1 $LOG/S4_B.log | tee -a $LOG/progress_study4.txt
  step "tier B analysis"
  OMP_NUM_THREADS=1 MPLBACKEND=Agg $PY experiments/analyze_study4.py > $LOG/analysis_study4.log 2>&1
  step "tier B counterpart of tier C"
  $PY experiments/b4c_gz.py --config experiments/configs/S4C_B_gz.yaml --split heldout --resume > $LOG/S4C_B_gz.log 2>&1
  tail -1 $LOG/S4C_B_gz.log | tee -a $LOG/progress_study4.txt
fi

METHODS="proposed~z=0.5,fb=nominal proposed~z=0.5 alns_fixed@40"
fly() {   # seeds...
  for s in "$@"; do
    bash journal_ros/run_batch4.sh s4_heldout_C "arrivals failures deadlines" "$s" "$METHODS" 50 periodic:60 2 high 0.5 \
      >> $LOG/S4_C.log 2>&1
  done
}
rtf_check() {   # pre-registered: a run with RTF outside [1.6, 2.2] is repeated once (original kept in invalid_rtf/)
  $PY - "$J/results/tier_c/s4_heldout_C" <<'PY' >> $LOG/S4_C.log 2>&1
import glob, json, os, shutil, sys
d = sys.argv[1]
os.makedirs(f"{d}/invalid_rtf", exist_ok=True)
for f in sorted(glob.glob(f"{d}/gz-*.json")):
    if not 1.6 <= json.load(open(f))["rtf"] <= 2.2 and not os.path.exists(f"{d}/invalid_rtf/{os.path.basename(f)}"):
        print("invalid RTF, repeat once:", os.path.basename(f))
        shutil.move(f, f"{d}/invalid_rtf/")
PY
}
INTERIM="9000 9001 9002 9003 9004 9005"
REST="9006 9007 9008 9009 9010 9011"
step "tier C, first half"
fly $INTERIM; rtf_check; fly $INTERIM
step "tier C interim analysis"
$PY experiments/analyze_study4c.py --stage interim > $LOG/analysis_study4c_interim.log 2>&1
if [ $? = 3 ]; then
  step "interim bound crossed: stop early"
  $PY experiments/analyze_study4c.py --stage interim --write > $LOG/analysis_study4c.log 2>&1
else
  step "tier C, second half"
  fly $REST; rtf_check; fly $REST
  step "tier C final analysis"
  $PY experiments/analyze_study4c.py --stage final > $LOG/analysis_study4c.log 2>&1
fi
step "done"
