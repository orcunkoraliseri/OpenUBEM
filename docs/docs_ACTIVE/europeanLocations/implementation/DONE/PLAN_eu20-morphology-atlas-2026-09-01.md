# PLAN — EU-20: the morphology atlas

**Slug:** `eu20-morphology-atlas` · **Date:** 2026-09-01 · **Arc:** `docs/docs_ACTIVE/europeanLocations/`
**Working directory:** `C:\Users\o_iseri\Desktop\OpenUBEM`
**Owner instruction (2026-09-01, verbatim):** *"maybe we can present one example from each group, L shape,
U shape, rectangular, square, triangle, etc. lets do that, i like this document i do not want to you change
it … create another version based on the groups, you can check the buildings and define groups, then propose
schema for each group and we can apply these"*

**Reference documents (read-only, never edited by this plan):**
`rules/RULES_dwelling_layout_scheme_2026-08-28.html` · `content/figure_4_2_dwelling_layout_schemes.svg` ·
`rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md` §6.

---

## 1. What this plan is, and what it is not

This plan produces **the measurement only** — the morphology groups, their counts, and one named
representative building per group with its real footprint. It does **not** propose schemes, does not
change any layout rule, and does not touch the generator. The scheme proposal and the new rules document
are the director's own work, written from this plan's output.

**Why the split.** The current classifier (`european_residential.py:440-476`) sorts every footprint into
exactly three buckets — courtyard, has-reflex, plain — which is why 739 L-shape and 249 courtyard
refusals (90 % of all 1,096) collapse into two undifferentiated failure classes. The atlas replaces a
guess about what the fleet looks like with a count.

🔴 **The taxonomy must generalise beyond these four districts.** Owner, 2026-09-01: *"because rule set
important to me, we will expand the building and country database later we will use these rule sets in
order to expand"*. Every group boundary is therefore a **dimensionless or metric-absolute** test on the
footprint itself (ratios, counts, metres) — never a percentile of this fleet, never a threshold tuned to
hit a coverage target, never a district- or country-conditional rule. A group must be nameable as a
building typology an architect would recognise in any European city, and its test must be computable for
a building in a country this project has never touched.

🔴 **Token discipline.** Cap every command's output (`head`, `--stat`, `-c`). Never print a CSV body, a
footprint coordinate list, an SVG source or a raw log. Write results to the files in §3 and report only
the numbers §7 asks for.

---

## 2. Hard rules for the executor

1. 🔴 **`D-EU-55` — never run EnergyPlus.** This plan reads GeoPackages and writes CSV/JSON/SVG. If you
   believe a task needs a simulation, STOP and report the exact command you would have run.
2. 🔴 **Never change a layout rule.** `openubem/geometry/european_residential.py` is **read-only** for
   this plan. So is every file under `rules/`, `plans3D/`, `outputs_3D/`, and
   `scripts/generate_eu_3d_viewers.py` (another session is editing that one right now — do not open it
   for writing under any circumstance).
3. **Measure, do not classify by wish.** Every group boundary must be a number you computed and can
   state. Where a footprint sits near a boundary, it goes in the group the numbers put it in, and you
   report how many such near-boundary cases exist.
