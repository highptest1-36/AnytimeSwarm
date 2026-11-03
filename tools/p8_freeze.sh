#!/usr/bin/env bash
# Run the study 8 tests and write the freeze list (docs/18_PROTOCOL_V8.md).
set -euo pipefail
cd /mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
export PYTHONDONTWRITEBYTECODE=1
~/venvs/atswarm/bin/python -m pytest -q -p no:cacheprovider tests/test_study8.py tests/test_study7.py tests/test_study6.py \
  tests/test_study5.py tests/test_study4.py 2>&1 | tail -3
sha256sum journal_core/study8.py journal_core/study7.py experiments/b8_grid.py experiments/b8c_gz.py experiments/b7_grid.py \
  experiments/analyze_study8.py experiments/analyze_study8c.py experiments/configs/S8a_B.yaml \
  experiments/configs/S8b_B.yaml experiments/configs/S8c_B_gz.yaml journal_ros/study8c.py journal_ros/run_mission8.sh \
  journal_ros/run_batch8.sh tools/run_study8.sh tests/test_study8.py docs/18_PROTOCOL_V8.md \
  > results/frozen_study8_sha256.txt
cat results/frozen_study8_sha256.txt
