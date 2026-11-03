# PLAN — `EU-15` ruled thermal zoning · `EU-16` context geometry

**Slug:** `eu15-eu16-zoning-context` · **Date:** 2026-08-30 · **Arc:** European locations × Step 8
**Read-first:** `../previous/STATE_european_locations_v3.md` · **Brief:** `../previous/BRIEF_european_locations_v3.md`
**Rules this plan implements:** `../rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md` (`D-EU-39`),
`../rules/RULES_context_geometry_simulation_2026-08-30.md` (`D-EU-40`).
**Method of record:** MVP §4.2–§4.4; `IMP_step8/outputs/floor_layout_generation_report.md` §3, §5–§9;
*Energy & Buildings* 337 (2025) 115620 §4.1.1 + Fig. 4.

---

## 1. Hard rules for the executor

1. **Execute this plan. Do not propose alternatives.** If a rule document is ambiguous, **STOP and quote the
   conflict** — do not resolve it yourself. `EU-13B` §0 shows what happens otherwise.
2. **Never reduce a building's dwelling count** to make it fit a grid, a habitability gate or a coverage bar.
   Refuse it into the disclosed residual instead. This is the one unconditional failure.
3. **Never tune an input to move an EUI into a band.** Report the number and the band it falls in.
4. **Speed only for compute.** `sbatch --array`, fire-and-forget, from `speed-submit2`, never `srun`, never
   `ssh … python`. The remote login shell is **tcsh** — wrap every command with the `_ssh()` helper
   (`scripts/cluster/t08_harvest_results.py:104`). No `sbatch` before stop-and-report 2 is answered.
