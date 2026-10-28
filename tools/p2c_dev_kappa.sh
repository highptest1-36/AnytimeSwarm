#!/usr/bin/env bash
# Study 2, P2c: does the stopping rule matter on a slow planner (kappa_B 200)? Dev seeds only; every method uses the
# same planning model (z = 0.5) and the periodic trigger so that only the stopping rule differs.
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
cd $J
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
M="alns_fixed@40~z=0.5,alns_fixed~z=0.5,alns_scaled~z=0.5,alns_stagnation~z=0.5,profile~z=0.5,online_curve~z=0.5,anytime~z=0.5,proposed~z=0.5,regret_repair~z=0.5"
~/venvs/atswarm/bin/python experiments/b2_grid.py --name dev2c_kappa --exec mid --lat high --kappas 200,50 \
  --windows 1,0.5 --triggers periodic:60 --methods "$M" --workers 4 --resume > results/tier_b/dev2c_kappa_log.txt 2>&1
echo "[p2c] done" >> results/tier_b/dev2c_kappa_log.txt
