#!/usr/bin/env bash
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm_Journal
cd $J
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg
nice -n 19 ~/venvs/atswarm/bin/python experiments/make_paper_numbers.py
