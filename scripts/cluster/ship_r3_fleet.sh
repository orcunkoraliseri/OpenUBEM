#!/usr/bin/env bash
# C08 Step 1+2: Pack and ship the R3 fleet (483 IDFs) to Speed cluster.
# Run from local machine after C07 generation is complete.
# Usage: bash scripts/cluster/ship_r3_fleet.sh

set -e

R3_STEP3="/c/Users/o_iseri/AppData/Local/Temp/ubem_boston_r3/step3"
EPW_SRC="/c/Users/o_iseri/AppData/Local/openubem/epw_cache/USA_MA_Boston.994971_TMYx.2011-2025.epw"
STAGE="/c/Users/o_iseri/AppData/Local/Temp/ubem_r3_stage"
REMOTE="o_iseri@speed.encs.concordia.ca"
FLEET_REMOTE="/speed-scratch/o_iseri/openubem/fleets/r3"

echo "[C08] Staging R3 fleet..."
rm -rf "$STAGE"
mkdir -p "$STAGE/idfs" "$STAGE/weather"

cp "$R3_STEP3/idfs/"*.idf "$STAGE/idfs/"
cp "$EPW_SRC" "$STAGE/weather/"

# Write fleet.lst (one osm_id per line, sorted, no extension)
ls "$STAGE/idfs/" | sed 's/\.idf$//' | sort -n > "$STAGE/fleet.lst"
N=$(wc -l < "$STAGE/fleet.lst")
echo "[C08] fleet.lst has $N entries"

echo "[C08] Creating tarball..."
cd "$STAGE"
tar -czf r3.tar.gz idfs weather fleet.lst
echo "[C08] Tarball size: $(du -sh r3.tar.gz | cut -f1)"

echo "[C08] Creating remote fleet dir..."
ssh "$REMOTE" "bash -lc 'mkdir -p ${FLEET_REMOTE}'"

echo "[C08] Uploading tarball (scp)..."
scp "$STAGE/r3.tar.gz" "${REMOTE}:${FLEET_REMOTE}/r3.tar.gz"

echo "[C08] Extracting on cluster login node (tiny tar, login-OK)..."
ssh "$REMOTE" "bash -lc 'cd ${FLEET_REMOTE} && tar -xzf r3.tar.gz && mkdir -p out && rm r3.tar.gz'"

echo "[C08] Verifying IDF count on cluster..."
REMOTE_N=$(ssh "$REMOTE" "bash -lc 'ls ${FLEET_REMOTE}/idfs | wc -l'")
echo "[C08] Remote IDF count: $REMOTE_N (expected $N)"
if [ "$REMOTE_N" != "$N" ]; then
  echo "[C08] ERROR: IDF count mismatch! Expected $N, got $REMOTE_N"
  exit 1
fi

echo "[C08] Fleet shipped OK. Next: submit SLURM array."
echo "[C08] N=$N FLEET_REMOTE=$FLEET_REMOTE"
