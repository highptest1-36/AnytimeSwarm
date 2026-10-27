#!/usr/bin/env bash
# Headless check: two vehicles (instances 1, 2) fly different routes in one shared world frame.
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm_Journal; LOG=$J/setup/logs
set +u; source /opt/ros/jazzy/setup.bash; source ~/px4_ros_ws/install/setup.bash; set -u
B=~/PX4-Autopilot/build/px4_sitl_default
stop() { pkill -f MicroXRCEAgent; pkill -f "px4_sitl_default/bin/px4 -d"; pkill -f "gz sim"; sleep 2; }
stop
MicroXRCEAgent udp4 -p 8888 > $LOG/demo_agent.log 2>&1 &
cd ~/PX4-Autopilot
HEADLESS=1 PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 PX4_GZ_MODEL_POSE="0,0" $B/bin/px4 -d -i 1 > $LOG/demo_px4_1.log 2>&1 &
sleep 15
HEADLESS=1 PX4_GZ_STANDALONE=1 PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 PX4_GZ_MODEL_POSE="5,0" $B/bin/px4 -d -i 2 > $LOG/demo_px4_2.log 2>&1 &
sleep 20
for i in 1 2; do (cd $B && ./bin/px4-param --instance $i set NAV_DLL_ACT 0 >/dev/null); done
# world frame North,East,Up. UAV1 spawned at east=0, UAV2 at east=5
timeout ${1:-120} python3 $J/demo/offboard_waypoints.py --ns /px4_1 --spawn 0,0 --hold 2 \
    --wps "0,0,6;20,0,6;20,-15,6;0,0,6" 2>&1 | grep --line-buffered "offboard" > $LOG/demo_2uav_1.txt &
P1=$!
timeout ${1:-120} python3 $J/demo/offboard_waypoints.py --ns /px4_2 --spawn 5,0 --hold 2 \
    --wps "0,5,8;20,20,8;0,20,8;0,5,8" 2>&1 | grep --line-buffered "offboard" > $LOG/demo_2uav_2.txt &
P2=$!
wait $P1 $P2   # only the two flyers, not the agent / PX4 / Gazebo
cat $LOG/demo_2uav_1.txt $LOG/demo_2uav_2.txt
stop