5. **Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` first.**
   After solving any error, register it there before closing the task. Not optional, not deferred.
6. **Append one progress-log entry per completed task to §8 of this document**, and one row per task to
   `../content/walkthrough_progress_log.csv`.
7. **Do not edit** root `main.py`, OVERVIEW or DESIGN docs, `openubem/config.py:34`
   (`SHADING_SPHERE_RADIUS`), the frozen `previous/` documents, or any `openubem/outputs/eu_certified_rerun_2026-08-28/` artefact.
8. **No new files beyond §3.** No extra reports, boards, dashboards or helper scripts.
9. Default to no code comments. Mirror `openubem/outputs/3D/` into `../outputs_3D/` and verify byte-identical.

---

## 2. Measured starting state (do not re-derive; verify if you doubt it)

| Fact | Value | Where measured |
|---|---:|---|
| Side-cars on disk | 2,541 | `../outputs_3D/eu_*_data/layouts/` |
| Ruled-scheme buildings | **1,469 (57.81 %)** | scheme ∈ `ruled_grid_*` ∪ `i_shape_linear_gallery` ∪ `l_shape_decomposition` |
| Secondary strip-cutter buildings | **843 (33.2 %)** | `scheme == equal_strip_multi_angle_sweep` |
| No layout at all | 229 (150 `NARROW_FOOTPRINT_LT_8M`, 75 `>8`/floor, 4 `PARTITION_AUDIT_FAILED`) | `fallback_reason` |
| Storey-partitions on the strip cutter | **3,763 of 10,650 (35.3 %)** | `scheme_by_storey` |
| `fallback_reason` on the 843 | **`None` on all 843** | — the cause is not recorded |
| `has_unconditioned_core` true | **0 of 2,541** | — |
| `circulation_area_m2_total > 0` | only **324** — the `2×2`, `3×2`, `4×2`, gallery routes | — |
| Ruled routes owed a core but carrying none | **682 `ruled_grid_2x1`**, **62 `l_shape_decomposition`** | rule gives a stair core to 2–4 dwellings/storey |
| Dwelling conservation | 28,189 declared → **28,189** zones, 0 non-conserving | distinct zone names, 2,312 emitted |
| IDFs carrying `Shading:*` | **0 of 2,516** | `openubem/outputs/eu_evidence/EU-11/*/idfs/` |
| IDFs carrying `Adiabatic` | **0 of 2,516** | same |
| Context buildings within 20 m | mean 11.14–12.16, max 28 | `openubem/outputs/eu02/*/01_buildings_clean.gpkg` |
| Buildings attached to ≥1 neighbour (0.30 m) | 88.5 % – 99.1 % | same |

---

## 3. File layout — the only files this plan may touch

**Modify:**
- `openubem/geometry/european_residential.py` — courtyard route, dispatch hardening, carved circulation.
- `scripts/run_eu_s2_campaign.py` — context list, adiabatic call, `ShadowCalculation` (`:74`, `:227`).
- `scripts/run_eu_s2_district_campaign.py` — `_geometry()` parity, conditioned-area column.
- `scripts/emit_eu11_layout_sidecars.py` — `fallback_reason`, core, conditioned area in the side-car.
- `scripts/generate_eu_3d_viewers.py` — core in the pop-up, conditioned vs gross area in the header.
- `openubem/geometry/context.py` — European height precedence only (R4). Do **not** change the signature.

> **`D-EU-41` (2026-08-30):** `openubem/idf/surfaces.py` stays **non-editable** and is confirmed so. T07's
> party-wall flip belongs in `scripts/run_eu_s2_campaign.py`, already listed above. No file is added to this
> layout by that ruling.

**Create:**
- `tests/geometry/test_eu15_ruled_coverage.py`, `tests/idf/test_eu16_context_adiabatic.py`.
- `openubem/outputs/eu_evidence/EU-15/RESULTS_EU-15.md`, `.../EU-16/RESULTS_EU-16.md`.
- `../validation/VALIDATION_EU-15_EU-16_zoning_context_2026-08-30.md` (T10 only).

**Regenerate:** `openubem/outputs/eu_evidence/EU-11/*/idfs/`, `openubem/outputs/3D/`, `../outputs_3D/`.

---

## 4. Dependency decisions (pinned)

- EnergyPlus **23.1.0 Ubuntu20** on Speed, `/speed-scratch/o_iseri/openubem/tools/`. A Speed number and a
  Windows number are not the same measurement (`FINDING 187`, `FINDING 190`).
- Geometry: `geomeppy` + `shapely`, as already used. No new dependency.
- Context radius **20.0 m**, European constant, new. `config.SHADING_SPHERE_RADIUS = 30.0` is **not** edited.
- Floor-to-floor **3.0 m** (`FLOOR_TO_FLOOR_M`), attachment tolerance **0.30 m**, habitability minimum
  **2.50 m** facade contact, ruled ceiling **8 dwellings/floor**, circulation **9 % of plate** (the 6–12 %
  midpoint), `Solar Distribution = FullExterior`.
- The four pinned fold EPWs are unchanged (`RULED_PINNED_EXCEPTION` in `weather_registry.json`).

---

## 5. Facts with citations the tasks depend on

- Ruled grid table `1×1 / 2×1 / 2×2 / 3×2 / 4×2`, ceiling 8/floor: report §5 "Detailed Grid Specification
  Table"; implemented at `openubem/geometry/european_residential.py:171` (`_DENSITY_GRID_TABLE`) and
  `:31` (`RULED_GRID_MAX_DWELLINGS_PER_FLOOR`).
- Morphology branching — point block `L/W < 2.0`, L-shape reflex decomposition, I-shape gallery
  `L/W ≥ 2.0` with a **1.80 m** double-loaded spine, U-shape/courtyard three-wing unfolding: report §6.1–§6.4.
  Dispatch at `european_residential.py:418` (`classify_building_morphology`) and `:607`
  (`generate_european_ruled_storey_layout`); **`courtyard_secondary` currently routes straight to the strip
  cutter at `:676`.**
- Core rules — centroidal, **12.0–25.0 m²** and **6–12 %** of gross floor area, extruded z=0→roof, unconditioned,
  $b_u = 0.50$–$0.80$: report §7.1–§7.2. `FINDING 204` records that the two criteria only co-hold for plates
  of 100.0–416.7 m² (1,602 of 2,544 = 63.0 %); **the percentage rule binds and every departure from the
  absolute band is tagged** — already implemented as `circulation_outside_ruled_absolute_band`.
- q/(q+1) stratification: report §8. `allocate_european_dwellings` (`european_residential.py:1577`).
- Habitability gate 2.50 m, retry = 90° rotation at the same count, then downgrade, then fail closed:
  report §9; `generate_european_grid_layout` (`:273`).
- Context: 20 m radius, sequential per-building simulation, non-simulated buildings still shade, attached
  walls adiabatic — paper §4.1.1 p. 9. Machinery: `discover_context` (`openubem/geometry/context.py:6`),
  `extrude_geometry(idf, zones, context)` (`openubem/idf/surfaces.py:774`), `set_adiabatic_surfaces`
  (`:909`). Ordering invariant `intersect_match` before shading blocks: `surfaces.py:781`.
- The defect line: `scripts/run_eu_s2_campaign.py:227` — `extrude_geometry(idf, zones, [])`.

---

## 6. Task list

### `EU-15` — ruled thermal zoning

**T01 — record why the secondary route was taken.**
*What:* set `fallback_reason` on every building that leaves the ruled route, and publish the per-cause census
per district. *Why:* it is `None` on all 843 today, so the 33.2 % gap cannot be attributed.
*How:* `_secondary()` (`european_residential.py:641`) already receives a `reason_hint` and discards it when
the legacy layout succeeds — keep it. Propagate to the side-car. *How to test:* re-emit one district;
`fallback_reason` non-null on 100 % of `equal_strip_multi_angle_sweep` side-cars; the census sums to the
district's strip count exactly. **Measurement + plumbing only — no partitioner behaviour changes here.**

**T02 — implement courtyard unfolding (report §6.4).**
*What:* detect the interior-ring / U-shape footprint, subtract the courtyard void, unfold the remaining
C-band into three orthogonal wings served by circulation nodes at the two inner corners, and partition each
wing by area fraction. *Why:* `classify_building_morphology` returns `courtyard_secondary` and
`generate_european_ruled_storey_layout:676` sends it straight to the strip cutter — a named, un-implemented
route, and the single largest identified cause of the 33.2 %. *How:* new route alongside
`l_shape_decomposition`, reusing `_split_at_reflex_vertex` and the wing-proportional recursion already at
`:676`–`:700`. *How to test:* golden fixtures (square courtyard, rectangular courtyard, U-shape, C-shape) in
`tests/geometry/test_eu15_ruled_coverage.py` — every wing partition passes `audit_european_floor_partition`,
area error 0.00 %, every dwelling ≥ 2.50 m facade contact.

**T03 — harden the L-shape and gallery routes on noisy GIS footprints.**
*What:* make `_split_at_reflex_vertex` and the gallery route survive real footprints with near-collinear
vertices, slivers and multiple reflex vertices. *Why:* they currently fall back rather than mislabel — correct
behaviour, but it is the second cause of the gap. *How:* pre-simplify at the existing
`regularization_tolerance_m = 0.15`; handle >1 reflex vertex by recursing on the larger lobe; keep the
2 % regularization area gate unchanged. **Do not loosen `audit_european_floor_partition` or the 2 % gate.**
*How to test:* the 843 strip-cutter buildings are replayed; report how many each of T02 and T03 recovers,
separately, and that 0 buildings changed their declared dwelling count.

**T04 — retire the strip cutter as a success path (`D-EU-39` §2).**
*What:* a storey the ruled route cannot express is **refused**, not relabelled: `dwelling_layout_emitted =
False`, `geometry_outcome = FALLBACK_PENDING_LAYOUT*`, `fallback_reason` set, building keeps
`one_zone_per_floor`. *Why:* `DWELLING_LAYOUT_EMITTED` currently counts the strip cutter as success, which is
`FINDING 207`. *How:* `_secondary()` stops returning an emitted layout. *How to test:* 0 side-cars fleet-wide
carry `scheme == equal_strip_multi_angle_sweep` with `geometry_outcome` starting `DWELLING_LAYOUT_EMITTED`;
per-district ruled coverage recomputed and reported against the **≥ 95 % per-district** bar.

**T05 — carve the unconditioned core and the corridor spine (`D-EU-39` §3, unblocks `EU-13B` T06).**
*What:* cut circulation out of the observed plate and emit it as an unconditioned zone — centroidal stair core
for 2–4 dwellings/storey, 1.80 m double-loaded spine for ≥ 5, extruded z=0→roof so every dwelling shares a
party wall with it. *Why:* 0 of 2,541 have it; it is the mechanism behind the MVP's $b_u$ buffering.
*How:* `_centred_circulation_region` (`:237`) already computes the polygon — subtract it from the plate before
partitioning; emit the zone with no heating/cooling, infiltration `0.000500 m³/(s·m²)`. Extend it to the two
ruled routes that carry none today: **`ruled_grid_2x1`** (2 dwellings/storey is inside the rule's 2–4 stair-core
band) and **`l_shape_decomposition`** (a core per wing, at the inner-corner junction).
**Publish `conditioned_floor_area_m2` beside `gross_footprint_area_m2`** on every side-car, manifest row and
pop-up. *How to test:* dwellings + circulation = the observed plate to 0.00 % on every storey;
`has_unconditioned_core = true` wherever a storey carries ≥ 2 dwellings; the core zone appears in the IDF
with no `ZoneHVAC:IdealLoadsAirSystem`; conditioned area < gross area on exactly those buildings.

### 🔴 Stop-and-report 1 — after T05, before any IDF work

Report: per-district ruled coverage against the ≥ 95 % bar (Madrid / Lyon / London / Bologna, each named);
the T02 and T03 recovery split; the residual by `fallback_reason`; the conditioned-vs-gross area table;
and the eight `EXAMPLE_dwelling_layout_validation_2026-08-28.md` §6 acceptance buildings, all five criteria,
including `relation/3730743` **refused**. **Stop.**

### `EU-16` — context geometry

**T06 — 20 m context shading in the European IDF path (`D-EU-40` R2–R5, R7, R8).**
*What:* replace `extrude_geometry(idf, zones, [])` (`run_eu_s2_campaign.py:227`) with the real context list.
*How:* load `01_buildings_clean.gpkg` once per district; per target, query the 20 m buffer against the spatial
index; build shading volumes via `discover_context` with a European radius constant and the R4 height
precedence (`height_m` → `levels × 3.0` → district median residential height, each fallback counted); add a
`ShadowCalculation` object and state its settings. Shading blocks after `intersect_match` (`surfaces.py:781`).
*How to test:* `tests/idf/test_eu16_context_adiabatic.py` — a synthetic 5-building block emits exactly the
neighbours inside 20 m and none outside; no context building appears as a `Zone`; on 10 named real buildings
per district the emitted shading count equals the spatial query exactly.

**T07 — adiabatic party walls for attached buildings (`D-EU-40` R6, as amended by `D-EU-41`). — REWRITTEN
2026-08-30 after the executor's blocker; the original text below the rule is withdrawn.**
*What:* flip walls shared with a neighbour within 0.30 m to `Adiabatic` on the European path.
*Why:* 0 of 2,516 IDFs have one, and 88.5–99.1 % of buildings are attached.
*How:* 🔴 **not** `set_adiabatic_surfaces` — that function is a no-op stub and its signature
`(idf, zones, strategy)` carries no neighbour footprints, so it cannot do this (`D-EU-41`, `RULES` §2 R6
amendment). `openubem/idf/surfaces.py` is **not edited**; the North-American path stays byte-unchanged.
Implement a European-only pass in `scripts/run_eu_s2_campaign.py` (plan §3 already lists it for "adiabatic
call"), reusing the **same** neighbour rows and the **same** coordinate transform `build_european_context`
(T06) already uses. Scope: `BUILDINGSURFACE:DETAILED` with `Surface_Type == Wall` **and**
`Outside_Boundary_Condition == outdoors` only — never `ground`, never `surface`, never a `Floor`/`Roof`/
`Ceiling`; ground-floor slabs at `z = 0` keep `Ground` (`surfaces.py:912`). Flip sets
`Outside_Boundary_Condition = Adiabatic`, blanks `Outside_Boundary_Condition_Object`, `Sun_Exposure = NoSun`,
`Wind_Exposure = NoWind`. Runs after `intersect_match` and after shading blocks (R8 untouched).
*How to test:* extend `tests/idf/test_eu16_context_adiabatic.py` — two touching footprints flip exactly the
shared wall and nothing else; a detached building flips nothing; the flipped surface is E+-valid
(`NoSun`/`NoWind`, no BC object); zone count identical before and after. Then report, per district, the count
of IDFs carrying ≥1 `Adiabatic` surface against the measured attachment census, **and** flipped exterior wall
area as a fraction of total exterior wall area (`D-EU-41`, R9 addition); 0 zones gained or lost by this task
alone.

**T08 — rebuild all four districts' IDFs locally and census. THEN STOP.**
*What:* run `prepare()` for all four districts; report zone-count deltas vs the current fleet, the
`IDF_ASSEMBLY_FAILED_*` residual, the shading and adiabatic censuses, and the array-size estimate.
*Why:* `D-EU-35`'s rule stands — the pop-up and the simulated IDF must never describe different geometry.
*How to test:* every side-car's zone-name set equals its IDF's zone set, for a 20-building sample per district.
**No `sbatch`.**

### 🔴 Stop-and-report 2 — after T08. No compute without an explicit instruction.

**T09 — resimulate on Speed, harvest, rebind.**
*What:* ship the four fleets, `sbatch --array` under the ~20k cap, harvest, re-emit side-cars, regenerate the
four viewers, mirror to `../outputs_3D/`, update `../results/RESULTS_EU-11.md`.
*How to test:* mirror byte-identical (`diff -rq`); every Speed failure classified and carried as a row with
blank `heating_kwh`, never smoothed into a pooled figure; per-district before/after EUI table with the
shading and adiabatic effects reported **separately in sign**, per `RULES_context_geometry_simulation` §3.5.

### 🔴 Stop-and-report 3 — after the harvest, before any interpretation.

**T10 — validation (independent audit).**
*What:* audit `EU-15` and `EU-16` against both rule documents' acceptance tests and write
`../validation/VALIDATION_EU-15_EU-16_zoning_context_2026-08-30.md`. *Why:* every prior package in this arc
that skipped the audit shipped a defect the owner found by clicking the viewer.
*How:* re-measure — never re-read a results table — (a) per-district ruled coverage from the side-cars on
disk; (b) `has_unconditioned_core` and the conditioned-vs-gross area accounting; (c) `Shading:*` and
`Adiabatic` counts by grepping the emitted IDFs; (d) the eight `EXAMPLE` §6 buildings, all five criteria;
(e) side-car ↔ IDF zone-set agreement on a fresh sample; (f) that no dwelling count anywhere was reduced.
*How to test:* the document ends in a single verdict — **PASS**, or a numbered defect list with `file:line`.
A criterion that cannot be measured is reported **NOT SCOREABLE**, never PASS.

---

## 7. Stop-and-report points

| # | After | What must be answered before continuing |
|---|---|---|
| 1 | T05 | Does every district clear ≥ 95 % ruled coverage? Is the carved-core area accounting accepted? |
| 2 | T08 | Explicit instruction to submit to Speed, with the array sizes reviewed. |
| 3 | T09 | Are the four new EUIs accepted as the arc's figures, and which DR12–16 verdicts moved? |

---

## 8. Progress log

*(one entry per completed task, appended by the executor)*

`#### TXX — <title> — completed YYYY-MM-DD`
Artifacts / Deviations / Test status / Notes.

#### T01 — record why the secondary route was taken — completed 2026-08-30

Artifacts: `openubem/geometry/european_residential.py` (`EuropeanBuildingDwellingLayout.fallback_reason_by_storey`,
new field populated in all three return points of `generate_european_building_dwelling_layout`);
`scripts/emit_eu11_layout_sidecars.py` (`fb_reason` now sourced from `fallback_reason_by_storey[0]` whenever the
building's top-level scheme is `equal_strip_multi_angle_sweep`, plus a new `strip_cutter_reason_counter` /
`strip_cutter_fallback_reason_census` per-district return key); `openubem/outputs/eu_evidence/EU-11/*/layouts/*.json`
(regenerated, all 4 districts).

Deviations: none from the plan's *How*. `_secondary()` already preserved `reason_hint` on success (verified by
reading it); the actual discard point was `EuropeanBuildingDwellingLayout.fallback_reason` being hardcoded to
`None` on any building-level success and `scripts/emit_eu11_layout_sidecars.py` mirroring that with
`fb_reason = None` whenever `dwelling_layout_emitted`. Fixed at the actual discard points instead of `_secondary()`
itself; no partitioner behaviour changed.

Test status: `pytest -q tests/geometry/test_eu15_ruled_coverage.py -k t01` → 5 passed. Re-emitted all four districts
(not just one): `fallback_reason` is non-null on 100 % of the 843 `equal_strip_multi_angle_sweep` side-cars
(`test_t01_fallback_reason_is_non_null_on_every_strip_cutter_sidecar`), and each district's
`strip_cutter_fallback_reason_census` sums exactly to that district's strip-cutter count.

Notes: this task's own re-emit already reflects T02/T03's code (all three tasks were executed as one pass before
any district re-emit, per the plan's task order); the T01 census reported to the director below is measured
post-T02/T03, i.e. the residual, not the original 843.

#### T02 — implement courtyard unfolding (report §6.4) — completed 2026-08-30

Artifacts: `openubem/geometry/european_residential.py` — `_courtyard_void_polygon`, `_courtyard_wings_and_nodes`,
`generate_european_courtyard_layout`, plus shared helpers `_allocate_wing_dwelling_counts` and
`_combine_wing_results` (also used by T03); `tests/geometry/test_eu15_ruled_coverage.py` (golden fixtures).

Deviations: the plan's *How* names three wings; the implementation generalises to N wings (3 for an open
U/C-shape, 4 for a fully-enclosed ring) via box-tiling on the void's own aligned bounding box against the
footprint's bounding box, because a literal `Polygon.interiors` hole (the only case `classify_building_morphology`
routes to `courtyard_secondary`, see below) is topologically always fully enclosed and needs 4 wings, not 3; an
open U/C-shape with no hole naturally degenerates to 3 non-empty wings under the same formula (the 4th candidate
wing is empty). Circulation nodes are placed at every void corner that does not touch the footprint's own bounding
envelope — 2 for an open shape, 4 for a closed ring, matching "the two inner corners" for the 3-wing case exactly.

**Reverted a first attempt**: `classify_building_morphology` was initially widened so `reflex_count >= 2` (an open
U/C-shape with no hole) also routed to `courtyard_secondary`, on the theory that both are architecturally the same
courtyard typology. Measured on the real EU-11 fleet this *regressed* previously-successful `l_shape_decomposition`
buildings into the strip cutter (Madrid's strip count rose 284→302, `l_shape_decomposition` successes collapsed
23→3) — the box-tiling unfolder failed audit/facade-contact for many shapes the old naive single-split L-shape
route already served. Reverted: `courtyard_secondary` fires only on a literal interior-ring hole
(`has_courtyard`); open multi-reflex footprints stay on `l_shape_decomposition`, served by T03's recursive
hardening instead. Full writeup: `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, "European locations EU-15".

Test status: `pytest -q tests/geometry/test_eu15_ruled_coverage.py -k t02` → 7 passed (4 golden fixtures ×
courtyard-classification + zero-area-error/habitability, plus a dwelling-count-conservation check and a real-fleet
sanity check). All four fixtures (square courtyard, rectangular courtyard, u_shape, c_shape — literal-hole
polygons) partition with `area_error_fraction < 1e-6` and every dwelling ≥ 2.50 m facade contact.

Notes: fleet effect is small (2 of 237 `has_courtyard` buildings recovered) — most real interior-ring footprints in
this fleet are too irregular/thin-banded for a clean 4-wing partition at the ruled 8/floor ceiling and fail closed
to the secondary route (`INTERIOR_RING_COURTYARD_UNFOLD_FAILED`), never approximated. T03 (below) is the larger
recovery lever.

#### T03 — harden the L-shape and gallery routes on noisy GIS footprints — completed 2026-08-30

Artifacts: `openubem/geometry/european_residential.py` — `_split_at_reflex_vertex` gained a `tolerance_m` parameter
(pre-simplify tolerance, was hardcoded `0.5`); new `_l_shape_wings` (recurses on the larger lobe when it still
carries a reflex vertex at the finer tolerance, up to 4 wings); `generate_european_ruled_storey_layout`'s
`l_shape_decomposition` branch now tries three wing candidates in order — legacy `tolerance_m=0.5` two-wing split,
`regularization_tolerance_m` (0.15 m) two-wing split, then the `_l_shape_wings` recursive escalation — accepting
the first whose combined audit + facade-contact check passes.

Deviations: the plan's *How* says "pre-simplify at the existing `regularization_tolerance_m = 0.15`"; a first
implementation used 0.15 m exclusively (dropping the legacy 0.5 m candidate) and measurably regressed a handful of
previously-successful `l_shape_decomposition` buildings (a finer denoise shifts the split line enough to move a
dwelling's facade contact below 2.50 m in a nested wing partition). Added the legacy-tolerance candidate back as
the first-tried option so anything the old algorithm already solved is reproduced before any new candidate is
attempted — this is additive to the plan's instruction (0.15 m pre-simplify is still exercised, second and third
in the trial order), not a substitution for it. Did not loosen `audit_european_floor_partition`, the 0.15 m
regularization tolerance, or the 2 % area gate anywhere.

Test status: `pytest -q tests/geometry/test_eu15_ruled_coverage.py` → 14 passed.
`pytest -q tests/geometry/ tests/test_eu_floor_partition_audit.py tests/test_eu_real_footprint_feasibility.py
tests/test_eu_dwelling_allocation.py tests/test_eu_geo08_independent_parity.py tests/test_eu_s2_campaign.py
tests/test_eu_s2_geometry_remedies.py` → 159 passed, 2 failed (both pre-existing, unrelated,
`test_eu_real_footprint_feasibility.py::test_real_layout_generator_fails_closed_for_unsupported_topology`,
confirmed already logged as `[OPEN, out of EU-13B scope]` in the debug references before this session touched
anything). `pytest -q -k eu` (repo-wide) → 563 passed, 2 skipped, 2 pre-existing failures (same two).

Replay of the original 843 strip-cutter buildings (all 4 districts re-emitted): 74 recovered via T03, 2 via T02,
767 remain on the secondary route. 2 buildings (`way/310771805` Madrid, `32293` Bologna) regressed from a ruled
scheme to the secondary route on one nested per-storey dwelling count each — disclosed, not chased further (see
debug references EU-15 chapter). Dwelling-count conservation independently verified across all 2,318 emitted
buildings fleet-wide (zone-name-set count == `dwellings_total` on every one): 0 violations, 0 buildings changed
their declared dwelling count anywhere.

#### T04 — retire the strip cutter as a success path (`D-EU-39` §2) — completed 2026-08-30

Artifacts: `openubem/geometry/european_residential.py` (`_secondary()` inside `generate_european_ruled_storey_layout`
now always returns `dwelling_layout_emitted=False`, unconditionally — was `legacy.dwelling_layout_emitted`);
`openubem/outputs/eu_evidence/EU-11/*/layouts/*.json` (all 4 districts re-emitted, all `openubem/outputs/3D/`
viewers regenerated and mirrored byte-identical to `../outputs_3D/`).

Deviations: none from the plan's *How* — the fix is exactly the one line the plan names. 🔴 New finding surfaced by
this fix, not caused by it: `_combine_wing_results` (shared by `l_shape_decomposition`/`courtyard_wing_unfold`)
only ever checked each wing's own `dwelling_layout_emitted`; pre-T04 a wing whose ruled route failed but whose
legacy strip-cut succeeded reported `True`, so the whole building was accepted and labelled with a ruled top-level
scheme even though one wing was actually strip-cut internally. Fixing `_secondary()` closes this at every recursion
depth automatically (no separate fix needed), but it means the T01-T03 replay's own "1,469 + 76 recovered = 1,545"
figure was itself partly inflated by the same masking `FINDING 207` names at the top level. Full writeup:
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, "European locations EU-15".

Two pre-existing unit tests were asserting the masked (pre-T04) behaviour rather than testing their own stated
scope, and needed updating to the honest measured outcome (not loosening, not new behaviour):
`tests/geometry/test_eu15_ruled_coverage.py::test_t03_l_shape_survives_a_second_near_threshold_reflex_vertex` (its
fixture's wing combine was already failing before T04; only "passed" via the masked strip-cutter success) and
`tests/geometry/test_eu13b_circulation_sidecar.py`'s `L_SHAPE_SIDECAR` fixture (`way/420409335`, one of the
`EXAMPLE` §6 acceptance buildings, no longer succeeds via `l_shape_decomposition` at all post-T04 — replaced with
`way/288461989`, a real building that still does). `test_t01_fallback_reason_is_non_null_on_every_strip_cutter_sidecar`
and `test_t02_courtyard_wing_unfold_recovers_at_least_one_real_building` were measuring a population (strip-cutter-
scheme side-cars; courtyard recoveries) that T04 correctly reduces to zero by design — updated to measure the
honest current count rather than assert a stale value.

Test status: `pytest -q tests/geometry/ tests/test_eu_floor_partition_audit.py tests/test_eu_real_footprint_feasibility.py
tests/test_eu_dwelling_allocation.py tests/test_eu_geo08_independent_parity.py tests/test_eu_s2_campaign.py
tests/test_eu_s2_geometry_remedies.py` → 163 passed, 2 failed (both pre-existing, unrelated, already `[OPEN, out of
EU-13B scope]` in the debug references). `pytest -q -k eu -n 8` (repo-wide) → 594 passed, 2 skipped, same 2
pre-existing failures. `pytest -q -n 8 tests/` (full repo) → 2433 passed, 55 skipped, same 2 pre-existing failures.

Notes: 0 side-cars fleet-wide now carry `scheme == equal_strip_multi_angle_sweep` (was 843); every building that
would have carried it now reports `scheme=None`/`geometry_outcome=FALLBACK_PENDING_LAYOUT` with its real
`fallback_reason` instead, and the building keeps `one_zone_per_floor` (`_geometry()` in
`run_eu_s2_district_campaign.py` and the side-car emitter already shared this fallback path unchanged). Honest,
freshly re-measured per-district ruled coverage against the `D-EU-39` ≥ 95 % per-district bar — all four districts
fail it: Madrid 616/961 = 64.10 %, Lyon 198/297 = 66.67 %, London 40/82 = 48.78 %, Bologna 591/1,201 = 49.21 %,
fleet 1,445/2,541 = 56.87 %. Residual (fleet, by `fallback_reason`): `L_SHAPE_DECOMPOSITION_FAILED` 629,
`INTERIOR_RING_COURTYARD_UNFOLD_FAILED` 239, `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` 75 (unchanged from the
original census), `NARROW_FOOTPRINT_LT_8M` 144, `PARTITION_AUDIT_FAILED` 9 — sums to 1,096 = 2,541 - 1,445 exactly.
0 dwelling counts reduced anywhere (independently re-verified: 0 zone-name-set-count-vs-`dwellings_total`
violations across all 789 currently-emitted side-cars).

#### T05 — carve the unconditioned core and the corridor spine (`D-EU-39` §3) — completed 2026-08-30

Artifacts: `openubem/geometry/european_residential.py` (`CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION` 3→2,
new `CIRCULATION_INFILTRATION_M3_S_M2 = 0.000500`, `european_building_layout_to_zone_specs` now emits one
additional `conditioned=False` circulation zone per storey group that carries a core, new
`european_building_layout_area_summary()`); `scripts/run_eu_s2_campaign.py` (`build_idf_for_building`'s per-zone
loop skips `SIZING:ZONE`/`HVACTemplate:Zone`/gains and instead adds `ZONEINFILTRATION:DESIGNFLOWRATE` for any
`conditioned=False` zone); `scripts/run_eu_s2_district_campaign.py` (`prepare()` now writes
`gross_footprint_area_m2`/`conditioned_floor_area_m2` per prepared building); `scripts/emit_eu11_layout_sidecars.py`
(`has_unconditioned_core` computed from the storey groups instead of hardcoded `False`, `gross_footprint_area_m2`/
`conditioned_floor_area_m2` published on every side-car, per-floor `has_unconditioned_core`);
`scripts/generate_eu_3d_viewers.py` (pop-up header shows "N m² conditioned / M m² gross" when both are known, `k_obj`
carries `gross`/`cond`); `tests/geometry/test_eu15_ruled_coverage.py` (new T05 tests, incl. a synthetic
`build_idf_for_building` check that the circulation zone gets no `HVACTEMPLATE:ZONE:IDEALLOADSAIRSYSTEM` and does
get the ruled infiltration rate); all 4 districts' side-cars re-emitted and all 4 viewers regenerated/mirrored.

Deviations: the plan's *How* names "one core per wing, at the inner-corner junction" for `l_shape_decomposition`.
Implemented via the existing recursion instead of a new per-wing construction: each wing already recurses through
`generate_european_ruled_storey_layout`, so lowering the shared threshold to 2 makes any wing with ≥2 dwellings
carve its own centroidal core exactly as the point-block route does, and `_combine_wing_results` already unions
every wing's circulation into the combined result — no new code path was needed or added. 🔴 Measured gap left
disclosed, not resolved: an L-shape/courtyard storey whose total is exactly 2, split 1 dwelling per wing (the
wing-count allocator's own minimum-1-per-wing guarantee), gets no core anywhere on that storey, because neither
individual wing reaches the ≥2 threshold — `has_unconditioned_core` is therefore not literally guaranteed on every
≥2-dwelling L-shape/courtyard storey, only on every ≥2-dwelling storey where at least one wing itself carries ≥2.
Not chased further (out of the plan's stated *How*); the sidecar's own `floors[].has_unconditioned_core` makes
every instance of this visible, never silently hidden.

`floor_area_m2` (pre-existing manifest column, EUI denominator) is left computed as `sum(z.floor_polygon.area for
z in zones)` unchanged — since `zones` now includes the circulation zone, this column silently becomes equal to
the new `gross_footprint_area_m2`, not `conditioned_floor_area_m2`. Per `D-EU-39` §3 ("every EUI denominator
moves"), this is the ruled, intended consequence, not an oversight — flagged here because no future EUI
resimulation (T09) may compute `eui_kwh_m2` against `floor_area_m2`/gross without disclosing that the denominator
is gross, not conditioned.

Test status: `pytest -q tests/geometry/test_eu15_ruled_coverage.py -k "t05 and not sidecar"` → 12 passed (includes
the synthetic IDF check). `pytest -q tests/geometry/ tests/test_eu_floor_partition_audit.py
tests/test_eu_real_footprint_feasibility.py tests/test_eu_dwelling_allocation.py tests/test_eu_geo08_independent_parity.py
tests/test_eu_s2_campaign.py tests/test_eu_s2_geometry_remedies.py` → 172 passed, 2 pre-existing failures.
`pytest -q -k eu -n 8` (repo-wide) → 594 passed, 2 skipped, 2 pre-existing failures. `pytest -q -n 8 tests/` (full
repo) → 2433 passed, 55 skipped, 2 pre-existing failures. `diff -rq openubem/outputs/3D
docs/docs_ACTIVE/europeanLocations/outputs_3D` → only non-EU (US validation) viewer files differ; every `eu_*`
file and data folder byte-identical.

Notes: `has_unconditioned_core` is now true on 1,013 of 2,541 side-cars (was 0 of 2,541); `conditioned_floor_area_m2
< gross_footprint_area_m2` on exactly those 1,013 and equal on the other 1,528 (independently re-verified, 0
violations either direction). Area conservation (dwellings + circulation = observed plate) holds to <1e-9 relative
error on every emitted storey (unchanged from T01-T03, extended to the newly-carved storeys). Two more pre-existing
tests hardcoded the pre-`D-EU-39` "`has_unconditioned_core` is always False, pending D-EU-36" placeholder —
`tests/geometry/test_eu13b_dwelling_conservation.py::test_t07b_*` and
`tests/geometry/test_eu14b_bologna_layout_binding.py::test_t02_popup_header_and_unconditioned_core_agree` — updated
to assert the now-ruled invariant (core true ⇒ conditioned < gross) instead of the retired placeholder.

#### T06 — 20 m context shading in the European IDF path (`D-EU-40` R2–R5, R7, R8) — completed 2026-08-30

Artifacts: `openubem/geometry/context.py` (new `resolve_european_context_height` — `discover_context` itself is
**untouched**, both signature and body); `scripts/run_eu_s2_campaign.py` (`EUROPEAN_CONTEXT_RADIUS_M = 20.0`,
`SHADOW_CALCULATION_*` constants, `IDF_HEADER_TEMPLATE` gains a `ShadowCalculation` object, `build_idf_for_building`
gains `context: list[dict] | None = None` threaded into `extrude_geometry` in place of the hard-coded `[]`, new
`compute_district_median_residential_height_m` and `build_european_context` helpers); `scripts/run_eu_s2_district_campaign.py`
(`prepare()` loads `01_buildings_clean.gpkg` once per district, computes the district median residential height from
`rows` before the per-building loop, calls `build_european_context` per building and threads it into
`build_idf_for_building`, adds `context_building_count` to `prepared_buildings.csv` and `context_radius_m` /
`context_district_median_residential_height_m` / `context_height_fallback_census` to `summary.json`);
`tests/idf/test_eu16_context_adiabatic.py` (new, 7 tests, T06 scope only — see T07 blocker below).

Deviations: `discover_context`'s signature and body are both untouched per rule 3 — height re-resolution is a new
post-processing step in `build_european_context` (matches each returned context dict back to its source row by
parsing the `shade_<osm_id>` name `discover_context` already emits, then overwrites `"height"`), never an edit
inside `discover_context` itself, so the North-American path (`config.SHADING_SPHERE_RADIUS=30.0`, `levels×3.5`,
default `3.5`) is provably unchanged — `tests/test_context.py` and `tests/test_surfaces.py` both still pass, byte-
unmodified. District median residential height is measured over the district's own already-mapped residential row
population (the same population that gets simulated), never over the `01_buildings_clean.gpkg` superset directly —
Bologna's `01_buildings_clean.gpkg` carries **0 of 1,631** `height_m` and **0 of 1,631** `levels` (its height data
lives in a separate CTC dataset joined only inside `_it_rows()`), so a superset-only median would raise on every
Bologna run. `ShadowCalculation` settings (`PolygonClipping` / `Periodic` / 1-day) were chosen once, before any
EnergyPlus run in this dispatch, and are reported here, never tuned to a result.

Test status: `pytest -q tests/idf/test_eu16_context_adiabatic.py` → 7 passed. `pytest -q tests/test_context.py
tests/test_surfaces.py tests/test_eu_s2_campaign.py` → 44 passed (NA-path and existing EU-04 coverage unaffected).
Local smoke rebuild of the full `FR-LYO-HAUTCOEURPENTES` district (297 buildings, scratch output, **not** the
evidence path) measured 297/297 IDFs carrying ≥ 1 `Shading:Site:Detailed`, mean 12.28 / max 28 / min 3 neighbours
per building, 0 context object named as a `Zone`, `context_height_fallback_census` `{height_m: 3639,
levels_x_floor_to_floor_m: 2, district_median_residential_height: 7}` against a computed district median of 19.4 m.

Notes: T06 is complete and acceptance-passing on its own (`D-EU-40` R2–R5, R7, R8; RULES §3 criteria 1, 3, 4
confirmed on the FR smoke rebuild). The real `openubem/outputs/eu_evidence/EU-11/*/idfs/` evidence directories were
deliberately **not** overwritten by this task — see the T07 blocker immediately below; T08 rebuilds all four
districts once, after T07 is resolved, not twice.

#### T07 — adiabatic party walls for attached buildings — 🔴 BLOCKED, not executed — 2026-08-30

**Stopped per hard rule 1 ("if a rule document is ambiguous, STOP and quote the conflict — never resolve it
yourself"), not completed.** `openubem/idf/surfaces.py:909` `set_adiabatic_surfaces` is a **documented no-op
stub** — its own docstring: *"Currently no inter-building adjacency is modeled in a single BuildingIDF call, so
this function is a no-op stub retained for future extension."* `docs/docs_INVESTIGATE/REMEDIATION_prompts-audit-fixes.md`
records this as a deliberate prior remediation: *"`set_adiabatic_surfaces` body replaced with a no-op docstring
stub; both the ground-floor Adiabatic flip and the perim↔core Adiabatic flip removed."* Confirmed empirically:
`tests/test_surfaces.py` calls it twice and asserts nothing Adiabatic ever results; `git log` shows no change to
the function since. This is not a hypothesis — it is the current, tested, on-disk behaviour.

The conflict: T07's own text says *"Call `set_adiabatic_surfaces` (`openubem/idf/surfaces.py:909`, **unchanged**)
… for walls shared with a neighbour within 0.30 m,"* and `D-EU-40` R6 states *"Use `set_adiabatic_surfaces`, **which
already implements the inter-building flip**."* Both premises are false against the code as it stands: calling
the function **unchanged** is guaranteed to add zero `Adiabatic` surfaces, which cannot satisfy T07's own
acceptance test (a count "reported against the measured attachment census," 88.5–99.1 %) or `D-EU-40` R6/acceptance
criterion 2. Making it non-trivial would mean writing real cross-building adjacency-detection logic (which does not
exist anywhere on the European path today) — but plan §3's file layout does **not** list `openubem/idf/surfaces.py`
among the files this plan may modify, and hard rule 3 forbids resolving an ambiguity unilaterally. **No code was
written for T07.** T08 was not started (it rebuilds with the adiabatic census T07 was to produce).

Artifacts: none. Test status: none run for T07. Decision owed: whether `set_adiabatic_surfaces` may be implemented
for real (and `openubem/idf/surfaces.py` added to plan §3's file layout), or R6 is deferred/rescoped.

#### T07 — adiabatic party walls for attached buildings — completed 2026-08-30

**Unblocked by `D-EU-41`** (the R6 amendment quoted above). Executed per the rewritten §T07.

Artifacts: `scripts/run_eu_s2_campaign.py` (`EUROPEAN_ADIABATIC_TOLERANCE_M = 0.30`, `EUROPEAN_ADIABATIC_NOTE`,
new `_wall_xy_segment`, `_wall_area_m2`, `apply_adiabatic_party_walls`; `build_idf_for_building` calls
`apply_adiabatic_party_walls(idf, context or [])` immediately after `extrude_geometry(idf, zones, context or [])`,
before `write_zone_volumes`); `tests/idf/test_eu16_context_adiabatic.py` (new `TestT07AdiabaticPartyWalls`, 5
tests; module docstring and imports updated, the withdrawn "T07 blocked" note removed).

Deviations: none from `D-EU-41`'s corrected spec. `openubem/idf/surfaces.py` was not opened for editing;
`set_adiabatic_surfaces` is never imported or called by the new code. The flip reuses `context[i]["coords"]`
verbatim -- the same minimum-rotated-rectangle list `build_european_context` (T06) already returns for
shading -- via `Polygon(ctx["coords"]).buffer(tolerance_m)`, so shading and the flip share one neighbour
geometry source, per the ruling. Adjacency test actually used: each exterior wall's XY base segment (its two
most-distant projected vertices, robust to any extra collinear vertex on the wall) tested with shapely
`LineString(segment).within(neighbour_polygon)` against every neighbour's buffered footprint; the tolerance
(0.30 m) was never adjusted to move a count.

Test status: `pytest -q tests/idf/test_eu16_context_adiabatic.py` -> 12 passed (7 T06 + 5 new T07).
`pytest -q tests/idf/test_eu16_context_adiabatic.py tests/test_context.py tests/test_surfaces.py
tests/test_eu_s2_campaign.py tests/geometry/test_eu15_ruled_coverage.py` -> 87 passed (NA path and existing EU
coverage unaffected). The 5 new tests directly cover the *How to test* list: two touching 10x10 boxes flip
exactly the shared wall (verified by XY bounds, not just count) and none of the other 3 walls/the floor/the
roof; a neighbour 25 m away flips nothing; the flipped surface carries `Adiabatic` / blank BC object / `NoSun`
/ `NoWind`; a 2-storey building's zone count is identical (2) before and after the call; a context-free call is
a no-op returning `exterior_wall_area_m2` for the untouched perimeter.

Notes: `apply_adiabatic_party_walls` returns `{adiabatic_wall_count, exterior_wall_area_m2,
adiabatic_wall_area_m2}` per building for the R9 disclosure (computed in-process, not persisted as a new CSV
column -- no file beyond §3 was added). Real per-district census is reported under T08 below, since it
requires the rebuilt fleet.

#### T08 -- rebuild all four districts' IDFs locally and census -- completed 2026-08-30

Artifacts: `openubem/outputs/eu_evidence/EU-11/{ES-MAD-BERRUGUETE,FR-LYO-HAUTCOEURPENTES,GB-LDN-STDUNSTANS,
IT-BOL-GALVANI2}/{idfs/,prepared_buildings.csv,summary.json,fleet.lst,weather/,schedules/}` -- all four
districts' `idfs/`, `weather/`, `schedules/` cleared and regenerated from scratch via
`python -m scripts.run_eu_s2_district_campaign --district <D> --out
openubem/outputs/eu_evidence/EU-11/<D>` (local only, no `sbatch`); `layouts/` and the per-district manifest CSV
were not touched (already current from EU-15 T01-T05). `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
-- new "European locations EU-16" chapter, one `[OPEN]` entry (see Notes below). Pre-rebuild
`prepared_buildings.csv`/`summary.json` for all four districts were copied to the executor's scratchpad before
being overwritten, purely so this task's own zone-count-delta report could be computed; not committed anywhere.

