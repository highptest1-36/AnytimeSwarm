#!/usr/bin/env bash
# Study 6 development runs (dev seeds 0-9 only): CBBA (periodic and event trigger, nominal and proposed model with the
# cost-aware fallback) and moment propagation with the cost-aware fallback. No parameter is tuned; the runs check the
# implementation, the planning time of CBBA and the effect sizes for the sample size. Results: results/tier_b/dev6.csv
set -uo pipefail
cd /mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
PY=~/venvs/atswarm/bin/python
T="+periodic:60"
M="cbba$T,cbba+event,cbba~z=auto4;lam=1$T,alns_fixed@40~mp=auto;lam=1$T"
$PY experiments/b6_grid.py --name dev6 --split dev --exec mid,high --lat high --kappas 10,50,200 \
    --windows 1,0.5 --methods "$M" --workers 8 --resume > results/tier_b/dev6_log.txt 2>&1
echo "dev6 done"
