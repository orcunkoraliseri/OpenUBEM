#!/usr/bin/env bash
# Direct resumable re-run of the la_centre Phase-E (E-R3-3) pilot.
# Repair job already drained (queue empty), so no wait-wrapper: run the v12
# pipeline directly. It REUSE-harvests the existing cluster sims (line-1007),
# runs bounded verify_and_repair, drops residual within tolerance -> final_dir.
# Turn-surviving (manager bg child); PYTHONUNBUFFERED for live log.
set -u
REPO="C:/Users/o_iseri/Desktop/OpenUBEM"
PY="$REPO/.venv/Scripts/python.exe"
LOG="$REPO/scratchpad/phaseE_er33_la_centre_resume4.log"
FINAL="$REPO/docs/validations/overAll/results/phaseE_er33/la_centre"

echo "==== RERUN4_START $(date) ====" >> "$LOG"
cd "$REPO" || { echo "cd failed" >> "$LOG"; exit 9; }
PYTHONUNBUFFERED=1 OPENUBEM_RECONSTRUCT_SERVICE_LOADS=0 \
  "$PY" scripts/validation/v12_cell_pipeline.py la_centre --output-subdir phaseE_er33 >> "$LOG" 2>&1
RC=$?
echo "==== RERUN4_EXIT rc=$RC $(date) ====" >> "$LOG"

if [ -f "$FINAL/05_results.csv" ]; then
  echo "RERUN4_COMPLETE_OK final_dir populated: $FINAL $(date)" >> "$LOG"
else
  echo "RERUN4_INCOMPLETE final_dir missing 05_results.csv (rc=$RC) $(date)" >> "$LOG"
fi
