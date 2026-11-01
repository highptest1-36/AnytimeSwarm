#!/usr/bin/env bash
# Close-up of one UAV: read its pose from Gazebo, place the GUI camera DIST m behind and above it, and capture.
#   bash tools/demo_near.sh <model> <dir> [dist]
set +u; source /opt/ros/jazzy/setup.bash; set -u
M=$1; DIR=$2; DIST=${3:-5}
P=$(gz model -m "$M" -p 2>/dev/null | grep -A1 "Pose \[ XYZ" | tail -1 | tr -d '[]|')
python3 - "$P" "$DIST" "$DIR" <<'PY'
import math, subprocess, sys
x, y, z = map(float, sys.argv[1].split()[:3]); d = float(sys.argv[2])
cx, cy, cz = x - 0.8 * d, y - 0.6 * d, z + 0.45 * d
yaw = math.atan2(y - cy, x - cx); pitch = math.atan2(cz - z, math.hypot(x - cx, y - cy))
cp, sp, cyw, syw = math.cos(pitch / 2), math.sin(pitch / 2), math.cos(yaw / 2), math.sin(yaw / 2)
q = (cp * cyw, -sp * syw, sp * cyw, cp * syw)
req = f"pose: {{position: {{x: {cx}, y: {cy}, z: {cz}}}, orientation: {{w: {q[0]}, x: {q[1]}, y: {q[2]}, z: {q[3]}}}}}"
subprocess.run(["gz", "service", "-s", "/gui/move_to/pose", "--reqtype", "gz.msgs.GUICamera", "--reptype",
                "gz.msgs.Boolean", "--timeout", "3000", "--req", req], capture_output=True)
print("uav at", x, y, z)
PY
sleep 2
gz service -s /gui/screenshot --reqtype gz.msgs.StringMsg --reptype gz.msgs.Boolean --timeout 5000 --req "data: \"$DIR/\"" >/dev/null
