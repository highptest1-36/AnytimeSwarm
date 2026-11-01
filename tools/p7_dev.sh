#!/usr/bin/env bash
# Study 7 development runs (dev seeds 0-9 only), before the protocol is frozen (docs/16_PROTOCOL_V7.md).
# 7a: the cost-aware fallback with both late-cost models (no tuned parameter), and the competitor families tuned per
#     late cost and per score: proportional buffer c with and without the nominal fallback, the proposed model without
#     fallback with z. Every run logs the late reward, so both scores u_fee and u_prop can be computed.
# 7b: implementation and size check of the shifted execution errors (seeds 0-4, kappa 50); nothing is tuned on it.
# Results: results/tier_b/dev7a.csv, dev7b.csv, dev7b_lat.csv
set -uo pipefail
cd /mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
PY=~/venvs/atswarm/bin/python
T="+periodic:60"
M="alns_fixed@40~z=auto4;fb=nominal$T,alns_fixed@40$T"
for l in 0.5 1 2; do M="$M,alns_fixed@40~z=auto4;lam=$l$T,alns_fixed@40~z=auto4;lam=$l;cost=fee$T"; done
for z in -0.5 0 0.5 1 1.5; do M="$M,alns_fixed@40~z=$z$T"; done
for c in 0.1 0.2 0.3 0.45 0.6 0.75 0.9 1.2; do M="$M,alns_fixed@40~prop=$c;fb=nominal$T,alns_fixed@40~prop=$c;fb=none$T"; done
$PY experiments/b7_grid.py --name dev7a --split dev --exec mid,high --lat high --kappas 10,50,200 \
    --windows 1,0.5 --methods "$M" --workers 8 --resume > results/tier_b/dev7a_log.txt 2>&1
echo "dev7a done"
B="alns_fixed@40$T,alns_fixed@40~buf=60$T,alns_fixed@40~prop=auto;fb=nominal$T,alns_fixed@40~mp=auto;lam=1$T"
B="$B,alns_fixed@40~z=auto4;fb=nominal$T,alns_fixed@40~z=auto4;lam=1$T"
$PY experiments/b7_grid.py --name dev7b --seeds 0-4 --exec high_gauss,high_t3,high_outlier,high_uavbias --lat high \
    --kappas 50 --windows 1,0.5 --methods "$B" --workers 8 --resume > results/tier_b/dev7b_log.txt 2>&1
$PY experiments/b7_grid.py --name dev7b_lat --seeds 0-4 --exec high_gauss --lat high_pareto \
    --kappas 50 --windows 1,0.5 --methods "$B" --workers 8 --resume > results/tier_b/dev7b_lat_log.txt 2>&1
echo "dev7b done"
