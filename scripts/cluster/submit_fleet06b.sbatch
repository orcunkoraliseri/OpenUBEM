#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --job-name=openubem_fleet06b
#SBATCH --output=/speed-scratch/o_iseri/openubem/fleets/%x_%A_%a.log

# FLEET-06b (techtransfer block-6 plan) -- one array task = one (cell_name, building_id)
# case from the 65,112-row scenario manifest (8 cells x 8,139 buildings). Output is
# partitioned per cell so FLEET-06c can harvest cell-by-cell without ambiguity.
# fleet.lst carries one "cell_name<TAB>stem<TAB>epw_basename" line per array task.
#
# Speed's SLURM caps a single array job at MaxArraySize=10001, so the 65,112-case fleet
# is split (per docs/docs_ACTIVE/TechTransfer/implementation/PLAN_techtransfer-block6-2026-09-18.md
# section 2d) into 7 chained array jobs, each reading its own contiguous slice file
# (FLEET_LST, default "fleet.lst" for a single-job/back-compat run).
#
# Usage: sbatch --array=1-N%32 --time=7-00:00:00 --export=FLEET_DIR=<path>,FLEET_LST=<slice file> submit_fleet06b.sbatch
# FLEET_DIR must contain: idfs/<cell_name>/<stem>.idf, weather/<epw...>, <FLEET_LST>

set -e

if [ -z "$FLEET_DIR" ]; then
    echo "ERROR: FLEET_DIR not set" >&2
    exit 1
fi
FLEET_LST="${FLEET_LST:-fleet.lst}"

LINE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "${FLEET_DIR}/${FLEET_LST}" | tr -d '\r')
if [ -z "$LINE" ]; then
    echo "ERROR: no line at ${SLURM_ARRAY_TASK_ID} of ${FLEET_LST}" >&2
    exit 1
fi
CELL_NAME=$(echo "$LINE" | cut -f1)
OSM_STEM=$(echo "$LINE" | cut -f2)
EPW_NAME=$(echo "$LINE" | cut -f3)
if [ -z "$CELL_NAME" ] || [ -z "$OSM_STEM" ] || [ -z "$EPW_NAME" ]; then
    echo "ERROR: malformed ${FLEET_LST} line at ${SLURM_ARRAY_TASK_ID}: '${LINE}'" >&2
    exit 1
fi

EPW="${FLEET_DIR}/weather/${EPW_NAME}"
IDF="${FLEET_DIR}/idfs/${CELL_NAME}/${OSM_STEM}.idf"
OUTDIR="${FLEET_DIR}/out/${CELL_NAME}/${OSM_STEM}"
EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-*Ubuntu20* 2>/dev/null | head -1)
[ -z "$EP_DIR" ] && EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-* | head -1)

mkdir -p "$OUTDIR"
cd "$OUTDIR"

echo "Task ${SLURM_ARRAY_TASK_ID}: cell=${CELL_NAME} stem=${OSM_STEM}"
echo "EnergyPlus: ${EP_DIR}/energyplus"
echo "IDF: $IDF"
echo "EPW: $EPW"
echo "OUTDIR: $OUTDIR"
"${EP_DIR}/energyplus" --version > "${OUTDIR}/energyplus_version.txt" 2>&1 || true
{
    echo "hostname=$(hostname)"
    echo "kernel=$(uname -sr)"
} > "${OUTDIR}/platform.txt"

cp "${EP_DIR}/Energy+.idd" "$OUTDIR/"
cp "$IDF" "$OUTDIR/in.idf"
"${EP_DIR}/ExpandObjects"
if [ -f "$OUTDIR/expanded.idf" ]; then
    RUN_IDF="$OUTDIR/expanded.idf"
else
    RUN_IDF="$OUTDIR/in.idf"
fi
echo "Running EnergyPlus on: $RUN_IDF"
set +e
"${EP_DIR}/energyplus" -w "$EPW" -d "$OUTDIR" "$RUN_IDF"
RC=$?
set -e
echo $RC > "${OUTDIR}/task.rc"
echo "Task ${SLURM_ARRAY_TASK_ID} finished with rc=${RC}"

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

echo "Task ${SLURM_ARRAY_TASK_ID}: cleanup done, kept eio+sql+end+err"
exit $RC
