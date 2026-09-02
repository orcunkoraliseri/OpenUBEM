# European locations — Debug References (arc-local error index)

> **Scope: the `docs/docs_ACTIVE/europeanLocations` arc only** — TABULA archetypes, the four district
> S2 campaigns (Madrid `ES-MAD-BERRUGUETE`, Lyon `FR-LYO-HAUTCOEURPENTES`, London `GB-LDN-STDUNSTANS`,
> Bologna `IT-BOL-GALVANI2`), the dwelling-layout scheme, context geometry, and their Speed runs.
>
> **Search this file before debugging anything in this arc. Append to it after fixing anything.**
> Opened 2026-08-31 under `D-EU-52`, modelled on
> `C:\Users\o_iseri\Desktop\idf_reader\docs_BEM_Explanation\debug_References.md`.
>
> **This does not replace `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.** That file stays the
> repo-wide index and the CLAUDE.md hard rule ("register every solved error there before closing the
> task") is unchanged. This file is the arc-scoped view: it carries the entries that are specific to the
> European pipeline in full, and routes to the repo-wide index for everything shared with the rest of
> OpenUBEM. When an entry lives in both, the repo-wide one is authoritative.
>
> Entry format, one bullet each:
> `- **<exact symptom / error string>** — <root cause>. Fix: <what changed, file:line>. *(source doc)*`
> `[OPEN]` = cause known, not fixed. Extend an existing entry rather than adding a near-duplicate.

## Chapters

1. [Footprint → dwelling layout: the box rule and its refusals](#1-footprint--dwelling-layout)
2. [Extrusion, interzone surfaces and EnergyPlus geometry fatals](#2-extrusion-interzone-surfaces-and-energyplus-geometry-fatals)
3. [The viewer vs the simulated IDF — this arc's recurring defect](#3-the-viewer-vs-the-simulated-idf)
4. [Context geometry, shading and adiabatic party walls](#4-context-geometry-shading-and-adiabatic-party-walls)
5. [Areas, denominators and EUI arithmetic](#5-areas-denominators-and-eui-arithmetic)
6. [Speed: submission, walltime, harvest, tcsh](#6-speed-submission-walltime-harvest-tcsh)
7. [Schedules, weather and file paths](#7-schedules-weather-and-file-paths)
8. [Data acquisition per country (ES / FR / GB / IT)](#8-data-acquisition-per-country)
9. [Reproducibility and certification traps](#9-reproducibility-and-certification-traps)
10. [Method traps: how these bugs got misdiagnosed](#10-method-traps)
11. [Not-a-bug: by design in this arc](#11-not-a-bug-by-design-in-this-arc)

---

## 1. Footprint → dwelling layout

All counts measured 2026-08-31 over the 2,544 side-cars in `outputs_3D/eu_*_data/layouts/`.

- **[OPEN] `fallback_reason = "L_SHAPE_DECOMPOSITION_FAILED"`, `scheme = null`, and the building is
  simulated as one undivided box per floor — 629 of 2,544 buildings (24.7 %), a quarter of every
  district** — `classify_building_morphology` routes any plate whose denoised convex-hull deficit exceeds
  3 % to the L route (`openubem/geometry/european_residential.py:453`); that route splits at the
  re-entrant corner, partitions each wing independently through the full ruled machinery, and refuses the
  **whole building** if any wing fails (`:983`). A refusal is not a fallback shape — it drops the
  building to `one_zone_per_floor`, so it loses its dwellings, its corridor and its stair core at once.
  Fix: not fixed; this is what `D-EU-50` / `EU-17` exists to relax. *(STATE_european_locations_v4.md §3
  `FINDING 212`)*
- **[OPEN] `fallback_reason = "INTERIOR_RING_COURTYARD_UNFOLD_FAILED"` — 239 buildings (9.4 %), 13.2 % of
  Bologna** — the courtyard route exists (`european_residential.py:724`, MVP §6.4 three-wing unfolding)
  and fails on real dense perimeter blocks. Note this reason string does **not** mean the route is
  missing: it was missing before `EU-15`, it is implemented now and it refuses. Fix: not fixed
  (`EU-17`). *(same)*
- **[OPEN] `fallback_reason = "NARROW_FOOTPRINT_LT_8M"` — 144 buildings, of which 135 in Bologna
  (11.2 % of that district)** — `NARROW_FOOTPRINT_THRESHOLD_M = 8.0` (`european_residential.py:1008`)
  refuses any plate whose minimum rotated width is under 8 m. Bologna's terraced stock is genuinely
  deep-and-narrow, so the gate fires structurally, not on noise. Fix: not fixed; needs a ruled
  single-aspect scheme, not a threshold change. *(same)*
- **`fallback_reason = "DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8"` — 75 buildings, 18 of them 22.0 % of
  London** — the ruled grid table stops at 8 dwellings/floor (`european_residential.py:31`, refusal at
  `:1759`) and London's declared per-floor counts reach 35. **This is the fail-closed refusal working as
  designed** (`FINDING 202`): the count is never reduced to fit. Not a defect; it is a table limit and
  needs an owner ruling, not a fix. *(STATE v4 §4 `D-EU-50` item 4)*
- **`fallback_reason = "REGULARIZATION_AREA_DELTA_GT_2PCT"` — suspected everywhere, measured on 2 of
  2,544** — `REGULARIZATION_AREA_DELTA_FALLBACK_FRACTION = 0.02` (`european_residential.py:32`, tested at
  `:74`, refusal at `:918` and `:986`) is the obvious suspect for "the box rule", and it is almost never
  the binding gate: the morphology dispatch upstream has already routed non-box plates elsewhere.
  Diagnostic rule: read `fallback_reason` before blaming the squaring tolerance. *(STATE v4 §3
  `FINDING 212` item 1)*
- **`FALLBACK_PENDING_LAYOUT / PARTITION_AUDIT_FAILED` with
  `partition_audit.failures = ('AREA_GAP', 'OUTSIDE_FOOTPRINT')` at `area_error_fraction = 5.09e-12`** —
  the partition is exact and the audit fails on float noise: the generator rotated about the literal
  coordinate origin while the audit compared against an **absolute** `1e-8 m²` tolerance, so the noise
  scaled with distance from (0,0) and layout success became **CRS-dependent** (clean in EPSG:32631,
  failing in EPSG:2154). Fix: rotate about `footprint.centroid` (`european_residential.py:511`) and audit
  with the footprint-relative `EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION`. CLOSED 2026-08-27 by re-measurement
  (297/297 agreement between projections); it also moved Lyon's emission from 18 to 28.
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. 5)*
- **`HABITABILITY_GATE_FAILED_AFTER_ROTATION` on ~84 % of the fleet, coverage ~16 % instead of ~97 %** —
  the equal-area bisection cuts with blade rectangles built as `box(mid, -1e6, 1e6, 1e6)`; a footprint
  left in absolute UTM coordinates has a northing near 4.9 × 10⁶ m, **outside the blade**, so every
  intersection is empty and the loop falls through to the habitability token — a misattribution, not the
  real cause. Fix: translate each footprint to its own centroid before partitioning; measured coverage
  15.76 % → 97.05 % over the same 2,544 buildings with no other change. 🔴 A reason token emitted by
  fall-through is not evidence of that failure mode — check the cell count before believing the token.
  *(rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md §8)*
- **`TRACE_ERROR:'NoneType' object has no attribute 'dwelling_layout_emitted'` on every L-shape/courtyard
  building whose allocated wings included a 1-dwelling wing, while re-deriving the true (unmasked)
  refusal cause (`EU-17` T04)** — `_trace_storey`'s `dwelling_count == 1` branch (`scripts/eu17_refusal_census.py`)
  returned `"layout": None` instead of an actual `EuropeanGridLayout`, since a single dwelling can never
  itself refuse; `_combine_wing_results` (`european_residential.py:611`) still needs a real layout object
  for *every* wing, including a 1-dwelling one, and crashed reading `.dwelling_layout_emitted` off `None`.
  Fix: the branch now builds the same `EuropeanGridLayout` the real `generate_european_ruled_storey_layout`
  constructs for `dwelling_count == 1` (`european_residential.py:873-888`), audit and facade lengths
  included. Fixed before the census ran fleet-wide; 0 `TRACE_ERROR` rows in the final
  `refusal_census.csv`. *(EU-17 T04, PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md)*
- **Published layout coverage (93.6 % / 88.1 %) is far above the ruled coverage on disk** —
  `geometry_outcome = DWELLING_LAYOUT_EMITTED*` counted the non-ruled `equal_strip_multi_angle_sweep`
  strip cutter as a success, hiding 843 buildings. Fix: `D-EU-39` §2 retired the strip cutter as a
  success path (`european_residential.py:890`, `_secondary` always returns
  `dwelling_layout_emitted=False`); confirmed 2026-08-31 — **0 side-cars carry the strip scheme**. The
  refusals it produced did **not** become ruled layouts: coverage went 57.81 % → 56.92 %.
  *(`FINDING 207` → `FINDING 211`)*
- **A courtyard combine fails `AREA_GAP`/`OUTSIDE_FOOTPRINT` (≈ 0.1–2.3 % relative) even though every
  wing individually emits cleanly, on both a real building (`relation/12582232`, gap 0.284 m² of 272.3 m²)
  and a clean synthetic square-ring fixture (gap 7.56 m² of 336 m²)** — `_courtyard_wings_and_nodes`
  (`european_residential.py:761`) centres each corner circulation node box **on the void's own inner
  corner**, so roughly half of every node box sits inside the void (never real footprint area); nodes are
  still subtracted correctly from the wings (a void-only sliver was never part of any wing to begin with),
  but `_combine_wing_results`' `circulation_area_total = sum(polygon.area for polygon in all_circulation)`
  (`:628`) summed the **raw, void-including** node areas, overstating carved circulation and breaking the
  `gross − void = conditioned + circulation` identity `EU-17` T06 requires. Fix: `nodes_aligned` is now
  clipped to `aligned_footprint` before being returned (`european_residential.py:786-797`) — this changes
  nothing about the wings (subtracting a void-extending box or its footprint-clipped remainder from a
  piece already confined to the footprint is identical) but makes the reported circulation area the area
  actually carved (`FINDING 217`, fixed). *(`EU-17` T06, `PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md` §6 T06,
  `tests/test_eu17_relaxed_layout.py::test_t06_gross_minus_void_equals_conditioned_plus_circulation`)*
- **[OPEN] Even after the node-clip fix above, a real courtyard building's wing combine still fails
  `AREA_GAP` (0.11 % relative, `relation/12582232`) regardless of which per-wing dwelling-count split is
  tried, including the only mathematically possible one (4 wings, 4 dwellings, 1 each)** — every wing
  individually audits clean (facade contact ≥ 3.39 m, area error ~0); the residual gap sits at the
  wing-boundary tiling itself, on a real (non-axis-aligned, GIS-noisy) void and footprint, not in
  allocation. `EU-17` T06's own "How" only asks to reuse T05's re-allocation search
  (`_wing_count_candidates`) here — reallocation cannot close a gap that exists identically for every
  candidate split, so this is a distinct, deeper defect in the wing-tiling geometry itself. Measured
  fleet-wide 2026-08-31: 0 of 249 true courtyard refusals recovered by T06 (`L_SHAPE_DECOMPOSITION_FAILED`
  recovered 29 of 739 over the same measurement). Fix: not fixed — needs its own investigation, out of
  `EU-17` T06's scoped "How" (`FINDING 218`, `[OPEN]`). *(`EU-17` T06, same source)*
- **`AttributeError: 'NoneType' object has no attribute 'intersection'` inside `_facade_contact_lengths`,
  raised from a dwelling polygon produced by EU-21 S1's ray-sector cut** (`courtyard_perimeter_band`) —
  `_ray_sector_cuts` (`european_residential.py:1362`) intersected the band with a pie-slice wedge polygon
  and, on a self-intersecting wedge (a near-zero-width sliver at the bisection's last step), got back a
  degenerate/invalid geometry whose `.boundary` is `None`; the pre-existing `MultiPolygon` handling never
  saw it because the result wasn't a `MultiPolygon` either. Fix: `_ray_sector_cuts` now repairs an invalid
  wedge with `.buffer(0)` before intersecting and raises `ValueError` on any segment that is not a
  strictly positive-area `Polygon`, so the caller's existing `except (ValueError, IndexError)` folds it
  into a normal `PARTITION_AUDIT_FAILED` refusal instead of crashing (`european_residential.py:1396-1403`).
  *(`PLAN_eu21-group-schemes-2026-09-01.md` P02)*
- **`AttributeError: 'MultiPolygon' object has no attribute 'exterior'` inside
  `regularize_footprint_orthogonal`, raised from a wing produced by EU-21 S3's morphological opening**
  (`wing_spine_decomposition`) — the small-wing merge (`european_residential.py:1631-1635`) unions a
  sub-threshold component into its nearest surviving wing by centroid distance, but "nearest" does not
  imply "touching": when the opening leaves a real gap, `unary_union` of two disjoint polygons returns a
  `MultiPolygon`, which the recursive call into `generate_european_ruled_storey_layout` cannot accept.
  Fix: after each merge, a `MultiPolygon` result is reduced to its largest component
  (`european_residential.py:1636-1642`); the untouched sliver is simply excluded from every wing and
  falls into the junction (circulation) area instead, which is conservative, not a correctness loss.
  *(`PLAN_eu21-group-schemes-2026-09-01.md` P04)*
- **`AttributeError: 'GeometryCollection' object has no attribute 'exterior'` inside the eu21 group-rules
  doc pass's `rings()`, raised while writing the Courtyard sheet** (`scripts/eu21/02_one_core_per_plate.py`)
  — a chain of `.difference()` calls absorbing leftover scraps into flats can degenerate into a
  `GeometryCollection` mixing in stray points/lines, which the old `parts()` helper only unwrapped for
  `MultiPolygon`; every other geometry type fell through and reached `rings()` unchanged. Fix: `parts()`
  now extracts `Polygon` sub-pieces from any geometry via `hasattr(g, "geoms")` instead of an
  `isinstance(g, MultiPolygon)` check (`scripts/eu21/02_one_core_per_plate.py:17-26`).
- **`AttributeError: 'MultiPolygon' object has no attribute 'exterior'` inside the same `rings()`, after
  the `GeometryCollection` fix above** — a "touching-at-a-point" case can leave `unary_union` unable to
  fully merge two real fragments back into one `Polygon`, so the new `weld()` helper could still hand
  back a `MultiPolygon` in that edge case. Fix: `weld()`'s final return goes through `biggest()`, which
  always collapses to the single largest `Polygon` component (`scripts/eu21/02_one_core_per_plate.py:47`).
  *(this session, 2026-09-01 — leftover-scrap absorption rule fix)*
- **Flat-to-flat boundaries in the eu21 group-rules doc showed a staircase of centimetre-scale zig-zags
  instead of one straight cut** (all groups, worst in TRAPEZOID/SLAB/TRIANGLE/COMPLEX_MULTI_WING) —
  separate from the round-join issue above: `absorb()` in `scripts/eu21/02_one_core_per_plate.py` grows
  each flat into unclaimed scrap in discrete 0.20 m wavefront steps, so the boundary it settles on
  approximates the true straight bisector with a stack of ~0.2 m segments rather than being one. Fix:
  new `straighten()` simplifies each flat (largest first) with `preserve_topology=True` and re-clips it
  against what earlier flats already claimed, called once after `fold_narrow_to_core()` and before
  `close_gaps()` so the hairline gaps it leaves are mopped up the normal way
  (`scripts/eu21/02_one_core_per_plate.py`, new `straighten()` + call site). Verified: notch count across
  all 11 groups' flats dropped from 55 to 3, each of the 3 remaining a single straight segment
  &lt;0.3&nbsp;m, not a curve. *(this session, 2026-09-01)*
- **Corridor rectangle's representative sheet showed a plain bisection with no corridor, even though
  its own rule text describes a linear-gallery corridor** — `scripts/eu21/01_cut_group_plans.py` drew
  every group's representative at its true per-floor median, and Corridor rectangle's (and Slab's)
  median is 2; `generate_european_ruled_storey_layout` special-cases `dwelling_count == 2` as a plain
  bisection and skips morphology dispatch entirely (`openubem/geometry/european_residential.py:1204-1208`),
  so the aspect-ratio-driven corridor route never activates at that count. Fix: `01_cut_group_plans.py`
  now draws these two groups at `max(3, median)` instead of `max(2, median)` — 3 is the lowest count
  where the corridor route activates, and both groups have real buildings at n=3 (`MIN_DRAW_TO_SHOW_SCHEME`,
  `scripts/eu21/01_cut_group_plans.py`). Verified: both now render `scheme=i_shape_linear_gallery` with a
  real double-loaded corridor spine, still 100% plate coverage. *(this session, 2026-09-01)*
- **A handful of small staircase notches survived the `straighten()` fix above** (worst example: Courtyard's
  F1, a 3-point ~0.27&nbsp;m/0.15&nbsp;m/0.12&nbsp;m zig-zag chain tucked between two long walls) — Douglas-Peucker
  `simplify()` only drops a point when it is close to the chord between its *surviving* neighbours, and a short
  run of centimetre-scale edges midway along a long wall sits far enough from that distant chord to look
  load-bearing, so `simplify()` (any tolerance safe enough not to eat the courtyard gallery ring's real
  many-vertex void, checked up to 0.75&nbsp;m) left it untouched. Fix: new `dekink()` in
  `scripts/eu21/02_one_core_per_plate.py` removes points one at a time — a point with at least one edge
  under `KINK_SEG_MAX` (0.5&nbsp;m) is dropped if doing so changes that one polygon's own area by less than
  `KINK_AREA_TOL` (0.3&nbsp;m²) — a per-point bound instead of a whole-shape tolerance, so it cannot eat a
  real corner the way a larger `simplify()` tolerance did (that also cost real area: raising `STRAIGHTEN_TOL`
  to 0.30–0.75 dropped Courtyard's own coverage to 91.79%, restored once `dekink()`'s bounded, per-point
  approach replaced it). Folded into the existing core-then-flats claimed-clip cascade (dekink core, then
  dekink-and-reclip each flat against it, two passes) rather than run on each shape independently, because
  independent dekinking let a flat and the core drop *different* points of a shared corner and go out of
  sync by the same ~0.27&nbsp;m, which `close_gaps()` then had to weld back as a many-cornered sliver.
  Verified: a strict scan (both adjoining edges &lt;0.5&nbsp;m — the true multi-point zig-zag signature) now
  returns zero across all 11 groups' flats and cores, all groups still ≥99.98% plate coverage, no
  flat/flat or flat/core overlaps &gt;0.02&nbsp;m². One single-sided small facet can still remain where a
  flat's own corner sits close to, but not exactly on, an independently-simplified core corner (Courtyard's
  F2, ~0.27&nbsp;m) — a real small straight notch, not a curve or a staircase, consistent with the
  already-accepted tolerance for this document. *(this session, 2026-09-01)*

- **A flat drawn as two separate pieces joined by a thin neck (owner: "look how F2 divided into two pieces, no every zone needs to be single zone")** — `absorb()` grows each flat into whatever the cut left over by nearest-wavefront, so a flat beside a long re-entrant edge can win a corridor-thin strip that reaches right across the plate and re-emerges as a second lobe under a distant wing. It is one polygon topologically, so no coverage, overlap or fragment-count check saw it. Fix: `unsnake()` — erode each flat by 0.75&nbsp;m, and if the erosion falls into two pieces, grow the pieces back inside the flat and hand every lobe but the largest to the neighbouring flat it shares the most wall with (`scripts/eu21/02_one_core_per_plate.py`). Because `tidy()` re-derives every shape and can re-create a tail the previous pass gave away, the two alternate three times rather than running once each. Verified: zero snakes across all 11 groups. *(this session, 2026-09-01)*
- **The 1.80&nbsp;m corridor drawn with a wide head at one end (Corridor rectangle: circulation 12.6&nbsp;% of the plate from the engine, 13.8&nbsp;% after the document pass)** — `close_gaps()` handed each leftover pocket to the *nearest* shape among flats **and** the core, so the block between the corridor end and the plate's top step was welded onto the corridor; `straighten()` then guarded the core against shrinking but not against growing, and `dekink()`'s per-point 0.3&nbsp;m² tolerance let it keep creeping. Contradicts `D-EU-64` clause 2, which gives every pocket to a flat. Fix, three parts in `02_one_core_per_plate.py`: `close_gaps()` now considers flats only; `straighten()` and the `dekink()` loop guard the core in **both** directions (±1&nbsp;% of its own area); and `fold_narrow_to_core()` takes a `budget=` of the area the scheme originally gave the core, capped at `CORE_GROWTH_CAP = 1.02`. Corridor back to 12.8&nbsp;%, Courtyard gallery 10.1&nbsp;% → 9.0&nbsp;%. *(this session, 2026-09-01)*
- **Vertex count on every flat tripling (Square 27 → 89 points) after adding a re-clip pass, with new sub-0.5&nbsp;m segments on interior boundaries** — the sequential disjointness pads use `core.buffer(0.001)` to keep neighbours from sharing an edge, and shapely's **default round join** renders that 1&nbsp;mm pad as an arc of ~16 segments per corner; every flat differenced against it inherited the arc. Fix: pad with the module's own `sbuf()` (`cap_style="flat", join_style="mitre"`) everywhere — `absorb()`, `straighten()`, the `dekink()` loop, `disjoint()`, `fold_narrow_to_core()`. Square back to 25 points, interior kinks 64 → 0. General rule for this file: **no bare `.buffer()` on a geometry that will be drawn.** *(this session, 2026-09-01)*

- **Party walls drawn with a dogleg near the outer wall (owner, five sheets: "look we have some unwanted edges")** — `absorb()` grows each flat into the leftovers in 0.20&nbsp;m wavefront steps, so the wall between two flats comes out as that line plus a step or two where the two wavefronts met; `straighten()`/`dekink()` only remove points whose own edges are short, and a 1–2&nbsp;m dogleg is neither short nor far from its local chord, so it survived every pass. Fix: `straight_cuts()` in `scripts/eu21/02_one_core_per_plate.py` re-cuts each neighbouring pair by the straight line through the two ends of the wall they share, on the union of that pair alone so nothing else on the plate moves and the core is stepped around, not through. Refused when the wall genuinely bends (`CUT_MAX_BEND` 2.5&nbsp;m), is too short to give a direction (`CUT_MIN_SPAN` 1.5&nbsp;m), would move more than `CUT_MAX_SWING` (20&nbsp;%) of the smaller flat, or leaves either side as more than one room. Verified: zero refusals for bend across all 11 groups afterwards, every party wall one straight line. *(this session, 2026-09-01)*
- **A zone carrying a hairline spike metres across its neighbour — invisible in the fill, but enough to make its own party wall measure as a 5.7&nbsp;m bend** — `close_gaps()` gave each leftover pocket to the flat at the shortest *distance*, and a seam left along the corridor or the outer wall touches two or three zones at distance zero, so it went whole to whichever came first in the list; welding it produced a ring that ran out along one line and back along another a few centimetres away. Fix, three parts in `02_one_core_per_plate.py`: `close_gaps()` now gives the pocket to the zone holding the longest share of its wall (`_shared_len`), not the nearest; `deneedle()` drops out-and-back tips (`NEEDLE_COS` 0.9995) one vertex at a time with a per-vertex area bound (`NEEDLE_AREA` 0.25&nbsp;m²) instead of refusing the whole ring when the needle is a hair off exact; and `despike()` opens each zone at `SPIKE_R` 0.05&nbsp;m to cut filaments that are not tips at all. Verified: worst residual open-loss 0.21&nbsp;m² on any of the 11 plates, no zone-to-zone overlap, coverage 99.84–100.00&nbsp;%. *(this session, 2026-09-01)*
- **A whole zone silently vanishing from a coverage check — `Rectangle` reporting 120.86&nbsp;% covered with 39&nbsp;m² of overlap after `disjoint()`, which by construction cannot overlap** — `unary_union()` over a set of zones that share exact edges dropped one of them at GEOS precision, so `fp.difference(covered)` returned that whole zone as a "gap" and `close_gaps()` welded it onto its neighbour. Fix: `uncovered(fp, shapes)` takes the difference one shape at a time instead of unioning first (`02_one_core_per_plate.py`), used by `close_gaps()` and by the scrap scan in the main loop. Note the union itself reported `is_valid == True` and `explain_validity() == "Valid Geometry"` — the loss is not detectable by a validity check, only by comparing the union's area against the sum of the parts. *(this session, 2026-09-01)*
- **Vertex counts doubling on every cleanup pass (`Slab` F3: 17 → 40 → 78 → 145 → 309 → 405 points over six passes) with the drawing unchanged** — every offset-and-clip step (`despike()`'s open, `straighten()`'s re-clip) re-inserts the offset polygon's own vertices onto walls that already had them, and none of `deneedle()`, `dekink()` or `simplify()` removes a point merely because it lies *on* the line between its neighbours. Fix: `_deneedle_ring()` also drops any vertex whose perpendicular distance to the chord between its two neighbours is under `FLAT_TOL` (0.01&nbsp;m), which is exact enough never to touch a real corner. Slab F3 back to single figures; total points per plate 19–58 across all 11 groups. *(this session, 2026-09-01)*
- **The surveyed outer wall being shaved, and a wedge opening along it that comes back as a hairline needle** — `straighten()` simplified each flat at `STRAIGHTEN_TOL` 0.20&nbsp;m and `dekink()` dropped short-edged points, neither of which distinguished a cut between two zones (a design decision, straighten it) from the outer wall (surveyed, its corners are the building). Cutting a real footprint corner leaves the flats short of the wall, and `close_gaps()` then welds that full-width wedge back onto one flat. Fix: `straighten()` restores whatever each shape held within `WALL_BAND` (0.35&nbsp;m) of `fp.exterior` after simplifying, and `dekink()` takes a `wall` mask and skips any vertex on it. Both bands are built with square joins — `fp.exterior.buffer(WALL_BAND)` with shapely's default **round** join hands every zone a fan of arc vertices along the wall it is restoring, which is the same staircase by another name. *(this session, 2026-09-01)*
- **The corridor's wide head returning as soon as the core growth cap was loosened enough to let a real gallery ribbon in (owner: "we have some unwanted narrow zone which can be added to the corridor")** — a pure area cap cannot tell the two apart: the Courtyard's 0.5&nbsp;m ribbon between the gallery and the outer wall and the Corridor rectangle's 2.4&nbsp;m&nbsp;×&nbsp;0.5&nbsp;m block across the corridor's end are both narrow and both touch the core. Fix: `fold_narrow_to_core()` now tests shape, not size — the pocket must be narrower than 2r, must be a ribbon *along* the core (mean width over the shared wall under `RIBBON_MEAN_W` 0.90&nbsp;m), and must not widen the core's band: `minimum_rotated_rectangle` growth over `MRR_GROWTH` (2.5) × the pocket's own area refuses it. A ribbon down one side barely changes that box; a head across one end widens it over the corridor's whole length — tens of m² of box for one m² of pocket. `CORE_GROWTH_CAP` is kept at 1.35 as a backstop only. Verified: Corridor rectangle 12.9&nbsp;%, Courtyard gallery 10.1&nbsp;% with the ribbon absorbed and no head. *(this session, 2026-09-01)*
- **A flat drawn with the core as a hole in it — nine of eleven plates, valid in shapely and impossible in EnergyPlus (owner: "you know that energyplus requires simple geometries")** — every pass reserved a 1&nbsp;mm collar around the core (`claimed = sbuf(core, 0.001)`), so no flat was ever cut to touch it. The ring of gap that leaves is **one connected pocket**, and `close_gaps()` welded it whole to a single flat, which then closed around the core through a hairline neck: `len(f.interiors) == 1`, `is_valid == True`, area correct, and the only visible trace is the extra edge beside the core the owner kept pointing at. It also poisons every wall measurement — the shared boundary of two flats comes back as the neck plus stray pieces, so `straight_cuts()` read a straight party wall as a 5.7&nbsp;m bend and refused it. Fix in `scripts/eu21/02_one_core_per_plate.py`: the collar is gone (flats are cut against `core` exactly, five call sites), `_share()` splits a pocket bordering more than one flat between them by wavefront instead of handing it whole, and `open_rings()` enforces the invariant afterwards. Verified: zero zones with an interior ring across all 11 groups, 4–21 points per zone. *(this session, 2026-09-01)*
- **A circulation zone shaped as a closed ring around a courtyard void — a zone floor cannot be stated with a hole** — the Courtyard gallery is a genuine annulus, so no re-cut removes the hole. Fix: `open_rings()`/`_open_ring()` cut the ring open on a radial line, preferring the wedge between two neighbouring corners of the void's own box (which hands over a whole side of the ring, a room) over the thin slice through a single corner (which hands over a finger). A candidate is refused unless the rest comes back as one hole-free piece **and** the cut actually touches a neighbour that can take it: the first working version cut a bite out of the middle of the ring, walled in by the ring itself, and the plate read 97.99&nbsp;% covered. Two further traps: `_shared_len()` at 0.06&nbsp;m bridges a hairline third zone lying between the two shapes and reports a wall that is not there (use `_touch_len()` at 0.001&nbsp;m), and a cut running along an edge the zone already had leaves a hairline arm of it behind, which is what walls the piece off — refused by comparing `rest` against its own `despike()`. Verified: Courtyard core 31.7&nbsp;m² (8.0&nbsp;%) as a C, coverage 99.99&nbsp;%. *(this session, 2026-09-01)*
- **A party wall straight on each side of a T-junction and stepped where the two halves meet** — `straight_cuts()` re-cut each *pair* on its own line, so a flat facing two others got two lines at slightly different heights, which is the step beside the core in `Rectangle`. Fix: each flat is now tried against **all** its neighbours together first, cutting them with one shared line, and only then pair by pair; what the cut moves to the far side is shared out between those neighbours by `_share()` rather than handed to one. Verified: worst flat-to-flat wall deviation 0.46&nbsp;m (on a 4.9&nbsp;m wall), everything else under 0.4&nbsp;m. *(this session, 2026-09-01)*
- **`unary_union()` returning two pieces that merely touch, and the weld then dropping one of them** — where two zones were cut separately their boundaries can differ by a fraction of a millimetre, so the union of a flat and the pocket beside it comes back as a `MultiPolygon`; `weld()` keeps the largest piece and the rest of the area leaves the plate silently (Courtyard stuck at 97.99&nbsp;% with a 7.89&nbsp;m² piece that reported `distance == 0` to the flat next to it). Fix: `join()` bridges the crack with a 2&nbsp;cm morphological close on square joins, then `deneedle()`s the points it bridged with; `fuse()` adds shapes one at a time and checks the area after each, because `unary_union()` can also drop a whole zone at GEOS precision and still report the result valid. Do the close **once per flat at the end** of `_share()`, not per wavefront step — welding at every step took Courtyard from 53 to 251 points. *(this session, 2026-09-01)*
- **A 5&nbsp;cm staircase left along the line where two flats' wavefronts met, invisible in the drawing and a dozen extra points on a wall that is one line** — `_share()` grows in 0.05&nbsp;m steps and runs *after* `straighten()`/`tidy()`, so nothing straightens what it leaves (`Sliver` F1: eight consecutive 0.050&nbsp;m segments). Fix: a closing pass at the end of the plate loop — `dekink()` with the outer-wall mask, then `disjoint()` and `close_gaps()` to re-clip and fill what removing it opened, twice. Verified: Sliver 43 → 27 points, sub-1&nbsp;m interior edges 20 → 4, coverage unchanged. *(this session, 2026-09-01)*

- **[OPEN] `LAW_GEOSException` — `shapely.errors.GEOSException: TopologyException: side location conflict at <x> <y>` / `TopologyException: unable to assign free hole to a shell at <x> <y>` / `TopologyException: found non-noded intersection between LINESTRING (...)`, raised inside `apply_law()` (`scripts/eu21/02_one_core_per_plate.py`) on 32 of 550 real sampled plates in the rules tests (15 of 198 at a building's own flats-per-floor count, 17 of 352 at an imposed 3/6/9/12)** — the `D-EU-64` post-pass was tuned on the eleven representative plates only and chains `unary_union` / `buffer` / `difference` on whatever the engine cut, with no `make_valid` or snap-to-grid step; on real footprints the engine's flat boundaries can be near-coincident and non-noded, and GEOS then refuses the union or cannot assign a hole. Fix: none yet — the test scripts catch it (`scripts/eu21/04_group_tests.py`, verdict `ERROR`, token `LAW_GEOSException`) and draw the plate as an error box instead of a plan; the plate is a finding, never replaced. Since 2026-09-01 (plan `eu21-direct-cutters` T04) the five tests no longer call `apply_law()` at all — they cut with `scripts/eu21/05_group_cutters.py` — so the token no longer appears in `rules_tests/test_0N.json`; the old results are kept as `test_0N.postpass.json`. The post-pass itself is unchanged and still fails on these plates, hence still `[OPEN]`. *(docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu21-rules-tests-2026-09-01.md §8 T03; implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T04; rules/tests/TEST_0[1-5]_*.html)*

- **`AssertionError: assert 12 > 12` in `test_eu13b_dwelling_conservation.py::test_t02_density_exceeded_reason_present_in_fallbacks`, after raising `RULED_GRID_MAX_DWELLINGS_PER_FLOOR` from 8 to 12 (`D-EU-65`)** — the test accepted both the historical token `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` (EU-11 side-cars written under the old 8 cap) and the current `DWELLING_DENSITY_REFUSAL_TOKEN`, but compared *both* against the same single bound, the current ceiling; a historical side-car with `observed_max_per_floor == 12` is `12 > 8` (true, correct when it fired) but `12 > 12` (false) under the new ceiling, so the assertion failed on true-but-stale data. Fix: `tests/geometry/test_eu13b_dwelling_conservation.py:82-97` branches the bound by which token fired — `> 8` for the historical string, `> RULED_GRID_MAX_DWELLINGS_PER_FLOOR` for the current constant. *(docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu21-cap12-2026-09-01.md §8, director ruling at CP-1 (a), T02b)*

---

- **`PARTITION_AUDIT_FAILED` from `ruled_grid_5x2` on every plate at 9 or 10 flats per floor, even a plain 20×20 box, while `ruled_grid_6x2` at 11–12 emits** — after `D-EU-65` raised `RULED_GRID_MAX_DWELLINGS_PER_FLOOR` to 12 (`openubem/geometry/european_residential.py:31`, table rows 9–12 at `:190-193`), the odd 5-column grid puts the centred core (`CIRCULATION_FRACTION_OF_PLATE` = 9 % of the plate) in its middle column, which is narrower than the core (4.0 m on the 20×20 box), so the column is split and the partition audit fails; with `carve_circulation=False` the same 9 and 10 emit cleanly, and the secondary `equal_strip_multi_angle_sweep` fails the audit as well. Effect in the rules tests: 0 plates drawn by `5x2`, every compact group refused at 9 (`rules/tests/TEST_02_*.html`, `TEST_04_*.html`). Fix: `D-EU-66` (2026-09-01) — rows 9 and 10 of `_DENSITY_GRID_TABLE` now point at the `6x2` grid with column merges (`openubem/geometry/european_residential.py:190-191`); the `5x2` grid left the table. *(implementation/PLAN_eu21-cap12-2026-09-01.md §8 T03)*
- **`shapely.errors.GEOSException: TopologyException: unable to assign free hole to a shell at <x> <y>`, raised inside `finish()`'s scrap-donation `unary_union()` while dissolving a leftover sliver into a candidate flat (`Rectangle`, k=12, direct cutter)** — `05_group_cutters.py`'s R1/R2 clean-up unions a tiny difference-scrap or a MultiPolygon's minor part onto whatever flat shares the longest boundary with it; on a real (not hand-picked) plate that scrap can carry a near-duplicate or non-noded vertex from the upstream `box(...).intersection(P)` chain, which GEOS refuses to union. Fix: `_safe_union()` (`scripts/eu21/05_group_cutters.py:114-121`) wraps every `unary_union()` call in `finish()`, retrying once with each input `buffer(0)`-cleaned before giving up and leaving the candidate merge unplaced (it then falls through to the next candidate, or stays scrap for `R3`/coverage bookkeeping) — never lets GEOS raise out of `finish()`. *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T01)*
- **A flat that is a single, valid `Polygon` throughout `finish()`'s R1/R2 passes comes back a `MultiPolygon` at the very last step — `AttributeError: 'MultiPolygon' object has no attribute 'exterior'` in the caller (`Rectangle`, k=12, spine_grid_12x1)** — the final `set_precision(f, 0.001)` snaps every vertex onto a 1 mm grid, and a flat with a thin neck (area unchanged, ~13.09 m² before and after) can have that neck collapse to zero width under the snap, which GEOS reports as two disjoint parts rather than one degenerate one — a defect the R1/R2 passes never see because they run *before* the snap that creates it. Fix: `finish()` (`scripts/eu21/05_group_cutters.py:124-197`) re-runs the R1 dissolve pass (up to 3 more passes) once more, after the module-wide `set_precision(...,0.001)` and before the `R3` no-interior check, so a snap-induced split is folded back into a neighbour exactly as a pre-existing MultiPolygon flat would be. Also hardened `_shared_len_metric()` to treat any candidate part with `area <= 1e-6 m²` as zero shared boundary rather than buffering it — a ~1e-15 m² floating-point sliver produced `RuntimeWarning: divide by zero encountered in buffer` from GEOS's mitred-join buffer on a near-degenerate vertex. *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T01)*

- **`AttributeError: 'MultiPolygon' object has no attribute 'interiors'` inside `finish()`'s R3 check, on the courtyard direct cutter (`cut_courtyard`, T02)** — the same snap-induced split as the `exterior` case above (T01), but on `circ` instead of a flat: the mid-pass `set_precision(state["circ"], 0.001)` can turn a single, valid `Polygon` circulation zone into a `MultiPolygon` by collapsing a thin neck (courtyard ring + core + connector geometry has more such necks than a convex-group band), and `finish()`'s R1 re-dissolve only re-processed `flats`, never `state["circ"]` itself. Fix: `finish()` (`scripts/eu21/05_group_cutters.py`, right after the mid-pass `set_precision` calls) now checks `state["circ"].geom_type == "MultiPolygon"` explicitly, keeps the largest part, and donates each smaller part to whichever flat shares the longest boundary with it — the same donation rule R1/R2 already use, just applied to circ once. *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T02)*
- **A courtyard's circulation ring staying a closed annulus (`circ.interiors` non-empty → `Refusal("WING_TREE_FAILED")`) even after the opening notch was subtracted, on real (non-hand-picked) plates whose void isn't an exact rectangle** — the notch box (`box(-a-CORRIDOR_W, -b, -a, b)` etc.) is built from the void's *idealized* MRR half-sides `(a, b)`, but the true ring (`Vl.buffer(CORRIDOR_W, ...).difference(Vl)`) follows the void's *actual*, slightly irregular boundary; on several `test_05.json` plates the real ring's material at that side extended a few centimetres beyond the idealized notch box, leaving an unsevered sliver that kept the annulus connected. Same root cause as the "core square only touching the ring at a single point" case below (idealized-frame formula vs. real buffered geometry). Fix: pad the notch box 0.30 m on every side (`scripts/eu21/05_group_cutters.py`, `notch()` inside `cut_courtyard`) — generous enough to guarantee full severance regardless of minor void-shape irregularity, without materially changing the "one ring side removed" semantics. *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T02)*
- **A stair core square built from the void's idealized-frame corner formula (`box(a+CORRIDOR_W, b+CORRIDOR_W, ...)`) touching the real ring at a single point instead of a full edge, so `unary_union(R, cores)` came back a `MultiPolygon` (cores isolated) instead of one connected circulation** — same idealized-vs-real mismatch as above: the formula assumes the void is exactly its own MRR, so a corner is only edge-flush with the true mitre-buffered ring when that vertex of the real void happens to sit near-exactly on the MRR's own corner; several real courtyards (chamfered or offset corners) leave the theoretical core box meeting the ring at one point (`distance() == 0.0` but shared boundary `length == 0`), which GEOS keeps as separate polygons. Fix: `_connector()` (`scripts/eu21/05_group_cutters.py`) checks the *shared boundary length/area*, not just `distance`, and where a core only point-touches (or misses within ~0.3 m) the ring it adds a small 0.30 m-wide bridge box (`nearest_points` + `buffer(cap_style="square", join_style="mitre")`) between them before the union — never widens the core itself, only guarantees a real connection. *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T02)*
- **Two distinct equal-area quantile cuts on the courtyard's perimeter parametrisation both snapping to the same corner (`t` list carrying a duplicate value), producing a zero-width sector (`MultiLineString`, area 0.0) and a spurious `Refusal("CELL_EMPTY")`** — the sheet's own rule ("a cut within 1.0 m of a corner snaps to the corner") says nothing about two different candidates both landing in that same 1 m radius, which happens whenever the void's short side is under ~2 m. Fix: `_snap_to_corners()` (`scripts/eu21/05_group_cutters.py`) claims each corner for its single *closest* candidate cut only (sorted by distance, first-come); any other candidate within 1 m of an already-claimed corner keeps its raw (unsnapped) position instead of colliding with it. *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T02)*
- **A wide (>180° of the loop) "sector" polygon built as a near-boundary path plus each vertex pushed outward `BIG` independently self-intersected into a degenerate star, corrupting the cumulative area profile (a 0.14 m arc-length step absorbing 140 m² in one measured case) — first hit while writing `cut_courtyard`'s step 6, later reused unmodified in `cut_wings`'s column search** — pushing multiple boundary vertices outward *each in its own local direction* only stays a simple polygon while the direction doesn't reverse across the loop; every `k=1`/`k=2` courtyard case and the very first `total`-area bisection call on any `k` needs the full loop, so this was not a rare edge case. Fix: `_sector_polygon()` (`scripts/eu21/05_group_cutters.py`) rebuilt as a `unary_union` of per-side axis-aligned box strips (one box per side segment the interval spans, each extended `BIG` along that side's own outward normal) — robust for any interval width, including the full loop. *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T02, reused by T03)*
- **`cut_wings`: a wing needing more forced column boundaries (one per child junction) than its own `k_w` budget allowed (`N_w < n_spans`) raised `Refusal("WING_TREE_FAILED")` on *every* k from 2 through 12 on the `COMPLEX_MULTI_WING` representative — a 7-wing tree whose most-branched hub (3 children) structurally needs `k_w >= 4` just to seat its own junctions, and the sum of every wing's own structural minimum (13) already exceeds `MAXK` (12)** — the sheet's own fallback ("take the extra flats back from the largest other wing; if impossible, refuse") assumes a single donor wing can cover the whole deficit, which is never true once more than one wing is under-budget at once. Fix: dropped the deficit/rebalance mechanism entirely — `_wing_columns()` (`scripts/eu21/05_group_cutters.py`) now truncates the forced-boundary list to at most `N_w - 1` entries (evenly sampled by index when there are more child junctions than free column slots) instead of demanding every junction get its own column; any child whose junction lost its dedicated boundary still reaches circulation through the generic connector-bridge step (below). L_SHAPE and U_OR_T_SHAPE went from failing outright at low k to passing 9/9 representative k-values; COMPLEX_MULTI_WING from 0/9 to 7/9 (k=9, 12 still structurally refuse — sum of per-wing minimums still exceeds `MAXK` even with the truncation, a genuine finding, not tuned). *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T03)*
- **A forced column boundary landing a fraction of a millimetre inside a wing's own edge (a child's junction sitting almost exactly at the parent wing's corner) created a near-zero-width column, propagating to a near-zero-area cell and a spurious `Refusal("CELL_EMPTY")`** (`U_OR_T_SHAPE` representative, k=4) — `_wing_columns()`'s original edge filter only excluded boundaries within `1e-6` m of the wing's true min/max x, far too tight for a junction that lands, say, 0.0008 m inside. Fix: widened the filter to `edge_pad = min(1.0, (maxx-minx)/4)` m from each true edge, and to the *previous kept boundary* too (not just the wing's own edges), so two forced boundaries — or a forced boundary and the wing's own edge — can never end up closer than that pad. *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T03)*
- **`cut_wings`'s core+band circulation coming back a `MultiPolygon` even when every band individually passed a "distance < 1e-6 and shared-boundary length > 0.02" direct-touch check against the growing union** (`COMPLEX_MULTI_WING` representative, k=4-8) — checking each new part against the union one at a time doesn't guarantee the *simultaneous* union of everything is one polygon; accumulated `set_precision` snapping at different points in the chain can still leave a hairline gap only visible in the full `unary_union`. Fix: replaced the incremental touch-then-add loop with a fixed-point pass (`scripts/eu21/05_group_cutters.py`, `cut_wings`) — union everything at once, and while the result is a `MultiPolygon`, keep the largest part as hub and `_connector()`-bridge every other part to it, up to 8 passes, before finally checking `geom_type == "Polygon"`. *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T03)*
- **`unary_union([core] + bands)` returning a `GeometryCollection` (one real `Polygon` plus a zero-area `LineString`) instead of the expected `Polygon`/`MultiPolygon`, so the `geom_type == "Polygon"` check never matched even though circulation was already fully connected** (`U_OR_T_SHAPE`, `way/311602374`, k=2) — a band's edge exactly tangent to the true footprint boundary after `.intersection(poly)` leaves a degenerate, zero-area `LineString` sliver in the union that `unary_union` does not drop on its own. Fix: `_polygons_only()` (`scripts/eu21/05_group_cutters.py`) strips every non-`Polygon`/`MultiPolygon` component out of a union result before the type check, applied to `combined` both on first computation and after every connector-bridge pass. *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T03)*
- **`Q = poly.simplify(...)` losing ~0.3 m² of a `COMPLEX_MULTI_WING` plate's true footprint area from the wing partition, cov 0.9989 (just under the 0.999 assertion floor)** — `Q = poly.simplify(DENOISE_TOL=0.30, preserve_topology=True)`, used only to find reflex vertices and split wings, is not guaranteed to *contain* the true `poly`: simplification can shave a small protrusion of the real, surveyed boundary off Q by up to ~0.3 m locally, and since every wing (and therefore every cell, band and flat) is built from Q, that sliver of the true footprint belongs to no wing at all and is never claimed by any flat — `finish()`'s R2 "no scrap" pass tries to donate it, but a piece with near-zero shared boundary to every flat just stays unplaced after 3 tries. Fix: `_reclaim_denoise_loss()` (`scripts/eu21/05_group_cutters.py`), called right after `_absorb_bays()`, computes `poly - union(wings)` and hands any piece over `SCRAP_M2` to whichever wing shares the longest boundary with it, *before* any column/band geometry is built from the wings — so the true footprint is always fully covered by the wing partition itself, not patched after the fact. Coverage across the full T03 battery is now 0.99996–1.00002. *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T03)*
- **`CUT_RuntimeError` — `RuntimeError: circulation not a single Polygon (MultiPolygon)`, raised at `cut_convex` (`scripts/eu21/05_group_cutters.py:314`), Slab k=9, `IT-BOL-GALVANI2/28583` — 2 of 550 plates in the T04 full-census run (test 02 and test 04, same building at its imposed size)** — `cut_convex`'s own `circ_local = unary_union([core, band]).intersection(P)` (`:312`) has no bridging fallback for a non-`Polygon` result, unlike `cut_courtyard`'s `_connector()` or `cut_wings`'s fixed-point merge loop; on this real (not hand-picked) footprint the corridor band and the core square evidently meet at less than a full edge after clipping to the plate. Fix: `cut_convex` (`scripts/eu21/05_group_cutters.py:378-392`) now runs the same fixed-point `_connector`-bridge merge loop `cut_wings` uses (hub = largest part, capped at 8 passes) before giving up; only if the loop still fails to reach one `Polygon` does it raise `Refusal("WING_TREE_FAILED")` — a drawn refusal, never an uncaught exception. Verified: this exact plate now refuses cleanly (the loop genuinely cannot bridge it); no longer an `ERROR`. *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T05d)*
- **`CUT_GEOSException` — `shapely.errors.GEOSException: TopologyException: unable to assign free hole to a shell at <x> <y>`, raised by `set_precision()` itself (`scripts/eu21/05_group_cutters.py:191`, `finish()`'s post-pass flat snap) on Slab k=12, `GB-LDN-STDUNSTANS/way/398158956` — 2 of 550 plates (test 02 and test 04)** — this is a different call site from the T01 finding above (that one is a flat *splitting* under the snap; here `set_precision` raises out of GEOS mid-call on one of the already-dissolved flats). `_safe_union()` only wraps `unary_union()` calls inside `finish()`; the module-wide `set_precision(f, 0.001)` calls on the final flat/circ list (`:191-192`, `:215-216`) are not wrapped and have no retry. Fix: every such call in `finish()` (`scripts/eu21/05_group_cutters.py:171-179`, `_safe_precision(g)`) now tries `set_precision` as-is, then retries on `g.buffer(0)`, then falls back to the unsnapped `g` and counts it in the returned `notes["unsnapped"]` — `finish()` never lets GEOS raise. Verified: this exact plate now draws cleanly, `cov=1.0000`, `unsnapped=0`. *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T05d)*
- **`CUT_AttributeError` — `AttributeError: 'GeometryCollection' object has no attribute 'interiors'`, raised in `finish()`'s R3 check (`scripts/eu21/05_group_cutters.py:210`) on two distinct real `U_OR_T_SHAPE` plates from `cut_wings` (`IT-BOL-GALVANI2/32891` k=2, test 03; `IT-BOL-GALVANI2/31952` k=4, test 05)** — a flat cell built by `cut_wings` (`cell_w ∩ wing ∩ poly − circulation`) came out a `GeometryCollection` rather than `Polygon`/`MultiPolygon`; `finish()`'s R1 dissolve pass (`:130-156`) only special-cases `f.geom_type != "MultiPolygon"` for splitting a flat into its largest part, so a `GeometryCollection` flat passes through both dissolve passes untouched and reaches R3's `f.interiors` access still in that shape. Two independent real plates, not one, so this is a real gap in `finish()`'s type handling, not a one-off. Fix: `finish()`'s entry (`scripts/eu21/05_group_cutters.py:166-167`) now passes every flat and the circulation through `_polygons_only()` before R1 runs, so a `GeometryCollection` cell is reduced to its `Polygon`/`MultiPolygon` components first and R1 handles it like any other multi-part cell. Verified: both plates now draw cleanly, `cov=1.0000`. *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T05d)*
- **`CELL_EMPTY` spuriously refused a true courtyard's exact-partition sector split on 3 of 9 real void ≥ 6 m plates (e.g. `IT-BOL-GALVANI2/32501` k=2), even though the two cut lines were geometrically correct and `split(Z, unary_union(lines))` should have produced one polygon per sector** — the cut line's start point (`_point_at_t(t, ...)`, exactly on the void's own MRR boundary) is also exactly on `Z`'s boundary at that spot (the ring is notched away there for the opening), so the ray only registers *one* clean crossing with `Z.boundary` (the far exterior-wall exit) instead of two; GEOS's `split()` then cannot use it as a genuine dividing chord and returns the whole annulus as a single unsplit piece, leaving every other sector's `sector_parts[i]` empty. Fix: `cut_courtyard`'s exact-partition step (`scripts/eu21/05_group_cutters.py:723-727`) starts each cut line 0.3 m *inward* of the void-boundary point (clearly inside the ring/void, off the tangent) before extending `BIG` outward, giving `split()` an unambiguous two-crossing chord; verified this drops the failure to 1 of 9 real plates (a genuine higher-k sector-assignment refusal, not the same bug). *(implementation/PLAN_eu21-direct-cutters-2026-09-01.md §8 T05c)*

## 2. Extrusion, interzone surfaces and EnergyPlus geometry fatals

- **`Severe RoofCeiling:Detailed="BLOCK <stem>_CIRCULATION STOREY 0 CEILING 0001_2", Vertex size mismatch
  between base surface … and outside boundary surface: …_CIRCULATION STOREY 1 FLOOR 0001_1` (8 vs 9
  vertices), then `**FATAL:GetSurfaceData: Errors discovered, program terminates.` — task dies in 2–4 s
  with `ExitCode 1:0`, before warmup, on ~8 % of an array** (`FINDING 210`, wave 1 of `EU-16` T09;
  example task `1299912_33`, stem `8b3598ac47b3f4a0`, Madrid) — geomeppy's own `intersect_match` cuts a
  same-zone-label block (the carved circulation ring spans every storey under one label) against its
  per-storey neighbours and inserts intersection vertices **independently** for the ceiling of storey *n*
  and the floor of storey *n+1*, so the two rings end up with different final vertex counts even though
  the ring emitted going in was identical and already 1 mm-snapped. Fix: detect and reroute —
  `find_mismatched_interzone_pairs` then `_force_reroute_room_layout_to_one_zone_per_floor`
  (`scripts/run_eu_s2_campaign.py:516-534`, implementation `openubem/idf/surfaces.py:640`).
  🔴 **Read chapter 3 before treating this as closed** — the reroute silently costs the building its
  dwelling zoning and its core. *(prompts/DIRECTOR_PROMPT_european_locations.md item 0a; STATE v4 §3)*
- **The same fatal with the raw vertex counts *matching* (both surfaces 7 vertices, mirror-ordered) —
  `find_mismatched_interzone_pairs` reports 0 mismatches and EnergyPlus still fatals** (`D-EU-43`
  residual; reproduced locally on stem `e21bec78b937acf5`) — a sub-mm near-duplicate vertex pair that
  `intersect_match` inserted into **both** rings (one grid-clean from the 1 mm snap, the other an
  unsnapped raw intersection coordinate ~0.2–0.6 mm away); EnergyPlus's duplicate-vertex removal is
  winding-direction-dependent and collapses the two sides differently (4 vs 6). Fix:
  `_has_near_duplicate_vertex_surfaces` (`scripts/run_eu_s2_campaign.py:94`) gates on consecutive-vertex
  proximity so the reroute fires proactively instead of on a count that this defect does not always move.
  *(debugs/docs/INVESTIGATION_bologna-failure-classification_2026-08-31.md)*
- **A whole district's IDFs predate a geometry fix and fail with a signature already known and already
  fixed — Bologna 177 `FAILED` of 1,204, split 85 exact `FINDING 210` + 52 exact `D-EU-43` + 40
  zero-area-only** — the fix was applied and Madrid / Lyon / London were rebuilt; Bologna was not, so its
  IDFs still carried the old geometry. Fix: rebuild through the unmodified gate and resubmit — done
  under `D-EU-47` (176 of 177 rebuilt and proven locally, 1 excluded pre-ship) but **the wave was
  cancelled before harvest by `D-EU-53`**, so the 177 stay recorded as failures and are recovered inside
  `EU-19`. Rule this teaches: after a geometry fix, **enumerate which districts' artefacts were actually
  rebuilt** — a per-district mtime histogram of `idfs/*.idf` answers it in one command
  (`find <district>/idfs -name '*.idf' -printf '%TY-%Tm-%Td %TH\n' | sort | uniq -c`).
  *(debugs/docs/INVESTIGATION_bologna-failure-classification_2026-08-31.md)*
- **`** Warning ** Indicated Zone Volume <= 0.0 for Zone=…` / `The calculated Zone Volume was=-49.03` /
  `… set to 10.0 m3`, together with `GetVertices: Floor is upside down! Tilt angle=[0.0]`** — OSM
  footprints arrive clockwise-wound and the by-storey extrusion path uses them unoriented, so the
  divergence-theorem volume integrates negative and EnergyPlus substitutes a fixed 10 m³. **Not cosmetic
  where infiltration/ventilation is `AirChanges/Hour`**: measured in the EU S2 campaign, 103/103 zones in
  31/31 buildings, 1,030.0 m³ of air simulated against a true 59,470.92 m³ — a **57.74× understatement**;
  re-winding without repairing the volume still leaves −11.8 % on heating demand, with EnergyPlus's own
  reported floor area, volume, wall area and surface count byte-identical between the two runs. Fix:
  `orient(poly, sign=1.0)` before `build_zones`, and `write_zone_volumes(idf, zones)` after
  `extrude_geometry` (`openubem/idf/builder.py:217`). ⚠ Trap when sizing the error: do **not** take
  |calculated volume| as the truth — read `Ceiling Height` and `Floor Area` from `eplusout.eio`.
  *(debugs/docs/DONE-docs/DECISION_REQUEST_EU-17_zone_volume_10m3_2026-08-26.md;
  docs_EXPLANATION/OpenUBEM_debug_References.md ch. 1, ch. 14)*
- **A geometry fix proven by a Python-only vertex-count check passes, and the same buildings still fatal
  on real EnergyPlus** (progress-log entry `T09-FINDING210-ROOTCAUSE-FIX-V2`) — the defect is created by
  EnergyPlus's own `GetVertices`/`CheckConvexity` collapse, downstream of anything a shapely-level check
  can see. Fix: no geometry change ships on synthetic proof. Run
  `ExpandObjects.exe` + `energyplus.exe` 23.1.0 locally on at least one building per failure signature
  and report RC and severe/fatal counts. *(prompts/previous/PROMPT_D-EU-47_bologna_rebuild_resubmit.md
  §Task item 3)*
- **[OPEN] `idf.intersect_match()` raises `ZeroDivisionError` outright (not a vertex-count mismatch
  after a successful match) on a real, non-degenerate multi-storey ruled layout — reproduced locally,
  no fatal geometry (no near-zero edges, min edge length 2.89 m) on `relation/12582233`
  (stem `c6e90803c98dba87`, Madrid, 7 storeys, `ruled_grid_2x1`), caught by the existing
  `try/except (IndexError, Exception)` around `idf.intersect_match()`
  (`openubem/idf/surfaces.py:865-884`, inside `extrude_geometry`) and rerouted via
  `_force_reroute_room_layout_to_one_zone_per_floor`** — investigated for `EU-17` T09(a): the dwelling
  and circulation zones on this building are genuine non-axis-aligned octagons/hexagons (the plate's long
  axis sits at an angle, not orthogonal to the UTM grid), stacked identically across 7 physical storeys;
  geomeppy's `intersect_match` is documented (chapter 2, `FINDING 210` entry above) to derive interzone
  intersection vertices **independently per storey pair**, and this is the same mechanism failing harder
  (an exception, not just a divergent vertex count) on rotated non-rectangular multi-storey stacks. Fix:
  **not fixed** — this is a geomeppy-internal numerical fragility on rotated polygon intersection, not a
  ring-construction defect this task's file list can reach (`openubem/idf/builder.py`, where the block is
  actually assembled from these coordinates, is not in `EU-17`'s editable set; a change to the geometry
  feeding it cannot be verified without EnergyPlus, which `D-EU-55` forbids this task from running). A
  Python-only fix attempted here without that proof would repeat exactly the false-green this arc has
  already had once (`T09-FINDING210-ROOTCAUSE-FIX-V2`, entry above) — left as a disclosed residual for
  `T13`, whose "How" already routes EnergyPlus-level proof of this class there
  (`FINDING 219`, `[OPEN]`).
  *(`EU-17` T09, `PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md` §6 T09)*
- **`FINDING 221` (P01) confirms `FINDING 219` fleet-wide and shows the prescribed fix does not reach it.**
  941 buildings carrying `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` were assumed (P00
  diagnosis, `PLAN_eu21-group-schemes-2026-09-01.md` §8) to be an over-broad ring-construction mismatch,
  since the discarded polygons were independently confirmed geometrically sound (max overlap 1e-10, area
  conserved to ≤0.01%). Reproducing `relation/12582233` (stem `c6e90803c98dba87`) with the blanket
  `except (IndexError, Exception)` (`openubem/idf/surfaces.py:867`) bypassed confirmed the exact
  `FINDING 219` signature — `ZeroDivisionError: division by zero` in
  `geomeppy/geom/vectors.py:105 Vector3D.set_length` via `minimal_set`/`normal_vector`
  (`geomeppy/geom/surfaces.py:147,164`), not the `IndexError` the code comment at `surfaces.py:863-864`
  names — but a district rebuild also shows the *other* raw signature, `IndexError` out of
  `break_polygons`, occurring in the same population (e.g. Lyon `f07c2c6a5deab600`). Root cause,
  confirmed by instrumenting `minimal_set`: a group of coplanar candidate surfaces at one storey
  boundary includes near-zero-area sliver fragments (~1e-9–1e-15 m²) produced when geomeppy's own
  `intersect()`/`polygonize` clips two adjacent zones' 3D-projected surfaces that are not bit-identical
  at their shared edge — confirmed **not** an input-coordinate defect (the raw `coords_m` per zone
  were already bit-identical at every shared vertex before extrusion; a global cross-zone vertex-snap
  pass at the `_stabilize_ring_coords` 1 mm grid, `_snap_shared_interzone_vertices`,
  `openubem/idf/surfaces.py:775-817`, `:822`, found nothing to unify on this building and moved the
  fleet-wide `..._REROUTED` count only 941→939 across all four `EU-21` districts). This matches
  `FINDING 219`'s own conclusion: the divergence is introduced by geomeppy's own downstream
  intersection arithmetic, not by ring construction, and is not reachable by a Python-only fix without
  EnergyPlus-level proof (`D-EU-55` forbids running it here). Fix: `_snap_shared_interzone_vertices`
  kept (additive, harmless, resolves a small residual where raw coordinates genuinely do diverge) but
  does not meet `P01`'s own ≥1,450-ruled acceptance bar (actual: 543 ruled, 939 still `..._REROUTED`
  fleet-wide). Per-storey scoping of the safety net (P01 T3) is separately blocked —
  `geomeppy/idf.py:247-260 add_block()` stacks `num_stories` only from a ground-relative origin, with no
  parameter to reinsert one interior storey's box at its true z while leaving the storeys above and below
  untouched — and `_purge_idf_geometry` (`surfaces.py:305-314`) clears the whole per-building IDF, so a
  true single-storey retry would require rebuilding all storeys' geometry on every attempt, not a
  targeted patch. Left `[OPEN]`, same disposition as `FINDING 219`/`220`. *(`P01`,
  `PLAN_eu21-group-schemes-2026-09-01.md` §8)*
- **[OPEN] The same class as `FINDING 219` above, but the reroute's own re-check still finds a mismatch
  and the *whole building* is lost, not just rerouted — `RuntimeError: interzone_vertex_mismatch_
  unresolved: mismatched=[] near_duplicate_vertex=True`, raised at `scripts/run_eu_s2_campaign.py:531`
  after `_force_reroute_room_layout_to_one_zone_per_floor` has already run once (`:512-513`) and
  `idf.intersect_match()` + the roof/horizontal/interfloor repair passes have already been re-applied
  (`:514-517`) — the residual `near_duplicate_vertex` (or, rarely, `mismatched`) check still fires, so no
  IDF is written for that building at all; `prepare()`'s outer `except (RuntimeError, ZeroDivisionError,
  IndexError)` (`scripts/run_eu_s2_district_campaign.py`) catches it as `IDF_ASSEMBLY_FAILED_RuntimeError`
  and the building is silently absent from `prepared_buildings.csv` — a full population loss, not a
  refusal-to-box.** Discovered rebuilding all four districts for `EU-17` T10 with today's T05-T09
  geometry (`openubem/outputs/eu_evidence/EU-17/<district>/`, 2026-08-31): **633 of 2,544 buildings
  (24.9 %) lost fleet-wide** — Madrid 284/961 (29.6 %), Lyon 28/297 (9.4 %), London 9/82 (11.0 %),
  Bologna 312/1,204 (25.9 %) — versus **0** such losses when these same four districts were built by the
  pre-T05 generator (EU-11's `summary.json` per district: `population_prepared` 961/297/82/1,204 exactly,
  `speed_failure_kinds: {}`). Confirmed not confined to newly-recovered ruled layouts: `relation/3730743`
  (Madrid, the `EXAMPLE_…md` §6 acceptance building that is *supposed* to refuse cleanly to a `whole`-zone
  box at the density cap, touching no ruled route at all) is lost to this exact `RuntimeError` too — the
  fragility is in extrusion/interzone-pairing of the real (rotated, GIS-noisy) footprint itself, not
  specific to the wider L-shape/courtyard wing search T05/T06 added. Not fixed, for the same reason as the
  `FINDING 219` entry above: no ring-construction defect reachable from `EU-17`'s editable file list, and
  a Python-only change cannot be verified without EnergyPlus (`D-EU-55`). Routed to `T13` alongside
  `FINDING 219` (`FINDING 220`, `[OPEN]`). *(`EU-17` T10, `PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md` §6 T10)*
- **`FINDING 220` root cause, on a 47-building sample (8 named
  rules-regression buildings + a stratified 39-per-district loss sample): `_force_reroute_room_layout_
  to_one_zone_per_floor` is never the bug — on every one of the 44 reroute calls observed, its actual
  return value matched a read-only, independent replica of its own footprint-reconstruction test
  (`openubem/idf/surfaces.py:681-709`), 100 % agreement. The gap is architectural, one file outside
  `EU-17`'s editable list: `build_idf_for_building`'s post-extrude at-risk gate
  (`scripts/run_eu_s2_campaign.py:516-534`) raises `RuntimeError` whenever `_has_near_duplicate_vertex_
  surfaces` fires (never `find_mismatched_interzone_pairs` — confirmed 0/41 in the sample) **and** the one
  safety net wired to it correctly declines to help, for one of two reasons that are both by-design, not
  bugs: (a) 38/41 — `zones` carries no `room_layout`/`european_dwelling_layout` mode zone at all (the
  building is already a plain `one_zone_per_floor` box before extrusion, either a clean generator
  refusal or, for two of the eight named buildings, the acceptance-correct outcome itself), so there is
  structurally nothing left to reroute; (b) 3/41 (all Madrid, all `DWELLING_LAYOUT_EMITTED`) — the
  courtyard-hole guard (`:693`) correctly refuses to collapse a genuine void (interior ring ≥ 1.0 m²,
  independently re-derived) into an illegal single holed block. Neither branch is a bug — both match the
  function's own docstring (`:651-653`, `:692-694`) exactly; 0/41 fail the reroute's own geometric
  reconstruction. `_has_near_duplicate_vertex_surfaces` itself is new — added the same day as this
  `FINDING 219`/`220` work (comment dated 2026-08-31, `scripts/run_eu_s2_campaign.py:71-91`) — so EU-11's
  zero losses predate the check that produces these losses; it is not evidence EU-11's geometry was any
  cleaner. Two of the eight named buildings (`BATIMENT0000000240879941_part0`,
  `BATIMENT0000000240880045_part0`, Lyon) are **not** part of this defect class at all: both are excluded
  upstream of `_geometry()` entirely, at `_mapped_rows`'s archetype-mapping gate
  (`TYPOLOGY_SIGNALS_DISAGREE` and `MISSING_OBSERVED_YEAR_BUILT` respectively) — confirmed by replaying
  the gate directly against `02_residential_manifest.gpkg`. Not fixed — the fix would be a new fallback
  tier (tolerate the box/courtyard geometry instead of raising) inside a file outside `EU-17`'s editable
  set, and per the `FINDING 219` entry's own precedent a Python-only argument is not proof it is safe;
  `D-EU-55` forbids the EnergyPlus proof that would be. The specific decision (tolerate vs. keep raising)
  is reported to the director/owner, not invented. **Fixed** (owner ruling `D-EU-58`, 2026-09-01, "vas-y",
  option (a)): the post-extrude at-risk gate (`scripts/run_eu_s2_campaign.py:530-556`) now retains the
  building's already-emitted geometry instead of raising when `did_reroute is False` **and** `mismatched`
  never fired at any point — exactly the pattern this entry traced on 41/41 sampled losses — and tags every
  zone with `fallback_reason="near_duplicate_vertex_tolerated_box"`, surfaced as its own column in
  `prepared_buildings.csv` (`scripts/run_eu_s2_district_campaign.py:391-398`, `:430-431`). Any building
  where `mismatched` is truthy at any point still raises, unchanged. Verified on the full four-district
  rebuild: all 633 buildings lost in T10's run recovered exactly (ES 284, FR 28, GB 9, IT 312), 0 residual
  `IDF_ASSEMBLY_FAILED_RuntimeError`/`interzone`-class losses remain in any `summary.json`, and 0 of a
  39-building spot-check of the tolerated population independently re-fails
  `find_mismatched_interzone_pairs`. `pytest -q tests/` (serial) unaffected: 2540 passed / 55 skipped / 5
  failed, same named failures as the T05/T10/T14 baseline. *(`EU-17a` T14 / `EU-17b` T15, `PLAN_eu17-eu18-
  boxrule-atlas-2026-08-31.md` §6 T14/T15, `scripts/eu17_reroute_trace.py`)*

---

## 3. The viewer vs the simulated IDF

🔴 **This is the arc's most recurrent defect class — three occurrences, three different mechanisms, one
symptom: the pop-up shows geometry that never ran.**

- **[OPEN] The side-car declares `has_unconditioned_core = true` and a ruled grid; the IDF that ran is
  `<stem>_F0_whole`, `<stem>_F1_whole`, … — one undivided zone per floor. 459 of 2,544 buildings
  (Madrid 175, Lyon 52, London 18, Bologna 214); only 2 of them disclose it** (`FINDING 213`, measured
  2026-08-31) — the `FINDING 210` safety net (chapter 2) reroutes **inside** `build_idf_for_building`,
  unioning the storey-0 sub-zones back into one block per floor and dropping the circulation zone with
  them (`openubem/idf/surfaces.py:640`). The disclosure that writes it back into `geometry_outcome`
  exists (`scripts/run_eu_s2_district_campaign.py:387-390`) but was added 2026-08-31, after the IDFs of
  2026-08-30 were built; and the side-car emitter regenerates the layout from the footprint
  (`scripts/emit_eu11_layout_sidecars.py`), so it never learns of the reroute at all. Fleet effect:
  **1,555 of 2,544 IDFs (61.1 %) are one zone per floor** while the side-cars report 43.1 % refused.
  Fix (partial, `EU-17` T09(b)) — the side-car emitter now reads the IDF's own zone kinds (T01's
  `scripts/eu_idf_plan_reader.py::read_district`), not just the independently-recomputed footprint layout:
  when the generator would emit a ruled layout but the built IDF carries only `whole`-kind zones, the
  side-car (and the manifest's `geometry_outcome`, via the existing `updated_outcomes` write-back) is
  overridden to `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` with no circulation and IDF-measured
  (not ruled-route) areas (`scripts/emit_eu11_layout_sidecars.py`, the `idf_reroute_divergence` branch).
  This closes the mechanism (no side-car can advertise a layout the IDF does not carry) but was verified
  only in isolation against the read-only EU-11 tree (rule 3 forbids writing there) — confirmed correctly
  flags the known example below and does **not** flag a genuine `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8`
  refusal (`relation/12582232`) as a false positive. The **459/518 count itself is not closed** until
  `T10` rebuilds fresh IDFs with today's generator and re-runs this emitter against them — running it now
  against EU-11's existing (pre-`EU-17`) IDFs would both violate the EU-11 read-only rule and compare
  today's improved generator against yesterday's IDFs, inflating the count with recoveries `T05`/`T06`/
  `T08` made possible rather than genuine `FINDING 213` cases. Diagnostic in one command (unchanged):
  `grep -lE "_F[0-9]+_whole,[ ]*!- Name" <district>/idfs/*.idf | wc -l`. *(STATE v4 §3 `FINDING 213`;
  `EU-17` T09, `PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md` §6 T09)*
- **`geometry_outcome` is computed before the IDF is built, so any in-build reroute leaves it stale** —
  `scripts/run_eu_s2_campaign.py:681-692` records the outcome from `build_geometry_for_row` and only then
  calls `build_idf_for_building`, which may reroute. Fix: the district path now re-derives the outcome
  from the zones after the build (`scripts/run_eu_s2_district_campaign.py:387-390`, 2026-08-31); the
  single-district path at `run_eu_s2_campaign.py` still does not. *(same)*
- **`EU-13`'s `geometry_outcome` disagreed with the `heating_kwh` / `floor_area_m2` already harvested for
  the same building — `relation/12582232` labelled `DWELLING_LAYOUT_EMITTED` with
  `floor_area_m2 = 1089.2873`, exactly 272.32 m² × 4 storeys, the massing-box total** — the side-car
  emitter recomputed the outcome and the pop-up zones from the footprint alone, entirely independent of
  `run_eu_s2_district_campaign.py:_geometry`, the function that actually built the submitted zones; that
  function's layout branch omitted `n_storey=` and its `else` branch had no dwelling-count imputation, so
  most newly-labelled buildings had in fact been simulated under older massing-box zoning. Fix:
  `_geometry` now mirrors the emitter exactly — same stacking, same four-tier imputation, same outcome
  strings (`scripts/run_eu_s2_district_campaign.py:112`). ⚠ **That fix made the two *generators* agree
  and cannot see the entry above, which happens downstream of both.**
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. "European locations X-05"; `D-EU-35`)*
- **The four viewers looked visually unchanged after `EU-13B`'s ruled math landed — no circulation ring
  anywhere** — the ruled partitioner computed a real per-storey circulation polygon, but
  `scripts/emit_eu11_layout_sidecars.py` discarded it before serialization and the viewer's
  `drawFloorPlan` had no code path to draw it. Fix: both scripts carry and draw the ring; unit test
  covers the ruled-grid (non-null) and `l_shape_decomposition` (`None`, pinned) cases; all four districts
  regenerated and mirror-verified. `FINDING 206`, fixed 2026-08-30.
  *(debugs/docs/INVESTIGATION_viewer-circulation-not-drawn_2026-08-30.md)*
- **[OPEN] `FINDING 215` — `EU-18a` T03's parity gate does not reproduce `FINDING 213`'s pinned 459 -- it finds 518
  (Madrid 234, Lyon 52, London 18, Bologna 214) -- a fourth, previously undocumented mechanism, isolated
  to Madrid and disjoint from the 175 already-known `FINDING 213` buildings** — a side-car's absorbed
  floor group (`storey_span > 1`, `european_residential.py:1857-1880`) declares a group height that
  reaches the side-car's own `storeys` total (verified self-consistent: `Σ storey_span` over its own
  `floors[]` groups equals `storeys` on every checked building), but the *IDF's own emitted zone* for
  that same group is shorter — its tallest surface's Z-coordinate implies **fewer** physical storeys than
  the side-car declares (measured off `parse_idf_floor_zones`'s `zone_max_z` / `FLOOR_TO_FLOOR_M = 3.0`).
  59 of 961 Madrid buildings, mostly off by exactly one storey (50), the rest off by 2-4 (5 / 2 / 2).
  Example: `way/289979823` (stem `010460eeb4131522`) -- side-car `storeys: 4`, its own `floors[]` shows a
  3rd group at `storey_index 2-3` with `storey_span: 2` (implying the group's zone should extrude 6.0 m
  to 12.0 m), but the IDF's `010460eeb4131522_F2_dwelling_0` zone only reaches Z = 9.0 m (`storey_span`
  of 1, not 2) -- 3 `ZONE` objects total (`F0`, `F1`, `F2`), not the 4 physical storeys the side-car
  declares. `scheme_consistent`, `zone_names_equal` and `circulation_presence_equal` all pass on these 59
  (the group's dwelling/circulation split is internally fine); only the storey count is short. Fix: not
  fixed -- root cause not yet located (candidate: `n_storey` computed differently between
  `scripts/run_eu_s2_district_campaign.py:_geometry` and `scripts/emit_eu11_layout_sidecars.py` for these
  59 specifically, contradicting fact 8's premise that both layers call the generator identically).
  *(EU-18a T03, `openubem/outputs/eu_evidence/EU-18/parity_ES-MAD-BERRUGUETE.csv`,
  `PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md` §6 T03)*
- **`eu18_parity_gate.py` reports 100 % `NO_SIDECAR` divergence (every building) on a freshly rebuilt
  `EU-17/<district>/` tree** — `run_eu_s2_district_campaign.py` writes `idfs/`, `prepared_buildings.csv`
  and the manifest, but never a `layouts/` side-car directory; that is a separate step
  (`scripts/emit_eu11_layout_sidecars.py`), and T15's rebuild (`D-EU-58`) invoked only the campaign
  script, not the side-car emitter, so `layouts/` was absent from the tree it left behind (unlike T10's
  own rebuild, which had run both). Fix: none needed in code — re-run
  `python -m scripts.emit_eu11_layout_sidecars --evidence-root <D>=<abs path>` per district (mirrors
  T10's own precedent) before `eu18_emit_plan_pages.py` / `eu18_parity_gate.py`; this populates
  `layouts/` (961/297/82/1204 files, matching the census) and the gate then measures the real
  `FINDING 213`/`FINDING 215` divergence instead of `NO_SIDECAR` noise. *(EU-18b T12,
  `PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md` §6 T12)*

---

## 4. Context geometry, shading and adiabatic party walls

- **`0` of 2,516 district IDFs contained a single `Shading:*` object or a single `Adiabatic` surface,
  while the method of record requires every building within 20 m as shading and adiabatic party walls**
  (`FINDING 208`) — one line: `extrude_geometry(idf, zones, [])` hard-coded an empty context list
  (`scripts/run_eu_s2_campaign.py:227` at the time), and no `ShadowCalculation` object existed. Fix:
  `build_european_context` + `apply_adiabatic_party_walls` wired into the district path (`EU-16` T06/T07).
  Re-measured 2026-08-31: **shading on 2,544 of 2,544 (100 %)**. *(rules/RULES_context_geometry_simulation_2026-08-30.md)*
- **`grep "Shading:" *.idf` returns zero on IDFs that do carry shading** — object names are written
  **UPPERCASE** on disk (`SHADING:SITE:DETAILED`), so a case-sensitive grep silently reports a false
  absence. Fix: always `grep -i`. This one has already produced a wrong "before" number once in this arc.
  *(prompts/PROMPT_EU-VAL_validation_audit_T10.md §(c))*
- **`set_adiabatic_surfaces(idf, zones, strategy)` cannot implement the inter-building party-wall flip,
  although two rule documents said it should** — it is a documented **no-op stub**
  (`openubem/idf/surfaces.py:909`) and its signature carries no neighbour footprints, so it can never
  know which wall is shared. Fix (`D-EU-41`, 2026-08-30): `openubem/idf/surfaces.py` stays non-editable;
  the flip is a European-only pass in `scripts/run_eu_s2_campaign.py` reusing `build_european_context`'s
  own neighbour rows and transform. Disclosure required with it: **flipped exterior wall area as a
  fraction of total exterior wall area** — an object count cannot distinguish one wall from half an
  envelope. *(rules/RULES_context_geometry_simulation_2026-08-30.md §2 `R6`)*
- **[OPEN] Adiabatic coverage is 89.4 / 86.5 / 70.7 / 80.7 % (Madrid / Lyon / London / Bologna) against
  an attachment census expecting 99.1 / 97.0 / 92.8 / 88.5 %** — measured by `EU-16A` T08, re-measured
  identically 2026-08-31 (859 / 257 / 58 / 972 IDFs carrying an `Adiabatic` surface). Reported as
  measured, never tuned, and **not explained anywhere on disk**. *(STATE v4 §3)*
- **[OPEN] London's mean context count is 7.52 neighbours against 11.60 in the rules-doc census; the
  other three agree to ±0.4** — measured over `prepared_buildings.csv:context_building_count`
  (Madrid 11.88, Lyon 12.28, London 7.52, Bologna 11.22; zero buildings with an empty context). Note this
  **supersedes** the `EU-16A` audit's carried claim of 30.1–49.1 neighbours, which does not reproduce on
  today's artefacts. *(STATE v4 §3)*

---

## 5. Areas, denominators and EUI arithmetic

- **A manifest column named `eui_kwh_m2` that is in fact a heating-only intensity** — the numerator is
  `heating_kwh`, the annual sum of hourly `Zone Ideal Loads Zone Total Heating Energy`; it carries no
  lighting, no appliances, no DHW, no cooling, so quoting it as a whole-building EUI is wrong by a large
  factor **in the direction that looks plausible**. Fix: the promoted artefact is not renamed; the basis
  is carried additively and no pooled figure is printed without the words "heating-only".
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. 8; previous/MVP_european_locations.md §9.7.3)*
- **[OPEN] `floor_area_m2` equals `gross_footprint_area_m2` on 2,544 of 2,544 rows and
  `conditioned_floor_area_m2` on none, although `D-EU-39` §3 ruled that carving the core moves every EUI
  denominator** (`FINDING 214`) — `scripts/run_eu_s2_district_campaign.py:408-418` assigns the gross sum
  to `floor_area_m2`. Both areas are published side by side, so the disclosure half of the ruling is met
  and the arithmetic half is not. Effect on the 582 buildings that carry a core: conditioned/gross means
  0.9551 / 0.9598 / 0.9083 / 0.9359, minimum 0.5189. Fix: not fixed — must be settled explicitly before
  any figure is restated. *(STATE v4 §3 `FINDING 214`)*
- **`gross_footprint_area_m2` is not a footprint area** — it is the building total, summed once per
  storey **group** (`european_building_layout_area_summary`, `openubem/geometry/european_residential.py:1904`),
  while `circulation_area_m2_total` is summed over physical storeys. The two are consistent
  (conditioned + circulation − gross ≤ 1.2 × 10⁻⁶ relative, measured fleet-wide) but the name invites a
  per-floor reading and a spurious ×storeys conservation failure. Diagnostic: check
  `conditioned + circulation == gross` **without** multiplying by `storeys`. *(STATE v4 §3)*
- **Shoelace area from raw IDF `BuildingSurface:Detailed` vertices disagreed with an independent shapely
  oracle by up to 3.6 × 10⁻⁵ relative, failing a 1 × 10⁻⁶ parity test** — the vertices are absolute UTM
  metres (~4.4 × 10⁵ / 4.5 × 10⁶); `Σ(x1·y2 − x2·y1)` on coordinates of that magnitude cancels ~5-6
  significant digits against a zone area of only ~10¹-10² m², a catastrophic-cancellation loss double
  precision cannot recover. Fix: `_ring_area` in `scripts/eu_idf_plan_reader.py` shifts every ring to its
  own first vertex before summing. *(EU-18a T01, `tests/test_eu_idf_plan_reader.py`)*

---

## 6. Speed: submission, walltime, harvest, tcsh

- **9 Lyon array tasks end in `TIMEOUT`, `eplusout.err` empty, no `task.rc`, working files present** —
  genuine wall-clock exhaustion, not a defect: all 9 exceeded the 2-hour limit by **0–28 s**
  (`scripts/cluster/submit_fleet_t08.sbatch:5`, `--time=02:00:00`), 8 of the 9 in the ≥72nd percentile of
  floor area. Fix: never edit the shared sbatch — override on the command line
  (`sbatch --time=… --array=…`). 🔴 **A 3 h override was then observed to time out twice as well**, so the
  standing rule is `--time=7-00:00:00` minimum on every submission: SLURM bills actual usage, a generous
  request costs nothing, and it removes the resubmit cycle entirely.
  *(debugs/docs/INVESTIGATION_lyon-timeout-classification_2026-08-31.md; previous/BRIEF_european_locations_v3.md §5;
  CLAUDE.md §CLUSTER)*
- **A harvest finds nothing under `openubem/fleets/EU11R2_<district>/`** — those are **upload staging**
  entries (`.tgz` + `.submit.sbatch`) only; a missing one is harmless. The arrays run
  `submit_fleet_t08.sbatch` with `FLEET_DIR=/speed-scratch/o_iseri/fleets/EU11_<district>`, so results
  live at `/speed-scratch/o_iseri/fleets/EU11_<district>/out/<stem>/`. Fix: harvest the `EU11_*` tree; a
  resubmit wave ships to its own dedicated dir (`EU11_<district>_deu47`) and never overwrites the shared
  base tree in place. *(prompts/DIRECTOR_PROMPT_european_locations.md item 0a)*
- **`sbatch` fails, script not found** — the remote path was guessed flat as
  `/speed-scratch/o_iseri/openubem/scripts/submit_fleet_t08.sbatch`; it is nested:
  `…/scripts/cluster/submit_fleet_t08.sbatch`. Fix: use the `cluster/`-nested path in every call.
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. 12)*
- **A remote command sent over bare `ssh` silently does nothing, or dies on a `!` in the string** — the
  Speed login shell is **tcsh**: bash syntax fails silently and `!` triggers history expansion. Fix: wrap
  every remote command in `bash -lc` via the repo's `_ssh()` helper
  (`scripts/cluster/t08_harvest_results.py:104`), and never put `!` in a remote command string.
  *(CLAUDE.md §CLUSTER)*
- **Every array task fails instantly with `Schedule:File=… not found`** — `ship_eu11_fleet.sh` staged and
  tarred only `idfs/`, `weather/`, `fleet.lst`, never the local `schedules/` directory, so the remote
  fleet had no schedule CSVs at all (100 % failure across Madrid 961, Lyon 297, London 82). Fix: stage
  and tar `schedules/` too; re-shipped and resubmitted clean.
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. 12)*
- **`FileExistsError: [WinError 183]` on `schedules/<stem>/`** — a preparer that unconditionally
  `mkdir()`s into a tree left over from a previous preparation (no `exist_ok`, no cleanup). Seen twice, at
  two call sites: `ship_eu11_fleet.sh`'s staging step, and `run_eu_s2_district_campaign.py::prepare`
  itself (`:347`). Fix: clear `idfs/`, `weather/`, `schedules/`, `fleet.lst` under
  `openubem/outputs/eu_evidence/EU-11/<district>/` before every `prepare()` re-run — otherwise stale
  CSVs from a superseded regeneration leak into the new tar.
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. 12, "European locations EU-13B")*
- **Never compute on the login node** (`speed-submit2` / `speed.encs.concordia.ca`) — no `srun`, no
  `ssh … python`. Login node is `mkdir` / `scp` / `tar` / `squeue` / `sacct` only. Always
  `sbatch --array`, fire-and-forget, then read the output file. Submit in waves under the ~20,000-task
  cap; harvest by expanding file lists **remotely** and streaming a tar (a local path list overflows
  Windows argv at ~32 KB). *(CLAUDE.md §CLUSTER)*

---

## 7. Schedules, weather and file paths

- **`Schedule:File=…, File Name: "C:\Users\…\*_gain.csv" not found` on Speed** — the accepted S2 builder
  emits an **absolute Windows** schedule path, valid locally and meaningless on Linux once the IDF alone
  is staged. Fix: `run_eu_s2_district_campaign.py::prepare` stages the byte-identical gain CSVs under
  `schedules/<stem>/` and retargets only each `Schedule:File` path to `../../schedules/<stem>/…`,
  relative to the array task's output directory.
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. "European locations EU-10")*
- **`FileNotFoundError` on `…/ES-MAD-BERRUGUETE/relation/12582232/relation/12582232.idf` the first time a
  runner met a Spanish building** — OSM stable ids are `way/123` / `relation/456` and the **slash is a
  path separator**, so every place that names a file after `building_id` silently opens a directory
  level: run directory, IDF, zone names, and each `Schedule:File` CSV. France never exposed it because
  BD TOPO ids (`BATIMENT0000000240879449_part0`) carry no slash — a runner can pass every French test and
  still be unable to write its first Spanish IDF. Fix: a `run_slug` that maps `/` to `_` for **naming
  only**, with the true `building_id` kept beside it in the manifest.
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. 7)*
- **`ERROR: Could not find input data file: <dir>\<dir>\<name>.idf`, `returncode=1`, no `eplusout.err` at
  all** — the runner built its temp directory from a **relative** `Path` and passed the still-relative
  `idf_path` alongside `cwd=tmp_root`; `cwd=` does not rebase relative path *arguments*, so EnergyPlus
  resolved it a second time against the new working directory. Fix: `.resolve()` the temp directory
  before building the `.idf` path from it (`scripts/run_eu_s1_smoke.py:283`).
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. 13)*

---

## 8. Data acquisition per country

Full entries live in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` **ch. 7**; this is the routing
list, so an arc session knows the symptom has been seen before.

- `HTTP Error 429 / 504` from `overpass-api.de/api/interpreter` on city-scale extracts.
- Building counts silently wrong when a WGS84 bbox is passed to `ingest_buildings` in GeoJSON order.
- A residential filter over OSM tags returns almost nothing in Italian and French cities.
- `data.geopf.fr` WFS `GetFeature` returns `"features": []` with HTTP 200 and no error.
- `HTTP 400 "No se puede procesar su peticion."` from the Spanish Catastro INSPIRE Buildings WFS — it
  answers a bbox question in exactly one parameter form, and any other form fails as an HTTP error.
- `curl` returns `HTTP 000` with 0 bytes for `catastro.minhap.es/INSPIRE/…` while the same path works
  under another host.
- The MHCLG/EPC endpoint pinned by `D-EU-10` is retired; its successor sits behind an account, and the
  old one answers `301` onto a GOV.UK landing page.
- ISTAT 2011 section breakdowns do not sum to the residential-building total (`E4+E5+E6 = 1,140` vs
  `E3 = 1,010`); and a zero join rate is a broken probe until proven otherwise — the ISTAT section key is
  **`NSEZ`**, not `SEZ2011`.
- `URLError [SSL: CERTIFICATE_VERIFY_FAILED]` against the Emilia-Romagna geoportal.
- A UPRN-to-footprint spatial join silently loses ~13 % of its pairs (London: 1,059 footprints instead of
  the pinned 1,219), with no error and no warning.
- Bologna construction period is `IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` on **100 %** of rows —
  never quote a Bologna figure without saying so. *(EU11_Bologna_construction_year_investigation.md)*

---

## 9. Reproducibility and certification traps

- **A campaign cell exits `0`, is recorded `completed: true`, `severe_count: 0`, `fatal_count: 0`, no
  `.err` marker — and returns a different heating value on the next identical run** — measured at
  429,401.898 kWh twice and 111,864.121 kWh once (−74.0 %) for
  `uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000`, strictly serial, from a byte-identical model. Fix: none —
  `D-EU-27` certifies a cell only when **three** independent replicates return a bitwise-identical
  `heating_kwh` with zero severes and zero fatals; the worst disagreement that filter rejected was
  382.1 %, so it must never be relaxed to two of three.
  *(implementation/previous/PLAN_finding181-stability-2026-08-28.md §7)*
- **[OPEN] `completed: true` and `clean: true` are each necessary and NOT sufficient** — EnergyPlus
  reports the diverging inside-surface heat balance as a **Warning**, which raises neither counter, so
  `marker_psy` / `marker_inside_hb` / `marker_calchb` must be screened from `eplusout.err` as well.
  42 certified cells carry `marker_psy` in all three replicates and **all 42 are `es`**; `D-EU-28`
  restricts the quotable perimeter to the 149 marker-free certified cells (`uk` 75, `it` 74, `es` 0).
  *(previous/MVP_european_locations.md §9.7.3)*
- **`idf_sha256` differs between two runs of the same cell although the model is identical** — the
  `Schedule:File` `File Name` field holds the **absolute** path (`openubem/semantic/european_schedules.py:119`),
  so the digest embeds the run directory. Fix: none applied — the digest is a run identifier, not a
  model-provenance key. *(implementation/previous/PLAN_finding181-stability-2026-08-28.md §7)*
- **A Speed number and a Windows number are not the same measurement** (`FINDING 187`, `FINDING 190`) —
  EnergyPlus 23.1.0 Ubuntu20 on Speed and 23.1.0 on Windows do not agree bitwise. Never mix them inside
  one pooled figure, and never validate a Speed result by re-running it locally and calling the local
  answer the truth.

---

## 10. Method traps

- **A reason token emitted by fall-through is not evidence of that failure mode.** `HABITABILITY_GATE_
  FAILED_AFTER_ROTATION` on 84 % of the fleet was an empty-intersection bug (ch. 1). Check the cell count,
  the vertex count, the actual intermediate — not the label.
- **Measure conformance on the artefact that ran, never on the layer that describes it.** Side-cars said
  43.1 % refused; the IDFs said 61.1 % boxes. Both were on disk at the same moment (ch. 3).
- **A synthetic check is not proof for a defect EnergyPlus creates.** (ch. 2)
- **Read what a warning says; do not count warning kinds.** A triage gate that only counts is satisfied
  by six kinds of which two invalidate the result. *(zone-volume entry, ch. 2)*
- **After a fix, enumerate which artefacts were actually rebuilt.** Bologna carried 177 failures of a
  signature that had already been fixed, purely because its IDFs were never regenerated (ch. 2).
- **A 0-byte log is not a dead job, and an ambiguous status is not a reason to double-dispatch.** Check
  CPU time first (`sacct`), then decide.
- **Never tune an input to move an EUI into a band**, and never remediate a baseline while measuring it.

---

## 11. Not-a-bug: by design in this arc

- **`>8 dwellings/floor` is refused, not approximated** (`FINDING 202`, `D-EU-39`) — 75 buildings, 18 of
  them London. Fail-closed is the design; the count is never reduced to fit the grid.
- **`l_shape_decomposition` serialises `circulation: None` even when its wings carried circulation** —
  `keep_circulation_polygon=False` (`openubem/geometry/european_residential.py:977`), pinned by a unit
  test. The area is kept, the drawable ring is dropped. Currently costs nothing measurable (0 floors
  fleet-wide with area but no polygon) but it **will** un-draw the L-shape cores `EU-17` creates —
  revisit it there. *(FINDING 206 follow-up; STATE v4 §3 `FINDING 212`)*
- **`ruled_grid_1x1` carries no circulation** — one dwelling per floor takes the whole plate
  (`european_residential.py:873-887`); there is nothing to circulate between. 401 buildings fleet-wide.
- **A single-storey building carries no circulation** — ruled 2026-08-31 (`D-EU-49`). 46 buildings; the
  3 that currently carry a core lose it.
- **The S0 equivalent-envelope geometry warnings** (`Floor is upside down`, `zone is not fully enclosed`,
  `Entered Zone Floor Area(s) differ more than 5%`) are inherent to that method
  (`openubem/idf/european_box.py:48-58`) and, since the `InternalMass` repair, no longer produce
  non-determinism. *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. "European locations X-05")*
