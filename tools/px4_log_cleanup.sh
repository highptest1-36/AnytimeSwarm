#!/bin/bash
# Delete the PX4 flight logs (.ulg) that SITL writes per UAV and flight (about 100 MB each; 127 GB after studies 1-4C).
# No analysis reads them: every result comes from the mission JSON files. PX4 parameters stay unchanged, so logging
# and its load on the machine are the same as in earlier flights; only the files are removed afterwards.
# Call after each flight from new study runners (the frozen runners of studies 1-4 are not changed):
#   bash tools/px4_log_cleanup.sh            # delete all .ulg under the SITL rootfs
#   bash tools/px4_log_cleanup.sh --keep DIR # move the logs of this flight to DIR instead (sample missions)
set -u
R=~/PX4-Autopilot/build/px4_sitl_default/rootfs
if [ "${1:-}" = "--keep" ] && [ -n "${2:-}" ]; then
  mkdir -p "$2"
  find $R -name "*.ulg" -exec mv -t "$2" {} +
else
  find $R -name "*.ulg" -delete
fi
find $R -mindepth 2 -type d -path "*/log/*" -empty -delete
