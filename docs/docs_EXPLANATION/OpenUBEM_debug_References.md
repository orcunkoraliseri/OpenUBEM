# OpenUBEM Debug References — Master Error/Solution Index

> Purpose: a single lookup document for every recurring error, bug, and failure documented across
> `docs/docs_DONE`, `docs/docs_ACTIVE`, `docs/docs_TODO`, `docs/docs_VALIDATION`, `docs/docs_REPORTS`
> and the `openubem/` package itself. **Before starting a new debugging session, search this file
> first — the symptom has probably been seen before.**
>
> Each entry: **Symptom** — cause -> fix. *(source path)*. Entries marked **[OPEN]** were never fixed.
>
> Generated 2026-08-20 by a 14-agent sweep of 618 markdown docs + 89 Python modules.
> Update this file whenever a new debug/measurement doc lands.

## Chapters

1. [Geometry: winding, zone volume, degenerate surfaces](#1-geometry-winding-zone-volume-degenerate-surfaces)
2. [Thermal runaway & envelope thermal mass](#2-thermal-runaway--envelope-thermal-mass)
3. [HVAC sizing, setpoints, exhaust & schedules](#3-hvac-sizing-setpoints-exhaust--schedules)
4. [Zoning & resolution modes](#4-zoning--resolution-modes)
5. [LayoutGenerator & LayoutAssigner](#5-layoutgenerator--layoutassigner)
6. [Classification & archetype assignment](#6-classification--archetype-assignment)
7. [Imputation, fusion & data acquisition](#7-imputation-fusion--data-acquisition)
8. [Results parsing, EUI arithmetic & meters](#8-results-parsing-eui-arithmetic--meters)
9. [Validation gates & metric traps](#9-validation-gates--metric-traps)
10. [Microclimate / UTCI (SVF, MRT, wind)](#10-microclimate--utci-svf-mrt-wind)
11. [Visualization (3D viewer, matplotlib, basemaps)](#11-visualization-3d-viewer-matplotlib-basemaps)
12. [Cluster / SLURM / SSH (Speed)](#12-cluster--slurm--ssh-speed)
13. [Pipeline plumbing, Windows & parallelism](#13-pipeline-plumbing-windows--parallelism)
14. [Test suite: collection aborts, fixtures, benign noise](#14-test-suite-collection-aborts-fixtures-benign-noise)
15. [Exceptions raised by the `openubem` package](#15-exceptions-raised-by-the-openubem-package)
16. [Method traps: how these bugs got misdiagnosed](#16-method-traps-how-these-bugs-got-misdiagnosed)
17. [Not-a-bug: expected behaviour & accepted limitations](#17-not-a-bug-expected-behaviour--accepted-limitations)
18. [Currently open items (register snapshot 2026-08-20)](#18-currently-open-items-register-snapshot-2026-08-20)

---

## 1. Geometry: winding, zone volume, degenerate surfaces

- **`Floor is upside down! Tilt angle=[0.0]` + `Indicated Zone Volume <= 0.0 ... set to 10.0 m3`** — OSM
  footprints arrive clockwise-wound; geomeppy's `build_zones` needs CCW for outward normals, so E+ computes
  a negative zone volume and clamps it to a 10 m³ stub. Universal (95% of la_urban, 100% of la_rural), but
  only *fatal* on the largest footprints (1,173–22,444 m²). Fix: `shapely.geometry.polygon.orient(poly_local,
  sign=1.0)` before `build_zones` in `openubem/idf/builder.py`.
  *(docs/docs_DONE/LOADS & SCHEDULES/hvac-ServiceLoads/debugs/DONE_10_fails.md; docs/docs_REPORTS/REPORT_phaseE_final.md §5)*
- **[OPEN] The same `orient()` fix is deliberately skipped in `auto` mode** — the guard at
  `openubem/idf/builder.py:464-465` excludes `auto`, which is the mode the published fleet EUI was built in;
  `GetVertices: ... is upside down!` therefore fires on 8,160/8,160 `auto` buildings. Underlying library
  defect: geomeppy 0.12.2's `is_clockwise()` returns `False` unconditionally on its CCW branch, so
  `invert_orientation()` never fires. (OPEN-56)
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-56_writer-localisation.md)*
- **[OPEN] Every building simulates with a 10 m³ zone-volume stub** — understates EUI by a fleet-stratified
  mean **+0.98%** (median +0.84%, up to +3.25%), direction-consistent in 65/69 sampled buildings. Magnitude
  does *not* scale with zone count (refuted, corr=+0.113): best model is a fixed ≈+1.0 kWh/m² per-building
  offset. Fix proven by intervention (write `Zone.Volume` explicitly → 6/6 previously-failing buildings
  complete, 0 severe) but **not applied to the published baseline**. (OPEN-56)
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_ten-tasks-2026-08-18-night.md)*
- **`GetSurfaceData: There are 100 degenerate surfaces (number of sides < 3)` → Fatal** — geomeppy's
  `core/perim` emits one perimeter wedge per footprint edge; an 89-edge near-convex footprint explodes into
  ~52 wedges/floor, many collapsing below 3 vertices. `idf.add_block()` does **not** raise, so the
  except-based fallback never fires and the building is falsely marked `success`. Fix: post-extrusion
  degenerate-surface check → discard block → rebuild as `one_zone_per_floor`.
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/PLAN_coreperim-degenerate-fix.md)*
- **`Vertex size mismatch between base surface and outside boundary surface` (e.g. 14 vs 15, or 38 vs 41) →
  `GetSurfaceData: Errors discovered, program terminates`** — a footprint with an interior ring (courtyard)
  produces a donut `core/perim` decomposition with mismatched inter-floor vertices; the degenerate-surface
  detector doesn't catch it (no <3-vertex surfaces, normal zone count). Fix: pre-screen
  `footprint_poly.interiors` non-empty → route straight to `one_zone_per_floor` (or bbox), never `core/perim`.
  Also seen as a residue of an internal `room_layout → one_zone_per_floor` reroute that doesn't repair paired
  horizontal surfaces before save.
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/PLAN_coreperim-degenerate-fix.md; docs/docs_TODO/layoutgenerator/outputs/t12_live_smoke.md:155)*
- **`CalcHeatBalanceInsideSurf` divergence with *no* degenerate/fatal geometry error** — a sliver perimeter
  zone (0.0645 m², 18.76 mm off-collinear, above the 10 mm vertex-collapse tolerance) inverts winding. Fix:
  `_coreperim_has_tiny_zone_area(min_area=0.5)` shoelace detector in the reroute gate. **Do not** add an
  inverted-winding detector — it false-triggers on all healthy floor surfaces (E+/geomeppy give floors
  negative signed area by convention).
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/PLAN_phaseC_geometry_fixbatch.md)*
- **Shapely `NotImplementedError` → `failed_worker_exception`** — a MultiPolygon footprint (e.g. from a
  `buffer(0)` anomaly) reaches `BuildingIDF.build()`, which has no MultiPolygon guard. Fix:
  `_coerce_to_polygon()` takes the largest-area part before `simplify_footprint`, tagging a `data_quality_flag`.
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/PLAN_phaseC_geometry_fixbatch.md)*
- **geomeppy `break_polygons` `IndexError` / `intersect_match` `IndexError` → `failed_worker_exception`** —
  `idf.intersect_match()` (`surfaces.py:577`) raises *before* the degenerate-reroute check at `:585`, so the
  exception escapes. Fix: wrap `intersect_match()` in try/except; force-rebuild as `one_zone_per_floor` and
  re-run intersect/repair once before re-raising (`_force_reroute_room_layout_to_one_zone_per_floor`).
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/PLAN_phaseC_geometry_fixbatch.md; docs/docs_TODO/layoutgenerator/PLAN_layoutgenerator_implementation.md:266)*
- **Generation worker hangs forever — 4 nested python processes at ~0% CPU, no exception, no timeout** —
  `intersect_match()` never returns on a high-complexity footprint (97 simplified vertices × 15 floors ≈ 1,455
  surface pairs). A bare `except` cannot catch a hang. Fix: pre-gate on complexity
  `M = simplified_vertex_count × n_floors`; if `M > 800` skip `intersect_match` and reroute to
  `one_zone_per_floor` (fleet max on successful `perimeter_core` = 465; the hang was at 1,455).
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/PLAN_geometry_generation_drops.md)*
- **`failed_interzone_vertex_mismatch` (building silently dropped)** — `find_mismatched_interzone_pairs`
  detected a mismatch post-extrusion and returned early instead of repairing. Fix: reroute to
  `one_zone_per_floor` and re-check; drop only if still mismatched. **[OPEN]** 6/30 la_suburban footprints
  still drop this way in LIVE_SMOKE.
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/PLAN_phaseC_geometry_fixbatch.md; docs/docs_TODO/layoutgenerator/outputs/t12_live_smoke.md:128)*
- **`CheckConvexity: Surface=...WALL 0019 WINDOW is non-planar` → terminates** — non-planar subsurface on a
  generated room layout; open in LIVE_SMOKE.
  *(docs/docs_TODO/layoutgenerator/outputs/t12_live_smoke.md:156)*
- **[OPEN] `.err` reports CHKSBS "Base surface does not surround subsurface" for a door that visibly *does*
  fit its wall** — first pass wrongly concluded "different generation" because E+ uppercases surface names in
  `.err` and the cross-check was case-sensitive; a case-insensitive re-match confirmed same geometry, so the
  `.err`-vs-geometry disagreement is real and unresolved. Note CHKSBS is a `** Warning **` and never kills a
  run by itself.
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-07_smallhotel-idf-diff.md)*
- **`.err` ends mid-line inside a `GetSimpleAirModelInputs` block, no Fatal marker anywhere, no `.end` file**
  — a silent `std::bad_alloc` OOM crash (seen on an 89-storey building). Invisible to every fatal-marker
  regex because E+ never reaches controlled termination.
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-41-38_failure-causes.md)*

## 2. Thermal runaway & envelope thermal mass

- **`CalcHeatBalanceOutsideSurf` / `Temperature (high|low) out of bounds` isolated to the top/roof zone, after
  the winding fix** — orient is necessary but not sufficient: an all-`MATERIAL:NOMASS` envelope has zero heat
  capacity, so solar gain on a large roof runs away (±200 °C). Confirmed by an intervention matrix (only "add
  thermal mass" and "remove windows" gave `success`). Fix: opt-in thermal-mass construction — replace
  `MATERIAL:NOMASS` with massive `MATERIAL` (ρ=800 kg/m³, cp=1000 J/kg·K, k=0.12 W/m·K, Thickness=R×k),
  preserving R exactly.
  *(docs/docs_DONE/LOADS & SCHEDULES/hvac-ServiceLoads/debugs/DONE_10_fails_solution.md §7A)*
- **[OPEN] That thermal-mass fix was never merged into production** — it lives only in
  `scripts/validation/phaseE_recover_10.py`; `grep -n "thermal_mass" scripts/validation/v12_cell_pipeline.py`
  returns zero matches. (OPEN-42)
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-42_six-failures.md)*
- **`CTF calculation convergence problem for Construction="..."` → `Fatal (InitConductionTransferFunctions)`**
  — `patch_envelope()` held conductivity at `_K=0.12 W/m·K` and let `Thickness=(1/u)*_K` absorb the whole
  R-value; a well-insulated roof (`u_roof < ~0.138`) becomes a >1 m / ~800 kg/m² slab whose time constant the
  CTF solver can't expand at the 900 s timestep. Fix: cap the mass layer at a frozen `T_MASS_MAX=0.35 m` with
  a `MATERIAL:NOMASS` residual layer, engaged above `T_ENGAGE=0.868 m`. Mass-preserving / R-preserving N-way
  splits and R·C-scaled caps were tried and **falsified — do not re-propose them**.
  *(docs/docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/COMPLETION_REPORT_e-la-20-multilayer-fix.md)*
- **CTF pass/fail is NOT monotone in cap thickness** — at `u=0.097`: `t_mass=0.4948 m` PASS, `0.5567 m`
  FATAL, `0.6186 m` PASS. Never justify a thickness constant by bracketing between two passing measurements;
  only a direct measurement at the exact shipping value/`u` is valid. (F-17)
  *(same doc)*
- **[OPEN] `CalcHeatBalanceInsideSurf` divergence in a small marginal zone (`ElevatorCoreFlr1`,
  `LaundryRoomFlr1`, `KITCHEN_FLR_5`, `HOTEL_BOT_LAUNDRY ZN`)** — caused by the `MATERIAL:NOMASS` swap on
  scaled small zones. Fixing one zone does not close the archetype: the same building can diverge in a
  *different* zone next (e.g. one whose floor is `GroundFCfactorMethod`, which `patch_envelope()` skips by
  design). Treat any such Fatal in *any* zone of a previously-failing building as "not yet closed". (E-LA-15)
  *(docs/docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md)*
- **[OPEN] `CalcHeatBalanceInsideSurf ... temperature of 12669512.96 C` on byte-identical input that
  previously ran fine → `ZERO-FAIL: N failures exceed tolerance`** — a correctness fix made
  `_get_cross_archetype_loads()` unconditional, so PDE bounds now draw from the full archetype table
  including data-centre archetypes (~9000+ W/m² equipment vs 5–20 typical). All 71 failures in the measured
  cell drew equipment ≥2496 W/m²; 0 failures below that floor. Root-caused, not fixed. (OPEN-55)
  *(docs/docs_ACTIVE/openings/extra/INVESTIGATION_open-55_pde-bounds-datacenter.md)*
- **[OPEN] `layout_assign` fatal `CalcHeatBalanceInsideSurf ... zone="LAUNDRYROOMFLR1"` (−59,865 °C to
  +182,399 °C), n_severe=1, only under `resolution_mode="layout_assign"`** — occurs only on buildings
  substituted with the `SmallHotel` DOE prototype; the fatal zone is the *bottommost* storey (opposite of
  OPEN-42's topmost signature) and co-occurs 7/7 with CHKSBS warnings. Mechanism undetermined. (OPEN-38)
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-38_laundryroom.md)*
- **Data-centre archetypes diverge at 10⁵–10⁶ °C during warmup** — ITE loads of 1076–5382 W/m² on a
  single-zone IdealAir model before HVAC is active; `SmallDataCenterLowITE` (430 W/m²) succeeds, putting the
  architectural threshold near ~800 W/m². Ruled permanently N/A rather than capping loads; would need
  `ElectricEquipment:ITE:AirCooled` + CRAC/CRAH.
  *(docs/docs_VALIDATION/step1/overAll/OPEN_QUESTIONS_R5.md, OQ-R5-7)*

## 3. HVAC sizing, setpoints, exhaust & schedules

- **PrimarySchool heating 760–1256 kWh/m² (total up to 2175) in mild LA, E+ completes with 0 severe errors so
  zero-fail checks can't catch it** — misdiagnosed twice (VAV cold-SAT reheat; then degenerate geometry)
  before the confirmed cause: a kitchen-exhaust `ZoneVentilation` at a fixed absolute flow (`exhaust_m3_s`,
  e.g. 4500 cfm) on a hardcoded constant-1.0 (24/7/365) schedule dumped on one zone, forcing ~36 kW of
  make-up air conditioning. Proven on byte-identical geometry (heating design load 2,021 W sane vs 47,487 W
  blown) and identical across PTAC/PSZ-AC/PSZ-HP. Fix: area-scale
  `exhaust_m3_s × min(1, total_area/prototype_area)` and replace the constant schedule with a 05:00–01:00
  window. Same bug inflated QSR/FSR restaurant EUI.
  *(docs/docs_DONE/LOADS & SCHEDULES/hvac-ServiceLoads/remediation/PLAN_phaseE_CPD_remediation.md CP-R1.9; docs/docs_REPORTS/REPORT_phaseE_final.md §10.1)*
- **Single-zone buildings on central VAV + HW-reheat reach 765–1,565 kWh/m²** — the whole building's airflow
  autosizes to one zone, is held at the locked 30% reheat minimum, and reheats continuously. Phase-D hid this
  because PTAC autosizes per-unit. Fix: guard in `assign_hvac` (`openubem/idf/hvac.py`) routing any
  single-zone non-residential building on a central/VAV/PVAV-reheat family to `PSZ-AC w/ Gas Furnace`.
  *(docs/docs_DONE/LOADS & SCHEDULES/hvac-ServiceLoads/remediation/PLAN_phaseE_CPD_remediation.md CP-R1.7/1.8)*
- **[OPEN] `Maximum_Flow_Fraction_During_Reheat` is silently overridden to 1.000 by the 0.30 minimum-flow
  floor** — a supply-air-temperature-reset fix cannot control reheat airflow while that lock is held; proven
  non-functional and abandoned rather than unlocking the floor (which would distort every healthy VAV
  building).
  *(same doc, D1)*
- **NYC office heating over-predicted +11…+23%** — 11 non-residential archetypes' `Heating_Setpoint_*`
  weekday blocks in `doe_schedules.json` held 21.1 °C flat until midnight with no evening setback (an "OQ-2
  digitization" bug), while the same archetypes' Saturday/AllOtherDays blocks correctly dropped to 15.6 °C.
  Fix: mirror each archetype's own weekend setback into its weekday block (15.6 °C from 19:00); leave
  genuinely-24h archetypes (hospital, hotel, data centre) and residential untouched. Result: −9.86%.
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/phaseD_realHVAC/PLAN_phaseD_real_hvac_resim.md)*
- **[OPEN] Office cooling setpoints hold 23.9 °C flat with no unoccupied rise (~29.4 °C per DOE prototype)**
  — same flattening class as the heating-setback bug; spot-checked, reported, deliberately not fixed (S4).
  *(same doc)*
- **E+ fatal `Illegal Field entered =FOR: ALLOTHERDAYS` — 22/47 MidriseApartment sims died before
  simulation** — `_compact_block` (`openubem/semantic/schedules.py:72`) guarded `if day_vals is None:
  continue`, but an empty list `[]` (a legitimate "Saturday = AllOtherDays" encoding) is not `None`, so it
  emitted a bare `For: Saturday,` with no `Until:` lines. Fix: `if not day_vals: continue` (fixes 6
  archetype/family pairs at once).
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/PLAN_phaseC-combined-resim.md)*
- **SuperMarket refrigeration EUI 1192 kWh/m²** — defrost schedule was constant-on. Fix: 3 staggered 20-min
  defrost pulses/day → 100.4 kWh/m². Verify schedule objects encode a duty cycle, not an on/off placeholder.
  *(docs/docs_DONE/LOADS & SCHEDULES/hvac-ServiceLoads/REPORT_phaseE_final.md)*
- **MidriseApartment lighting EUI overcounted ~10× (43.9 vs ~4.5 kWh/m²)** — OpenUBEM's synthetic lighting
  schedule peaked at ~0.9, but the real DOE residential lighting schedule is diversity-baked with peak 0.181
  paired against the *full* installed LPD. Normalizing the schedule to peak 1.0 (the natural-looking fix)
  would have re-inflated it 5× more — use the DOE schedule verbatim, unnormalized.
  *(docs/docs_DONE/LOADS & SCHEDULES/scheduleDigitization/AUDIT_research_verdict.md)*
- **73,803 Severe `"Transformer Overloaded"` on MediumOffice at S=1.60** — `scale_baseline_idf()` doesn't
  scale fixed-capacity auxiliary equipment (transformers, DHW tank capacity, coil/fan rated flow). Fix:
  extend the scaling spec. (E-LA-06)
  *(docs/docs_DONE/SETUP/layoutAssigner/DONE/COMPLETION_REPORT.md)*
- **`SizeFluidCooler` Fatal ("water outlet temp"), 81.9% of LargeOffice failing fleet-wide** —
  `FluidCooler:TwoSpeed`'s `High/Low_Speed_Nominal_Capacity` never scaled. Fixed by adding the fields to the
  scaling engine (E-LA-07/08).
  *(docs/docs_DONE/SETUP/layoutAssigner/debug/DONE/COMPLETION_REPORT_debug.md)*
- **`dhw_eui` distorted up to 1643 kWh/m²** — `WaterHeater:Mixed.Peak_Use_Flow_Rate` was never added to the
  scaling engine, so it stayed at baseline scale while floor area scaled. Fixed (E-LA-10).
  *(same doc)*
- **[OPEN] `Design Size Rated Heating Capacity [W] = INF` / `Rated Water Flow Rate = NaN` on
  `COIL:HEATING:WATERTOAIRHEATPUMP` (`CheckForRunawayPlantTemps` Fatal)** — WSHP autosize degeneracy on
  shrunk DataCenter zones, exposed only after the FluidCooler fix. Root-caused, no fix (E-LA-11).
  Sibling degeneracies, also open: `SizeAirLoopBranches: ... air flow less than 1.0000E-003 m3/s` (E-LA-15)
  and `Calculation of cooling coil design UA failed` / `Autosizing of cooling tower UA failed ... Bad
  starting values for UA` (E-LA-16, which also hits already-passing buildings).
  *(same doc; docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-51_e-la-16-identity.md)*

## 4. Zoning & resolution modes

- **`resolution_mode="building"` EUI is ~1/num_floors of the correct value** (lights ratio exactly 0.200 on a
  5-floor building; nyc_centre `building` mean 102.7 vs `auto` 198.9) — `build_zones`'s `single_zone` branch
  emits one zone whose floor polygon is the footprint only, so `*/Area` loads use a one-floor zone area, and
  DHW/cooking/refrigeration `_total_floor_area()` counts unique `_F<idx>` name tokens (a lone `_F0_whole`
  zone yields 1). Fix: add `num_floors`/`floor_area_m2` to the `single_zone` dict, emit absolute design
  levels (`LightingLevel`/`EquipmentLevel`/`People` = intensity × floor_area_m2), and make all three
  `_total_floor_area` copies honour an explicit `num_floors` before name-parsing.
  *(docs/docs_DONE/SETUP/Simulation_Resolution/resolution_sets/PLAN_resolution_mode_switch.md M18)*
- **Lighting/equipment EUI silently divided by floor count (`lighting_eui × levels` = an exact constant per
  archetype — the proof)** — `decide_zoning_strategy` collapsed any building with footprint < 500 m² to a
  single full-height zone carrying one floor's internal loads, then divided by `footprint × n_floors`. Hit
  44.9% of an 8,148-building fleet, including MidriseApartment (the size check on line 16 fired before the
  residential rule on line 18). Fix: route any `num_floors > 1` to `one_zone_per_floor`; add a regression
  test asserting `lighting_eui_kwh_m2` is independent of floor count for the same archetype/LPD.
  *(docs/docs_DONE/BUGS/zoningBug/PLAN_zoning-multifloor-fix.md)*
- **`auto` mode silently diverged from the adopted phaseE baseline (MediumOffice heating/cooling/fans off by
  −52…−60 kWh/m²)** — an unconditional `poly_local = orient(poly_local, sign=1.0)` added in
  `BuildingIDF.build()` re-wound every footprint to CCW; inert for single-zone/one-per-floor but it changes
  geomeppy's core/perim split and VAV sizing for `perimeter_core`. Fix: gate it — `if self.resolution_mode
  != "auto":` before the `orient()` call (`openubem/idf/builder.py:~293`).
  *(docs/docs_DONE/SETUP/Simulation_Resolution/resolution_sets/PLAN_resolution_mode_switch.md M10/T07b)*
- **E+ Fatal on `fast_zone` (perimeter_core) for narrow or courtyard footprints** — a narrow footprint's
  4.57 m inward core buffer collapses (core < 10 m²); a courtyard produces a donut core with mismatched
  inter-floor vertices. Both fall back to `one_zone_per_floor`; fallback rows are logged and counted, not
  treated as failures.
  *(docs/docs_DONE/SETUP/Simulation_Resolution/resolution_sets/SIMULATION_RESOLUTION_zoning_by_building.md §4)*
- **Harvest CSV comes back with zero EUI on every row (`float division by zero` in `_parse_sql`)** —
  `build_cell_info` read the phaseE `05_results.gpkg`, which has no `total_floor_area_m2`/`floor_area_m2`
  column (only `footprint_area_m2` + `levels`). Fix: compute `floor_area_m2 = footprint_area_m2 × max(1,
  levels)` plus a defensive `fa<=0` guard in `_parse_sql`.
  *(docs/docs_DONE/SETUP/Simulation_Resolution/resolution_sets/PLAN_resolution_mode_switch.md M18)*
- **Every cell reaching the post-sim "reroute" step crashes with a `TypeError` on argument count** — a
  monkey-patch stub at `v12_cell_pipeline.py:520` was a 3-arg lambda, but commit `e063865` added a 4th
  positional arg to `decide_zoning_strategy` (`builder.py:325`). Fix: `lambda arch, area, floors, *_a, **_k:
  ...` — make monkey-patch stubs permissive of trailing args.
  *(docs/docs_DONE/BUGS/misclassification/RESUME_T11_fresh_manager_session.md)*
- **`results_status=failed_zone_mismatch` on buildings that simulated cleanly (0 severe, valid SQL)** —
  `_check_zone_integrity` (`parser.py:225`) hard-dropped on `len(resolved_zone_ids) != num_zones`, but
  `num_zones` in the manifest goes stale after a reroute. Fix: raise/drop only on a foreign osm_id or zero
  resolvable zones; demote a pure count shortfall to non-gating (recovered 4 false drops without resim).
  *(docs/docs_DONE/LOADS & SCHEDULES/hvac-ServiceLoads/debugs/DONE_10_fails.md §3)*
- **Manifest reports `zoning_strategy=room_layout` even when the building silently degraded** — 6 of 24
  "successes" actually fell back to 2-zone one-zone-per-floor geometry inside `extrude_geometry()`, logged
  only as `intersect_match raised IndexError -> rerouting` at `openubem/idf/surfaces.py:623`; the manifest
  field never reflects it. **[OPEN]**
  *(docs/docs_TODO/layoutgenerator/outputs/t12_live_smoke.md:134)*
- **`unknown resolution_mode: ...`** — `openubem/geometry/zoning.py:35` rejects any mode outside the
  supported set; check the caller's spelling.

## 5. LayoutGenerator & LayoutAssigner

- **[OPEN] geomeppy `intersect_match` coplanar-containment `IndexError` → E+ Fatal /
  `failed_worker_exception`** — wing-local corridor cuts create T-junctions at wing boundaries (a room edge
  meeting the middle of a neighbour's edge); the full-span grid exists precisely to avoid this. Related:
  merging a degenerate sliver into its neighbour re-creates the T-junction — **drop** degenerate cells,
  never merge them (T12-FIX).
  *(docs/docs_TODO/layoutgenerator/debugs/PLAN_cleanzoning_connected_corridor.md:56)*
- **[OPEN] A closed O-ring corridor yields a single annulus polygon with an interior ring, re-introducing the
  donut E+ Fatal** — fix: clip the corridor buffer *per wing* (hole-free by construction) instead of against
  the whole holed footprint. The general rule: never pass a holed polygon to `add_block`; `_split_donut`
  cuts O-shapes into hole-free wings with inner-ring walls tagged `Outdoors`.
  *(docs/docs_TODO/layoutgenerator/debugs/PLAN_design_buildout_by_archetype.md:688; docs/docs_TODO/layoutgenerator/PLAN_layoutgenerator_implementation.md:18)*
- **[OPEN] `GEOSException: TopologyException` raised (not degraded to `[]`) on real `units_corridor`
  footprints** — `zoning.py:83-101` handles only the empty-return degrade path, not an exception, so opt-in
  zone-mode production would propagate the raise. Known cases: `way/280612418`, `way/442341172`,
  `way/428643330`.
  *(docs/docs_TODO/layoutgenerator/debugs/PLAN_design_buildout_by_archetype.md:436)*
- **[OPEN-BLOCKED] `GetOutsideAirSysInputs ... invalid Controller List Name="OUTDOORAIR:MIXER" not found`,
  100% of `Outpatient`** — not a scaling bug: `eppy`'s `EpBunch.__repr__` (used by `IDF.save()`) pre-expands
  `Controller:MechanicalVentilation` to 156 field names and `zip(lines[1:], comments[1:])` silently truncates
  objects with more values (this archetype has 170/194), so the object ends in `,` not `;` and runs on into
  the next. Rejected fixes: eppy's `increaseIDDfields` (`ValueError: 'CONTROLLER:MECHANICALVENTILATION' not
  in list`, a geomeppy key-casing bug) and a post-save comma→semicolon patch (drops the excess zone-groups).
  (E-LA-09/13)
  *(docs/docs_DONE/SETUP/layoutAssigner/debug/DONE/PLAN_debug_implementation.md)*
- **[OPEN-BLOCKED] `layout_assign` zones keep DOE baseline names instead of `{osm_id}_F{floor}_{label}`** —
  so `openubem/results/parser.py`'s `_check_zone_integrity()`/`ZONE_RX` always false-negatives for
  `layout_assign` buildings, silently failing the harvest gate. (E-LA-05)
  *(docs/docs_DONE/SETUP/layoutAssigner/DONE/COMPLETION_REPORT.md)*
- **`Daylighting:ReferencePoint` coordinates not scaled by `scale_baseline_idf()`** — a latent defect masked
  by E-LA-07-class-2; must be fixed *before* class-2 or its retest is confounded by a second Fatal. (E-LA-12,
  fixed)
  *(docs/docs_DONE/SETUP/layoutAssigner/DONE/structural-fixes/PLAN_structural-fixes_implementation.md)*
- **Substituted buildings overlap their neighbours in the 3D viewer** — the emitted world position is
  `real_footprint_centroid_UTM + baseline_prototype's own S=1 local coordinates`; surface-level scaling
  shrinks rooms but never rescales the zone-origin grid. A faithful read of the IDF's own convention, not a
  viewer bug.
  *(docs/docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/results/viewer_blank_diagnosis.md)*
- **[OPEN] Hotels degrade to per-floor zoning on any complex shape (L/U/T/O/cross) in production** — the
  engine can pack real GuestRoom+Corridor layouts on those shapes (verified 15/27/48 zones, area-conserved),
  but the T13a production gate keeps hotels per-floor pending E+ validation, entangled with the T18-DIAG
  sliver defect. LargeOffice and Primary/SecondarySchool have **no geometry engine at all** (T13b/T13c).
  *(docs/docs_TODO/layoutgenerator/PLAN_layoutgenerator_implementation.md:183-195)*

## 6. Classification & archetype assignment

- **DOE/PNNL prototypes misclassify into the wrong archetype** (511 m² SmallOffice → Medium; 4,982 m²
  MediumOffice → Large; 6,871 m² PrimarySchool → Secondary; 4-story SmallHotel → Large) —
  `openubem/semantic/building_classifier.py`'s cut-points (500/4000 m² office, 5000 m² school, levels≥4
  hotel) were copied from DESIGN §3C and never validated against the prototype sizes they represent. Fix:
  office 2322/9290 m² *total floor area*, hotel split at ≥5 levels, school split by level count — recorded as
  DESIGN erratum **E-R3-3**. `tests/test_building_classifier.py` boundary assertions had to be rewritten;
  they passed only because the bug existed.
  *(docs/docs_DONE/BUGS/misclassification/BUG_archetype_classification_thresholds.md)*
- **The code keys on `total_floor_area_m2` while DESIGN §3C's cut-points were written for
  `footprint_area_m2`** — an earlier undocumented amendment (E-R3-1) swapped the metric without updating the
  values; a second fix (E-R3-2) touched a duplicate literal at fallback rule 17a. Always check for prior
  errata before treating a bug report's diff as the full picture.
  *(docs/docs_DONE/BUGS/misclassification/INVESTIGATION_archetype_classification_thresholds.md)*
- **[OPEN] Mixed-use rule 15 (`MIXED_USE_DOMINANT_TAG`) never fires in production** —
  `_normalise_use_class()` returns a disagreement score of exactly `0.5`, but `dominant_tag_threshold`
  defaults to `0.60` at all 4 call sites (`building_classifier.py:102,172,517,579`), so every real tag
  disagreement falls through to the generic `MidriseApartment` fallback (rule 16). The unit test masked it by
  calling `_apply_rule_table` directly with a fabricated `score=1.0`. Proposed fix: threshold 0.50 at all 4
  sites + an end-to-end regression test (`function_tag="office", building_tag="house"` → `SmallOffice`).
  Blast radius never measured — the open item deliberately treats this as a modelling decision, not a
  drop-in fix.
  *(docs/docs_DONE/BUGS/input-framework/PLAN_input-framework-classification-fixes.md; docs/docs_TODO/mixed_use_classification.md:21-62)*
- **[OPEN] `05_results.gpkg` archetype_id doesn't reproduce when `BuildingClassifier().classify()` is re-run
  on the same frozen input** — one writer traced (`v12_cell_pipeline.py` Step2→3→5), no second writer found,
  yet the current code predicts `SmallHotel`/`LargeHotel` where the file holds `SmallOffice`/`LargeOffice`.
  Corroborated by a retained raw `in.idf` containing `Building, HotelSmall` — the mismatch is real,
  implicating stale/mismatched generations. (OPEN-28)
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-06_archetype-writer-trace.md)*
- **A manually-labelled classifier fixture disagrees with classifier output on rows lacking a level count** —
  7/11 mismatches trace to one convention gap: the labels assumed "no floor count → 1 storey", while the
  classifier imputes a plausible level count via group-median lookup from comparable nearby buildings. A
  labelling-convention disagreement, not a classifier defect.
  *(docs/docs_ACTIVE/openings/extra/FIX_open-22_tagrich-fixture.md)*
- **A fix's own before/after diagnostic doesn't reproduce against the real pipeline** — the diagnostic was
  computed without the stratified group-median-levels imputation that `BuildingClassifier.classify()`
  actually applies. Pin regression tests to a **live-verified** value, never to a plan's stated value.
  *(docs/docs_DONE/BUGS/input-framework/PLAN_input-framework-classification-fixes.md)*
- **[OPEN] `building=yes` untagged footprints get size-bucketed to an office guess (rule 17a) with 2 wrong
  thresholds** — tracked as provenance Tier A, thresholds still defective.
  *(docs/docs_DONE/INPUTS/imputation/docs_Done/REPORT_missing_input_handling.md:56)*

## 7. Imputation, fusion & data acquisition

- **`ValueError: Unknown label type: continuous`** — `IterativeImputer(estimator=RandomForestClassifier(...))`
  applies one estimator class across the whole joint feature+target matrix. Fix: route classification targets
  to a natural single-target classifier (`RandomForestClassifier`/`LogisticRegression`/`KNeighborsClassifier`);
  keep the matrix family for regression targets.
  *(docs/docs_DONE/INPUTS/imputation/docs_Done/PLAN_phaseC_ml_imputer.md:505)*
- **`ValueError: could not convert string to float`** — the generic `impute_missing` spatial/statistical tiers
  are continuous-only (`knn_fill` does `.astype(float)`, `_statistical_tier` calls `.median()`). Fix: route
  categorical targets through `neighbour_vote` (spatial) and group-mode (statistical); in the mask-and-recover
  harness report `NOT_SCORABLE` rather than fabricating a score.
  *(docs/docs_DONE/INPUTS/imputation/PLAN_input_imputation_implementation.md:1467)*
- **`mice`/`linear` predict `year_built` in the AD-5000+ range and the confidence path stamps `ML_*_HIGH` on
  100% of it** — globally-linear estimators extrapolate catastrophically on a coordinate-pooled multi-city
  frame. Fix: default per-target method is `knn` for coordinate-pooled targets; `_clamp_to_observed_range`
  bounds fills (MAE ≈34 instead of 900–1160) though it is a proven no-op for `knn` itself.
  *(docs/docs_DONE/INPUTS/imputation/implementation/IMPLEMENTATION_phaseC_ml_imputer.md:101)*
- **`ValueError: Cannot determine common CRS for concatenation inputs`** — pooling per-city frames from 3
  different native UTM zones without reprojecting. Fix: reproject before pooling (fails loudly, no silent
  corruption).
  *(docs/docs_DONE/INPUTS/imputation/debugs/PLAN_phaseC_knn_repro_investigation.md:188)*
- **An ad hoc reproduction script silently defaults to `missforest` instead of `knn` (MAE 27.82 vs 25.14)** —
  the shipped default `IMPUTE_ML_METHOD_BY_TARGET` is `"missforest"` for every target; the original driver
  always overrode it per-method. Always set `config.IMPUTE_ML_METHOD_BY_TARGET[target] = "knn"` explicitly.
  Not a code regression.
  *(same doc:129,211)*
- **Two columns come back `NaN`/`None` on a *second* read of the same cached Overture data while others
  survive** — `height_cache.pull_overture` stores `fetch_overture()`'s already-normalized output, but
  `fusion.OvertureSource.join` re-reads via `fetch_overture()` again, double-normalizing and nulling any
  renamed column (`levels`, `use_class`). Fix: `_load_overture_layer(cfg)` in `openubem/semantic/fusion.py`
  detects an already-normalized cache and skips re-normalization. **[OPEN weakness]** the guard is a
  duplicated literal column set, not a shared import, and no unit test covers the cached-read path.
  (E-UTCI-13)
  *(docs/docs_ACTIVE/openings/extra/FIX_open-13_height-cache-and-collection.md)*
- **`Binder Error: Referenced column "year_built" not found` on the first live Overture query** — the real
  Overture Buildings schema has no `year_built` column at all (a synthetic-fixture blind spot; only assessor
  data carries it). Fix: drop it from the live-fetch SELECT.
  *(docs/docs_DONE/INPUTS/imputation/results/phase_D/RESULTS_phaseD.md:97)*
- **`INSTALL spatial` / `INSTALL httpfs` hang or fail on a machine without cached DuckDB extensions** — those
  extensions load only inside the live-endpoint fetch branch; the default `slice_path` branch reads via
  `gpd.read_parquet` with no `duckdb` import, so tests/CI never trigger a network install.
  *(docs/docs_DONE/INPUTS/imputation/docs_Done/PLAN_phaseD_fusion.md:492)*
- **`impute_column: bounds must be provided for PDE imputation on column 'height_m'` on 100%-missing cells,
  while `knn_fill` fills exactly 0 rows at every radius 100–1000 m** — `"auto"` dispatch resolves to the `pde`
  branch (needs explicit bounds) whenever a column is 100% NaN, vs `kde` when even a few real values exist.
  `knn_fill` returning 0 is the MNAR guard working as designed: every candidate donor is itself 100% missing.
  Widening the radius cannot fix it (the module is strictly per-cell).
  *(docs/docs_DONE/OUTDOOR/UTCI/e-utci-09/figures/i03_spatial_impute_structural_test.md:29)*
- **Rows with zero spatial neighbours are silently neither filled nor MNAR-flagged** — `_query_neighbours`
  returns empty → `continue` skips setting `blocked_mask[i]` (`spatial_impute.py:218-220`). Observability
  gap, dangerous once wired into production. Fixed with a distinct `SPATIAL_NO_NEIGHBOUR_SKIPPED` flag.
  (E-UTCI-10)
  *(docs/docs_DONE/OUTDOOR/UTCI/e-utci-09/PLAN_e-utci-09_investigation.md:435)*
- **`.get(key) or default` silently overwrites a stored falsy-but-valid `0`** — Python truthiness treats
  `0`/`""`/`NaN` as missing. Fix: `.get(key, default)` plus a tracked provenance flag; found across HVAC/DHW/
  cooking numeric-default sites.
  *(docs/docs_DONE/INPUTS/imputation/docs_Done/REPORT_missing_input_handling.md:160)*
- **`validate_schema()` raises on an EXACT column-count/tail-match gate** (`if len(gdf.columns) != 57`) — any
  additive column (e.g. `imputed_fields_count`) fails it regardless of placement. Never wire a new summary
  column into `enrich_semantics` without updating the schema gate.
  *(docs/docs_DONE/INPUTS/imputation/PLAN_input_imputation_implementation.md:1341)*
- **[OPEN] Missing EPW weather-file path fails silently** — the IDF proceeded with E+ internal defaults
  instead of a hard fail. Partly addressed: `BuildingIDF.__init__` now raises for a missing/invalid EPW path
  (`.build()` still never raises by design, so per-building problems stay in `data_quality_flag`). (OPEN-26)
  *(docs/docs_DONE/INPUTS/imputation/docs_Done/REPORT_missing_input_handling.md:65; docs/docs_ACTIVE/openings/extra/FIX_open-26-29_polish-and-fatal-tests.md)*
- **Fusion sources fail silently when unconfigured — by design** — `available()` returns `False` when
  `FUSION_LIDAR_NDSM_PATH` / `FUSION_ASSESSOR_PATH` is unset, so the source is skipped with no error. A 0%
  fill rate on an unconfigured source is not a bug.
  *(docs/docs_DONE/INPUTS/imputation/docs_Done/PLAN_phaseD_fusion.md:311)*
- **[OPEN] 3–4 of 12 microclimate cells report `svf_mean=1.0000` (flat open field)** — upstream Stage-1 OSM
  ingestion: `height_m`/`levels` are 84.5–100% NaN in the affected cells vs 0.67–26.09% elsewhere (a clean
  bimodal split from differential OSM tagging density), not a code defect. Partly cleared by an Overture pull
  + fusion tier; `nyc_rural` 36.4% / `austin_rural` 19.2% remain. Fleet-wide 34.39% (2,806/8,160) have no
  `height_m`. (OPEN-12, E-UTCI-09)
  *(docs/docs_DONE/OUTDOOR/UTCI/e-utci-09/COMPLETION_REPORT_e-utci-09-investigation.md:14)*
- **[OPEN] Unknown-archetype buildings draw equipment EUI up to 13,824 kWh/m² against a cell mean of
  ~230–390** — the PDE donor pool for Unknown spans the full 29-archetype table uniformly, including
  data-centre plug loads (`occupant_m2_per_person` range `[4.65, 464.52]`); the OPEN-49 fix removed the
  condition that had hidden it. A donor screen was implemented (71→0 divergences) but exposed OPEN-59:
  Unknown buildings still run **1.7× classified**, now via DHW (+61.0, 2.4×) and lighting/cooling (5.6–6.7×).
  (OPEN-55/59)
  *(docs/docs_ACTIVE/openings/extra/PROPOSAL_open-55_unknown-pde-bounds.md; docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md)*

## 8. Results parsing, EUI arithmetic & meters

- **EnergyPlus `.err` severe/fatal lines are silently never detected** — real E+ output uses **two** spaces
  (`**  Severe  **`) and the spacing is inconsistent even within one file (`** Severe  **`), so the literal
  one-space substring check returns nothing: no exception, no log. Fix: the shared whitespace-tolerant
  matchers in `openubem/results/err_parse.py` (`re.compile(r"^\s*\*\*\s+Fatal\s+\*\*", re.MULTILINE)` etc.),
  applied at `runner.py:141`, `v12_cell_pipeline.py:625`, `make_manifest_from_cluster.py:47` and 7 harvest
  scripts. Verified 44/44 true fatals caught on the 40,800-file E02 corpus. (OPEN-45)
  **[OPEN]** remaining unfixed sites: `openubem/simulation/runner.py:140`, `tests/test_sim_integration.py:171`;
  and `error_summary` in `v12_cell_pipeline.py:625-626` is still always `""` for every failing building ever
  manifested. Also: `SEVERE_RE`'s `^` anchor only matches the first line of a multi-line severe, so the count
  is a lower bound.
  *(docs/docs_ACTIVE/openings/extra/FIX_open-45_severe-matcher.md; MEASUREMENT_open-29_status-retrace.md; MEASUREMENT_open-42_six-failures.md)*
- **`has_fatal` is a dead column fleet-wide since T17** — same one-space vs two-space literal mismatch.
  (E-LA-21)
  *(docs/docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/COMPLETION_REPORT_e-la-20-investigation.md)*
- **[OPEN] `total_eui_kwh_m2` undercounts lighting and equipment for any building with a zone multiplier —
  only 6/48 buildings reconcile end-use sums to total within 2%** — the total sums Interior Lighting and
  Interior Equipment from *per-zone hourly output variables*, which E+ does **not** scale by zone multiplier,
  then divides by a multiplier-aware floor area (`openubem/results/parser.py:431-433`). Heating/cooling/fans/
  pumps/DHW come from the multiplier-correct ABUPS table and match to <0.01%. (OPEN-60)
  *(docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md)*
- **A rebuilt script's fleet EUI is 15–37% higher than the archived production figure for byte-identical
  IDFs** — the ad hoc script computed "Total Site Energy ÷ Total Building Area" from the ABUPS summary, while
  production's `openubem/results/parser.py` sums per-end-use EUIs from custom RunPeriod meters divided by
  `resolve_simulated_floor_area()`'s multiplier-aware `.eio` area. Two different numerators **and**
  denominators that look interchangeable. Fix: re-parse with production's `parse_building()`; no resim
  needed. (OPEN-58)
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35_storey-intervention.md)*
- **Two different buildings produce byte-identical `eplusout.sql`** — `run_ep()` invoked EnergyPlus with no
  `cwd=`, so all runs shared one working directory and overwrote each other's outputs. Concurrency is *not*
  required to trigger it; any caller importing that shared `run_ep` is exposed. Fix: an isolated `cwd` per
  invocation. (OPEN-58; blast radius: 6 artifacts)
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-58_blast-radius.md)*
- **`elevators_eui_kwh_m2` reads 0.0 for every building though total EUI is correct** —
  `openubem/idf/outputs.py`'s `HVAC_METERS` requested Cooking and Refrigeration submeters but omitted
  `Elevators:InteriorEquipment:Electricity`, even though the emitter (`elevators.py:65`) and parser
  (`parser.py:47/111`) both reference it. With no meter request E+ never writes the subcategory, so it
  defaults to 0 and stays folded inside `equipment_eui`. One-line fix. **[OPEN, worse]**
  `openubem/idf/elevators.py` is now orphaned dead code — nothing calls `assign_elevators`, and every
  elevator archetype's IDF has zero `Elevators` `ElectricEquipment` objects.
  *(docs/docs_DONE/LOADS & SCHEDULES/elevators/PLAN_elevator_loads_implementation.md; docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-46_divergence-inventory.md)*
- **`footprint_area_m2 = 200.0` for buildings whose simulation failed** —
  `v12_cell_pipeline.py:659` (`_build_enriched_gdf`) initializes the column to a hardcoded `200.0` and only
  overwrites it `if status == "success"`, so the placeholder survives into every downstream audit CSV.
  Repeated ad hoc in ~15 other call sites. **[OPEN]**
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-42_placeholder-and-fleet-impact.md)*
- **5 SuperMarket rows silently pass through a reconstruction step unmodified** — the results key is
  `SuperMarket`, the lookup key was `Supermarket` (case mismatch), so the entry fell through to a passthrough
  default. A companion `_T12_ROUNDTRIP_PASSTHROUGH` exception set was masking similar gaps (Outpatient, …)
  and was removed once the map was fixed; the honest numbers differ substantially (SuperMarket +90.4% vs the
  fudged −31.5%).
  *(docs/docs_DONE/LOADS & SCHEDULES/serviceLoads/PLAN_service-loads-reconstruction_2026-06-17.md T12-corr)*
- **Prototype floor-area denominator wrong for whole-building quantities on partially-modelled prototypes** —
  `elevators_by_archetype.json` used the *reduced-zone-model* area (3 representative levels) as the
  denominator for a whole-building DOE `design_level_w`, inflating HighriseApartment to 10.23 kWh/m²/yr. Fix:
  derive true footprint × real floor count from Z-origin geometry (<0.02% vs DOE-published area) → 3.07.
  Generic rule: check whether a prototype's "modelled area" equals its "true full-building area" before using
  it as a denominator.
  *(docs/docs_DONE/LOADS & SCHEDULES/elevators/PLAN_elevator_loads_implementation.md T01 CP-1)*
- **`_floor_count_from_zones` counted unique E+ zone names as storeys** (Hospital: 55 zones → 55 "floors" vs
  5 actual), producing wrong `floor_area = footprint × n_floors` and tiny per-floor footprints — 0/19
  buildings passed the ±5% round-trip gate. Fixing this alone moved Hospital from −93.7% to −12.2%. Never
  infer storey count from zone count for multi-zone reference models.
  *(docs/docs_VALIDATION/step1/overAll/OPEN_QUESTIONS_R5.md OQ-R5-5/6)*
- **EUI extraction from `eplusout.sql` fails even though the file exists** — `Output:SQLite` was set to
  `Simple` (or missing); `TabularDataWithStrings` (needed for `AnnualBuildingUtilityPerformanceSummary`) only
  exists under `SimpleAndTabular`.
  *(same doc, OQ-R5-4)*
- **12 corrupt SQL files shipped in one cell** — a truncated `tar` transfer from the cluster. Verify every
  fetched SQL with `PRAGMA integrity_check` plus `Zones > 0` before treating a harvest as complete.
  *(docs/docs_DONE/GENERAL/Resume_Prompts/monitorRun_resumeManager.md)*

## 9. Validation gates & metric traps

- **CBECS NMBE / CV(RMSE) / KS gates FAIL in every cell and every region under every basis/COP/load-fraction
  combination tested (CV(RMSE) 47–97%, KS_D 0.22–0.55)** — structural to an archetype-deterministic UBEM
  (near-zero within-archetype variance vs CBECS's per-building survey spread) plus regional/composition
  mismatch. A scalar reporting basis only shifts the mean, never the shape. Correctly designated report-only
  (V-R5-5); **never tune to pass**.
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/v19_validation/PLAN_v19_national_cbecs_rescore.md; docs/docs_VALIDATION/step1/overAll/MEMO_phaseB_cbecs_diagnosis.md)*
- **A "passing" aggregate metric that was actually a bug artifact** — CP-D NMBE read −3.1% (PASS) only
  because the kitchen-exhaust blowups (1,323 and 888 kWh/m² outliers) inflated the commercial mean enough to
  offset a systematic level deficit. After the fix: honest NMBE −17.6%, R² 0.40 → 0.91. **Rule:** an
  unexpectedly good aggregate number is itself suspect when two independent defects can cancel — check R² /
  per-archetype medians alongside NMBE.
  *(docs/docs_REPORTS/REPORT_phaseE_final.md §10.5-10.6)*
- **A fuel-basis correction (cool ÷3.5, heat ×1.19) makes NMBE worse (−16.0% → −29.5%/−35.3%)** — the
  pre-correction number was a coincidental offset between inflated cooling-thermal and understated
  heating-fuel. Test proposed corrections in isolation; never accept an accidental cancellation as
  validation.
  *(docs/docs_VALIDATION/step1/overAll/MEMO_phaseB_cbecs_diagnosis.md)*
- **High R² (0.69–0.996) alongside failing CV(RMSE) and KS_D** — R² checks shape, not level. Together with
  the registered "NMBE is blind to variance collapse" rule: **never read either metric alone as
  "validated."**
  *(docs/docs_VALIDATION/step1/overAll/V13_cross_case_synthesis.md)*
- **[OPEN] LA and Austin cells were scored against the CBECS *Northeast* reference** — the harness carried
  the NE reference forward from the V11 NYC pilot and was never re-pointed per region. Always verify the
  reference-region parameter is set per case, not inherited from a template. (R6)
  *(same doc)*
- **F12 EUI-plausibility gate FAILs on QSR/FSR at 1085–1120 kWh/m²/yr, just above the generic [25,1000]
  band** — cooking/refrigeration-dominated archetypes legitimately exceed generic caps; small-N cells amplify
  a few outliers past the 1% tolerance. Held deliberately per V-R5-8: an archetype-aware band must be a
  pre-run gate-spec change, never a reactive widening after seeing a FAIL.
  *(docs/docs_VALIDATION/step1/overAll/OPEN_QUESTIONS_R5.md)*
- **LA office over-predicted +78.4%, offices +30–50% in every city** — IDFs use `IdealLoadsAirSystem`, so
  `Zone Ideal Loads ... Cooling/Heating Energy` are *thermal loads*, but `openubem/results/parser.py:204`
  compared them directly to metered electricity with no COP conversion; cooling-dominated LA reads ~3.5× what
  a real DX system would meter. Interim fix: divide cooling by COP ≈3.5 at the reporting layer; real fix was
  the Phase-D physical PTAC + prototype-COP resim.
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/v19_validation/PLAN_v19_basis_diagnostic.md)*
- **National CBECS NMBE fails in all 3 census regions under a single national service-load fraction table**
  (NYC +12.2%, LA −16.8%, Austin −12.6%) — a climate-blind national table over-restores in heating-heavy NYC
  and under-restores in mild LA/Austin. Fix: per-census-division fraction tables (ratio-tilt anchored on the
  pre-validated national level, no anchor fitting) — all 3 regions flip to passing, at a disclosed cost to
  two small LA sub-segments.
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/phaseD_realHVAC/PLAN_regional_service_load_fractions.md)*
- **Restaurant service-load reconstruction overshoots ESPM by +110…+160%** — `modeled_frac=0.33` assumed 67%
  unmodeled service load; the true fraction is 0.69. Dividing by too small a fraction amplifies any base
  error by `1/frac` (a 2× base error becomes 6×). Also: FSR and QSR were aliased onto the *same* fraction
  entry despite different load profiles, and NYC multifamily over-grossed +34% because the national
  `modeled_frac=0.69` leaves only ~8% room in a heating-dominated climate. **[OPEN]** the restaurant 4-end-use
  base is itself 2.03× PNNL-expected (likely office/retail schedules on a cooking archetype) — needs resim.
  *(docs/docs_VALIDATION/step1/overAll/V18_calibration_diagnosis.md)*
