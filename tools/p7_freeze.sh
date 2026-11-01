#!/usr/bin/env bash
# Run the study 7 tests and write the freeze list (docs/16_PROTOCOL_V7.md).
set -euo pipefail
cd /mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
export PYTHONDONTWRITEBYTECODE=1
~/venvs/atswarm/bin/python -m pytest -q -p no:cacheprovider tests/test_study7.py tests/test_study6.py tests/test_study5.py tests/test_study4.py 2>&1 | tail -3
sha256sum journal_core/study7.py experiments/b7_grid.py experiments/analyze_study7.py experiments/configs/S7a_B.yaml \
  experiments/configs/S7b_B.yaml experiments/configs/S7b_lat_B.yaml tools/run_study7.sh tests/test_study7.py \
  docs/16_PROTOCOL_V7.md > results/frozen_study7_sha256.txt
cat results/frozen_study7_sha256.txt
