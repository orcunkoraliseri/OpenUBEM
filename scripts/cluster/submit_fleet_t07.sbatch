#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --job-name=openubem_t07
#SBATCH --output=/speed-scratch/o_iseri/openubem/fleets/%x_%A_%a.log

# T07 fleet re-simulation. Multi-weather variant of submit_fleet_t08.sbatch:
# fleet.lst carries one "stem<TAB>epw_basename" line per array task, since
# this fleet spans 12 climate cells (multiple EPWs), not a single EPW.
#
# Usage: sbatch --array=1-N%32 --time=7-00:00:00 --export=FLEET_DIR=<path> submit_fleet_t07.sbatch
# FLEET_DIR must contain: idfs/<stem>.idf, weather/<epw...>, fleet.lst

set -e

if [ -z "$FLEET_DIR" ]; then
    echo "ERROR: FLEET_DIR not set" >&2
    exit 1
fi

LINE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "${FLEET_DIR}/fleet.lst" | tr -d '\r')
if [ -z "$LINE" ]; then
    echo "ERROR: no line at ${SLURM_ARRAY_TASK_ID} of fleet.lst" >&2
    exit 1
fi
OSM_STEM=$(echo "$LINE" | cut -f1)
EPW_NAME=$(echo "$LINE" | cut -f2)
if [ -z "$OSM_STEM" ] || [ -z "$EPW_NAME" ]; then
    echo "ERROR: malformed fleet.lst line at ${SLURM_ARRAY_TASK_ID}: '${LINE}'" >&2
    exit 1
fi

EPW="${FLEET_DIR}/weather/${EPW_NAME}"
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
