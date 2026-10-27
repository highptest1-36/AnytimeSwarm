#!/usr/bin/env bash
# Check that every PX4 instance publishes its local position and report altitude / arming (tier C debugging).
set +u
source /opt/ros/jazzy/setup.bash
source ~/px4_ros_ws/install/setup.bash
for i in 1 2 3; do
  echo "== px4_$i: $(ros2 topic list | grep -c "/px4_$i/") topics"
  timeout 6 ros2 topic echo --once /px4_$i/fmu/out/vehicle_local_position_v1 --field z 2>&1 | head -1 | sed 's/^/   z = /'
  timeout 6 ros2 topic echo --once /px4_$i/fmu/out/vehicle_status_v1 2>&1 | grep -E "^arming_state|^nav_state:|^failsafe:" | tr '\n' ' '
  echo
  timeout 6 ros2 topic echo --once /px4_$i/fmu/out/vehicle_land_detected 2>&1 | grep -E "^landed|^ground_contact" | tr '\n' ' '
  echo
done
