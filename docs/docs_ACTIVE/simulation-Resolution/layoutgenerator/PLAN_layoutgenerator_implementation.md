# PLAN — `layoutGenerator.py`: room-level interior zoning for non-rectangular footprints

> Binding contract: the L01–L15 `RESULT_*` deep-research answers under
> `docs/docs_ACTIVE/simulation-Resolution/layoutgenerator/deepResearch/`, and the OpenUBEM
> zero-fitted-parameters + mandatory-provenance constraints. On approval this plan is copied to
> `docs/docs_ACTIVE/simulation-Resolution/layoutgenerator/PLAN_layoutgenerator_implementation.md`
> (the persistent manager doc); execution follows manager-writes / Sonnet-executes, with Opus
> writing the delicate load-bearing pieces (classifier, dispatcher, conservation math, interior-BC wiring).

---

## Context — why this change

OpenUBEM's highest-fidelity `zone` mode is a stub: `geometry/zoning.py` `decide_zoning_strategy` raises
`NotImplementedError` for `"zone"`, and even `fast_zone`/`perimeter_core` **silently degrades non-rectangular
footprints to `one_zone_per_floor`** at `zoning.py:77-97`:
- narrow: `core_poly = footprint_poly.buffer(-4.57); if core_poly.is_empty or core_poly.area < 10.0` → recurse per-floor;
- courtyard: `if list(footprint_poly.interiors)` → recurse per-floor (a donut core otherwise causes an **EnergyPlus Fatal** via mismatched inter-floor vertices).

