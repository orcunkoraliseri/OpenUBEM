# MEASUREMENT — OPEN-38 x OPEN-56: are the 44 fatals volume-anomalous?

**Date:** 2026-08-21
**Task:** T07 of `implemenation/previous/PLAN_ten-live-items-2026-08-21.md`
**Script:** `scripts/analysis/open38_open56_zone_volumes_2026-08-21.py`
**Inputs:** `openubem/outputs/comparisons/open38_fatal_causes_2026-08-20.csv` (44 rows),
`openubem/outputs/comparisons/open56_open09_run4_err_census_2026-08-20.csv` (8,160 rows),
E02 harvest `.eio` files.
**Outputs:** `openubem/outputs/comparisons/open38_open56_zone_volumes_2026-08-21.csv`
(2,040 zone rows), `openubem/outputs/comparisons/open38_open56_zone_volumes_by_building_2026-08-21.csv`
(70 building rows).

## Controls

- **C15 — coverage.** All 44 fatal `(cell, mode, stem)` triples were checked; **23 of 44 had a
  readable `eplusout.eio`, 21 did not.** The 21 missing are listed individually in the script's
  stdout and reproduced below. Each missing directory has `.end`, `.err`, `.sql` present but no
  `.eio` — this is not a parse failure, the file is simply absent from the harvest for those runs.
- **C16 — hand-check.** `la_rural_auto/way_472960972`, zones `F0_PERIM1`/`F1_PERIM1`/`F2_PERIM1`:
  raw `.eio` gives volume 190.65 m³, floor area 54.47 m², ceiling height 3.50 m for all three;
  the script's CSV output matches to the printed precision. Passed.
- **C17 — control independence.** The control was drawn `random.seed(2026)`, without
  replacement, and the overlap check against the 44-member fatal set returned **0**. Passed.

## Finding before the results: F5 does not generalise past its one verified example

F5 (plan §5) states "`.eio` carries per-zone volume even for runs that died fatal," verified on
one building. **A plain existence walk of the whole E02 harvest** (40,800 `<cell>_<mode>/<stem>`
directories) found **only 145 have an `eplusout.eio` at all — 0.36 %.** F5 is true of the one
building it names, but it is not a property of the harvest; `.eio` retention looks close to
absent except for a small, apparently unsystematic set of directories. Consequence for this
task:

- Only **23 of the 44** fatal buildings could be read (52.3 %), not all 44.
- The control was **re-specified to draw only from `.eio`-present candidates** within each
  `(cell, mode)` combo present in the 44, rather than sampling blind against the full directory
  listing and hoping enough resolved (an earlier blind draw of 200 produced only 7 readable
  buildings — reported here for transparency, then discarded in favour of the eio-filtered draw).
  Even after that fix, most of the required combos are eio-starved:
  `la_centre_auto` 0 available, `la_centre_floor` 0, `nyc_centre_auto` 0,
  `nyc_rural_layout_assign` 0, `nyc_centre_fast_zone` 1, `la_centre_layout_assign` 0,
  `la_rural_auto`/`la_rural_fast_zone`/`la_rural_floor` 10 each, `la_urban_layout_assign` 12.
  **The proportionally-allocated target of 200 controls could not be met; 47 were drawn** — every
  eio-having candidate available in the required combos, none left unsampled.

This is reported as the result, per hard rule 3, not smoothed into a full-200 control.

### The 21 fatals with no `.eio`

`la_centre/auto/way_319507579`, `la_centre/floor/way_428015178`,
`la_rural/auto/way_472961047`, `la_rural/auto/way_472961092`,
`la_rural/fast_zone/way_472961047`, `la_rural/fast_zone/way_472961089`,
`la_rural/fast_zone/way_472961090`, `la_rural/fast_zone/way_472961093`,
`la_rural/fast_zone/way_472961164`, `la_rural/floor/way_472961047`,
`la_rural/floor/way_472961164`, `nyc_centre/auto/way_266149332`,
`nyc_centre/auto/way_266170765`, `nyc_centre/fast_zone/way_265301877`,
`nyc_centre/fast_zone/way_265301889`, `nyc_centre/fast_zone/way_265302168`,
`nyc_centre/fast_zone/way_266149332`, `nyc_centre/fast_zone/way_266170540`,
`nyc_centre/fast_zone/way_266170544`, `nyc_centre/fast_zone/way_266170765`,
`nyc_centre/fast_zone/way_292840084`.

## Results, on the buildings that could be read (23 fatal, 47 control)

**Volume-degenerate zones** (`volume_m3 <= 0`, or the volume disagrees with `floor_area × ceiling
height` by more than 1 %):

| group | zones | degenerate | rate |
|---|---|---|---|
| fatal | 844 | 162 | 19.19 % |
| control | 1,196 | 50 | 4.18 % |

**Per-building — at least one degenerate zone:**

