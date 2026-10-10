#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: bash scripts/cluster/stage_eu22_fix.sh [--dry-run <dir>]" >&2
  echo "  default: build the package and ship it to Speed (scp/tar only)." >&2
  echo "  --dry-run <dir>: build and unpack the package into <dir>; no ssh." >&2
  exit 1
}

DRY=0
DRYDIR=""
if [ "${1:-}" = "--dry-run" ]; then
  [ -n "${2:-}" ] || usage
  DRY=1
  DRYDIR="$2"
elif [ "$#" -ne 0 ]; then
  usage
fi

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
EV="$REPO/openubem/outputs/eu_evidence/EU-11/division_fix_2026-10-10"
SITES="FI-HEL-KALLIO AT-VIE-RUDOLFSHEIM HU-BUD-ERZSEBETVAROS"
NAME="eu22_fix_2026-10-10"
REMOTE_HOST="o_iseri@speed.encs.concordia.ca"
REMOTE_BASE="/speed-scratch/o_iseri"

rssh() {
  ssh "$REMOTE_HOST" "bash -lc '$1'"
}

say() {
  echo "[EU22-fix-stage] $*"
}

for f in ids_combined.csv $(for s in $SITES; do echo "ids_$s.csv"; done); do
  [ -f "$EV/$f" ] || { echo "ERROR: missing $EV/$f" >&2; exit 1; }
done
for f in eu22_fix_env.sbatch eu22_fix_array.sbatch; do
  [ -f "$HERE/$f" ] || { echo "ERROR: missing $HERE/$f" >&2; exit 1; }
done
for s in $SITES; do
  [ -f "$REPO/openubem/outputs/eu02/$s/02_residential_manifest.gpkg" ] || { echo "ERROR: missing eu02 manifest for $s" >&2; exit 1; }
  [ -f "$REPO/openubem/outputs/eu_evidence/EU-22/$s/acquisition_report.json" ] || { echo "ERROR: missing acquisition_report.json for $s" >&2; exit 1; }
done

if [ "$DRY" -eq 1 ]; then
  WORK="$DRYDIR"
  mkdir -p "$WORK"
else
  WORK="$(mktemp -d)"
fi
PKG="$WORK/$NAME"
[ ! -e "$PKG" ] || { echo "ERROR: $PKG already exists" >&2; exit 1; }
mkdir -p "$PKG/repo" "$PKG/logs"

tar -C "$REPO" --exclude=__pycache__ --exclude=openubem/outputs -cf - openubem scripts inputs pyproject.toml uv.lock | tar -C "$PKG/repo" -xf -
for s in $SITES; do
  tar -C "$REPO" --exclude=__pycache__ -cf - "openubem/outputs/eu02/$s" | tar -C "$PKG/repo" -xf -
done
for s in $SITES; do
  mkdir -p "$PKG/repo/openubem/outputs/eu_evidence/EU-22/$s"
  cp "$REPO/openubem/outputs/eu_evidence/EU-22/$s/acquisition_report.json" "$PKG/repo/openubem/outputs/eu_evidence/EU-22/$s/"
done
cp "$EV"/ids_combined.csv "$PKG/"
for s in $SITES; do cp "$EV/ids_$s.csv" "$PKG/"; done
cp "$HERE/eu22_fix_env.sbatch" "$HERE/eu22_fix_array.sbatch" "$PKG/"
(cd "$REPO" && uv export --frozen --no-dev --no-hashes --no-emit-project --quiet) | grep -v '^ *#' > "$PKG/requirements_eu22.txt"

N=$(( $(grep -c '' "$PKG/ids_combined.csv") - 1 ))
say "combined ids=$N, requirements lines=$(grep -c '' "$PKG/requirements_eu22.txt"), package size=$(du -sh "$PKG" | cut -f1)"

if [ "$DRY" -eq 1 ]; then
  say "DRY RUN: package unpacked in $PKG; nothing sent"
  exit 0
fi

( cd "$WORK" && tar -czf "$NAME.tgz" "$NAME" )
rssh "mkdir -p $REMOTE_BASE/envs $REMOTE_BASE/$NAME/logs"
scp "$WORK/$NAME.tgz" "$REMOTE_HOST:$REMOTE_BASE/$NAME.tgz"
rssh "tar -xzf $REMOTE_BASE/$NAME.tgz -C $REMOTE_BASE"
rssh "ls $REMOTE_BASE/$NAME | head -20"
rm -rf "$WORK"
say "staged at $REMOTE_BASE/$NAME ; array size N=$N (use --array=1-$N%W, W = 32 minus our other running arrays)"
