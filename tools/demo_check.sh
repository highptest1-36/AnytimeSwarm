#!/usr/bin/env bash
# Check the tools needed for the illustrative tier C figures (no flight).
for g in /opt/ros/jazzy/opt/gz_sim_vendor/share/gz/gz-sim8/gui/gui.config ~/.gz/sim/8/gui.config; do
  [ -f "$g" ] && { echo "$g"; grep -o 'filename="[A-Za-z]*"' "$g" | sort -u | tr '\n' ' '; echo; }
done
ls ~/PX4-Autopilot/build/px4_sitl_default/rootfs/ 2>/dev/null | head
find ~/PX4-Autopilot/build/px4_sitl_default/rootfs -name '*.ulg' 2>/dev/null | wc -l
grep -n "def map_to_gz\|def spawn_xy\|SCALE\|scale" /mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal/journal_ros/common.py | head
