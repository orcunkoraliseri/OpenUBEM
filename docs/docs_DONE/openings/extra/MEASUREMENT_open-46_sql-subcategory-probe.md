# MEASUREMENT — OPEN-46 / T03: SQL subcategory probe

**Executor:** B. **Date:** 2026-08-12. **Status: STOPPED per task instruction — SQL files not on this machine.**
**Scope: EVIDENCE ONLY. No source file edited. No SQL substituted.**

## Result up front

The adopted `phaseE_elevrb` run's EnergyPlus SQL files are **not present on this machine**. Every
`sql_path` in every `04_simulation_manifest.parquet` under
`docs/docs_VALIDATION/validations/overAll/results/phaseE_elevrb/` points at
`C:\Users\o_iseri\AppData\Local\Temp\ubem_elev_rebaseline\<cell>\sim_out\<osm_id>\eplusout.sql`, and
**every directory under that tree, for all twelve cells, contains zero files.** Per the task text
("If the SQL files are not on this machine, say that plainly and stop the task — do not substitute a
freshly generated SQL and report it as the adopted run's"), **T03 stops here.** No source file was
touched. No substitute SQL was generated or reported as the adopted run's.

## Evidence

### 1. The manifest rows and row count (matches §4's cited figure)

```
austin_centre 413
austin_rural 245
austin_suburban 437
austin_urban 425
la_centre 226
la_rural 149
la_suburban 1343
la_urban 618
nyc_centre 738
nyc_rural 198
nyc_suburban 1589
nyc_urban 1779
TOTAL rows 8160
```

Sample `sql_path` values pulled directly from the parquet (first two `status == 'success'` rows per
cell, three cells shown):

```
austin_centre:
C:\Users\o_iseri\AppData\Local\Temp\ubem_elev_rebaseline\austin_centre\sim_out\way_37417988\eplusout.sql
C:\Users\o_iseri\AppData\Local\Temp\ubem_elev_rebaseline\austin_centre\sim_out\way_37417989\eplusout.sql

la_centre:
C:\Users\o_iseri\AppData\Local\Temp\ubem_elev_rebaseline\la_centre\sim_out\way_39335032\eplusout.sql
C:\Users\o_iseri\AppData\Local\Temp\ubem_elev_rebaseline\la_centre\sim_out\way_202905185\eplusout.sql

nyc_urban:
C:\Users\o_iseri\AppData\Local\Temp\ubem_elev_rebaseline\nyc_urban\sim_out\way_220649876\eplusout.sql
C:\Users\o_iseri\AppData\Local\Temp\ubem_elev_rebaseline\nyc_urban\sim_out\way_221190748\eplusout.sql
```

### 2. Filesystem check on the sample (six files, three cells — satisfies "at least five SQL files
from at least three different cells")

```
MISSING  .../austin_centre/sim_out/way_37417988/eplusout.sql
MISSING  .../austin_centre/sim_out/way_37417989/eplusout.sql
MISSING  .../la_centre/sim_out/way_39335032/eplusout.sql
MISSING  .../la_centre/sim_out/way_202905185/eplusout.sql
MISSING  .../nyc_urban/sim_out/way_220649876/eplusout.sql
MISSING  .../nyc_urban/sim_out/way_221190748/eplusout.sql
```

### 3. The absence is total, not a sampling artifact

The `way_*` / `relation_*` directories under `ubem_elev_rebaseline\<cell>\sim_out\` exist (subdirectory
counts below), but **every one of them is empty**:

```
austin_centre: subdirs=414   files=0
austin_rural:  subdirs=246   files=0
austin_suburban: subdirs=438 files=0
austin_urban:  subdirs=426   files=0
la_centre:     subdirs=227   files=0
la_rural:      subdirs=150   files=0
la_suburban:   subdirs=1344  files=0
la_urban:      subdirs=619   files=0
nyc_centre:    subdirs=739   files=0
nyc_rural:     subdirs=199   files=0
nyc_suburban:  subdirs=1590  files=0
nyc_urban:     subdirs=1780  files=0
```

`find <cell-root> -type f | wc -l` = 0 for all twelve cells. This is a stronger statement than the
previous pass's finding about the six failed buildings: **all ~8,160 buildings' SQL is gone, not just
the six failed ones.**

### 4. No archive or alternate copy found

Searched the repo and the user profile (to reasonable depth) for any archive or alternate location:

- `find <repo> -iname "*elevrb*"` outside the `docs_VALIDATION` results tree (which holds parquet/CSV/
  geojson/gpkg, not SQL) → no hits.
- `find ~ -maxdepth 4 -iname "*elev_rebaseline*"` → only the empty temp tree itself.
- `find ~ -maxdepth 4 -iname "*phaseE_elevrb*"` → no hits.
- `find <repo> -iname "eplusout.sql"` → hits exist, but they belong to unrelated arcs (pytest fixtures
  under `.pytest_tmp/`, and LayoutAssigner storey-matching debug runs under
  `docs/docs_DONE/SETUP/layoutAssigner/debug/...`). **None of these were substituted or probed as if
  they were the adopted run's** — that would violate the task's explicit instruction.

### 5. Non-vacuity control (hard rule 7)

Before concluding "not found," the probe script (`scripts/analysis/open46_sql_subcategory_probe.py`)
first builds a synthetic sqlite database in the scratchpad with a `TabularDataWithStrings` table
containing a deliberately planted `Elevators` row under `End Uses By Subcategory`, then runs the exact
same query the real-file probe uses:

```
Planted row query result: [('End Uses By Subcategory', 'Elevators', 'Electricity', '123.45')]
CONTROL PASSED: probe query finds a planted Elevators row.
Synthetic control database removed: C:\Users\o_iseri\AppData\Local\Temp\open46_control_7qe_7hpv\synthetic_control.sql
```

The synthetic database was deleted immediately after the control ran. This proves the scanner is
capable of finding an Elevators subcategory row when one exists — the "0 files exist" result on the
real files is therefore a real absence of the files themselves, not a broken scanner returning a false
negative.

## Answers to the three sub-questions

**Because no SQL file could be opened, none of the three sub-questions has been answered from real
evidence.** This is the honest outcome the task explicitly names as acceptable:

1. `trim_hourly` True/False — **not determined.** No SQL file to inspect for `AllSummary` tabular
   tables or hourly zone variables.
2. `TabularDataWithStrings` "End Uses By Subcategory" table with an `Elevators` row — **not
   determined.**
3. Meter / `ReportDataDictionary` entry named for elevators — **not determined.**

## What this means for §3 decision 3 and T05

§3 decision 3 is written on the assumption that the elevator meter is absent from the adopted run's
SQL ("which is the case for every file the adopted run produced, unless T03 proves otherwise"). **T03
did not prove otherwise — it could not test the assumption at all**, because the artifacts it would
need to test are gone. The guarded, additive design in §3 decision 3 remains the only safe default:
since the SQL cannot be inspected, it cannot be shown to carry the meter, so the guard (`elevators_eui_
kwh_m2 = 0.0`, no de-folding, when the meter is absent) must be treated as load-bearing for the entire
adopted `phaseE_elevrb` run, not just a fallback case.

## Artifacts

- `scripts/analysis/open46_sql_subcategory_probe.py` — probe script with non-vacuity control.
- `openubem/outputs/comparisons/open46_sql_subcategory_probe.csv` — six probed files, all `exists=False`.
- This report.

## What was NOT done

- No SQL file was opened or queried (none exists).
- No source file was edited.
- No configuration was read to infer `trim_hourly` — the task requires artifact-based determination
  only, and no artifact is available.
