#!/usr/bin/env bash
# C08 Step 4+5: Fetch R3 cluster simulation results and build manifest.
# Usage: bash scripts/cluster/fetch_r3_results.sh <JOB_ID>
# JOB_ID: SLURM array job ID from submission step.

set -e

JOB_ID="${1:-}"
REMOTE="o_iseri@speed.encs.concordia.ca"
FLEET_REMOTE="/speed-scratch/o_iseri/openubem/fleets/r3"
LOCAL_OUT="/c/Users/o_iseri/AppData/Local/Temp/ubem_boston_r3/sim"
FLEET_LST="/c/Users/o_iseri/AppData/Local/Temp/ubem_boston_r3/step3/idfs"
EPW_PATH="C:\\Users\\o_iseri\\AppData\\Local\\openubem\\epw_cache\\USA_MA_Boston.994971_TMYx.2011-2025.epw"
IDF_DIR="/c/Users/o_iseri/AppData/Local/Temp/ubem_boston_r3/step3/idfs"
MANIFEST_OUT="/c/Users/o_iseri/AppData/Local/Temp/ubem_boston_r3/04_simulation_manifest.parquet"
REPO="/c/Users/o_iseri/Desktop/OpenUBEM"

mkdir -p "$LOCAL_OUT"

# Build list of osm_ids from fleet.lst on cluster
echo "[C08-fetch] Fetching fleet.lst from cluster..."
ssh "$REMOTE" "bash -lc 'cat ${FLEET_REMOTE}/fleet.lst'" > /tmp/r3_fleet.lst
N=$(wc -l < /tmp/r3_fleet.lst)
echo "[C08-fetch] $N buildings to fetch"

echo "[C08-fetch] Fetching per-building results..."
SUCCESS=0
FAIL=0
while IFS= read -r OSM_ID; do
    OSM_ID=$(echo "$OSM_ID" | tr -d '[:space:]')
    [ -z "$OSM_ID" ] && continue
    mkdir -p "${LOCAL_OUT}/${OSM_ID}"
    for F in eplusout.sql eplusout.err eplusout.end; do
        scp -q "${REMOTE}:${FLEET_REMOTE}/out/${OSM_ID}/${F}" \
            "${LOCAL_OUT}/${OSM_ID}/${F}" 2>/dev/null || true
    done
    if [ -f "${LOCAL_OUT}/${OSM_ID}/eplusout.end" ] && grep -q "Completed Successfully" "${LOCAL_OUT}/${OSM_ID}/eplusout.end" 2>/dev/null; then
        SUCCESS=$((SUCCESS+1))
    else
        FAIL=$((FAIL+1))
        echo "  FAILED: $OSM_ID"
    fi
done < /tmp/r3_fleet.lst

echo "[C08-fetch] Fetch complete: $SUCCESS success, $FAIL failed (total $N)"

# Copy fleet.lst to sim dir for manifest adapter
cp /tmp/r3_fleet.lst "${LOCAL_OUT}/fleet.lst"

echo "[C08-fetch] Building manifest..."
cd "$REPO"
python scripts/cluster/make_manifest_from_cluster.py \
    "${LOCAL_OUT}" \
    "${MANIFEST_OUT}" \
    --idf-dir "${IDF_DIR}" \
    --epw "${EPW_PATH}" \
    ${JOB_ID:+--job-id "${JOB_ID}"}

echo "[C08-fetch] Manifest written: $MANIFEST_OUT"
echo "[C08-fetch] Cleaning remote out/ dir..."
ssh "$REMOTE" "bash -lc 'rm -rf ${FLEET_REMOTE}/out'"
echo "[C08-fetch] Done."
