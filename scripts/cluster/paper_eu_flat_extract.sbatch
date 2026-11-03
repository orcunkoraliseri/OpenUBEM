#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --job-name=paper_eu_flat
#SBATCH --output=/speed-scratch/o_iseri/openubem/fleets/paper_eu_flat_2026-10-21/logs/%x_%A_%a.log

set -euo pipefail

ROOT="${FLAT_ROOT:-/speed-scratch/o_iseri/openubem/fleets/paper_eu_flat_2026-10-21}"
PY="${FLAT_PY:-/speed-scratch/o_iseri/envs/openubem_eu22/bin/python}"
CHUNK="${FLAT_CHUNK:-100}"
I="${SLURM_ARRAY_TASK_ID:?SLURM_ARRAY_TASK_ID not set}"

SEL=$(awk -F, -v i="$I" -v c="$CHUNK" 'NR > 1 { gsub("\r", ""); n = int(($3 + c - 1) / c); if (i > acc && i <= acc + n) { print $1, $2, i - acc - 1; exit } acc += n }' "$ROOT/case_list.csv")
if [ -z "$SEL" ]; then
    echo "ERROR: task $I is past the end of $ROOT/case_list.csv at chunk size $CHUNK" >&2
    exit 1
fi
set -- $SEL
SITE="$1"
FOLDER="$2"
K="$3"
if [ ! -d "$FOLDER/out" ]; then
    echo "ERROR: missing $FOLDER/out" >&2
    exit 1
fi

mkdir -p "$ROOT/parts"
echo "Task $I: $SITE chunk $K of $FOLDER"
"$PY" "$ROOT/eu_flat_spread.py" chunk --folder "$FOLDER" --site "$SITE" --chunk-index "$K" --chunk-size "$CHUNK" --out "$ROOT/parts/${SITE}__chunk$(printf '%03d' "$K").csv"
echo "Task $I: done"
