#!/usr/bin/env bash
# Study 4 development runs (dev seeds 0-9 only): selects c of the proportional buffer, z of moment propagation and
# (n0, z) of online calibration. Results: results/tier_b/dev4_tune.csv
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
cd $J
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
PY=~/venvs/atswarm/bin/python
T="fb=nominal+periodic:60"
M="alns_fixed@40~z=auto;$T"
for c in 0.05 0.1 0.2 0.3 0.45; do M="$M,alns_fixed@40~prop=$c;$T"; done
for z in 0 0.5 1; do M="$M,alns_fixed@40~mp=$z;$T"; done
for n in 50 300; do for z in 0 0.25 0.5; do M="$M,alns_fixed@40~online=$n;z=$z;$T"; done; done
$PY experiments/b4_grid.py --name dev4_tune --split dev --exec mid,high --lat high --kappas 10,50,200 \
    --windows 1,0.5 --methods "$M" --workers 8 --resume > results/tier_b/dev4_tune_log.txt 2>&1
