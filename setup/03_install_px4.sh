#!/usr/bin/env bash
# PX4-Autopilot v1.17.0 (pinned) + SITL build. Run as the normal user.
# --no-nuttx skips the ARM toolchain: only SITL is needed, no flight-controller firmware.
set -euo pipefail
PX4_TAG=v1.17.0
cd ~

if [ ! -d PX4-Autopilot ]; then
  git clone --branch "$PX4_TAG" --recurse-submodules https://github.com/PX4/PX4-Autopilot.git
fi
cd PX4-Autopilot
git describe --tags

bash Tools/setup/ubuntu.sh --no-nuttx
# ubuntu.sh installs Python deps with pip into the user site; make sure they are found
export PATH="$HOME/.local/bin:$PATH"

make px4_sitl
echo "PX4 $PX4_TAG SITL built"