- **Per-building round-trip deviation of ~45% reads as failure at a ±5% single-building gate** — published
  archetype UBEMs show 40–100% per-building error cancelling to 1–10% at stock scale (field norm: aggregate
  city median within ±10–15% of measured). The ±5% single-building gate is the wrong acceptance test for an
  archetype-level UBEM.
  *(docs/docs_VALIDATION/step1/overAll/V17_external_measured_validation.md)*
- **An EUI do-no-harm gate fails at pooled multi-city granularity (NMBE −5.51%) but is neutral at production
  per-cell granularity (+0.0000)** — `knn` needs a pooled frame to clear its ≥200-row fit floor; production
  imputes per-cell where it never fires. Always re-check a leaderboard failure at the actual production
  granularity.
  *(docs/docs_DONE/INPUTS/imputation/docs_Done/PLAN_phaseC_ml_imputer.md:39)*
- **Pooling two continuous targets into one `recover_pairs` call collapses `complete_cases` to rows where
  BOTH are observed** (n≈170, under `knn`'s 200-row floor) — baseline and `knn` both collapse to the same
  wrong number (MAE 41.9, n=34), which looks like divergence but is a shared masking bug. Check `n_holdout`
  against the documented count before trusting a leaderboard.
  *(docs/docs_DONE/INPUTS/imputation/debugs/PLAN_phaseC_knn_repro_investigation.md:183)*
- **A validation gate reports "single_zone repairs: 0" for a cell that had a real repair** — the gates-report
  funnel undercounts; cross-check against the run log's "Repairing"/"Repair round" lines.
  *(docs/docs_DONE/GENERAL/Resume_Prompts/pahseC_resumeManager.md)*
- **`counter_total_eui` in `roundtrip_report.csv` is a constant 2.0× the sum of its own four end-use
  columns**, unlike the matrix convention where total == Σ4 — verify the total/sum convention matches before
  computing deltas across two validation CSVs.
  *(docs/docs_VALIDATION/step1/overAll/V16_service_loads_reconstruction.md)*
- **`AssertionError: T10/T11 CROSS-CHECK GATE FAILED for <target>`** — a regenerated leaderboard/scatter MAE
  doesn't reproduce the committed `RESULTS_phaseC.md` value to 2 dp. STOP: the invocation is wrong; **do not
  tune to hide the mismatch**.
  *(openubem/results/draw_leaderboard.py:326; openubem/results/impute_scatter.py:253)*

## 10. Microclimate / UTCI (SVF, MRT, wind)

- **`compute_svf` mid-canyon SVF is ~2× the "analytic target" (0.74 vs 0.414 at H/W=0.5)** — the code and its
  `cos²γ` horizon formula were correct; the **plan's cited analytic formula was wrong**. Correct closed form
  for a two-wall canyon is `1/√(1+(2H/W)²)`, not `√(1+(2H/W)²)−2H/W`. Fix the target, not the code.
  *(docs/docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md:3279)*
- **After fixing the target, the SVF gate still fails by 0.001–0.009** — the code samples at pedestrian
  height (`z=DEM+1.1 m`) while the analytic target assumes canopy floor; use `1/√(1+(2(H−1.1)/W)²)` for an
  apples-to-apples check. The remainder is raster discretization and shrinks with resolution. (A "true
  Euclidean pixel distance" fix made the gap *worse* — discarded.)
  *(same doc:3370)*
- **The cool-pavement-paradox gate fails and no single `Psi_grd` passes both it and the open-field/night
  tests** — `Psi_grd=0.5` gets the albedo sign wrong; `Psi_grd=W_h=0.06` gets the sign right but falls 5–10×
  short. **Root cause from reading running SOLWEIG source** (`solweig.py`): the ground's true total view
  factor is **0.50**, not 0.06 — `Lground=Lup*0.5` is added unconditionally in each of the 4 lateral
  directions (`Fup=0.06` + `4×Fside(0.22)×0.5=0.44`). Setting it to 0.50 fixes the paradox gate (+5.39 °C)
  and open-field noon (64.3 °C). A prior "CLOSED" ruling based on a literature *abstract* rather than source
  code was wrong and was superseded. Note `W_H=0.06` in `openubem/microclimate/mrt.py:84` is still the
  correct *direct* top/bottom weight — do not "fix" it.
  *(same doc:3628)*
- **Fixing `Psi_grd` broke the previously-passing canopy-shade test (15.35 → 27.09 °C)** — not a physics
  regression: the shaded test case used `sh_veg=0.0` (total beam block) and `compute_tmrt`'s
  `beam_gate = sh_building * sh_veg` made `sh_veg` a no-op while `sh_building=False`. Correct test setup:
  `sh_building=True` **and** `sh_veg=DECIDUOUS_TAU_SUMMER` (0.20, `domain.py:162`) → 21.24 °C. Fixing a model
  constant can unmask a test-construction bug the wrong constant was masking.
  *(same doc:3787)*
- **[OPEN] `test_night_tmrt_close_to_ta` fails (Tmrt−Ta = −11.22 °C vs a required −5…0 °C)** — T12's ground
  physics were hand-verified and ruled out; the root problem is the tolerance itself, which has **no citation
  anywhere**. A primary source (Gál 2020, ICUC10) confirms SOLWEIG-class models under-predict nighttime Tmrt
  by 2–10 °C, but gives no citable replacement for the svf=1 open case. STOP, not fixed.
  *(same doc:3897)*
- **`pedestrian_wind_macdonald` returns physically impossible speeds (up to 834,439 m/s, even −19 m/s)** —
  `v_H = v10*ln((H-d)/z0)/ln((10-d)/z0)` assumes the 10 m reference sits above the canopy; with tall
  buildings the `max(10-d, ped_height_m)` floor can drive the log ratio's denominator to ~2.6e-6 →
  catastrophic cancellation. The pre-existing unit test only asserted `< free_stream` — too weak. Fix 1
  (E-UTCI-07): fall back to `cost730` whenever `10.0-d <= ped_height_m`, counted via a
  `wind_macdonald_domain_invalid_cell_hours` manifest field. Fix 2 (residual 84,439 cell-hours at cells the
  first trigger never flags): an **unconditional postcondition** — fall back to `cost730` whenever
  `0 <= v_1p1 <= v10` is violated, regardless of cause → 0 bound violations domain-wide. An epsilon guard on
  the log ratio was rejected (doesn't uniformly bound the output).
  *(same doc:4026, 4178)*
- **`ResimRefusedError` / `AnnualEnergyPlusWindowRefusedError`** — deliberate structural traps:
  `window_mode='annual'` with per-surface-per-hour output across a fleet is a multi-terabyte trap. Pass
  `override_annual=True` / `override_annual_energyplus=True` only when the size has been deliberately
  computed.
  *(openubem/microclimate/resim.py:162; openubem/microclimate/window.py:76)*

## 11. Visualization (3D viewer, matplotlib, basemaps)

- **Viewer scene reads as a "collapsed super-block" — one dominant purple mass swallowing the real towers** —
  not a geometry merge: 121/738 buildings (≈50% of ground area) had `no_height` in OSM, were imputed to 1
  storey / 3.5 m, and rendered with a confident viridis EUI colour. Largest case: Grand Central Terminal
  (`relation/11171793`, a legitimate 155,536 m² single OSM relation).
  *(docs/docs_DONE/VISUALS/3D-visualization/PLAN_3dviz_implementation.md T22)*
- **…and the fix over-fired: 85–100% of some cells rendered flat beige `#E4DFD6`** — `buildingFillColor`
  short-circuited on `heightMissing(attrs)` *before* the real EUI lookup, painting real simulation output
  over with beige at low opacity. Every building was actually simulated (`n_buildings == len(05_results.csv)`
  in all 12 cells). Fix: remove the short-circuit; footprint-only buildings show their real colour at full
  opacity with a dashed-outline legend indicator instead.
  *(docs/docs_DONE/VISUALS/3D-visualization/debug/PLAN_3dviz_debug_representation.md)*
- **Per-building translucency in a merged single-mesh scene** — "set material opacity per building" doesn't
  apply. Widen the vertex `color` attribute from itemSize 3 (RGB) to 4 (RGBA) with `material.transparent =
  true`; three.js auto-enables `USE_COLOR_ALPHA` (verified against pinned `three@0.155.0`).
  *(docs/docs_DONE/VISUALS/3D-visualization/PLAN_3dviz_implementation.md T22)*
- **`data_quality_flag` token matching breaks on the separator** — Step-1 `osm_fetcher.py` comma-joins its
  tokens, then `provenance.py::_append_flag` pipe-joins more onto that
  (`"no_floors,no_height,no_year|GROUPMODE_MED"`). Use a plain substring test (`flag.includes("no_height")`),
  not a split.
  *(same doc T18)*
- **3-hour hang regenerating 12 viewers, wall-clock cap never fired** — a single stuck Overpass retry hung the
  whole run because `with ThreadPoolExecutor() as ex:` blocks on exit (`shutdown(wait=True)`). Fix: run the
  fetch on a **daemon thread** with `thread.join(timeout)`; on timeout the wedged thread is abandoned.
  *(docs/docs_DONE/VISUALS/3D-visualization/manager_prompt/sonnet_manager_handoff.md)*
- **Overpass rate-limits mid-regen, large cells stall indefinitely** — the regen driver had been launched
  **twice concurrently**, both hammering the same endpoint, with no per-request timeout. Fix: exactly one
  driver instance; `ox.settings.requests_timeout = 60` plus a per-cell wall-clock backstop
  (`CELL_CTX_CAP_S = 240`); accept roads-only degradation rather than treating it as a bug.
  *(docs/docs_DONE/VISUALS/3D-visualization/manager_prompt/opus_manager_handoff.md)*
- **Headless Chromium can't create a WebGL context for LIVE_SMOKE screenshots** — `--use-gl=swiftshader`
  alone stopped working on Chrome 150.0.7871.24. Use
  `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`.
  *(docs/docs_DONE/VISUALS/3D-visualization/PLAN_3dviz_implementation.md T20)*
- **esbuild `--alias` for the vendored three.js bundle doesn't resolve on Windows** — relative
  `node_modules/...` alias targets depend on the invoking `cwd`. Use absolute resolved paths.
  *(same doc T17)*
- **"Where are the building footprints? it is just gray background"** — `plot_eui_map` read
  `05_results.gpkg`, which holds only **centroids**. Fix: read polygons from `01_buildings.gpkg` and
  left-merge the attribute columns from `05_results.gpkg` on `osm_id`.
  *(docs/docs_DONE/VISUALS/plotting/PLAN_plotting-suite_2026-06-16.md T10)*
- **Basemap tile fetch fails with an out-of-range zoom (the "zoom-22 class of bug"), or the basemap is
  blurry** — auto-zoom against point-source coordinates produces an invalid tile level; `zoom="auto"` also
  under-selects and then bilinearly upsamples. Fixes: an explicit fallback loop
  (`None → 17 → 16 → 15 → 14 → 13`) wrapped in try/except so a failure degrades to footprints-on-white; and
  step the zoom up past contextily's auto value until the native raster's long axis ≥ `target_px` (cap +3).
  *(same doc T10; docs/docs_DONE/VISUALS/3D-visualization/debug/PLAN_3dviz_debug_representation.md)*
- **A data-centre outlier (`counter_total_eui` ≈ 14,584) blows out the roundtrip scatter axis** — drop rows
  whose `openuben_archetype` contains `"DataCenter"` after the success filter in both `plot_roundtrip_scatter`
  and `plot_dev_ranked_bar`, recompute the displayed median, and caption the exclusion. Same functions also
  had to filter to `counter_status.str.startswith("success")` before aggregating — they were mixing failed
  counterpart simulations into the stats.
  *(docs/docs_DONE/VISUALS/plotting/PLAN_plotting-suite_2026-06-16.md T11 + correctness fix)*
- **`TypeError` in `viewer_app.mjs::_buildLegend()`** — thrown when a scene has zero CityObjects with a
  numeric `total_eui_kwh_m2`. Real, reproduced headlessly; initially misattributed as the cause of a reported
  "blank scene" (the real cause was a slow-loading 26 MB / 190k-surface file).
  *(docs/docs_DONE/SETUP/layoutAssigner/debug/storey-Matching/results/viewer_blank_diagnosis.md)*

## 12. Cluster / SLURM / SSH (Speed)

- **`tcsh` silently drops `cat > file <<EOF` sent over bare `ssh`** — no error, just an empty/missing remote
  file. Use `scp` for transfer and wrap every remote command in `bash -lc` (the `_ssh()` helper,
  `scripts/cluster/t08_harvest_results.py:104`).
  *(docs/docs_DONE/GENERAL/Resume_Prompts/monitorRun_resumeManager.md; CLAUDE.md)*
- **[OPEN] `_ssh` (`scripts/validation/v12_cell_pipeline.py:111-116`) never inspects `result.returncode`** —
  a failed `mkdir -p` at `:265` went unnoticed, then `scp` died with `dest open ... No such file or
  directory`, discarding 43 minutes of correct upstream work and **blaming the wrong operation**. 3 of 8 call
  sites share the bug (`:265`, `:457`, `:536` — the latter two discard a completed SLURM array). Worst site:
  `:325` in `poll_cluster` runs `squeue ... 2>/dev/null | wc -l`, so a suppressed `squeue` failure reads as
  `0` = "all tasks done" and the pipeline harvests results that were never produced. Also,
  `subprocess.run(timeout=...)` is never wrapped in a `TimeoutExpired` catch. Cost: 3 of 12 cells lost in one
  run. Remedy specified (`check: bool` raising on nonzero), not applied. (OPEN-54)
  *(docs/docs_ACTIVE/openings/extra/INVESTIGATION_open-54_ssh-unchecked-exit.md)*
- **A completion poller declares a SLURM array "complete" when the controller itself failed** — fixed by
  capturing `${PIPESTATUS[0]}` and requiring positive `sacct` corroboration (any of
  `{PENDING,RUNNING,REQUEUED,RESIZING,SUSPENDED,CONFIGURING,COMPLETING}` → re-poll; no states → re-poll), and
  by making `_ssh()` raise by default on remote failure.
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_ten-items-2026-08-18-late.md)*
- **Remote stderr `Unmatched '.` from tcsh, child exit 1, raised as `RemoteCommandError`** — long `_ssh`
  payloads hit a tcsh parse limit near ~8,192 bytes, but it is **intermittent, not a fixed threshold**: one
  bisection put the flip at 8,166–8,191 bytes, one byte *under* 8,192, ruling out a simple buffer
  explanation. A separate Windows-only CRLF-on-stdin fault returns a clean, plausible, silently-wrong `0` and
  is invisible on Linux. Mitigation: chunk `_ssh()` payloads well under 7,500 characters. (was OPEN-57,
  closed)
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-57_probe-length-threshold.md)*
- **`WinError 206` / truncated-quote errors fetching cluster results at fleet sizes ≥ ~150** — enumerating
  per-building paths inline hits the Windows 32,767-character command-line limit. Use a single streamed
  remote `find | tar --null -T -` pipe into a local `.tgz`.
  *(docs/docs_VALIDATION/step1/overAll/OPEN_QUESTIONS_R5.md OQ-R5-10)*
- **`fleet.lst` build produces 1778/1778 `cp` failures** — entries used slash-format osm_ids while the sbatch
  script builds `idfs/<entry>.idf`. Entries must be the IDF filename stem (underscore format, Unix LF).
  *(same doc)*
- **`.eio` files never present locally after a harvest** — 5 harvest scripts' `tar czf - --ignore-failed-read
  */eplusout.sql */eplusout.err */eplusout.end` fetch list simply never named `eplusout.eio`. Fixed at all
  sites. (OPEN-37)
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-37_eio-fetch-closure.md)*
- **[OPEN] ~2.14 GB of untrimmed per-task directories orphaned on scratch, no `task.rc` present** — the sbatch
  template's `set -e` kills the job script at the failure point, before the lines that write `RC=$?`/`task.rc`
  and run the disk-trim block, so a failed task keeps its full output (~48.6 MB vs ~0.3 MB trimmed).
  Reproduces in every fleet generation using the T08-derived template.
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-39-40_cluster-records.md)*
- **[OPEN] 874/875 E02 harvest directories missing `.sql`/`.end` while `.err`/`.eio` report "Completed
  Successfully"** — statistically indistinguishable from a healthy control (99.9% vs 100%), all-or-nothing at
  the batch level (exactly 2 of 60 `(cell, mode)` batches), so it is a **harvest-copy gap**, not a simulation
  failure. Cause not determinable further from `.err`/`.eio` (neither logs `Output:SQLite` request status).
  (OPEN-53)
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-53_missing-sql.md)*
- **A cell fails with the SSH connection dropped (sshd closed the connection, not a nonzero remote exit)** —
  a solo transport drop; no remote job existed, nothing harvestable, no cleanup needed. The fix that worked:
  retry the cell **alone** (a single `run_cell()` with nothing else queued in the process) — both failing
  cells succeeded on the first solo retry.
  *(docs/docs_ACTIVE/openings/extra/INVESTIGATION_open48-run4-cell-failures.md)*
- **A `grep -c` / `||`-fallback exit-code interaction corrupted a wait loop's exit condition** — it polled
  forever without ever detecting that the cluster job had finished; caught only by a manual live check.
  *(docs/docs_DONE/SETUP/layoutAssigner/debug/DONE/COMPLETION_REPORT_debug.md)*
- **Local-CPU-scaled wall-clock extrapolations for cluster runs are unreliable** — two recorded ~10× misses.
  Never gate `--time=` limits or go/no-go decisions on local timing extrapolation; measure on real nodes.
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_speed-probe-cost.md)*

## 13. Pipeline plumbing, Windows & parallelism

- **The cell driver hard-kills a whole cell (`sys.exit(2)`) when even 1 building is unsimulatable** — the
  zero-fail exit fired from **three different places across three rounds of hardening**: (1)
  `v12_cell_pipeline.py:1025-1030` `run_cell`; (2) 4 unconditional `sys.exit(2)` calls inside
  `verify_and_repair` (~line 561) that fire *before* the run_cell tolerance can act; (3)
  `dropped_buildings.csv` written into `results_dir` before Step 5 created it → `OSError: Cannot save file
  into a non-existent directory`. Fix: a `max(5, ceil(0.01*n_generated))`-tolerant logged-drop path at every
  gate + `results_dir.mkdir(parents=True, exist_ok=True)`.
  *(docs/docs_DONE/LOADS & SCHEDULES/hvac-ServiceLoads/remediation/PLAN_phaseE_CPD_remediation.md §9-10)*
- **A `print()` crashes the job on the Windows cp1252 console** — Unicode/emoji in log or verdict strings.
  Seen in the drop-log path (la_rural fan-out) and in `scripts/diagnostics/v19_phasec_rescore.py`. Fix:
  remove the glyphs; add `# -*- coding: utf-8 -*-`.
  *(docs/docs_REPORTS/REPORT_phaseE_final.md §10.4; docs/docs_DONE/SETUP/phaseC_combinedResim/PLAN_phaseC-combined-resim.md)*
- **Resim driver freezes mid-run: 4 nested python processes at ~0% CPU, no exception** — `joblib`'s `loky`
  backend (`run_step3(..., n_jobs=4)`) deadlocks intermittently under Python 3.14 on Windows (IPC deadlock,
  not compute). Fix: `n_jobs=1`, plus a skip-if-remote-done resumable fetch and a per-cell wall-clock timeout
  so one stuck cell can't freeze a 12-cell sweep.
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/phaseD_realHVAC/PLAN_phaseD_real_hvac_resim.md)*
- **One bad building crashes the entire serial generation loop** — the `n_jobs=1` path in `run_step3`
  (`builder.py:402-405`) had no try/except around `BuildingIDF(row).build()`, unlike the isolated loky path.
  Fix: mirror `_build_one`'s try/except, record `failed_worker_exception`, continue.
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/PLAN_geometry_generation_drops.md)*
- **Parallel-pool rules (Windows `spawn`)** — worker functions must be module-level (closures/lambdas can't
  pickle); child `print()` output is lost or interleaved, so buffer it and return it in the result dict;
  distinguish real pool crashes (`BrokenProcessPool`, OOM, segfault → re-raise) from application errors (bad
  IDF, applier exception → catch *inside* the worker, return `ok=False`) so one bad job doesn't abort the
  pool.
  *(docs/docs_DONE/SETUP/parallelProcessing/parallel_idf_prep_detailed.md)*
