#!/usr/bin/env bash
# Durable completion of the la_centre Phase-E (E-R3-3) pilot.
# Manager-armed (survives agent turns; notifies on exit). Waits for the running
# cluster repair job to drain (avoid repair-dir collision), then does the
# resumable re-run to completion. Unbuffered log so progress is live.
set -u
REPO="C:/Users/o_iseri/Desktop/OpenUBEM"
PY="$REPO/.venv/Scripts/python.exe"
HOST="o_iseri@speed.encs.concordia.ca"
LOG="$REPO/scratchpad/phaseE_er33_la_centre_resume3.log"
FINAL="$REPO/docs/validations/overAll/results/phaseE_er33/la_centre"

echo "==== DURABLE_COMPLETE_START $(date) ====" >> "$LOG"

# 1) Wait for the repair array (openubem_la_centre_repair) to leave the queue.
for i in $(seq 1 36); do
  n=$(ssh -o BatchMode=yes -o ConnectTimeout=20 "$HOST" \
        "squeue -u o_iseri -h -n openubem_la_centre_repair 2>/dev/null | wc -l" 2>/dev/null)
  rc=$?
  echo "  wait_repair poll $i: rc=$rc count='$n' $(date)" >> "$LOG"
  if [ "$rc" -eq 0 ] && [ "$n" = "0" ]; then
    echo "  repair job drained; proceeding to re-run. $(date)" >> "$LOG"
    break
  fi
  sleep 300
done

# 2) Durable resumable re-run to completion (line-1007 reuse skips main re-sim;
#    verify_and_repair runs its bounded repair/reroute passes, then step5 drops
#    any residual failure within tolerance -> final_dir).
echo "==== RERUN_START $(date) ====" >> "$LOG"
cd "$REPO" || { echo "cd failed" >> "$LOG"; exit 9; }
PYTHONUNBUFFERED=1 OPENUBEM_RECONSTRUCT_SERVICE_LOADS=0 \
  "$PY" scripts/validation/v12_cell_pipeline.py la_centre --output-subdir phaseE_er33 >> "$LOG" 2>&1
RC=$?
echo "==== RERUN_EXIT rc=$RC $(date) ====" >> "$LOG"

if [ -f "$FINAL/05_results.csv" ]; then
  echo "DURABLE_COMPLETE_OK final_dir populated: $FINAL $(date)" >> "$LOG"
else
  echo "DURABLE_COMPLETE_INCOMPLETE final_dir missing 05_results.csv (rc=$RC) $(date)" >> "$LOG"
fi
