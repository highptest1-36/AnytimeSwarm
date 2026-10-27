#!/usr/bin/env bash
# Headless check of demo/offboard_waypoints.py on one vehicle (instance 0).
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm_Journal; LOG=$J/setup/logs
set +u; source /opt/ros/jazzy/setup.bash; source ~/px4_ros_ws/install/setup.bash; set -u
B=~/PX4-Autopilot/build/px4_sitl_default
stop() { pkill -f MicroXRCEAgent; pkill -f "px4_sitl_default/bin/px4 -d"; pkill -f "gz sim"; sleep 2; }
stop
MicroXRCEAgent udp4 -p 8888 > $LOG/demo_agent.log 2>&1 &
cd ~/PX4-Autopilot
HEADLESS=1 PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 $B/bin/px4 -d > $LOG/demo_px4.log 2>&1 &
sleep 20
# SITL has no ground station: allow arming without a GCS link (airframe default NAV_DLL_ACT=2 blocks it)
(cd $B && ./bin/px4-param --instance 0 set NAV_DLL_ACT 0 >/dev/null)
timeout ${1:-120} python3 $J/demo/offboard_waypoints.py --hold 2 2>&1 | grep --line-buffered "offboard_waypoints" | tee $LOG/demo_1uav.txt
stop
