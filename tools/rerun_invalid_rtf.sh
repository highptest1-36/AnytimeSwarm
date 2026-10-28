#!/usr/bin/env bash
# Tier C held-out runs whose real-time factor fell below 0.8F (protocol validity range [0.8F, 1.1F], F = 2) are moved to
# heldout_C/invalid_rtf/ and repeated once with the same seed (handled like a technical failure; see
# docs/05_PROTOCOL_JOURNAL.md, deviations). The batch skips every run that already has a result file.
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
D=$J/results/tier_c/heldout_C
mkdir -p $D/invalid_rtf
~/venvs/atswarm/bin/python - <<PY
import glob, json, shutil
for f in sorted(glob.glob("$D/gz-*.json")):
    m = json.load(open(f))
    if not 1.6 <= m["rtf"] <= 2.2:
        print("invalid RTF", round(m["rtf"], 3), f.split("/")[-1])
        shutil.move(f, "$D/invalid_rtf/")
PY
bash $J/journal_ros/run_batch.sh heldout_C "arrivals failures deadlines" "$(seq -s ' ' 4000 4009)" \
  "alns_fixed alns_fixed@40 anytime anytime_risk" 50 event 2 mid >> $J/results/heldout_logs/C_rerun_rtf.log 2>&1
echo "[rerun] $(date -Is) done" >> $J/results/heldout_logs/C_rerun_rtf.log
