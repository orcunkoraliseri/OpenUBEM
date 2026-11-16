#!/usr/bin/env bash
# Session-owned completion waiter (re-armed after /clear). Blocks until the
# 11-cell fan-out writes FANOUT_ALL_DONE, then exits so THIS session is notified
# and can run the T11.6 CP-3 before/after comparison. Event-driven: no active
# job polling; 30-min status-file checks; stall guard; 12h ceiling.
set -u
REPO="C:/Users/o_iseri/Desktop/OpenUBEM"
STATUS="$REPO/scratchpad/fanout_11.status"
FINBASE="$REPO/docs/validations/overAll/results/phaseE_er33"
now() { date +%s; }

for i in $(seq 1 24); do   # 24 * 30min = 12h ceiling
  sleep 1800
  done_n=$(ls -1 "$FINBASE"/*/05_results.csv 2>/dev/null | wc -l)
  if grep -q "FANOUT_ALL_DONE" "$STATUS" 2>/dev/null; then
    echo "AWAIT_COMPLETE done_cells=$done_n $(date)"
    grep "FANOUT_ALL_DONE" "$STATUS" | tail -1
    exit 0
  fi
  st_age=$(( $(now) - $(date -r "$STATUS" +%s 2>/dev/null || echo 0) ))
  echo "check $i: done_cells=$done_n/11 status_age=${st_age}s $(date)"
  if [ "$st_age" -gt 3000 ]; then   # >50min no status write and not all done -> stall
    echo "AWAIT_STALL status idle ${st_age}s (>50min), done=$done_n/11 $(date)"
    exit 2
  fi
done
echo "AWAIT_TIMEOUT 12h ceiling done=$(ls -1 "$FINBASE"/*/05_results.csv 2>/dev/null | wc -l)/11 $(date)"
exit 3