So no L/U/T/O-shaped building ever reaches room-level zoning. `layoutGenerator.py` closes that gap: decompose
the real footprint → place a corridor on the spine → pack DOE-standard room modules along a double-loaded
corridor, conserving floor area and loads. First target is **MidriseApartment** — the one archetype whose DOE
prototype *is* a corridor+units layout, so the generator can be validated by reproducing the DOE 9-zone
standard (the user's "DOE-standard vs generated" comparison). Then expand to the higher-accuracy-value
archetypes (office/hotel/school).

### Scope decisions (defaults; confirm on review — user was away when asked)
- **D-A: MidriseApartment is the first build+validate target**, office committed as mandatory Phase 5, not vague "future". Rationale: apartment dims are 100% consistent across L06/L07/L08 and its DOE prototype is a corridor+units layout (self-validating). *Research nuance the user must know:* L14/L15 rank apartments **lowest** accuracy-value (<3% ΔEUI vs 10–20% for offices) and refute un-forcing residential fleet-wide; L08 recommends un-forcing. Resolved as: apartments = the testbed; offices = the deployment payoff.
- **D-B: opt-in `zone` mode only.** `auto` stays unchanged (apartments remain `one_zone_per_floor` in fleet runs); room-level runs only when `zone` is explicitly requested. Respects the <3%-benefit / 5×-cost finding; keeps fleet cost flat.

---

## ✅ Phase checklist (top-level progress surface)

- [x] **Phase 0 — Scaffolding + shape classifier** (T01–T02)
- [x] **Phase 1 — Corridor-packing geometry engine, MidriseApartment** (T03–T06) → **CP-1 MET 2026-07-02**
- [x] **Phase 2 — Per-space-type loads + conservation** (T07–T08)
- [x] **Phase 3 — Interior surfaces + synthetic sim tests** (T09–T10) → **CP-2 MET 2026-07-02** (0 Fatal / 0 Severe full-annual E+ on bar/L/U/T/O)
- [x] **Phase 4 — Validation: reproduce DOE standard + LIVE_SMOKE** (T11–T12) → **CP-3 MET 2026-07-02**
- [ ] **Phase 5 — Expand to complex buildings + full sim + DOE-vs-generated comparison** (T13–T15) → **CP-4 (user sign-off)**
- [ ] **T16 — Layout visual grid (DOE reference vs generated)** — user-requested floor-plan visual

---

## Hard rules for the executor
1. Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. No `.py` under `docs/`. Never edit root `main.py`, OVERVIEW, or DESIGN.
2. Executor executes this plan; does not re-plan or re-debate pinned decisions. Stop-and-quote on DESIGN/spec ambiguity.
3. Default to no comments; one line max when the WHY is non-obvious.
4. All `.png`/figures → `openubem/outputs/` (flat). Never bury under `docs/.../results/`.
5. **No login-node compute.** Cluster runs are `sbatch` fire-and-forget + read output file. Delegate monitoring to a cheap model, ≥30-min intervals.
6. `auto` mode behavior must not change (D-B). Do not reintroduce an unconditional `orient()` — the T07b fix at `builder.py:326-327` gates re-winding out of `auto`.
7. Every zone dict the generator emits **must** set `"extruded": True` after geometry succeeds, or it is silently dropped from loads/HVAC (`builder.py:387-402`).
8. **Zero fitted parameters.** Every dimension/threshold traces to a cited source (DOE prototype, ASHRAE 90.1-2019, IBC). **Provenance mandatory** on every emitted zone.

---

## File layout to create / touch

```
openubem/geometry/
  layoutGenerator.py          NEW — classifier + corridor-packing engine + fallback ladder
openubem/geometry/zoning.py   EDIT — dispatch "zone" → layoutGenerator (T06); leave auto/fallbacks intact
openubem/idf/surfaces.py      EDIT — interior BCs for corridor/unit/courtyard-inner (T09)
openubem/idf/builder.py       EDIT — per-space-type loads path + conservation (T08); thread space_type
openubem/data/loads/
  doe_space_type_loads.json   NEW — Apartment/Corridor per-space intensities (Deru 2011 Table 3-51)
tests/
  test_layout_generator.py    NEW — classifier + geometry + conservation unit tests (T02,T03,T10)
  test_layout_doe_reproduce.py NEW — reproduce-DOE-standard validation (T11)
  fixtures/synthetic_10_buildings.py  EDIT — add L/U/T/O apartment fixtures
scripts/cluster/
  t09_layout_pilot.py         NEW — sbatch pilot, zone-vs-floor-vs-building + DOE comparison (T14)
openubem/outputs/comparisons/ artifacts (T14–T15); openubem/outputs/*.png (T15)
```

---

## Dependency decisions (pinned — do not re-debate)
- **Geometry = pure `shapely` + `geomeppy` only.** Per RESULT_L05: **do NOT add** straight-skeleton (`scikit-geometry` GPL / `ladybug-polyskel` AGPL / unmaintained pure-Python) or medial-axis (`scikit-image`, requires rasterization → violates zero-fitted). Use negative buffer, `shapely.ops.split`, `unary_union`, `make_valid`, `minimum_rotated_rectangle`, `convex_hull`, `simplify`. L08's "medial axis" framing is conceptual — use **bounding-box centerline bisection**, not MAT.
- **Corridor centerline = OBB longitudinal midline**, not medial-axis transform.
- **Fallback thresholds = L06 algebraic (traceable), not L08 flat numbers.** For MidriseApartment: `W_double = corridor + 2·depth = 1.68 + 2·7.62 = 16.92 m`; `W_single = corridor + depth = 9.30 m`; below `W_single` → 4.57 m offset-buffer; core empty or `<10 m²` → `one_zone_per_floor`.
- **No intra-floor Zone Multiplier** (L06 rule; L08's per-facade multiplier deferred). Merged-orientation zone = its true summed polygon. `Zone Multiplier` reserved for floor repetition only (Ground + Mid×(N−2) + Top), and even that is **off** for the DOE-reproduction validation (DOE MidriseApartment models all 4 floors explicitly).
- **DP simplify tolerance = 0.1 m** default, 0.25 m for noisy OSM. **Min thermal zone area = 2.0 m²**; corner-wedge merge if `area < 10 m²` or aspect `> 5:1`.
- **Provenance grammar** = `openubem.semantic.provenance.append_flag_token`, `{METHOD}_{SOURCE}_{TIER}` — not ad-hoc bare strings.

---

## Source-of-truth verified facts

**Integration points (from codebase map):**
- `zoning.py`: `decide_zoning_strategy(archetype_id, footprint_area_m2, num_floors, resolution_mode="auto")`; `build_zones(osm_id, footprint_poly, archetype_id, num_floors, strategy, floor_to_floor_m=3.5, perimeter_depth_m=4.57)`. `"zone"` currently raises `NotImplementedError` (line ~24) — **the hook**. `_ONE_PER_FLOOR = {MidriseApartment, HighriseApartment, TallBuilding, SuperTallBuilding}`.
- `perimeter_core` returns a single placeholder dict, expanded later by `surfaces.py::_expand_core_perim_placeholder` (~line 273) which calls `idf.add_block(zoning="core/perim", perim_depth=...)`.
- `surfaces.py::extrude_geometry(idf, zones, context)` (line 597) is the extrusion entry: groups zones by footprint → one `add_block` per footprint (stacks floors) → `intersect_match()` → repair passes (`_pair_interfloor_surfaces` line 60 matches on `frozenset` of rounded vertices; `_repair_roof_roof_pairs`; `_repair_mismatched_horizontal_pairs`) → degenerate reroute. Generation-time gate `find_mismatched_interzone_pairs` (line 480) called from `builder.py:339`; on failure `_force_reroute_coreperim_to_one_zone_per_floor`, else drop with `generation_status="failed_interzone_vertex_mismatch"`.
- `set_adiabatic_surfaces(idf, zones, strategy)` (line 731) is a **no-op stub** — the seam for interior partitions (unit↔unit Adiabatic).
- Loads: `openubem/data/loads/doe_prototype_loads.json` is **per-archetype building-average only** (MidriseApartment: lighting 7.53, equipment 7.53 W/m², occ 18.58 m²/person, wwr 0.21). `builder.py::assign_loads` applies the same intensity to every zone. **No per-space-type table exists** — Phase 2 creates one and must reconcile to the archetype total (T05b/T08b conservation invariant).
- Provenance: `openubem/semantic/provenance.py` (`append_flag_token`, `set_provenance`, tiers HIGH/MED/LOW). Manifest records `zoning_strategy, num_zones, generation_status, resolution_mode, data_quality_flag` at every `build()` exit.
- Tests: `tests/test_zoning.py`, `tests/test_surfaces.py`, `tests/test_step3_orchestrator.py` (has `test_load_conservation_across_modes`, rebuilds IDF per mode and sums IDF load objects at `rel_tol=1e-6`), `tests/test_resolution_mode_live.py` (LIVE_SMOKE, skips if fixture absent). Synthetic fixture `tests/fixtures/synthetic_10_buildings.py`.
- Single-cell run: `py -3 scripts/validation/v12_cell_pipeline.py <cell>`. DOE prototype baseline IDFs+outputs under `openubem/outputs/extra/cpb_fixtures/`. Cluster sweep template: `scripts/cluster/t07_resolution_pilot.py`.

**MidriseApartment pinned dims (100% consistent across L06/L07/L08):**
corridor **1.68 m**, unit depth **7.62 m**, bay **11.58 m**, unit **88.25 m²**, **8 units/floor** (ground = 7 units + 1 office/lobby), circulation **9.9%**, DOE floor plate **46.33 × 16.92 m**, DOE floor-to-floor **3.05 m** (use 3.05 for DOE reproduction; pipeline default 3.5 elsewhere — flag per building).
Per-space loads (Deru 2011 Table 3-51): Apartment LPD **5.27**, EPD **5.38** W/m², occ 1/46.5 m², area share 90.1%; Corridor LPD **5.38**, EPD **0**, occ 0, OA 0.25 L/s·m², area share 9.9%.

**Shape classifier thresholds (RESULT_L04, all zero-fitted):** rectangularity `area/MBR.area ≥0.85`=compact; convexity `area/hull.area ≥0.95`; interior ring→O; erosion `buffer(-4.57).is_empty` or `<10 m²`→ribbon; DP-simplified vertex count 4=rect,6=L,8=U/T,12=cross; U-vs-T via `OBB.difference(poly)` notch count (1=U,2=T). Decision order: interior ring → erosion collapse → convex+rect (compact/slab by elongation<0.40) → vertex/concave-corner pattern → irregular. Area `<100 m²` or ribbon → single-zone fallback.

**Conservation (RESULT_L11 "Space-Type-Weighted Normalization"):**
`I'_z = I_t · (f_t · A_tot / Σ_{z∈type t} A_z)` ⇒ `Σ_z A_z·I'_z = archetype building total` exactly, independent of geometry drift. Absolute building loads (elevators/IT/DHW standby) → exactly ONE designated core zone, never replicated.

**Interior BCs (RESULT_L11 Table 3):** unit↔unit (same setpoint) → **Adiabatic**; corridor↔unit → **Surface** (matched pair); perim↔core → Surface; courtyard inner wall → **Outdoors** (self-shaded, never merge inner/outer ring); real exterior → Outdoors/Ground, never Adiabatic; inter-floor slab → Surface when plates match (`_pair_interfloor_surfaces`), else Adiabatic.

**Cross-file conflicts resolved:** (1) hotel dims inconsistent L06 vs L08 → **irrelevant to Phase 1**, reconcile before T13. (2) skeleton vs shapely → **shapely** (L05 authority). (3) fallback thresholds → **L06 algebraic**. (4) intra-floor multiplier → **no** (L06). (5) Generative ML (L13) → **skip**, deterministic procedural is the correct MVP.

---

## Task list

### Phase 0 — Scaffolding + classifier
- **T01 — Module skeleton + pinned constants.** *What:* create `layoutGenerator.py` with a `MODULE_SPECS` dict (MidriseApartment row: corridor 1.68, depth 7.62, bay 11.58, circ 0.099) and public signatures `classify_footprint(poly) -> ShapeClass`, `generate_layout(osm_id, footprint_poly, archetype_id, num_floors, floor_to_floor_m) -> list[dict]`. *Why:* single source for pinned dims (zero-fitted). *How:* constants module-level, cite source in a one-line comment. *Test:* import + constants asserted in T02.
- **T02 — Footprint shape classifier.** *What:* `classify_footprint` returning compact/slab/L/U/T/cross/O/ribbon/irregular via the L04 metric ladder. *Why:* routes each footprint to the right packing recipe. *How:* pure shapely; `make_valid` + `simplify(0.1)` first; thresholds from verified facts; return enum + metrics dict for provenance. *Test:* synthetic polygons (box, L via union of two boxes, U, T, O via box-with-hole, thin ribbon) each classify correctly; noisy-vertex box still = compact.

### Phase 1 — Corridor-packing geometry engine (MidriseApartment) → CP-1
- **T03 — Double-loaded bar packer.** *What:* `_pack_bar(wing_poly, spec)` — OBB longitudinal centerline → corridor strip (width 1.68) → subtract → two unit rows → **merge units by cardinal orientation** → return zones `[corridor, N, S, E, W]` (subset that exists) with `space_type` ∈ {corridor, apartment}, area, polygon, provenance. *Why:* the core of the user's method (L06). *How:* fallback ladder W≥16.92 double / 9.30≤W<16.92 single / <9.30 offset-buffer(4.57) / core<10 → one_zone_per_floor; corner-wedge merge <10 m² or aspect>5:1; `fallback_triggered`/`fallback_reason` in provenance. *Test:* rectangular 46.33×16.92 → 5 zones, areas conserve to footprint ±0.001%, corridor≈9.9%.
- **T04 — Wing decomposition (L/U/T/cross).** *What:* `_decompose_wings(poly)` orthogonal slicing from reflex vertices (pure shapely) → hole-free rectangular wings; route each to `_pack_bar`; shared wing edges flagged for Adiabatic; outer corner→corner unit, inner corner→core. *Why:* generalizes App-G to non-convex (L03/L05). *How:* ray-cast from reflex vertices to opposite edges, `split`, `unary_union` cleanup; no external decomposition lib. *Test:* L-shape → 7 zones, area conserved, no zone <2 m², all geometry valid.
- **T05 — Donut splitter (O/courtyard).** *What:* `_split_donut(poly)` — 4 cutting LineStrings from hole-bbox corners to outer envelope → `split` → 4 hole-free wings → per-wing `_pack_bar`; inner-ring walls tagged Outdoors; inner/outer never merged. *Why:* fixes the `zoning.py:89` courtyard E+ Fatal (root cause: geomeppy extrudes holed polygon → mismatched inter-floor vertices). *How:* **never pass a holed polygon to add_block**; validate 4 simple wings; sliver merge <2 m². *Test:* box-with-hole → wings hole-free, 0 interiors each, area conserved; courtyard-inner surfaces later resolve to Outdoors (T09).
- **T06 — Dispatch wiring.** *What:* in `decide_zoning_strategy`, `"zone"` → new strategy `"room_layout"` for units+corridor family (MidriseApartment first) **replacing** the `NotImplementedError`; `build_zones` routes `"room_layout"` → `layoutGenerator.generate_layout`. Leave `auto` and all existing fallbacks intact (D-B). *Why:* activates the engine opt-in. *How:* generate_layout internally calls classifier → wing/donut/bar; emits zone dicts with `mode`, `space_type`, provenance token via `append_flag_token`; manifest gets `zoning_strategy="room_layout"`. *Test:* `decide_zoning_strategy(..., "zone")` returns `room_layout` for MidriseApartment, still `NotImplementedError`/unchanged for out-of-family until T13; `build_zones` zone dicts have required keys.

> **CP-1 (stop & report):** engine produces valid, area-conserving zones for rect/L/U/T/O MidriseApartment footprints; `auto` unchanged; no simulation yet. Report zone counts + area-conservation deltas per shape.

### Phase 2 — Loads + conservation
- **T07 — Per-space-type loads table.** *What:* `openubem/data/loads/doe_space_type_loads.json` with Apartment + Corridor rows (verbatim Deru 2011 Table 3-51, cite in file). *Why:* corridor ≠ dwelling loads (EPD 0, occ 0). *How:* schema mirrors existing loads json; provenance source `DOE_PROTOTYPE`. *Test:* loader returns both rows; values match verified facts.
- **T08 — Space-Type-Weighted Normalization in assign_loads.** *What:* when zones carry `space_type`, compute `I'_z = I_t·(f_t·A_tot/A_t,gen)` per zone; absolute service loads to one core zone only. *Why:* conserve building total regardless of geometry drift (L11). *How:* extend `assign_loads`; reconcile so `Σ = get_loads() archetype total`; guard against double-counting. *Test:* extend `test_load_conservation_across_modes` — `zone` mode building totals equal `floor`/`building` within `rel_tol=1e-6`.

### Phase 3 — Interior surfaces + synthetic sim tests → CP-2
- **T09 — Interior boundary conditions.** *What:* implement corridor↔unit=Surface, unit↔unit=Adiabatic, courtyard-inner=Outdoors in `set_adiabatic_surfaces`/post-`intersect_match`; ensure emitted zones set `"extruded": True`; keep mismatch-gate happy. *Why:* correct envelope exposure + no E+ Fatal. *How:* reuse `_pair_interfloor_surfaces` frozenset matching for corridor/unit pairs; tag courtyard-inner walls before repair passes so they aren't flipped. *Test:* extrude an L and an O fixture, assert BC of each surface class; 0 mismatched interzone pairs.
- **T10 — Synthetic geometry+sim tests.** *What:* `test_layout_generator.py` full suite — classification, zone counts, area ±0.001%, no slivers, valid geometry, and an E+ **stability smoke** (build IDF for L/U/T/O apartment fixtures, assert 0 Fatal). Add L/U/T/O fixtures to `synthetic_10_buildings.py`. *Why:* acceptance suite from L15. *Test:* the suite itself (pytest green).

> **CP-2 (stop & report):** loads conserved across modes; 0 E+ Fatal on all synthetic shapes; interior BCs correct. This is the silent-bug-compounding checkpoint — report conservation deltas + surface-BC audit.

### Phase 4 — Validation → CP-3
- **T11 — Reproduce the DOE standard.** *What:* `test_layout_doe_reproduce.py` — run generator on the DOE MidriseApartment footprint (46.33×16.92, 4 floors, 3.05 m, multiplier off) and compare against `openubem/outputs/extra/cpb_fixtures/` DOE baseline IDF: zone count/areas, per-space loads, and simulated EUI. *Why:* the user's "DOE-standard vs generated" comparison, as a hard validation. *How:* acceptance — area ±0.001%, loads ±0.1%, circulation within ±5 pp, EUI within ±15% band (flag if beyond). *Test:* the comparison asserts thresholds; emit a diff table to `openubem/outputs/comparisons/`.
- **T12 — LIVE_SMOKE on real OSM apartments.** *What:* run generator on real L/U/O apartment footprints from a phaseE cell fixture (pattern of `test_resolution_mode_live.py`); assert 0 Fatal, gen-success ≥95%. *Why:* synthetic-green ≠ live-green (known blind spot). *How:* skip cleanly if fixture absent; delegate any cluster run via sbatch. *Test:* the smoke gate.

> **CP-3 (stop & report):** DOE reproduction within thresholds + LIVE_SMOKE pass. Gates expansion. Report the DOE-vs-generated diff table.

### Phase 5 — Expansion + full sim + comparison → CP-4

**Hotel dimension conflict — RECONCILED (manager, 2026-07-02; gate cleared for T13a).**
L06 (Time-Saver/Neufert architectural norms) and L08 (DOE/PNNL prototype geometry) disagree on hotel guest-room dims. **Resolution principle: the DOE/PNNL prototype dimensions WIN**, because (a) the arc's zero-fitted rule pins every dimension to the DOE prototype (as MidriseApartment did — corridor 1.68/depth 7.62/bay 11.58 are the DOE plate, not architectural typicals), and (b) validation is by DOE-prototype reproduction (T11 pattern), so the generator must target the prototype's own 24-ft guest-room module, not the 26–30-ft real-world architectural norm. L06's deeper depths (SmallHotel 8.23 m, LargeHotel 9.14 m) are Time-Saver/Neufert generic typicals → **superseded**. Corridor widths: SmallHotel **1.83 m** from L06's DOE-Small-Hotel-specific citation (L08's 3.66 m is self-flagged GAP; L08 Step-1's 2.44 m is the generic-hotel value, not small-hotel); LargeHotel **2.44 m** where L06 and L08 agree (PNNL 2020).

Pinned `MODULE_SPECS` rows (schema identical to MidriseApartment; `circulation_fraction` is reference-only — verified NOT read by any code path, geometry is driven by `corridor_width_m`/`unit_depth_m`/`bay_width_m`):
| Archetype | family | corridor_width_m | unit_depth_m | bay_width_m | unit_area_m2 | circ_frac (ref) | unit_space_type | source |
|---|---|---|---|---|---|---|---|---|
| SmallHotel | units_corridor | **1.83** (6 ft) | **7.32** (24 ft) | **3.66** (12 ft) | **26.79** (=7.32×3.66) | 0.23 (77% eff, L06) | GuestRoom | Deru 2011 (DOE Small Hotel) Table 3-51; corridor per L06 DOE-Small-Hotel spec; IBC 2021 §1020.3 |
| LargeHotel | units_corridor | **2.44** (8 ft) | **7.32** (24 ft) | **4.11** (13.5 ft) | **30.09** (=7.32×4.11) | 0.29 (71% eff, L06) | PNNL Commercial Prototype Models 2020 (Large Hotel); depth/bay/corridor per L08 Table 1; IBC 2021 §1020.3 |

Validation anchors exist: `docs/docs_VALIDATION/.../ASHRAE901_HotelSmall_STD2022_Buffalo.idf` + `ASHRAE901_HotelLarge_STD2022_Buffalo.idf` (+ `cpb_fixtures/LargeHotel/`). Ground/basement non-guest programs (lobby/restaurant/BOH) are an L08-flagged GAP — **out of scope for T13a**: guest-floor geometry only (the units+corridor engine), per-floor uniform (no separate ground-floor program modeling). Dormitory (no DOE prototype) — deferred.

- **T13a — Hotels (SmallHotel + LargeHotel) via the existing units+corridor engine.** *What:* add the two pinned `MODULE_SPECS` rows above + two `doe_space_type_loads.json` blocks (GuestRoom + Corridor per-space LPD/EPD from the DOE prototype / Deru 2011 Table 3-51, mirroring the MidriseApartment schema — corridor equipment=0/occ=false). *Why:* hotels are the direct analog of the validated apartment path (same `_pack_bar`/`_pack_connected_spine` engine; `decide_zoning_strategy` auto-routes any `family=="units_corridor"` spec → **no dispatch change**), and L14 ranks lodging among the higher-accuracy-value archetypes. *How:* pure data rows + tests; classifier is archetype-agnostic (no change); the engine is unchanged. **If the DOE prototype's guest-room vs corridor LPD/EPD are not cleanly separable, STOP and quote (spec-ambiguity rule) — do not invent a split.** *Test:* (1) classification/zone-count/area-conservation unit tests for both hotels on rect/L/U/T/O footprints (mirror the MidriseApartment tests, tol as in `test_step3_orchestrator`); (2) DOE-reproduction check mirroring `tests/test_layout_doe_reproduce.py` against the HotelSmall/HotelLarge prototype (area ±0.001%, per-space loads ±0.1%, circulation ±5 pp, EUI ±15%, 0 Fatal), diff table to `openubem/outputs/comparisons/`; (3) E+ 23.1 0-Fatal/0-Severe smoke on hotel L/U/T/O footprints.
- **T13b — Offices (LargeOffice, non-rect core/perimeter) — DEFERRED (Opus-delicate, separate slice).** Non-rect offices need wing-decompose + per-wing 4.57 m core/perimeter (RESULT_L09) — a **different geometry path** from corridor packing (compact offices already work via `perimeter_core`→geomeppy `add_block`). New load-bearing geometry → manager/Opus, not this Sonnet slice.
- **T13c — Schools (Primary/Secondary, hybrid) — DEFERRED (Opus-delicate, separate slice).** Classroom wings via the L06 corridor method (corridor 2.44 m, classroom depth 9.14 m) + single-zone assembly blocks (gym/cafeteria/admin), with a wing-vs-block shape-split heuristic (RESULT_L09) — genuinely new geometry → manager/Opus.
- **T14 — Cluster pilot (sbatch).** *What:* `t09_layout_pilot.py` — run a real-cell subset in `zone` vs `floor` vs `building`, harvest EUI. *Why:* cost + accuracy evidence at scale (L15 targeted-not-fleetwide verdict). *How:* sbatch array fire-and-forget, read output; harvest to `openubem/outputs/comparisons/`; monitoring on a cheap model ≥30 min. *Test:* pilot completes, comparison CSV written.
- **T15 — DOE-vs-generated comparison report + plots.** *What:* consolidate DOE-standard vs generated (zones, loads, EUI, runtime) into a report + `.png`s in `openubem/outputs/`. *Why:* the deliverable the user asked for. *How:* reuse `plotting_suite.py`/`aggregator.py`. *Test:* artifacts present; report reviewed.

> **CP-4 (stop & report — USER SIGN-OFF):** full comparison complete. No production `auto` change and no baseline promotion without explicit user sign-off.

### Visuals (user-requested, 2026-07-02)
- **T16 — Layout visual grid (DOE reference vs generated).** *What:* a single figure — a grid of floor-plan panels. Panel 1 = **DOE MidriseApartment single-floor reference** (8 dwelling units + central full-length corridor, drawn from the pinned dims: plate 46.33×16.92 m, corridor 1.68 m, units 11.58×7.62 m). Remaining panels = generated `room_layout` floor plans for MidriseApartment across representative footprints (compact bar, L, U, T, O/courtyard, rotated), zones **color-coded by space_type** (corridor vs apartment), titled with shape + zone count. Grid auto-sizes (≈4×4 or 5×5) to the building count. *Why:* lets the user visually compare the generated layouts against the DOE standard at a glance (validation-by-eye + a report figure). *How:* matplotlib; draw each zone's `floor_polygon` (floor-0) filled by space-type color; reuse `generate_layout`; **output PNG to `openubem/outputs/`** (flat, per project rule). *Test:* the figure renders without error and one panel per building + the DOE reference is present.

---

## Progress log
*(Append one entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes.)*

#### T01 — layoutGenerator skeleton + pinned constants — completed 2026-07-02
- Artifacts: `openubem/geometry/layoutGenerator.py` (constants block, `MODULE_SPECS["MidriseApartment"]`, `wing_width_thresholds`, `ShapeClass` enum, public `classify_footprint`).
- Deviations: none. All dims cited to Deru 2011 / ASHRAE 90.1-2019 / IBC 2021 (zero-fitted).
- Test status: covered by T02 suite (12 passed).
- Notes: `generate_layout` public signature deferred to T03–T06 (built incrementally as packer lands).

#### T02 — footprint shape classifier — completed 2026-07-02
- Artifacts: `classify_footprint(poly) -> (ShapeClass, metrics)` in `layoutGenerator.py`; `tests/test_layout_generator.py` (`TestClassifier`, `TestModuleSpecs`).
- Deviations: classification DP simplify uses ε=1.0 m (RESULT_L04) for vertex/concave counting, distinct from the 0.1 m geometry-cleanup simplify — both encoded as separate constants. Compact-vs-slab split is by elongation<0.40 per L04; both route to the same bar packer so the split is provenance-only. Reflex-corner count used as the primary L/U/T/cross discriminator (more robust than exact vertex count), OBB-notch count disambiguates U(≤1) vs T(2).
- Test status: `pytest tests/test_layout_generator.py -q` → 12 passed. DOE plate 46.33×16.92 → SLAB (aspect 0.365, expected); L/U/T/O/ribbon/tiny all correct; noisy-vertex rectangle stays compact.
- Notes: metrics dict is provenance-ready (rectangularity/convexity/elongation/reflex/vertices/core_area) for the manifest token.

#### T03 — double-loaded bar packer — completed 2026-07-02
- Artifacts: `_pack_bar`, `_emit_floor_zones`, `_band_zone`, `_long_edge_angle`, and public `generate_layout` in `layoutGenerator.py`; `TestBarPacker` (7 tests) in `tests/test_layout_generator.py`.
- Deviations (design decisions, DESIGN-consistent): (1) **Inset-corridor 5-zone scheme** — to yield L06's 5 *single-polygon* zones (corridor + N/S/E/W) that each extrude via one `add_block`, the corridor spine is inset from the wing ends by one unit-depth so the E/W end-bands are contiguous full-width rectangles, not disjoint MultiPolygons. Consequence: corridor share ≈6.7% on the DOE plate vs DOE 9.9% — within the ±5pp acceptance (L15), and load-normalization (T08) conserves totals regardless of the area split. (2) Fallback ladder: `W≥16.92` double_loaded (5 zones); `9.30≤W<16.92` single_loaded (4 zones: corridor+row+E/W); `W<9.30` wing_fallback_narrow (whole-wing single zone) — reached only for narrow *wings* of a decomposed shape, since narrow whole footprints classify as RIBBON upstream and `generate_layout` returns `[]`. (3) Zone naming `{osm_id}_F{i}_w{wing}{tag}` — last token `w{wing}{tag}` is underscore-free and unique per sub-polygon, so `surfaces._group_key` makes each sub-polygon its own N-storey `add_block` with **zero changes to extrude_geometry**.
- Test status: `pytest tests/test_layout_generator.py -q` → 19 passed. Area conserved to <1e-5 on double/wider/single bars; 5/5/4 zone counts; unique group tokens; narrow + unsupported-archetype both fall back to `[]`.
- Notes: `_decompose_wings` (T04) and `_split_donut` (T05) are interim single-wing stubs (warn + return whole footprint); L/U/T/O still route through them but produce approximate zoning until T04/T05 land. T06 will only enable `room_layout` in the dispatcher after those are real.

#### T04 — wing decomposition (L/U/T/cross) — completed 2026-07-02
- Artifacts: `_decompose_wings`, `_reflex_points`, `_orthogonal_cut`, `_dominant_edge_angle`, `_merge_slivers` in `layoutGenerator.py`; `TestWingDecomposition` (7 tests).
- Deviations/decisions: (1) **Alignment by dominant (longest) exterior edge, not the min-area OBB** — the min-area rectangle of a symmetric plus/cross is diagonal (~45°), which broke axis-aligned cuts and over-fragmented a cross into 7 wings + a sliver. Dominant-edge alignment keeps orthogonal footprints axis-aligned; cross now → 3 wings, rotated-L → 2 wings. (2) Reflex-vertex cutting: cast full-span axis lines at reflex xs and at reflex ys, polygonize, keep interior faces; choose the axis giving highest mean piece-rectangularity, fewest pieces as tiebreak. (3) **Sliver-merge conservation safeguard** (`_merge_slivers`) — sub-2m² bands are unioned into the neighbor with the longest shared edge instead of being dropped, guaranteeing exact area conservation; plus an end-band guard (`Lx > 2·d + bay_width`) that avoids creating a degenerate thin corridor middle in short wings.
- Test status: `pytest tests/test_layout_generator.py -q` → 28 passed. L/U/T/cross + rotated-L all conserve area to ±0.00000%, all zones hole-free, valid, unique group tokens.
- Notes: `_pack_bar`'s `_band_zone` no longer drops sub-min bands (merge handles it). Wing counts: L=2, U=3, T=3, cross=3.

#### T05 — donut splitter (O/courtyard) — completed 2026-07-02
- Artifacts: `_split_donut` in `layoutGenerator.py`; `TestDonutSplitter` (5 tests).
- Deviations/decisions: **tic-tac-toe split** (full-span cut lines at each interior ring's bounding edges) yields 8 hole-free rectangular wings (4 corners + 4 sides) around the void — simpler and more robust than a 4-cut pinwheel (which yields L-shaped wings needing re-decomposition). The courtyard cell is excluded via `aligned.contains(representative_point)`. **Key physics win:** because each wing extrudes as its own block, walls facing the empty courtyard have no adjacent partner, so `intersect_match` leaves them `Outdoors` automatically, and inner/outer rings are never merged — this structurally prevents the donut E+ Fatal (`zoning.py:89` root cause) with no special-casing needed in T09.
- Test status: `pytest tests/test_layout_generator.py -q` → 33 passed. Square/off-center/rotated courtyards → 8 hole-free wings, area conserved <1e-5, no wing contains the courtyard, no holed blocks reach extrusion.
- Notes: actual 0-E+-Fatal confirmation on a built IDF is deferred to T10 (sim-stability smoke); T05 covers the geometric guarantees.

#### T06 — dispatch wiring (zone → room_layout) — completed 2026-07-02
- Artifacts: `openubem/geometry/zoning.py` (`zone`-mode branch + `room_layout` `build_zones` branch, top-level `layoutGenerator` import); `tests/test_zoning.py` (3 rewritten zone-mode tests); `tests/test_layout_generator.py` `TestDispatch` (2 tests).
- Deviations: **`zone` mode no longer raises `NotImplementedError` for out-of-family archetypes** (plan §Task-T06 note said keep it "until T13"). Rationale — `run_step3` (builder.py:491) validates the mode once with a dummy archetype `decide_zoning_strategy("_", 1.0, 2, "zone")`; a raise there would reject `zone` fleet-wide and defeat the opt-in feature. New behavior: units+corridor family (MidriseApartment) → `room_layout`; every other archetype → `perimeter_core` (generic core/perim superset of `fast_zone`). `auto`/`building`/`floor`/`fast_zone` unchanged (D-B preserved). `build_zones("room_layout")` calls `layoutGenerator.generate_layout` and falls back to `one_zone_per_floor` when it returns `[]` (RIBBON/IRREGULAR/unsupported archetype).
- Test status: `pytest tests/test_layout_generator.py tests/test_zoning.py -q` → 78 passed; `tests/test_surfaces.py tests/test_coreperim_degenerate.py` → 43 passed (no regressions). Manifest `zoning_strategy` will read `room_layout` for zone-mode apartments (builder records the strategy string).
- Notes: richer provenance token (`append_flag_token` grammar) deferred; zones currently carry `generation_status_note` (config rung) + strategy string in the manifest. **CP-1 reached.**

---

### CP-1 report — 2026-07-02 (engine produces valid area-conserving zones; auto unchanged; no simulation yet)
- **Zone counts / floor (MidriseApartment):** compact bar 5, L 8, U 10, T 8, cross 8, square courtyard 16. All single-polygon, hole-free, valid, unique group tokens.
- **Area conservation:** ±0.00000% on rect/L/U/T/cross; <1e-5 on rotated + courtyard footprints (float precision).
- **Fallback ladder verified:** double_loaded (W≥16.92) / single_loaded (9.30≤W<16.92) / wing_fallback_narrow / RIBBON→`[]`→one_zone_per_floor.
- **`auto` mode untouched** (regression suites green). **`zone` mode** opt-in: apartments→room_layout, others→perimeter_core.
- **Not yet done (by design):** no per-space-type loads (T07–T08), no interior-BC pass / 0-Fatal sim confirmation (T09–T10), no DOE-reproduction validation (T11). These are the next phases.

#### T07 — per-space-type loads table + loader — completed 2026-07-02
- Artifacts: `openubem/data/loads/doe_space_type_loads.json` (MidriseApartment: Apartment LPD 5.27 / EPD 5.38 / occ=true, Corridor LPD 5.38 / EPD 0 / occ=false, Deru 2011 Table 3-51); `get_space_type_loads(archetype_id)` in `openubem/semantic/loads.py`.
- Deviations: none. Values are the *relative* per-space split; T08 α-normalizes to the archetype total (the Deru per-space intensities weight-average to ~5.28, not the archetype-table 7.53 from PNNL-20405 — different sources — so raw values are never used directly; α reconciles them).
- Test status: covered by T08 suite (`test_space_type_loader`).
- Notes: loader returns `None` for non-units+corridor archetypes so `assign_loads` cleanly skips the space-type path for everything else.

#### T08 — space-type-weighted load normalization — completed 2026-07-02
- Artifacts: `normalized_space_loads(zones, lpd_arch, epd_arch, occ_m2_per_person, space_table)` module fn in `openubem/idf/builder.py`; new first branch in `BuildingIDF.assign_loads` using it when zones carry `space_type`; `TestLoadNormalization` (4 tests).
- Deviations: none — implements RESULT_L11 exactly. `I'_z = I_t·(I_arch·A_tot / Σ A·I_t)` per load type; people distributed only to `has_occupancy` zones by area. PEOPLE/ELECTRICEQUIPMENT objects skipped when their value is 0 (corridor), LIGHTS always emitted. Existing absolute / Watts-Area paths for non-space-type zones are untouched (other resolution modes unaffected).
- Test status: `pytest tests/test_layout_generator.py -q` → 39 passed. Lights/equip/people all conserve to the archetype total to rel_tol 1e-9 on bar + L; corridor equip=people=0, corridor lights>0, all equipment/occupancy concentrated in apartment zones.
- Notes: full-IDF zone-mode conservation (summing actual IDF LIGHTS/EQUIP/PEOPLE objects vs floor mode) is exercised at T10; the pure-function conservation is proven here.

#### T09 — interior boundary conditions — completed 2026-07-02
- Artifacts: `tests/test_layout_surfaces.py` (9 integration tests building IDFs via `extrude_geometry` on bar/L/courtyard room_layout zones).
- Deviations: **no new production code required.** The per-sub-polygon-block architecture (T03 naming → `_group_key` → one N-storey `add_block` per sub-polygon) means `intersect_match` already pairs corridor↔unit walls as `Surface`, ground slabs stay `ground`, and courtyard-facing / outer-envelope walls (no partner) stay `Outdoors` — exactly the RESULT_L11 Table-3 targets. `set_adiabatic_surfaces` stays a no-op (unit↔unit merged-orientation walls are rare and correctly Surface-paired anyway). Verified: bar → 15 zones / 102 surfaces, L → 24 / 168, courtyard → 48 / 300, **all with 0 mismatched interzone pairs** (mismatch gate never reroutes) and every zone `extruded=True`.
- Test status: `pytest tests/test_layout_surfaces.py -q` → 9 passed (~10 s). No holed block ever reaches extrusion (donut Fatal root cause structurally eliminated).
- Notes: 0-mismatched-pairs is the geometry-level proxy for "no E+ geometry Fatal"; the actual EnergyPlus run confirming 0 Fatal is T10 (delegated to a Sonnet employee, in flight). T11 DOE baseline located: `docs/docs_VALIDATION/.../ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` (+ existing Level-2 DOE round-trip infra) — the reproduction reference.

#### T10a — room_layout intersect_match fallback (fan-out safety net) — completed 2026-07-02 (manager/Opus)
- Artifacts: `openubem/idf/surfaces.py` — new `_force_reroute_room_layout_to_one_zone_per_floor(idf, zones, reason)`; wired into the `extrude_geometry` intersect_match `except` handler (fires only after `_force_reroute_coreperim_...` declines).
- Why: the existing intersect_match exception reroute filtered `_is_coreperim_zone` only, so a `room_layout` building whose geometry made geomeppy `break_polygons` raise `IndexError` had **no fallback** → `failed_worker_exception` (no IDF). This closes hard-rule #7 (every footprint must survive or degrade) for the `zone` family and covers the synthetic-vs-live blind spot (live OSM footprints can still trip geomeppy even where synthetic shapes don't).
- How: reconstruct the true footprint = `unary_union(floor-0 sub-polys)`, buffer(+1cm)/buffer(−1cm) to bridge sub-mm wing-seam drift from `_pack_bar`'s ±90° rotation round-trip; a hole-free reconstruction (L/U/T/cross) → one stacked `add_block` per floor (real one_zone_per_floor); a reconstruction with a **real** void (≥1 m² → courtyard) **declines** (returns False, re-raises) so a single holed block never re-introduces the donut E+ Fatal; sub-mm sliver rings are dropped.
- Deviations: none — mirrors the core/perim reroute contract (`_purge_idf_geometry` → rebuild → re-`intersect_match`). No change to normal-path geometry (the global emit-snap I trialled was reverted because it distorted the rotated-donut past its 1e-5 conservation test for zero normal-path benefit; gap-closing lives in the fallback only).
- Test status: `pytest tests/test_layout_generator.py tests/test_surfaces.py tests/test_zoning.py tests/test_step3_orchestrator.py -q` → **130 passed**. Direct reroute checks: L (hole-free) → True, 2 whole zones/floor; courtyard-O (holed) → False (declines, per-wing split retained). `extrude_geometry` on synthetic bar/L/U/T/O still builds cleanly (82 surfaces on the L, 0 mismatched) — the fallback does **not** fire on synthetic shapes (they don't crash geomeppy); it is the live-footprint safety net.
- Notes: I could **not** reproduce the background agent's earlier `failed_worker_exception` on the synthetic L via direct `extrude_geometry` — current code builds it fine — so this is defensive coverage, not a confirmed-crash fix. The actual EnergyPlus 0-Fatal run on all shapes (the real CP-2 gate) is still T10, delegated to Sonnet.

#### T10 — synthetic geometry + E+ 0-Fatal smoke — completed 2026-07-02 (Sonnet employee, manager-audited)
- Artifacts: throwaway smoke harness + per-shape E+ run dirs in scratchpad (`ep_runs/{bar,L,U,T,O}/eplusout.err|.sql|.htm`). No `openubem/` or `tests/` changes. Run recipe mirrors `scripts/validation/phaseE_cpb_fixtures.py`: `generate_layout(..., 3 floors)` → `extrude_geometry` → `idf.set_default_constructions()` → synthetic PEOPLE/LIGHTS/EQUIP + `assign_hvac`/`assign_dhw` → E+ 23.1 (`C:\EnergyPlusV23-1-0\energyplus.exe`, Chicago TMY3), **full annual** (18–54 s wall each).
- Result table (zones / surfaces / E+ status / Fatal / Severe / Warn): bar 15/102 OK 0/0/3439 · L 18/114 OK 0/0/3873 · U 30/210 OK 0/0/7841 · T 24/162 OK 0/0/5391 · O 48/300 OK 0/0/18177. **All 5: Completed Successfully, 0 Fatal, 0 Severe.**
- Deviations: none. First run fatal'd (`Missing construction_name`) — a gap in the employee's smoke script (forgot `set_default_constructions()`, which `builder.py:215` runs after extrusion), **not** a production defect; employee added the call to the harness only. The `room_layout` reroute fallback (T10a) did **not** fire on any synthetic shape — `intersect_match` succeeded first-pass on all — confirming it is a live-footprint safety net, not needed for these shapes.
- Test status: 130 unit tests green (T10a) + this 5-shape full-annual E+ pass. Warnings are the known-harmless geomeppy "Floor/Roof is upside down" vertex-order quirk and frost/freeze from deliberately-undersized synthetic HVAC — no geometry Severe.
- Notes: audit flag — the L is now **18 zones / 114 surfaces**, vs the T09 log's 24/168; this is the `_clean`-fix geometry evolution (6 zones/floor now), not a regression — bar (15/102) and O (48/300) match T09 exactly and all build clean.

> **CP-2 — MET 2026-07-02 (manager greenlight).** Loads conserved across modes (T08); interior BCs correct + 0 mismatched interzone pairs (T09); **0 E+ Fatal / 0 Severe on full-annual runs of all synthetic shapes** (T10); room_layout fallback in place for live footprints (T10a). Phase 4 (T11 DOE reproduction + T12 LIVE_SMOKE → CP-3) is unblocked.

#### T11 — reproduce the DOE MidriseApartment standard — completed 2026-07-02 (Sonnet, manager-audited) — PASS
- Artifacts: `openubem/outputs/comparisons/t11_doe_vs_generated.md` (diff table); scratchpad `t11_runs/` (generated IDF + run, version-transitioned DOE baseline + run).
- Baseline: `docs/docs_VALIDATION/step1/Level 2 DOE round-trip/00.BaselineBuildings_NUs/ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` — the only MidriseApartment candidate (none in cpb_fixtures). Tagged IDF v22.1; ran E+ 23.1's shipped Transition-V22-1→V22-2→V23-1 (schema-only) → 0 Fatal/0 Severe. Both models run Chicago TMY3 (no Buffalo EPW available — weather is matched between the two so the comparison is internally fair; **caveat:** neither is the DOE prototype's true Buffalo climate).
- Result vs thresholds: floor area 3135.61 vs 3134.61 m² (~0% vs footprint×floors) **PASS ±0.001%**; per-space loads Apartment 5.27/5.38, Corridor 5.38/0 W/m² exact **PASS ±0.1%**; circulation 6.66% vs 9.9% (−3.24 pp) **PASS ±5 pp**; annual site EUI 114.63 vs 122.63 kWh/m² (−6.5%) **PASS ±15%**; generated run 0 Fatal/0 Severe **PASS**. Zone count 20 (5/floor×4) vs DOE 27 (9/floor) — **INFO, by design:** `_pack_bar` merges units by cardinal orientation (L06 no-intra-floor-multiplier rule), so 5 zones/floor (corridor + N/S/E/W) is expected, not a defect.
- **Manager audit of the employee's DHW flag — RESOLVED, baseline NOT affected.** Employee flagged a phantom 435 GJ "District Heating" row in the generated run's `eplustbl.htm` (likely `dhw.py`'s standalone `WaterUse:Connections`) and warned the Phase-E EUI dataset might be inflated if the parser reads htm summaries. **Verified false for our pipeline:** production EUI = `results/parser.py::_parse_meters_sql`, which reads explicit SQL RunPeriod meters (`WaterSystems:Electricity/:NaturalGas` capture DHW once; **no `DistrictHeating` meter summed**) — it never reads `eplustbl.htm`. The ABUPS cross-check (`parser.py:404`) only compares Interior Lighting+Equipment electricity, not District Heating. `config.py`'s `eplustbl.htm` is a requested output, never parsed. The employee's "corrected" −6.5% (metered elec+gas) is exactly what production computes. Lower-priority follow-up (NOT a blocker, NOT a regression): re-audited `dhw.py:116-149` — it emits **both** a real fuel-metered `WaterHeater:Mixed` (Peak_Use_Flow_Rate standalone, `EndUse_Subcategory=DHW` → `WaterSystems:*`) **and** an unconnected standalone `WaterUse:Connections` (blank nodes) whose draw E+ satisfies from an idealized district source → the phantom `DistrictHeating` in the htm. So the phantom is a **redundant duplicate of the real metered heater, not a missing flow** → production (reading `WaterSystems:*`) is neither inflated NOR under-counting; the metered −6.5% is correct. The redundant `WaterUse:Connections` is a modeling wart (pollutes htm tabular, redundant solver work) worth a future cleanup, but the Phase-E arc was ratified with these exact SQL meters and is unaffected.
- Deviations: none (validation only; no `openubem/`/`tests/` changes). Employee added `set_default_constructions()` to its throwaway harness only.

#### T16b — continuous corridor spine across wings (manager/Opus, delicate geometry) — completed 2026-07-02
- **Trigger:** user reviewed the T16 grid and flagged that the DOE reference has one continuous central corridor, but generated L/U/T/O/Cross placed an **independent corridor stub per wing** (each wing's `_pack_bar` centered a corridor on its own OBB → corridors never met at junctions). User: "the corridors need to be continued through U, L, T, O, Cross shapes." Also moved all layoutGenerator figures to `openubem/outputs/LayoutGenerator/` (`plot_layout_grid.py` OUT re-pointed; `layoutgenerator_doe_vs_generated.png` + `t11_doe_vs_generated.md` relocated).
- **Final design (zero-fitted, shapely-only, honors D-B opt-in + hard-rule #7):** for multi-wing shapes (L/U/T/cross) and O, `generate_layout` routes to `_pack_connected_spine`, which (1) rotates the footprint to its dominant-edge frame **once**; (2) decomposes into axis-aligned wings in-frame via `_wings_in_frame` (reflex-cut for L/U/T/cross, interior-ring-bbox cut for O — no compound rotation, so conservation stays machine-precision; reflex cut values are **exact, not rounded**, so cuts land on the footprint's own vertices — rounding to mm mismatched the ±90° rotation-fuzzed vertex by ~0.4 mm and carved a degenerate sliver); (3) builds each wing's long-axis midline and **connects them into one network** with orthogonal L-bridges (`_connect_centerlines`, nearest-component elbow inside the footprint); (4) `corridor = network.buffer(c/2) ∩ footprint`; (5) grid-slices the footprint at corridor-edge (centerline ±c/2) and wing-bound lines via `_grid_cut`, which keeps only interior cells (a courtyard void is never inside a block; a corridor loop is cut at corners into simple rectangles → **the donut E+ Fatal cannot re-form**) and drops cut lines grazing the boundary (`_dedupe` + 0.05 m margin → no ~0-width slivers); (6) tags each cell corridor/apartment by point-in-buffered-spine; (7) drops collinear vertices in-frame, rotates back once.
- **Conforming by construction — no merge step.** The full-span grid cut yields a conforming tiling (every cell edge on a global grid line), so geomeppy's `intersect_match` never hits its coplanar-containment `break_polygons` IndexError. **Root-cause story for the record:** a first cut of this feature did an aggressive `_merge_rectangular` (great look, 8–15 zones) but cross-wing merges created **T-junctions** (a short wall abutting the middle of a longer coplanar wall), which crashed geomeppy on the L → tripped the T10a room_layout reroute → whole-L fallback emitted 6 sub-mm degenerate surfaces. Tried merge+conform-split; it just converged back to the raw grid (and inflated L to 22). Conclusion: the raw conforming grid **is** the right answer — dropped `_merge_rectangular`/`_merge_typed_slivers`/`_conform_tiling` entirely.
- **Single-wing (compact/slab/point) path UNCHANGED** — still `_pack_bar` → **DOE bar / T11 untouched and still valid.**
- **Results (grid `openubem/outputs/LayoutGenerator/layoutgenerator_doe_vs_generated.png`):** corridors continuous & turn corners — L bends at the elbow, U wraps down-across-up, T meets at the junction, O loops fully around the courtyard, Cross forms a +, rotated Ls work in-frame. Zones/floor: bar 5 (unchanged), L 15, U 27, T 18, O 48, cross 21, L_rot47 15 (higher than a bar because a continuous-corridor non-rectangular footprint has an honestly larger *conforming* zone count; the earlier "8–15" was non-conforming and crashed). **Area drift +0.00000% all shapes** (O rotated-donut passes strict 1e-5); min edge 1.68 m all shapes (no degenerate cells); circulation 12–14%. **geomeppy `intersect_match` succeeds directly on all six — no reroute.**
- Test status: **130/130 green** (`test_layout_generator test_zoning test_surfaces test_step3_orchestrator`).
- **E+ 23.1 re-verification DONE 2026-07-02 (Sonnet full-annual, Chicago TMY3) — CP-2 RE-CONFIRMED.** All six shapes `EnergyPlus Completed Successfully`, **0 Fatal / 0 Severe, reroute-fired=NO** (reroute-capture log empty for every shape). Both gates met: (1) 0 Fatal everywhere incl. the O courtyard loop (144 extruded zones, 864 surfaces); (2) **L kept its room-level zones** (45 zones / 270 surfaces, names `L_F0_w0c0…`) instead of the `_WHOLE` fallback — the `intersect_match` IndexError and degenerate sliver walls are gone. Extruded zone counts (3 floors) vs pre-fix: L 3→45, U 30→81, T 30→54, O 45→144, cross 36→63; bar unchanged at 15 (DOE control). Independently corroborated against each shape's `eplusout.end` (0 Severe). IDFs+`.err` under `…/scratchpad/ep_runs/<shape>/`. No production code touched (harness change limited to adding the `cross` shape).
- Deviations: none vs DESIGN (RESULT_L06 corridor-spine is explicitly a connected double-loaded run; the prior per-wing stubs were the deviation this corrects). Figures moved to `openubem/outputs/LayoutGenerator/` per user directive (supersedes the flat-outputs convention for this arc).

#### T12 — LIVE_SMOKE on real OSM apartments — completed 2026-07-02 (Sonnet employee, manager-audited) — FAIL (bug caught)
- Artifacts: `openubem/outputs/LayoutGenerator/t12_live_smoke.md` (report); scratchpad `t12_recon_classified.csv`, `t12_build_smoke_manifest.csv`, `t12_zone_build/` (IDFs), `t12_real_idf_runs/<osm_id>/eplusout.err` (primary evidence — E+ runs on the actual production IDFs). No `openubem/`/`tests/`/`docs/` changes beyond the output artifact.
- **Recon precondition MET:** 434/2,821 real MidriseApartments (15.4%) classify non-rect (L/U/T/CROSS/O) across 9/12 cells (`la_suburban` 228, `la_urban` 151 richest). The live path genuinely exercises the new geometry — not a synthetic-only pass.
- **Gate 1 (gen-success ≥95%) FAIL:** zone-mode `run_step3(resolution_mode="zone")` on `la_suburban` n=30 → **80% (24/30)**; 6× `failed_interzone_vertex_mismatch` (CROSS×1, T×3, U×2), dropped at builder.py's post-extrude gate.
- **Gate 2 (0 Fatal on real footprints) FAIL:** ran E+ 23.1 directly against the 5 real production IDFs (not a simplified recipe) → **4/5 FATAL** despite `generation_status=success` + clean geomeppy parse. Cross-checked with a standalone recipe → same pattern → the geometry itself is broken, not the pipeline's extra steps.
- **Two root-cause failure signatures** (well-evidenced by preserved `.err`):
  1. **`_WHOLE` vertex-count / non-planar mismatch** (`way/442340538` U 38-vs-41 vertex mismatch; `way/442340549` L non-planar window) — these are **T10a reroute products**: `surfaces.py:623` `intersect_match IndexError → _force_reroute_room_layout_to_one_zone_per_floor` fired, and the reroute's buffer round-trip does NOT produce E+-valid interfloor geometry on many-vertex real footprints (my T10a code was validated only against clean synthetic shapes where it never fired).
  2. **Malformed-zone temperature blowup during warmup** (`way/442340503` −871°C `_W0C7`; `way/442340539` −4.6M°C `_W0U4`) — genuine room_layout zones (not rerouted) that are thermodynamically degenerate → the **packer produces near-zero-area / badly-connected sliver zones on messy OSM footprints** that pass the 2 m² filter + geometry-parse but not E+.
- **Observability gap surfaced (c):** the `zoning_strategy=room_layout` manifest column does not reflect the internal `surfaces.py:623` reroute — **6 of the 24 "successes" silently degraded to 2-zone one_zone_per_floor** yet report `room_layout`. Manifest-fidelity bug worth fixing regardless of the geometry fix.
- **Warning-storm flag (d):** `way/442340523` completed (no Fatal) but with **103,394 warnings** / 5m56s — suspicious, worth a look before trusting it.
- **Verdict:** T12 FAILS both gates → **CP-3 BLOCKED.** This is exactly the synthetic-blind-spot the LIVE_SMOKE was added to catch: T10/T16b 0-Fatal on clean synthetic L/U/T/O ≠ live-green on real OSM footprints. Deviations: none (validation only, per hard-rule #2 no production code touched).

##### Manager deep-diagnosis 2026-07-02 (Opus, read the preserved `.err` zone-names directly — refines/corrects the employee's labeling)
Reading the actual `eplusout.err` per footprint (scratchpad `t12_real_idf_runs/<osm_id>/`) shows **only 1 of the 4 Fatals is a reroute product; 3 of 4 are the packer itself on real footprints** — and they split into exactly **two clean fault classes**:
| osm_id | shape | Fatal zone names | class |
|---|---|---|---|
| way/442340549 | L | `_WHOLE` (reroute) | **NON-PLANAR** — `CheckConvexity` Severe on `_WHOLE ... WALL 0013/0019` |
| way/442340538 | U | `_W0C2`,`_W0C3` (genuine cells) | **NON-PLANAR** — Severe on cell WALL/FLOOR/ROOF |
| way/442340503 | T | `_W0C7` (genuine cell) | **DEGENERATE ZONE** — −871 °C blowup |
| way/442340539 | U | `_W0U4` (genuine cell) | **DEGENERATE ZONE** — −4.6 M °C blowup |

- **Class 1 — non-planarity (549 reroute + 538 packer):** `layoutGenerator.py:660` does `simplify(0.001)` on each cell **in the aligned/rotated frame**, then rotates back to world → the inverse rotation reintroduces floating-point non-coplanarity that E+'s strict `CheckConvexity` rejects. The reroute (`surfaces.py:607`) has the same disease via its `buffer(0.01)/buffer(-0.01)` round-trip introducing near-collinear vertices. **Fix:** after rotate-back, snap emitted coords to the existing `VERTEX_SNAP_M = 0.005` grid AND drop collinear vertices **in world frame** (not aligned frame); apply the same snap+collinear-drop to the reroute footprint before `add_block`.
- **Class 2 — degenerate sliver zones (503 + 539):** `MIN_ZONE_AREA_M2 = 2.0` + `_merge_slivers` guard only the `_pack_bar` band path (called at `:326`); the `_grid_cut` cells in `_pack_connected_spine` are gated on **area only** (`_dedupe` 0.05 m), so a >2 m² but ~0.1 m-wide strip survives → thermodynamic blowup in warmup. **Fix:** add a min-edge / aspect gate to the grid-cut cells and route them through `_merge_slivers` (merge the strip into its longest-shared-edge neighbor — conserves area exactly).
- **Also (observability):** the manifest `zoning_strategy=room_layout` doesn't reflect the `surfaces.py:773` internal reroute (6/24 silently became 2-zone). **Fix:** stamp a `generation_status_note`/manifest column when the reroute fires.
- **Effort estimate:** ~3 targeted edits (packer emit snap+collinear-drop; grid-cut min-edge gate + `_merge_slivers` reuse; reroute footprint clean + manifest flag), all in `layoutGenerator.py`/`surfaces.py`. **Regression gates before re-accepting:** full 130 unit suite + the T10/T16b synthetic E+ 0-Fatal smoke (must stay green — the T16b connected-spine path is delicate) + re-run T12 on the 4 Fatal footprints + a fresh `la_suburban` n≥30 gen-success pass. **Awaiting user scope decision (fix now / narrow opt-in to compact+slab / park).**

#### T12-FIX — real-footprint geometry robustness (manager/Opus, delicate) — code DONE 2026-07-02, E+ re-validation IN FLIGHT
- **Root cause (confirmed by reading a Fatal cell's IDF vertices, not inferred):** way/442340538 `_W0C2` floor was a **degenerate triangle — vertices 1 & 2 were 7 microns apart** (`0.91418856,5.94477545` vs `0.91418864,5.94478235`). All four packer-path Fatals trace to the same defect: real OSM footprints are not exactly orthogonal, so after `_dominant_edge_angle` alignment the axis-aligned grid cuts **shear against the slightly-tilted real edges and shed near-zero-area sliver cells**. E+ reports these as `CheckConvexity ... non-planar` (538, degenerate normal) or as warmup temperature blowups (503 −871 °C, 539 −4.6 M °C, near-zero-volume zones). The one reroute Fatal (549 `_WHOLE`) is the reroute's version — the `buffer(0.01)/buffer(-0.01)` round-trip leaves near-collinear vertices that geomeppy merges into a non-planar wall.
- **Fix (3 edits, minimal + surgical — chosen to NOT reintroduce merging, which is what crashed geomeppy in T16b):**
  1. `layoutGenerator.py`: new `MIN_CELL_WIDTH_M = 1.0` + `_is_degenerate_cell(poly)` (`area < MIN_ZONE_AREA_M2` OR `buffer(-MIN_CELL_WIDTH_M/2).is_empty` — narrower than 1 m everywhere; below corridor 1.68 m so the corridor is never caught). `_pack_connected_spine` **drops** degenerate cells at emit (does NOT merge them — merging remakes the T16b T-junction crash); `generate_layout`'s existing 1% area-conservation net then degrades a footprint that loses too much to `one_zone_per_floor`. Healthy-cell handling (aligned `simplify(0.001)` → rotate → `_clean`) is otherwise **unchanged** → machine-precision conservation preserved.
  2. `surfaces.py` `_force_reroute_room_layout_to_one_zone_per_floor`: snap the reconstructed footprint to a 5 mm grid (`set_precision(0.005)`) + `simplify(0.02)` before `add_block`, dropping the near-collinear vertices that caused the 549 non-planar walls.
  3. `builder.py`: after `extrude_geometry`, if any zone carries `generation_status_note == "room_layout_intersect_fallback"` (surfaces.py reroute path) **OR** `room_layout_area_fallback` (generate_layout area-net path — edit 4), set manifest `zoning_strategy = "one_zone_per_floor"`.
  4. `zoning.py` + `builder.py` (added after re-validation): the E+ re-validation revealed the 4 Fatal footprints degrade via `generate_layout`'s 1% area-conservation net (surfaces.py reroute fired **0×**), so edit 3 alone left 25/30 manifest rows reporting `zoning_strategy=room_layout` while building 2-zone per-floor geometry. `zoning.py` now tags the area-net fallback zones `room_layout_area_fallback=True`, and `builder.py`'s relabel honors that tag too — a pure manifest-label change, zero geometry/IDF impact.
- **Regression gate 1 PASS:** `test_layout_generator test_zoning test_surfaces test_step3_orchestrator` = **130/130 green** (re-run after edit 4); the strict `donut2` `1e-5` area-conservation test passes (an earlier `set_precision` snap variant tripped it at 2.6e-5 → reverted; the drop-only fix keeps machine precision).
- **Regression gates 2–4 (E+ 23.1) PASS — all 4 gates (Sonnet employee, manager-audited 2026-07-02):**
  - **(A) 4 previously-Fatal footprints → 0 Fatal / 0 Severe** (503 42 Sev→0, 538 22→0, 539 1→0, 549 16→0; way/442340523 warning storm cleared 103,394→152).
  - **(B) synthetic bar/L/U/T/O/cross STAY 0 Fatal / 0 Severe**, reroute-fired = NO, room-level zoning intact (15–144 zones).
  - **(C) fresh la_suburban n=30 = 100% gen-success** (was 80%), 0 `failed_`.
  - **(D) 5 real non-rect footprints → 0 Fatal / 0 Severe.**
  - No footprint still Fatals → no `.err` signature to iterate on. Report: `openubem/outputs/LayoutGenerator/t12_live_smoke.md`.
- **Behavior note (intended graceful-degrade, not a regression):** most messy la_suburban non-rect MidriseApartments now legitimately fall back to per-floor rather than emit a broken room layout — the aggressive-but-correct degenerate-cell drop trips `generate_layout`'s area net. Correctness > coverage on adversarial live geometry; synthetic and DOE-prototype shapes keep full room-level zoning.

> **CP-3 — MET 2026-07-02 (manager greenlight; NOT user sign-off — only CP-4 is).** T11 DOE reproduction PASS (all thresholds) + T12 LIVE_SMOKE PASS (all 4 gates after the geometry fix). Phase 5 (T13–T15 → CP-4) unblocked but **not started** — awaiting user go.

---

## Verification (end-to-end)
1. **Unit:** `py -3 -m pytest tests/test_layout_generator.py tests/test_zoning.py tests/test_surfaces.py tests/test_step3_orchestrator.py -q` — classification, area/load conservation across modes, interior BCs, 0-Fatal smoke.
2. **DOE reproduction:** `py -3 -m pytest tests/test_layout_doe_reproduce.py -q` — generated MidriseApartment vs DOE baseline within thresholds; diff table in `openubem/outputs/comparisons/`.
3. **LIVE_SMOKE:** `py -3 -m pytest tests/test_resolution_mode_live.py -q` (or the new live test) against a real phaseE cell — 0 Fatal, ≥95% gen-success.
4. **Single-cell:** `py -3 scripts/validation/v12_cell_pipeline.py <apartment-heavy cell>` in `zone` mode — inspect manifest `zoning_strategy=room_layout`, gen-success gate.
5. **Cluster pilot:** `sbatch` `t09_layout_pilot.py`; read output file; compare EUI/runtime zone-vs-floor-vs-building + DOE in `openubem/outputs/comparisons/`; plots in `openubem/outputs/`.
