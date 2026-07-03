#!/usr/bin/env bash
# Event-driven completion watcher for detached resume5.
# Exits (notifies) on SUCCESS (final_dir/05_results.csv), pipeline EXIT marker,
# or a genuine work-dir STALL (sim_out mtime idle > 50 min AND no final_dir).
# Stall keyed on WORK-DIR mtime, never the buffered stdout log.
set -u
REPO="C:/Users/o_iseri/Desktop/OpenUBEM"
LOG="$REPO/scratchpad/phaseE_er33_la_centre_resume5.log"
WORK="C:/Users/o_iseri/AppData/Local/Temp/ubem_validation/phaseE_er33/la_centre"
FINAL="$REPO/docs/validations/overAll/results/phaseE_er33/la_centre"
OUT="$REPO/scratchpad/watch_la_centre_resume5.status"

echo "WATCH_ARMED $(date)" > "$OUT"
now() { date +%s; }

for i in $(seq 1 96); do   # 96 * 15min = 24h ceiling
  sleep 900
  if [ -f "$FINAL/05_results.csv" ]; then
    echo "WATCH_SUCCESS final_dir populated $(date)" >> "$OUT"; exit 0
  fi
  if grep -q "RERUN5_EXIT" "$LOG" 2>/dev/null; then
    echo "WATCH_PIPELINE_EXIT (see resume5 log) $(date)" >> "$OUT"; exit 0
  fi
  newest=$(find "$WORK" -type f -printf '%T@\n' 2>/dev/null | sort -n | tail -1)
  if [ -n "$newest" ]; then
    age=$(( $(now) - ${newest%.*} ))
    echo "  poll $i: work_newest_age=${age}s $(date)" >> "$OUT"
    if [ "$age" -gt 3000 ]; then
      echo "WATCH_STALL work-dir idle ${age}s (>50min), no final_dir $(date)" >> "$OUT"; exit 0
    fi
  else
    echo "  poll $i: work dir empty/unreadable $(date)" >> "$OUT"
  fi
done
echo "WATCH_TIMEOUT 24h ceiling $(date)" >> "$OUT"
