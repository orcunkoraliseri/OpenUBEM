# MEASUREMENT — OPEN-18: is the small-cold-cell sample reachable from what we already have?

**Date:** 2026-08-21 · **Task:** T08 of `PLAN_ten-live-items-2026-08-21.md` · **Item:** OPEN-18
**Script:** `scripts/analysis/open18_small_cold_population_2026-08-21.py`
**Output:** `openubem/outputs/comparisons/open18_small_cold_population_2026-08-21.csv` (130 rows,
one per `cell x archetype_id`)

## 1. What criteria the √S test needs — searched, not found numerically

Read in full:

- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-18-20_method-bounds.md` — describes the
  population qualitatively only: *"a size-stratified sample (small buildings, S well under 1,
  matched by archetype) in the coldest cells (`nyc_rural`/`nyc_centre`, the register's own climate
  proxy for 'cold')"* (line 47). No numeric footprint band, no numeric S threshold beyond the
  worked example *"median `MidriseApartment` S = 0.054"* (line 23), and no storey range at all.
- `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03-18_untrimmed-sample.md` §6 (lines 95-110) —
  the only concrete precedent: n=8, drawn as the **10th/35th percentile slots of `footprint_area_m2`**
  within the four NYC cells, and explicitly states this sample **does not size OPEN-18** (n too
  small, "would need a purpose-built sample").
- Register (`INVESTIGATION_open-items-register-II.md:117, 219-222`) — carries OPEN-18 only as
  *"small buildings, cold cells"* / *"unsized — needs a purpose-built small-cold-cell sample"*. No
  numbers.

**Conclusion: no document on disk states a numeric footprint band, a numeric cold-climate threshold,
or a storey range for this test.** Per the plan's own instruction, a band is proposed below as an
explicit assumption — the executor's, not the record's.

## 2. Executor-proposed criteria (assumption, not the record's)

- **Small** = `footprint_area_m2 <= the 35th percentile of footprint_area_m2` computed **within each
  cell**, among `simulation_status == 'success'` buildings. This reuses the upper bound of the only
  precedent on disk (T04's "10th/35th percentile slots") rather than inventing a new absolute
  threshold.
- **Cold** = ASHRAE climate zone 5 or colder (zones 5/6/7/8 — cool, cold, very-cold, subarctic per
  ASHRAE 169). This is a standard external definition, not one drawn from any OpenUBEM doc, used
  because the register's own proxy (`nyc_rural`/`nyc_centre`) turns out **not to be climatically
  uniform** — see §3.
- **Storey range**: not filtered on, because no doc states one. The qualifying population's `levels`
  distribution (min/median/max) is reported per cell/archetype instead, for the user to apply a
  range later if they choose one.

## 3. Finding: the register's own "cold cells" proxy is not climatically uniform

Per-cell `climate_zone` / EPW, read from each cell's `02a_climate_epw.parquet` (plan step 2, "state
which EPW each cell used rather than assuming climate from the city name"):

| cell | ASHRAE zone | EPW station |
|---|---|---|
| austin_centre / urban | 2A | Camp Mabry ANGB |
| austin_suburban | 2A | Austin Exec AP |
| austin_rural | 3A | Horseshoe Bay Resort |
| la_centre / urban | 3B | LA Downtown-USC |
| la_suburban | 3B | Torrance Muni |
| la_rural | 3B | Lancaster-Fox Field |
| **nyc_centre / urban** | **4A** | Central Park Obs |
| **nyc_suburban** | **4A** | Uniondale-Mitchel AFB |
| **nyc_rural** | **6A** | Hudson River Reserve |

`nyc_centre` (the method-bounds doc's other "coldest cell") is ASHRAE **4A**, mixed-humid — the same
zone as `nyc_suburban` and `nyc_urban`, and not meaningfully colder than them. Only **`nyc_rural`
(6A)** is actually a cold zone under the standard ASHRAE definition. So under the criteria in §2, the
fleet's only cold-climate representation is one cell, not two.

## 4. Population size

Fleet-wide (all 12 cells, `simulation_status == 'success'`): **8,153** buildings. `footprint_area_m2
<= p35` (per-cell): **2,855** buildings fleet-wide — but almost none of them are also cold, because
only `nyc_rural` qualifies as cold:

| cell | n_success | n_small (p35) | n_small_and_cold |
|---|---|---|---|
| nyc_rural | 198 | 69 | **69** |
| all other 11 cells | 7,955 | 2,786 | 0 |

**n = 69**, all in `nyc_rural`. By archetype: `SmallOffice` 56, `MidriseApartment` 7,
`OpenUBEMUnknown` 5, `SmallHotel` 1. `levels` in this population: min 1, median (SmallOffice) 1, max
tracked in the CSV per archetype — dominated by 1-storey buildings.

**No minimum sample size for the √S test is stated anywhere**, so n=69 cannot be checked against a
threshold; it is reported as-is.

## 5. Answer

**n = 69, concentrated entirely in `nyc_rural`, dominated by one archetype (`SmallOffice`, 56/69).**
This is larger than the n=8 the untrimmed-sample task had, but it is a single cell and mostly one
archetype — not the archetype-matched, multi-cell spread a size-stratified test would want. **The
existing corpus is a filter away for a first look, but not a substitute for a purpose-built sample**:
widening "cold" to include `nyc_centre`/`nyc_suburban`/`nyc_urban` (4A) would multiply n several-fold
but at the cost of the climate condition the test is meant to isolate — that trade is the user's to
make, not this task's.

One sentence on new simulation: **no new simulation is needed to take a first cut at n=69 today**
(all are `auto`-mode `success` rows with published EUI); a broader or archetype-balanced sample would
still need new runs, since `nyc_rural`'s archetype mix does not span the full 9-archetype set.

## Remedy shape (NOT applied)

None proposed — this task sizes, it does not remediate.

## How-to-test results

- **C18** — every criterion is either quoted with file:line (§1) or labelled `EXECUTOR-PROPOSED` (§2).
  No unlabelled criterion. ✅
- **C19** — the qualifying set is `simulation_status == 'success'` only, applied before the
  small/cold filters (script line: `ok = res[res["simulation_status"] == "success"]`). ✅
