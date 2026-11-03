# MEASUREMENT — OPEN-35: T04 stops at the ceiling; no production code changed

**Task:** T04, `PLAN_board-17-ready-2026-08-19.md`
**Date:** 2026-08-19
**Script:** `scripts/analysis/open35_fallback_agreement_scope_2026-08-19.py`
**Output:** `openubem/outputs/comparisons/open35_fallback_agreement_scope.csv` (8,160 rows)

---

## Verdict, first line: STOP AND REPORT. No production code was changed, no tests were added.

Plan §4.4 pins: *"A fix that changes more than 11 buildings' geometry is out of scope — stop
and report it"* and *"If your change moves MORE than 11, stop and report — that means the
diagnosis was wrong, not that the ceiling was too low."* Both candidate implementations of
"make both fallbacks consume the same value" measured below exceed 11. Per that rule, this
task stops here rather than landing a change and rationalizing the overrun.

## 1. Which fallback is wrong — settled, not the issue

§4.4 already resolves this: *"the geometry side is the one that ignores the available
median"* — `derive_num_floors()` (`openubem/geometry/footprint.py:58-63`) defaults to `1`
when both `levels` and `height_m` are missing, while `_impute_levels()`
(`openubem/semantic/building_classifier.py:137-156`) already falls back to a group- or
global-median storey count for the same case. This is not in dispute and this task did not
re-litigate it.

## 2. Two ways to implement "make geometry consume the median too" — both measured

Both scopes were computed fleet-wide (all 12 `phaseE` cells, 8,160 buildings), from the
existing Step-1 `01_buildings.gpkg` files — no fleet re-run, no simulation, no
re-classification. Method: recompute `derive_num_floors()`'s current output and a proposed
new output side by side for every row.

**Scope A (naive) — apply the median to every building with both `levels` and `height_m`
missing, regardless of whether the archetype decision ever consumed it:**

**509 buildings change.** This changes geometry for buildings whose archetype rule never
looked at `levels_imputed` at all — e.g. office tiering under the default
`use_floor_count=False` (OPEN-47) is area-only and ignores levels entirely, so "fixing"
those buildings' geometry to match a value the archetype stage never used is not what OPEN-35
describes; it is a new, unrelated behaviour change.

**Scope B (principled) — apply the median only where the archetype rule that actually fired
consumed the imputed levels for its decision**, detected the same way the classifier already
marks it internally: `archetype_source`'s first token is in `_LEVELS_CONSUMING`
(`RULE_HIGHRISE`, `RULE_RESIDENTIAL_TIER`, `RULE_LODGING_TIER`,
`building_classifier.py:70-72`) and the imputed source is not `OSM_OBSERVED`
(`building_classifier.py:635-639` — this is the exact condition the classifier itself uses
to decide whether to append the `HEURISTIC_*`/`GROUPMEDIAN_LEVELS_MED` provenance token).
This is the narrowest defensible reading of "make both consume the same fallback": only
touch geometry where archetype selection actually disagreed with it.

**21 buildings change.** Still exceeds the ceiling of 11.

## 3. The 21 contain all 11 of OPEN-35's census, plus 10 the census excluded

`open35_storey_intervention_results_v2.csv`'s 11 treatment-arm buildings are a **strict
subset** of Scope B's 21 (verified by set difference — zero missing). The other **10** are
all `LargeHotel` archetype, assigned via `RULE_LODGING_TIER` (2 in `austin_centre`, 8 in
`nyc_centre`), imputed to 5 and 19 storeys respectively by the same `GROUPMEDIAN_LEVELS_MED`
mechanism:

| cell | osm_id | new floors | archetype |
|---|---|---:|---|
| austin_centre | way/231123149 | 5 | LargeHotel |
| austin_centre | way/328723692 | 5 | LargeHotel |
| nyc_centre | way/260180778, way/265301856, way/266034056, way/266170756, way/266170763, way/283346493, way/288448678, way/293183674 | 19 (each) | LargeHotel |

**Why OPEN-35's own census missed these:** `MEASUREMENT_open-35_storey-intervention.md` §1
scoped its census to *"the 1,031 buildings given a mid/high archetype"*, which it defined as
`MidriseApartment` (1,028) + `HighriseApartment` (3) only — the register's own table lists
those two rows as "mid/high archetype" and stops there. `RULE_LODGING_TIER` routes through
the identical `_LEVELS_CONSUMING` code path and can equally assign a multi-storey archetype
(`LargeHotel`) off an imputed group median, but it was never counted because "mid/high
archetype" was read as "apartment archetype" rather than "any archetype whose rule consumes
levels_imputed."

