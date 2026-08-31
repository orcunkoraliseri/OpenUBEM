#!/usr/bin/env bash
# EU-11: Pack and ship one S2 district fleet to Speed cluster.
# Usage: bash scripts/cluster/ship_eu11_fleet.sh <DISTRICT>
# DISTRICT one of: ES-MAD-BERRUGUETE, FR-LYO-HAUTCOEURPENTES, GB-LDN-STDUNSTANS

set -e

DISTRICT="$1"
if [ -z "$DISTRICT" ]; then
  echo "Usage: $0 <DISTRICT>" >&2
  exit 1
fi

LOCAL_DIR="/c/Users/o_iseri/Desktop/OpenUBEM/openubem/outputs/eu_evidence/EU-11/${DISTRICT}"
if [ ! -d "$LOCAL_DIR" ]; then
  echo "ERROR: local district dir not found: $LOCAL_DIR" >&2
  exit 1
fi

STAGE="/c/Users/o_iseri/AppData/Local/Temp/ubem_eu11_stage_${DISTRICT}"
REMOTE="o_iseri@speed.encs.concordia.ca"
FLEET_REMOTE="/speed-scratch/o_iseri/fleets/EU11_${DISTRICT}"

echo "[EU-11] Staging $DISTRICT..."
rm -rf "$STAGE"
mkdir -p "$STAGE/idfs" "$STAGE/weather" "$STAGE/schedules"

cp "$LOCAL_DIR/idfs/"*.idf "$STAGE/idfs/"
cp "$LOCAL_DIR/weather/"*.epw "$STAGE/weather/"
cp "$LOCAL_DIR/fleet.lst" "$STAGE/fleet.lst"
cp -r "$LOCAL_DIR/schedules/"* "$STAGE/schedules/"

N=$(wc -l < "$STAGE/fleet.lst")
NIDF=$(ls "$STAGE/idfs" | wc -l)
echo "[EU-11] fleet.lst has $N entries, $NIDF IDFs staged"
if [ "$N" != "$NIDF" ]; then
  echo "[EU-11] ERROR: fleet.lst count ($N) != IDF count ($NIDF)" >&2
  exit 1
fi

echo "[EU-11] Creating tarball..."
cd "$STAGE"
tar -czf eu11.tar.gz idfs weather schedules fleet.lst
echo "[EU-11] Tarball size: $(du -sh eu11.tar.gz | cut -f1)"

echo "[EU-11] Creating remote fleet dir..."
ssh "$REMOTE" "bash -lc 'mkdir -p ${FLEET_REMOTE}'"

echo "[EU-11] Uploading tarball (scp)..."
scp "$STAGE/eu11.tar.gz" "${REMOTE}:${FLEET_REMOTE}/eu11.tar.gz"

echo "[EU-11] Extracting on cluster login node (tiny tar, login-OK)..."
ssh "$REMOTE" "bash -lc 'cd ${FLEET_REMOTE} && tar -xzf eu11.tar.gz && mkdir -p out && rm eu11.tar.gz'"

echo "[EU-11] Verifying IDF count on cluster..."
REMOTE_N=$(ssh "$REMOTE" "bash -lc 'ls ${FLEET_REMOTE}/idfs | wc -l'")
echo "[EU-11] Remote IDF count: $REMOTE_N (expected $N)"
if [ "$REMOTE_N" != "$N" ]; then
  echo "[EU-11] ERROR: IDF count mismatch! Expected $N, got $REMOTE_N"
  exit 1
fi

echo "[EU-11] Fleet shipped OK. Next: submit SLURM array."
echo "[EU-11] DISTRICT=$DISTRICT N=$N FLEET_REMOTE=$FLEET_REMOTE"
