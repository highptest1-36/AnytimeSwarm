#!/usr/bin/env bash
# Study 2, P2b: dev exploration after the exact (finish-dependent) chance-constrained deadline. Dev seeds 0-9 only.
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
cd $J
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
M="alns_fixed@40+event,alns_fixed@40+periodic:60,anytime_risk+periodic:60"
M="$M,proposed~z=0+periodic:60,proposed~z=0.25+periodic:60,proposed~z=0.5+periodic:60,proposed~z=1+periodic:60"
M="$M,proposed~z=0.5+hybrid:30:60,proposed~z=0.5+hybrid:30:120,proposed~z=0.5+event"
M="$M,alns_fixed@40~z=0.5+periodic:60,alns_fixed@40~buf=30+periodic:60,alns_fixed@40~buf=60+periodic:60,alns_fixed@40~buf=120+periodic:60"
~/venvs/atswarm/bin/python experiments/b2_grid.py --name dev2b_explore --exec mid,high --lat high --kappas 50 \
  --windows 1,0.5 --methods "$M" --workers 4 --resume > results/tier_b/dev2b_explore_log.txt 2>&1
echo "[p2b] done" >> results/tier_b/dev2b_explore_log.txt
