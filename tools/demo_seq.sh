#!/usr/bin/env bash
# Capture sequence during the second illustrative flight: close-ups early, overviews near the end of the mission.
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
D=$J/results/tier_c/demo; L=$D/nominal.log
mkdir -p $D/shots/close_nom $D/shots/over_nom
sleep 45; bash $J/tools/demo_near.sh x500_1 $D/shots/close_nom 3.5
sleep 30; bash $J/tools/demo_near.sh x500_3 $D/shots/close_nom 3.5
while ! grep -q "MISSION END" $L; do
  t=$(grep -o "t=[0-9.]*s" $L | tail -1 | tr -dc '0-9.')
  if [ -n "$t" ] && [ "${t%.*}" -ge 180 ]; then
    bash $J/tools/demo_cam.sh pose 0 -230 150 0 0.62 1.5708 $D/shots/over_nom >/dev/null
    bash $J/tools/demo_cam.sh pose 0 0 330 0 1.5707 1.5708 $D/shots/over_nom >/dev/null
  fi
  sleep 12
done
echo seq done
