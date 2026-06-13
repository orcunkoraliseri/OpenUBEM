#!/bin/bash
set -e
FLEET_DIR=/speed-scratch/o_iseri/fleets/la_suburban
OUT_DIR=$FLEET_DIR/out
MISSING_FILE=$FLEET_DIR/missing_stems.txt
TGZ_OUT=$FLEET_DIR/sim_out_missing.tgz
FILELIST=/tmp/la_sub_missing_filelist.txt
echo "Building missing-stems tgz..."
cd "$OUT_DIR"
> "$FILELIST"
while IFS= read -r stem; do
  if [ -d "$stem" ]; then
    echo "./$stem/eplusout.sql" >> "$FILELIST"
    echo "./$stem/eplusout.err" >> "$FILELIST"
    echo "./$stem/eplusout.end" >> "$FILELIST"
  else
    echo "WARNING stem not found: $stem" 1>&2
  fi
done < "$MISSING_FILE"
n=$(cat "$FILELIST" | wc -l)
echo "Files to pack: $n"
tar czf "$TGZ_OUT" -T "$FILELIST"
echo "Done: $TGZ_OUT"
du -sh "$TGZ_OUT"
