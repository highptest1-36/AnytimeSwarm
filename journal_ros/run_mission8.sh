#!/usr/bin/env bash
# Study 8C: one tier C mission as journal_ros/run_mission4.sh (study 4C), with the nodes started through
# journal_ros/study8c.py (planners of journal_core/study8.solve8: cost-aware fallback, nominal fallback, proportional
# buffer; whole planning call timed; time windows multiplied by --windows F) and the tier C error model of study 4
# (models/error_model_tierc_dev4.json).
#
#   bash $J/journal_ros/run_mission.sh --gui --rviz                       # watch: Gazebo window + RViz2
#   bash $J/journal_ros/run_mission.sh --profile failures --seed 3 --method alns_fixed --kappa-b 50 --gui
#   bash $J/journal_ros/run_mission.sh --out results/tier_c/x.json       # headless benchmark run
#
# Options: --profile arrivals|failures|deadlines  --seed N  --method <planner>  --budget-ms B  --kappa-b K
#          --trigger event|deviation:<s>|periodic:<s>  --gui  --rviz  --speed F (PX4_SIM_SPEED_FACTOR)
#          --out FILE.json  --latency-mean-s L  --exec nominal|low|mid|high (disturbance level, as tier B)
# The script stops every process it started when the mission manager exits (or on Ctrl+C).
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
PROFILE=arrivals; SEED=0; METHOD=anytime; BUDGET=250; KAPPA=10; TRIGGER=event; GUI=0; RVIZ=0; SPEED=1
OUT=""; LAT=""; EXEC=nominal; WIN=1
while [ $# -gt 0 ]; do
  case $1 in
    --profile) PROFILE=$2; shift 2;; --seed) SEED=$2; shift 2;; --method) METHOD=$2; shift 2;;
    --budget-ms) BUDGET=$2; shift 2;; --kappa-b) KAPPA=$2; shift 2;; --trigger) TRIGGER=$2; shift 2;;
    --gui) GUI=1; shift;; --rviz) RVIZ=1; shift;; --speed) SPEED=$2; shift 2;; --out) OUT=$2; shift 2;;
    --latency-mean-s) LAT=$2; shift 2;; --exec) EXEC=$2; shift 2;; --windows) WIN=$2; shift 2;;
    *) echo "unknown option $1"; exit 2;;
  esac
done
TAG="gz-${PROFILE}-${SEED}_${METHOD}_k${KAPPA}_${TRIGGER//:/}_${EXEC}_w${WIN}"
export ATSWARM_WINDOW=$WIN
[ -z "$OUT" ] && OUT="$J/results/tier_c/manual/${TAG}.json"
case $OUT in /*) ;; *) OUT="$J/$OUT";; esac
LOG=$J/results/tier_c/logs/$TAG
mkdir -p "$LOG" "$(dirname "$OUT")"
PY=~/venvs/atswarm/bin/python
set +u
source /opt/ros/jazzy/setup.bash
source ~/px4_ros_ws/install/setup.bash
source $J/ros2_ws/install/setup.bash
set -u
export PYTHONDONTWRITEBYTECODE=1

PIDS=()
cleanup() {
  for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null; done
  pkill -f "px4_sitl_default/bin/px4" 2>/dev/null; pkill -f "gz sim" 2>/dev/null
  pkill -f MicroXRCEAgent 2>/dev/null; pkill -f "parameter_bridge /clock" 2>/dev/null
  pkill -f "journal_ros/(uav_executor|viz).py" 2>/dev/null; pkill -x rviz2 2>/dev/null
  sleep 2
}
trap 'cleanup; exit 130' INT TERM
cleanup

N=3
read -r -a SPAWN <<< "$($PY -c "
import sys; sys.path.insert(0, '$J/journal_ros')
from common import spawn_xy
print(' '.join(f'{x:g},{y:g}' for x, y in (spawn_xy(k, $N) for k in range($N))))")"

echo "[run] $TAG  gui=$GUI rviz=$RVIZ speed=$SPEED -> $OUT"
MicroXRCEAgent udp4 -p 8888 > "$LOG/agent.log" 2>&1 & PIDS+=($!)
cd ~/PX4-Autopilot
B=./build/px4_sitl_default/bin
for i in $(seq 1 $N); do
  ENVV="PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500 PX4_GZ_MODEL_POSE=${SPAWN[$((i-1))]} PX4_SIM_SPEED_FACTOR=$SPEED"
  [ "$GUI" = 0 ] && ENVV="HEADLESS=1 $ENVV"
  [ "$i" -gt 1 ] && ENVV="PX4_GZ_STANDALONE=1 $ENVV"
  env $ENVV $B/px4 -d -i "$i" > "$LOG/px4_$i.log" 2>&1 & PIDS+=($!)
  [ "$i" = 1 ] && sleep 18 || sleep 8
done
sleep 8
for i in $(seq 1 $N); do
  (cd build/px4_sitl_default && ./bin/px4-param --instance "$i" set NAV_DLL_ACT 0 >/dev/null \
     && ./bin/px4-param --instance "$i" set COM_LOW_BAT_ACT 0 >/dev/null)
done

ros2 run ros_gz_bridge parameter_bridge /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock \
  > "$LOG/clock_bridge.log" 2>&1 & PIDS+=($!)
SIMT="--ros-args -p use_sim_time:=true"
$PY $J/journal_ros/study8c.py executor --profile "$PROFILE" --seed "$SEED" --exec "$EXEC" $SIMT > "$LOG/executor.log" 2>&1 & PIDS+=($!)
if [ "$GUI" = 1 ] || [ "$RVIZ" = 1 ]; then
  $PY $J/journal_ros/viz.py --profile "$PROFILE" --seed "$SEED" $SIMT > "$LOG/viz.log" 2>&1 & PIDS+=($!)
fi
if [ "$RVIZ" = 1 ]; then
  rviz2 -d $J/journal_ros/atswarm.rviz $SIMT > "$LOG/rviz.log" 2>&1 & PIDS+=($!)
fi
$PY $J/journal_ros/study8c.py manager --profile "$PROFILE" --seed "$SEED" --method "$METHOD" --budget-ms "$BUDGET" \
  --kappa-b "$KAPPA" --trigger "$TRIGGER" ${LAT:+--latency-mean-s $LAT} --error-level "$EXEC" --error-model "$J/models/error_model_tierc_dev4.json" --out "$OUT" $SIMT \
  2>&1 | tee "$LOG/mission.log"
[ "$GUI" = 1 ] && sleep 8          # let the UAVs land on screen
cleanup
echo "[run] done -> $OUT"
