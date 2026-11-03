#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --job-name=fleet07_pack
#SBATCH --output=/speed-scratch/o_iseri/openubem/fleets/fleet07_2026-09-26/pull/%x_%A_%a.log

# FLEET-07c pull-method packing job (techtransfer block-7 plan, manager 2026-09-27).
# One array task packs 1,000 consecutive lines of fleet07_all.lst (40,746 lines,
# waves 1-5 concatenated) into a single tar under pull/, containing only
# eplusout.end, eplusout.err and gzip'd eplusout.sql per case. The raw out/ tree
# is read-only here; nothing under it is modified or deleted.
#
# Usage: sbatch --array=1-41%32 --time=7-00:00:00 fleet07_pack.sbatch

set -e

ROOT=/speed-scratch/o_iseri/openubem/fleets/fleet07_2026-09-26
ALL_LST="$ROOT/fleet07_all.lst"
NN=$(printf "%02d" "$SLURM_ARRAY_TASK_ID")
START=$(( (SLURM_ARRAY_TASK_ID - 1) * 1000 + 1 ))
END=$(( SLURM_ARRAY_TASK_ID * 1000 ))

STAGE="$TMPDIR/stage_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
rm -rf "$STAGE"
mkdir -p "$STAGE"

LINES="$TMPDIR/lines_${NN}.lst"
sed -n "${START},${END}p" "$ALL_LST" > "$LINES"

N_CASES=0
N_MISSING=0
MISSING_FILE="$ROOT/pull/chunk_${NN}.missing"
: > "$MISSING_FILE"

while IFS=$'\t' read -r CELL STEM EPW; do
    [ -z "$CELL" ] && continue
    N_CASES=$((N_CASES + 1))
    SRC="$ROOT/out/$CELL/$STEM"
    DST="$STAGE/$CELL/$STEM"
    mkdir -p "$DST"

    HAS_END=0
    HAS_SQL=0

    if [ -f "$SRC/eplusout.end" ]; then
        cp "$SRC/eplusout.end" "$DST/eplusout.end"
        HAS_END=1
    fi
    if [ -f "$SRC/eplusout.err" ]; then
        cp "$SRC/eplusout.err" "$DST/eplusout.err"
    fi
    if [ -f "$SRC/eplusout.sql" ]; then
        gzip -c "$SRC/eplusout.sql" > "$DST/eplusout.sql.gz"
        HAS_SQL=1
    fi

    if [ "$HAS_SQL" -eq 0 ] || [ "$HAS_END" -eq 0 ]; then
        N_MISSING=$((N_MISSING + 1))
        echo -e "$CELL\t$STEM\thas_end=$HAS_END\thas_sql=$HAS_SQL" >> "$MISSING_FILE"
    fi
done < "$LINES"

set +e
tar cf "$ROOT/pull/chunk_${NN}.tar" -C "$STAGE" .
TAR_RC=$?
set -e
rm -rf "$STAGE"
if [ "$TAR_RC" -ne 0 ]; then
    echo "tar failed with exit code $TAR_RC" >&2
    exit "$TAR_RC"
fi

echo "$NN $N_CASES $N_MISSING" > "$ROOT/pull/chunk_${NN}.done"
