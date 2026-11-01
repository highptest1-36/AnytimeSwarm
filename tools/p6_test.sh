#!/usr/bin/env bash
# Study 6: unit tests and a timing check of CBBA (dev scenarios only).
set -uo pipefail
cd /mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
~/venvs/atswarm/bin/python -m pytest -q tests/test_study6.py tests/test_study5.py 2>&1 | tail -15
