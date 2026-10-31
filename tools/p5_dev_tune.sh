#!/usr/bin/env bash
# Study 5 development runs (dev seeds 0-9 only). The cost-aware fallback has no tuned parameter (z of study 4, lam is
# the late cost); the competitors are tuned per late cost on these runs: c of the proportional buffer with and without
# fallback, z of the chance-constrained model without fallback. Results: results/tier_b/dev5_tune.csv
set -uo pipefail
cd /mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
PY=~/venvs/atswarm/bin/python
T="+periodic:60"
M="alns_fixed@40~z=auto4;fb=nominal$T"
for l in 0.5 1 2; do M="$M,alns_fixed@40~z=auto4;lam=$l$T"; done
for z in 0 0.5 1 1.5; do M="$M,alns_fixed@40~z=$z$T"; done
for c in 0.3 0.45 0.6 0.75 0.9 1.2; do M="$M,alns_fixed@40~prop=$c;fb=nominal$T,alns_fixed@40~prop=$c;fb=none$T"; done
M="$M,alns_fixed@40~mp=auto;fb=nominal$T,alns_fixed@40~mp=auto$T,alns_fixed@40$T,alns_fixed@40~buf=60$T"
$PY experiments/b5_grid.py --name dev5_tune --split dev --exec mid,high --lat high --kappas 10,50,200 \
    --windows 1,0.5 --methods "$M" --workers 8 --resume > results/tier_b/dev5_tune_log.txt 2>&1
echo "dev5 done"
