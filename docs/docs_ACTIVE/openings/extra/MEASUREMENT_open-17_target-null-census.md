# MEASUREMENT — OPEN-17: fleet-wide null census per imputation target (2026-08-21)

> Executes T03 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-live-items-2026-08-21.md`.
> Measurement only. No imputer run, no fallback wired, no production file touched.
> Script: `scripts/analysis/open17_target_null_census_2026-08-21.py`
> CSV: `openubem/outputs/comparisons/open17_target_null_census_2026-08-21.csv`

## Target-list conflict, resolved per the plan's own instruction

The plan text names a placeholder seventh target, `roof_shape`, with the instruction: *"If the
register's seventh target is not `roof_shape`, quote the conflict and use the register's list."*
Two independent checks both say it is not `roof_shape`:

1. `01_buildings.gpkg`'s 22 non-geometry columns have no `provenance_roof_shape` — the seven
   `provenance_*` columns are exactly plan §4's pinned list: `provenance_levels,
   provenance_height_m, provenance_year_built, provenance_building_tag, provenance_function_tag,
   provenance_postcode, provenance_geometry`.
2. The register's own citation for OPEN-17
   (`extra/MEASUREMENT_open-17_tier-census.md`, "Target x tier x count" table) enumerates the seven
   targets by name: `building_tag, function_tag, geometry, height_m, levels, postcode, year_built`.

So this task uses that list — `levels, height_m, year_built, function_tag, postcode, building_tag,
geometry` — not `roof_shape`. `roof_shape` is a real column in the gpkg but carries no provenance
tracking and is not one of OPEN-17's seven targets.

## Population

All twelve `evidence/open48_refleet4/<cell>/01_buildings.gpkg`. **8,160 buildings total** (C7:
matches the pinned figure exactly, no discrepancy to explain).

## Method

Two null definitions are reported side by side, because they diverge sharply for two targets:

- **`n_null`** — raw pandas null (`isna()`) on the target column itself (on `geometry`: `isna() |
  is_empty`).
- **`n_needs_value_provenance`** — rows whose `provenance_<target>` token is not `OSM_OBSERVED`
  (i.e. `OSM_MISSING` or `OSM_GENERIC`). This is the "an imputed/generic value is not counted as
  observed" reading the plan asks for, and it is what the OPEN-17 tier census used for its own
  denominator.

Both are also split by whether the building was simulated successfully in the adopted run (joined
to each cell's `results/05_results.csv` on `osm_id`, exact string match, no normalisation needed —
both files use the same `way/12345` form).

## Fleet result

| target | n_total | n_null (raw) | n_needs_value (provenance) | pct_needs_value | n_needs_value & simulated ok |
|---|---:|---:|---:|---:|---:|
| year_built | 8,160 | 5,913 | 5,913 | 72.46 % | 5,912 |
| levels | 8,160 | 7,719 | 7,719 | 94.60 % | 7,713 |
| height_m | 8,160 | 2,806 | 2,806 | 34.39 % | 2,805 |
| postcode | 8,160 | 4,183 | 4,183 | 51.26 % | 4,177 |
| function_tag | 8,160 | 0 | 7,741 | 94.87 % | 7,734 |
| building_tag | 8,160 | 0 | 4,105 | 50.31 % | 4,105 |
| geometry | 8,160 | 0 | 0 | 0.00 % | 0 |

**The two zero-raw-null targets are the finding.** `function_tag` and `building_tag` are never
`NaN` in the gpkg — but 7,741 `function_tag` rows are `OSM_MISSING` (a placeholder string, not a
null) and 4,105 `building_tag` rows are `OSM_GENERIC` (present but uninformative, e.g. `"yes"`). A
null-only census would have reported these two targets as **fully covered**; they are in fact the
**two largest holes on the list** after `levels`. `geometry` needs nothing — 8,160/8,160
`OSM_OBSERVED`, consistent with it being the one target the acquisition pass never fails on.

Fleet-wide token counts (matches `extra/MEASUREMENT_open-17_tier-census.md`'s tier census exactly,
cross-check, no re-derivation): `building_tag` 4,105 `OSM_GENERIC` / 4,055 `OSM_OBSERVED`;
`function_tag` 7,741 `OSM_MISSING` / 419 `OSM_OBSERVED`; `geometry` 8,160 `OSM_OBSERVED` / 0.

## Per-target: could the existing tier reach it?

- **`year_built`** — already covered. `resolve_vintage`'s 3-tier spatial/group-mode/legacy-default
  system is wired into production and fills 5,913/5,913 (100 %). This is OPEN-17's one working
  target.
- **`levels`** — the largest hole (7,719, 94.6 %). No production imputer fires. The 5-tier
  `impute_missing` machinery (`fusion`/`spatial`/`ml`/`draw`/`statistical`) exists and is built, but
  is never called from the fleet-build path (only from `validation/eui_impact.py`,
  `validation/mask_recover.py` and analysis/test code) — it could reach `levels` if wired, subject
  to OPEN-35's separate, still-undecided fallback question for the residual (T05, same pass).
- **`function_tag`** — 94.9 % missing, the second-largest hole and larger than the null-only view
  suggested. Same unwired-machinery answer as `levels`.
- **`postcode`** — 51.3 % missing. Same unwired-machinery answer.
- **`building_tag`** — 50.3 % generic (not missing — present but uninformative). A generic tag is a
  different repair (disambiguation among a fixed vocabulary) than a missing value, and the 5-tier
  machinery as built targets missing values, not generic ones; whether it is shaped to help here is
  a separate question this task does not answer.
- **`height_m`** — 34.4 % missing. Same unwired-machinery answer; OPEN-14 (this same pass) sizes
  what one specific tier (`fusion`) could do for it.
- **`geometry`** — 0 % missing. Nothing to reach.

## Test status

- **C7 — pass.** 8,160 across the twelve gpkgs, exact.
- **C8 — pass, consistent.** `year_built` raw-null count is 5,913, matching the known
  `5,913/5,913` tier-fill figure exactly (no inconsistency to report).

## Remedy shape (NOT applied)

None proposed — this task is a census, not a design. The two candidate remedies visible in the data
(wire the 5-tier `impute_missing` router into the production path; treat `building_tag`'s
`OSM_GENERIC` rows as a distinct repair target from `OSM_MISSING` rows) are the user's decision, not
this executor's.
