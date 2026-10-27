#!/usr/bin/env bash
# Tier C development flights for the error model / latency calibration (DEV seeds 0-2, every profile, low and mid).
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm_Journal
for lv in low mid; do
  bash $J/journal_ros/run_batch.sh "calib_dev_$lv" "arrivals failures deadlines" "0 1 2" "alns_fixed@40" 10 event 2 "$lv"
done
