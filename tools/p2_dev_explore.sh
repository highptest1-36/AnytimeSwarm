#!/usr/bin/env bash
# Study 2, P2: development exploration (dev seeds 0-9 only) to choose z, trigger and the scaled-budget factor.
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
cd $J
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
M="alns_fixed@40+event,alns_fixed+event,alns_scaled~ms=0.5+event,alns_scaled~ms=1+event,alns_scaled~ms=2+event"
M="$M,profile+event,online_curve+event,anytime+event,anytime_risk+event"
M="$M,proposed~z=0+event,proposed~z=0.5+event,proposed~z=1+event,proposed~z=1.5+event"
M="$M,proposed~z=0.5+periodic:60,proposed~z=0.5+hybrid:20:60,proposed~z=0.5+hybrid:30:60,proposed~z=0.5+hybrid:30:120,proposed~z=0.5+hybrid:60:120"
M="$M,alns_fixed@40~z=0.5+event,alns_fixed@40+periodic:60,alns_fixed@40~z=0.5+periodic:60,anytime_risk+periodic:60"
~/venvs/atswarm/bin/python experiments/b2_grid.py --name dev2_explore --exec mid,high --lat high --kappas 50 \
  --windows 1,0.5 --methods "$M" --workers 4 --resume > results/tier_b/dev2_explore_log.txt 2>&1
echo "[p2] done" >> results/tier_b/dev2_explore_log.txt
