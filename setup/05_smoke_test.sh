#!/usr/bin/env bash
# G1 acceptance test: headless PX4 X500 in Gazebo + XRCE-DDS agent + ROS 2 telemetry.
#   bash 05_smoke_test.sh            # 1 UAV
#   bash 05_smoke_test.sh 2          # 2 UAVs (instance 1 starts Gazebo, instance 2 joins)
set -uo pipefail
N=${1:-1}
LOG=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm_Journal/setup/logs
mkdir -p "$LOG"
set +u; source /opt/ros/jazzy/setup.bash; source ~/px4_ros_ws/install/setup.bash; set -u
export PATH="$HOME/.local/bin:$PATH"

cleanup() { pkill -f MicroXRCEAgent; pkill -f "bin/px4"; pkill -f "gz sim"; sleep 2; }
cleanup

MicroXRCEAgent udp4 -p 8888 > "$LOG/smoke_agent.log" 2>&1 &
cd ~/PX4-Autopilot
for i in $(seq 1 "$N"); do
  STANDALONE=""; [ "$i" -gt 1 ] && STANDALONE="PX4_GZ_STANDALONE=1"
  env HEADLESS=1 $STANDALONE PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 \
      PX4_GZ_MODEL_POSE="$(( (i-1)*5 )),0" \
      ./build/px4_sitl_default/bin/px4 -i "$i" > "$LOG/smoke_px4_$i.log" 2>&1 &
  sleep 20
done
sleep 20

echo "== /fmu topics"
ros2 topic list | grep fmu | sort | tee "$LOG/smoke_topics.txt"
TOPIC=$(grep -m1 "fmu/out/vehicle_odometry" "$LOG/smoke_topics.txt")
echo "== one message from $TOPIC"
timeout 15 ros2 topic echo --once "$TOPIC" | head -20
echo "== rate"
timeout 10 ros2 topic hz "$TOPIC" 2>&1 | tail -2
echo "== gz real-time factor"
timeout 5 gz topic -e -t /stats -n 1 2>/dev/null | grep -E "real_time_factor|sim_time" | head -3

cleanup
