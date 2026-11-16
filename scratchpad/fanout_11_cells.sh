#!/usr/bin/env bash
# T11 fan-out: run the remaining 11 Phase-E (E-R3-3) cells to phaseE_er33.
# Sequential (no local CPU / cluster-array contention), idempotent (skips any
# cell whose final_dir already has 05_results.csv -> resumable), continue-on-
# failure (one bad cell never blocks the rest). Turn-surviving (manager bg task).
# Reroute lambda bug fixed (v12:520) so any cell reaching reroute completes.
# Ordered small->large by seed gpkg size so a systemic issue surfaces cheaply.
set -u
REPO="C:/Users/o_iseri/Desktop/OpenUBEM"
PY="$REPO/.venv/Scripts/python.exe"
FINBASE="$REPO/docs/validations/overAll/results/phaseE_er33"
STATUS="$REPO/scratchpad/fanout_11.status"

CELLS=(la_rural nyc_rural austin_rural austin_suburban austin_centre austin_urban la_urban nyc_centre nyc_suburban la_suburban nyc_urban)

echo "==== FANOUT_START $(date) ====" >> "$STATUS"
cd "$REPO" || { echo "FANOUT_CD_FAIL $(date)" >> "$STATUS"; exit 9; }

ok=0; fail=0; skip=0
for cell in "${CELLS[@]}"; do
  if [ -f "$FINBASE/$cell/05_results.csv" ]; then
    echo "SKIP $cell (already complete) $(date)" >> "$STATUS"; skip=$((skip+1)); continue
  fi
  log="$REPO/scratchpad/phaseE_er33_${cell}.log"
  echo "CELL_START $cell $(date)" >> "$STATUS"
  echo "==== $cell START $(date) ====" >> "$log"
  PYTHONUNBUFFERED=1 OPENUBEM_RECONSTRUCT_SERVICE_LOADS=0 \
    "$PY" scripts/validation/v12_cell_pipeline.py "$cell" --output-subdir phaseE_er33 >> "$log" 2>&1
  rc=$?
  echo "==== $cell EXIT rc=$rc $(date) ====" >> "$log"
  if [ -f "$FINBASE/$cell/05_results.csv" ]; then
    echo "CELL_DONE $cell rc=$rc final_dir OK $(date)" >> "$STATUS"; ok=$((ok+1))
  else
    echo "CELL_FAIL $cell rc=$rc no final_dir $(date)" >> "$STATUS"; fail=$((fail+1))
  fi
done

echo "==== FANOUT_ALL_DONE ok=$ok fail=$fail skip=$skip $(date) ====" >> "$STATUS"
