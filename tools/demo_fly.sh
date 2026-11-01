#!/usr/bin/env bash
# Illustrative tier C flights for the manuscript figures (development seed only; no statistics are taken from them).
# One mission (dev seed 1, arrivals, high disturbances, windows x0.5, kappa_B 50, periodic 60 s, speed 2, as study 4C)
# is flown with the Gazebo GUI, once with the proposed model with fallback and once with the nominal model. During each
# flight, the Gazebo GUI is captured every SHOT_S seconds; after each flight, the PX4 logs (ULog) are kept.
#   bash tools/demo_fly.sh            -> results/tier_c/demo/{<method>.json, shots/<method>/*.png, ulog/<method>/*.ulg}
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
D=$J/results/tier_c/demo
SHOT_S=${SHOT_S:-45}
ROOTFS=~/PX4-Autopilot/build/px4_sitl_default/rootfs
mkdir -p "$D"
set +u; source /opt/ros/jazzy/setup.bash; set -u
fly() {   # method tag
  local M=$1 T=$2
  mkdir -p "$D/shots/$T" "$D/ulog/$T"
  touch "$D/.start_$T"
  ( sleep 75
    for n in $(seq -w 1 40); do
      gz service -s /gui/screenshot --reqtype gz.msgs.StringMsg --reptype gz.msgs.Boolean --timeout 3000 \
        --req "data: \"$D/shots/$T/\"" > /dev/null 2>&1
      sleep "$SHOT_S"
      pgrep -f "study4c.py manager" > /dev/null || break
    done ) &
  local SH=$!
  bash $J/journal_ros/run_mission4.sh --profile arrivals --seed 1 --method "$M" --kappa-b 50 \
    --trigger periodic:60 --exec high --windows 0.5 --speed 2 --gui --out "$D/$T.json" > "$D/$T.log" 2>&1
  kill $SH 2>/dev/null
  for f in $(find "$ROOTFS" -name '*.ulg' -newer "$D/.start_$T"); do
    i=$(echo "$f" | sed -E 's#.*/rootfs/([0-9]+)/.*#\1#'); cp "$f" "$D/ulog/$T/uav${i}_$(basename "$f")"; done
  echo "[demo] $T done: $(ls "$D/shots/$T" | wc -l) shots, $(ls "$D/ulog/$T" | wc -l) logs"
}
fly "proposed~z=0.5,fb=nominal" proposed
fly "alns_fixed@40" nominal
echo "[demo] all done"