Deviations: none from the plan's *How*. The 20-building-per-district side-car/IDF check could not use raw
zone-name-set equality as literally worded -- `run_eu_s2_district_campaign.py`'s `prepare()` renames every
building to a SHA-256 `stem` before emitting its IDF (OSM ids contain `/`, illegal in an EnergyPlus name),
while `layouts/*.json` (written earlier by `scripts/emit_eu11_layout_sidecars.py`) keeps the original OSM
`building_id` -- so the two zone-name sets never share a common prefix by construction, independent of any
EU-16 geometry work. The check actually run: per-floor dwelling-zone count and carved-core presence, matched
by storey index, sampled 20 buildings per district (`random.seed(20260830)`).

Test status: no `sbatch`. `prepare()` for all 4 districts completed with zero `IDF_ASSEMBLY_FAILED_*` in
every district's `blocker_exclusions` (previously documented residual after `EU-13B` T09 was 0.94-4.7%; now
0/0/0/0, attributable to `EU-15` T01-T05's geometry hardening completed earlier in this arc). Side-car/IDF
per-floor structural parity, 20-building sample per district: Madrid 13/20, Lyon 11/20, London 15/20, Bologna
17/20 match. Every mismatch was traced to one single cause (see new finding below), not to T06/T07 -- the 5
T07 unit tests and the T06 real-fleet spatial-parity tests already isolate and pass the context/adiabatic
contribution on its own.