- **A batch of parallel E+ runs yields empty output dirs or odd fatals (`HVACTemplate:* objects found... must
  run ExpandObjects`, `Missing required property 'Building'`)** — a concurrency/harness artifact; re-running
  the same buildings **serially** completes cleanly (18 s, 0 severe). Always re-verify apparent failures
  serially before scoring them. Related: `SQLite database failed to open` fatal during local parallel runs is
  a filesystem lock artifact — re-run in a clean isolated directory.
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35_storey-intervention.md; docs/docs_DONE/BUGS/misclassification/RESUME_T11_fresh_manager_session.md)*
- **`move_to_runtime` throws `WinError 32` after a local E+ worker exits** — `eplusout.sql` stays locked, so
  `rmtree` of the temp source fails even though the copy already succeeded. Verify by counting
  `eplusout.end` files in `runtime/.../sim_out` (don't trust the exception), then delete the leftover
  `%TEMP%/ubem_validation/cases/<cell>` manually.
  *(docs/docs_DONE/GENERAL/Resume_Prompts/pahseC_resumeManager.md)*
- **Rerunning a cell's ship step doesn't pick up regenerated IDFs** — `ship_to_cluster`'s guard was
  `if not dst.exists(): shutil.copy2(...)`. Fix: unconditional copy, plus `rmtree` `fleet_staging/` and
  `sim_out/` before each regeneration (keep weather/step1/step2 caches).
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/PLAN_phaseC_geometry_fixbatch.md)*
- **`assign_climate_zones` crashes on a 1-row subset** — its "wrong continent" zero-Tier1 guard fires
  spuriously on a single repaired building. For single-row repairs, reuse the cached
  `02a_climate_epw.parquet` zone instead of re-deriving.
  *(docs/docs_DONE/GENERAL/Resume_Prompts/pahseC_resumeManager.md)*
