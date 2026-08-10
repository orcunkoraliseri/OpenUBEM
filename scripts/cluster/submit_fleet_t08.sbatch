#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --time=02:00:00
#SBATCH --job-name=openubem_t08
#SBATCH --output=/speed-scratch/o_iseri/openubem/fleets/%x_%A_%a.log

# T08 variant of submit_fleet.sbatch.
# Same simulation logic; after E+ completes, deletes all non-essential output files
# (*.eso, *.mtd, *.rdd, *.mdd, *.htm, table files) to keep cluster storage bounded.
# Keeps: eplusout.eio (simulated floor area), eplusout.sql (results),
# eplusout.end (completion marker), eplusout.err (Fatal check).
#
# Usage: sbatch --array=1-N%16 --export=FLEET_DIR=<path> submit_fleet_t08.sbatch
# FLEET_DIR must contain: idfs/<stem>.idf, weather/<epw>, fleet.lst

set -e

if [ -z "$FLEET_DIR" ]; then
    echo "ERROR: FLEET_DIR not set" >&2
    exit 1
fi

OSM_STEM=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "${FLEET_DIR}/fleet.lst")
if [ -z "$OSM_STEM" ]; then
    echo "ERROR: no stem at line ${SLURM_ARRAY_TASK_ID} of fleet.lst" >&2
    exit 1
fi

EPW=$(ls "${FLEET_DIR}/weather/"*.epw | head -1)
IDF="${FLEET_DIR}/idfs/${OSM_STEM}.idf"
OUTDIR="${FLEET_DIR}/out/${OSM_STEM}"
EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-*Ubuntu20* 2>/dev/null | head -1)
[ -z "$EP_DIR" ] && EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-* | head -1)

mkdir -p "$OUTDIR"
cd "$OUTDIR"

echo "Task ${SLURM_ARRAY_TASK_ID}: stem=${OSM_STEM}"
echo "EnergyPlus: ${EP_DIR}/energyplus"
echo "IDF: $IDF"
echo "EPW: $EPW"
echo "OUTDIR: $OUTDIR"

# Copy IDD and run ExpandObjects (required for HVACTemplate objects)
cp "${EP_DIR}/Energy+.idd" "$OUTDIR/"
cp "$IDF" "$OUTDIR/in.idf"
"${EP_DIR}/ExpandObjects"
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

# T08 output trimming: keep only SQL + completion + error files; delete bulk output.
# This is critical for fast_zone city passes (>800 GB untrimmed per city).
rm -f "$OUTDIR"/*.eso \
      "$OUTDIR"/*.mtd \
      "$OUTDIR"/*.rdd \
      "$OUTDIR"/*.mdd \
      "$OUTDIR"/*.htm \
      "$OUTDIR"/*.tab \
      "$OUTDIR"/*.csv \
      "$OUTDIR"/in.idf \
      "$OUTDIR"/expanded.idf \
      "$OUTDIR"/Energy+.idd \
      "$OUTDIR"/eplusout.dxf \
      "$OUTDIR"/eplusout.audit \
      "$OUTDIR"/eplusout.bnd \
      "$OUTDIR"/eplusout.dbg \
      "$OUTDIR"/eplusout.sln \
      "$OUTDIR"/eplusout.rvaudit \
      "$OUTDIR"/eplusmtr.* \
      "$OUTDIR"/eplusout.mtr 2>/dev/null || true
# Kept: eplusout.eio, eplusout.sql, eplusout.end, eplusout.err, task.rc

echo "Task ${SLURM_ARRAY_TASK_ID}: cleanup done, kept eio+sql+end+err"
exit $RC
