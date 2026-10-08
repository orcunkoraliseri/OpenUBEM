# Executor prompt — T07 dry-list derivation (Madrid Catastro storeys)

**For: an external LLM session (Gemini / Antigravity), not a Claude subagent.**
**Repo root (Windows):** `C:\Users\o_iseri\Desktop\OpenUBEM`
**Python:** `python` is **not** on PATH in this repo's expected environment. Always invoke the venv
interpreter explicitly: `C:\Users\o_iseri\Desktop\OpenUBEM\.venv\Scripts\python.exe`. Run all commands with
that repo root as the working directory.

## What this task is

This is **read-only analysis only** — no production code is written or modified, no network request is
made, no cluster/Speed access, no `git commit`. You are deriving and logging one CSV list. Nothing else.

## Hard rules

1. Do **not** edit any `.py` file. Do **not** run any EnergyPlus simulation. Do **not** touch Speed/SLURM in
   any way (no `ssh`, no `sbatch`). Do **not** make any HTTP/network request.
2. Do **not** edit `main.py`, any file under `docs/docs_main/`, `docs/docs_stepN/`, or any OVERVIEW/DESIGN
   doc.
3. The only file you may **write** is:
   `openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE_ceiling82_2026-09-05/t07_dry_list.csv`
   (create the parent folder if it does not already exist).
4. Do not invent or guess any id. Every id in the output list must come from the source files below,
   verified by the exact filter stated. If you cannot verify a row, drop it and note the drop, do not keep
   it "to be safe."
5. If the total count you derive is not exactly **163**, or the two source counts below disagree, **STOP**
   and report the actual numbers and the discrepancy — do not silently round or adjust to force 163.

## Background (why this list, why 163)

Madrid has 163 residential footprints excluded from the fleet with reason `MISSING_OBSERVED_STOREY_COUNT`.
Spain's Catastro cadastre does carry a storey count for these parcels, but on the `BuildingPart` feature
type, reachable only via the `GetBuildingPartByParcel` stored query (per-parcel, not a bbox query) — a
follow-up task (not yours) will fire that query, but only after this dry list is produced and logged, per
this project's hard rule: **no live network campaign fires before its exact target-id list is written down
and reviewable.**

## Source files

- `openubem/outputs/eu_evidence/EU-04/es_catastro_attribute_sidecar.csv` — one row per EU-02 Madrid
  footprint; has columns including `catastro_local_id`, `levels`, `height_m`, `roof_height_m`,
  `provenance_levels`. The 163 targets are rows where `levels`, `height_m`, and `roof_height_m` are all
  null/empty **and** `provenance_levels == "OSM_MISSING"`.
- Cross-check source: re-run Madrid's own campaign row-derivation to get the current
  `MISSING_OBSERVED_STOREY_COUNT` exclusion set independently, and confirm its count and (if feasible without
  editing any file) its building-id set line up with the sidecar-derived list. The campaign code lives in
  `scripts/run_eu_s2_district_campaign.py` (read-only — look, do not edit) — find wherever Madrid's residential
  rows are assembled and excluded for a missing storey count, and use it only to cross-check the count, not to
  run anything.

## What to produce

`t07_dry_list.csv` with exactly these columns, one row per target parcel, sorted by `catastro_local_id`:

```
catastro_local_id,osm_building_id,footprint_source_row_present
```

- `catastro_local_id` — the Catastro parcel id to query via `GetBuildingPartByParcel`.
- `osm_building_id` — the EU-02 footprint id it joins to (whatever id column the sidecar uses to join back
  to the residential manifest — inspect the sidecar's own columns to find it, do not assume a name).
- `footprint_source_row_present` — `true`/`false`: whether you could independently confirm this id also
  appears in Madrid's own `MISSING_OBSERVED_STOREY_COUNT` exclusion set from the cross-check above.

## Report back (do not paraphrase into a summary — quote the real numbers)

1. Total row count in the sidecar matching the filter (must be 163 — if not, STOP here and report the actual
   number plus a few example rows that fell outside the filter, so the discrepancy can be diagnosed).
2. Count of rows where `footprint_source_row_present` is `false` (should be 0 or explain each one).
3. The path of the CSV you wrote, and its first 5 and last 5 rows pasted verbatim.
4. Nothing else — no fetch, no code changes, no recommendation on what to do next. That decision belongs to
   the project's director (a separate Claude Code session), not to you.
