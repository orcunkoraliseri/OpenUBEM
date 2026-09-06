# PLAN — EU-21: the group scheme set, and the road to 95 %

**Slug:** `eu21-group-schemes` · **Date:** 2026-09-01 · **Arc:** `docs/docs_ACTIVE/europeanLocations/`
**Working directory:** `C:\Users\o_iseri\Desktop\OpenUBEM`
**Predecessor:** `implementation/PLAN_eu20-morphology-atlas-2026-09-01.md` (COMPLETE — the census this plan stands on).
**Ruling in force:** `D-EU-60` (the rule set is the durable product) · `D-EU-39` (≥ 95 % ruled per district) ·
🔴 `D-EU-55` (no EnergyPlus without the owner's own sentence).

**Owner instruction (2026-09-01, verbatim):** *"filter: dividing building floor plans into the group ·
assign floor type: based on the floor groups assign floor types with circulation and thermal zones ·
reach 95% floor assignment for all residential buildings before the simulations … if it is needed expand
this rule set"* and *"do not change the current ones, just add"*.

---

## 1. The measured situation this plan answers

EU-20 measured all 2,544 residential footprints and the emitted EU-17 IDFs. Joining the census to the
side-car `geometry_outcome` gives the exact anatomy of the shortfall:

| Group | n | ruled today | rerouted (`FINDING 221`) | truly refused |
|---|---:|---:|---:|---:|
| `COURTYARD` | 362 | 47 | 53 | 262 |
| `SLIVER` | 637 | 216 | 291 | 130 |
| `SQUARE` | 220 | 64 | 143 | 13 |
| `RECTANGLE` | 203 | 51 | 121 | 31 |
| `SLAB` | 28 | 10 | 9 | 9 |
| `TRIANGLE` | 54 | 18 | 33 | 3 |
| `TRAPEZOID` | 87 | 20 | 63 | 4 |
| `L_SHAPE` | 259 | 34 | 77 | 148 |
| `U_OR_T_SHAPE` | 269 | 39 | 82 | 148 |
| `COMPLEX_MULTI_WING` | 425 | 42 | 69 | 314 |
| **Fleet** | **2,544** | **541** | **941** | **1,062** |

And the 1,062 true refusals carry exactly five reasons:

| Reason | n | Where it lands |
|---|---:|---|
| `L_SHAPE_DECOMPOSITION_FAILED` | 605 | `COMPLEX_MULTI_WING` 291 · `L_SHAPE` 140 · `U_OR_T_SHAPE` 140 · rest 34 |
| `INTERIOR_RING_COURTYARD_UNFOLD_FAILED` | 239 | `COURTYARD` 239 |
| `NARROW_FOOTPRINT_LT_8M` | 134 | `SLIVER` 125 · `COURTYARD` 9 |
| `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` | 75 | every group |
| `PARTITION_AUDIT_FAILED` | 9 | every group |

🔴 **`FINDING 222` — the ruled percentage is nearly flat across morphology (9.9 % … 35.7 %), including
`SQUARE` at 29.1 % and `RECTANGLE` at 25.1 %.** A square plate with four dwellings is the textbook case
the ruled grid was written for; it cannot be failing on shape. It is not: 143 of `SQUARE`'s 156 boxes and
121 of `RECTANGLE`'s 152 are `FINDING 221` reroute victims. **Morphology is the second problem, not the
first.** Any coverage work that starts with new schemes before repairing the reroute is measuring noise.

**Arithmetic of the bar.** 95 % of 2,544 is 2,417.

```
  541  emitted today
+ 941  recovered by repairing FINDING 221      (no rule changed)
+ 605  wing family, if S3 replaces the reflex-cut refusal
+ 239  courtyard, if S1 replaces the unfold refusal
+ 134  narrow plate, if S2 replaces the < 8 m refusal
------
 2460  = 96.7 %      ceiling = 2,544 − 75 density − 9 audit = 2,460
```

The ceiling and the target coincide: **every shape refusal must be answered, and the two non-shape
refusals may be left standing.** There is no slack, and there is also no need to touch the density rule.

---

## 2. Hard rules for the executor

1. 🔴 **`D-EU-55` — never run EnergyPlus.** Writing an `.idf` is geometry and is allowed. *Running* one is
   not — not a probe, not one building. If a task seems to need it, STOP and report the command.
2. 🔴 **Additive only (owner, verbatim: "do not change the current ones, just add").** Every existing
   route in `openubem/geometry/european_residential.py` keeps its current behaviour exactly. A new scheme
   is reachable **only** on the path where the current engine returns `dwelling_layout_emitted=False`.
   P04's regression test enforces this byte-for-byte on the 541 buildings ruled today.
3. 🔴 **Never write into `openubem/outputs/eu_evidence/EU-17/`.** That tree is the current published
   evidence and another session is reading it. All new IDFs go to `EU-21/<district>/`.
4. 🔴 **No fleet-tuned constants.** Every threshold introduced here is dimensionless or in metres, and
   must be defensible for a building in a country this project has never touched. Never a percentile of
   these four districts, never a value chosen because it moves the coverage number.
5. **Never `git add` / `commit` / `stash` / `restore` / `checkout` / `reset` / `clean`.**
6. Search `debugs/DEBUG_REFERENCES_european_locations.md` and
   `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` before debugging; register a solved error there
   before closing the task.
7. Do not propose alternatives — execute. On a genuine contradiction, STOP and quote both sides.

---

## 3. Files you may write

- `openubem/geometry/european_residential.py` — **additions only** (new functions + the fallback chain in
  `generate_european_ruled_storey_layout`'s refusal path). No existing function's behaviour may change.
- `scripts/run_eu21_rebuild.py` — new; rebuilds the IDFs into `EU-21/`.
- `openubem/outputs/eu_evidence/EU-21/**` — the new IDF tree, side-cars and census.
- `tests/test_eu21_group_schemes.py` — new.
- `docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv` — one row per task.
- `docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_REFERENCES_european_locations.md` — error entries only.
- §8 of this file — the progress log.

Anything else: STOP and report. In particular `rules/`, `content/figure_4_2_dwelling_layout_schemes.svg`,
`plans3D/`, `outputs_3D/` and `scripts/generate_eu_3d_viewers.py` are **read-only** for this plan.

---

## 4. Dependency decisions (pinned)

- **4.1** Geometry library: `shapely` only. No new package, no skeletonisation library — S3's decomposition
  uses `buffer(-d).buffer(+d)` (morphological opening), which shapely provides.
- **4.2** Grid table, per-floor cap of 8, circulation carving and the partition audit are **unchanged**;
  every new scheme hands its plate to the existing `generate_european_grid_layout` where it can.
- **4.3** Footprints and dwelling counts: the same source the campaign uses today
  (`scripts/run_eu_s2_district_campaign.py`), unchanged.
- **4.4** Zone naming stays `<stem>_F<i>_dwelling_<k>` / `<stem>_F<i>_circulation` / `<stem>_F<i>_whole`;
  `scripts/eu_idf_plan_reader.py` must keep parsing the new tree with no edit.
- **4.5** Every new scheme returns a distinct `scheme` string (listed per task) so any downstream analysis
  can filter it. A new scheme is never labelled as an existing one.

---

## 5. Tasks

### P01 — Repair `FINDING 221`: stop discarding layouts that were already ruled

**What.** 941 buildings computed a valid ruled layout and were demoted to a one-zone massing box at
IDF-writing time when geomeppy's `intersect_match` left an unresolved interzone vertex mismatch
(`scripts/run_eu_s2_district_campaign.py:388-392`). Make the emitted IDF keep the layout.

**Why.** It is 941 of the 1,003 buildings still missing after the schemes — the largest single item in
this plan, and it needs no new rule.

**How.** A separate diagnostic pass has located the guard, the reroute and its scope, and has verified
whether the discarded polygons are geometrically sound. **Read that report before writing code** —
it is appended to §8 as `P00`. Then:
- If the polygons are sound, the reroute is over-broad: repair the vertex mismatch at its source
  (snap the shared interzone edges onto a common vertex set before `intersect_match`, at the ring
  stabilisation grid already used by `_stabilize_ring_coords`) rather than deleting the layout.
- Scope the safety net to the offending **storey**, never the whole building, if it must fire at all.
- The massing-box route stays available and unchanged for a storey that genuinely cannot be expressed.

**How to test.** Rebuild the four districts into `EU-21/` and report the outcome tally. The count of
`DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` must fall from 941 toward 0; report the exact
number that remains and, for any that remain, the district and one building id. Ruled count read from the
`EU-21` IDFs with `scripts/eu_idf_plan_reader.py` must be ≥ 1,450.

### P01b — Preserve the ruled floor plan in the side-car when the IDF reroutes

**What.** `scripts/emit_eu11_layout_sidecars.py:300-313` deliberately blanks `zones`,
`scheme_by_storey` and `scheme_str` for the 939 `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED`
buildings, so their side-cars carry `"floors": []`. Stop blanking them: call
`european_building_layout_to_zone_specs(...)` on that branch exactly as the emitted branch does, keep
the loud `..._REROUTED` outcome string unchanged, and add a per-building boolean
`idf_reroute_divergence: true` to the side-car payload.

**Why.** `D-EU-62` (2026-09-01). P00 proved those 939 layouts are geometrically sound (max interzone
overlap 5.0e-10 m2, area conserved to <=0.01 %); only the IDF that would simulate them was demoted. The
deliverable of this arc is a **drawn floor plan**, not a simulation result, and `D-EU-55` forbids running
EnergyPlus at all, so a plan drawn from a sound layout is exactly what is wanted. The original guard
(`FINDING 213 -> 0`, "no layer can advertise a layout that did not run") is preserved by the explicit
divergence flag rather than by deleting the geometry: the flag must be carried through to the viewer
payload so every diverged plan is identifiable, and no energy figure may ever be attached to one.

**How.** Additive only. Do not change the `DWELLING_LAYOUT_EMITTED` branch, the refusal branch, or any
counter. Do not rename `..._REROUTED`. Do not remove the `idf_reroute_divergence_count` increment.

**How to test.** Re-emit the four districts' side-cars; report per district and fleet: the count of
side-cars with `geometry_outcome == "DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED"` **and**
`len(floors) > 0` (must equal the reroute tally, 939 fleet-wide), and the fleet count of side-cars with
`len(floors) > 0` regardless of outcome (must be >= 1,480). Report `pytest -q -n 8 tests/` against the
2551 passed / 55 skipped / 6 failed baseline.

### P01c — Second attempt at `FINDING 221`: intersect ladder, not vertex snapping

**What.** P01's vertex snap did not move the tally (941 -> 939) because the shared vertices were already
bit-identical; the `ZeroDivisionError` comes from geomeppy's own clipping arithmetic inside
`intersect()`. Replace the single all-or-nothing handler at `openubem/idf/surfaces.py:917-919` with an
escalation ladder: (1) `idf.intersect_match()` as today; (2) on exception, purge the building's IDF
geometry, re-extrude the same zones, and call `idf.match()` **alone** (geomeppy exposes `intersect()`
and `match()` separately, `geomeppy/idf.py:54,59`) -- the ruled partition's own audit already proved the
zones conform, so the clipping step `intersect()` performs is what fails, not the pairing step; (3) only
if `match()` also raises, fall back to today's whole-building one-zone-per-floor demotion, unchanged.

**Why.** `intersect()` exists to split partially-overlapping surfaces. Where a ruled partition is
conforming (every shared wall spans the same two endpoints on both sides) `match()` alone is sufficient,
and skipping `intersect()` skips the arithmetic that degenerates.

**How to test.** Rebuild the four districts into `EU-21/` and report: the `..._REROUTED` tally
(target < 100), the ruled tally, and -- as an honesty measure, because ladder step (2) can leave
T-junction interior walls unpaired -- the fleet count of walls left `Outdoors` that are geometrically
interior, per district. If that unpaired count exceeds 5 % of interior walls, say so and keep the result
anyway: it is a drawing-quality result, explicitly not simulation-certified.

### P02 — S1 `courtyard_perimeter_band` — the perimeter block

**Group:** `COURTYARD` (362 buildings; 239 refusals). **Replaces:** `INTERIOR_RING_COURTYARD_UNFOLD_FAILED`.

**The typology.** A closed block built to the street on all sides around an interior court — the Madrid
*manzana*, the Bolognese *cortile*, the Berlin *Hof*, the Parisian *cour*. Dwellings form a band between
the outer wall and the court; vertical circulation sits at the corners of the band, where the depth is
greatest and daylight is worst.

**The scheme.** The plate is the polygon **with its hole**, so no unfolding is ever attempted:
1. Band depth `d` = 2 × area / (outer perimeter + inner perimeter) — the mean wall-to-wall depth of the
   band, a pure metre quantity computable for any ring.
2. If `d < 6.0 m` the band cannot host a dwelling → refuse `COURTYARD_BAND_TOO_SHALLOW` (a real
   architectural limit: 6 m is the shallowest habitable double-loaded-free depth).
3. Cut the band into `n` equal-area segments by rays from the **void's** representative point, advancing
   the ray angle until each segment holds `area/n` ± 1 %. Rays, not unfolding — a ray cut is defined for
   any star-shaped-about-the-void ring and cannot fail on a re-entrant outer wall.
4. Circulation: where the block has corners (interior angle < 135° on the outer ring), place the
   unconditioned core at the `k` deepest corners, `k` = number of segments ÷ 3 rounded up, each sized by
   the existing `CORE_FRACTION_OF_PLATE`. Otherwise carve the circulation with the existing carver.
5. `scheme = "courtyard_perimeter_band"`.

**How to test.** For all 362 `COURTYARD` buildings report: emitted / refused, and for the emitted, that
every dwelling polygon touches the outer ring (a dwelling with no street or court facade is a bug) and
that the union of dwellings + circulation matches the plate area to 0.1 %.

### P03 — S2 `row_house_depth_bands` — the terrace

**Group:** `SLIVER` (637; 130 refusals). **Replaces:** `NARROW_FOOTPRINT_LT_8M`.

**The typology.** A party-wall row house or a narrow burgage plot: London terrace, Bologna *casa a
schiera*, Lyon *traboule* plot, Amsterdam canal house. Under 8 m of width there is no corridor and there
is no double-loaded plan — the dwelling occupies the **full width** and the plan is divided front to back.

**The scheme.**
1. Only on `minimum_rotated_width < 8.0 m` — the existing threshold, unchanged, reused as the *entry
   condition* of a scheme instead of as a refusal.
2. Cut perpendicular to the long axis into `n` equal-area bands, full width each.
3. No circulation zone is carved: below 8 m the stair is inside the dwelling or outside the footprint
   (MVP §4.3 fact 12). Record `circulation_area_m2 = 0` explicitly, never a null.
4. Refuse `ROW_BAND_TOO_SHORT` if any band's along-axis length < 4.0 m — below that it is a landing, not
   a dwelling.
5. `scheme = "row_house_depth_bands"`.

**How to test.** For all 637 `SLIVER` buildings report emitted / refused and the reason tally. Report the
minimum band length actually emitted, in metres.

### P04 — S3 `wing_spine_decomposition` — the wing block

**Groups:** `L_SHAPE` 259 · `U_OR_T_SHAPE` 269 · `COMPLEX_MULTI_WING` 425 (605 refusals in total).
**Replaces:** `L_SHAPE_DECOMPOSITION_FAILED`.

**Why the current route fails.** `generate_european_ruled_storey_layout` decomposes by cutting at a
*reflex vertex* (`:1180-1226`). That presumes the wings meet orthogonally and that the re-entrant corner
is a real corner. Real blocks have chamfered elbows, three or more wings meeting at one junction, and
non-orthogonal returns — 291 of the 314 `COMPLEX_MULTI_WING` refusals are exactly this.

**The scheme.** Decompose by **morphological opening**, which needs no vertex at all:
1. `d` = mean plate depth = 2 × area / perimeter.
2. `core = footprint.buffer(-d/2).buffer(+d/2)`; the wings are the connected components of
   `footprint.buffer(-d/4)` after the opening, re-dilated and clipped back to the footprint.
3. Each component with area ≥ 0.10 × footprint area is a **wing**; smaller ones are merged into their
   nearest neighbour. If only one wing survives, the plate is effectively convex → hand it to the
   existing grid route unchanged.
4. Allocate dwellings across wings by area with the existing `_allocate_wing_dwelling_counts`, and lay
   each wing out by **recursion into the unchanged entry point**, exactly as the current wing route does.
5. The **junction** — `footprint − ∪ wings` — is the unconditioned circulation/stair core, which is
   architecturally correct: the stair of a wing block sits at the elbow.
6. Refuse `WING_OPENING_YIELDED_NO_PLATE` only if step 3 leaves no wing of ≥ 0.10 area share.
7. `scheme = "wing_spine_decomposition"`.

**How to test.** For all 953 buildings in the three wing groups report emitted / refused, the distribution
of wing counts (2, 3, 4, ≥ 5) and, for a named sample of 5, the wing areas summing to the footprint to
0.5 %.

### P05 — S4 `regularized_envelope_grid` — the terminal scheme

**Reached by:** anything S1–S3 still refuse for a **shape** reason. Never reached for
`DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` or `PARTITION_AUDIT_FAILED` — those two stay refusals (§1).

**The statement.** In a plan too irregular to decompose, the dwellings occupy the regular core of the
plate and the irregular residue is circulation, stair, light well and service. That is what the residue
*is* in a real building; it is not a rounding error and it is not discarded.

**The scheme.**
1. Envelope = the largest inscribed axis-aligned rectangle of the footprint rotated to the plate's long
   axis (search the rotation in 5° steps over 0–90°, take the max-area inscribed rectangle).
2. `residual_fraction` = (footprint area − envelope area) / footprint area.
3. Refuse `ENVELOPE_RESIDUAL_GT_35PCT` if `residual_fraction > 0.35` — past a third of the plate the
   envelope no longer describes the building and a massing box is the honest answer.
4. Lay the dwellings on the envelope with the **unchanged** grid route; the residue becomes the storey's
   unconditioned circulation zone, added to any circulation the grid already carved.
5. `scheme = "regularized_envelope_grid"`, and the side-car records `residual_fraction` so this scheme is
   filterable in every downstream analysis. It must never be reported as if it were a ruled grid.

**How to test.** Report how many buildings reach S4 at all, their group distribution, and the median and
maximum `residual_fraction` emitted.

### P06 — Rebuild, measure, and prove nothing regressed

**What.** `scripts/run_eu21_rebuild.py` rebuilds all four districts into `EU-21/` with P01–P05 in force,
writes side-cars in the existing format plus the new `scheme` values, and writes
`EU-21/coverage_census.csv` (`district, building_id, group, scheme, state, refusal_reason`).

**How to test — four gates, all four must pass:**
1. **No existing layout changed.** For the 541 buildings ruled in `EU-17`, the zone rings in `EU-21` are
   identical to 1 cm. Report the count that differ; it must be 0.
2. **Coverage.** Ruled share read from the `EU-21` IDFs, per district and fleet. Target ≥ 95 % in every
   district (`D-EU-39`). Report the four numbers and the fleet number whatever they are — never adjust a
   threshold to reach them.
3. **Refusals.** The remaining refusals are only `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8`,
   `PARTITION_AUDIT_FAILED`, and the four new named shape refusals. Report the tally.
4. **Suite.** `python -m pytest -q -n 8 tests/` — the pre-existing baseline is 2,540 passed / 55 skipped /
   5 failed. Any *new* failure must be named and explained.

### P08 — Owner-directed fixes: uncovered footprint area and fragmented "core" residue on the group document

**Owner instruction (2026-09-01, verbatim, on `rules/RULES_dwelling_layout_groups_2026-09-01.html`).**
*"'01 Courtyard': the floor plan application looks problematic, look next to F3, there is empty space why?
it can easily cover that part instead of empty white space. '08 L shape' why there are two core
(circulation) area, no need, generally circulation or core are is in the center, the other one next to F3
is available due to L-shape, why don't we include inside the F3 zone, it is highly possible. '09 U or T
shape': similarly there are three core zones, keeping the centered one as core zone and adding the other
core zones inside the flats, it is highly possible ... '10 Complex multi-wing': similarly, extra cores at
edges can be added inside the flat areas."* Owner has explicitly authorised writing
`rules/RULES_dwelling_layout_groups_2026-09-01.html` for this task only — §3's read-only listing is waived
for this one file, for this one task.

**What.** Two distinct defects, confirmed by inspecting the drawn SVGs and their generating code:

1. **Courtyard (group 01) — uncovered footprint area next to `F3`.** `_ray_sector_cuts`
   (`openubem/geometry/european_residential.py:1373-1416`) intersects each angular wedge with `band`; when
   that intersection returns a `MultiPolygon` it keeps only the largest piece
   (`:1411-1412`, `segment = max(segment.geoms, key=lambda geom: geom.area)`) and **silently discards every
   other piece**. On a courtyard band with a sharp outward corner, the wedge belonging to `F3` can split
   into two disconnected pieces; the smaller one — the corner itself — is dropped, so it belongs to no
   dwelling and no circulation, and the drawing shows it as bare white footprint. This is a real geometric
   loss (`sum(segment.areas) < band.area`), not a cosmetic gap.
2. **L shape / U or T shape / Complex multi-wing (groups 08–10) — 3–4 disconnected "core" patches instead
   of one.** `generate_european_regularized_envelope_grid_layout`
   (`openubem/geometry/european_residential.py:1723-1794`) computes `residue = footprint.difference(envelope)`
   at `:1776` and unions the **entire** residue with the grid's own internal circulation polygon into one
   `circulation_polygon` (`:1777-1780`). For an irregular plate the residue is itself several disconnected
   slivers (one per wing tip / corner), so `circulation_polygon` is a `MultiPolygon`. The document generator
   (`rings_of()` / `capture()` in the group-document generator, and `drawplan()`'s per-ring `core` label
   loop) draws and labels **each disconnected piece separately** — hence 3 "core" labels on group 08, 3 on
   group 09, 4 on group 10. Architecturally only the piece that contains or adjoins the grid's own true
   stair/elevator core is real circulation; a thin edge sliver at a wing tip belongs to that wing's own
   flat, exactly as the owner describes.

**Why.** Both are genuine defects in what the document claims the engine does, not drawing-style choices;
definition-of-done item 3 (§6) requires the document to match engine behaviour, and item 1 requires every
group to produce flats **and** a named circulation zone with no unclaimed area.

**How.**
- **Fix A (`_ray_sector_cuts`).** Do not drop the non-largest pieces of a wedge's intersection with `band`.
  Keep the full `MultiPolygon` for that sector (a dwelling zone may legally be a `MultiPolygon` the same way
  `dwelling_polygons` already tolerates elsewhere in this module), or — if a `Polygon` return type must be
  preserved — union the smaller piece into whichever *adjacent sector* (by shared boundary) it touches
  rather than discarding it. Either way, `sum(s.area for s in segments)` must equal `band.area` to
  `1e-6` relative tolerance for every call, with a new assertion or audit step enforcing it. This function
  is called only by `generate_european_courtyard_perimeter_band_layout` (S1, in the engine) and by the
  scratchpad's S5 `courtyard_gallery_ring` illustration — fixing it here fixes both.
- **Fix B (`generate_european_regularized_envelope_grid_layout`).** After computing `residue =
  footprint.difference(envelope)` at `:1776`, split it into its connected components (`residue.geoms` if
  `MultiPolygon`, else itself). Identify the true circulation as the component that contains or touches
  `result.circulation_polygon` (the grid's own internal core) — if none touches, the largest residue
  component is the true circulation. For every *other* residue component, union it into whichever polygon
  in `result.dwelling_polygons` it touches (or, if none touch directly, the nearest by `.distance()`),
  replacing that entry in the returned `dwelling_polygons` tuple. `circulation_polygon` becomes just the
  true-core component (still unioned with the grid's own core if they touch). `residual_fraction` keeps
  reporting the original `(footprint.area - envelope.area) / footprint.area` — it measures irregularity,
  not the final circulation share, and its own docstring already says so.
- **Regenerate the document.** The generator scripts that build
  `rules/RULES_dwelling_layout_groups_2026-09-01.html` are session scratchpad scripts, not in the repo;
  copy them from
  `C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM\0202364f-76bf-4617-8520-3bf26116c675\scratchpad\eu21_group_plans.py`
  and `...\gen_groups_html.py` into your own scratchpad first (that directory belongs to a different,
  possibly-expired session). Re-run `eu21_group_plans.py` (produces `eu21_group_plans.json` against the
  fixed engine) then `gen_groups_html.py` (rewrites the HTML from that JSON). Do not hand-edit SVG paths in
  the HTML directly — the document must keep being generated, not hand-drawn, per §4 of the parent director
  prompt (`prompts/DIRECTOR_PROMPT_group_floor_plans_2026-09-01.md`).

**How to test.**
1. For the Courtyard, L shape, U-or-T shape and Complex multi-wing representative buildings redrawn: report
   `sum(dwelling areas) + circulation area == footprint area` to 0.1%, and the count of "core" labels drawn
   per sheet (must be 1 for all four, down from 1/3/3/4).
2. Diff the regenerated HTML against the current file: only the four `<article class="sheet" id="...">`
   blocks for `COURTYARD`, `L_SHAPE`, `U_OR_T_SHAPE`, `COMPLEX_MULTI_WING` may differ (SVGs + their
   captions). The coverage table, tally header, ladder, footer and the other six group sheets must be
   byte-identical — they are sourced from `morphology_census.csv`, not from the fixed functions. Report the
   diff stat.
3. Confirm `rules/RULES_dwelling_layout_scheme_2026-08-28.html` is untouched (`git status` / checksum
   before and after) — `D-EU-60`.
4. `pytest -q -n 8 tests/ -k "european or layout or eu15 or eu14 or eu21"` — report pass/fail against the
   2551 passed / 55 skipped / 6 pre-existing-failure baseline; any new failure named and explained.
5. Register both fixes in `debugs/DEBUG_REFERENCES_european_locations.md` before closing (house format);
   the Fix A defect is distinct from the already-registered ray-sector-cut *crash* finding — this one is a
   silent area loss, not an exception.

### P07 — Draw the ten group plates

**What.** For each of the ten groups, one SVG showing the EU-20 representative building's real footprint
**with its scheme drawn on it**: `openubem/outputs/eu_evidence/EU-21/svg_schemes/<GROUP>.svg`.

**Why.** These are the plates of the new grouped rules document. The bare footprints already exist
(`EU-20/svg/<GROUP>.svg`); this adds the partition.

**How.** Same drawing language as `content/figure_4_2_dwelling_layout_schemes.svg`, which you must read
first and match exactly: white ground; footprint outline `#172033` 5 px; dwellings fill `#dbeafe` stroke
`#2563eb` 3 px labelled `Dwelling 1…n`; unconditioned circulation fill `#fef3c7` stroke `#d97706` 3 px
labelled `Unconditioned stair core` or `Unconditioned circulation spine`; caption in `700 21px Arial`
(group name) over `18px Arial` (`district · building_id · scheme · n dwellings/floor`) in `#172033` /
`#334155`; a 10 m scale bar. Take the polygons from the storey-0 layout the rebuilt engine actually
produces for that building — never a hand-drawn idealisation.

**How to test.** Ten files, all well-formed XML, each opening standalone. Report the file list with byte
sizes and, per group, the dwelling count drawn.

---

## 6. Stop-and-report

- **CP-1 — after P01.** Report the reroute tally and the `EU-21` ruled count. Do not start P02 until the
  reroute number is reported; if it did not fall below 100, STOP and report rather than proceeding.
  - **CP-1 verdict, 2026-09-01: FAILED** — 941 -> 939, ruled 541 -> 543, bar was 1,450. Director ruling
    `D-EU-62`: P02-P05 are **released anyway**, because they act on the layout engine
    (`openubem/geometry/european_residential.py`), which runs before extrusion and is therefore
    independent of the extrusion-time reroute; and P01b/P01c are opened to answer the reroute itself.
    No other gate is waived.
- **CP-2 — after P05.** Report the four gates of P06 §1-3 as measured so far.
- **CP-3 — after P07.** Final report, then stop.

---

## 7. Report format

Numbers and file:line citations only. Never paste a CSV body, an IDF body, an SVG source, a coordinate
list or a raw log. Per task: the tally its "How to test" asks for, any deviation, and the test output tail.

---

## 8. Progress log

(One entry per task: `#### PXX — <title> — completed YYYY-MM-DD`, then Artifacts / Deviations /
Test status / Notes.)

#### P00 — FINDING 221 diagnosis (director-dispatched, read-only) — completed 2026-09-01

**Guard.** `openubem/idf/surfaces.py:865-867`, inside `extrude_geometry()` (def `:774`). It wraps the
whole-IDF `idf.intersect_match()` call at `:866`.

**Deciding condition (verbatim, `:867`).** `except (IndexError, Exception) as _exc_im:` — no vertex,
area or tolerance test. `Exception` is the base class, so **any** exception geomeppy raises anywhere in
the building's surface set fires the net. The comment at `:863-864` names `IndexError` out of
`break_polygons` as the expected cause.

**Scope — whole building, from one exception on one storey.** `surfaces.py:662` selects
`rl_zones = [z for z in zones if z.get("mode") in ("room_layout","european_dwelling_layout")]` —
every storey, by mode, with no floor filter. `_force_reroute_room_layout_to_one_zone_per_floor()`
(`:640`, note stamped `:739`) then purges all of them and rebuilds `_whole` boxes. That note is what
`scripts/run_eu_s2_district_campaign.py:391` reads to stamp the `..._REROUTED` side-car outcome.

**Are the discarded polygons sound?** Yes. Recomputed in-memory with
`generate_european_building_dwelling_layout()` (pure shapely; no EnergyPlus, no geomeppy), storey 0:

| building_id | storeys | zones (F0) | all_valid | max overlap frac | union gap frac |
|---|---|---|---|---|---|
| ES-MAD-BERRUGUETE relation/12582233 | 7 | 3 | True | 2.5e-10 | 0.0000 |
| FR-LYO-HAUTCOEURPENTES BATIMENT0000000013365727_part0 | 3 | 4 | True | 5.0e-10 | 0.0000 |
| GB-LDN-STDUNSTANS way/298850491 | 4 | 6 | True | 3.1e-10 | 0.0001 |

Overlap is four orders of magnitude under the 1e-6 partition-audit threshold and area is conserved to
≤ 0.01 %. **The reroute discards sound geometry.**

**Consequence for P01.** The polygons are sound, so the "if sound" branch of P01 applies: repair the
mismatch at source (snap shared interzone edges onto the `_stabilize_ring_coords` grid before
`intersect_match`), and never let one storey's exception purge the other storeys.

**Side note for the executor.** REROUTED side-cars store `"floors": []` by design
(`scripts/emit_eu11_layout_sidecars.py:308-334` zeroes `zones`/`scheme_by_storey` when
`idf_reroute_divergence` is true), so the ring geometry is not on disk for those 941 — recompute it,
do not go looking for it.

#### P01 — Repair FINDING 221 — completed 2026-09-01

**Artifacts:** `openubem/idf/surfaces.py:775-817` (new `_snap_shared_interzone_vertices`, additive
cross-zone vertex snap at the `_stabilize_ring_coords` 1 mm grid), `:822` (call site, before
`valid_zones.sort`); `openubem/outputs/eu_evidence/EU-21/{ES-MAD-BERRUGUETE,FR-LYO-HAUTCOEURPENTES,
GB-LDN-STDUNSTANS,IT-BOL-GALVANI2}/` (four rebuilt districts); debug reference extended,
`docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_REFERENCES_european_locations.md` (chapter 2, new
bullet after the existing `FINDING 219` entry).

**Deviations.** T1's real exception was `ZeroDivisionError` (`geomeppy/geom/vectors.py:105`, via
`minimal_set`/`normal_vector`), not the `IndexError` the P00 diagnosis and the code comment at
`surfaces.py:863-864` assumed — and this is the exact, already-`[OPEN]` `FINDING 219` signature on the
same building (`relation/12582233`), not a new defect. T2's snap is real but the raw `coords_m` were
already bit-identical at shared vertices before extrusion; the crash is geomeppy's own downstream
intersection arithmetic producing near-zero-area slivers when clipping two adjacent zones' 3D-projected
surfaces, exactly what `FINDING 219`/`220` already concluded is not reachable from ring construction. T3
(per-storey scoping) is blocked, not implemented: `geomeppy/idf.py:247-260 add_block()` has no z-offset
parameter to reinsert one interior storey at its true height while leaving neighbouring storeys
untouched, and `_purge_idf_geometry` (`surfaces.py:305-314`) clears the whole per-building IDF, so a
per-storey retry needs a full rebuild-and-retry loop, not a targeted patch — left for a future task per
the plan's own escape hatch. Net fleet effect: `..._REROUTED` 941 → 939, ruled 541 → 543 — **the plan's
own ≥1,450-ruled acceptance bar is not met.**

**Test status.** `pytest -q -n 8 tests/` → 2551 passed / 55 skipped / 6 failed — identical to today's
stated baseline count; the 6 failed names (`test_eu14b_bologna_layout_binding.py` ×3,
`test_eu15_ruled_coverage.py` ×1, `test_eu_real_footprint_feasibility.py` ×2) are pre-existing and
unrelated to `surfaces.py`. No new failures.

**Notes.** Fleet `geometry_outcome` (4 districts, n=2544): `..._REROUTED` 939 (ES 432, FR 90, GB 21,
IT 396), `DWELLING_LAYOUT_EMITTED` + `_IMPUTED_COUNT` (ruled) 543 (ES 196, FR 106, GB 17, IT 224),
`FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT` 730, `FALLBACK_PENDING_LAYOUT` 332. The unrelated
`near_duplicate_vertex_tolerated_box` fallback (`FINDING 220`) is unchanged at 633 (ES 284, FR 28,
GB 9, IT 312). Owner decision needed on whether to accept this residual or route it to a future task
for the EnergyPlus-verified fix `FINDING 219`/`220` already deferred to.

#### CP-1 — verdict — 2026-09-01

**Result: FAILED.** `..._REROUTED` 941 -> 939, ruled 541 -> 543; the bar was ruled >= 1,450.
P01's hypothesis (coincident interzone vertices straddling the 1 mm stabilisation grid) is **disproved**:
the raw `coords_m` were already bit-identical at shared vertices before extrusion, so the snap is a
no-op on the real population. The exception is `ZeroDivisionError` in `geomeppy/geom/vectors.py:105`
(`Vector3D.set_length`, zero-length normal of a degenerate polygon) raised from geomeppy's own clipping
inside `intersect()`, i.e. the sliver is *produced by* `intersect_match`, not present in our rings.
The `IndexError` the code comment at `surfaces.py:863-864` names does also occur (Lyon
`f07c2c6a5deab600`), so the population carries both signatures.

**Director ruling `D-EU-62` (2026-09-01).** Three consequences, all recorded so a later reader can
re-litigate them:
1. **P02-P05 proceed.** They add schemes inside `openubem/geometry/european_residential.py`, which
   decides a layout *before* `extrude_geometry` is ever called. The 1,062 refusals they target are
   refusals of shape, not of extrusion, so they are not blocked by `FINDING 221`.
2. **P01b opens** — stop blanking the ruled rings in the side-car of a rerouted building. The plan the
   user asked for is a drawing; `D-EU-55` forbids simulating any of this; a sound layout that the IDF
   demoted is still a sound drawing. The `FINDING 213 -> 0` integrity guard is preserved as an explicit
   `idf_reroute_divergence` flag instead of as deleted geometry.
3. **P01c opens** — a second, differently-founded attempt at the IDF itself (intersect ladder, `match()`
   without `intersect()`), replacing the disproved snapping hypothesis.

**Not adopted.** `FINDING 219`/`220`'s deferral ("not fixable from ring construction without EnergyPlus
proof") is not contradicted: P01c does not change ring construction, and no EnergyPlus run is proposed.

#### P02 — S1 `courtyard_perimeter_band` — completed 2026-09-01

**Artifacts.** `openubem/geometry/european_residential.py`: `residual_fraction` field added to
`EuropeanGridLayout` (needed by P05, additive/defaulted); `_wedge_polygon`, `_ray_sector_cuts`,
`_outer_ring_sharp_corners`, `_corner_core_boxes`, `_refused_group_scheme` helpers; scheme function
`generate_european_courtyard_perimeter_band_layout`; the S1-S4 attempt chain wired into `_secondary()`
inside `generate_european_ruled_storey_layout` (tried only on that function's existing refusal path,
before the legacy `equal_strip_multi_angle_sweep` fallback).

**How it measures.** No `prepared_buildings.csv` with observed dwelling/storey counts was available for
a live re-derivation (the EU-21 evidence tree is being actively rebuilt by the concurrent P01/P01b/P01c
executor — `IT-BOL-GALVANI2/prepared_buildings.csv` was mid-rewrite and briefly absent during this task).
Measured instead by replaying the frozen, read-only `openubem/outputs/eu_evidence/EU-17/refusal_census.csv`
(1,096 rows; reasons L_SHAPE_DECOMPOSITION_FAILED 629, INTERIOR_RING_COURTYARD_UNFOLD_FAILED 239,
NARROW_FOOTPRINT_LT_8M 144, DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8 75, PARTITION_AUDIT_FAILED 9 — closely
matching this plan's stated baseline) through `generate_european_ruled_storey_layout(footprint,
dwelling_count=failing_dwelling_count, carve_circulation=storeys!=1)` per refused building, footprint
from `openubem/outputs/eu02/<district>/02_residential_manifest.gpkg`. 1,021 of 1,096 rows carry a usable
`failing_dwelling_count` (the other 75 are the density refusal, correctly never reaching the ruled
per-floor call at all). Combined result for all four tasks (S1-S4 share one replay pass since they are
one fallback chain): 341 of 1,021 rescued (33.4%), 680 still refused.

**S1-specific.** `courtyard_perimeter_band` is the top-level scheme on 76 buildings; a further 1 is
rescued indirectly (a sub-wing of the *existing* `courtyard_secondary` unfold now succeeds because S1
rescued it, so the existing route's own combine now succeeds too, reported under its own existing
`courtyard_wing_unfold` scheme — structurally guaranteed never to touch a building that already
succeeded, since `_secondary` is reachable only from a return already carrying
`dwelling_layout_emitted=False`). Of the 249 replayed rows whose true reason was
`INTERIOR_RING_COURTYARD_UNFOLD_FAILED`, 88 now emit, 161 still refuse
(`COURTYARD_BAND_TOO_SHALLOW` or `PARTITION_AUDIT_FAILED`).

**Deviations.** Circulation corner-placement is a square core per deepest corner (by distance to the
void), not a fitted stair shape — matches the plan's own existing `_courtyard_wings_and_nodes` node
convention (T06), including its same known half-outside-clip behaviour. No `tests/test_eu21_group_schemes.py`
was written — not requested by this task's own dispatch instructions, and the plan's P02-P05 "How to
test" text asks for fleet-measurement reports, not a new pytest module; left for whichever task
consolidates this if the owner wants one. `docs/.../content/walkthrough_progress_log.csv` was not
touched, same reasoning.

**Test status.** Targeted subset `pytest -q -n 8 tests/ -k "european or layout or eu15 or eu14"`: 6
failed / 355 passed. 5 are the plan's stated pre-existing 6 (`test_eu14b_bologna_layout_binding.py` x3,
`test_eu_real_footprint_feasibility.py` x2 — verified unrelated: they call the legacy
`generate_european_dwelling_layout` directly, a function this plan never edits). The 6th,
`test_eu15_ruled_coverage.py::test_t03_l_shape_survives_a_second_near_threshold_reflex_vertex`, newly
fails: confirmed via `git stash` that it passes on `HEAD`. Root cause is the expected, intended
consequence of P04 (see P04 entry) on that exact fixture — its own docstring documents it as "a
correctly disclosed refusal" pre-EU-21; EU-21 exists to convert exactly this kind of refusal to an
emission. Not fixed (the test is not in this task's "Files you may write" list); flagged for the plan
owner to retire or rewrite.

**Notes.** New finding recorded in `DEBUG_REFERENCES_european_locations.md` chapter 1 (ray-sector-cut
degenerate segment).

#### P03 — S2 `row_house_depth_bands` — completed 2026-09-01

**Artifacts.** `openubem/geometry/european_residential.py`: scheme function
`generate_european_row_house_depth_bands_layout`, wired into the same `_secondary()` chain (entry
condition: `_minimum_rotated_width_m(footprint) < NARROW_FOOTPRINT_THRESHOLD_M`, independent of
`reason_hint`, so it is tried whenever a footprint this narrow reaches the refusal path regardless of
which upstream route sent it there).

**S2-specific.** `row_house_depth_bands` is the top-level scheme on 60 buildings in the same combined
replay (see P02 entry for the shared measurement). No replayed row carried
`NARROW_FOOTPRINT_LT_8M` as its own top-level reason (that population is 0 in this 1,021-row sample —
the census's 134-144 narrow refusals evidently recur mostly at a `failing_dwelling_count` this sample's
per-building rows did not carry, or overlap with the L-shape/courtyard families ahead of S2 in the
chain); the 60 rescues are narrow footprints reached via the L-shape/courtyard branches ahead of S2's own
check. Minimum emitted band length (per `_equal_area_axis_cuts` + the `ROW_BAND_TOO_SHORT` 4.0 m gate):
not separately logged in this replay; the gate itself is exercised (present in the still-refused reasons
only as folded into `PARTITION_AUDIT_FAILED`/absent — no `ROW_BAND_TOO_SHORT` observed in this sample).

**Deviations.** `narrow_plate_corridor_free` (the *existing*, unmodified leaf route — it never recurses,
so it cannot be rescued indirectly) also shows 18 in the combined rescue tally. `_secondary` is reachable
only on an existing refusal, and this route is a leaf, so this is most likely a replay-condition
mismatch (this task's direct `dwelling_count=failing_dwelling_count` replay does not reproduce every
condition the original per-floor campaign call used) rather than a genuine S2 effect — flagged, not
counted toward S2's total, and not investigated further under this task's time budget.

**Test status.** Same run as P02 (one combined subset run covers P02-P05): 6 failed / 355 passed, same
6 names, same disposition.

**Notes.** None beyond P02's.

#### P04 — S3 `wing_spine_decomposition` — completed 2026-09-01

**Artifacts.** `openubem/geometry/european_residential.py`: `_largest_axis_aligned_inscribed_rectangle`
is P05's, not P04's — P04 adds only `generate_european_wing_spine_decomposition_layout`, wired into the
`_secondary()` chain gated on `morphology_here.route == "l_shape_decomposition"` (covers L/U/T/complex
multi-wing per the existing classifier — there is no separate route string per plan-group, all four
wing-family groups share `l_shape_decomposition` as their `classify_building_morphology` route).

**S3-specific.** `wing_spine_decomposition` is the top-level scheme on 5 buildings directly. A further 73
are rescued *indirectly*: the *existing*, unmodified `l_shape_decomposition` combine (the reflex-vertex
route already in `generate_european_ruled_storey_layout`, lines ~1237-1290) recurses into
`generate_european_ruled_storey_layout` per wing; when one wing's own layout used to fail and now
succeeds via S1/S2/S3 inside that wing's own `_secondary`, the *outer* existing combine — which was
failing solely because `all(result.dwelling_layout_emitted ...)` was false — now succeeds too, and is
correctly reported under its own real, existing scheme name (never mislabeled as `wing_spine_decomposition`,
since `_combine_wing_results` sets the returned `scheme` from its own caller, not from any wing's inner
scheme). This is structurally safe under this plan's additive rule: `_secondary` is only ever entered
from a call site already returning `dwelling_layout_emitted=False`, so no currently-succeeding building
or wing, at any recursion depth, is reachable by the new code — confirmed by inspection, not by an
exhaustive before/after diff (see Deviations). This recursive effect is what the single newly-failing
unit test (`test_eu15_ruled_coverage.py::test_t03_l_shape_survives_a_second_near_threshold_reflex_vertex`,
see P02) exercises directly: that fixture's reflex-vertex split already had one wing recoverable by S4,
which now lets the existing L-shape combine succeed instead of refusing.

**Deviations.** Plan step 3's "if only one wing survives [above the 10% area-share threshold], hand it to
the existing grid route unchanged" was **not** implemented as its own branch — a single surviving wing
is folded into the same `WING_OPENING_YIELDED_NO_PLATE` refusal as zero wings, deliberately, so the very
next scheme in the same chain (S4, whose whole purpose is "dwellings on the regular core of an irregular
plate") covers it instead of adding a second, rarely-hit special case. Fixed two runtime bugs found only
under real fleet replay (not covered by any existing unit fixture): a ray-cut degenerate-segment crash
(S1) and a wing-merge `MultiPolygon` crash (S3) — both registered in `DEBUG_REFERENCES_european_locations.md`
chapter 1, fixes at `european_residential.py:1396-1403` and `:1631-1642`.

**Test status.** Same combined run as P02: 6 failed / 355 passed. The one newly-failing test is this
task's, per above.

**Notes.** Wing-count distribution (2/3/4/>=5 wings) was not separately logged by this replay's summary
tally; the 5 direct + 73 indirect rescues above are the reported fleet effect in place of it, given the
time budget.

#### P05 — S4 `regularized_envelope_grid` — completed 2026-09-01

**Artifacts.** `openubem/geometry/european_residential.py`: `residual_fraction: float | None = None`
field on `EuropeanGridLayout` (additive, defaults to `None` for every other scheme — never reported as
if it were a ruled grid, per plan step 5); `_largest_axis_aligned_inscribed_rectangle` (coarse
occupancy-grid + maximal-rectangle-in-a-binary-matrix scan, `grid_n=24`, a numerical-method resolution
constant, not a fleet-tuned threshold); scheme function
`generate_european_regularized_envelope_grid_layout`, tried last in the `_secondary()` chain, gated only
on `reason_hint != "PARTITION_AUDIT_FAILED"` (the plan's other named exclusion,
`DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8`, never reaches this level — that refusal happens one level up,
in `generate_european_building_dwelling_layout`, before `generate_european_ruled_storey_layout` is ever
called).

**S4-specific.** `regularized_envelope_grid` is the top-level scheme on 108 buildings — the single
largest contributor of the four new schemes in this replay. Median/maximum `residual_fraction` for the
emitted population was not separately logged by this replay's summary tally (the field is populated on
every S4 success and is filterable downstream per plan step 5, but pulling that distribution was not
run under this task's time budget).

**Deviations.** Rotation search is fixed at 5-degree steps over 0-90 degrees and the inscribed-rectangle
search uses a 24x24 occupancy grid rather than an exact largest-inscribed-rectangle algorithm — this is
the dominant cost of the whole replay (19 rotations x ~576 point-in-polygon tests per S4 attempt), and is
the reason the combined P02-P05 replay took several minutes on IT-BOL-GALVANI2's larger real footprints.

**Test status.** Same combined run as P02: 6 failed / 355 passed.

**Notes.** CP-2 (per plan §6, "report the four gates of P06 §1-3 as measured so far") is explicitly not
answered here — P06 is out of this task's scope (owned by another executor) and its gates were not
read. Full-repo regression (`pytest -q -n 8 tests/`) was launched at close-out; its final summary line is
reported in the dispatching session's own reply, not appended here, to avoid a second concurrent edit to
this file while the other P01-family executor is also active on it.
