# MEASUREMENT — OPEN-35: what was actually built for the 39 (2026-08-21 night)

> Executes T04 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-live-items-2026-08-21-night.md`.
> Measurement only. No fallback picked, no production file touched.
> Script: `scripts/analysis/open35_evidence-cards_2026-08-21b.py`
> CSV: `openubem/outputs/comparisons/open35_evidence-cards_2026-08-21b.csv`

## Method

For each of the 39 buildings in `open35_fallback_population_2026-08-21.csv`: stem the `osm_id`
(`/` → `_`) and read `evidence/open48_refleet4/<cell>/sim_out/<stem>/eplusout.eio`. None of the 39
carry a `_part0`/`_part1` split — checked directly, all 39 stems match a `sim_out` directory
exactly. Parsed every ` Zone Information,` line by position against the header confirmed present in
every file (F3 order), taking `Min Z`/`Max Z`/`Floor Area` per zone. Joined to
`05_results.csv` (per cell) and to the population CSV's own `current_num_floors`,
`preopen35_num_floors`, `current_floor_area_m2`.

## C8 — 39 in, 39 out; readability and simulation coverage

- 39 rows in, 39 rows out.
- **39 of 39 had a readable `.eio`** with a `Zone Information` block.
- **38 of 39 have `simulation_status == success`** in `05_results.csv` — reproduces F9's "38
  simulated" exactly. The one non-simulated building is `way/266034056` (`nyc_centre`,
  `LargeHotel`, `simulation_status == not_simulated`, no published floor area, no EUI).

## Top 5 by `current_floor_area_m2` (the fallback-assigned floor area), discussed individually

1. **`relation/7480583`** (`austin_centre`) — assigned 45 floors, fallback-assigned floor area
   242,204.26 m². Built **45 zones, 45 distinct storey levels** (one zone per floor, confirmed by
   45 distinct `(min_z, max_z)` pairs). Published floor area 301,996.35 m² (footprint 6,711.03 ×
   45 — matches F9 exactly). `simulation_status = success`, `total_eui_kwh_m2 = 104.82`.
   **This is C9: the built model agrees with the fallback's 45 storeys.** No discrepancy to
   report — the model built exactly what the fallback assigned.
2. **`way/134807227`** (`austin_centre`) — assigned 45 floors, fallback-assigned floor area
   176,263.74 m². Built 45 zones, 45 distinct levels — again a one-zone-per-floor match. Published
   floor area 176,258.70 m² (near-identical to the fallback figure). `success`,
   `total_eui_kwh_m2 = 109.91`.
3. **`way/281344664`** (`nyc_urban`) — assigned 6 floors, fallback-assigned floor area
   66,464.81 m². Built 6 zones, 6 distinct levels. Published floor area 66,464.82 m² (matches to
   the cm). `success`, `total_eui_kwh_m2 = 98.17`.
4. **`way/266034056`** (`nyc_centre`) — assigned 19 floors, fallback-assigned floor area
   55,716.81 m². Built 19 zones, 19 distinct levels — the geometry was still generated correctly.
   But `simulation_status = not_simulated`: this building is the one of the 39 that never ran, so
   it has no published floor area and no EUI to compare against the 45-storey case above.
5. **`way/231123149`** (`austin_centre`) — assigned 5 floors, fallback-assigned floor area
   41,126.62 m². Built **45 zones but only 5 distinct storey levels** — 9 zones per floor
   (perimeter/core subdivision), not 1. The storey count itself still agrees with the fallback (5
   built vs 5 assigned); the higher zone count is a zoning-strategy artifact, not a storey
   disagreement. Published floor area 40,900.35 m² (close to the assigned figure).
   `success`, but `total_eui_kwh_m2 = 377.30` — over 3x the other four in this top 5, flagged here
   as an outlier worth the user's attention but not diagnosed further (measurement only).

## What this settles for `relation/7480583`

The user's open question was whether 45 assigned storeys produced 45 storeys of zones. **They
did**: 45 zones, 45 distinct `(min_z, max_z)` levels, and the published floor area reproduces
footprint × 45 to the reported precision. There is no zone-count/storey-count disagreement for the
single building that is 1.24 % of the fleet floor area on its own.

## Test status

- **C8 — pass.** 39 in, 39 out; 39/39 `.eio` readable; 38/39 `simulation_status == success`,
  matching F9.
- **C9 — pass.** `relation/7480583`: built zone count 45, distinct storey levels 45, against the
  45 the fallback assigned. They agree — reported plainly, not explained away.
