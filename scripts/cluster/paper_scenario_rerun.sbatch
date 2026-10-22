#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --job-name=paper_scenario_rerun
#SBATCH --output=/speed-scratch/o_iseri/openubem/fleets/paper_scenario_rerun_2026-10-21/logs/%x_%A_%a.log

set -euo pipefail

ROOT="${SCENARIO_ROOT:-/speed-scratch/o_iseri/openubem/fleets/paper_scenario_rerun_2026-10-21}"
PY="${SCENARIO_PY:-/speed-scratch/o_iseri/envs/openubem_eu22/bin/python}"
WAVE="${WAVE:?WAVE not set (sbatch --export=ALL,WAVE=<k>)}"
I="${SLURM_ARRAY_TASK_ID:?SLURM_ARRAY_TASK_ID not set}"

LINE=$(awk -F, -v w="$WAVE" -v t="$I" '
    NR==1 { for (i = 1; i <= NF; i++) h[$i] = i; next }
    { gsub(/\r/, "") }
    ($h["wave"] == w && $h["wave_task"] == t) {
        print $h["cell"] "\t" $h["osm_id"] "\t" $h["stem"] "\t" $h["archetype"] "\t" $h["idf_path"] "\t" $h["epw_name"] "\t" $h["floor_area_m2"]
        exit
    }' "$ROOT/case_list.csv")
if [ -z "$LINE" ]; then
    echo "ERROR: no row for wave $WAVE task $I in $ROOT/case_list.csv" >&2
    exit 1
fi
IFS=$'\t' read -r CELL OSM_ID STEM ARCH SRC_IDF EPW_NAME FA <<< "$LINE"
if [ -z "$CELL" ] || [ -z "$OSM_ID" ] || [ -z "$STEM" ] || [ -z "$ARCH" ] || [ -z "$SRC_IDF" ] || [ -z "$EPW_NAME" ] || [ -z "$FA" ]; then
    echo "ERROR: malformed row for wave $WAVE task $I: '$LINE'" >&2
    exit 1
fi

EPW="$(dirname "$(dirname "$SRC_IDF")")/weather/${EPW_NAME}"
for f in "$SRC_IDF" "$EPW" "$ROOT/scenario_build.py" "$ROOT/openubem/__init__.py"; do
    if [ ! -f "$f" ]; then
        echo "ERROR: missing $f" >&2
        exit 1
    fi
done

OUTDIR="$ROOT/out/${CELL}/${STEM}"
EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-*Ubuntu20* 2>/dev/null | head -1)
[ -z "$EP_DIR" ] && EP_DIR=$(ls -d /speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-* | head -1)

mkdir -p "$OUTDIR"
cd "$OUTDIR"
rm -f "$OUTDIR/UNCHANGED" "$OUTDIR/row.csv" "$OUTDIR/status.csv" "$OUTDIR/task.rc"

echo "Task ${I} wave ${WAVE}: cell=${CELL} stem=${STEM} archetype=${ARCH}"
echo "IDF: $SRC_IDF"
echo "EPW: $EPW"
echo "OUTDIR: $OUTDIR"

cp "${EP_DIR}/Energy+.idd" "$OUTDIR/"
cp "$SRC_IDF" "$OUTDIR/${STEM}.idf"
export PYTHONPATH="$ROOT"
export OPENUBEM_ENERGYPLUS_IDD_PATH="$OUTDIR/Energy+.idd"

"$PY" "$ROOT/scenario_build.py" "$OUTDIR/${STEM}.idf" "$ARCH" "$CELL" "$OUTDIR/in.idf" "$OUTDIR/status.csv"
CHANGED=$(awk -F, 'NR==1 { for (i = 1; i <= NF; i++) if ($i == "changed") c = i; next } { gsub(/\r/, ""); print $c; exit }' "$OUTDIR/status.csv")

cleanup() {
    rm -f "$OUTDIR"/*.eso \
          "$OUTDIR"/*.mtd \
          "$OUTDIR"/*.rdd \
          "$OUTDIR"/*.mdd \
          "$OUTDIR"/*.htm \
          "$OUTDIR"/*.tab \
          "$OUTDIR"/eplus*.csv \
          "$OUTDIR/${STEM}.idf" \
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
}

if [ "$CHANGED" != "1" ]; then
    echo "Task ${I}: scenario IDF equals the adopted IDF, no EnergyPlus run"
    touch "$OUTDIR/UNCHANGED"
    echo 0 > "$OUTDIR/task.rc"
    cleanup
    exit 0
fi

"${EP_DIR}/energyplus" --version > "${OUTDIR}/energyplus_version.txt" 2>&1 || true
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
    if "$PY" "$ROOT/scenario_build.py" parse "$OUTDIR/eplusout.sql" "$OSM_ID" "$FA" "" "$OUTDIR/row.csv"; then
        echo "Task ${I}: row.csv written"
        rm -f "$OUTDIR/eplusout.sql"
    else
        echo "ERROR: parse failed, eplusout.sql kept" >&2
        RC=3
    fi
else
    echo "ERROR: no usable eplusout.sql (rc=${RC})" >&2
    if [ "$RC" -eq 0 ]; then
        RC=4
    fi
fi

cleanup
echo "Task ${I}: cleanup done, kept err, eio, end, row.csv, status.csv"
exit $RC
