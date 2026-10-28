#!/usr/bin/env bash
# Batch of headless tier C missions: every (profile, seed, method) combination, one mission at a time.
#   bash $J/journal_ros/run_batch.sh <name> "<profiles>" "<seeds>" "<methods>" [kappa_b] [trigger] [speed] [exec]
#   bash $J/journal_ros/run_batch.sh pilot_c "arrivals failures" "0 1" "alns_fixed@40 anytime" 10 event 1
# Results: results/tier_c/<name>/<scenario>_<method>.json (existing files are skipped -> resumable).
# Order: seeds outer, methods inner, so that methods are interleaved in time (same machine conditions).
set -uo pipefail
J=/mnt/d/paper/TAIMMA_2027/AnytimeSwarm/AnytimeSwarm_Journal
NAME=$1; PROFILES=$2; SEEDS=$3; METHODS=$4; KAPPA=${5:-10}; TRIGGER=${6:-event}; SPEED=${7:-1}; EXEC=${8:-nominal}
OUTD=$J/results/tier_c/$NAME
mkdir -p "$OUTD"
echo "[batch] $NAME profiles=($PROFILES) seeds=($SEEDS) methods=($METHODS) kappa_B=$KAPPA trigger=$TRIGGER speed=$SPEED exec=$EXEC"
for s in $SEEDS; do
  for p in $PROFILES; do
    for m in $METHODS; do
      f="$OUTD/gz-$p-${s}_${m}.json"
      [ -f "$f" ] && continue
      for attempt in 1 2; do
        timeout 1500 bash $J/journal_ros/run_mission.sh --profile "$p" --seed "$s" --method "$m" --kappa-b "$KAPPA" \
          --trigger "$TRIGGER" --speed "$SPEED" --exec "$EXEC" --out "$f" > "$OUTD/last_run.log" 2>&1
        if [ -f "$f" ]; then
          echo "[batch] $(date -Is) ok  gz-$p-$s $m: $(grep -o 'MISSION END.*utility=[0-9.]*' "$OUTD/last_run.log" | tail -1)"
          break
        fi
        echo "[batch] $(date -Is) FAIL gz-$p-$s $m (attempt $attempt), see logs"
        cp "$OUTD/last_run.log" "$OUTD/fail_gz-$p-${s}_${m}_$attempt.log"
      done
    done
  done
done
echo "[batch] $NAME done"