## 4. This is the plan's own anticipated failure mode, not a new one

§4.4: *"If your change moves MORE than 11, stop and report — that means the diagnosis was
wrong, not that the ceiling was too low."* The diagnosis that was wrong is not "which fallback
to fix" (that is settled, §1 above) — it is **the size of the population the fix touches**.
The 11-building ceiling came from a census that under-covers the mechanism it was measuring
by excluding `RULE_LODGING_TIER`. A fix landed today, scoped either way, would either (Scope
A) touch 509 buildings including many with no real archetype/geometry disagreement, or (Scope
B) touch 21, correctly scoped to the actual mechanism but still 10 over the pinned ceiling.

**No fix was implemented. No file under `openubem/` was touched. No test file was written**
— the plan's required tests (`tests/test_storey_fallback_agreement.py`) describe behaviour of
a fix that was not landed, so writing them now would either test nothing real or force a
choice between Scope A and Scope B that is a director decision, not this task's to make.

## 5. Recommendation, not a ruling

Two ways forward, both requiring a director decision:
1. **Extend OPEN-35's census** to include `RULE_LODGING_TIER` cases (bringing the true
   population to 21) and re-set the ceiling to match, then land Scope B.
2. **Scope the fix to exactly OPEN-35's original 11** (residential/apartment archetypes
   only, i.e. restrict Scope B further to `head in {RULE_RESIDENTIAL_TIER, RULE_HIGHRISE}`),
   leaving the 10 `LargeHotel` cases as a newly-discovered, separate sub-finding for the
   register rather than folding them into this fix silently.

Evidence for either path: `openubem/outputs/comparisons/open35_fallback_agreement_scope.csv`
(8,160 rows, both scopes' proposed values and change flags per building).

---

## Addendum, 2026-08-19 — director ruling 4.4a landed: Scope B implemented and verified

**Ruling (plan §4.4a):** the ceiling of 11 was wrong, not the diagnosis. Scope B (21
buildings) is ADOPTED; Scope A (509) is REJECTED. The fix below implements Scope B only.

### What changed

`openubem/geometry/footprint.py` — `derive_num_floors()` only. New optional keyword-only
parameters mirroring `_impute_levels()`'s own extras exactly: `use_class`,
`levels_group_median`, `levels_global_median`. When `levels` and `height_m` are both
missing, the function now falls back to the group-/global-median **only if**
`row["archetype_source"]` carries a `GROUPMEDIAN_LEVELS_MED` token — the same population
`_impute_levels()`/the classifier's own token-assembly gate on (`archetype_source`'s first
token in `_LEVELS_CONSUMING` and imputed source `!= OSM_OBSERVED`). No call site was
changed (`idf/builder.py`, `results/parser.py`, `results/aggregator.py` all still call
`derive_num_floors(row)` positionally, unmodified); every pre-existing call is therefore
byte-identical to its pre-fix behaviour. `openubem/semantic/building_classifier.py` was
**not modified** — geometry is the only side that moved, per §4.4.

### Tests

`tests/test_storey_fallback_agreement.py` (new, 7 tests) — both fallbacks agree on the
Scope B population (group-median and global-median branches), a building with observed
`levels`/`height_m` is unaffected, a cell with no storey data anywhere returns 1 from
both, and two negative tests proving the Scope A/B boundary (a non-levels-consuming rule,
and an `archetype_source` without a `GROUPMEDIAN_LEVELS_MED` token, are never touched even
when both `levels`/`height_m` are missing and a median is available). All pass; the
pre-existing `tests/test_footprint.py` (5 `derive_num_floors` cases) is unaffected.

### Fleet-wide membership verification

`scripts/analysis/open35_scope_b_verify_2026-08-19.py` calls the **landed** production
`derive_num_floors()` (not a reimplementation) across all 12 `phaseE` cells, 8,160
buildings, existing Step-1 `01_buildings.gpkg` files only — no re-classification, no
simulation, no fleet re-run. Result: **exactly 21 buildings change**, set-identical to
`changed_scope_b == True` in `open35_fallback_agreement_scope.csv` (0 missing, 0 extra).
Per-cell: `austin_centre` 5, `la_urban` 3, `nyc_centre` 8, `nyc_urban` 5 — matches §4.4a's
own breakdown (`MidriseApartment` 8 / `HighriseApartment` 3 / `LargeHotel` 10).

No local EnergyPlus run was performed — this task's scope is the agreement fix and its
tests, not an EUI-impact re-measurement; OPEN-35's own storey-intervention EUI impact was
already measured in `MEASUREMENT_open-35_storey-intervention.md` for the 11-building
census subset.
