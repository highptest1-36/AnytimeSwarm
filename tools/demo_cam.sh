#!/usr/bin/env bash
# Camera control and capture for the illustrative tier C screenshots (Gazebo GUI must be running).
#   bash tools/demo_cam.sh list
#   bash tools/demo_cam.sh follow <model> <dir>         follow a UAV from behind and capture
#   bash tools/demo_cam.sh pose x y z roll pitch yaw <dir>  move the camera and capture
set +u; source /opt/ros/jazzy/setup.bash; set -u
cmd=$1; shift
shot() { gz service -s /gui/screenshot --reqtype gz.msgs.StringMsg --reptype gz.msgs.Boolean --timeout 5000 \
           --req "data: \"$1/\"" ; }
case $cmd in
  list) gz model --list 2>/dev/null; gz service -l 2>/dev/null | grep -i "gui/" ;;
  follow)
    gz service -s /gui/follow --reqtype gz.msgs.StringMsg --reptype gz.msgs.Boolean --timeout 3000 --req "data: \"$1\""
    gz service -s /gui/follow/offset --reqtype gz.msgs.Vector3d --reptype gz.msgs.Boolean --timeout 3000 \
      --req "x: -6, y: -6, z: 4"
    sleep 4; shot "$2" ;;
  pose)
    gz service -s /gui/follow --reqtype gz.msgs.StringMsg --reptype gz.msgs.Boolean --timeout 3000 --req "data: \"\""
    python3 - "$@" <<'PY'
import math, subprocess, sys
x, y, z, r, p, yw = map(float, sys.argv[1:7])
cr, sr = math.cos(r / 2), math.sin(r / 2); cp, sp = math.cos(p / 2), math.sin(p / 2); cy, sy = math.cos(yw / 2), math.sin(yw / 2)
q = (cr * cp * cy + sr * sp * sy, sr * cp * cy - cr * sp * sy, cr * sp * cy + sr * cp * sy, cr * cp * sy - sr * sp * cy)
req = (f"pose: {{position: {{x: {x}, y: {y}, z: {z}}}, orientation: {{w: {q[0]}, x: {q[1]}, y: {q[2]}, z: {q[3]}}}}}")
subprocess.run(["gz", "service", "-s", "/gui/move_to/pose", "--reqtype", "gz.msgs.GUICamera", "--reptype",
                "gz.msgs.Boolean", "--timeout", "3000", "--req", req])
PY
    sleep 3; shot "$7" ;;
esac