- **A cell silently never ran** — it was simply absent from `CELL_CONFIGS` in `v12_cell_pipeline.py`
  (nyc_centre). Check the config table before debugging the pipeline.
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/PLAN_phaseC_geometry_fixbatch.md)*
- **Two concurrent background runs race on the same output directory** — a 376–752 MB raster of unknown
  provenance resulted; an `svf_mean` byte-match was wrongly taken as proof the race was harmless (SVF is
  deterministic geometry and matches regardless of interleaving). Always check for a live process
  (`Get-CimInstance Win32_Process`) before relaunching against a shared output path; **kill before
  delete-and-relaunch**.
  *(docs/docs_DONE/OUTDOOR/UTCI/implementation/sub-plans/DONE-PLAN_e-utci-09_height_backfill.md:1656)*
- **A background driver dies repeatedly with no explanation** — it was launched from inside a subagent turn
  and torn down when that turn ended. Launch turn-surviving background drivers from the main session only.
  Related: long-lived local background pollers get externally killed after an idle/lifetime threshold —
  decouple into short, re-armable per-cycle checks.
  *(docs/docs_DONE/BUGS/misclassification/RESUME_T11_fresh_manager_session.md; docs/docs_DONE/SETUP/phaseC_combinedResim/PLAN_phaseC-combined-resim.md)*
