#!/usr/bin/env bash
# ROS 2 Jazzy + Gazebo Harmonic (ros_gz) on Ubuntu 24.04. Run as the normal user.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y curl git wget locales software-properties-common \
  build-essential cmake python3-pip python3-venv

sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
sudo add-apt-repository universe -y

if ! dpkg -s ros2-apt-source >/dev/null 2>&1; then
  ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
    | grep -F '"tag_name"' | awk -F'"' '{print $4}')
  CODENAME=$(. /etc/os-release && echo "${UBUNTU_CODENAME:-${VERSION_CODENAME}}")
  curl -L -o /tmp/ros2-apt-source.deb \
    "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.${CODENAME}_all.deb"
  sudo dpkg -i /tmp/ros2-apt-source.deb
fi

sudo apt-get update
sudo apt-get install -y ros-jazzy-desktop ros-dev-tools python3-colcon-common-extensions \
  python3-rosdep ros-jazzy-ros-gz

[ -f /etc/ros/rosdep/sources.list.d/20-default.list ] || sudo rosdep init
rosdep update

grep -q "/opt/ros/jazzy/setup.bash" ~/.bashrc || echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
echo "ROS 2 Jazzy + ros_gz installed"
