#!/usr/bin/env bash
# Run the study 6 tests and write the freeze list (docs/14_PROTOCOL_V6.md).
set -euo pipefail
cd /mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
export PYTHONDONTWRITEBYTECODE=1
~/venvs/atswarm/bin/python -m pytest -q tests/test_study6.py tests/test_study5.py tests/test_study4.py 2>&1 | tail -3
sha256sum journal_core/study6.py experiments/b6_grid.py experiments/analyze_study6.py experiments/configs/S6_B.yaml \
  tools/run_study6.sh tests/test_study6.py docs/14_PROTOCOL_V6.md > results/frozen_study6_sha256.txt
cat results/frozen_study6_sha256.txt
