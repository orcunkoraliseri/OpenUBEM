# MEASUREMENT — OPEN-53: is "meter-only" a property of the 874, or of the whole harvest?

**Date:** 2026-08-21
**Task:** T01, `PLAN_ten-live-items-2026-08-21.md`
**Script:** `scripts/analysis/open53_harvest_sql_census_2026-08-21.py`
**Output:** `openubem/outputs/comparisons/open53_harvest_sql_census_2026-08-21.csv` (40,800 rows, one per
harvest directory)

## Method

Walked `C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest\<cell>_<mode>\<stem>\` in full (no
sampling). For every directory recorded `has_sql`, `has_end`, `has_err`, `has_eio`, `sql_bytes`. For
every directory whose `eplusout.sql` exists, opened it read-only and recorded `n_dict_rows`
(`ReportDataDictionary` count), `n_zone_keys` (`Name LIKE 'Zone %'`), `n_abups_enduse_rows`
(`TabularDataWithStrings` joined view, `AnnualBuildingUtilityPerformanceSummary` / `End Uses`),
`has_elec_facility`, `has_gas_facility`. Zero files threw `sql_open_error`.

## Result — the population is 40,800, not a sample

- **Total directories: 40,800** (12 cells x 5 modes x 680 avg buildings/cell-mode; confirms 8,160
  buildings x 5 modes).
- **`.sql` present: 39,926 / 40,800.** All 874 missing `.sql` files are concentrated in exactly two
  modes: `fast_zone` (437 missing) and `floor` (437 missing). `auto`, `building`, `layout_assign` are
  **100 % complete** — 8,160/8,160 each.
- **`.end` missing: 875**, of which **874 also have no `.sql`** and **1 has a `.sql` but no `.end`**
  (a run that produced output before the end-marker step, or a marker write that failed).
- **Of the 39,926 directories that DO have a `.sql`: zero — 0 — have any ABUPS End-Uses row, and zero
  have any zone-level (`Zone %`) reporting key.** Every single one carries exactly 9 or 10
  `ReportDataDictionary` rows, all Run-Period facility/end-use meters
  (`Electricity:Facility`, `NaturalGas:Facility`, and a handful of sub-meters such as
  `InteriorLights:Electricity`, `Fans:Electricity`, `Heating:NaturalGas`, `Pumps:Electricity`, etc.).
  `Electricity:Facility` and, where gas is used, `NaturalGas:Facility` are present in every file
  sampled.

### Cross-tab by mode (has_sql / any_abups / any_zonekey)

| mode | n | has_sql | any_abups | any_zonekey |
|---|---|---|---|---|
| auto | 8,160 | 8,160 | 0 | 0 |
| building | 8,160 | 8,160 | 0 | 0 |
| fast_zone | 8,160 | 7,723 | 0 | 0 |
| floor | 8,160 | 7,723 | 0 | 0 |
| layout_assign | 8,160 | 8,160 | 0 | 0 |

### Cross-tab by cell (has_sql / any_abups / any_zonekey)

| cell | n | has_sql | any_abups | any_zonekey |
|---|---|---|---|---|
| austin_centre | 2,065 | 2,065 | 0 | 0 |
| austin_rural | 1,225 | 1,225 | 0 | 0 |
| austin_suburban | 2,185 | 1,311 | 0 | 0 |
| austin_urban | 2,125 | 2,125 | 0 | 0 |
| la_centre | 1,130 | 1,130 | 0 | 0 |
| la_rural | 745 | 745 | 0 | 0 |
| la_suburban | 6,715 | 6,715 | 0 | 0 |
| la_urban | 3,090 | 3,090 | 0 | 0 |
| nyc_centre | 3,690 | 3,690 | 0 | 0 |
| nyc_rural | 990 | 990 | 0 | 0 |
| nyc_suburban | 7,945 | 7,945 | 0 | 0 |
| nyc_urban | 8,895 | 8,895 | 0 | 0 |

(all 874 missing-`.sql` are in `austin_suburban`, split across its `fast_zone`/`floor` arms — every
other cell has `.sql` for all five modes.)

## Verdict — F4 is confirmed, at full census scale, not overturned

The ten-file scout (F4) said the sampled `.sql` files were meter-only. The full 39,926-file census
says the **entire harvest** is meter-only — 100 %, not a property of a subset. This means:

- **The 874 directories missing `.sql` are not special.** Every directory that *does* have a `.sql`
  is exactly as meter-only as the ones that don't. Re-fetching the missing 874 would buy custody
  (having the file on disk) and nothing else — it would not add zone-level or ABUPS detail that the
  rest of the harvest lacks.
- OPEN-53's live question is now only its second one: **should `parse_building()` fall back to a
  meter-only EUI when zone keys are absent?** T02 measures the cost of that fallback.

## Test results

- **C1** — `.end`-missing count = **875**, matches the predecessor's F8/T04 number exactly (within
  the ±2 tolerance). PASS.
- **C2** — three files re-opened by hand (`la_suburban/auto/way_442341027`,
  `nyc_urban/floor/way_241862851`, `austin_suburban/building/way_382994240`); all five fields matched
  the census row exactly (`n_dict_rows=9, n_zone_keys=0, n_abups_enduse_rows=0,
  has_elec_facility=True, has_gas_facility=True` in all three). PASS.
- **C3** — F4's ten-file scout is **confirmed**, not overturned — strengthened to a full 39,926-file
  census showing 100 % meter-only, versus the scout's 10/10.

## Remedy shape (NOT applied)

Not applicable — this task recommends no fix. It only reclassifies OPEN-53's shape: the custody
question (re-fetch the 874) is now decoupled from the parser question (add a meter-only fallback),
and the latter is the one worth measuring, which T02 does.