- **[OPEN] `FileNotFoundError ... .pytest_tmp\...\step3\idfs\way_R7.idf` inside `run_step3()` writing
  `03_idf_manifest.parquet`, despite an earlier `output_dir.mkdir(parents=True, exist_ok=True)`** — looks
  like a race or tmp-dir issue specific to the pytest session; not diagnosed, reproducibility unconfirmed.
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-24_live-gate.md)*
- **`run_ep_isolated()` silently produces no `eplusout.sql` (rc from the subprocess never even
  checked; `outdir` stays populated only with the `mkdir`) when the caller passes relative `Path`
  objects for `idf`/`epw`** — `run_ep_isolated()` sets `cwd=str(outdir)` on the `subprocess.run`
  call (`scripts/analysis/open35_storey_intervention_2026-08-19.py:107`) precisely to give every
  invocation its own working directory (the OPEN-58 fix); a relative `idf`/`epw` path resolves
  against the **new** `cwd` after the switch, not the caller's original directory, so EnergyPlus
  is pointed at a path that doesn't exist there and exits non-zero with `capture_output=True`
  swallowing the message. Fix: always pass `.resolve()`'d (absolute) `Path`s for `idf`, `epw` and
  `outdir` into `run_ep_isolated()`. *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_district-heating.md)*