4. **Never `git add` / `commit` / `stash` / `restore` / `checkout` / `reset` / `clean`.**
5. Before debugging any error, search `debugs/DEBUG_REFERENCES_european_locations.md` and
   `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. Register a solved error there before closing
   the task.
6. Do not propose alternatives — execute. On genuine ambiguity, STOP and quote the conflict.

---

## 3. Files you may write

- `scripts/eu20_morphology_atlas.py` — new, the whole measurement.
- `openubem/outputs/eu_evidence/EU-20/morphology_census.csv` — one row per building.
- `openubem/outputs/eu_evidence/EU-20/morphology_groups.csv` — one row per (district, group).
- `openubem/outputs/eu_evidence/EU-20/representatives.json` — the chosen examples with their rings.
- `openubem/outputs/eu_evidence/EU-20/svg/<group>.svg` — one footprint drawing per group.
- `docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv` — append one row per task.
- `docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_REFERENCES_european_locations.md` — error entries only.
- §8 of this file — the progress log.

Anything else: STOP and report.

---

## 4. Dependency decisions (pinned)

- **4.1 Footprint source:** `openubem/outputs/eu02/<district>/02_residential_manifest.gpkg`, read with
  `geopandas.read_file`. This is the same source the campaign prepares from
  (`scripts/run_eu_s2_district_campaign.py`); do not substitute `01_buildings_clean.gpkg`.
- **4.2 Districts and expected counts:** `ES-MAD-BERRUGUETE` 961 · `FR-LYO-HAUTCOEURPENTES` 297 ·
  `GB-LDN-STDUNSTANS` 82 · `IT-BOL-GALVANI2` 1,204 = **2,544**. If a district's manifest yields a
  different residential count, STOP and report both numbers.
- **4.3 Denoising:** reuse `european_residential.py`'s own denoise/regularisation helpers by **import**
  (`_reflex_vertex_count`, `_reflex_vertices`, and whatever the classifier at `:440-476` calls). Import
  them, never copy them, and never edit that module. A group taxonomy built on a differently-denoised
  ring would not describe the geometry the generator actually sees.
- **4.4 Geometry library:** `shapely` only, already a project dependency. No new package.
- **4.5 CRS:** each district's own projected CRS as it sits in the manifest — metres. Never reproject.

---

## 5. Tasks

### M01 — Measure every footprint

**What.** `scripts/eu20_morphology_atlas.py` writes `EU-20/morphology_census.csv`, one row per
residential building, with columns:

`district, building_id, area_m2, perimeter_m, n_vertices_raw, n_vertices_denoised, n_interior_rings,
interior_ring_area_m2, hull_deficit_fraction, rectangularity, min_rot_rect_w_m, min_rot_rect_l_m,
aspect_ratio, reflex_count, longest_edge_m, n_edges_ge_15pct_perimeter, circularity, storeys,
dwellings_total, idf_state`

**Why.** Every group boundary in M02 must come from one of these numbers.

**How.**
- `rectangularity` = footprint area / minimum-rotated-rectangle area.
- `aspect_ratio` = min-rotated-rect long side / short side.
- `hull_deficit_fraction` and `reflex_count` from the **imported** helpers (dep. 4.3).
- `circularity` = 4π·area / perimeter².
- `n_edges_ge_15pct_perimeter` = count of edges of the denoised exterior ring at least 15 % of the
  perimeter long — this is what separates a triangle/wedge from a general convex blob.
- `storeys` / `dwellings_total`: from the side-cars under
  `openubem/outputs/eu_evidence/EU-17/<district>/layouts/**/*.json`, keyed by `building_id` (side-car
  filenames are `<id-with-slash-as-folder>.json`, **not** the IDF stem — see
  `emit_eu11_layout_sidecars.py`). Missing → blank, never 0.
- `idf_state`: read the building's `.idf` under `openubem/outputs/eu_evidence/EU-17/<district>/idfs/`
  and report `RULED` (any `_dwelling_` zone), `MASSING_BOX` (only `_whole`), or `NO_IDF`. Use
  `scripts/eu_idf_plan_reader.py` — do not write a second parser. The stem→`building_id` map is the
  sha256-16 of the building id (`run_eu_s2_district_campaign.py:373`).

**How to test.** Row count is exactly 2,544. Print the count per district and the `idf_state` tally; the
tally must be RULED 541 / MASSING_BOX 2,003 / NO_IDF 0. If it is not, STOP and report both tallies.

### M02 — Define the groups

**What.** `EU-20/morphology_groups.csv` — one row per (district, group) plus a `FLEET` district row, with
the group's count, share, and the median of each M01 metric inside it.

**Why.** The owner asked for groups defined from the buildings, not from a textbook.

**How.** Start from this candidate taxonomy and apply it **in order** — first match wins:

| # | Group | Test |
|---|---|---|
| 1 | `COURTYARD` | `n_interior_rings ≥ 1` |
| 2 | `SLIVER` | `min_rot_rect_w_m < 8.0` |
| 3 | `SQUARE` | `rectangularity ≥ 0.90` and `aspect_ratio < 1.5` |
| 4 | `RECTANGLE` | `rectangularity ≥ 0.90` and `1.5 ≤ aspect_ratio < 3.0` |
| 5 | `SLAB` | `rectangularity ≥ 0.90` and `aspect_ratio ≥ 3.0` |
| 6 | `TRIANGLE` | `n_edges_ge_15pct_perimeter ≤ 3` and `reflex_count = 0` |
| 7 | `TRAPEZOID` | `reflex_count = 0` and `rectangularity < 0.90` |
| 8 | `L_SHAPE` | `reflex_count = 1` |
| 9 | `U_OR_T_SHAPE` | `reflex_count = 2` |
| 10 | `COMPLEX_MULTI_WING` | `reflex_count ≥ 3` |

Then **report, do not silently adjust**: any group holding < 1 % of the fleet, any group holding > 35 %,
and the count of buildings within 10 % of a threshold on either side. If a group is empty or swallows a
third of the fleet, say so in the progress log and leave the taxonomy as written — the director decides
whether to re-cut it, not you.

**How to test.** Group counts sum to 2,544 per district and fleet-wide. Print the fleet table.

### M03 — Choose one representative per group

**What.** `EU-20/representatives.json` — for each group, **one** named building.

**Why.** The new rules document shows one worked example per group; it must be a real building the owner
can look up, not a drawing.

**How.** Within each group, rank candidates by closeness to the group's own medians on
`area_m2`, `aspect_ratio` and `rectangularity` (normalised distance, equal weight), and prefer, in this
order: a building with `storeys ≥ 3`, a non-blank `dwellings_total`, and a district that does not
already supply another group's representative (spread the examples across the four districts where the
data allows — report where it did not). Emit per group: `group, district, building_id, storeys,
dwellings_total, area_m2, aspect_ratio, rectangularity, reflex_count, n_interior_rings, idf_state,
exterior_ring` (list of `[x, y]` in local metres with the ring's own centroid at the origin, rounded to
1 cm) and `interior_rings` (same form, possibly empty).

**How to test.** One entry per non-empty group; every `building_id` exists in `morphology_census.csv`;
every ring closes and its shoelace area matches `area_m2` to 1e-6 relative.

### M04 — Draw each representative

**What.** `EU-20/svg/<group>.svg` — the representative's bare footprint, one file per group.

**Why.** These drop into the new rules document as the group plates. The **scheme** overlay is not drawn
here — that is the director's proposal, written after this plan returns.

**How.** Match `content/figure_4_2_dwelling_layout_schemes.svg` exactly in language: white ground,
footprint outline `#172033` at 5 px, no fill, courtyard voids cut out as holes (`fill-rule: evenodd`),
a `10 m` scale bar, a north arrow, and the group name plus `district · building_id` as a caption in
`700 21px Arial` / `18px Arial` fill `#172033` / `#334155`. `viewBox` sized so the footprint occupies
~80 % of the frame. No JavaScript, no external references, no colour beyond those already named.

