#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --job-name=paper_hourly_rerun
#SBATCH --output=/speed-scratch/o_iseri/openubem/fleets/paper_hourly_rerun_2026-10-21/logs/%x_%A_%a.log

set -euo pipefail

ROOT="${HOURLY_ROOT:-/speed-scratch/o_iseri/openubem/fleets/paper_hourly_rerun_2026-10-21}"
PY="${HOURLY_PY:-/speed-scratch/o_iseri/envs/openubem_eu22/bin/python}"
I="${SLURM_ARRAY_TASK_ID:?SLURM_ARRAY_TASK_ID not set}"

ROW=$(sed -n "$((I + 1))p" "$ROOT/case_list.csv" | tr -d '\r')
if [ -z "$ROW" ]; then
    echo "ERROR: no row for task $I in $ROOT/case_list.csv" >&2
    exit 1
fi
TASK=$(echo "$ROW" | cut -d, -f1)
STEM=$(echo "$ROW" | cut -d, -f5)
SRC_IDF=$(echo "$ROW" | cut -d, -f7)
EPW_NAME=$(echo "$ROW" | cut -d, -f8)
if [ "$TASK" != "$I" ] || [ -z "$STEM" ] || [ -z "$SRC_IDF" ] || [ -z "$EPW_NAME" ]; then
    echo "ERROR: malformed row for task $I: '$ROW'" >&2
    exit 1
fi

EPW="$(dirname "$(dirname "$SRC_IDF")")/weather/${EPW_NAME}"
for f in "$SRC_IDF" "$EPW" "$ROOT/add_hourly_meters.py" "$ROOT/hourly.py"; do
    if [ ! -f "$f" ]; then
        echo "ERROR: missing $f" >&2
        exit 1
    fi
done

OUTDIR="$ROOT/out/${STEM}"
EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-*Ubuntu20* 2>/dev/null | head -1)
[ -z "$EP_DIR" ] && EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-* | head -1)

mkdir -p "$OUTDIR"
cd "$OUTDIR"

echo "Task ${I}: stem=${STEM}"
echo "EnergyPlus: ${EP_DIR}/energyplus"
echo "IDF: $SRC_IDF"
echo "EPW: $EPW"
echo "OUTDIR: $OUTDIR"
"${EP_DIR}/energyplus" --version > "${OUTDIR}/energyplus_version.txt" 2>&1 || true
{
    echo "hostname=$(hostname)"
    echo "kernel=$(uname -sr)"
} > "${OUTDIR}/platform.txt"

cp "${EP_DIR}/Energy+.idd" "$OUTDIR/"
cp "$SRC_IDF" "$OUTDIR/original.idf"
"$PY" "$ROOT/add_hourly_meters.py" "$OUTDIR/original.idf" "$OUTDIR/in.idf"
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
echo "Task ${I} finished with rc=${RC}"

if [ "$RC" -eq 0 ] && [ -f "$OUTDIR/eplusout.sql" ]; then
    if "$PY" "$ROOT/hourly.py" extract "$OUTDIR/eplusout.sql" "$ROOT/out/${STEM}.csv.gz"; then
        echo "Task ${I}: hourly extract done"
    else
        echo "ERROR: hourly extract failed" >&2
        RC=3
    fi
else
    echo "ERROR: no usable eplusout.sql (rc=${RC})" >&2
    if [ "$RC" -eq 0 ]; then
        RC=4
    fi
fi

rm -f "$OUTDIR"/*.eso \
      "$OUTDIR"/*.mtd \
      "$OUTDIR"/*.rdd \
      "$OUTDIR"/*.mdd \
      "$OUTDIR"/*.htm \
      "$OUTDIR"/*.tab \
      "$OUTDIR"/*.csv \
      "$OUTDIR"/original.idf \
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

echo "Task ${I}: cleanup done, kept sql, err, eio, end"
exit $RC