- **`AttributeError: 'NoneType' object has no attribute '__dict__'` inside `dataclasses._process_class` ->
  `_is_type`, raised while loading a sibling analysis script via `importlib.util.spec_from_file_location` +
  `module_from_spec().exec_module()`** — the loaded module defines a `@dataclass`, and dataclasses' internal
  type resolution does `sys.modules.get(cls.__module__).__dict__`; a module built via `module_from_spec` is
  never registered in `sys.modules` unless the caller does it explicitly, so the lookup returns `None` and
  `.__dict__` fails. Fix: `sys.modules[spec.name] = module` **before** `spec.loader.exec_module(module)`.
  *(scripts/analysis/open61_census_build_2026-08-20.py, loading open61_census_read_2026-08-20.py's
  `DistrictHeatingRead` dataclass by file path)*
- **`FileNotFoundError: [Errno 2] No such file or directory: '...\idfs\<safe_id>.idf'` from
  `eppy.modeleditor.IDF.save()` inside `BuildingIDF.build()`** — the success path
  (`openubem/idf/builder.py:642-643`) writes straight to `output_dir / "idfs" / f"{safe_id}.idf"` without
  creating the `idfs` subdirectory itself (only a different branch, `:713`, does
  `(output_dir/"idfs").mkdir(exist_ok=True)`). Every caller of `.build()` must pre-create
  `(output_dir / "idfs").mkdir(parents=True, exist_ok=True)` before calling —
  `open35_storey_intervention_2026-08-19/20.py`'s `build_arms()` already does this; a fresh caller that only
  creates `output_dir` itself (not its `idfs` child) hits this. Fix: create the `idfs` child directory, not
  just `output_dir`, before `.build()`. *(scripts/analysis/open61_census_build_2026-08-20.py T02)*

- **A multi-hour analysis run dies mid-way with no traceback; its background-task log contains only `[killed]`** —
  a long job launched through the agent harness's own background-task mechanism is a child of the session and is
  terminated when the session is compacted or the task is stopped. The OPEN-61 fleet census lost its process this way
  after 5 hours and 7,354 of 8,153 buildings; only the flushed CSV rows survived. Fix: launch any run longer than a
  few minutes as a **detached OS process** instead — `Start-Process -FilePath py -ArgumentList "-3",<script>
  -RedirectStandardOutput <log> -RedirectStandardError <err> -WindowStyle Hidden -PassThru` — and watch its log file
  rather than its stdout; and give the runner a **resume path** (read the osm_ids already in the output CSV, run only
  the complement, open the CSV in append mode) so an interrupted run never has to be repeated.
  *(scripts/analysis/open61_census_build_2026-08-20.py T03)*
- **`shutil.rmtree(work_dir, ignore_errors=True)` leaves `sim_out/eplusout.sql` behind on Windows** — the SQLite
  file is still open (or held by the OS) when cleanup runs, so the unlink fails, `ignore_errors` swallows it, and the
  directory survives holding just the `.sql`. Effect is twofold: a per-building cleanup meant to bound disk use
  instead accumulates ~2.5 MB per building (41 GB over the fleet census), **and** a re-run of that building reads a
  stale `eplusout.sql` if EnergyPlus fails, silently parsing the previous run's results. Fix: delete the work dir
  explicitly before re-running a building, and treat leftover `.sql` files as a corpus to be inventoried rather than
  as cleanup that succeeded. *(scripts/analysis/open61_census_build_2026-08-20.py T03)*

## 14. Test suite: collection aborts, fixtures, benign noise

