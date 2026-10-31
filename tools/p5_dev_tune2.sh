#!/usr/bin/env bash
# Study 5 development runs, second grid (dev seeds 0-9 only): the first grid selected values on its edge
# (proportional buffer c = 0.3 without fallback at mid, z = 0 without fallback at high), so the competitors' grids are
# extended downwards. Results: results/tier_b/dev5_tune2.csv
set -uo pipefail
cd /mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
PY=~/venvs/atswarm/bin/python
T="+periodic:60"
M="alns_fixed@40~z=-0.5$T"
for c in 0.1 0.2; do M="$M,alns_fixed@40~prop=$c;fb=nominal$T,alns_fixed@40~prop=$c;fb=none$T"; done
$PY experiments/b5_grid.py --name dev5_tune2 --split dev --exec mid,high --lat high --kappas 10,50,200 \
    --windows 1,0.5 --methods "$M" --workers 8 --resume > results/tier_b/dev5_tune2_log.txt 2>&1
echo "dev5 tune2 done"
