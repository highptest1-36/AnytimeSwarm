#!/usr/bin/env bash
# Study 5 smoke test on development seed 0 (one configuration per new option).
set -uo pipefail
cd /mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
PY=~/venvs/atswarm/bin/python
M="alns_fixed@40~z=auto4;lam=1+periodic:60,alns_fixed@40~z=auto4;lam=0.5+periodic:60,alns_fixed@40~z=auto4;fb=nominal+periodic:60,alns_fixed@40~z=auto+periodic:60,alns_fixed@40~prop=0.6;fb=none+periodic:60,alns_fixed@40~prop=0.6;fb=nominal+periodic:60"
$PY experiments/b5_grid.py --name dev5_smoke --split dev --seeds 0-0 --scales small --exec high --lat high --kappas 50 \
    --windows 0.5 --methods "$M" --workers 4 2>&1 | tail -5
$PY - <<'P'
import pandas as pd
d = pd.read_csv("results/tier_b/dev5_smoke.csv")
d["late_frac"] = d.late_served / d.n_tasks
print(d.groupby("method")[["utility_rate", "late_served", "served", "plan_ms_mean"]].mean().round(3).to_string())
P
