# MEASUREMENT — OPEN-35: how many buildings sit on the undecided branch (2026-08-21)

> Executes T05 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-live-items-2026-08-21.md`.
> Measurement only. No fallback picked, no production file touched.
> Script: `scripts/analysis/open35_fallback_population_2026-08-21.py`
> CSV: `openubem/outputs/comparisons/open35_fallback_population_2026-08-21.csv`

## Locating `archetype_source` (per the plan's instruction)

`archetype_source` is not persisted anywhere in the adopted run's own artifacts:
`evidence/open48_refleet4/<cell>/04_simulation_manifest.parquet` (12 columns) and
`.../step3/03_idf_manifest.parquet` (10 columns) were both checked directly — neither carries it.

It **is** on disk: `openubem/outputs/comparisons/open35_fallback_agreement_scope.csv` (8,160 rows,
produced 2026-08-19 by `scripts/analysis/open35_fallback_agreement_scope_2026-08-19.py`, which reads
`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`). Verified before
use that this is the same population as `evidence/open48_refleet4`, not a stale or different fleet:
for `austin_centre`, identical `osm_id` sets (413/413) and identical null-`height_m` counts (349/349)
between the two paths. Per the plan's instruction ("locate it... if no on-disk artifact carries
`archetype_source`, stop") — one exists, and it is reused rather than re-running the classifier.

## Method

For each of the 8,160 buildings: `_archetype_consumed_group_median(row)`
(`openubem/geometry/footprint.py:91-95`) applied directly to the `archetype_source` value. For the
resulting population, the **current** storey count is computed with the same call the production
wiring makes (`_derive_num_floors_wired`, `openubem/idf/builder.py:162-176`): `derive_num_floors`
with `use_class`, and `levels_group_median`/`levels_global_median` from
`BuildingClassifier()._build_levels_median_lookup(gdf)`, fit per cell (matching production's
per-cell IDF-generation scope). The **pre-OPEN-35** storey count is `derive_num_floors(row)` with no
keyword arguments — which, for this population (both `levels` and `height_m` null by construction),
always falls through branch 3 (no group-median dicts supplied) to `return 1`.

## Population found

**39 buildings**, six cells:

| cell | n |
|---|---:|
| austin_rural | 17 |
| nyc_centre | 8 |
| austin_centre | 5 |
| nyc_urban | 5 |
| la_urban | 3 |
| austin_suburban | 1 |
| **total** | **39** |

This is nearly **twice** the 21-building sample OPEN-35's regression work has been reasoning about.

## Test status

- **C11 — pass.** Every one of the 39 has both `levels` and `height_m` null (0 counter-examples,
  checked and asserted in the script, not merely claimed).
- **C12 — pass.** All 21 buildings in the existing OPEN-35 sample
  (`changed_scope_b == True` in `open35_fallback_agreement_scope.csv`, matching
  `extra/MEASUREMENT_open-35_regression-population.md`'s "21-building Scope-B set") are inside this
  task's 39. No difference to explain.

## What the two rules cost, and the pooled-EUI denominator stake

Of the 39, **38 were simulated successfully** in the adopted run; the 39th
(`nyc_centre / way/266034056`) is the known dropped OPEN-35 regression building
(`not_simulated`, no published `floor_area_m2`).

For the 38 successfully-simulated members, `05_results.csv`'s `levels`/`height_m` columns confirm
the **current** branch is exactly what production used (e.g. `nyc_centre / way/260180778`:
`levels=19.0`, `height_m=66.5` — the group-median value this task recomputes independently, byte for
byte). Their published `floor_area_m2` (`floor_area_provenance = eio_simulated`, i.e. EnergyPlus's
own zone-area accounting, not a flat footprint×floors multiply) sums to **839,313.9 m²**. Under the
pre-OPEN-35 branch (1 floor each), the same 38 buildings' footprint-area-based floor area would sum
to **59,157.9 m²**.

**Fleet floor-area denominator (Σ `floor_area_m2` over all 8,153 successfully-simulated buildings,
fleet-wide) = 24,333,586.4 m².** Swapping only these 38 buildings from the current branch to the
pre-OPEN-35 branch would take that denominator to **23,553,430.3 m²** — a **-3.21 %** shift.
**Denominator only, per the plan's instruction — the pooled EUI headline itself is not restated
here.**

(Cross-check, not a discrepancy: a naive footprint×floors recomputation of the "current" branch
gives 780,577.7 m² for the same 38, about 7 % below the EIO-published 839,313.9 m² — this is
expected, because `floor_area_m2` is EnergyPlus's actual simulated zone area, not a flat multiply;
the storey **count** — the thing that actually decides which branch a building is on — matches
production exactly for every row checked.)

## Remedy shape (NOT applied)

None. Which of the two branches OPEN-35 should keep is the user's ruling, not this task's; this task
only supplies the size (39, not 21) and the denominator stake (-3.21 % on the 38 that would flip).