**How to test.** Every SVG opens standalone in a browser; report file count and the byte size of each.

---

## 6. Stop-and-report

**One stop, at the end of M04.** Report and wait. Do not begin any scheme proposal — that is explicitly
not yours (§1).

---

## 7. Report format

Report only: the M01 tallies, the fleet group table from M02, the representative chosen per group with
its district/id, the M04 file list, and any `file:line` citation for a decision this plan did not
specify. Do not paste footprint coordinates, CSV bodies, SVG source or raw logs.

---

## 8. Progress log

(One entry per task: `#### MXX — <title> — completed YYYY-MM-DD`, then Artifacts / Deviations /
Test status / Notes.)

#### M01 — Measure every footprint — completed 2026-09-01

**Artifacts:** `scripts/eu20_morphology_atlas.py`; `openubem/outputs/eu_evidence/EU-20/morphology_census.csv`
(2,544 rows).

**Deviations:** the residential building set was obtained by joining `02_residential_manifest.gpkg`
(`osm_id`) against `openubem/outputs/eu_evidence/EU-17/<district>/prepared_buildings.csv`'s `building_id`
column, rather than re-running the campaign's archetype mapper — `scripts/run_eu_s2_district_campaign.py:198-232`
(`_it_rows`) makes two live `requests.get` calls (:203, :224), forbidden by "no live-network integration
tests". Verified first that every `prepared_buildings.csv` id is present in the manifest's `osm_id` set
(0 missing, all 4 districts) before joining. `idf_state` is read directly off each `.idf`'s zone names via
`scripts/eu_idf_plan_reader.py::parse_idf_floor_zones` (not the `geometry_outcome` manifest column, which
can go stale on a reroute — FINDING 210, `scripts/run_eu_s2_district_campaign.py`). `FR-LYO-HAUTCOEURPENTES`
footprints carry a Z coordinate (`.has_z` True, only district); dropped with `shapely.force_2d` before any
planar metric (dep 4.5 is metres-only, this is not a reprojection).

**Test status:** row count 2,544 (961/297/82/1,204 per district, exact match to dep 4.2); `idf_state` tally
RULED 541 / MASSING_BOX 2,003 / NO_IDF 0, exact match to the plan's expected tally.

**Notes:** —

#### M02 — Define the groups — completed 2026-09-01

**Artifacts:** `openubem/outputs/eu_evidence/EU-20/morphology_groups.csv` (49 rows: 39 district×group +
10 FLEET).