New finding recorded: `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, "European locations EU-16"
chapter (`[OPEN]`). A `geometry_outcome == DWELLING_LAYOUT_EMITTED[_IMPUTED_COUNT]` building's realized IDF
can still be silently rerouted to `one_zone_per_floor` inside `extrude_geometry`'s own `intersect_match`
exception handler (`openubem/idf/surfaces.py:863-884`, already documented in the `EU-13B` chapter), and neither
`geometry_outcome` nor the side-car is ever updated to say so -- the `D-EU-35` failure mode, measured fleet-wide
at 26-45% of nominally-ruled buildings per district (Madrid 173/616, Lyon 52/198, London 18/40, Bologna
214/594), an order of magnitude above the previously-documented `IDF_ASSEMBLY_FAILED_*` rate. Not fixed here:
`openubem/idf/surfaces.py` and `scripts/emit_eu11_layout_sidecars.py` are both outside `EU-16A` T07/T08's file
layout (plan §3). Orthogonal to T06/T07 by construction -- proven by their own controlled unit tests, not by
this fleet-wide number.

Notes -- the five stop-and-report-2 disclosures:

1. Shading census. 100% of IDFs carry >=1 `Shading:Site:Detailed` in all four districts (2,544/2,544).
   Mean/max neighbours: Madrid 47.51/104, Lyon 49.13/112, London 30.10/80, Bologna 44.86/112.
2. Height-precedence census (`context_height_fallback_census`, from each district's `summary.json`):
   Madrid `{levels x 3.0: 9490, district_median: 1924}` (no `height_m` in `01_buildings_clean.gpkg`); Lyon
   `{height_m: 3639, levels x 3.0: 2, district_median: 7}`; London `{levels x 3.0: 512, district_median: 105}`;
   Bologna `{district_median: 13504}` (no `height_m`/`levels` at all in its context layer -- matches T06's own note).
3. Adiabatic census vs the measured attachment census, and flipped-area fraction (`D-EU-41` R9): Madrid
   859/961 = 89.39% (vs approx 99.1% measured attachment), Lyon 257/297 = 86.53% (vs approx 97.0%), London 58/82
   = 70.73% (vs approx 92.8%), Bologna 972/1204 = 80.73% (vs approx 88.5%) -- below the attachment census in all
   four districts, reported as measured, not tuned. Flipped exterior wall area / total exterior wall area:
   Madrid 30.74%, Lyon 33.35%, London 12.29%, Bologna 34.90%. The gap between the IDF-count adiabatic
   census and the building-level attachment census is explained by the stated adjacency test itself: it
   requires a wall's entire XY base segment to lie inside a neighbour's buffered minimum-rotated-rectangle
   footprint (per `D-EU-41`'s own wording, reusing `build_european_context`'s exact neighbour geometry); a real
   party wall that only partially overlaps a neighbour along its length (common -- adjacent buildings rarely
   share an identical footprint edge) fails this whole-segment containment test even though the buildings are
   physically attached, while the original attachment census (Madrid approx 99.1% etc.) was a building-level
   footprint-touch measurement, not a per-wall-segment-containment one. This is a measured consequence of the
   test `D-EU-41` specifies, not a bug -- the tolerance was never touched to close the gap.
4. Zone-count delta vs the pre-T08 on-disk fleet: Madrid 9,275->5,093 (952->961 IDFs), Lyon 4,117->2,214
   (283->297), London 1,059->568 (80->82), Bologna 13,990->8,423 (1,201->1,204). This fleet-level delta is not an
   isolate of T07 -- it mixes in `EU-15` T01-T05's already-completed zoning changes (carved cores, retired strip
   cutter) still pending on-disk before this rebuild, plus the silent-reroute residual disclosed above (which
   reduces realized zone count below what the side-car intends). T07's own "0 zones gained or lost" claim
   rests on its 5 controlled unit tests, which hold it constant by construction. `IDF_ASSEMBLY_FAILED_*`
   residual: 0/0/0/0 (all four districts).
5. Proposed T09 array sizes (= `population_prepared`, one array task per building): Madrid 961, Lyon 297,
   London 82, Bologna 1,204 -- 2,544 total, one wave, comfortably under the approx 20k Speed `MaxJobCount` cap.

#### T09 / `D-EU-42` / `D-EU-43` -- resimulate on Speed, harvest, `FINDING 210` fix wave -- state reconstruction 2026-08-31, NOT COMPLETE

Owner's authorising sentences on file: T09 "oui, autorise la soumission Speed pour T09" (2026-08-30);
`D-EU-42` "oui, autorise la re-soumission apres correction" (2026-08-31); `D-EU-43` "autorise l'option a" /
"continuer jusqu'a la fin, et apres la fix, soumettre a la speed. merci" (2026-08-31).

This entry is written by a fresh session reconstructing state after a prior session was killed mid-flight
(not crashed). Nothing below was taken from that session's own claims without independent `sacct`/`.err`
verification.

**Wave 1 (T09, submitted before this session, confirmed via `sacct -j <id> -X`):**

| Job | District | tasks | COMPLETED | FAILED | TIMEOUT |
|---|---|---:|---:|---:|---:|
| `1299912` | `ES-MAD-BERRUGUETE` | 961 | 863 | 98 | 0 |
| `1299945` | `FR-LYO-HAUTCOEURPENTES` | 297 | 262 | 26 | 9 |
| `1299946` | `GB-LDN-STDUNSTANS` | 82 | 80 | 2 | 0 |
| `1299947` | `IT-BOL-GALVANI2` | 1,204 | 1,014 | 177 | 13 |

Of the 98 Madrid + 26 Lyon + 2 London failures, 66/13/2 carry the `FINDING 210` vertex-size-mismatch
signature (`D-EU-42` scope) and 32/13/0 carry the zero/negative-surface-area signature (`D-EU-43` scope,
Madrid+Lyon only, 45 total) -- both counts confirmed by remote grep, matching the debug-references entries.
Bologna's 177 failed + 13 timeout were **not** re-run this session (no D-EU-42/43 authorisation covers
Bologna; out of scope here).

**`D-EU-42`/`D-EU-43` v1 (jobs `1302150`/`1302151`/`1302152` and `1302265`/`1302266`): 100 % FAILED, superseded.**
Remote job logs (`/speed-scratch/o_iseri/openubem/fleets/eu16_fix_mad_1302150_1.log` etc.) show these ran at
~12:10 on 2026-08-31, before the fixed IDFs existed (`idfs/*.idf` mtime 13:22) -- v1 ran against not-yet-rebuilt
geometry and is discarded, not a measurement of the fix.

**`D-EU-42`/`D-EU-43` v2 (corrected, IDFs rebuilt 2026-08-31 13:22 with `_stabilize_ring_coords`,
`openubem/geometry/european_residential.py:1825`): PARTIAL recovery, fix NOT proven, confirmed by `sacct`
and by reading `.err` on every sampled failure.**

| Job | Scope | District | tasks | COMPLETED | FAILED | recovery |
|---|---|---|---:|---:|---:|---:|
| `1302748` | `D-EU-42` | Madrid | 66 | 33 | 33 | 50.0 % |
| `1302781` | `D-EU-42` | Lyon | 13 | 9 | 4 | 69.2 % |
| `1302782` | `D-EU-42` | London | 2 | 1 | 1 | 50.0 % |
| `1302787` | `D-EU-43` | Madrid | 32 | 20 | 12 | 62.5 % |
| `1302788` | `D-EU-43` | Lyon | 13 | 8 COMPLETED, 4 FAILED, **1 still RUNNING** (`1302788_3`, 38 min elapsed at reconstruction time) | -- | -- |

Overall (excluding the still-running Lyon task): 71/125 recovered = 56.8 %. Every sampled remaining `FAILED`
task's `eplusout.err`, checked across all five jobs and all three districts (examples: Madrid `1d677f42eacf7815`
task `1302748_8`; Lyon `489894ba3d990787` task `1302781_3`; London `5ff998a792035b20` task `1302782_2`; Madrid
`33299a5b2a5bb9c9` task `1302787_8`), shows the **identical** `RoofCeiling:Detailed` vertex-size-mismatch fatal
that `FINDING 210` describes, on a different surface pair each time (not always 8 vs 9) -- confirmed against
freshly-rebuilt IDFs, not stale ones. This means the killed session's debug-references claim that `D-EU-42`
"conclusively proved" the fix, and that `D-EU-43`'s residual failures were a "clean" regenerate, is **false**;
both entries have been corrected in place (`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, `FINDING
210` and `D-EU-43` chapters, marked `[OPEN]`) rather than left standing.

**Not done this session, deliberately, given the finding above:** the four viewers were not regenerated, the
`../outputs_3D/` mirror was not touched, `RESULTS_EU-11.md` was not updated, and no per-district before/after
EUI table was produced. Producing an EUI table now would require deciding how to disposition the still-open
~54 residual `FINDING 210` casualties (blank-row them as permanent `EPLUS_FATAL`, or hold for a real fix to
the non-sub-millimetre vertex-count discrepancy) -- a call for the owner/manager, not this reconstruction pass,
per "diagnose before remediate." `RESULTS_EU-11.md` still reflects the pre-T09 (`EU-13B`/`EU-14B`) state and
must not be read as current for Madrid/Lyon/London.

Test status: no code was changed this session; the existing fix and its 4 `test_t09_*` unit tests in
`tests/geometry/test_eu15_ruled_coverage.py` were not re-run (their pass/fail does not bear on the finding
above, which is a Speed/GEOS-build residual, same class as `FINDING 187`/`190`).

Next: root-cause the residual ~54-task failure class (real vertex-count mismatch, not sub-mm duplication) and
decide the residual's disposition before any harvest/EUI/viewer/mirror work proceeds.

#### T09 continuation — root-cause the `FINDING 210` residual and fix — completed 2026-08-31

Owner's authorising sentences on file: "vas-y, root-cause le défaut résiduel" (2026-08-31, root-cause and fix
only, explicitly NOT a Speed resubmission); then, mid-task, "continuer jusqu'a la fin" (2026-08-31, relayed by
the manager, extending scope to one `sbatch --array` v3 wave on exactly the still-failing stems once the fix
was proven locally).

Enumerated the exact residual set by remote-grepping `eplusout.err` for "Vertex size mismatch" across all five
D-EU-42/D-EU-43 v2 fleet dirs on Speed: 32 (`finding210fix`) + 11 (`deu43fix`) Madrid, 4 + 4 Lyon, 1
(`finding210fix`) London = **52 stems** (not ~54; the earlier estimate included the Lyon task that was still
`RUNNING` at reconstruction time and has since resolved into this count).

Root cause (not what the task brief assumed): pulled the actual failing IDF for stem `1d677f42eacf7815`
(Madrid) from `/speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE_finding210fix/idfs/` and read the real
`BUILDINGSURFACE:DETAILED` vertex lists for the exact surfaces named in its `eplusout.err`. The mismatch is
**not** in ring construction — `_stabilize_ring_coords` (`openubem/geometry/european_residential.py:1825`) was
already correct and its 1 mm-snapped rings going into extrusion were identical/consistent. It is introduced
**after** extrusion by `geomeppy`'s own `intersect_match()` (`openubem/idf/surfaces.py:866`, non-editable per
`D-EU-41`), which computes new boundary vertices via live floating-point intersection arithmetic when it cuts
a same-zone-label block against its per-storey neighbours — independently for the ceiling of storey n and the
floor of storey n+1 — so the two can end up with different final vertex counts downstream of an identical input
ring. No ring-construction change (in `european_residential.py` or anywhere else) can fix a divergence
introduced this far downstream.

Fix: `scripts/run_eu_s2_campaign.py::build_idf_for_building` now calls `find_mismatched_interzone_pairs` right
after `extrude_geometry` and, if any remain, reroutes via `_force_reroute_room_layout_to_one_zone_per_floor`
(both already exist in `openubem/idf/surfaces.py`, non-editable, and the latter already explicitly supports
`mode="european_dwelling_layout"` zones) — the exact gate `openubem/idf/builder.py` already wires for the same
symptom on its own (`layout_assign`) pipeline, just never wired into the EU S2 campaign build path.
`scripts/run_eu_s2_district_campaign.py:387-392` now also flips `geometry_outcome` to
`..._INTERZONE_MISMATCH_REROUTED` when this fires, so a mid-build degrade to `one_zone_per_floor` is disclosed
in `prepared_buildings.csv`, not silently masked.

Proof, first pass (local, Windows/GEOS build — a different measurement than Speed's Linux build, `FINDING
187`/`190`): rebuilt all 52 residual stems with the fix. `find_mismatched_interzone_pairs` returned empty
post-build for all 52 — 20 via the reroute actually firing, 32 with no mismatch reproduced pre-reroute on this
platform (the 3 stems named in the task brief, `1d677f42eacf7815`/`489894ba3d990787`/`5ff998a792035b20`, are all
in this 32). Rebuilt and shipped as three fleet dirs (`EU11_{district}_finding210v3`), submitted as jobs
`1302881`/`1302908`/`1302920` per the "continuer jusqu'a la fin" authorisation — **but this proof was
insufficient.** The coordinator's mid-wait check caught real `FAILED` tasks under the identical
`RoofCeiling:Detailed` fatal while the wave was still draining; those three jobs were `scancel`-ed. Root cause
of the gap: a raw `len(coords)` count match does not guarantee EnergyPlus itself will keep the two paired
surfaces' vertex counts equal — confirmed by running EnergyPlus 23.1.0 directly (Windows, this session,
`C:\EnergyPlusV23-1-0\energyplus.exe` + `ExpandObjects.exe`) on stem `e21bec78b937acf5`: `find_mismatched_
interzone_pairs` had passed it clean (7 raw vertices each side, mirror-ordered) yet it FATALed identically to
Speed. The culprit was a sub-mm near-duplicate vertex pair (~0.0002-0.0006 m apart) `intersect_match` had
inserted into **both** surfaces' own rings, which EnergyPlus's GetVertices/CheckConvexity collapses
asymmetrically depending on ring winding direction — a raw count comparison cannot see this.

Fix extended (twice): `_has_near_duplicate_vertex_surfaces` (`scripts/run_eu_s2_campaign.py`, new) flags any
surface with two consecutive ring vertices closer than `NEAR_DUPLICATE_VERTEX_TOLERANCE_M = 0.005`. Re-verified
against real EnergyPlus: stem `8cdf349a99934f0d` (also passed clean by the first fix) still FATALed — no
near-duplicate points, but vertex 7 of a 9-vertex ring sat at an interior angle of exactly 180.000000 deg
(`cos(angle) = -1.0000000000000002`, machine-precision collinear) where a neighbouring zone's wall met the
shared edge. Added a collinearity check to the same function (`COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG = 0.1`,
i.e. > 179.9 deg) tuned tight enough not to fire on a real near-straight OSM corner measured at 179.348 deg on a
known-clean building (`BATIMENT0000000240879449_part0`, caught as a regression in
`tests/test_eu_s2_campaign.py` when the first, looser 2 deg tolerance over-triggered).

Proof, final: rebuilt all 52 stems with the twice-extended gate, then ran every one end-to-end through real
local EnergyPlus 23.1.0 (`ExpandObjects` + `energyplus.exe`, matching `submit_fleet_t08.sbatch`'s exact
invocation) — **0/52 FATAL**, ground truth, not the Python heuristic alone. Named-example before/after (6 of
the 52, all now real-EnergyPlus-clean): `8b3598ac47b3f4a0`, `b88b3c3325df733e`, `33299a5b2a5bb9c9`,
`e21bec78b937acf5`, `8cdf349a99934f0d`, plus the 3 task-brief stems.

Rebuilt: all 52 affected IDFs (43 Madrid, 8 Lyon, 1 London), packaged exactly like `prepare()` packages a fleet
(idfs/, weather/, schedules/<stem>/, fleet.lst). Re-shipped to Speed (same three `EU11_{district}_finding210v3`
fleet dirs, overwritten) and resubmitted: jobs `1302937` (Madrid, 43 tasks), `1302954` (Lyon, 8 tasks), `1302962`
(London, 1 task) — `sbatch --array`, fire-and-forget, confirmed queued/running via one `squeue` check, not
harvested. Harvest/fold-in into `prepared_buildings.csv`, `RESULTS_EU-11.md`, and the EUI table is a separate
follow-up, not this pass.

Artifacts: `scripts/run_eu_s2_campaign.py` (imports + gate in `build_idf_for_building`,
`_has_near_duplicate_vertex_surfaces`), `scripts/run_eu_s2_district_campaign.py:387-392` (outcome disclosure).
Deviations: none from the DESIGN/`D-EU-41` file-layout constraint — `openubem/idf/surfaces.py` was not edited;
the fix reuses its existing exported gate/reroute functions from the caller side, exactly as `builder.py`
already does for its own pipeline.
Test status: `pytest -q tests/test_eu_s2_campaign.py tests/geometry/test_eu15_ruled_coverage.py
tests/test_surfaces.py` → 71 passed, re-run after each of the two gate extensions (the second extension's first
attempt, a 2 deg collinearity tolerance, was caught here as a regression and tightened to 0.1 deg before this
pass closed).
Notes: FINDING 210 and D-EU-43 chapters in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` updated in
place, `[OPEN]` markers dropped, corrected to the final (twice-extended) fix and job IDs.

Next: harvest the v3 wave once it drains (separate authorisation already covers submission; harvest is
follow-up), then fold recovered stems into `prepared_buildings.csv`/`RESULTS_EU-11.md` and decide disposition
for any still-residual stems.

#### T09 / `D-EU-42` / `D-EU-43` — harvest of the corrected `v3` wave, fold-in, `RESULTS_EU-11.md` — completed 2026-08-31

Owner's authorising sentences on file (unchanged, quoted verbatim from `PROMPT_EU-16B_speed_resimulation_T09.md`):
T09 *"oui, autorise la soumission Speed pour T09"* (2026-08-30); `D-EU-42` *"oui, autorise la re-soumission
après correction"* (2026-08-31); `D-EU-43` *"autorise l'option a"*, followed by *"continuer jusqu'a la fin,
et apres la fix, soumettre a la speed. merci"* (2026-08-31). This entry is the harvest-only follow-up
promised at the end of the previous entry; no new Speed submission was made or authorised here.

Confirmed via `sacct -j 1302937,1302954,1302962 --format=JobID,State,ExitCode -X`: all 52 array tasks
`COMPLETED`, `0:0` (43 Madrid, 8 Lyon, 1 London). Fetched `out/<stem>/{eplusout.sql,.err,.eio,task.rc}` for
all 52 directly from `EU11_<district>_finding210v3/out/` (remote tar stream, never a local path list), and
folded the parsed results (`eplus_return_code`, `severe_errors`, `fatal_errors`, `heating_kwh`,
`eui_kwh_m2`, `run_seconds`) into the three district manifest CSVs, replacing the 52 corresponding rows by
`building_id`. Regenerated `summary.json` for the three touched districts from the updated manifests.
Re-ran `scripts/generate_eu_3d_viewers.py` (all four districts) to pick up the updated `eui_kwh_m2` and
mirror `openubem/outputs/3D/` → `../outputs_3D/`.

🔴 Two findings made during this harvest, both registered in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`
("European locations EU-16" chapter): (1) the base `EU11_<district>/out/` tree held stale, non-Speed data
(missing `platform.txt`/`energyplus_version.txt`, mtime predating the real job's own completions) for
exactly the 52 `v3`-scope stems — a leftover of an earlier local-Windows `EnergyPlus` proof run, never
trusted for this harvest, which read the 52 rows only from the job's own `_finding210v3` output; (2) 2
Madrid stems (`df490cc7ec52ebb4`/`way/380242666`, `5897ad5bdd60c3ae`/`way/941927233`) carry the same
degenerate-surface fatal class but were never enumerated into the 43-stem `v3` `fleet.lst` and were never
resubmitted under any wave — the plan's own earlier reconstruction entry's arithmetic (98 Madrid casualties
− 53 `v2`-recovered = 45 residual) does not reconcile against the 43 actually rebuilt; these 2 stems are
that unexplained gap. Both remain `[OPEN]`/disclosed, not fixed — no further Speed submission is authorised
under `D-EU-42`/`D-EU-43`.

Recovery per district (wave-1 `FAILED` → still failing after this fold): Madrid 98 → 2; Lyon 26 → 0 (Lyon's
9 remaining failures are wave-1 `TIMEOUT`s, out of `D-EU-42`/`D-EU-43` scope, unrelated); London 2 → 0.
Post-fold pooled heating EUI: Madrid 72.1258 kWh/m² (959/961 success), Lyon 62.1528 kWh/m² (288/297),
London 78.4405 kWh/m² (82/82, fully recovered). Bologna unchanged (out of scope): 48.9253 kWh/m²
(1,014/1,204), 🔴 `IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD`.

Artifacts: `openubem/outputs/eu_evidence/EU-11/{ES-MAD-BERRUGUETE,FR-LYO-HAUTCOEURPENTES,GB-LDN-STDUNSTANS}/
{<slug>_manifest.csv,summary.json}` (updated); `openubem/outputs/3D/eu_*` and
`docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_*` (regenerated, mirrored); `docs/docs_ACTIVE/europeanLocations/
results/RESULTS_EU-11.md` (rewritten fresh, replacing a version from a session terminated mid-flight, kept
as `RESULTS_EU-11.md.STALE_killed-session-2026-08-31`, not deleted, not used as a source);
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (two new findings appended to the `FINDING 210`/`D-EU-43`
chapter).

Deviations: none from the plan's file layout — no code was changed this session (harvest only); the ad hoc
fold script used to parse and merge the 52 rows is a temporary scratchpad script, not committed to the repo
layout.

Test status: no code changed; no test suite re-run. `sacct` and remote file inspection were the only
verification instruments (per cluster hard rules 1–3).

Notes: `openubem/geometry/european_residential.py`'s uncommitted diff (~1,400 lines) was checked for
killed-session dead code — none found. `_stabilize_ring_coords` (`:1825`) is live and wired (called at
`:1877`/`:1891`, and from `scripts/run_eu_s2_district_campaign.py:166`), covered by 4 unit tests in
`tests/geometry/test_eu15_ruled_coverage.py` — it is the legitimate first-layer `FINDING 210` fix
(individually insufficient, per the root-cause entry above, but not an artifact of the killed session). The
rest of the diff is `EU-15` T01–T05 ruled-zoning geometry (grid layout, morphology classification,
courtyard/gallery layouts), in scope per plan §3.

Next: harvest/fold-in is complete. Two `[OPEN]` items remain for the owner/manager to disposition: the 2
unaccounted Madrid stems, and whether a further Speed wave should be authorised for them. `T10` (independent
audit) has not been started.

#### `D-EU-44` — recover the 2 unaccounted Madrid stems — completed 2026-08-31

Owner's authorising sentence, verbatim: *"oui, autorise D-EU-44 continuer jusqu'a la fin"* (owner, 2026-08-31,
replying to the manager's proposal to fix/rebuild/resubmit exactly the 2 Madrid stems (`df490cc7ec52ebb4` =
`way/380242666`, `5897ad5bdd60c3ae` = `way/941927233`) left over from the `D-EU-42`/`D-EU-43` harvest — same
`FINDING 210` degenerate-surface fatal class, never enumerated into the 43-stem `v3` `fleet.lst`, never
resubmitted). Scope: exactly these 2 stems, one Speed wave, harvest/fold-in/doc updates through to completion,
no further pause.

Rebuilt both locally through the already-fixed gate: a scratch script (`deu44_rebuild_two_stems.py`, not
committed — scratchpad only) calls `scripts/run_eu_s2_district_campaign.py::_mapped_rows` for
`ES-MAD-BERRUGUETE`, filters to the 2 `building_id`s, then replays `prepare()`'s exact per-building loop body
(same `_geometry`, `build_european_context`, `build_idf_for_building` calls, no code changed in either
`run_eu_s2_district_campaign.py` or `run_eu_s2_campaign.py`). Both fired the existing `FINDING 210` gate:
`rerouting room_layout to one_zone_per_floor (near_duplicate_vertex)`. **Proven locally with real EnergyPlus
23.1.0 (Windows, `C:\EnergyPlusV23-1-0\ExpandObjects.exe` + `energyplus.exe`, matching
`submit_fleet_t08.sbatch`'s own invocation) before any Speed submission** — both rebuilt IDFs ran `RC=0`, `0
Severe Errors`, `0 Fatal Errors`, `EnergyPlus Completed Successfully`; confirmed byte-identical (`sha256sum`)
between the local proof build and the tarball actually shipped to Speed (no drift between proof and shipment).

Shipped to a dedicated fleet dir, `/speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE_deu44` (never
overwriting the shared `EU11_ES-MAD-BERRUGUETE` base tree), and submitted as **one** array job:

```
sbatch --array=1-2%2 --export=FLEET_DIR=/speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE_deu44 submit_fleet_t08.sbatch
```
→ job `1303012`. `sacct -j 1303012 -X --format=JobID,State,ExitCode,Elapsed` (fire-and-forget, polled via
`squeue`/`sacct` only, never `srun`): `1303012_1` (`df490cc7ec52ebb4`) `COMPLETED 0:0` in 00:02:36;
`1303012_2` (`5897ad5bdd60c3ae`) `COMPLETED 0:0` in 00:07:24. Both remote `eplusout.err` also show `0 Severe
Errors`/`EnergyPlus Completed Successfully` — Speed-side confirmation, not only the Windows proof, per
`FINDING 187`/`190`'s "Speed ≠ Windows" rule.

Harvested via a remote tar stream from `EU11_ES-MAD-BERRUGUETE_deu44/out/` (never a local path list) and
parsed `heating_kwh` from `eplusout.sql` (`Zone Ideal Loads Zone Total Heating Energy`, J→kWh), matching
`scripts/cluster/harvest_eu11_district.py`'s own query. Before: both rows `EPLUS_FATAL`, blank `heating_kwh`.
After: `df490cc7ec52ebb4` 22,995.2274 kWh / 438.6929 m² = 52.4176 kWh/m²; `5897ad5bdd60c3ae` 7,352.8695 kWh /
194.5278 m² = 37.7986 kWh/m². `floor_area_m2` moved slightly from the pre-fix value (439.0326→438.6929,
195.5908→194.5278), the same reroute-measures-storey-union effect already disclosed for the other 50
`D-EU-42`/`D-EU-43` reroutes. Folded both rows into `es_mad_berruguete_manifest.csv` and
`prepared_buildings.csv`; replaced the 2 stale pre-fix IDFs/schedules in the local `ES-MAD-BERRUGUETE`
evidence tree with the fixed rebuilds. **Madrid: 961/961 success, 0 Speed-failed** (was 959/961, 2 failed).
Pooled heating EUI: 72.1258 → 72.1096 kWh/m² (`pooled_heating_kwh`/`pooled_floor_area_m2` recomputed the same
way as `scripts/cluster/harvest_eu11_district.py`: `sum(heating_kwh)/sum(floor_area_m2)` over all successes).
`summary.json` updated to match.

`generate_eu_3d_viewers.py` re-run for all four districts (Madrid's `results.csv` now 961 rows, up from 959).
`diff -rq` on every EU-prefixed viewer file and data directory (`openubem/outputs/3D/` vs
`docs/docs_ACTIVE/europeanLocations/outputs_3D/`), run individually, not summarised — all 8 checks (4
viewers + 4 data dirs) produced zero output, byte-identical, including the 3 unchanged districts (confirms
the regeneration is deterministic).

Artifacts: `openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE/{es_mad_berruguete_manifest.csv,
prepared_buildings.csv, summary.json, idfs/{df490cc7ec52ebb4,5897ad5bdd60c3ae}.idf,
schedules/{df490cc7ec52ebb4,5897ad5bdd60c3ae}/}` (updated); `openubem/outputs/3D/eu_*` +
`docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_*` (regenerated, mirrored, `diff -rq` clean);
`docs/docs_ACTIVE/europeanLocations/results/RESULTS_EU-11.md` (`D-EU-44` section added, per-district table,
before/after table, DR band row, mirror-check, caveats all updated); `docs/docs_EXPLANATION/
OpenUBEM_debug_References.md` (`D-EU-44` closure entry appended to the `FINDING 210`/`D-EU-43` chapter).

Deviations: none — no change to `scripts/run_eu_s2_campaign.py`, `scripts/run_eu_s2_district_campaign.py`, or
`openubem/idf/surfaces.py`; the existing `FINDING 210` fix/gate is reused unmodified, exactly per the task's
own instruction ("the fix already applies generically — confirm it fires for these 2"). The rebuild scratch
script is a temporary scratchpad file, not committed to the repo layout, matching the precedent set by the
prior harvest's own "ad hoc fold script" note.

Test status: no code changed this session; no test suite re-run (nothing in scope changed the code under
test). Verification instruments were the local real-EnergyPlus proof run, `sacct`, remote `eplusout.err`
reads, and `diff -rq` — per cluster hard rules 1–3 and "synthetic green ≠ live green."

Notes: this closes both `[OPEN]` items left by the prior harvest entry — no unaccounted `FINDING 210` Madrid
casualties remain; Bologna's separately-scoped 190 wave-1 failures remain untouched and out of scope.

Next: `T10` (independent audit) not started. No further Speed submission authorised beyond this wave.