| group | buildings | any degenerate | rate |
|---|---|---|---|
| fatal | 23 | 6 | 26.09 % |
| control | 47 | 16 | 34.04 % |

The zone-level rate is ~4.6x higher in the fatal group; the per-building rate is not higher in
the fatal group (it is slightly lower). The two readings disagree because a small number of
fatal buildings carry many zones each (see volume distribution below), so zone-level and
building-level degenerate rates move in different directions.

**Volume distribution (m³), zone-level:**

| group | n | mean | median | q25 | q75 | min | max |
|---|---|---|---|---|---|---|---|
| fatal | 844 | 1,098.67 | 41.89 | 11.52 | 137.78 | 2.87 | 78,552.81 |
| control | 1,196 | 1,220.41 | 453.16 | 324.53 | 824.49 | 10.00 | 15,072.61 |

**Volume distribution (m³), per-building median:**

| group | n buildings | mean of medians | median of medians | q25 | q75 |
|---|---|---|---|---|---|
| fatal | 23 | 4,661.47 | 88.70 | 13.75 | 301.60 |
| control | 47 | 960.45 | 305.31 | 10.00 | 995.45 |

The fatal group's zone volumes skew markedly smaller at the median (41.9 m³ vs 453.2 m³, roughly
11x smaller) but its mean and max are pulled far higher by a small number of very large zones
(one zone reaches 78,552.81 m³). The fatal group is not uniformly small-volume; it is bimodal —
mostly small zones with a few extreme outliers.

## The 86 % family (F7), checked and located precisely

F7 states "the 44 fatals are 86 % one family." Re-derived from `severe_class` in
`open38_fatal_causes_2026-08-20.csv`: **21 `Temperature (high) out of bounds` + 17
`CalcHeatBalanceInsideSurf` = 38/44 = 86.4 %.** (The remaining 6 are 5 `Temperature (low) out of
bounds` + 1 shadowing/non-convex — outside the family.) This resolves which subset "86 %" refers
to; F7 itself does not state the grouping rule.

Of the 23 readable fatals, 19 are in the 86 % family and 4 are not:

| family_86pct | n buildings | mean median-volume | median of median-volume | any-degenerate rate |
|---|---|---|---|---|
| True (86 % family) | 19 | 5,358.44 | 34.45 | 26.3 % |
| False (rest) | 4 | 1,350.89 | 249.40 | 25.0 % |

The 86 % family's per-building median volume (34.45 m³) is an order of magnitude smaller than
the non-family fatals (249.40 m³), but the degenerate-zone rate is essentially the same between
the two groups (26.3 % vs 25.0 %). **Volume alone does not cleanly separate the 86 % family from
the rest of the fatals** on the `volume_degenerate` flag as defined here, though it does
separate them on raw magnitude.

## OPEN-56 join (2x2), auto-arm only

The err census (`open56_open09_run4_err_census_2026-08-20.csv`) covers `mode == 'auto'` only, per
its own scope and per plan §4. Of the 23 readable fatal + 47 readable control buildings, only 20
are `mode == 'auto'` (6 fatal, 14 control); every one of the 20 joined successfully (0 unmatched).

| group | has_volstub = True |
|---|---|
| fatal (auto only, n=6) | 6 |
| control (auto only, n=14) | 14 |

**Every auto-arm building in both groups — fatal and control alike — has `has_volstub = True`.**
On this join, `has_volstub` does not discriminate fatal from non-fatal at all: it fires
universally in the auto arm regardless of outcome. **Caveat, stated per the plan:** this 2x2 is
built on only 20 of the 70 readable buildings (auto-arm only, per the err census's own scope);
the 50 non-auto buildings (44 fast_zone/floor/layout_assign readable buildings) are excluded from
this table entirely, not merged in as a false negative.

## Answer to "are the 44 fatals volume-anomalous?"

Partially, and not in a way that is simple to state as one verdict:

1. **Coverage is the headline finding, not the volume question** — only 52.3 % of the 44 could be
   read at all, because `.eio` retention across the harvest is 0.36 %, not universal as F5's
   single-example framing implied.
2. On what could be read, fatal zones skew to much smaller median volume than control zones
   (41.9 m³ vs 453.2 m³) but with a heavier tail of extreme large-volume zones.
3. The `volume_degenerate` flag (as defined by the plan) fires more often on fatal *zones*
   (19.2 % vs 4.2 %) but not more often per fatal *building* (26.1 % vs 34.0 %) — the two
   readings point opposite directions.
4. The 86 % mechanism family (temperature-out-of-bounds + `CalcHeatBalanceInsideSurf`) is not
   separable from the other fatals on the `volume_degenerate` flag (26.3 % vs 25.0 %), though it
   is markedly smaller in raw median volume.
5. `has_volstub` (OPEN-56) does not discriminate on this small auto-arm join — it is true for
   every building checked, fatal or not.

## Remedy shape (NOT applied)

None proposed — out of scope for this task by the plan's own framing (§6 T07 "Why").
