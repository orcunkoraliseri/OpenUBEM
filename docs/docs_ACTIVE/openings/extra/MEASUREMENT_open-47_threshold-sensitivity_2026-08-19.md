# MEASUREMENT — OPEN-47 T06: how much of the fine-classification error is the two untraced size thresholds?

**Task:** T06, `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-items-2026-08-19.md`
**Date:** 2026-08-19
**Script:** `scripts/analysis/open47_threshold_sweep_2026-08-19.py`
**Outputs:** `openubem/outputs/comparisons/open47_threshold_sweep.csv` (782 rows),
`openubem/outputs/open47_threshold_sweep_surface.png`
**Fixture (every figure below):** `tests/fixtures/labelled_archetypes_tagrich_v2.csv`, 98 graded
rows (2 `UNDETERMINED` excluded), per OPEN-22's binding naming rule. Neither the fixture nor the
old 50-row fixture was touched. `openubem/semantic/building_classifier.py` was not edited — the
two thresholds were monkeypatched in-process, in a `try/finally`, restored before the script
exits, and the restoration is asserted and printed.

## 1. Mandatory control — reproduced exactly

At today's values (`_OFFICE_SMALL_MAX_M2 = 2322.0`, `_OFFICE_MEDIUM_MAX_M2 = 9290.0`):

```
n_graded=98  fine=87/98 = 0.8878  coarse=98/98 = 1.0000
```

Matches `extra/FIX_open-22_tagrich-gate.md` to four decimals. The sweep proceeded.

## 2. Grid

Jointly over `_OFFICE_SMALL_MAX_M2` and `_OFFICE_MEDIUM_MAX_M2`:
- 25 points evenly spaced over ±50% of each current value (small: 1161.0–3483.0 m²; medium:
  4645.0–13935.0 m²),
- plus the exact CBECS general size-bin edges bracketing each threshold (EIA CBECS 2018
  flipbook, p.9 — the same table `RESEARCH_open-47_threshold-provenance.md` already verified):
  10,000 / 25,000 / 50,000 ft² for the small threshold, 50,000 / 100,000 / 200,000 ft² for the
  medium threshold, converted at 1 ft² = 0.09290304 m².

28 × 28 = 784 combinations, 2 skipped where `small_max ≥ medium_max` (invalid ordering) → **782
scored grid points.**

## 3. Result — the two thresholds explain none of the 11 fine errors

**Zero of the 782 settings beats 88.8% fine top-1.** The maximum fine accuracy anywhere on the
grid is 0.8878 (87/98) — the current setting — tied by 28 grid points, all clustered tight around
today's values (small_max ∈ [2322.0, 2515.5], medium_max ∈ [8128.75, 10064.17]).

**Of the 11 baseline fine errors, zero are fixed under any of the 782 settings.** Every point on
the grid that differs from the tied plateau scores *strictly worse* than baseline — never better —
because moving either threshold only ever breaks previously-correct rows (31 distinct rows are
broken by at least one setting somewhere on the grid; the worst point, small_max=4645.15 /
medium_max=5032.08, drops to 68.4%). **Widening or narrowing the office bins purely trades correct
classifications for incorrect ones; it never recovers any of the 11.**

**Coarse top-1 is 100.0% (98/98) at every one of the 782 grid points, with no exception.** This
follows directly from `_COARSE_CLASS_MAP`: every office archetype (`Small/Medium/LargeOffice`,
detailed or not) maps to `"commercial"`, so moving the boundary between them can never change a
prediction's coarse class. The office-size threshold is, by construction, invisible to the coarse
metric.

## 4. Why the sweep can't touch these 11 — traced per row

`openubem/outputs/comparisons/open22_v2_fixture_breakdown.csv` (already on disk from OPEN-22)
gives each error's rule token. Of the 11:

| osm_id | expected | emitted (baseline) | rule token | reachable by this sweep? |
|---|---|---|---|---|
| 405668761 | MidriseApartment | HighriseApartment | RULE_RESIDENTIAL_TIER | **no** — never calls `_office_size_tier` |
| 147478372 | MidriseApartment | HighriseApartment | RULE_RESIDENTIAL_TIER | **no** |
| 147486325 | LargeHotel | TallBuilding | RULE_HIGHRISE | **no** |
| 29650708 | **OpenUBEMUnknown** | MediumOffice | FALLBACK_SIZE_DEFAULT | **no** — `_office_size_tier` only returns Small/Medium/LargeOffice, never `OpenUBEMUnknown`; the error is *entering* this rule branch at all, not where its output lands inside it |
| 1175801196 | **OpenUBEMUnknown** | MediumOffice | FALLBACK_SIZE_DEFAULT | **no**, same reason |
| 1175853280 | **OpenUBEMUnknown** | MediumOffice | FALLBACK_SIZE_DEFAULT | **no**, same reason |
| 124873930 | SmallOffice | LargeOffice | RULE_USE_CLASS_SIZE | in principle yes — but footprint 657 m², so the gap is driven by `levels_imputed`, not the bin edge (see below) |
| 147776396 | SmallOffice | LargeOffice | RULE_USE_CLASS_SIZE | same |
| 148164098 | SmallOffice | LargeOffice | RULE_USE_CLASS_SIZE | same — footprint only 611 m²; total floor area only exceeds even the widest swept medium edge (18,580.6 m², the 200,000 ft² CBECS bin) if `levels_imputed` is implausibly large |
| 148164123 | SmallOffice | MediumOffice | RULE_USE_CLASS_SIZE | same |
| 148685510 | MediumOffice | LargeOffice | RULE_USE_CLASS_SIZE | same |

**3 of the 11** never reach `_office_size_tier` at all (residential-tier / high-rise rules) — the
sweep is structurally irrelevant to them. **3 of the 11** are `OpenUBEMUnknown` expected against an
office emitted — the sweep can move which office tier is emitted but can never emit
`OpenUBEMUnknown`, so these are also structurally unreachable. **The remaining 5** do route through
`_office_size_tier`, but their footprint areas (577–2,005 m²) are small enough that the emitted
tier can only be this far off if `levels_imputed` (from `_impute_levels`, not from either swept
constant) is driving `total_floor_area_m2 = footprint × levels_imputed` past the threshold
regardless of where in this defensible band the threshold sits — consistent with the sweep's
empirical finding that no point in the grid recovers them.

## 5. Answer to T06's question

**How much of the fine-classification error is the two untraced size thresholds? None of it, on
this fixture, over a defensible ±50% + neighbouring-CBECS-edge grid.** All 11 fine errors are
driven by upstream classification path decisions (which rule branch is entered; imputed floor
count) that the two size-bin constants do not control. The plateau containing today's values is
narrow (28/782 grid points, roughly ±8% of the small edge and ±9%/+8% of the medium edge) but it
is a *tie*, not a peak — nothing on the grid beats it, and every deviation from it is strictly
worse or unchanged. Coarse accuracy is 100% everywhere and cannot be moved by this axis at all.

**This is not a "the untraced numbers are harmless because accuracy is flat" result and not a
"they are sharply load-bearing" result either — it is a third outcome the plan's §"Why" framing
did not name: the untraced numbers are not what is producing the residual error, in either
direction.** OPEN-47's provenance question (Chen, Hong & Piette 2017, a case-study table, not a
cited external standard) stands on its own footing; this measurement does not change it. What this
measurement settles is narrower and specific to OPEN-47's item text: **the 11 fine errors handed
to OPEN-47 by OPEN-22's closure are not evidence that the office bin edges are wrong** — closing
the item cannot lean on "the errors would go away at better thresholds," because none do.

## 6. What this task did not do (per plan constraint)

**No threshold was changed in the shipped module.** No recommendation is made to change
`_OFFICE_SMALL_MAX_M2` / `_OFFICE_MEDIUM_MAX_M2` — the finding is that no setting in the swept
range does better, so there is nothing to recommend on this axis. Any future fix for the 5
`RULE_USE_CLASS_SIZE` / `FALLBACK_SIZE_DEFAULT` rows would need to look at `_impute_levels` or the
rule-entry conditions, not the size bins — that is a recommendation for a **different** item's
scope, not taken here, and not filed as a new item without a director ruling.
