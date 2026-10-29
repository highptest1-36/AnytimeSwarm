#!/usr/bin/env bash
# Study 4 development runs, part 2 (dev seeds 0-9 only): the same one-parameter search for the proposed effective
# deadline with the fallback (z was selected in study 2 without it) and wider grids where part 1 hit a boundary.
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
cd $J
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
PY=~/venvs/atswarm/bin/python
T="fb=nominal+periodic:60"
M=""
for z in ${ZCC:-0 0.25 0.5 1 1.5}; do M="$M,alns_fixed@40~z=$z;$T"; done
for z in ${ZMP:-1.5 2}; do M="$M,alns_fixed@40~mp=$z;$T"; done
for c in ${CPROP:-0.6 0.8}; do M="$M,alns_fixed@40~prop=$c;$T"; done
M=${M#,}
$PY experiments/b4_grid.py --name ${RUN_NAME:-dev4_tune2} --split dev --exec mid,high --lat high --kappas 10,50,200 \
    --windows 1,0.5 --methods "$M" --workers 8 --resume > results/tier_b/${RUN_NAME:-dev4_tune2}_log.txt 2>&1