- **`AttributeError: module 'openubem.semantic.imputation' has no attribute '_draw_tier'` at
  `tests/test_draw_methods.py:645` → `Interrupted: 1 error during collection`, exit 2, ZERO of 1,937 tests
  collected** — a class body (`class TestNoEUILeakage`, line 631) evaluates the symbol at import time, so one
  broken file aborts the whole suite. `@pytest.mark.skip` on the class does **not** help — the body still
  executes. Fix: module-level `pytest.skip(..., allow_module_level=True)` naming the blocking item, or gate
  with `_HAS_DRAW_TIER = hasattr(imp, "_draw_tier") and hasattr(imp, "_draw_stratum_col_for")` +
  `@pytest.mark.skipif`. The underlying feature (OPEN-17's draw tier) was deliberately never implemented.
  *(docs/docs_ACTIVE/openings/extra/FIX_open-13_height-cache-and-collection.md)*
- **`AttributeError: module 'openubem.config' has no attribute 'IMPUTE_DRAW_METHOD_BY_TARGET'` /
  `IMPUTE_DEBIAS_NEWERSKEW` (9 tests)** — one root cause, not 9 defects: tests were committed ahead of a
  feature that was never wired in. Before treating this shape as a live defect, run
  `git log --all -S<symbol>` on the target module. Same pattern hit fusion:
  `AttributeError: ... 'FUSION_SOURCES_BY_TARGET'` → 25 failed / 4 passed, because `fusion.py` and its 29
  spec tests landed but the six `FUSION_*` config keys and `_fusion_tier`'s body did not.
  *(docs/docs_ACTIVE/openings/extra/FIX_five-more-items-2026-08-13.md; docs/docs_DONE/OUTDOOR/UTCI/implementation/sub-plans/DONE-PLAN_e-utci-09_height_backfill.md:1523)*
- **`FileExistsError [WinError 183]` / `(rm_rf) error removing ...: OSError [WinError 145]` from two
  concurrent pytest sessions** — a fixed `--basetemp=.pytest_tmp` in `pyproject.toml` means a second session's
  `rm_rf` wipe races the first session's live writes. Deleting the `addopts` line is **not** the fix: this
  machine's OS temp root throws `PermissionError [WinError 5]` on
  `C:\Users\o_iseri\AppData\Local\Temp\pytest-of-o_iseri`. Correct fix: a repo-local **per-session-numbered**
  basetemp. (OPEN-52, closed)
  *(docs/docs_ACTIVE/openings/extra/FIX_open-52_pytest-basetemp.md, FIX_open-52_temproot-remedy.md)*
- **Running the suite silently rewrote a checked-in fixture** (`tests/fixtures/synthetic_30_archetype_coverage.gpkg`;
  one rewrite already committed in `6aeebb0`) — the `synthetic_30_gdf` session fixture wrote its GeoPackage to
  the checked-in path (GDAL's GPKG driver writes through a filename). Fix: write to `tmp_path_factory`.
  (OPEN-50)
  *(docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md)*
- **The suite baseline is `pytest -q tests/`** — a bare root-level `pytest -q` reports ~36 false failures.
  *(project convention; see MEMORY index)*
- **Benign noise, never a failure: `Windows fatal exception: access violation` / `<cannot get C stack on this
  system>`** — joblib/loky worker-spawn noise under Python 3.14 on Windows, localized around
  `test_step3_orchestrator.py::test_parallel_byte_identity` and `test_sim_integration.py`. The run still
  reports the full pass count. Check the exit status, not the stdout dump. Documented independently in at
  least five arcs.
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-46_path-verification.md; docs/docs_DONE/BUGS/zoningBug/PLAN_zoning-multifloor-fix.md; docs/docs_TODO/layoutgenerator/debugs/PLAN_design_buildout_by_archetype.md:501)*

## 15. Exceptions raised by the `openubem` package

Grep target for "which module can throw this, and what does it mean?"

### `openubem/acquisition`
- **`ValueError: Input schema gate: missing/extra columns / expected 26 columns`** / **`archetype_id '...'
  not in 30-element vocab`** — the 26-column contract into the climate-zone join. *(climate_zone.py:45,48,50,55)*
- **`RuntimeError: zero_tier1_matches`** — every building missed the within-county join → wrong continent /
  uncovered territory, not a per-building gap. **`unmatched_buildings`** — check input CRS.
  **`invalid_zone_tokens`** — county lookup table corrupt. *(climate_zone.py:121,165,176)*
- **`ValueError: EPW check 2/4 failures`** — first line isn't `LOCATION,...`, unparseable, or row count isn't
  8760/8784 → the mirror served a truncated file. *(epw_manager.py:94,97,122)*
- **`RuntimeError: epw_cold_cache_offline` / `epw_all_tiers_exhausted`** — `fetch_epw(offline=True)` with an
  empty cache, or all mirrors failed. *(epw_manager.py:247,273)*
- **`FileNotFoundError: height_cache.load_cached(...): no cached Overture pull`** — the reader never fetches;
  run `pull_overture(cell)` first. **`ValueError: pull_overture: '<cell>' is not one of the 4 affected
  cells`** — it's a manual E-UTCI-09 entry point, never call it from CI. *(height_cache.py:65,105)*
- **`ValueError: Schema error: ... / expected 23 columns / 'osm_id' not unique`** — OSM ingest output failed
  its 23-column schema/dtype/uniqueness contract. **`Exactly one of {location, bbox, osm_path} must be
  set`**. *(osm_fetcher.py:100,121,132,534-552)*
- **`ValueError: fetch_overture: one of slice_path or endpoint must be given.`** *(overture_fetcher.py:52)*

### `openubem/geometry`
- **`ValueError: patch_envelope: row[...] is null/missing for archetype_id=...`** — requires Step-2 semantic
  enrichment; refuses to silently default an envelope column. *(envelope_patcher.py:86)*
- **`ValueError: unknown resolution_mode: ...`** *(zoning.py:35)*
- Gotcha: `layout_assigner.py:69` carries a comment flagging the bug its task fixed — read it before touching
  that code.

### `openubem/idf`
- **`ValueError: osm_id=...: epw_path ... is missing or does not exist`** — refuses to build at the
  template's placeholder `Site:Location` (0,0). *(builder.py:241)*
- **`KeyError: archetype_id '...' not found in hvac_cop_by_archetype.json`** — regenerate with
  `extract_prototype_cop.py`. *(hvac.py:645)*
- **`RuntimeError: intersect_match failed after one_zone_per_floor reroute`** — the second attempt also
  failed; re-raised for `_build_one`. *(surfaces.py:801)*
- Gotcha: `surfaces.py` lines 339, 565, 663, 771, 773 are **silent** `logger.warning` fallbacks (bbox / skip
  the zone or block) that never raise — grep them when geometry looks degraded but nothing threw.

### `openubem/semantic`
- **`ValueError: use_floor_count=True requires levels, got None`** *(building_classifier.py:214)*
- **`SchemaError` family** — override archetype not in vocab, duplicate osm_id in the override CSV, I/O
  column count/order mismatch, invalid `archetype_confidence`/`archetype_source`, or an `OpenUBEMUnknown` row
  missing its required LOW+FALLBACK_UNKNOWN / OVERRIDE_USER provenance. *(building_classifier.py:501-583)*
- **`ValueError: fusion: zero-fitted-params violation -- EUI column(s) ... must never be read`** — structural
  guard; no adapter may read an EUI column. *(fusion.py:39; imputation.py:176)*
- **`KeyError: fusion: unknown source '...'`** *(fusion.py:156)* · **`NotImplementedError`** on
  `FusionSource.available/.join` *(fusion.py:136,143)*
- **`ValueError: impute_column: method='ml' requires model_path` / `bounds must be provided for PDE
  imputation` / `unknown method`** *(imputation.py:71,105,113)* · **`build_ml_imputer: unknown method`**
  (frozen `_ML_METHOD_NAMES`; no tuning path exists by design) *(imputation.py:253)*
- **`BelowFloorError(method, n_observed, floor)`** — too few observed rows to fit. **`StrictImputationError`**
  — strict mode found still-missing targets. *(imputation.py:420,936)*
- **`ValueError: Loads table gap: no row for archetype(s) [...]`** — add it to
  `doe_prototype_loads.json`/`openstudio_loads.json`. **`Setpoint inversion at rows [...]`** (DESIGN §3D/F15).
  *(loads.py:142,154)*
- **`KeyError: No schedule library entry for archetype '...'`** *(schedules.py:51)* ·
  **`ValueError: confidence must be one of {...}`** *(provenance.py:63)*
- **`ValueError: enrich_semantics input gate: missing columns / null epw_path / null climate_zone`**
  *(semantic/__init__.py:101-109)* · **`validate_schema: expected 57 columns / last 28 columns mismatch / NaN
  in appended column / out of range / setpoint invariant violations`** (DESIGN F19 gate)
  *(semantic/__init__.py:118-177)*
- **`ValueError: OPEN-55 donor screen: excluding [...] empties the Unknown PDE donor pool`**
  *(semantic/__init__.py:264)*

### `openubem/simulation`
- **`ValueError: build_task_list: missing epw_path for N simulable buildings`** *(parallel.py:50)*
- **`RuntimeError: EnergyPlus binary not found at <exe>`** — set `ENERGYPLUS_PATH`. **`Could not parse
  EnergyPlus version` / `EnergyPlus version mismatch: expected ..., found ...`** vs
  `config.ENERGYPLUS_VERSION`. *(runner.py:31,38,43)*

### `openubem/microclimate`
- **`ValueError: Domain: <name>.shape != dsm.shape`** *(domain.py:58,60)* · **`build_vegetation(tier='cdsm')
  requires cdsm_path and tdsm_path`** *(domain.py:183,214)*
- **`air_temperature_field(tier='tier1') requires svf and altitude_deg`** *(airtemp.py:105,109)* ·
  **`pedestrian_wind(tier='macdonald') requires buildings_gdf, domain, wind_direction_deg`** *(wind.py:279,288)*
- **`read_epw_hourly: <n> data rows, expected 8760 or 8784`** *(epw_hourly.py:54)* ·
  **`write_geotiff: data shape != domain.shape`** *(raster_io.py:70)*
- **`scenario='tree_canopy'/'pv_canopy' requires canopy_gdf`** *(scenarios.py:136-178)* ·
  **`select_window(...)` mode/keys errors** *(window.py:52,72,83)*
- **`FileNotFoundError: run_step6: neither 01_buildings_clean.gpkg nor 01_buildings.gpkg found` / `no IDF
  archive at <cell>_step3_idfs_archive.zip`** · **`unparseable EPW LOCATION line`**
  *(microclimate/__init__.py:58,94,153)*
- **`ResimRefusedError` / `AnnualEnergyPlusWindowRefusedError`** — deliberate multi-terabyte traps (ch. 10).

### `openubem/results`, `validation`, `viz`
- **`AssertionError: T10/T11 CROSS-CHECK GATE FAILED`** — see ch. 9. *(draw_leaderboard.py:326; impute_scatter.py:253)*
- **`RuntimeError: I2 breach: foreign osm_id in work dir for '...' (abort whole run)`** — DESIGN §3B
  integrity check. *(parser.py:253; results/__init__.py:173)*
- **`FileNotFoundError: 05_results.gpkg / 01_buildings.gpkg not found for cell '...'` / `No phased cells
  found under ...`** *(plotting_suite.py:72,103,105,681)* · **`phase_<n> folder has zero PNGs`**
  *(impute_montage.py:58)*
- **`ValueError: Fractions for '<key>' sum to X, expected 1.0 ± 1e-3`** *(service_loads.py:53,58)*
- **`ValueError: eui_impact_report: observed/imputed arrays must be paired`** *(eui_impact.py:143)* ·
  **`assign_spatial_blocks: no usable postcode/block column and no 'geometry' column`** *(mask_recover.py:124)*
- **`ValueError: buildings_gdf has no CRS`** *(basemap_raster.py:125)* · **`No manifest rows with a matching
  footprint centroid.`** *(cityjson_emitter.py:109)* · **`IDF file not found` / `No BuildingSurface:Detailed
  objects in <idf_path>`** *(geometry_extract.py:64,514)*
- Gotcha: `results/__init__.py:230,245` turn figure-rendering and viewer-export failures into non-fatal
  `warnings.warn` — check the warnings if a figure or viewer is unexpectedly missing.

- **`AttributeError: 'str' object has no attribute 'idfobjects'` from `compute_band_map()`** — the
  function takes an already-loaded eppy/geomeppy IDF object, not a path string. Fix: load the file
  first (`IDF(path)`) and pass the object. *(openubem/geometry/layout_assigner.py; hit while
  re-deriving `n_proto` during the CP-3 audit, 2026-08-20)*

## 16. Method traps: how these bugs got misdiagnosed

- **Diff against the actual committed baseline, not against sibling code paths in the same tree.** The `auto`
  regression passed every conservation test because those tests only compared modes *within one working
  tree*, all carrying the same new bug. *(§4)*
- **Include a non-degenerate fixture in every conservation/invariant test.** The `building`-mode
  `/num_floors` undercount was invisible to the original test because all its fixtures were single-floor. *(§4)*
- **A prior artifact is never a matched control.** An EUI before/after comparison silently inverted sign
  (+4.30% reported vs −0.99% true) because a script hardcoded reference values from an earlier artifact while
  other pipeline state (classification, HEAD) had moved. (E-LA-24)
- **"Content is right" and "locator is right" are two independent claims.** A citation's data matched
  digit-for-digit while every section/table number was fabricated. Verify DOIs at
  `https://api.crossref.org/works/<doi>` — two cited DOIs resolved to unrelated papers or 404'd. Also
  distinguish link rot from fabrication before concluding a source doesn't exist. (OPEN-47)
- **Decompose an aggregate shift by end-use per-building before writing a causal story.** A large regression
  attributed to "removing a service-load overlay" was ~90% a heating-only effect; the earlier version's
  apparent accuracy was a compensating-error coincidence (oversized PTAC heating filling the gap). *(§9)*
- **An imprecisely-recalled defect-ID list in a code comment hides a live defect from grep sweeps.** A
  comment at `layout_assigner.py:863-865` misattributed E-LA-16 (cooling-coil UA autosize) to the unrelated
  warmup-convergence family for weeks. (OPEN-51)
- **A monkey-patch stub / literal string / hardcoded threshold message rots silently.** See the 4-arg lambda
  (§4), the one-space `** Severe **` literals (§8), and a gate whose failure message hardcodes "< 80% gate"
  regardless of the configured threshold.
- **Re-verify apparent parallel failures serially, and verify process liveness independently.** Concurrency
  artifacts, tool-level timeouts silently killing a LIVE_SMOKE, and stale duplicate background processes have
  each produced false failure reports here. *(§13)*
- **A subagent that ends its turn waiting on a background/cluster process is marked complete mid-work.**
  Don't assume a dispatched agent resumes itself after a long wait.
- **Never widen a gate or tune a constant after seeing a FAIL.** Band and threshold changes must be proposed
  as pre-run spec changes. *(§9)*
- **A regex object-splitter bounded only by the next occurrence of the SAME keyword corrupts the last
  object of every file.** A hand-rolled IDF reader that sliced `BUILDINGSURFACE:DETAILED` blocks between
  successive `^BUILDINGSURFACE:DETAILED,` matches let the last such block's slice run to end-of-file,
  so its vertex regex picked up every subsequent object's numbers too (any trailing `SHADING:*`,
  `FENESTRATIONSURFACE:DETAILED`, etc.). Fix: split the whole file on blank lines first
  (`\n[ \t]*\r?\n`, verified separator style for this generator), then filter blocks by keyword —
  every block is self-contained regardless of position in the file.
  *(scripts/analysis/open03_envelope_decomposition_2026-08-20.py; docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_envelope-decomposition.md)*
- **Summing every `Surface Type "floor"` object as "total floor area" silently doubles buildings that
  carry an unconditioned Attic zone.** An Attic zone's own floor surface (OBC `Surface`) sits at the
  same elevation as the conditioned zone's ceiling below it — same physical plane, second object — so
  a naive floor-type sum counted it twice (measured 538 m² vs the correct ~255 m² on one fixture). The
  IDF already carries the fix: every `ZONE` object's `Part of Total Floor Area` field (Yes/No) is
  E+'s own signal for which zones' floor area counts; restrict any floor-area sum to zones where that
  field is not `No` instead of guessing from zone names.
  *(scripts/analysis/open03_envelope_decomposition_2026-08-20.py; docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_envelope-decomposition.md)*
