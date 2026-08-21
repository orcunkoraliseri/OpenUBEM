# MEASUREMENT — OPEN-03 / T03: envelope decomposition, 48 buildings, both arms, no simulation

**Plan:** `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-items-2026-08-20-late.md` §6 T03.
**Harness:** `scripts/analysis/open03_envelope_decomposition_2026-08-20.py` (stdlib only, no
eppy — reads `BUILDINGSURFACE:DETAILED` / `FENESTRATIONSURFACE:DETAILED` vertex lists directly
out of the IDF text; no EnergyPlus run in this task).
**Output:** `openubem/outputs/comparisons/open03_envelope_decomposition.csv` (96 rows: 48
buildings x 2 arms).

Read first: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_enduse-localisation.md` — this
task does not repeat it. That doc already found, on 4 buildings, that the pooled EUI gap is
87.6% heating and that the one large building in that sample (`nyc_centre/265424467`) has 44%
less exterior wall under `layout_assign` at an *identical* floor area and zone count. This task
extends that single-building observation to all 48 sample buildings across all 12 cells.

## Pre-registered controls (before running anything)

- **C7 expectation:** most of the 48 pairs would agree on floor area to within 2%, because the
  plan's premise is "same floor plate." Expected exclusion count: low (under 10).
- **C8 expectation:** the carried 44% would either reproduce as a fleet-wide pattern or turn out
  to be specific to the one building it was measured on. No prior basis to prefer one over the
  other going in.

Both expectations were wrong in instructive ways — see below.

## (a) Pairing — 48/48

Every one of the 48 `layout_assign` sample IDFs (`scratchpad/open03-untrimmed-sample/<cell>/
step3_layout_assign/idfs/<osm_id>.idf`) has a same-named production IDF at
`evidence/open48_refleet4/<cell>/fleet_staging/idfs/<osm_id>.idf`. Zero missing. Confirmed by the
harness's own `find_pairs()` (`open03_envelope_decomposition_2026-08-20.py:181-191`) and printed
as `[pairing] sample=48 found_pairs=48 missing=0`.

## Method notes (two bugs found and fixed during this task, both registered)

1. **Object-boundary bug.** An early version of the parser bounded each IDF object by the *next
   occurrence of the same keyword*, so the last `BUILDINGSURFACE:DETAILED` (or
   `FENESTRATIONSURFACE:DETAILED`) object in a file had its vertex regex run all the way to
   end-of-file, picking up unrelated trailing objects' numbers (shading surfaces, etc.). Fixed by
   splitting the whole file on blank lines first, then filtering blocks by keyword — every block
   is then self-contained. Registered in `OpenUBEM_debug_References.md` §16.
2. **Attic double-count.** `Surface Type "floor"` objects belonging to an unconditioned Attic
   zone sit at the same elevation as the conditioned zone's ceiling below and are a second object
   for a plane already accounted for; naively summing all `floor`-type areas as "total floor
   area" doubled it on any building carrying an Attic zone (measured 538 m² vs. correct ~255 m²
   on `austin_centre/way_328529693`, LA arm). Fixed using the IDF's own signal: every `ZONE`
   object carries a `Part of Total Floor Area` field (Yes/No); floor-area and storey-count sums
   are now restricted to zones where that field is not `No`. Registered in the same file.

Both fixes are in the delivered script; the numbers below are post-fix. As a cross-check, the
post-fix wall/window/floor-area figures for `nyc_centre/way_265424467` reproduce the prior
MEASUREMENT doc's numbers to three decimals (9122.104 vs. the prior doc's 9122, 16270.79 vs.
16271, 17769.102 vs. 17769.10) — the two independently-written readers agree.

**Bucket definitions** (also in the script's docstring): exterior wall = `wall` + `outdoors`;
roof = `roof` + `outdoors`; ground-contact = `floor` with OBC `ground`/`groundfcfactormethod` +
`wall` with OBC `groundfcfactormethod`; window = `FenestrationSurface:Detailed` area (x
Multiplier) + rare exterior `BuildingSurface:Detailed` `window` objects; total floor area =
`floor`-type area restricted to `Part of Total Floor Area != No` zones; exterior surface area =
wall + roof + ground (windows already sit inside the wall footprint in this IDF style — wall
polygons are not punched out for openings); storey count = distinct wall base elevations (0.1 m
rounding), same zone restriction as floor area.

## (b) C7 — floor-area agreement within 2%

**40 of 48 excluded — most of them, and that is the finding.** Only 8 pairs agree on total floor
area to within 2% (all at ~0.000% — effectively bit-identical footprints):
`austin_centre/way_1008727470`, `austin_rural/way_1165379866`, `la_centre/way_425993511`,
`la_suburban/way_442341109`, `la_urban/way_402222550`, `nyc_centre/way_265424467`,
`nyc_suburban/way_846412106`, `nyc_urban/way_241862488` — one per cell except
`austin_suburban`, `austin_urban`, `la_rural`, `nyc_rural`, which have zero survivors.

Excluded buildings, name and cause, fall into two distinct patterns:

- **Borderline geometric mismatch (5.26–5.67%, just above the 2% line):** 12 buildings —
  `austin_centre/way_328529693`, `austin_rural/way_1450171441`, `way_1480414338`, `way_762128912`,
  `austin_suburban/way_382992872`, `la_centre/way_905248736`, `nyc_rural/way_270445757`,
  `way_772627016`, `way_772627029`, `way_772627043`, `nyc_suburban/way_610017070`,
  `way_815835776` — same storey count both arms, small consistent footprint offset. Real, not a
  parsing artifact, and it fails the 2% bar as specified.
- **Large mismatch (25%–200%), storey-count driven:** the remaining 28 buildings. Example,
  named: `austin_centre/way_328649870` — `layout_assign` builds a 3-storey DOE-prototype template
  (`Core_bottom/mid/top` + 4 perimeter zones each, ground floor 735.05 m² — bit-identical to the
  `auto` arm's single floor), `auto` builds **one storey** of the same 735.05 m² footprint. Total:
  2205.14 m² vs. 735.05 m² (diff 200.00%, i.e. exactly 3x). This is not a units or double-count
  bug — the per-floor footprint area is identical; the two arms disagree on **how many storeys**
  to put on it.

Diagnostic (not C7-gated, all 48, median ratio `layout_assign ÷ auto`, per cell):

| cell | storey_count ratio | floor_total ratio |
|---|---|---|
| austin_centre | 1.0000 | 0.9737 |
| austin_rural | 1.0000 | 0.9473 |
| austin_suburban | 0.5000 | 0.4716 |
| austin_urban | 0.5000 | 0.4740 |
| la_centre | 0.7500 | 0.5967 |
| la_rural | 0.5000 | 0.4737 |
| la_suburban | 0.5000 | 1.4897 |
| la_urban | 0.4167 | 1.2500 |
| nyc_centre | 0.3247 | 0.1882 |
| nyc_rural | 1.0000 | 0.9473 |
| nyc_suburban | 1.0000 | 0.9737 |
| nyc_urban | 0.3333 | 0.3158 |

The four cells with storey-count ratio exactly 1.0000 (`austin_centre`, `austin_rural`,
`nyc_rural`, `nyc_suburban`) are exactly the cells whose C7 exclusions are the small
"borderline-5.27%" kind. Every cell with a storey ratio below 1 has large (25–200%) floor-area
mismatches. **Storey-count disagreement, not envelope shape, is what removes most of the 48 from
an answerable "same floor plate" comparison.**

## (c) C8 — does the carried 44% reproduce

**It does not, outside the one building it was measured on.** Wall-area ratio
(`layout_assign ÷ auto`) on the 8 C7-surviving pairs, per cell:

| cell | ext_wall ratio | i.e. |
|---|---|---|
| austin_centre | 1.0000 | no difference |
| austin_rural | 1.5672 | 57% *more* wall |
| la_centre | 0.3634 | 64% less wall |
| la_suburban | 0.8589 | 14% less wall |
| la_urban | 0.8141 | 19% less wall |
| **nyc_centre** | **0.5606** | **44% less wall — reproduces, because this is the same building the 44% was measured on** |
| nyc_suburban | 1.0000 | no difference |
| nyc_urban | 1.0000 | no difference |

`nyc_centre/way_265424467` is the exact building the carried 44% figure came from
(`MEASUREMENT_open-03_enduse-localisation.md`), so its reproduction here (0.5606, i.e. 43.94%
less) is a consistency check on the reader, not new evidence that 44% generalizes. Across the
other 7 surviving cells the ratio ranges from +57% to −64% with no consistent sign or magnitude.
**The 44% is a single-building number, not a fleet or per-cell pattern — a fourth carried figure
that does not reproduce, consistent with this arc's prior three retractions.**

## (d) Which term carries the gap

Two separate answers, at two different scopes:

- **Across all 48 (why most can't even be compared): storey count.** The per-cell table in (b)
  shows floor-area ratio tracks storey-count ratio almost 1:1 in 10 of 12 cells. This is the term
  that removes buildings from the comparison in the first place.
- **Among the 8 where storeys and floor area already agree (the only fair comparison of shape):
  wall area, and only wall area.** On every one of those 8 pairs, `roof_m2` ratio = 1.0000 and
  `ground_m2` ratio = 1.0000 *exactly* — roof and ground-contact area are unchanged when the
  floor plate matches. `ext_wall_m2` ratio is the only envelope term that moves, and it moves in
  both directions (0.3634 to 1.5672) with no consistent sign. Window area mostly tracks wall area
  (WWR ratio = 1.0000 in `austin_centre`, `la_centre`, `nyc_centre`, `nyc_suburban`, `nyc_urban`,
  meaning WWR is held constant while wall moves under it) except `austin_rural` (WWR ratio 0.3035,
  window moves independently of wall there).

**Plain statement:** wall area is the only envelope term that differs when the floor plate is
held fixed, but it is not a universal 44%-less pattern — it swings both ways by cell, and the one
case that does show ~44% less is the single building the figure was originally measured on.

## CANDIDATE DEFECT

`layout_assign` and the production (`auto`) pipeline assign **different storey counts to the
same building footprint** for a large share of the 48-sample buildings — 28 of 48 by the ~25–200%
floor-area mismatch pattern in (b), concentrated in 8 of 12 cells (median storey-count ratio
0.32–0.75, table in (b)). Named example: `austin_centre/way_328649870`, 3 storeys (`layout_assign`)
vs. 1 storey (`auto`) on a bit-identical 735.05 m² footprint. This is a distinct, previously
unmeasured mechanism from OPEN-03's original "44% less wall" framing — it is upstream of wall
shape and would dominate any EUI comparison on the affected buildings by itself (3x floor area
implies roughly 3x total load before any envelope-shape effect is considered). Not opened here;
mechanism and evidence only.

Secondary, smaller: 2 of the 48 `layout_assign` IDFs (`austin_urban/way_381810583`,
`la_centre/way_427817563`) use `Zone` `Multiplier` > 1 to represent repeated identical floors
(a modeling shortcut); 0 of 48 paired `auto` IDFs do. Not large enough to explain the pattern in
(b) on its own (only 2 buildings) but is a second, independent structural asymmetry between the
two arms' zoning strategies.

## (f) What was not done, and why

- **No simulation was run** — the task is explicitly geometry-only; EUI/load consequences of the
  storey-count finding are not measured here.
- **No attempt to determine *why* `layout_assign` and `auto` disagree on storey count** — that is
  upstream mechanism work (likely in the layout/height-assignment logic), out of scope for a
  text-read measurement task and flagged as a candidate defect for the director to scope.
- **The 40 C7-excluded buildings' envelope shape (wall/roof/ground/window) was not compared** —
  by definition, a building whose floor plate itself disagrees cannot answer "same floor plate,
  different wall," so comparing their wall areas would not be meaningful; their storey-count and
  floor-total ratios are reported instead (table in (b)), which is the informative signal for
  that subset.
- **WWR-preservation behaviour** (constant WWR in 5 of 8 survivors, not in `austin_rural`) is
  noted as a diagnostic in (d) but not chased further — it is a secondary observation, not part
  of the four requested categories.

## Artifacts

`scripts/analysis/open03_envelope_decomposition_2026-08-20.py`,
`openubem/outputs/comparisons/open03_envelope_decomposition.csv`.
