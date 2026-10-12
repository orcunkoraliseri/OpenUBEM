#!/bin/bash
#SBATCH --partition=ps
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --job-name=eu22_sidecar
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
export OPENUBEM_REPO_ROOT="$ROOT/repo"

SRC="$ROOT/sidecar_in/$SITE"
OUT="$ROOT/sidecar_parts/$SITE/$I"
SLUG=$(printf '%s' "$SITE" | tr 'A-Z-' 'a-z_')
[ -f "$SRC/prepared_buildings.csv" ] || { echo "ERROR: missing $SRC/prepared_buildings.csv" >&2; exit 1; }
[ -f "$SRC/${SLUG}_manifest.csv" ] || { echo "ERROR: missing $SRC/${SLUG}_manifest.csv" >&2; exit 1; }

rm -rf "$OUT"
mkdir -p "$OUT/idfs" "$OUT/layouts"

STEM=$("$PY" -X utf8 - "$SRC" "$OUT" "$SLUG" "$BID" <<'PYEOF'
import csv, sys
src, out, slug, bid = sys.argv[1:5]
def cut(name_in, name_out):
    with open(f"{src}/{name_in}", newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        head = next(r)
        k = head.index("building_id")
        rows = [x for x in r if x and x[k] == bid]
    if len(rows) != 1:
        sys.exit(f"ERROR: {name_in}: {len(rows)} rows for {bid}, expected 1")
    for name in (name_out if isinstance(name_out, list) else [name_out]):
        with open(f"{out}/{name}", "w", newline="", encoding="utf-8") as g:
            w = csv.writer(g)
            w.writerow(head)
            w.writerow(rows[0])
    return head, rows[0]
head, row = cut("prepared_buildings.csv", ["prepared_buildings.csv", "population.csv"])
cut(f"{slug}_manifest.csv", f"{slug}_manifest.csv")
print(row[head.index("stem")])
PYEOF
)
[ -n "$STEM" ] || { echo "ERROR: no stem for $BID" >&2; exit 1; }
[ -f "$SRC/idfs/$STEM.idf" ] || { echo "ERROR: missing $SRC/idfs/$STEM.idf" >&2; exit 1; }
ln -s "$SRC/idfs/$STEM.idf" "$OUT/idfs/$STEM.idf" 2>/dev/null || cp "$SRC/idfs/$STEM.idf" "$OUT/idfs/$STEM.idf"

echo "Task $I: site=$SITE id=$BID stem=$STEM sweep_s=$OPENUBEM_NOCORE_SWEEP_S kminus1=${OPENUBEM_NOCORE_KMINUS1:-0}"
cd "$ROOT/repo"
PYTHONPATH="$ROOT/repo" "$PY" -X utf8 -m scripts.emit_eu11_layout_sidecars --district "$SITE" --evidence-root "$SITE=$OUT" --population-manifest "$SITE=$OUT/population.csv"
N=$(find "$OUT/layouts" -name '*.json' | wc -l)
[ "$N" -eq 1 ] || { echo "ERROR: task $I wrote $N layout files, expected 1" >&2; exit 1; }
echo "Task $I done: $OUT ($N layout)"
