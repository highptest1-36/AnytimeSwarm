#!/usr/bin/env bash
# Show (and with --kill stop) every simulation / tier C process inside WSL. Run as: bash tools/wsl_status.sh [--kill]
PAT='px4_sitl_default/bin/px4|gz sim|MicroXRCEAgent|uav_executor.py|mission_manager.py|viz.py|run_batch.sh|run_mission.sh|parameter_bridge|rviz2'
if [ "${1:-}" = "--kill" ]; then
  pkill -f 'run_batch.sh|calib_dev.sh'
  pkill -f 'run_mission.sh'
  pkill -f 'px4_sitl_default/bin/px4'
  pkill -f 'gz sim'
  pkill -f MicroXRCEAgent
  pkill -f 'uav_executor.py|mission_manager.py|viz.py|parameter_bridge'
  pkill -x rviz2
  sleep 2
fi
ps -eo pid,etime,pcpu,args | grep -E "$PAT" | grep -v grep | cut -c1-140
echo "processes: $(ps -eo args | grep -E "$PAT" | grep -vc grep)"
