#!/usr/bin/env bash
# Python environments for the journal (run as the normal user inside WSL).
#   ~/venvs/atswarm311 : CPython 3.11.9 + the exact package versions of the conference runs (reproduction, G0)
#   ~/venvs/atswarm    : system Python 3.12 (ROS 2 Jazzy's interpreter) + same package versions + rclpy visible
set -euo pipefail
PKGS="numpy==2.4.6 scipy==1.17.1 pandas==3.1.0 scikit-learn==1.9.1 matplotlib==3.11.2 PyYAML==6.0.3 pytest==9.1.1 ortools==9.15.6755"
mkdir -p ~/venvs

if [ ! -x ~/venvs/tools/bin/uv ]; then
  python3 -m venv ~/venvs/tools
  ~/venvs/tools/bin/pip install -q uv
fi
UV=~/venvs/tools/bin/uv

$UV python install 3.11.9
[ -d ~/venvs/atswarm311 ] || $UV venv -p 3.11.9 ~/venvs/atswarm311
VIRTUAL_ENV=~/venvs/atswarm311 $UV pip install -q $PKGS

# --system-site-packages exposes /opt/ros/jazzy python packages (rclpy, px4_msgs) once ROS is sourced
[ -d ~/venvs/atswarm ] || python3 -m venv --system-site-packages ~/venvs/atswarm
VIRTUAL_ENV=~/venvs/atswarm $UV pip install -q $PKGS

for v in atswarm311 atswarm; do
  echo "== $v"
  ~/venvs/$v/bin/python -c "import sys, numpy, scipy, pandas, sklearn, ortools; print(sys.version.split()[0], numpy.__version__, scipy.__version__, pandas.__version__, sklearn.__version__, ortools.__version__)"
done