- **A "distinct wall min-Z elevation" storey-count method silently collapses to 1 band whenever
  a building's `GlobalGeometryRules` `Coordinate System` is `Relative` AND the file encodes each
  repeated floor band's elevation in the `ZONE` object's own `Z_Origin` field rather than in the wall
  vertices themselves** — every wall vertex then reads a near-zero LOCAL Z regardless of the true
  floor elevation, because the method (`open03_envelope_decomposition_2026-08-20.py`'s `parse_idf()`)
  never adds the owning zone's `Z_Origin` back in (unlike `layout_assigner.compute_band_map()`, which
  does this correctly, lines ~490-497). Measured zone-by-zone across all 18 `layout_assign`
  baseline-mapped archetypes present in the fleet (not assumed): **severe** in `MidriseApartment`
  (18/27 zones), `HighriseApartment` (18/27), `TallBuilding` (145/164), `SuperTallBuilding` (232/256),
  `Outpatient` (59/118), `SecondarySchool` (21/46) — together 2,983/8,160 buildings (36.6 % of the
  fleet); **immaterial** in `LargeOffice` (3/23 zones, none floor-area-counting) and
  `QuickServiceRestaurant`/`FullServiceRestaurant` (the 1 affected zone in each is non-floor-area);
  **absent** in the other 10 mapped archetypes (`ZONE.Z_Origin == 0.0` uniformly, absolute Z baked
  directly into wall vertices). **Tracked as OPEN-62 from 2026-08-20.**
  **Blast radius bounded the same day (director, at the source): production code does NOT share this
  omission** — `layout_assigner.py:471` reads the zone `Z_Origin` and `:491-493` adds it back before
  `min(v[2])`, and `openubem/viz/geometry_extract.py:143-155` does the same; no third production
  reader counts storeys from wall Z. The defect is confined to `parse_idf()` in
  `open03_envelope_decomposition_2026-08-20.py` and the one script that imports it, so it is a
  **measurement-instrument erratum, not a geometry defect**.
  **FIXED 2026-08-20 (T01, `PLAN_open62-z-origin-and-three-rulings-2026-08-20.md`)** —
  `parse_idf()` (`scripts/analysis/open03_envelope_decomposition_2026-08-20.py:117-224`) now mirrors
  `layout_assigner.py:465-495`: it reads `GLOBALGEOMETRYRULES`' `Coordinate System` and each `ZONE`'s
  own `Z Origin`, adding it into the wall-vertex minimum before rounding when the file is `Relative`.
  The fix is additive — `storey_count` is the corrected value, `storey_count_naive` is the untouched
  pre-fix value, and C9a confirms `storey_count_naive` reproduces the pre-fix
  `open03_envelope_decomposition.csv` exactly (96/96 arm-rows, 48 buildings × 2 arms). **The
  building-level falsifiable prediction (C12) only partly held**: at the whole-building `storey_count`
  level (not the zone level the severity table above counts), only 4 of the 6 named archetypes
  actually move — `HighriseApartment`, `MidriseApartment`, `SuperTallBuilding`, `TallBuilding`.
  `Outpatient` and `SecondarySchool` hold at delta 0 despite their severe zone-level counts, because
  those two archetypes mix encodings: other zones on the same floor already bake their elevation
  directly into wall vertices, so the floor's band is already present in the naive set and the
  `Z_Origin` correction lands on a band that was already there. Verified directly on both archetypes'
  baseline IDFs (zone-level wall-Z-base sets identical before/after correction). Restated fleet
  census and control C9b are T02. 🔴 **C9b RAN AND FAILED 2026-08-20 (T02/CP-2), and the failure
  changes what this entry means.** Checked against `layout_assigner.py`'s own origin-aware reader,
  the corrected parser agrees on only **12 of 18 archetypes**; 6 disagree over **3,734 buildings**
  (`TallBuilding` 11 v 20, `SuperTallBuilding` 16 v 30, `Warehouse` 2 v 1, and 1 v 2 on
  `FullServiceRestaurant` / `QuickServiceRestaurant` / `SmallOffice`). Traced on
  `TallBuilding.idf`: floor surfaces give **20** distinct elevations, all wall bases 20, exterior
  wall bases 19, and *exterior wall bases in floor-area-counting zones* — what this function actually
  counts — give **10** (`0.0, 4.9, 23.8, 55.3, 72.8, 88.6, 104.4, 118.4, 132.4, 135.9`, i.e. the
  levels where a new exterior wall STARTS). 🔴 **So `storey_count` is not a storey count — it is the
  number of distinct exterior-wall base elevations in floor-area zones, and it undercounts any
  building whose facade spans multiple floors.** The `Z_Origin` fix above is correct and necessary
  but **NOT sufficient**. ~~any value read from this column is a **lower bound**~~ -- **WITHDRAWN at
  CP-3, see the director's correction at the end of this entry: it is not a bound in either
  direction.** Do not treat this entry as closed: the `Z_Origin` symptom is fixed, the quantity is
  still wrong.
  **T06 ADDS `storey_count_floor` 2026-08-20** (`PLAN_open62-z-origin-and-three-rulings-2026-08-20.md`,
  ruling R7): `parse_idf()` (`open03_envelope_decomposition_2026-08-20.py:118-236`) now also counts
  distinct origin-corrected elevations among ALL `Surface Type "floor"` objects, **unfiltered by
  zone** (R7's own wording carries no zone filter, and this is the value that reproduces CP-2's
  "Floor surfaces (the independent reader)" measurement, 20 on `TallBuilding.idf`) -- exposed as
  `layout_assign_storey_count_floor` in `open03_storey_census_zfix.csv`, additive, `storey_count`
  and `storey_count_naive` untouched. **T06's own "How" text said to apply the wall path's zone
  filter "so the two are comparable"; that filtered value does NOT reproduce the pre-registered C14
  targets** (on `TallBuilding` it collapses to 11, coinciding with the wall-base `storey_count`,
  because a zone's floor sits at the zone's own base elevation and the filter drops 9 of the file's
  20 distinct zone-Z levels entirely -- 155/164 zones are floor-area-counting but concentrate on
  only 11 Z values). Resolved in favour of the unfiltered reading (matches R7's own definition, the
  calling task's explicit statement that "C14 targets come from the floor-surface reader", and the
  numeric targets themselves); the filtered variant is kept in `parse_idf()`'s return dict as
  `storey_count_floor_zonefiltered` for reference but is not written to any CSV. **C14 result:
  `storey_count_floor` agrees with `layout_assigner.compute_band_map()`'s `n_proto` -- a second,
  independently implemented floor-surface reader in production code -- on all 18/18 baseline-mapped
  archetypes**, including the 6 archetypes C9b found the wall-base method disagreeing on. **C16
  (storey_count_floor >= storey_count, allowed to fail) found 38/8,160 violations, all one
  archetype: `Warehouse`** (wall-base reads 2, floor-surface reads 1) -- not reconciled; a
  wall-based elevation with no matching floor plate (e.g. a mezzanine/dock-door wall segment) is
  the kind of case the wall method could over-count relative to floors, distinct from the
  under-counting story C9b told. **C17 restates C13's built mean/max as values, not lower bounds,
  using `storey_count_floor`: mean 2.94 (>= C13's 2.25 lower bound), max 30 (>= C13's 16 lower
  bound).** The module docstring's stale "KNOWN CAVEAT ... NOT fixed here" paragraph is now rewritten
  to describe both symptoms and both fixes in sequence rather than claiming either is unfixed.
  🔴 **DIRECTOR'S CORRECTION, CP-3 2026-08-20 — three claims above are wrong and are corrected here.**
  (a) **The `Warehouse` mechanism is not a mezzanine.** Measured directly on the preserved prototype
  (`scratchpad/open03_proto_saved/Warehouse.idf`): exterior wall z-bases are `{0.0: 8 walls,
  4.267: 2 walls}` while FLOOR surfaces are **3, all at z = 0.0**. It is a single-storey high-bay
  facade split into two vertical wall bands. (b) **`storey_count` is therefore NOT a lower bound** --
  it under-counts `TallBuilding` (20 -> 11) and `SuperTallBuilding` (30 -> 16) and **over-counts**
  `Warehouse` (1 -> 2). It is unbounded in both directions; C13's 2.25/16 survive only because
  `floor < wall` happens to occur **0 times** inside the 5,714-row unmatched subset, which is an
  accident of archetype mix. (c) **C17's 2.94 may NOT be published as a value: `storey_count_floor`
  counts an ATTIC as a storey.** Verified origin-corrected on the prototypes: `SmallOffice.idf`
  z = 3.05 carries **9 floor surfaces, every one in zone `Attic`**; `FullServiceRestaurant.idf` and
  `QuickServiceRestaurant.idf` (both `Relative`) carry zone `attic` at z = 3.049. All three are
  one-storey prototypes reported as 2. That is **3,580 buildings (43.9 % of the fleet)** and **2,797
  of the 5,714 unmatched rows (48.9 %)**; attic-corrected, the built mean is **2.45**, not 2.94. The
  publishable statement is the **range 2.45 - 2.94**. (d) Consequently **C14's 18/18 agreement with
  `compute_band_map()`'s `n_proto` does not certify a storey count** -- `n_proto` is documented in
  production as *"deliberately left as the measured Z-BAND COUNT, never a represented-storey count"*
  (`openubem/geometry/layout_assigner.py:404-406`). This is **not a production defect**; production
  branches `match_storeys()` on it and never publishes it as storeys. 🔴 **Net: no reader in this
  codebase returns a storey count** -- naive collapses `Relative` files to 1, wall-base is unbounded
  both ways, floor-surface counts attics. ⚠️ **Do not "fix" this by excluding zones named `Attic`** --
  zone-name matching is the generalisation A1 already falsified (F-07, `layout_assigner.py:389`), and
  it would move archetypes across `match_storeys()`'s `n_proto` branches, which that docstring warns
  against by name.
  *(scripts/analysis/open03_storey_census_2026-08-20.py; scripts/analysis/open03_envelope_decomposition_2026-08-20.py; docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_storey-census.md; docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md §6 OPEN-62)*

## 17. Not-a-bug: expected behaviour & accepted limitations

- **E+'s 10 m³ minimum-volume clamp warning is universal and benign as a *warning*** — and the `.err`
  "Volume ≤ 0" line is **anti-correlated** with pathology: a healthy 44-zone LargeOffice carries 44 of them
  while the runaway single-zone schools carry 1 each. Do not use it alone as a defect signal. (But see §1:
  the underlying negative-volume clamp *is* a real ≈+1% EUI understatement.)
  *(docs/docs_DONE/LOADS & SCHEDULES/hvac-ServiceLoads/remediation/PLAN_phaseE_CPD_remediation.md §9)*
- **Small uniform EUI offsets between Windows and Linux (Speed) EnergyPlus runs are expected float/platform
  rounding.** Only a *structural* delta (tens of kWh/m², concentrated in one archetype) is a regression.
  *(docs/docs_DONE/SETUP/Simulation_Resolution/resolution_sets/PLAN_resolution_mode_switch.md M17)*
- **Food-service archetypes running +423 kWh/m² above the phaseE benchmark is a stale-anchor artifact** — the
  on-disk benchmark predates the cooking/DHW/refrigeration realism commits (`b2ca38f`, `e8e03d2`) and has
  `refrigeration_eui=0`. Non-food archetypes bit-reproduce phaseE (mean |Δ| = 0.004).
  *(same doc M16)*
- **An imputer's predicted-vs-actual scatter looking "flat" vs the 1:1 diagonal is inherent variance
  collapse**, not a bug — any single-best-estimate imputer pulls toward the conditional mean under the
  zero-fitted-parameters rule. Judge a stochastic-draw imputer (`pmm`) on histogram/ECDF, not the scatter.
  *(docs/docs_DONE/INPUTS/imputation/implementation/IMPLEMENTATION_phaseC_ml_imputer.md:127)*
- **CBECS/CV(RMSE)/KS gate failures are structural and report-only** (§9). **`knn_fill` filling 0 rows on a
  100%-missing cell is the MNAR guard working** (§7). **Fusion sources skipping when unconfigured is by
  design** (§7). **Warmup non-convergence under `thermal_mass=True` is a known, non-blocking side effect**
  (1.29% → up to 64% prevalence depending on segment; `status` stays `success`) — but it is *not* proven
  cosmetic for accuracy (OPEN-09).
- **A missing E+ install mapping / version mismatch fails loudly by design** — `runner.py` refuses to run a
  binary whose `--version` doesn't match `config.ENERGYPLUS_VERSION`.

## 18. Currently open items (register snapshot 2026-08-20)

Authoritative list: `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md` (20 tracked, next free
ID OPEN-61). Snapshot only — always re-read the register before acting.

| ID | One-line |
|---|---|
| OPEN-09 | `thermal_mass=True` warmup non-convergence; ~3.66% fleet EUI-projection consequence untouched |
| OPEN-10 | `ZoneGroup` list multiplier could restore exact expressibility; narrower than first claimed |
| OPEN-12 | rural `height_m` residual (nyc_rural 36.4%, austin_rural 19.2%); needs source coverage, not another imputation pass |
| OPEN-13 | draw-tier test-collection abort contained via skip, not fixed (E-UTCI-13 leg closed) |
| OPEN-14 | UTCI height backfill not reproducible from a clean checkout |
| OPEN-15/16/17 | imputation tiers built but switched off; the draw tier is not a simple opt-in |
| OPEN-19 | LA cells run ~+40% hot; no climate-zone/code-year switch exists yet |
| OPEN-20 | wider validation matrix still needed |
| OPEN-27 | DESIGN doc still names the wrong term (live code now pinned against it) |
| OPEN-28 | `05_results` archetype_id not reproducible from frozen input (§6) |
| OPEN-35 | two fallbacks fill the same missing storey count and disagree |
| OPEN-38 | `layout_assign` SmallHotel laundry-room thermal runaway + unfitted doors (§2) |
| OPEN-42 | thermal-mass recovery fix never merged into production (§2) |
| OPEN-48 | the adopted baseline run cannot be reproduced from this repository |
| OPEN-51 | defect ID `E-LA-16` used for two contradictory failure signatures (§16) |
| OPEN-53 | 874/875 E02 harvest dirs missing `.sql`/`.end` (§12) |
| OPEN-54 | `_ssh` never checks the remote exit code (§12) |
| OPEN-55 | Unknown-archetype PDE bounds can draw data-centre loads (§7) |
| OPEN-56 | 10 m³ zone-volume stub fleet-wide, ≈+1.0 kWh/m² understatement (§1) |
| OPEN-58 | `run_ep()` shared-cwd cross-contamination + wrong EUI formula (§8) |
| OPEN-59 | Unknown buildings still run 1.7× classified after the equipment fix (§7) |
| OPEN-60 | `total_eui_kwh_m2` undercounts lighting/equipment under zone multipliers (§8) |

---

*Maintenance: when a debug/measurement doc lands, add its distinct, reusable failure modes here in the same
`**Symptom** — cause -> fix. *(path)*` form. Keep `[OPEN]` markers current against the register.*
