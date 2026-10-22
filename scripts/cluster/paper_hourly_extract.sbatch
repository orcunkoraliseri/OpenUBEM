#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --job-name=paper_hourly
#SBATCH --output=/speed-scratch/o_iseri/openubem/fleets/paper_hourly_2026-10-21/logs/%x_%A_%a.log

set -euo pipefail

ROOT="${HOURLY_ROOT:-/speed-scratch/o_iseri/openubem/fleets/paper_hourly_2026-10-21}"
PY="${HOURLY_PY:-/speed-scratch/o_iseri/envs/openubem_eu22/bin/python}"
I="${SLURM_ARRAY_TASK_ID:?SLURM_ARRAY_TASK_ID not set}"

ROW=$(sed -n "$((I + 1))p" "$ROOT/case_list.csv" | tr -d '\r')
if [ -z "$ROW" ]; then
    echo "ERROR: no row for task $I in $ROOT/case_list.csv" >&2
    exit 1
fi
TASK=$(echo "$ROW" | cut -d, -f1)
CELL=$(echo "$ROW" | cut -d, -f2)
STEM=$(echo "$ROW" | cut -d, -f5)
SQL=$(echo "$ROW" | cut -d, -f6)
if [ "$TASK" != "$I" ] || [ -z "$CELL" ] || [ -z "$STEM" ] || [ -z "$SQL" ]; then
    echo "ERROR: malformed row for task $I: '$ROW'" >&2
    exit 1
fi
if [ ! -f "$SQL" ]; then
    echo "ERROR: missing $SQL" >&2
    exit 1
fi

mkdir -p "$ROOT/out"
echo "Task $I: $CELL $STEM"
"$PY" "$ROOT/hourly.py" extract "$SQL" "$ROOT/out/${CELL}__${STEM}.csv.gz"
echo "Task $I: done"
