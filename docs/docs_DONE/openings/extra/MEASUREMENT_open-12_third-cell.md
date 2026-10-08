# MEASUREMENT — OPEN-12: the third 100% cell, named, and the replacement figures locked

**Date:** 2026-08-20 · **Task:** T04 of `PLAN_five-items-2026-08-20-late.md`

Script: `scripts/analysis/open12_height_residual_2026-08-20.py`. Output:
`openubem/outputs/comparisons/open12_height_residual.csv` (12 rows, one per cell).

## What the prior retrace already settled (not re-derived here)

`extra/MEASUREMENT_open-12_height-residual-retrace.md` (T05, 2026-08-18) already established that
the register's original `nyc_rural` 36.4% / `austin_rural` 19.2% only reproduce on a gitignored,
never-committed UTCI-arc scratch dataset (`scratchpad/e-utci-09-backfill/backfilled/...`), never a
repository artifact and not read by any adopted pipeline. It also already read `nyc_suburban` as a
control off the fleet's tracked Stage-1 files and found it at 100.0000% too, but stopped short of
naming it as OPEN-12's third cell. This task takes that as given and does not re-open either point.

## Method: all 12 cells, current adopted corpus

Read `evidence/open48_refleet4/<cell>/01_buildings.gpkg` for all 12 cells (`height_m`,
`provenance_height_m`). Checked `04_simulation_manifest.parquet` in every cell for a resolved-height
column — it never has one (columns are `osm_id, idf_path, work_dir, sql_path, status, n_warnings,
n_severe, wall_clock_s, ep_version, epw_path, error_summary, csv_path`; a run-status manifest, not a
value carrier). `provenance_height_m` takes exactly two values fleet-wide: `OSM_OBSERVED` and
`OSM_MISSING` — no third provenance token appears anywhere, so there is no fill mechanism recorded
in the persisted per-cell inputs. `n_filled_by_manifest_mechanism` is 0 in all 12 cells; the residual
share is identical to the missing-at-source share everywhere.

## Per-cell table (named, not pooled)

| cell | n | n missing at source | residual share |
|---|---:|---:|---:|
| austin_centre | 413 | 349 | 84.5036% |
| **austin_rural** | 245 | 245 | **100.0000%** |
| austin_suburban | 437 | 114 | 26.0870% |
| austin_urban | 425 | 47 | 11.0588% |
| la_centre | 226 | 45 | 19.9115% |
| la_rural | 149 | 1 | 0.6711% |
| la_suburban | 1343 | 15 | 1.1169% |
| la_urban | 618 | 42 | 6.7961% |
| nyc_centre | 738 | 121 | 16.3957% |
| **nyc_rural** | 198 | 198 | **100.0000%** |
| **nyc_suburban** | 1589 | 1589 | **100.0000%** |
| nyc_urban | 1779 | 40 | 2.2485% |

C9 — sum of `n` printed by the script: **8160**. Matches.

## C10 — the three 100% cells, named

`austin_rural`, `nyc_rural`, `nyc_suburban`. The two the register already names (`nyc_rural`,
`austin_rural`) are both among them. **The third, previously unnamed, is `nyc_suburban`** — n=1589,
all 1589 missing `height_m` at source (`provenance_height_m` = `OSM_MISSING` for all 1589 rows).

## The fleet-wide count: CONFIRMED, not replaced

Summing `n_missing_height_m_source` across all 12 cells gives **2,806** — the exact figure already
carried in the register (`OPEN-12 | ... | 3 cells, 2,032 buildings; 2,806 / 8,160 fleet-wide |`,
`INVESTIGATION_open-items-register-II.md:90`). The register's "3 cells, 2,032 buildings" also
reproduces exactly: 245 + 198 + 1589 = 2,032. **Neither number needs replacing.** The aggregate was
already correctly computed over all 12 cells including the unnamed `nyc_suburban`; what was missing
was only (a) the two per-cell percentage citations, which cite a different non-fleet dataset and do
not describe the fleet's tracked inputs, and (b) the name of the third cell behind the 2,032 figure.

## Replacement figures for the register (paste verbatim)

- `nyc_rural`: 36.4% → **100.0000% (198/198)**
- `austin_rural`: 19.2% → **100.0000% (245/245)**
- Third cell, now named: `nyc_suburban` — **100.0000% (1,589/1,589)**
- Fleet-wide count: **2,806 / 8,160 — CONFIRMED, unchanged**, re-derived from the current
  `evidence/open48_refleet4` corpus (12/12 cells), not carried forward from an unverified source.
- "3 cells, 2,032 buildings" — CONFIRMED, unchanged (245 + 198 + 1,589 = 2,032).

## CANDIDATE DEFECT

None found in this task. The manifest's lack of any resolved-height or fill-mechanism field across
all 12 cells is consistent with, not contradictory to, the retrace doc's and N15's prior finding that
the fleet's tracked path has no height-filling step at all — this task treats that as confirmed
architecture, not a new defect.

## What was not done

No fill mechanism was traced beyond the persisted `01_buildings.gpkg` / `04_simulation_manifest.parquet`
inputs named in the plan's How — the plan scopes this task to those two files, and both were read for
all 12 cells. Whatever downstream IDF generation does with a missing `height_m` (e.g. a levels-based
default) was not investigated; it is out of scope for a task about the persisted inputs' residual.
