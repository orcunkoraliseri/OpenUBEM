#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --job-name=eu22_fix
#SBATCH --output=/speed-scratch/o_iseri/eu22_fix_2026-10-10/logs/%x_%A_%a.log

set -euo pipefail

ROOT="${EU22_FIX_ROOT:-/speed-scratch/o_iseri/eu22_fix_2026-10-10}"
PY="${EU22_FIX_PY:-/speed-scratch/o_iseri/envs/openubem_eu22/bin/python}"
I="${SLURM_ARRAY_TASK_ID:?SLURM_ARRAY_TASK_ID not set}"

ROW=$(sed -n "$((I + 1))p" "$ROOT/ids_combined.csv" | tr -d '\r')
SITE="${ROW%%,*}"
BID="${ROW#*,}"
if [ -z "$ROW" ] || [ -z "$SITE" ] || [ -z "$BID" ] || [ "$SITE" = "$ROW" ]; then
    echo "ERROR: no valid 'site,building_id' row for task $I in $ROOT/ids_combined.csv" >&2
    exit 1
fi

export OPENUBEM_ENERGYPLUS_IDD_PATH="$ROOT/Energy+.idd"
[ -f "$OPENUBEM_ENERGYPLUS_IDD_PATH" ] || { echo "ERROR: missing $OPENUBEM_ENERGYPLUS_IDD_PATH (EnergyPlus 23.1 IDD)" >&2; exit 1; }
export OPENUBEM_NOCORE_SWEEP=1
export OPENUBEM_NOCORE_SWEEP_S="${OPENUBEM_NOCORE_SWEEP_S:-3600}"
case "$SITE" in
    AT-VIE-RUDOLFSHEIM|HU-BUD-ERZSEBETVAROS) export OPENUBEM_NOCORE_KMINUS1=1 ;;
    *) unset OPENUBEM_NOCORE_KMINUS1 ;;
esac

mkdir -p "$ROOT/parts/ids"
IDS="$ROOT/parts/ids/$I.csv"
OUT="$ROOT/parts/$SITE/$I"
printf 'building_id\n%s\n' "$BID" > "$IDS"
mkdir -p "$ROOT/parts/$SITE"
rm -rf "$OUT"

echo "Task $I: site=$SITE id=$BID sweep_s=$OPENUBEM_NOCORE_SWEEP_S kminus1=${OPENUBEM_NOCORE_KMINUS1:-0}"
cd "$ROOT/repo"
PYTHONPATH="$ROOT/repo" "$PY" -X utf8 scripts/run_eu_s2_district_campaign.py --district "$SITE" --only-ids "$IDS" --out "$OUT"
echo "Task $I done: $OUT"
