#!/usr/bin/env bash
# Print one /atswarm/fleet_state message (phase, altitude, position of every UAV) of a running tier C mission.
set +u
source /opt/ros/jazzy/setup.bash
source /mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal/ros2_ws/install/setup.bash
timeout 10 ros2 topic echo --once /atswarm/fleet_state 2>&1 | grep -E "mission_|^  id|phase|alive|^  z:|^  x:|^  y:" | head -30
