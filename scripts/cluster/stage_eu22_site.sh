#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: bash scripts/cluster/stage_eu22_site.sh <SITE> <tag> [--dry-run]" >&2
  echo "  <tag> example: win_2026-10-09 (local tree = EU-11/<SITE>_<tag>)" >&2
  exit 1
}

DRY=0
ARGS=()
for a in "$@"; do
  if [ "$a" = "--dry-run" ]; then DRY=1; else ARGS+=("$a"); fi
done
[ "${#ARGS[@]}" -eq 2 ] || usage
SITE="${ARGS[0]}"
TAG="${ARGS[1]}"

case "$SITE" in *[!A-Za-z0-9_-]*|"") echo "ERROR: bad SITE: $SITE" >&2; exit 1;; esac
case "$TAG" in *[!A-Za-z0-9_.-]*|"") echo "ERROR: bad tag: $TAG" >&2; exit 1;; esac

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
TREE="$REPO/openubem/outputs/eu_evidence/EU-11/${SITE}_${TAG}"
SBATCH_LOCAL="$HERE/submit_eu22_site.sbatch"
REMOTE_HOST="o_iseri@speed.encs.concordia.ca"
FLEET="/speed-scratch/o_iseri/fleets/EU22_${SITE}_${TAG}"

rssh() {
  ssh "$REMOTE_HOST" "bash -lc '$1'"
}

say() {
  echo "[EU22-stage] $*"
}

step() {
  if [ "$DRY" -eq 1 ]; then
    echo "[dry-run] $1"
  else
    eval "$2"
  fi
}

if [ "$DRY" -eq 1 ]; then
  say "DRY RUN: nothing is executed"
fi

if [ "$DRY" -eq 0 ]; then
  [ -d "$TREE" ] || { echo "ERROR: local tree not found: $TREE" >&2; exit 1; }
  [ -f "$SBATCH_LOCAL" ] || { echo "ERROR: missing $SBATCH_LOCAL" >&2; exit 1; }
  for p in idfs weather schedules fleet.lst; do
    [ -e "$TREE/$p" ] || { echo "ERROR: missing $TREE/$p" >&2; exit 1; }
  done
  N=$(grep -c '' "$TREE/fleet.lst")
  NIDF=$(ls "$TREE/idfs" | wc -l | tr -d ' ')
  say "fleet.lst entries=$N, local idfs=$NIDF"
  if [ "$N" != "$NIDF" ]; then
    echo "ERROR: fleet.lst count ($N) != IDF count ($NIDF)" >&2
    exit 1
  fi
else
  N="<N>"
  say "local tree: $TREE"
  say "remote fleet dir: $FLEET"
fi

step "ssh $REMOTE_HOST \"bash -lc 'test ! -e $FLEET && mkdir -p $FLEET'\"" \
     "rssh 'test ! -e $FLEET && mkdir -p $FLEET'"

step "tar -czf - -C $TREE idfs weather schedules fleet.lst | ssh $REMOTE_HOST \"bash -lc 'cd $FLEET && tar -xzf -'\"" \
     "tar -czf - -C '$TREE' idfs weather schedules fleet.lst | rssh 'cd $FLEET && tar -xzf -'"

step "scp $SBATCH_LOCAL ${REMOTE_HOST}:${FLEET}/submit_eu22_site.sbatch" \
     "scp '$SBATCH_LOCAL' '${REMOTE_HOST}:${FLEET}/submit_eu22_site.sbatch'"

step "ssh $REMOTE_HOST \"bash -lc 'mkdir -p $FLEET/out'\"" \
     "rssh 'mkdir -p $FLEET/out'"

if [ "$DRY" -eq 1 ]; then
  echo "[dry-run] ssh $REMOTE_HOST \"bash -lc 'ls $FLEET/idfs | wc -l'\"   (must equal fleet.lst entries)"
  say "dry run complete; no command was executed"
  exit 0
fi

REMOTE_N=$(rssh "ls $FLEET/idfs | wc -l" | tr -d ' \r\n')
say "remote idfs=$REMOTE_N (expected $N)"
if [ "$REMOTE_N" != "$N" ]; then
  echo "ERROR: remote IDF count mismatch: expected $N, got $REMOTE_N" >&2
  exit 1
fi

say "staged OK: SITE=$SITE tag=$TAG N=$N FLEET=$FLEET"
say "manager submits: cd $FLEET && sbatch -p ps --time=7-00:00:00 --array=1-${N}%32 --mem=32G --export=ALL,FLEET_DIR=$FLEET submit_eu22_site.sbatch"
