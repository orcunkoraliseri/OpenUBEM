#!/usr/bin/env bash
# Progress + stall watcher for the 11-cell fan-out. With PYTHONUNBUFFERED=1 the
# per-cell logs flush live (poll lines every ~90s), so newest mtime across all
# per-cell logs + the status file is a true liveness signal. Fires on
# FANOUT_ALL_DONE, or a genuine stall (no log/status write in >40 min AND not
# all done). 40-min threshold clears the longest inter-write gap (cluster waits
# still emit ~90s poll lines to the unbuffered log). 16h ceiling.
set -u
REPO="C:/Users/o_iseri/Desktop/OpenUBEM"
STATUS="$REPO/scratchpad/fanout_11.status"
FINBASE="$REPO/docs/validations/overAll/results/phaseE_er33"
OUT="$REPO/scratchpad/watch_fanout_11.status"
SCR="$REPO/scratchpad"

echo "WATCH_FANOUT_ARMED $(date)" > "$OUT"
now() { date +%s; }

for i in $(seq 1 64); do   # 64 * 15min = 16h
  sleep 900
  done_n=$(ls -1 "$FINBASE"/*/05_results.csv 2>/dev/null | wc -l)
  if grep -q "FANOUT_ALL_DONE" "$STATUS" 2>/dev/null; then
    echo "WATCH_FANOUT_COMPLETE done_cells=$done_n $(date)" >> "$OUT"
    grep "FANOUT_ALL_DONE" "$STATUS" | tail -1 >> "$OUT"; exit 0
  fi
  newest=$(find "$SCR" -maxdepth 1 -name 'phaseE_er33_*.log' -printf '%T@\n' 2>/dev/null; \
           find "$STATUS" -printf '%T@\n' 2>/dev/null)
  newest=$(printf '%s\n' $newest | sort -n | tail -1)
  if [ -n "$newest" ]; then
    age=$(( $(now) - ${newest%.*} ))
    echo "  poll $i: done_cells=$done_n/11 newest_log_age=${age}s $(date)" >> "$OUT"
    if [ "$age" -gt 2400 ]; then
      echo "WATCH_FANOUT_STALL logs idle ${age}s (>40min), done=$done_n/11 $(date)" >> "$OUT"; exit 0
    fi
  else
    echo "  poll $i: no logs yet, done_cells=$done_n $(date)" >> "$OUT"
  fi
done
echo "WATCH_FANOUT_TIMEOUT 16h ceiling done=$(ls -1 "$FINBASE"/*/05_results.csv 2>/dev/null | wc -l)/11 $(date)" >> "$OUT"
