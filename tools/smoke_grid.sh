#!/usr/bin/env bash
# Functional smoke test of experiments/b_grid.py on DEV seeds (gz and xl scales). Not an experiment.
cd /mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
export PYTHONDONTWRITEBYTECODE=1
PY=~/venvs/atswarm/bin/python
$PY experiments/b_grid.py --name smoke_gz --scales gz --exec mid --lat none --kappas 50 --triggers event \
    --methods alns_fixed@40,anytime_risk --workers 1 --quick 2>&1 | grep -E "exec=|ok|Error|Traceback"
$PY experiments/b_grid.py --name smoke_xl --scales xl --exec mid --lat none --kappas 50 --triggers event \
    --methods anytime_risk --workers 1 --quick 2>&1 | grep -E "exec=|ok|Error|Traceback"
rm -f results/tier_b/smoke_gz.csv results/tier_b/smoke_xl.csv
