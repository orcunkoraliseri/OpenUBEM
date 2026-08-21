# MEASUREMENT — OPEN-35 / board row C05: storey-fallback intervention with a control

> T04 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_four-board-items-2026-08-20.md`.
> **Status: STOPPED at the selection/verification stage. No EnergyPlus simulation was run.**
> One of the task's own pre-registered controls cannot be satisfied for the sample as specified
> (see §4). This report documents the selection, the two fallback-site citations, and the
> reason for the stop, per the plan's hard rule 2 (measurement tasks may not fix anything; a
> failed control is reported, not routed around) and the executor's explicit instruction to
> stop and report rather than continue past a failed control.

## 1. Population and scope

Source: `openubem/outputs/comparisons/open35_eui_consequence.csv` (8,160 rows — the register's
own C05/OPEN-35 evidence file). "Affected" = `neither == True` (both `levels` and `height_m`
missing on the raw input) **and** `levels == 1.0` as persisted (the population the register
sizes at 2,611/8,160).

Per the plan's step 1, the sample is restricted to the 8 cells the register itself names as
containing both affected and unaffected buildings: `austin_centre`, `austin_suburban`,
`austin_urban`, `austin_rural`, `la_centre`, `la_suburban`, `la_urban`, `nyc_centre`.
**`nyc_suburban` and `nyc_rural` are excluded entirely** — the register states neither has any
unaffected building at all, so within those two cells the comparison has no floor to stand on.

## 2. The two fallback sites (cited at HEAD, 2026-08-20)

| Path | Stage | Fallback when both `levels` and `height_m` are missing | Cite |
|---|---|---|---|
| `_impute_levels()` | archetype **selection** | `levels_group_median[use_class]` → `levels_global_median` → flat `1` (`LEVELS_DEFAULT_LOW`) | `openubem/semantic/building_classifier.py:137-156` |
| `derive_num_floors()` | geometry **construction** | as of the 2026-08-19 OPEN-35 T05/T06 wiring fix (director ruling 4.4a): flat `1` **unless** `_archetype_consumed_group_median(row)` is true, in which case it now consumes the SAME group/global median as the archetype-selection stage | `openubem/geometry/footprint.py:58-90`, gate at `footprint.py:91-95` |

**Correction to the plan's phrasing.** The plan's step 2 describes deriving the "other" fallback
candidate "from height." For this population (neither `levels` nor `height_m` present, by its
own definition) `_impute_levels()`'s height branch (`HEURISTIC_HEIGHT`, which divides `height_m`
by floor-to-floor height) can never fire — `height_m` is NaN for every candidate. The candidate
this population actually exercises is the group-/global-median branch. This is a wording
imprecision, not a conflict with the register or the DESIGN doc, so it did not trigger a STOP by
itself; it is flagged here so the two candidate values in §4 are read correctly.

**A second, load-bearing fact this citation surfaces.** `derive_num_floors()` is no longer
unconditionally flat-1 — production's builder (`openubem/idf/builder.py:453`, via
`_derive_num_floors_wired`) and parser (`openubem/results/parser.py:697-711`, via its own
`_derive_num_floors_wired`) now BOTH gate on `_archetype_consumed_group_median(row)`. For any
row where that gate is true, **today's production already builds and parses "as persisted" at
the group-median storey count, not at 1** — i.e. for that subset, "base = as built today
(levels = 1.0)" (plan step 2) is no longer actually true of current production, even though the
archived corpus the 2,611/1,031 count was measured from still shows `levels = 1.0` (that corpus
predates the 2026-08-19 fix). See §5.

## 3. Controls (pre-registered, written before any simulation was run)

1. The base arm's EUI must reproduce the fleet result already on record
   (`open35_eui_consequence.csv`'s `total_eui_kwh_m2`) for those same buildings to within 1 %.
   Per-building deltas for all 24 (not a summary).
2. At least 20 of 24 treated runs must complete with zero severe errors. Fewer → STOP and report.
3. Paired difference per building, the median, the sign split, and the within-cell medians,
   reported separately per cell — no pooling into one headline figure, and no restatement as a
   correction to the adopted fleet EUI.

Plus the plan's own How-to-test: **confirm the treated IDFs actually differ from base in storey
count for all 24** before any of the above are attempted.

## 4. Selection (step 1) and the census that step 4's control was checked against BEFORE building
   any IDF

For every affected candidate in the 8 cells, this task computed, from the enriched gdf
(`step2_classify_enrich`, run fresh, exactly as `open35_storey_intervention_2026-08-19.py` does):
`use_class`, the archetype-selection fallback value (`_impute_levels()`), whether that value is
`> 1` (`genuine_disagreement`), and whether today's `archetype_source` already carries the
`GROUPMEDIAN_LEVELS_MED` token (`archetype_consumed_group_median_today`). A candidate is only
usable for a clean paired intervention — one where "base = as built today, at 1 storey" is
actually still true and the treated arm is verifiably different — if `genuine_disagreement` is
true **and** `archetype_consumed_group_median_today` is false. 790 candidates were censused this
way across the 8 cells (`openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_census.csv`).

**Eligible pool per cell** (candidates satisfying both conditions):

| cell | affected candidates | eligible (usable) |
|---|---:|---:|
| austin_centre | 247 | 242 |
| austin_suburban | 74 | 3 |
| austin_urban | 43 | 43 |
| **austin_rural** | **244** | **0** |
| la_centre | 31 | 31 |
| la_suburban | 15 | 15 |
| la_urban | 29 | 26 |
| nyc_centre | 107 | 99 |

**`austin_rural` has zero eligible candidates out of 244** — checked exhaustively, not sampled.
For every one of its 244 affected buildings, across all 11 archetypes present (`SmallOffice` 176,
`RetailStandalone` 21, `MidriseApartment` 18, `OpenUBEMUnknown` 7, `QuickServiceRestaurant` 7,
`MediumOffice` 5, `Courthouse` 3, `FullServiceRestaurant` 3, `Outpatient` 2, `LargeOffice` 1,
`SuperMarket` 1), the archetype-selection fallback (`_impute_levels()`) also resolves to exactly
`1`. This is because `austin_rural`'s fleet-wide `levels_group_median` is `1` for every
`use_class` that has an observed-levels row in that cell — the two fallbacks **genuinely agree**
there; there is nothing to intervene on. This is deterministic given the population and cannot be
changed by choosing different buildings within the cell.

Selection for the other 7 cells drew 3 per cell from the eligible pool, tier-preferring the
register's own mid-/high-rise apartment population (`MidriseApartment`/`HighriseApartment`,
tier 0) first, then the wider mid-/high-rise set (`LargeOffice`/`LargeHotel`/`Hospital`, tier 1),
then any other archetype (tier 2), seed 42 for the within-tier draw.

**A second finding, from the same census, explains why 0/21 selected buildings carry the
register's headline mid-/high-rise apartment archetype.** Across the 8 cells there are only 25
`MidriseApartment`/`HighriseApartment` candidates left in the affected population at all (the
other ~1,000 of the register's 1,031 sit in the excluded `nyc_suburban`/`nyc_rural`). Of those 25,
6 show `genuine_disagreement`, but **24 of the 25 already carry
`archetype_consumed_group_median_today = True`** — i.e. today's production has already self-
corrected nearly all of the register's headline apartment population since the 2026-08-19 wiring
fix, leaving essentially none of it usable for this design. The 21 buildings actually selected
are 15 `LargeOffice` (tier 1) and 6 `Courthouse`/`SmallOffice` (tier 2, in `austin_suburban` and
`la_suburban`, where the tier-1 pool was too thin).

Selection table (21 of the intended 24 — see §5 for why 3 are missing), with both candidate
storey values and the on-record fleet EUI for the base-arm reproduction check (§3, control 1):

| cell | osm_id | archetype_id | base storeys | treated storeys | on-record EUI kWh/m² |
|---|---|---|---:|---:|---:|
| austin_centre | way/37417989 | LargeOffice | 1 | 5 | 106.98 |
| austin_centre | way/516285449 | LargeOffice | 1 | 5 | 113.01 |
| austin_centre | way/55932518 | LargeOffice | 1 | 5 | 108.48 |
| austin_suburban | way/206376503 | Courthouse | 1 | 3 | 115.71 |
| austin_suburban | way/221890776 | Courthouse | 1 | 3 | 142.73 |
| austin_suburban | way/382991813 | Courthouse | 1 | 3 | 120.62 |
| austin_urban | way/1206018498 | LargeOffice | 1 | 5 | 114.28 |
| austin_urban | way/243238233 | LargeOffice | 1 | 5 | 108.15 |
| austin_urban | way/312329732 | LargeOffice | 1 | 6 | 113.58 |
| la_centre | way/1012945102 | LargeOffice | 1 | 5 | 101.94 |
| la_centre | way/1106947213 | LargeOffice | 1 | 5 | 100.09 |
| la_centre | way/900894807 | LargeOffice | 1 | 5 | 100.13 |
| la_suburban | way/285843826 | Courthouse | 1 | 2 | 88.64 |
| la_suburban | way/449558400 | SmallOffice | 1 | 2 | 137.35 |
| la_suburban | way/449558402 | SmallOffice | 1 | 2 | 93.25 |
| la_urban | relation/6412968 | LargeOffice | 1 | 11 | 102.36 |
| la_urban | way/402036175 | LargeOffice | 1 | 11 | 96.13 |
| la_urban | way/402036182 | LargeOffice | 1 | 11 | 99.44 |
| nyc_centre | way/260085136 | LargeOffice | 1 | 19 | 123.06 |
| nyc_centre | way/260085159 | LargeOffice | 1 | 19 | 118.98 |
| nyc_centre | way/266170853 | LargeOffice | 1 | 19 | 119.12 |
| **austin_rural** | — | — | — | — | **no eligible candidate exists** |

## 5. Why this stops here

The plan's own How-to-test requires confirming, for **all 24**, that the treated IDF differs
from base in storey count, and the pre-registered controls forbid pooling across cells or
substituting a different cell for one the plan named. `austin_rural` cannot supply even one
building — let alone 3 — for which base and treated storey counts would differ, because the two
fallbacks genuinely agree there for every candidate. No selection strategy changes this outcome:
it was checked exhaustively over all 244 of the cell's affected buildings, not sampled.

Continuing with 21/24 (dropping `austin_rural`), or with 24 buildings where 3 are known in
advance to be a zero-difference pair, would each silently redefine a control the plan wrote as
mandatory. Per hard rule 2 (measurement tasks may not fix anything) and the explicit instruction
to stop rather than continue past a failed control, **no EnergyPlus simulation was run** and no
EUI, delta, or sign-split numbers exist for this task. Nothing published elsewhere is affected —
this is a pure non-result.

## 6. Recommended disposition (not decided here — decision on `austin_rural` and the tier
   substitution is the manager's, not the executor's)

Two independent scope questions need a ruling before this task can resume:
1. **`austin_rural`** — accept 21/7-cells instead of 24/8-cells, or replace it with a different
   cell also containing both affected and unaffected buildings, or note the zero-disagreement
   result as itself informative (a 9th "this cell's two fallbacks never actually disagreed"
   data point) and run 21 buildings + document the exception.
2. **Archetype mix** — the register's headline concern (mid-/high-rise apartment buildings) is
   almost entirely already self-corrected in the 8 in-scope cells' current production code
   (24/25 remaining candidates). The 21-building sample that IS available is dominated by
   `LargeOffice`/`Courthouse`/`SmallOffice`. Whether that is an acceptable substitute for "the
   1,031/1,119 subset" the plan asked to be preferred is a scope call, not a measurement one.

## Artifacts

- `scripts/analysis/open35_storey_intervention_2026-08-20.py` — census + selection (build/
  simulate code is present but was never invoked past the selection-stage STOP).
- `openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_census.csv` — all 790
  affected candidates across the 8 cells, both fallback values, eligibility flags.
- `openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_selection.csv` /
  `..._2026-08-20.csv` (same content, plan-named copy) — the 21-building selection table above.

---

# T04b — the intervention actually ran, on 21 buildings across 7 cells

**Appended 2026-08-20 by the director**, after CP-3 resolved the two scope questions §6 left open.
Rulings: **proceed on 21 buildings / 7 cells, do not substitute a cell**; `austin_rural` is recorded
as a **structural null (0 of 244)**; the office-heavy archetype mix is **accepted with the framing
corrected** rather than forced back onto an apartment population that no longer exists.

## T4b.1 What the two arms are

| arm | storey source | value | is this what production builds today? |
|---|---|---:|---|
| **base** | geometry fallback (`base_storeys_geometry_fallback`) | **1 for all 21** | **yes** — it is what the fleet run on record used |
| **treated** | archetype fallback (`treated_storeys_archetype_fallback`, the levels-group median) | 2 to 19 | no |

Every one of the 21 has `archetype_consumed_group_median_today = False` and
`genuine_disagreement = True`. So this is a **paired within-building** intervention: same building,
same weather, same archetype, one input changed. That is the design OPEN-35 needed and the reason
the naive +62.20 kWh/m2 composition gap could never answer it.

## T4b.2 The three pre-registered controls — all three pass

| # | control | threshold | measured | verdict |
|---|---|---|---|---|
| 1 | every base-arm EUI reproduces `on_record_total_eui_kwh_m2` | within **1 %** | worst case **0.0199 %**; 0 of 21 outside | pass |
| 2 | treated runs complete with no severe error | **>= 18 of 21** | **19 of 21**; all 21 completed, **0 fatal** | pass |
| 3 | every treated IDF storey count differs from its base IDF, read from the built IDF | **21 of 21** | **21 of 21**; 0 identical pairs | pass |

Control 1 at 0.02 % is the strong result here: the harness reproduces the production fleet number on
the untouched arm, so the treated arm's movement is the intervention and not the harness. This is
the control OPEN-58 taught the project to run, and it is the reason these numbers are usable at all.

The two severe-error rows (`way/516285449`, `way/382991813`) each carry **one** severe and no fatal,
and both completed. They are retained and flagged, not dropped.

## T4b.3 Result — within-cell medians only

**Reported per cell. Never pooled into a headline, never restated as a fleet EUI correction, never
carried back onto OPEN-35's stale 1,031-building framing.**

| cell | n | median change | median delta | range |
|---|---:|---:|---:|---|
| la_centre | 3 | **+75.25 %** | +76.71 kWh/m2 | +65.36 to +78.28 |
| austin_suburban | 3 | **+73.58 %** | +90.51 | +57.75 to +78.22 |
| austin_centre | 3 | **+73.09 %** | +79.28 | +68.49 to +85.31 |
| austin_urban | 3 | **+70.28 %** | +76.01 | +37.51 to +74.90 |
| nyc_centre | 3 | **+59.88 %** | +71.24 | +58.37 to +68.02 |
| la_urban | 3 | **+37.89 %** | +37.25 | +36.39 to +58.28 |
| **la_suburban** | 3 | **-2.58 %** | -2.41 | **-11.31** to +61.68 |
| **austin_rural** | **0** | **structural null** | — | two fallbacks agree for all 244 |

## T4b.4 What the cell split is really measuring, and it is not the cell

The cell medians are ordered almost entirely by **how many storeys the treated arm added**, not by
climate or by density tier:

| treated storeys | n | behaviour |
|---|---:|---|
| 19 (nyc_centre) | 3 | +58 to +68 % |
| 11 (la_urban) | 3 | +36 to +58 % |
| 5 or 6 | 9 | +65 to +85 % |
| 3 (Courthouse) | 3 | +58 to +78 % |
| **2** | 3 | **-11.31 %, -2.58 %, +61.68 %** |

The two negative rows are both `SmallOffice` in `la_suburban` going **1 to 2 storeys**
(`way/449558400` -11.31 %, `way/449558402` -2.58 %). In a mild climate, giving a small office a
second floor spreads roof and ground losses over twice the area and improves the surface-to-volume
ratio faster than it adds load. **The sign of this defect is not fixed** — it is negative for small
buildings in mild climates and strongly positive everywhere else. That is a genuine finding and it
would have been erased by pooling.

By archetype: `LargeOffice` n=15 median **+68.02 %**, `Courthouse` n=4 median **+67.63 %**,
`SmallOffice` n=2 median **-6.95 %**.

## T4b.5 What may and may not be said

**May be said.** For the buildings where OPEN-35's two storey fallbacks genuinely disagree, the
choice of fallback is **not a rounding matter**: it moves a single building's EUI by a within-cell
median of **-2.6 % to +78.3 %**, measured on a paired within-building intervention with the base arm
reproducing the fleet record to 0.02 %. Six of seven cells move strongly upward. Production uses the
**lower** arm for all 21.

**May not be said.**
- Not a fleet correction. 21 buildings out of 8,153 do not restate **153.8231 kWh/m2**, and this
  measurement does not attempt to.
- Not a population estimate. The 21 are the **eligible** buildings, i.e. selected precisely because
  the two fallbacks disagree. The 459 eligible in the seven cells are the sampling frame; buildings
  where the fallbacks agree are unaffected by construction.
- Not about apartments. The register's original mid-/high-rise apartment framing is **stale** and
  corrected at CP-3: 25 candidates remain in the eight cells, 24 already build at the group median,
  0 are eligible. This sample is `LargeOffice` (15), `Courthouse` (4), `SmallOffice` (2).
- Not a remedy. Which fallback is *correct* is not settled here. This measures the size of the
  disagreement, not its direction of truth.
- **OPEN-61 contamination is present and untreated.** Both arms are parsed by the same
  `total_eui_kwh_m2`, which drops District Heating from Water Systems. It is a common-mode omission
  in a paired difference and is far below the effect sizes above, but it is on the record.

## T4b.6 Artifacts

- `scripts/analysis/open35_storey_intervention_runs_2026-08-20.py` — 42 paired EnergyPlus runs.
- `openubem/outputs/comparisons/open35_storey_intervention_runs_2026-08-20.csv` — 21 rows, both
  arms, all three control columns.
- `openubem/outputs/comparisons/open35_storey_intervention_2026-08-20_selection.csv` — the frozen
  selection, written before any simulation.
