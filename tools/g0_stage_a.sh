#!/usr/bin/env bash
# G0 stage A (no timing involved): regenerate the DEV scenarios and replanning snapshots on Linux with
#   Python 3.11.9 (same interpreter + packages as the conference runs) and Python 3.12 (journal / ROS env),
# then compare both, leaf by leaf, with the conference pickles. Snapshot generation runs ALNS for a fixed
# number of iterations (kappa = 0), so any difference is a platform / interpreter effect, not timing.
set -euo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
R=$J/repro
ORIG=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm
OUT=$J/results/g0
mkdir -p "$OUT"
cd "$R"

C=configs/frozen_2026-10-24.yaml
sed -e 's#^  data_dir: data .*#  data_dir: data_py312#' -e 's#^  results_dir: results.*#  results_dir: results_py312#' \
    "$C" > configs/g0_py312.yaml
grep -n "data_dir\|results_dir" configs/g0_py312.yaml

{
echo "# G0 stage A  $(date -Is)"
sha256sum "$C" "$ORIG/$C" models/improvement_model.json "$ORIG/models/improvement_model.json"
for env in atswarm311 atswarm; do
  cfg=$C; [ "$env" = atswarm ] && cfg=configs/g0_py312.yaml
  echo "== 02_generate_snapshots --split dev  ($env, $cfg)"
  /usr/bin/time -f "   wall %e s, max RSS %M KB" ~/venvs/$env/bin/python experiments/02_generate_snapshots.py --config "$cfg" --split dev | tail -2
done
for d in data data_py312; do
  for f in scenarios_dev snapshots_dev; do
    ~/venvs/atswarm311/bin/python $J/tools/compare_pickles.py --code "$R" "$ORIG/data/$f.pkl" "$R/$d/$f.pkl" || true
  done
  # the conference CSV was written on Windows (CRLF); compare content, not line endings
  if cmp -s <(tr -d '\r' < "$ORIG/data/snapshots_dev_summary.csv") <(tr -d '\r' < "$R/$d/snapshots_dev_summary.csv"); then
    echo "snapshots_dev_summary.csv ($d): identical content (line endings ignored)"
  else
    echo "snapshots_dev_summary.csv ($d): DIFFERENT"; diff <(tr -d '\r' < "$ORIG/data/snapshots_dev_summary.csv") "$R/$d/snapshots_dev_summary.csv" | head -5
  fi
done
} 2>&1 | tee "$OUT/stage_a.txt"
