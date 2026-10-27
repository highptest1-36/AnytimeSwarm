#!/usr/bin/env bash
# ROS 2 workspace with px4_msgs (matched to PX4 1.17) and Micro XRCE-DDS Agent v2.4.3.
set -euo pipefail
WS=~/px4_ros_ws
mkdir -p "$WS/src"
cd "$WS/src"
[ -d px4_msgs ] || git clone --branch release/1.17 https://github.com/PX4/px4_msgs.git
[ -d Micro-XRCE-DDS-Agent ] || git clone --branch v2.4.3 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git

cd "$WS"
set +u; source /opt/ros/jazzy/setup.bash; set -u
# px4_msgs generates many interfaces; 4 workers keeps peak RAM below the WSL limit
MAKEFLAGS="-j4" colcon build --symlink-install --parallel-workers 4 --cmake-args -DCMAKE_BUILD_TYPE=Release

grep -q "$WS/install/setup.bash" ~/.bashrc || echo "source $WS/install/setup.bash" >> ~/.bashrc
echo "px4_ros_ws built"
