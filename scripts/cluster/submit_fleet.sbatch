#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --time=01:30:00
#SBATCH --job-name=openubem_fleet
#SBATCH --output=/speed-scratch/o_iseri/openubem/fleets/%x_%A_%a.log

# Usage: sbatch --array=1-N%8 --export=FLEET_DIR=<path> submit_fleet.sbatch
# FLEET_DIR must contain: idfs/<osm_id>.idf, weather/<epw>, fleet.lst

set -e

if [ -z "$FLEET_DIR" ]; then
    echo "ERROR: FLEET_DIR not set" >&2
    exit 1
fi

OSM_ID=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "${FLEET_DIR}/fleet.lst")
if [ -z "$OSM_ID" ]; then
    echo "ERROR: no osm_id at line ${SLURM_ARRAY_TASK_ID} of fleet.lst" >&2
    exit 1
fi

EPW=$(ls "${FLEET_DIR}/weather/"*.epw | head -1)
IDF="${FLEET_DIR}/idfs/${OSM_ID}.idf"
OUTDIR="${FLEET_DIR}/out/${OSM_ID}"
EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-*Ubuntu20* 2>/dev/null | head -1)
[ -z "$EP_DIR" ] && EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-* | head -1)

mkdir -p "$OUTDIR"
cd "$OUTDIR"

echo "Task ${SLURM_ARRAY_TASK_ID}: osm_id=${OSM_ID}"
echo "EnergyPlus: ${EP_DIR}/energyplus"
echo "IDF: $IDF"
echo "EPW: $EPW"
echo "OUTDIR: $OUTDIR"

# Copy IDD and run ExpandObjects in OUTDIR (required for HVACTemplate objects)
cp "${EP_DIR}/Energy+.idd" "$OUTDIR/"
cp "$IDF" "$OUTDIR/in.idf"
"${EP_DIR}/ExpandObjects"
# ExpandObjects writes expanded.idf if HVACTemplate objects present, else in.idf unchanged
if [ -f "$OUTDIR/expanded.idf" ]; then
    RUN_IDF="$OUTDIR/expanded.idf"
else
    RUN_IDF="$OUTDIR/in.idf"
fi
echo "Running EnergyPlus on: $RUN_IDF"
"${EP_DIR}/energyplus" -w "$EPW" -d "$OUTDIR" "$RUN_IDF"
RC=$?
echo $RC > "${OUTDIR}/task.rc"
echo "Task ${SLURM_ARRAY_TASK_ID} finished with rc=${RC}"
exit $RC
