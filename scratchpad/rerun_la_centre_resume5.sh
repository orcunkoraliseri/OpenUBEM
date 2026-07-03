#!/usr/bin/env bash
# Resume5: la_centre Phase-E (E-R3-3) pilot, AFTER fixing the reroute-aware
# monkey-patch lambda signature bug (v12_cell_pipeline.py:520 now accepts the
# 4th resolution_mode arg added by commit e063865). Main fleet's 226 cluster
# sims are complete -> REUSE-harvest (line 1007) skips re-submit; pipeline goes
# straight to bounded verify_and_repair -> fixed reroute -> final_dir.
# Turn-surviving (manager bg child + nohup); PYTHONUNBUFFERED for live log.
set -u
REPO="C:/Users/o_iseri/Desktop/OpenUBEM"
PY="$REPO/.venv/Scripts/python.exe"
LOG="$REPO/scratchpad/phaseE_er33_la_centre_resume5.log"
FINAL="$REPO/docs/validations/overAll/results/phaseE_er33/la_centre"

echo "==== RERUN5_START $(date) ====" >> "$LOG"
cd "$REPO" || { echo "cd failed" >> "$LOG"; exit 9; }
PYTHONUNBUFFERED=1 OPENUBEM_RECONSTRUCT_SERVICE_LOADS=0 \
  "$PY" scripts/validation/v12_cell_pipeline.py la_centre --output-subdir phaseE_er33 >> "$LOG" 2>&1
RC=$?
echo "==== RERUN5_EXIT rc=$RC $(date) ====" >> "$LOG"

if [ -f "$FINAL/05_results.csv" ]; then
  echo "RERUN5_COMPLETE_OK final_dir populated: $FINAL $(date)" >> "$LOG"
else
  echo "RERUN5_INCOMPLETE final_dir missing 05_results.csv (rc=$RC) $(date)" >> "$LOG"
fi
