#!/usr/bin/env bash
# G0 stage B: re-run the conference DEV pipeline on Linux (Python 3.11.9, frozen config, same order as
# results/run_dev_v2_chain.sh of the conference repo) inside repro/, under the Linux machine-idle guard.
#   reference (ALNS 3 s + OR-Tools 5 s) -> 03 traces + predictor -> 04 static -> 05 closed loop -> 06 -> 10
# The predictor that 03 re-trains on Linux is kept as models/improvement_model_linux.json for comparison;
# static and closed-loop runs use the FROZEN conference predictor (models/improvement_model.json, sha256 checked).
set -euo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm_Journal
R=$J/repro
OUT=$J/results/g0
PY=~/venvs/atswarm311/bin/python
C=configs/frozen_2026-10-24.yaml
G="$PY $J/tools/run_guarded.py $R"
FROZEN_SHA=b22254d999d56a23268f2e0e58e1d6221f93a9d83b12288a3c8205e1282f67b3
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OUT"
cd "$R"
step() { echo "[g0-b] $1  $(date -Is)"; }

step start
nproc; free -g | head -2
echo "$FROZEN_SHA  models/improvement_model.json" | sha256sum -c -
cp models/improvement_model.json models/improvement_model_frozen.json

step "reference (6 workers)"
$G experiments/04_run_static.py --config $C --split dev --only-reference --ref-workers 6

step "03 traces + predictor (Linux re-train)"
$G experiments/03_train_improvement_model.py --config $C --recollect
mv models/improvement_model.json models/improvement_model_linux.json
cp models/improvement_model_frozen.json models/improvement_model.json
echo "$FROZEN_SHA  models/improvement_model.json" | sha256sum -c -

step "04 static (frozen predictor)"
$G experiments/04_run_static.py --config $C --split dev --skip-reference

step "05 closed loop (frozen predictor)"
$G experiments/05_run_closed_loop.py --config $C --split dev

step "06 bootstrap + 10 offline policies"
$G experiments/06_bootstrap.py --config $C --split dev
$G experiments/10_offline_policies.py --config $C --split dev

step done
