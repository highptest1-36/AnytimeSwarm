#!/usr/bin/env bash
# Study 8 development and pilot runs before the freeze (docs/18_PROTOCOL_V8.md sections 4a, 4b, 5a).
#   bash tools/p8_dev.sh load     # 4a: nominal model only, both families, LOAD8 grid (dev seeds 0-9)
#   bash tools/p8_dev.sh check    # 4b: every 8b method on the new family, dev seeds 0-2 (needs LOAD8 set)
#   bash tools/p8_dev.sh budget   # 8a implementation check: every method at 5 and 250 ms, dev seeds 0-1, one config
#   bash tools/p8_dev.sh pilot    # 5a: tier B counterpart of tier C on pilot seeds 19000-19099
# Results: results/tier_b/dev8_*.csv, pilot8c_gz.csv
set -uo pipefail
cd /mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
PY=~/venvs/atswarm/bin/python
T="+periodic:60"
case ${1:-} in
  load)
    $PY experiments/b8_grid.py --name dev8_load_conf --split dev --scales small,medium,large --exec nominal --lat none \
        --kappas 10 --windows 1 --methods "alns_fixed@40$T" --workers 4 > results/tier_b/dev8_load_conf_log.txt 2>&1
    for L in 0.6 0.8 1.0 1.25 1.5; do
      ATSWARM_LOAD8=$L $PY experiments/b8_grid.py --name dev8_load_$L --split dev --scales small8,medium8,large8 \
          --exec nominal --lat none --kappas 10 --windows 1 --methods "alns_fixed@40$T" --workers 4 \
          > results/tier_b/dev8_load_${L}_log.txt 2>&1
    done
    $PY - <<'PY'
import pandas as pd
c = pd.read_csv("results/tier_b/dev8_load_conf.csv")
print(f"conference family: U {c.utility_rate.mean():.4f}, completion {c.completion_rate.mean():.4f} ({len(c)} missions)")
for L in ("0.6", "0.8", "1.0", "1.25", "1.5"):
    d = pd.read_csv(f"results/tier_b/dev8_load_{L}.csv")
    print(f"LOAD8 {L}: U {d.utility_rate.mean():.4f}, completion {d.completion_rate.mean():.4f}, "
          f"|dU| {abs(d.utility_rate.mean() - c.utility_rate.mean()):.4f}")
PY
    ;;
  check)
    M="alns_fixed@40$T,alns_fixed@40~z=auto4;fb=nominal$T,alns_fixed@40~z=auto4;lam=1;cost=fee$T"
    M="$M,alns_fixed@40~z=auto4;lam=1$T,alns_fixed@40~mp=auto;lam=1$T"
    M="$M,alns_fixed@40~prop=0.3;fb=none$T,alns_fixed@40~prop=0.45;fb=none$T,alns_fixed@40~z=1$T,alns_fixed@40~z=0.5$T"
    $PY experiments/b8_grid.py --name dev8b_check --seeds 0-2 --scales small8,medium8,large8 --exec mid,high \
        --lat high --kappas 50 --windows 1,0.5 --methods "$M" --workers 4 > results/tier_b/dev8b_check_log.txt 2>&1
    tail -1 results/tier_b/dev8b_check_log.txt
    ;;
  budget)
    M=""
    for B in 5 250; do
      for o in "~z=auto4;lam=1;cost=fee" "~z=auto4;lam=1" "~mp=auto;lam=1" "~prop=0.45;fb=none" ""; do
        M="$M,alns_fixed@$B$o$T"
      done
    done
    $PY experiments/b8_grid.py --name dev8a_check --seeds 0-1 --scales small,medium,large --exec high --lat high \
        --kappas 50 --windows 0.5 --methods "${M#,}" --workers 4 > results/tier_b/dev8a_check_log.txt 2>&1
    tail -1 results/tier_b/dev8a_check_log.txt
    ;;
  pilot)
    M="alns_fixed@40~z=0.5;lam=1;cost=fee$T,alns_fixed@40~z=0.5;fb=nominal$T,alns_fixed@40~prop=0.45;fb=none$T"
    $PY experiments/b8c_gz.py --name pilot8c_gz --seeds 19000-19099 --scales gz --exec high --lat none --kappas 50 \
        --windows 0.5 --methods "$M" --workers 4 > results/tier_b/pilot8c_gz_log.txt 2>&1
    tail -1 results/tier_b/pilot8c_gz_log.txt
    ;;
  *) echo "usage: p8_dev.sh load|check|budget|pilot"; exit 2;;
esac