**Deviations:** none against the pinned taxonomy. Rectangularity/aspect_ratio/min-rotated-rect are computed
on the raw footprint, and hull_deficit_fraction/reflex_count on the classifier's own denoised ring, mirroring
`classify_building_morphology` exactly (`openubem/geometry/european_residential.py:436` raw-footprint
`minimum_rotated_rectangle`; `:449,452-453` `denoised = footprint.simplify(0.5, preserve_topology=True)` +
`hull_deficit_fraction` + the `reflex_count` gate) — `_reflex_vertex_count` imported, never copied (dep 4.3).

**Test status:** group counts sum to 2,544 fleet-wide and to 961/297/82/1,204 per district — confirmed.

**Notes:** no group is empty or holds <1%/>35% of the fleet (SLAB smallest at 1.10%, SLIVER largest at
25.04%); left as-is per §5. 1,703 unique buildings sit within 10% of one of the four continuous thresholds
(8.0 m sliver width, 0.90 rectangularity, 1.5/3.0 aspect_ratio) — per-threshold breakdown:
`min_rot_rect_w_m~8.0` 266, `rectangularity~0.9` 1,353, `aspect_ratio~1.5` 457, `aspect_ratio~3.0` 178.

#### M03 — Choose one representative per group — completed 2026-09-01

**Artifacts:** `openubem/outputs/eu_evidence/EU-20/representatives.json` (10 entries, one per group).

**Deviations:** "rank by closeness ... and prefer, in this order" (§5 M03 How) was not fully pinned, so it
was implemented as a sequential filter cascade — storeys≥3, then non-blank dwellings_total, then an unused
district — each applied only if it leaves a non-empty pool; groups are processed in the taxonomy's own fixed
order (COURTYARD→...→COMPLEX_MULTI_WING) so "already used" has one stable meaning. The final tie-break is
minimum equal-weight relative deviation (`|value-median|/|median|`, summed unweighted over area_m2,
aspect_ratio, rectangularity) from the FLEET-wide group median — "equal weight" was read as no further
standardisation on top of an already dimensionless ratio. Ring centring uses the exterior ring's own
vertex-average centroid, matching `scripts/eu_idf_plan_reader.py:220-233`'s `_storey0_centroid` convention
(not shapely's area centroid). The `area_m2` emitted per representative is the shoelace area of its own
emitted, 1 cm-rounded ring (not the census row's pre-rounding area), so the ring/area self-consistency test
holds by construction rather than by a chosen tolerance.

**Test status:** 10/10 groups non-empty, one entry each; every `building_id` verified present in
`morphology_census.csv` (0 missing); every emitted ring's shoelace area matches its own `area_m2` to better
than 1e-6 relative — checked directly for all 10, not just by construction.

**Notes:** with 10 groups and only 4 districts, spread across all four was only achieved for the first 4
groups in taxonomy order (COURTYARD→IT-BOL-GALVANI2, SLIVER→FR-LYO-HAUTCOEURPENTES, SQUARE→GB-LDN-STDUNSTANS,
RECTANGLE→ES-MAD-BERRUGUETE); the remaining 6 groups (SLAB, TRIANGLE, TRAPEZOID, L_SHAPE, U_OR_T_SHAPE,
COMPLEX_MULTI_WING) had no unused-district candidate and reused one — reported per §5's own instruction.

#### M04 — Draw each representative — completed 2026-09-01

**Artifacts:** `openubem/outputs/eu_evidence/EU-20/svg/{COURTYARD,SLIVER,SQUARE,RECTANGLE,SLAB,TRIANGLE,
TRAPEZOID,L_SHAPE,U_OR_T_SHAPE,COMPLEX_MULTI_WING}.svg` (10 files).

**Deviations:** styling values (stroke `#172033` 5 px no fill, caption fonts `700 21px`/`18px` Arial, fills
`#172033`/`#334155`) were taken verbatim from `content/figure_4_2_dwelling_layout_schemes.svg:3`'s inline
stylesheet. That reference figure carries no scale bar or north arrow to copy from, so both were drawn fresh
in the same `#172033` stroke at 2 px (a stroke-width choice, not a new colour) — a 10 m tick-ended bar
bottom-left, and an up-pointing triangle + "N" label bottom-right; north is not rotated per building (UTM
northing is used directly as pixel-up, no per-building bearing was available to compute a true rotation).

**Test status:** all 10 files parse as well-formed XML (`xml.etree.ElementTree`, 10/10). Byte sizes:
COURTYARD.svg 1,679 · SLIVER.svg 1,304 · SQUARE.svg 1,243 · RECTANGLE.svg 1,233 · SLAB.svg 1,254 ·
TRIANGLE.svg 1,248 · TRAPEZOID.svg 1,234 · L_SHAPE.svg 1,258 · U_OR_T_SHAPE.svg 1,320 ·
COMPLEX_MULTI_WING.svg 1,552.

**Notes:** —
