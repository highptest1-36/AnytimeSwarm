#!/usr/bin/env bash
# Light analysis while a grid is running (single thread, low priority).
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm_Journal
cd $J
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
nice -n 19 ~/venvs/atswarm/bin/python experiments/analyze_heldout.py
