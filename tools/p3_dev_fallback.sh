#!/usr/bin/env bash
# Study 3, P3a: does a nominal fallback for tasks that the chance-constrained model gives up repair its weakness under
# high disturbances with halved windows (study 2), without losing its advantage elsewhere? Dev seeds only.
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
cd $J
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
M="proposed+periodic:60,proposed~fb=nominal+periodic:60,proposed~fb=60+periodic:60,alns_fixed@40~buf=60+periodic:60,alns_fixed@40+periodic:60"
~/venvs/atswarm/bin/python experiments/b3_grid.py --name dev3_fallback --exec mid,high --lat high --kappas 10,50,200 \
  --windows 1,0.5 --methods "$M" --workers 4 --resume > results/tier_b/dev3_fallback_log.txt 2>&1
echo "[p3a] done" >> results/tier_b/dev3_fallback_log.txt
