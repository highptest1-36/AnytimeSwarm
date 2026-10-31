#!/usr/bin/env bash
# Run the study 5 tests and write the freeze list (docs/13_PROTOCOL_V5.md).
set -euo pipefail
cd /mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
export PYTHONDONTWRITEBYTECODE=1
~/venvs/atswarm/bin/python -m pytest -q tests/test_study5.py tests/test_study4.py 2>&1 | tail -3
sha256sum -c results/frozen_study4_sha256.txt 2>&1 | grep -v ": OK$" || true
sha256sum journal_core/study5.py experiments/b5_grid.py experiments/analyze_study5.py experiments/analyze_dev5.py \
  experiments/configs/S5_B.yaml tools/run_study5.sh tests/test_study5.py docs/13_PROTOCOL_V5.md \
  > results/frozen_study5_sha256.txt
cat results/frozen_study5_sha256.txt
