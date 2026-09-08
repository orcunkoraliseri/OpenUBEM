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
  sign=1.0)` before `build_zones` in `openubem/idf/builder.py`. **Measured energy cost, 2026-08-26 (EU S2,
  31 buildings):** the volume clamp alone understates ACH-driven ventilation loss **57.74×**; repairing the
  volume without re-winding still leaves **−11.8 %** on heating demand, with EnergyPlus's own reported zone
  floor area, zone volume, exterior gross wall area and heat-transfer surface count **byte-identical**
  between the two runs — the vertex *sets* match and only their *order* differs. **No area- or
  volume-based geometry check can detect this class of defect.** Recurrence note: this entry already
  carried the correct fix when `scripts/run_eu_s2_campaign.py` shipped with the defect, so the entry was
  not consulted. *(docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md §12.20, FINDING EU-S2-08)*
  *(docs/docs_DONE/LOADS & SCHEDULES/hvac-ServiceLoads/debugs/DONE_10_fails.md; docs/docs_REPORTS/REPORT_phaseE_final.md §5)*
- **The same `orient()` fix is deliberately skipped in `auto` mode** — the guard at
  `openubem/idf/builder.py:464-465` excludes `auto`, which is the mode the published fleet EUI was built in;
  `GetVertices: ... is upside down!` therefore fires on 8,160/8,160 `auto` buildings. Underlying library
  defect: geomeppy 0.12.2's `is_clockwise()` returns `False` unconditionally on its CCW branch, so
  `invert_orientation()` never fires. Root cause fully localised 2026-08-21: CORE zones (0% stubbed) escape
  this because geomeppy's `core/perim` path re-derives the core polygon via `Polygon2D.buffer()`
  (`geomeppy/geom/polygons.py:104-113`), which internally calls the *real* `shapely.geometry.polygon.orient
  (sign=1.0)` unconditionally — a different, working `orient()` than the one openubem gates off. That
  correction never runs for the `by_storey`/WHOLE path (`geomeppy/idf.py:263-267`, used by
  `one_zone_per_floor`/`single_zone`), which extrudes the raw, unoriented footprint coordinates — 100%
  stubbed. PERIM zones (95.75% stubbed) sit in between because `core_perim.py`'s `get_perims()` mixes the
  correctly-oriented core boundary with the original (unoriented) footprint edge points. Winding itself was
  left alone (remedy shape (a), extending `orient()` to `auto`, was explicitly not authorised — sign
  unverified, changes geometry fleet-wide); fixed instead by writing `Zone.Volume` explicitly (below). (OPEN-56)
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-56_writer-localisation.md;
  docs/docs_ACTIVE/openings/extra/FIX_open-56_zone-volume.md)*
- **Every building simulates with a 10 m³ zone-volume stub** — understates EUI by a fleet-stratified
  mean **+0.98%** (median +0.84%, up to +3.25%), direction-consistent in 65/69 sampled buildings. Magnitude
  does *not* scale with zone count (refuted, corr=+0.113): best model is a fixed ≈+1.0 kWh/m² per-building
  offset. Fixed 2026-08-21 (T02, `rulings-and-fixes-2026-08-21` plan): `BuildingIDF.build()` now calls
  `_write_zone_volumes(idf, extruded_zones)` (`openubem/idf/builder.py`, right after the extruded-zones guard
  and before `assign_constructions()`), which sets each `ZONE` object's `Volume` field explicitly to
  `floor_area x height_m` — floor area summed from that zone's own `FLOOR`-type
  `BUILDINGSURFACE:DETAILED` objects (`idf.getsurfaces("floor")`, real post-extrusion geometry, not the
  zones-dict `floor_polygon` which CORE/PERIM zone dicts share as the whole-building placeholder footprint
  and would give the wrong area), height from the zone's own `height_m` (floor-to-floor height, correct for
  every zone role already). **Not applied to the published baseline** (153.8231 over 8,153 is unchanged —
  no fleet re-run was part of this fix). (OPEN-56)
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_ten-tasks-2026-08-18-night.md;
  docs/docs_ACTIVE/openings/extra/FIX_open-56_zone-volume.md)*
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
- **[OPEN] `** Severe ** RoofCeiling:Detailed=... Vertex size mismatch between base surface ... and outside boundary surface` on every interzone ceiling/floor pair of one building, then `** Fatal ** GetSurfaceData: Errors discovered, program terminates` - on a building that was ALREADY in `one_zone_per_floor`** - so the recorded remedy for the entry above (reroute to `one_zone_per_floor` and re-check) cannot apply: this building started there. Measured on `BATIMENT0000000240879534_part0` (Lyon, `AB`, 7 storeys), the single `EPLUS_FATAL` of the 96-building `S3` campaign. 🔴 **Both paired objects are written with 12 vertices**, so the mismatch is produced INSIDE EnergyPlus by its own collinear-vertex removal, not by the writer emitting different counts. What makes the two sides decide differently: the footprint carries **one exactly collinear vertex** (turn `0.0000` deg, perpendicular deviation `0.000000 m`) at the end of a **0.200 m** segment, three more within 1.4 mm of collinear, and the mirrored interzone pair differs in the **last decimal digit** of its coordinates (`642384.787910771` against `642384.7879107706`). The footprint itself is valid, simple, 13 ring vertices, no duplicate points, minimum segment 0.200 m - so a footprint-validity check passes it and tells you nothing. ⚠ **Not fixed, deliberately.** The obvious remedy - snap mirrored interzone surfaces to bit-identical coordinates, or drop near-collinear vertices before extrusion - changes corpus geometry and the accepted `S2` IDF hashes, and this arc has already had to refuse one corpus-wide vertex remedy that rested on a limit that did not exist (ch.1, the withdrawn ~120-vertex `BuildingSurface:Detailed` ceiling). Recorded as one classified failure of 96 with the measurement attached, and put to the owner in `ACCEPTANCE_S3_promotion_2026-08-27.md` §5.2.
  *(openubem/outputs/eu_evidence/EU-04/s3/s3_campaign/FR-LYO-HAUTCOEURPENTES/BATIMENT0000000240879534_part0/eplusout.err; openubem/outputs/eu_evidence/EU-04/s3/s3_campaign_manifest.csv)*
  **Recurrence (EU-11, Speed, 8 buildings):** the exact same building recurs — `BATIMENT0000000240879534_part0`
  is Lyon `fleet.lst` entry 31 (stem `b2d90c2cba300225`), same 12-Severe+1-Fatal `GetSurfaceData` fatal,
  `task.rc=1`. The identical symptom class (RoofCeiling:Detailed vertex-count mismatch on an interzone
  ceiling/floor pair → `GetSurfaceData` Fatal) also hit 4 other Lyon buildings (`BATIMENT0000000240880205_part0`,
  `..0227_part0`, `..0573_part0`, `..1541_part0`; 2/4/6/12 severe, 1 fatal each) and 3 Madrid buildings
  (`way/287696585`, `way/434026690` — 4 severe each; `way/434878262` — 8 severe; 1 fatal each). 8/1,340 EU-11
  Speed runs total. Same disposition: not fixed, each carried as one classified `EPLUS_FATAL` row (blank
  `heating_kwh`/`eui_kwh_m2`, real `eplus_return_code`/`severe_errors`/`fatal_errors`) in its district manifest.
  *(openubem/outputs/eu_evidence/EU-11/FR-LYO-HAUTCOEURPENTES/fr_lyo_hautcoeurpentes_manifest.csv;
  openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE/es_mad_berruguete_manifest.csv)*
  **Recurrence 2 (EU-14, Bologna, Speed job `1295646`, 2 buildings):** `dc5cb4dcddab40d3` (`AB`, 8-severe,
  1-fatal, `RoofCeiling:Detailed` on `_1` block interzone pairs) and `524073ad3c85f685` (`MFH`, 6-severe,
  1-fatal, `_WHOLE` block interzone pairs) — identical symptom, identical `GetSurfaceData` Fatal, `task.rc=1`.
  10/2,544 EU-11+EU-14 Speed runs total. Same disposition: not fixed, carried as classified `EPLUS_FATAL`
  rows in `it_bol_galvani2_manifest.csv` once harvested.
  **Recurrence 3 (EU-13B T09, Madrid/Lyon/London resimulation, Speed jobs `1297338`/`1297355`/`1297373`):**
  identical symptom, much higher incidence — Madrid 38/952 (was 4/961 pre-T09), Lyon 6/283 (was 7/297),
  London 4/80 (was 1/82). Sample-checked directly (`efd148a964fbbb14`, Madrid): same `RoofCeiling:Detailed`
  vertex-count mismatch (9 vs 10) on a `BLOCK ..._0 STOREY 3/2 FLOOR/CEILING` interzone pair, same `rc=0`,
  1-fatal signature as every prior recurrence. The T04 ruled-grid/T05 morphology geometry creates far more
  interzone ceiling/floor surface pairs per building (many dwelling sub-zones per storey instead of one),
  so more chances for this pre-existing EnergyPlus collinear-vertex float-precision defect to trigger — the
  higher count is an increased-exposure effect of T09's own geometry change, not a new defect. Same
  disposition: not fixed, each carried as one classified `EPLUS_FATAL` row (blank `heating_kwh`/`eui_kwh_m2`)
  in its district's post-T09 manifest, never smoothed into the pooled EUI.
  *(openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE/es_mad_berruguete_manifest.csv;
  openubem/outputs/eu_evidence/EU-11/FR-LYO-HAUTCOEURPENTES/fr_lyo_hautcoeurpentes_manifest.csv;
  openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS/gb_ldn_stdunstans_manifest.csv)*
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
  Same crash also seen ending mid-line inside a `SizeWaterCoil:` warning during plant sizing, on a
  43-storey LargeHotel (`nyc_centre way/266170763`, OPEN-61 census): 0 Severe / 0 Fatal in `.err`,
  no `.end`, a 318 MB `.eso` and a 305 MB `.sql` that has 36 tables but **no `TabularDataWithStrings`**,
  and a 15.6 GB working set at death. Diagnostic that separates OOM from a real fatal: open the `.sql`
  and test for `TabularDataWithStrings` — a controlled fatal still writes it, an OOM crash never does.
  Fix: none available in-process; the building is recorded as a null-with-reason census row, not retried.
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-41-38_failure-causes.md;
  docs/docs_ACTIVE/openings/implemenation/previous/PLAN_open61-census-open03-storeys-2026-08-20.md)*

- **`** Fatal ** Errors occurred on processing input file` from `energyplus.exe` on an extruded real
  footprint, with no preceding Severe that names a geometry object** — the footprint's exterior ring
  carries more vertices than a `BuildingSurface:Detailed` can hold. Measured on
  `BATIMENT0000000240877527_part0` (Lyon BD TOPO, AB, 5 storeys): 173 exterior vertices against the
  IDD's ~120-vertex field limit, so E+ fails during input processing rather than during simulation.
  Nothing upstream simplifies the ring: `build_zones(..., strategy="one_zone_per_floor")` uses
  `exterior.coords` verbatim, so any dense historic parcel can hit this. Fix: none applied — found
  inside the EU-04 `S1` measurement task and recorded fail-closed as `EPLUS_FATAL`, a named refusal,
  never an energy result. Candidate remedy for a later, explicitly scoped item: a vertex-budget
  simplification (`shapely.simplify` with an area-preserving tolerance) before extrusion, with the
  simplification error recorded per building. *(docs/docs_ACTIVE/europeanLocations/prompts/previous/EXECUTOR_PROMPT_EU-04_s1_smoke_2026-08-25.md;
  openubem/outputs/eu_evidence/EU-04/s1_smoke_manifest.csv)*

  🔴 **CORRECTED 2026-08-26 by the 4J side while vetting an external report that repeated this
  entry back to us. Both halves of the diagnosis fail, and the entry stands only as a record of what was
  believed.**

  * **There is no ~120-vertex `BuildingSurface:Detailed` limit.** Checked in `C:\EnergyPlusV22-1-0\
    Energy+.idd` and `C:\EnergyPlusV24-2-0\Energy+.idd`: the object carries `\extensible:3`,
    `\min-fields 20`, and **no `\max-fields`**, and the IDD's own note reads *"shown with 120 vertex
    coordinates — **extensible object**"*. 120 is what the IDD prints, not a ceiling. The fatal was
    attributed to a limit that does not exist, on an error message that named no geometry object.
  * **The failure no longer reproduces.** `EPLUS_FATAL` appears **nowhere** in
    `openubem/outputs/eu_evidence/EU-04/`. `s1_smoke_manifest.csv`, regenerated **2026-08-26 12:10**,
    reports **12 of 12 `EPLUS_COMPLETED`** with the layout axis unchanged (8 `NON_CONVEX_FOOTPRINT`,
    3 `NARROW_FOOTPRINT_LT_8M`, 1 `DWELLING_LAYOUT_EMITTED`) — the same 12 buildings, re-run.
    `BATIMENT0000000240877527_part0` ends *"EnergyPlus Completed Successfully — 0 Severe Errors"* in
    **all three** campaigns: `s1_smoke` (26 warnings), `s2_campaign` (24), `s2_campaign_v2` (19).

  ⚪ **The candidate remedy above should not be executed as written.** An external round proposed
  exactly it — Ramer-Douglas-Peucker at `epsilon = 0.15 m` on every cadastral polygon — rated Tier 1
  on the non-existent IDD limit. Applying it would change the geometry of the whole corpus to fix a
  defect that is gone. If ring density is later shown to cause a **reproducible** fatal, the remedy is
  re-opened **with the new measurement attached**.

  🔴 **The lesson this entry now carries is the useful part: a recorded blocker outlives the
  blockage.** The refusal was real when written on 2026-08-25 and false by 2026-08-26, while three
  documents still cited it. *(Cross-reference:
  `GSSCanada-main/4J_docs_occ/DeepResearchPrompts/VETTING_RL28_RL29.md` §1.4–§1.5;
  `GSSCanada-main/4J_docs_occ/Step10_docs/4thJ_10_ubemRealStock.md` §6.5.)*
  🔴 **`MVP_european_locations.md` §EU-04 still reads "11 of 12 `EPLUS_COMPLETED` ... 1
  `EPLUS_FATAL`" and needs the same correction from its owner.**

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
- **[OPEN] `** Severe  ** Temperature (low) out of bounds [-289.29] for zone="EU_CELL_ZONE"` / `Temperature (high) out of bounds (202.24]`, ending `EnergyPlus Terminated--Fatal Error Detected. 58 Warning; 125 Severe Errors`** — the European equivalent-envelope cell is an ill-posed heat-balance problem: massless (`Material:NoMass`) envelope, an unenclosed zone, and windows hosted on `OtherSideCoefficients`. Surface temperatures diverge to physically impossible values during warmup. Not caused by any harness code; the same IDF can also complete with a plausible-looking number, so the failure is intermittent. Mitigated (not cured) by `Timestep 12`, which is the only tested change that stabilises without moving the answer. Still unfixed; `D-EU-27` was ruled Option B on 2026-08-28 and mitigation, not cure, was adopted — `Timestep,12;` in both campaign entry points plus a three-replicate bitwise-identity filter, which leaves 191 of 510 cells certified. *(docs/docs_ACTIVE/europeanLocations/implementation/previous/PLAN_finding181-stability-2026-08-28.md §7 T04)*
- **[OPEN] `** Severe  ** Convergence error in SolveForWindowTemperatures for window …_WINDOW_EAST_1` followed by `Program exited before simulations began`** — same European cells, fatal during sizing after ~0.4 s with `severe error count=1`. The window solver cannot converge because the window's host surface carries `OtherSideCoefficients` rather than a real exterior boundary. Same root cause and same open decision as the entry above. *(docs/docs_ACTIVE/europeanLocations/implementation/previous/PLAN_finding181-stability-2026-08-28.md §7 T04)*
- **A European campaign cell exits `0`, is recorded `completed: true`, `severe_count: 0`, `fatal_count: 0` with no `.err` marker — and returns a different heating value on the next identical run** — measured at 429401.898 kWh twice and 111864.121 kWh once (−74.0 %) for `uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000`, in **strictly serial** mode, from a byte-identical model. Neither `completed: true` nor a clean `.err` screen is sufficient to certify a cell; only replication detects it. Fix: none — `D-EU-27` (ruled Option B, 2026-08-28) certifies a cell only when three independent replicates return a bitwise-identical `heating_kwh` with `severe_count = 0` and `fatal_count = 0`; the worst disagreement that filter rejected was 382.1 %, so it must never be relaxed to two of three. *(docs/docs_ACTIVE/europeanLocations/implementation/previous/PLAN_finding181-stability-2026-08-28.md §7 T01, T03)*
- **`idf_sha256` differs between two runs of the same campaign cell although the model is identical** — the IDF's `Schedule:File` `File Name` field holds the *absolute* path, written verbatim by `openubem/semantic/european_schedules.py:119` (`File_Name=str(output)`), so the digest embeds the run directory. Diffing two such IDFs shows exactly one differing line and the referenced CSVs are byte-identical. Fix: none applied — the digest is a run identifier, not a model-provenance key; no published figure is affected. *(docs/docs_ACTIVE/europeanLocations/implementation/previous/PLAN_finding181-stability-2026-08-28.md §7 T01)* `FINDING 263` (2026-09-07, EU-11 London, D-EU-108 T05b): a *second*, distinct cause of the same symptom, reproduced on a **same-process double build** of a row whose `geometry_outcome` is `*_INTERZONE_MISMATCH_REROUTED` or whose `fallback_reason` is `near_duplicate_vertex_tolerated_box` (`way/1432262694`, `way/298850495`) — real ULP-level vertex/volume shifts and, in one case, an inserted wall surface with the subsequent walls renumbered, i.e. the near-duplicate-vertex tolerance path itself is not deterministic. Fix: none applied here — every `idf_sha256` identity gate (`D-EU-107`, `D-EU-108`, `D-EU-109`) must exclude the `*_INTERZONE_MISMATCH_REROUTED` / `near_duplicate_vertex_tolerated_box` population and state the excluded count; a gate quoted `N/N` without naming that exclusion is not a passed gate. `D-EU-109`'s ring cleanup removes these buildings from the tolerated/reroute path entirely, at which point the control becomes valid over the full population; `D-EU-109` T03 re-runs it that way. *(docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-london-coverage-2026-09-07.md, `CP-4` director countersign + T05b)*

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

- **[CLOSED 2026-08-27] `generate_european_dwelling_layout` returns `FALLBACK_PENDING_LAYOUT / PARTITION_AUDIT_FAILED`
  with `partition_audit.failures = ('AREA_GAP', 'OUTSIDE_FOOTPRINT')` at an `area_error_fraction` of
  5.09e-12** - the emitted partition is exact; the audit fails on float noise. Cause: the generator rotates
  the footprint about the literal coordinate origin (`openubem/geometry/european_residential.py:504`,
  `affinity.rotate(..., origin=(0.0, 0.0))`) while `audit_european_floor_partition` compares against an
  **absolute** `topology_tolerance_m2=1e-8` (`openubem/geometry/european_residential.py:643`). The noise
  therefore scales with distance from (0,0): the same building emits a clean layout in EPSG:32631
  (~642000, 5070000) and fails in EPSG:2154 (~852000, 6519000). Layout success is CRS-dependent, so a
  census run in Lambert-93 would report near-zero emitted layouts for the same corpus. Not fixed - found
  inside a measurement task (EU-04 `S1-EXEC-01` CP-1, 2026-08-25) and recorded rather than remedied;
  candidate fix is rotation about the footprint centroid and/or a footprint-area-relative topology
  tolerance. Workaround in force: S1 runs in the manifest's native `EPSG:32631`.
  **CLOSED by measurement 2026-08-27.** Both candidate fixes are in the code today: `generate_european_dwelling_layout` rotates about `footprint.centroid` (`openubem/geometry/european_residential.py:511`) and the audit is called with `EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION`, a footprint-relative tolerance (`:536`).
  Re-measured over all **297** Lyon attribute-ready rows in both projections: emission agrees **297 of 297** between `EPSG:32631` and `EPSG:2154`. Two consequences that must be read together. **(a)** The dependence is gone, so a census run in Lambert-93 would no longer under-report. **(b)** The same fix changed the corpus result: the **10** rows `s1_layout_reachability_census.csv` recorded as `PARTITION_AUDIT_FAILED` now emit, so Lyon's emission is **28 of 297**, not 18, and `layout_contract_ceiling.json`'s 64.3 % survival calibration is withdrawn in `layout_contract_ceiling.CORRECTION.json`. The native-CRS rule is kept anyway - it costs nothing and it is what the ruling pinned.
  *(openubem/outputs/eu_evidence/EU-04/s3/s3_scope_measurement.csv; openubem/outputs/eu_evidence/EU-04/D-EU-22/layout_contract_ceiling.CORRECTION.json)*
  *(docs/docs_ACTIVE/europeanLocations/prompts/previous/EXECUTOR_PROMPT_EU-04_s1_smoke_2026-08-25.md:115)*
- **Ruled dwelling partition silently emits empty cells, and the run reports `HABITABILITY_GATE_FAILED_AFTER_ROTATION` on ~84 % of the fleet (coverage ~16 % instead of ~97 %)** — the equal-area bisection cuts a footprint with axis-aligned blade rectangles built as `box(mid, -1e6, 1e6, 1e6)`. A footprint left in **absolute UTM coordinates** has a northing near 4.9×10⁶ m, outside the blade, so every intersection is empty, the cell count never matches the requested dwelling count, and the loop falls through to the habitability reason token — which is a **misattribution**, not the real cause. Fix: translate each footprint to its own centroid before partitioning (`affinity.translate(fp, -fp.centroid.x, -fp.centroid.y)`), exactly as the sample execution does; measured fleet coverage went 15.76 % → 97.05 % over the same 2,544 buildings with no other change. 🔴 A reason token emitted by fall-through is not evidence of that failure mode — check the cell count before believing the token. *(docs/docs_ACTIVE/europeanLocations/EXAMPLE_dwelling_layout_validation_2026-08-28.md §8)*

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
- **London EU-11 fleet only 82/1,242 residential buildings (6.6 %) — not a coverage failure, `_gb_rows`
  (`scripts/run_eu_s2_district_campaign.py:187`) simply never mapped OSM's `house` tag (1,018 of 1,242
  buildings) to any TABULA building type; the mapping dict only recognised `apartments`/`detached`/`terrace`.**
  Confirmed empirically by re-running `_gb_rows` against the full manifest and reading its `Counter` exclusion
  reasons directly, not by inspecting code alone: `UNMAPPABLE_RESIDENTIAL_TYPE` was 345 of the 1,160 excluded
  (the rest: 445 no EPC match, 355 EPC-period-straddle, 15 missing storeys). First fix attempt (`"house":
  "SFH"`) was wrong: `openubem/semantic/european_archetype_mapping.py:28-30` documents *why* — "OSM `house`
  cannot distinguish SFH from TH... must not be promoted... without supplementary evidence" — a `house` tag
  covers both detached and mid-terrace, which have materially different envelope heat loss. Correct fix: split
  by footprint adjacency (`compute_footprint_adjacency`, already used for FR/IT) — `"TH" if is_attached else
  "SFH"` — same pattern as Bologna's `_it_rows:262-267`. Verified result for London: 82 → 389 buildings
  (all recovered ones are `TH`, zero `SFH` — architecturally correct for dense inner-London terraces, and a
  useful sanity check that the fix isn't guessing). The shared cross-country function
  (`map_observed_building_to_tabula`) only runs this two-signal derivation for `country == "FR"` — Madrid's
  analogous `house`/`residential` gap (~81 buildings) is NOT yet fixed, needs the same treatment extended to
  ES plus a check that Spanish cadastral data (`observed_dwellings`) is actually populated for those rows.
  *(docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v5.md, `FINDING 251`; `CHECKLIST_european_locations_v5.md`, `eu-nocore-full-fleet-expansion` T01)*

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
  *(docs/docs_ACTIVE/openings/extra/PROPOSAL_open-55_unknown-pde-bounds.md; docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md)*
- **[OPEN] `ImportError: cannot import name 'recover_pairs' from 'openubem.validation.mask_recover'`** —
  `openubem/results/impute_scatter.py:63` imports a name that does not exist in `mask_recover.py` (the
  module only defines `mask_and_recover`); the module fails at import time, before its own
  `config.IMPUTE_DRAW_METHOD_BY_TARGET` unguarded read at `impute_scatter.py:235` (F7) is ever reached.
  `openubem/results/draw_leaderboard.py:174` has no such import problem and does reproduce F7's
  `AttributeError: module 'openubem.config' has no attribute 'IMPUTE_DRAW_METHOD_BY_TARGET'` on first
  use of `_draw_pairs`. Both modules are orphaned (OPEN-17: `ml`/`draw` are intentionally not in
  `IMPUTE_ENABLED_TIERS`); not fixed here — no tier is promoted or wired by this measurement.
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-17_tier-census.md)*
- **`HTTP Error 429: Too Many Requests` / `HTTP Error 504: Gateway Timeout` from
  `https://overpass-api.de/api/interpreter` during city-scale building extracts** — the public Overpass
  instance grants only ~2 concurrent slots per IP and drops large `area(...)`/`out geom` queries under
  load; two extract jobs running in parallel produced 429 and district-sized queries produced 504.
  Fix: serialise the extracts (one job at a time), retry with increasing backoff (20/40/60 s) and skip
  outputs that already exist, then re-run only the failed units. Mirrors are not a reliable fallback —
  `overpass.kumi.systems` returned `HTTP Error 502: Bad Gateway` and `overpass.private.coffee` timed
  out for the same query the main endpoint later served. All twelve EU-02 extracts completed this way.
  *(docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md §4)*
- **Building counts silently wrong when a WGS84 bbox is passed to `ingest_buildings` in GeoJSON order** —
  `openubem/acquisition/osm_fetcher.py:43` forwards `bbox` to `osmnx.features.features_from_bbox`, whose
  signature in the pinned osmnx 1.9.3 is `(north, south, east, west)`, while GeoJSON/`shapely.bounds`
  order is `(west, south, east, north)`. Passing the GeoJSON order produces an empty or nonsensical
  extract rather than an error. Fix: convert explicitly at the call site — the DESIGN order is
  `(n, s, e, w)`, as `osm_fetcher.py:82` already documents for the warning payload.
  *(docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md §4.5)*
- **A residential filter over OSM tags returns almost nothing in Italian and French cities** — the
  `building=yes` share measured 2026-08-24 is 65.5 % in a dense Bologna area statistica and 61.1 % over
  the whole Lyon commune (cadastre imports set no use tag), versus 1.5–27 % in Madrid barrios. Any
  count from `openubem/data/osm_to_use_class.json` alone is therefore a *tagging* measurement, not a
  stock measurement, and a density ranking built on it partly ranks mapping completeness (Islington's
  Barnsbury ward: 83.8 % unknown, 43rd of 58 on residential/km²). Fix: for IT/FR join a non-OSM
  classifier before applying any residential gate. **Resolved and measured 2026-08-24:** ISTAT 2011
  section variables `E3`/`E1` for Italy (60 of 71 screened Bologna units then pass the 0.60 dominance
  gate, against 2 on OSM; in the selected unit OSM sees 31 residential buildings and ISTAT 1,010), and
  IGN BD TOPO® V3 `batiment.usage_1/usage_2` via `data.geopf.fr/wfs/ows` for France (11 of 36 Lyon
  quartiers then pass, against 0). Both also carry the attributes OSM lacks — dwellings, storeys,
  height, construction date, wall material.
  *(docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md §6)*
- **`data.geopf.fr` WFS `GetFeature` returns `"features": []` with HTTP 200 and no error message** — the
  IGN Géoplateforme WFS 2.0 rejects the WFS-standard `BBOX=<lat>,<lon>,<lat>,<lon>,EPSG:4326` axis order
  silently and yields an empty, entirely plausible-looking FeatureCollection. Fix: give the bbox as
  `BBOX=<west>,<south>,<east>,<north>,CRS:84` (lon,lat); the same request then returns
  `numberMatched="107347"` over the Lyon commune. Add `SORTBY=cleabs` before paging with `STARTINDEX`,
  or pages silently overlap.
  *(docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md §4.2)*
- **ISTAT 2011 section breakdowns do not sum to the residential-building total (`E4+E5+E6 = 1,140` vs
  `E3 = 1,010`)** — the `dati-cpa_2011` archive ships no data dictionary, and the intuitive reading
  (`E4` = first construction-material class) is off by one: `E4` is *edifici utilizzati ad uso non
  residenziale*, so material is `E5..E7`, period `E8..E16`, storeys `E17..E20`, dwelling units
  `E21..E26`, state of repair `E28..E31`. Fix: never assume the positions — verify with the five
  identities that must each equal `E3`, plus `E2 − E3 = E4`, over the whole comune before use.
  *(docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md §0 item 5)*
- **Joining ISTAT census variables to a municipal section layer matches zero rows** — ISTAT's `SEZ2011`
  is the 12-digit national code (`370060000001`) while a comune's own published layer carries the local
  section number (`sez2011 = 1`). Fix: join on `int(NSEZ) == int(sez2011)` inside the comune, not on the
  full code; a silent zero-match here produces a complete, all-zero ranking table rather than an error.
  *(docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md §4.3)*
- **Opendatasoft Explore v2.1 `group_by` returns `{"total_count": N, "results": []}`** — the aggregation
  is only emitted when `limit > 0`; with `limit=0` the endpoint answers with the row count and an empty
  result list, which reads as "no distinct values". A companion trap: aliasing the grouped field in
  `select` (`select=descrizion as v&group_by=descrizion as v`) returns **HTTP 400 Bad Request**. Fix:
  `?group_by=<field>&select=count(*) as n&limit=30&order_by=n desc`, no alias on the grouped field.
  *(docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md §4.4)*
- **`HTTP Error 403: Forbidden` from `data.ademe.fr/data-fair/api/v1/datasets/<slug>/lines`** — the
  human-readable slug (`dpe03existant`) is accepted by the catalogue endpoint but not by `lines`. Fix:
  resolve the numeric dataset id from `/datasets?q=dpe&select=id,title,count` and call
  `/datasets/meg-83tjwtg8dyz4vv7h1dqe/lines?size=0&bbox=<w>,<s>,<e>,<n>`.
  *(docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md §4.5)*
- **`URLError [SSL: CERTIFICATE_VERIFY_FAILED] self-signed certificate in certificate chain` against
  `servizigis.regione.emilia-romagna.it` / `geoportale.regione.emilia-romagna.it`** — the Emilia-Romagna
  geoportal serves its WFS behind a CA that is not in the Python trust store. Fix: do **not** disable
  verification for a data source of record; substitute an equivalent authority — here the Comune di
  Bologna Opendatasoft portal (`c_a944ctc_edifici_pl`) plus ISTAT, both of which cover the same need.
  *(docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md §4.7)*
- **A selected site's `unit_code` names a different unit than the geometry and counts on the same row** — in
  `eu02_site_measurements_v2.{csv,json}` the Lyon site carried `unit_code = 8075`, which resolves to
  *Quartier Saxe Roosevelt*, while every measured field on that row (0.3753 km², 868 buildings, 544
  residential, 1,449.6 per km², 6,387 dwellings) belongs to quartier `7016`, *Haut et Cœur des Pentes*. The
  name and the numbers were taken from the selected row of the ranking frame and the identifier from a
  different one; because no arithmetic depends on the code, every sum, share and checksum still verified and
  the error survived the whole review. Fix: derive the identifier from the same row as the measurement, and
  before writing a site packet assert that `(unit_id, unit_name, area_km2, residential)` all agree with the
  candidate ranking file the site was chosen from. Corrected to `7016` on 2026-08-24.
  *(docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/EU02_neighbourhood_selection_2026-08-24.md §8.1)*
- **`HTTP 400` with body `No se puede procesar su peticion.` from every request to `https://ovc.catastro.meh.es/INSPIRE/wfsBU.aspx`, including a bare `GetCapabilities`** — the Spanish Catastro INSPIRE WFS **rejects the literal `curl/*` `User-Agent` and nothing else**; the status is 400, not 403, so it reads as a malformed request and sends you off editing query parameters that were correct all along. **Measured on 2026-08-27, same URL, four clients:** `curl/8.5.0` → **400**; `python-requests/2.32.3` → **200**; a custom `OpenUBEM/1.0` → **200**; an **empty** `User-Agent` → **200**. So it is not a browser check and it is not a bot policy — it is a curl blocklist, which is why a `requests`-based probe of the same endpoint never sees it and a shell probe always does. Fix: send **any** `User-Agent` other than curl's default (`curl -A ''` is enough). **Second trap behind the first:** once reachable, `ListStoredQueries` shows the service exposes only `GetBuildingByParcel`, `GetFeatureById`, `GetBuildingPartByParcel`, `GetOtherBuildingByParcel` and `GetAllConstructionByParcel` — **every stored query is keyed on a cadastral reference**, so a stored-query `bbox=` request answers `Paremter REFCAT can't be null` (the service's own spelling). ⚠ **Corrected 2026-08-27, same day, by a parallel measurement:** an **ad hoc** `TYPENAMES=bu:Building` + `BBOX=` `GetFeature` **does work** — it requires the `,urn:ogc:def:crs:EPSG::4326` suffix on the bbox and **lat,lon** axis order, and `TYPENAME` singular is rejected. What is true is narrower: **no *stored query* is bbox-keyed.** The earlier `HTTP 500` on that form came from the missing browser `User-Agent`, not from the form. Either route answers a coverage question: the ad hoc bbox `GetFeature`, or the INSPIRE **ATOM bulk download** (province feed → municipality zip → stream-parse the GML). *(docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-22_s3_attribute_source_2026-08-27.md §7)*
- **`curl` returns `HTTP 000` with 0 bytes for `https://www.catastro.minhap.es/INSPIRE/...` while the same path under another host works** — the `catastro.minhap.es` host is dead (connection never establishes), and because the failure is a connection failure rather than a 404 it produces an empty file and an empty grep rather than an error anyone notices. Fix: use `https://www.catastro.hacienda.gob.es/INSPIRE/...`; the ATOM root, the province feeds and the municipality zips are all served there. Note the path is case-sensitive on the download leg (`/INSPIRE/Buildings/28/28900-MADRID/A.ES.SDGC.BU.28900.zip`). *(docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-22_s3_attribute_source_2026-08-27.md §7)*
- **Every request to `https://epc.opendatacommunities.org/api/v1/domestic/search` returns `301 Moved Permanently` and lands on a GOV.UK landing page, and the same path on the new host returns `HTTP 404`** — the MHCLG EPC open-data host has been **retired**, not moved path-for-path: it now 301s wholesale to `https://get-energy-performance-data.communities.gov.uk/`, whose own guidance states *"You need to sign in or create an account with GOV.UK One Login to receive a bearer token"*, and whose `/login/authorize` hands off to `https://oidc.account.gov.uk/authorize`. There is **no open bulk route** — `/files/all-domestic-certificates.zip` 404s on the new host. Fix: none available in code; the data now requires an account credential, which is an **owner action**. Record the site as `CREDENTIAL_BLOCKED` and never as a data absence — the distinction decides whether a downstream sample is refuted or merely deferred. By contrast **OS Open UPRN needs no key** (`https://api.os.uk/downloads/v1/products/OpenUPRN/downloads?area=GB&format=CSV&redirect`), but it carries identity and coordinates only and **never a construction year**. *(docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-22_s3_attribute_source_2026-08-27.md §7)*
- **The Spanish Catastro INSPIRE Buildings WFS answers a bbox question, but only in one exact
  parameter form — and a wrong form fails as an HTTP **200** carrying an OWS `ExceptionReport`,
  never as a transport error.** `https://ovc.catastro.meh.es/INSPIRE/wfsBU.aspx` publishes **five
  stored queries and none of them is by bbox** (`GetBuildingByParcel`, `GetFeatureById`,
  `GetBuildingPartByParcel`, `GetOtherBuildingByParcel`, `GetAllConstructionByParcel`), so a
  `STOREDQUERIE_ID=GetBuildingByBBOX` guess silently falls through to the by-reference query and
  returns `Paremter REFCAT can't be null` (the service's own spelling). The **ad hoc** `GetFeature`
  does work: `TYPENAMES` must be **plural** — `TYPENAME` returns *"At least one of the parameters
  TYPENAMES and RESOURCEID must be present"* — and `BBOX` must carry the CRS URN as a fifth field
  with **lat,lon** axis order: `BBOX=<s>,<w>,<n>,<e>,urn:ogc:def:crs:EPSG::4326`. Measured on
  2026-08-27: **48 consecutive tiles, HTTP 200 throughout, 3,782 features**, under the plain
  non-browser User-Agent `OpenUBEM-D-EU-22-coverage-probe/1.0`, reproduced identically on a second
  run. 🔴 **Do not record this service as unusable** — an earlier note in the `D-EU-22`
  record said the WFS *"cannot answer a coverage question at all"* and attributed an HTTP 400 to the
  User-Agent; that HTTP 400 did **not** reproduce, and the cost of believing it is a 611 MB
  municipality ATOM download for a question 48 tiled requests answer. Two further facts worth
  keeping: `numberOfFloorsAboveGround` on `bu-ext2d:Building` is served as
  `xsi:nil="true" nilReason="other:unpopulated"` — a **declared** non-population, the storey count
  lives on `BuildingPart` — and `www.catastro.minhap.es` no longer connects, the live host being
  `www.catastro.hacienda.gob.es`.
  *(openubem/outputs/eu_evidence/EU-04/D-EU-22/probe_es_catastro_coverage.py; evidence
  `es_catastro_coverage_probe.json`; `debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-22_s3_attribute_source_2026-08-27.md` §7 Finding 3 and §8.2)*
- **The MHCLG EPC endpoint pinned by `D-EU-10` is retired, and its successor is behind an account —
  an open dataset that stopped being openly *fetchable*.** Every path under
  `epc.opendatacommunities.org` now returns **HTTP 301** to
  `get-energy-performance-data.communities.gov.uk`, whose own guidance reads *"You need to sign in or
  create an account with GOV.UK One Login to receive a bearer token"*; both of its access routes
  (`download` and `api`) land on that gate, and there is **no open bulk route**. 🔴 The
  failure mode to recognise: an unauthenticated request returns **HTTP 200 and an HTML sign-in page**,
  so a client that only checks the status code records a success and parses zero rows. OS Open UPRN,
  the other half of the ruled GB pair, **is** open and needs no key
  (`api.os.uk/downloads/v1/products/OpenUPRN/downloads?area=GB&format=CSV`, 618,494,417 bytes, md5
  `2f023512afc378cd7b9351b24ccf1a34`, one 2.27 GB CSV member) — but it carries identity and
  coordinates only and **never a construction year**, so it is the join key and never the answer.
  ⚪ Consequence for any GB coverage claim: **UNMEASURED is not zero.** A credential, not a
  dataset, is what is missing.
  *(openubem/outputs/eu_evidence/EU-04/D-EU-22/probe_gb_it_coverage.py; evidence
  `gb_it_coverage_probe.json`)*
- **A zero join rate is a broken probe until proven otherwise — the ISTAT section key is `NSEZ`, not
  `SEZ2011`.** The 2011 indicator tables carry both: `SEZ2011` is the 12-digit national key
  (`PROCOM` + section) while the Comune's own `sezioni-di-censimento-anno-2011` layer publishes the
  bare section number in a field also called `sez2011`. Keying on the national code joins **0 of 104**
  polygons and looks exactly like "the data does not cover this bbox"; keying on `int(NSEZ)` joins
  **102 of 104**. Fix: the probe now refuses to report a zero join as a finding — it stamps
  `probe_status = BROKEN` and says so — because this arc has twice had to withdraw a conclusion
  frozen on an unexamined zero.
  *(openubem/outputs/eu_evidence/EU-04/D-EU-22/probe_gb_it_coverage.py;
  `outputs/EU02_neighbourhood_selection_2026-08-24/eu02_reproducible_queries.json` `_revision_B_non_osm_sources.IT_istat_sections.join_key`)*

- **`FileNotFoundError` on `.../s3_campaign/ES-MAD-BERRUGUETE/relation/12582232/relation/12582232.idf` the first time a campaign runner met a Spanish building** - OSM stable ids are `way/123` and `relation/456`, and the slash is a **path separator**, so every place a run names a file after `building_id` silently opens a directory level: the run directory, the IDF, each zone name, and each `Schedule:File` gain CSV. France never exposed this because BD TOPO ids (`BATIMENT0000000240879449_part0`) carry no slash, so a runner can pass every French test and still be unable to write its first Spanish IDF. Fix: `scripts/run_eu_s3_campaign.py:run_slug` maps `/` to `_` for **naming only** - the true `building_id` stays in the campaign manifest beside a `run_slug` column, so a run directory can always be traced back to its OSM id. Zone names are renamed with the same slug before IDF assembly, since EnergyPlus object names reach the filesystem through the external-schedule CSV path.
  *(openubem/outputs/eu_evidence/EU-04/s3/s3_campaign_manifest.csv)*

- **`HTTP 404` with a GOV.UK HTML body from every EPC API call to `https://get-energy-performance-data.communities.gov.uk/api/...`, and `HTTP 200` HTML (not JSON) from the retired `https://epc.opendatacommunities.org/api/v1/domestic/search`** — the England/Wales EPC service moved to GOV.UK One Login and the **API host is a different hostname from the website**: the base URL is `https://api.get-energy-performance-data.communities.gov.uk` (note the `api.` prefix) and the paths lost their `v1`: `/api/domestic/search`, `/api/certificate?certificate_number=...`. The old `opendatacommunities` host still answers 200 with a redirect page, so a naive check reads it as alive. Auth is **`Authorization: Bearer <token>`**, not the old HTTP Basic `base64(email:apikey)`; the token is shown on the service's *My account* page. Verified live 2026-08-27: bad postcode → `404 {"data":{"error":"No certificates could be found for that query"}}` (JSON error = token accepted), `E1 6AN` → `200` with 3 rows. **Second trap:** `/api/domestic/search` returns a *summary* record only — `uprn`, `certificateNumber`, address, `registrationDate`, `currentEnergyEfficiencyBand`; there is **no `construction-age-band`, `property-type` or `total-floor-area`** in it, so any age/area coverage question needs a **second call per certificate** to `/api/certificate`. Fix: use the `api.` host, Bearer auth, and budget two calls per building. *(docs/resources/UK/Energy certificate data APIs – GOV.UK.pdf; service technical documentation at `/api-technical-documentation/making-a-request`)*

- **A UPRN-to-footprint spatial join silently loses ~13 % of its pairs (London: 1,059 footprints matched instead of the pinned 1,219; 6,504 pairs instead of 6,838), with no error and no warning** — OS Open UPRN's native `X_COORDINATE`/`Y_COORDINATE` are **OSGB36 / EPSG:27700**, while the EU-02 manifest is EPSG:32630 and pyproj reprojects it to 27700 **without the OSTN15 grid shift**. The two sides then sit 1–2 m apart, which is more than the width of the gap between London terraces, so points fall just outside their own building. Nothing raises: both layers claim CRS 27700. Fix: build the point layer from the file's own WGS84 `LATITUDE`/`LONGITUDE` columns (`Point(lon, lat)`, `crs=4326`, then `.to_crs(27700)`) so both sides travel through the same transformation — `openubem/outputs/eu_evidence/EU-04/D-EU-22/probe_gb_epc_coverage.py` T02 join. Proved by caching the 16,151 candidate points once and running three variants: native E/N → 1059/1193/6504; lat-lon→  27700 → 1219/1231/6838; lat-lon→ 32630 vs manifest native → 1219/1231/6838. General rule: **never mix a dataset's native projected coordinates with a reprojection of another dataset into the same EPSG** — go through lat/lon on both sides. *(docs/docs_ACTIVE/europeanLocations/previous/PLAN_gb-epc-coverage-probe-2026-08-27.md, T02)*

- **A join CSV holds 1,276 distinct `osm_id` values over a 1,242-row manifest, and 47 cells contain a pandas repr block (`way/395533900    36.83
way/395533900    41.02
Name: footprint_area_m2, dtype: float64`) instead of a number** — the writer looped `for idx in buffer_only_idx: row = joined_buffer.loc[idx]`, but the sjoin result carries a **duplicated index** (one point can match several buffered footprints), so `.loc[idx]` returns a **DataFrame**, not a Series, and `row["osm_id"]` writes a whole column's string repr into one cell. A second bug rode along: `index.difference()` compares index labels, not pairs, so valid buffer-only pairs were dropped. Fix: collect `strict_pairs = {(uprn, osm_id)}` while writing the strict rows, then iterate `joined_buffer.iterrows()` and emit a `buffer_1m` row for every pair not already in that set — `.iterrows()` on both loops guarantees every cell is a scalar. Standing rule: **after any `gpd.sjoin`, never index the result with `.loc[label]`**; iterate rows. *(docs/docs_ACTIVE/europeanLocations/previous/PLAN_gb-epc-coverage-probe-2026-08-27.md, T02)*

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
- **`total_eui_kwh_m2` undercounts lighting and equipment for any building with a zone multiplier —
  only 6/48 buildings reconcile end-use sums to total within 2%** — the total sums Interior Lighting and
  Interior Equipment from *per-zone hourly output variables*, which E+ does **not** scale by zone multiplier,
  then divides by a multiplier-aware floor area (`openubem/results/parser.py:431-433`). Heating/cooling/fans/
  pumps/DHW come from the multiplier-correct ABUPS table and match to <0.01%. (OPEN-60)
  Fix: `parse_eio_zone_multipliers()` returns `{ZONE_NAME_UPPER: Zone Multiplier × Zone List
  Multiplier}` from the same `.eio` route `resolve_simulated_floor_area()` already uses (not a second
  reader), and `_compute_eui()` groups each zone variable by `key_value` and scales per zone before
  summing — `openubem/results/parser.py`, 2026-08-21 (T03). Unknown zone → 1.0; empty/absent map
  → bit-identical to the pre-fix path, so no new failure mode. ⚠️ **The 6/48 figure has NOT been
  re-measured after the fix** — that sample's `.sql` files were deleted in the 2026-08-20 W9 prune
  (OPEN-53) and re-measuring needs a re-simulation. Do not quote the fix as verified against n=48.
  *(docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md;
  docs/docs_ACTIVE/openings/extra/FIX_open-60_multiplier-eui.md)*
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
- **`Zone Information` fields parsed from `eplusout.eio` come back shifted by one column (volume reads as ceiling height, etc.)** — the `! <Zone Information>` header line begins with the `!` comment token, so splitting it on `,` yields one more leading element than the data rows that follow. Indexing data rows by `header.index(name)` is then off by one for every field. Fix: strip the leading `! <...>` token from the header before building the index map, and assert on a known-good row (a `_F0_WHOLE` zone whose `Floor Area × Ceiling Height` is recomputable) before reporting any number. Found and fixed mid-task while parsing all 8,160 `.eio` of the adopted run for OPEN-56.
  *(docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-live-items-2026-08-21-night.md T02)*
- **A fleet recomputation reproduces the adopted headline to 0.005 % but never exactly (153.8304 vs 153.8231)** — not a parsing or filter bug, and not rounding: every row-set filter, every precision 0–5 dp, all six archived `evidence/open48_refleet*` run directories, and the provenance path the restatement doc itself cites (`%LOCALAPPDATA%\Temp\ubem_validation\open48_refleet4\`) all return 153.8304 on an identical sorted `osm_id` set. Cause unknown and **not recoverable from what is on disk**. Fix: none — do not "correct" the recomputation to match, and do not restate the adopted figure; quote 153.8231 and cite this entry.
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_t01_headline-reproduction.md)*
- **`_parse_meters_sql` silently zeroed ALL nine HVAC meters, not just the new one, for any `.sql` lacking `TabularDataWithStrings`** (self-inflicted while adding OPEN-61's district-heating read) — the new `_read_abups_district_heating(conn)` call was placed inside the same `try` block *before* the `for name, value_j in rows:` loop that applies the real meter rows; when the ABUPS table didn't exist (every minimal synthetic fixture in `tests/test_parser_hvac_metered.py`, `tests/test_parser_elevators.py`), the `OperationalError` propagated out of the `with` block and was caught by the outer swallow-all `except Exception: pass` before the loop ever ran, so `Cooling:Electricity`, `Elevators:InteriorEquipment:Electricity`, etc. all came back 0.0 instead of their real values. Fix: give the ABUPS read its own inner `try/except`, placed *after* the meter-rows loop, so a failure there defaults only `_DISTRICT_HEATING_KEY` to 0.0 and never touches the other nine (`openubem/results/parser.py`, `_parse_meters_sql`). Caught by three previously-passing tests going red (`test_reads_all_four_meters`, `test_missing_meter_returns_zero`, `test_elevator_meter_read`) on the first full-suite run after the change.
  *(docs/docs_ACTIVE/openings/implemenation/PLAN_open61-dh-remedy-2026-08-22.md T01)*
- **`total_eui_kwh_m2` golden regression tests failed after OPEN-61's district-heating fold** (`test_r1_total_eui`, `test_r2_total_eui`, `test_r6_total_eui`, `tests/test_results_parser.py:279,289,304`) — T01 folded ABUPS "District Heating" `Total End Uses` into `dhw_eui_kwh_m2` unconditionally, on plan F3's finding that 100.00% of district heating is Water Systems — but F3 measured only the OPEN-61 fleet census corpus (8,152 rows, `open61_census_fleet.csv`), not every `.sql` the parser can ever see. The three golden fixtures (`tests/fixtures/golden_sql/r1_single_zone.sql`, `r2_one_zone_per_floor.sql`, `r6_perimeter_core.sql`) are pre-Phase-D artifacts whose ABUPS table routes 100% of the District Heating column to the **Heating** row (148.24 / 709.99 / 1646.86 GJ respectively) and 0.00 to Water Systems — the exact opposite of F3 — consistent with an Ideal-Loads-Air-System heating plant (EnergyPlus tags Ideal Loads heating as DistrictHeating fuel by convention; superseded fleet-wide by Phase-D's metered `Heating:Electricity`/`Heating:NaturalGas` route, per `parser.py`'s own module docstring). T01's fold therefore misattributed 105.05 / 78.89 / 101.66 kWh/m² of real HEATING energy into `dhw_eui_kwh_m2` for these three fixtures, inflating `total_eui_kwh_m2` by the same amount (`heating_eui_kwh_m2` itself was untouched and its own golden tests still passed — only the three `total_eui` assertions failed). **Fix (T01b, director-authored 2026-08-22, F11): `_read_abups_district_heating()` reads `RowName='Water Systems'`, not `'Total End Uses'`** (`openubem/results/parser.py`, `_read_abups_district_heating`) — on all 8,152 fleet census rows the two rows are identical (max diff 0.0, F11), so this changes no fleet number, but on the three golden fixtures (Water Systems = 0.00 GJ) it correctly reads 0.0 instead of the misattributed heating energy. All three golden tests pass again with no fixture or expected-value edit. New guard test added: `tests/test_parser_open61_district_heating.py::TestDistrictHeatingServingSpaceHeatingNotFoldedIn` (uses `r1_single_zone.sql` directly). Tracked as **OPEN-64** (district heating serving a non-DHW end use, general case).
  *(docs/docs_ACTIVE/openings/implemenation/PLAN_open61-dh-remedy-2026-08-22.md T01/T01b, CP-1 STOP + fix 2026-08-22)*

- **`assert False` in `TestEuiGolden::test_r1_total_eui` — `math.isclose(276.9193027210884, 171.873920234131, rel_tol=1e-06)`** (and the identical failures in `test_r2_total_eui`, 265.1497 vs 186.2619, and `test_r6_total_eui`, 262.9418 vs 161.2838), while `test_r1_heating_eui` / `test_r1_cooling_eui` / `test_r1_lighting_eui` on the **same fixture** all pass — the OPEN-61 district-heating fold read the ABUPS `RowName='Total End Uses'` cell instead of `RowName='Water Systems'`, so district heating that serves **space heating** was added into `dhw_eui_kwh_m2` and thence into the total. **Only the total failing while every component passes is the signature of energy being ADDED, not recomputed** — go straight to a newly-summed term, do not re-derive the components. Confirm in one query: `SELECT RowName,Value FROM TabularDataWithStrings WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' AND TableName='End Uses' AND ColumnName='District Heating'` — the golden fixtures return `Heating` 148.24 GJ and `Water Systems` 0.00 GJ, and 148.24 × 277.7778 ÷ 392 m² = 105.0456 kWh/m² matches the observed delta exactly. Fix: `RowName` changed to `'Water Systems'` in `_read_abups_district_heating`, `openubem/results/parser.py` (OPEN-61 T01b). ⚠️ **Root method trap, not just a typo: a quantity measured over the production fleet ("100 % of district heating is Water Systems", 8,152 buildings) was used as a statement about the code. The golden fixtures are the mirror image of the fleet.** The 13 unread ABUPS district-heating rows are tracked as **OPEN-64**. *(docs/docs_ACTIVE/openings/implemenation/PLAN_open61-dh-remedy-2026-08-22.md §5 F11, T01b)*

- **A manifest column named `eui_kwh_m2` that is in fact a heating-only intensity** (`openubem/outputs/eu_evidence/EU-04/s3/s3_campaign_manifest.csv`, promoted under `D-EU-24`) — the numerator is `heating_kwh`, the annual sum of the hourly `Zone Ideal Loads Zone Total Heating Energy` `Output:Variable` extracted at `scripts/run_eu_s2_campaign.py:285`; it carries no lighting, no appliance electricity, no DHW and no cooling, so quoting it as a whole-building EUI is wrong by a large factor **in the direction that looks plausible**. Fix: the promoted artefact is NOT renamed (that would rewrite a promoted file); the basis is carried additively in `openubem/outputs/eu_evidence/EU-04/s3/s3_campaign_manifest_BASIS.md` and MVP §9.7.3, and the pooled 66.86769 kWh/m² may not be printed without the words "heating-only".
  *(docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md §9.7.3, EU-05 entry)*
- **`TabularData` empty in `eplusout.sql` even though `Output:SQLite` was written as `SimpleAndTabular`** — `SimpleAndTabular` says only *where* tabular output goes, never that any was requested. With no `Output:Table:SummaryReports` object EnergyPlus writes no `AnnualBuildingUtilityPerformanceSummary`, so `select count(*) from TabularData` returns 0 and every end-use read against that `.sql` silently finds nothing. Fix: add `Output:Table:SummaryReports,AllSummary;`, checking first for an existing `OutputControl:Table:Style` — a duplicate is a Severe.
  *(docs/docs_ACTIVE/europeanLocations/EXECUTOR_PROMPT_EU-05_meter_sidecar_2026-08-27.md §5 T01)*
- **A distinct-schedule-CSV count read as a dwelling count** — the 374 distinct `Schedule:File` CSVs across the 95 accepted `S3` IDFs are **one per zone**; summing `zone_count` by `layout_mode` gives 26 dwelling zones (in the 12 `DWELLING_LAYOUT_EMITTED` buildings) against 348 one-zone-per-floor massing floors. Any per-dwelling quantity scored over 374, or over the 95 buildings, uses the wrong denominator. Fix: denominators written down in `s3_campaign_manifest_BASIS.md` §2 and MVP §9.7.3 EU-06 — the per-dwelling population is **12 buildings / 26 dwellings**.
  *(docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md §9.7.3, EU-06 entry)*

- **`meters_present 0 of 95` recorded as un-measurable because "emitting meters means re-running the promoted campaign and changing every `idf_sha256`"** — the reason confuses emitting meters *in* the promoted campaign with measuring them at all. Fix: off-path sidecar over copies — verify each promoted IDF's SHA-256, append only `Output:Meter` + `Output:Table:SummaryReports`, run in a separate tree, compare the hourly ideal-loads series row-for-row (`max_abs_diff 0.0`) and recompute all promoted hashes afterwards; `scripts/run_eu_meter_sidecar.py`. All five meters existed on all 95. *(docs/docs_ACTIVE/europeanLocations/EXECUTOR_PROMPT_EU-05_meter_sidecar_2026-08-27.md)*
- **`OtherEquipment` read as "1 W/m²" from its `Power per Zone Floor Area` field** — with `Design Level Calculation Method = Watts/Area` the field is a **multiplier** on the `Schedule:File`, and when the schedule's type limits are `AnyNumber_Wm2` the CSV itself carries the W/m². Fix: read the schedule, not the object — all 381 `S3` gain CSVs are flat at 3.0 W/m² at `f = 0`, so the delivered gain is 3× the field value. *(openubem/outputs/eu_evidence/EU-04/s3/s3_campaign_manifest_BASIS.md)*
- **EnergyPlus writes a trailing space + bare CR on the last CSV header field inconsistently between two runs of the same IDF**, so a raw column-name-set comparison falsely reports `column set mismatch`. Fix: match columns on the **stripped** header name while reading values by the original key; `scripts/run_eu_meter_sidecar.py`. *(same doc, T02)*
- **`TabularDataWithStrings` values read as GJ and multiplied by 277.78** — under `OutputControl:Table:Style ... JtoKWH` the values are **already kWh** and `ColumnName` carries no unit suffix (`District Heating`, not `District Heating [GJ]`). Fix: no conversion; verified against a promoted `heating_kwh`. *(same doc, T01)*

## 9. Validation gates & metric traps

- **CBECS NMBE / CV(RMSE) / KS gates FAIL in every cell and every region under every basis/COP/load-fraction
  combination tested (CV(RMSE) 47–97%, KS_D 0.22–0.55)** — structural to an archetype-deterministic UBEM
  (near-zero within-archetype variance vs CBECS's per-building survey spread) plus regional/composition
  mismatch. A scalar reporting basis only shifts the mean, never the shape. Correctly designated report-only
  (V-R5-5); **never tune to pass**.
  *(docs/docs_DONE/SETUP/phaseC_combinedResim/v19_validation/PLAN_v19_national_cbecs_rescore.md; docs/docs_VALIDATION/step1/overAll/results/MEMO_phaseB_cbecs_diagnosis.md)*
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
  *(docs/docs_VALIDATION/step1/overAll/results/MEMO_phaseB_cbecs_diagnosis.md)*
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
- **Every campaign manifest reads `"energyplus_version": "23.1"` no matter which binary ran** (FINDING 187) —
  the field was a hard-coded literal, never measured, so a 24.2.0 run, a Linux run and a Windows run all
  self-report 23.1 and no version-dependent result can be attributed. Fix: split into
  `energyplus_version_declared` (the guard's 23.1) and `energyplus_version_measured`, parsed from the binary
  actually invoked and set to `"not_run"` in `dry_run`. *(openubem/campaign/eu_cell_runner.py:613-616;
  docs/docs_ACTIVE/europeanLocations/previous/STATE_european_locations_v2.md §3)*
- **A gate requires a manifest field that the manifest writer never emits** — `step8_gates`' `immutable_fields`
  demanded `platform` while `MANIFEST_FIELDS` had no such key, so G8.14's platform arm could never be
  satisfied and the gap read as a scoring result rather than a missing writer. **Check both sides of a
  required-field contract before diagnosing the gate.** Fix: `_platform_record()` writes hostname, os,
  machine, processor, python_version, energyplus_exe and energyplus_sha256, and `platform` was added to
  `MANIFEST_FIELDS`. *(openubem/campaign/eu_cell_runner.py:77-82,123; openubem/validation/step8_gates.py)*

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
- **EU-11 remedy-campaign 3D viewer opens fully blank, zero buildings drawn, no visible error to the user** —
  `scripts/update_eu_outputs_3d.py` emitted the scene-JSON provenance block as `provenance_counts`, but the
  shared viewer bootstrap script reads `D.counts.measured` unguarded near the top of the IIFE
  (`document.getElementById("hm").textContent=D.counts.measured...`); `D.counts` is `undefined`, the
  `TypeError` throws before the building-draw loop ever runs, and canvas stays empty. Confirmed by parsing the
  embedded scene JSON directly — 1,351 valid building records, zero NaN/degenerate geometry — data was fine,
  only the key name was wrong. Fix: rename the emitted key to `"counts"` and add the missing `"data_dir"` key
  (used unguarded for the footer link) to match the JS contract exactly.
  *(scripts/update_eu_outputs_3d.py:238; regenerated `docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_GB-LDN-STDUNSTANS_viewer.html`)*
- **Per-building CSV join against `osm_id` silently returns zero hits for one district only (Bologna),
  others fine** — `pandas.DataFrame.iterrows()` yields each row as a `Series`, which upcasts *all* columns to
  one common dtype; joining an `int64 building_id` column next to a `float64 eui_kwh_m2` column turns every
  id into a float during iteration (`27410` → `27410.0` → `str()` → `"27410.0"`), which then matches no
  `str(row["osm_id"])` key. Only surfaced for Bologna because its `building_id` values are plain numeric
  (Comune di Bologna ids); the other 3 EU districts use OSM-prefixed ids (`way/…`, `relation/…`,
  `BATIMENT…`) that are already `object`/string dtype and don't upcast. Fix: read the id column with
  `pd.read_csv(..., dtype={"building_id": str})` and iterate via `zip(df["col_a"], df["col_b"])`, never
  `iterrows()`, when joining a string id against a numeric sibling column.
  *(scripts/generate_eu_3d_viewers.py:793-808, `_load_eu11_eui`)*

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
- **`sacct --format=JobID,State%20` silently truncates the JobID column on a large still-pending array,
  collapsing e.g. `1305167_[171-293]` into `1305167_[17+` — read as "17 pending" instead of the true 123**
  — the default JobID field width is fixed, and `%20` only widens the State column, not JobID; the `+`
  marks truncation, not a count. Caused a monitoring-loop progress report to overstate completed counts by
  ~40 % across three districts (Lyon 268 reported vs. 162 real, Madrid 916 vs. 192, Bologna 1178 vs. 122) in
  one polling cycle before being caught by eyeballing that the "pending" number hadn't grown despite ~1,700
  new tasks having been queued. Fix: always widen JobID too — `--format=JobID%25,State%20` — so array
  ranges print in full. *(EU-11 Speed campaign monitoring, 2026-09-04)*
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
- **EU-11 S2 campaign: every array task failed instantly with `Schedule:File=... not found`** — the new
  `scripts/cluster/ship_eu11_fleet.sh` staged and tarred only `idfs/`, `weather/`, `fleet.lst`, never the
  local `schedules/` directory, so the remote fleet dir had no schedule CSVs at all (100% failure, Madrid
  961, Lyon 297, London 82). Fix: stage and tar `schedules/` too (`ship_eu11_fleet.sh`); re-shipped and
  resubmitted clean (Madrid job 1293106, Lyon 1293123, London 1293124), spot-checked `task.rc=0` with
  "EnergyPlus Completed Successfully" post-fix.
  *(docs/docs_ACTIVE/europeanLocations/prompts/PROMPT_EU-11_full_district_campaign_speed.md)*
- **`ship_eu11_fleet.sh`'s local staging step raised `FileExistsError: [WinError 183]` on the schedules
  directory** — the staging step created `schedules/` unconditionally with `mkdir()` (no `exist_ok`) on a
  district already staged once, so a re-ship after a `prepare()` regeneration collided with the leftover
  directory from the prior run. Fix: `exist_ok=True` (and clear the stale contents first so old schedule
  CSVs from a superseded regeneration can't leak into a new tar). Hit during `D-EU-35`'s Madrid/Lyon/London
  re-shipping.
  *(scripts/cluster/ship_eu11_fleet.sh; docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-35_geometry_simulation_desync_resimulation_2026-08-28.md)*
- **A `sacct` PENDING bracket's lower bound duplicated an individually-listed task of a different state**
  (`1305186_205 RUNNING` alongside `1305186_[205-1200%8] PENDING` in the same poll) — a snapshot race: the
  task transitioned PENDING→RUNNING while `sacct` was compiling its grouped-range output, so it appears both
  individually (current state) and as the bracket's stale lower edge. Naive `hi-lo+1` expansion overcounts
  pending by exactly 1 (sum came to `total_tasks+1`). Fix: cross-check the arithmetic sum
  (completed+failed+running+expanded-pending) against the job's known `total_tasks`; if over by 1 and an
  individual line duplicates the bracket's lower bound in a different state, subtract 1 from the bracket
  count (Lyon/Madrid the same poll had no such overlap — bracket start was exactly one past the last
  individual line, confirming this is a race artifact, not a general off-by-one in the expansion rule).
  *(EU-11 Speed campaign monitoring, 2026-09-04, poll #5)*
- **`sbatch` submission for `D-EU-35`'s re-shipped fleets failed, script not found** — the remote path was
  guessed as `/speed-scratch/o_iseri/openubem/scripts/submit_fleet_t08.sbatch` (flat under `scripts/`); the
  real path nests it under `scripts/cluster/`:
  `/speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet_t08.sbatch`. Fix: use the `cluster/`-nested
  path in every `sbatch` call.
  *(scripts/cluster/submit_fleet_t08.sbatch)*

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
  Also seen as **`UnicodeEncodeError: 'charmap' codec can't encode character '∩' in position 3:
  character maps to <undefined>`** — an `∩` (set-intersection glyph) in an f-string `print()` inside
  `scripts/analysis/open09_open38_overlap_2026-08-21.py`, run via `.venv/Scripts/python.exe` on the
  default cp1252 console (T10, `PLAN_ten-live-items-2026-08-21.md`). Fix: replaced the glyph with `x`
  in the print string; `PYTHONIOENCODING=utf-8` also unblocks it without an edit if the glyph must stay.
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
- **`ERROR: Could not find input data file: <dir>\<dir>\<name>.idf` from `energyplus.exe`, `returncode=1`,
  no `eplusout.err` written at all** — the runner built its per-building temp directory from a **relative**
  `Path` (`SMOKE_ERR_DIR / f"_tmp_{building_id}"`), then called `subprocess.run([..., "-d", str(tmp_root),
  str(idf_path)], cwd=tmp_root, ...)`; `cwd=` only changes the child process's working directory, it does not
  rebase relative path *arguments*, so `energyplus.exe` resolved the still-relative `idf_path` against the new
  `cwd` a second time, looking for `tmp_root/tmp_root/<name>.idf`. Same root cause as the `run_ep_isolated()`
  entry above (relative path + `cwd=` switch), different, louder symptom because here EnergyPlus itself reports
  the exact missing path instead of silently producing no output. Fix: `.resolve()` the temp directory before
  building the `.idf` path from it (`scripts/run_eu_s1_smoke.py:283`).
  *(scripts/run_eu_s1_smoke.py, EU-04 S1 smoke, D-EU-04-H)*

- **`ModuleNotFoundError: No module named 'cdsapi'` raised at import time by `scripts/acquire_era5_eu_folds.py:27` (`from cdsapi.api import get_url_key_verify`)** — the script was launched with the Windows `py` launcher, which resolves to the system interpreter (`AppData/Local/Programs/Python/Python313/python.exe`), not the project virtualenv. `cdsapi`, `pvlib` and `xarray` are installed only in `.venv` and are still undeclared in `pyproject.toml`, so nothing outside `.venv` can import them. The failure is environment selection, not a missing install. Fix: invoke the acquisition and conversion scripts as `./.venv/Scripts/python.exe scripts/acquire_era5_eu_folds.py ...`; `py -0p` lists the launcher targets and confirms `.venv` is not among them. *(docs/docs_ACTIVE/europeanLocations/previous/PLAN_eu-boundary-closure-2026-08-26.md, T01)*

- **`PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'era5_madrid_2009-06.zip'` inside `ecmwf.datastores.processing.Results.download`** — a manual `--poll` invocation was run in the foreground while the background `--run-sequential` loop for the same fold was also polling; both processes saw the CDS job as `successful` at the same moment and raced to write the same target file, so the loser's `os.remove(target)` inside `download()` hit a file the winner still had open. The file itself downloaded correctly (the winner completed it); only the loser process crashed. Fix: `scripts/acquire_era5_eu_folds.py:poll()` catches `PermissionError` around `result.download(str(dest))`, prints `DOWNLOAD_RACE_SKIPPED`, and continues instead of raising -- the next `--poll` retries naturally since `dest` is absent for the losing process. Operational rule: do not run a manual `--poll` while `--run-sequential` is active for the same fold. *(docs/docs_ACTIVE/europeanLocations/previous/PLAN_eu-boundary-closure-2026-08-26.md, T01)*

- **EnergyPlus aborts with `Could not find weather file` even though the `.epw` exists and its path is correct from the shell** — the gate-6 smoke runner invokes EnergyPlus with `cwd=<temp run dir>` while passing the EPW as a **relative** path, so the child resolves it against the temp directory instead of the repo root and never sees the file. The path is right; the working directory is not. Fix: resolve the weather path to absolute before building the argument list — `Path(epw_path).resolve()` at the top of `evaluate_energyplus_smoke_gate`, `openubem/acquisition/european_weather.py`. Found by running the real control (the pinned France EPW, which the registry already records as `gate_6_energyplus_smoke: PASS`) rather than by unit tests, which used a monkeypatched runner and could not see it. General rule for any `subprocess.run(..., cwd=...)`: every path handed to the child must be absolute, because the child's notion of "here" is not yours. *(docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md §12.12)*

- **A long live-API sweep runs at double its pinned rate limit and burns quota twice over, while every log line looks healthy** — a dispatched subagent had launched its own copy of the sweep and the director later launched another; both were hitting the same host and the same on-disk cache at ~10 req/s against a pinned 5 req/s. Neither process can see the other. `wmic process where "..." get CommandLine` returns nothing on this machine; the working probe is PowerShell `Get-CimInstance Win32_Process | Where-Object CommandLine -match '<script>'`, which showed two independent PID pairs. Fix: `Stop-Process -Id <loser pids> -Force`, then keep exactly one owner of any rate-limited job. Rule: **before launching a long network job, list the processes** — an agent's claim that its job "finished" or "is running" is prose, not evidence. *(docs/docs_ACTIVE/europeanLocations/previous/PLAN_gb-epc-coverage-probe-2026-08-27.md, T03)*

- **A subagent reported `completed`, then woke up again minutes later, deleted a 5,781-file live response cache and restarted a 40-minute sweep from zero** — a finished agent is not inert: it can re-notify and act again, and its startup path included a "clean the cache" step. Cost ≈ 5,800 wasted API calls; **no corruption**, because the cache is keyed per UPRN and the sweep is idempotent (`was_cached` short-circuits both the sleep and the call counter). Fix: `TaskStop` on that task id, and never again dispatch an agent into an arc that owns a long-lived cache. Rules: **make every long job resumable and per-key cached** so a rogue restart costs time and never truth; and **no destructive step in a job's startup path**. *(docs/docs_ACTIVE/europeanLocations/previous/PLAN_gb-epc-coverage-probe-2026-08-27.md, T03)*

- **A 40-minute background job stops dead with a 0-byte log and no error, ~30 minutes after it was launched** — two separate traps compounded. (a) `TaskStop` on an agent **also kills the child processes that agent launched**, so stopping a rogue agent silently killed the sweep it had parented. (b) Python **block-buffers stdout when redirected to a file**, so a 0-byte log on a healthy long job is normal and cannot be used as a liveness signal. Fix: relaunch with `PYTHONUNBUFFERED=1` (progress then appears line-by-line and resume is visible as `api_calls: 0` on already-cached items), and **before `TaskStop`-ing an agent, check whether a job you want to keep is parented to it** — launch long jobs from the director session, never from a subagent. *(docs/docs_ACTIVE/europeanLocations/previous/PLAN_gb-epc-coverage-probe-2026-08-27.md, T03)*

- **Two `scripts/eu21/08_district_viewer.py` runs for the same `--district`/`--tag` are alive at once, both about to write the same `district_plans/<D>_nocore_<tag>.json`** — an executor that cannot see its own earlier background launch relaunched the regeneration 8 minutes later; the script writes the JSON in one unguarded `json.dump` at the end (`scripts/eu21/08_district_viewer.py:887`), so two finishers would have interleaved into a corrupt baseline that every later parity run would then be gated against. Caught before either finished, by `Get-CimInstance Win32_Process | Select ProcessId,ParentProcessId,CreationDate` — the **CreationDate** column is what separates the survivor from the duplicate; the command line alone cannot. Fix: `Stop-Process -Id <later pids> -Force` on the newer launch only, keeping the older (further-along) one, then hand the executor the measured process table instead of letting it re-derive state. Rule: an executor's "still waiting on my background task" is a claim about its own memory, not about the machine — list the processes before believing there is exactly one. *(docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-plan-homogeneity-2026-09-07.md, T03b)*

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
  *(docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md)*
- **The suite baseline is `pytest -q tests/`** — a bare root-level `pytest -q` reports ~36 false failures.
  *(project convention; see MEMORY index)*
- **Benign noise, never a failure: `Windows fatal exception: access violation` / `<cannot get C stack on this
  system>`** — joblib/loky worker-spawn noise under Python 3.14 on Windows, localized around
  `test_step3_orchestrator.py::test_parallel_byte_identity` and `test_sim_integration.py`. The run still
  reports the full pass count. Check the exit status, not the stdout dump. Documented independently in at
  least five arcs.
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-46_path-verification.md; docs/docs_DONE/BUGS/zoningBug/PLAN_zoning-multifloor-fix.md; docs/docs_TODO/layoutgenerator/debugs/PLAN_design_buildout_by_archetype.md:501)*

- **A single test file takes minutes of CPU while the same code runs in milliseconds outside pytest** — the test asserted membership directly against a large serialised string, `assert "\\" not in serialised` and 26 more `assert f"{letter}:" not in serialised`, where `serialised` was a ~340 KB `json.dumps` of the frozen campaign-cell spec. **pytest's assertion rewriter carries both operands of every rewritten comparison through its explanation machinery**, so 28 membership tests against a 340 KB operand cost minutes; the same 28 checks in a plain `python -c` finish in under a millisecond (measured: `build 0.09 s, dumps 0.00 s, membership 0.0000 s`). Fix: evaluate the membership tests in ordinary code and assert once on the small result — `offenders = [t for t in tokens if t in serialised]` then `assert offenders == []` — which also gives a better failure message, since it names the offending token instead of dumping the string. `tests/test_eu_campaign_cell_spec_freeze.py` went from **over 5 minutes to 1.02 s** for 9 tests. **Diagnostic trap this hid:** the first attributed cause was a `git status` subprocess in the code under test; measuring it directly gave 0.085 s and cleared it, and a `--durations` run with `-x` looked fast only because it stopped before reaching the slow test. Always get `--durations` over the FULL file before attributing a cause. *(docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md §12.12)*

- **`AssertionError: assert ['\\'] == []` from `test_serialised_spec_carries_no_absolute_or_windows_path`, with no path anywhere in the diff** — the guard forbids **any** backslash in `json.dumps(spec, ensure_ascii=True)` because that is how a Windows path would leak in, but a backslash also appears whenever a JSON string contains a newline (`\n`) or a non-ASCII character (`\uXXXX`). The offender was **prose**: two caveat amendments in `openubem/data/campaign/eu_boundary_caveats_v1.0.json` were written with embedded blank lines. The guard was right and the data was wrong. Fix: whitespace-normalise every caveat string (`" ".join(v.split())`) and re-run the freeze. **Diagnostic trap:** walking the parsed spec for a literal backslash finds nothing — the escape is created *by serialisation*, so search the `json.dumps(...)` output, not the object. *(docs/docs_ACTIVE/europeanLocations/DONE/CLOSURE_eu_boundary_contract_v1.0.md §12)*

- **`test_allow_unpinned_writes_draft_with_510_cells` fails with `assert draft_path.is_file()` → False, and the captured stdout reads `status=FROZEN_PINNED` instead of DRAFT** — FINDING EU-S2-09, fourth recurrence: the test calls `main(["--allow-unpinned"])`, which reads the **live** `weather_registry.json`, and silently assumed at least one fold was still `RULED_NOT_PINNED`. Once the last fold was promoted the run legitimately produced a pinned spec at the non-DRAFT path. Fix: inject a synthetic registry rather than soften the assertion — `_synthetic_registry_with_statuses(tmp_path, {..., "it": "RULED_NOT_PINNED"})` plus `monkeypatch.setattr(freeze_mod, "build_spec", lambda **kw: real_build_spec(weather_registry_path=..., **kw))`, because `build_spec`'s default argument is bound at definition time and monkeypatching `DEFAULT_WEATHER_REGISTRY_PATH` therefore does nothing. In the same pass `tests/test_eu_weather_registry.py` stopped pinning the literal top-level `status` and now asserts the **invariant** that the label agrees with the per-fold statuses — stricter than the literal, since it also fails on a stale label. **Rule: never assert a literal value of a mutable ruled data file.** *(docs/docs_ACTIVE/europeanLocations/DONE/CLOSURE_eu_boundary_contract_v1.0.md §12)*

- **A repo-path guard fails on legitimate prose containing `<letter>:`** — a test forbidding Windows absolute paths matched a bare `f"{letter}:"` and fired on `EPSG:32631` inside the caveat register's own text. A drive letter only denotes an absolute path when a separator follows it. Fix: match `f"{letter}:/"` and `f"{letter}:\\"` instead of the bare colon form, in `tests/test_eu_campaign_cell_spec_freeze.py`. *(same source)*

- **`AssertionError` comparing an emitted path to `tmp_path.as_posix()` after a writer was changed to emit repo-relative paths** — `test_caveats_register_happy_path_embeds_every_entry_and_its_source` asserted `spec["caveats_source"]["path"] == good_registry.as_posix()` (absolute) while the freezer's `_repo_relative_posix` returns `.pytest_tmp/pytest-of-.../eu_boundary_caveats_synthetic.json`, because pytest's basetemp sits **inside** the repository and therefore relativises. The assertion is latent: it passes on any machine or run where `Path.resolve()` leaves the temp path outside the repo root. Fix: assert against the writer's own rule, `freeze_mod._repo_relative_posix(good_registry)`, in `tests/test_eu_campaign_cell_spec_freeze.py:172`. **General form: when production code gains a path-normalising helper, every test that hard-codes the un-normalised form must be re-pointed at the helper, not at a literal.** *(docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md §12.12c)*

- **`FileNotFoundError: ...debugs/docs/DONE-docs/tabula_102_extra_columns_2026-08-23.csv` in `test_extracted_numeric_columns_match_102_row_reference`** — 23 files were moved from `docs/docs_ACTIVE/europeanLocations/debugs/docs/` into a new `DONE/` subfolder by another session, **without the citation sweep the project's archiving rule requires**. A test held the pre-move path as a hard-coded literal, so a documentation archive turned the suite red. Fix: re-point `REFERENCE_CSV` at `.../debugs/docs/DONE/...` in `tests/test_eu_construction_sets.py:19-27`. **General form: an archive is not finished when the files land — roughly twenty other documents in the same arc still cite the pre-move paths.** Resolve by filename, never by rewriting the path prefix. *(docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/CLOSURE_QUESTIONS_european_locations_2026-08-26.md §5)*

- **`** Warning ** Indicated Zone Volume <= 0.0 for Zone=...` / `The calculated Zone Volume was=-49.03` / `The simulation will continue with the Zone Volume set to 10.0 m3.`** — geomeppy's by_storey/WHOLE extrusion path uses the raw, unoriented footprint coordinates, so floor normals point the wrong way (`** Warning ** GetVertices: Floor is upside down! Tilt angle=[0.0], should be near 180`), the divergence-theorem volume integrates negative and EnergyPlus substitutes a **fixed 10.0 m³**. The core/perim path escapes it because `Polygon2D.buffer()` calls shapely's `orient()` unconditionally. **Not cosmetic when ventilation or infiltration uses `AirChanges/Hour`**: EnergyPlus derives the flow as ACH × zone volume ⁄ 3600, so the air flow and its heat loss scale with the substituted volume. Measured in the EU S2 campaign: 103/103 zones in 31/31 buildings, **1 030.0 m³ of air simulated against a true 59 470.92 m³ — a 57.74× understatement** (8.23×–122.52× per zone). Fix: call `write_zone_volumes(idf, zones)` after `extrude_geometry(...)`, which writes `Zone.Volume = floor area × storey height` — the OPEN-56 remedy already present at `openubem/idf/builder.py:217` and called by `BuildingIDF` at `builder.py:660`; the EU runners `scripts/run_eu_s2_campaign.py:215` and `scripts/run_eu_s1_smoke.py:291` never called it. **Trap when sizing the error: do NOT take |calculated volume| as the true volume.** Under a flipped floor normal the sum returns −(floor area × 1 m) regardless of storey height, which reads as "1 m-tall zones" and understates the error threefold; read `Ceiling Height` and `Floor Area` from `eplusout.eio` instead. **Diagnostic rule this teaches: read what a warning says, do not count warning kinds** — a triage gate that only counts is satisfied by six kinds of which two invalidate the result. *(docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_EU-17_zone_volume_10m3_2026-08-26.md)*
- **`KeyError: 'es'` in `tests/test_eu_fold_epw_conversion.py` / `assert 'RULED_PINNED' != 'RULED_PINNED'` / `test_refuses_when_a_fold_is_not_pinned` fails after an owner ruling** — eight tests asserted on the CURRENT contents of the live, mutable `openubem/data/weather/weather_registry.json`. `load_fold_targets` (`scripts/convert_era5_eu_folds_to_epw.py:61-67`) returns only folds whose `status == "RULED_NOT_PINNED"`, so promoting a fold correctly removes it from the target set and every test keyed on that fold raises `KeyError`. **Nothing regressed — the ruling was the point.** Fix: behaviour tests build a synthetic registry in `tmp_path` and pass it via the function's own `registry_path` parameter; only genuine shipped-file invariants read the live file, and they iterate over whatever folds are present instead of naming one. **Rule this teaches: a data file whose purpose is to change when an owner rules something must never be the fixture a unit test asserts against** — otherwise the pressure at the moment of a ruling is to revert the ruling to make the suite green. **RECURRED 2026-08-26 on the `uk` promotion, in the same file, as `KeyError: 'uk'` plus a second shape: `assert not any(module.OUTPUT_ROOT.rglob("uk_*.epw"))` failed because a correctly-promoted London EPW now sits in the real `openubem/data/weather/`. The `es` repair had converted eight tests in one file and missed two in `tests/test_eu_fold_epw_conversion.py`. Fix: the first now builds a synthetic registry via `_write_registry`/`_synthetic_entry` like its neighbours; the second `monkeypatch.setattr(module, "OUTPUT_ROOT", tmp_path / "out")` (`tests/test_eu_fold_epw_conversion.py:95,116`). **Second rule: an output DIRECTORY the pipeline legitimately writes into is the same trap as a mutable data file — assert against a `tmp_path` root, never the shipped one.** Expect a third recurrence at the `it` promotion. *(docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md §12.21, FINDING EU-S2-09)*
- **`FileNotFoundError: ...\debugs\docs\DONE\tabula_102_extra_columns_2026-08-23.csv`** — an archive sweep renamed the containing folder without the citation sweep the project's archiving rule requires. It happened **twice on 2026-08-26** to the same file (`docs/` -> `DONE/` -> `DONE-docs/`), breaking `tests/test_eu_construction_sets.py` each time although the CSV itself never changed. Fix: stop hard-coding the prefix — resolve the reference **by filename**, `sorted(search_root.rglob(NAME))`, which is the repository's own 2026-08-09 archiving rule (*resolve by filename, not by rewriting the path prefix*) applied to a test constant. Any test that pins a path into a docs archive folder will break on the next sweep; resolve by name instead. *(docs/PROJECT_CHECKLIST.md head section, OPEN-33)*

- **`ValueError: could not convert string 'HH_es_00035_Presence' to float64 at row 0, column 1.`** raised from `numpy.loadtxt` inside `read_presence_csv` — the GSSCanada 4J presence bundles ship each series as a **one-column CSV with a header line naming its household**, while `openubem.semantic.european_schedules.read_presence_csv` documents and enforces a **headerless** contract. Neither side is wrong; the two contracts simply differ, and the emitter's own contract must not be widened, because a headerless reader that silently skips a first line would also swallow a truncated first hour. Fix: the consumer reads the shipped format instead — `_read_presence_series` in `openubem/campaign/eu_cell_runner.py` strips one leading non-numeric line, returns it, and the caller **verifies it equals `HH_<fold>_<hid>_Presence`**, turning the header into a second independent confirmation of the household beside the SHA-256. *(docs/docs_ACTIVE/europeanLocations/implementation/previous/PLAN_run-campaign-cell-2026-08-27.md)*

- **A hand-written convex-polygon intersection returns `0.0` for every pair, including polygons that visibly overlap — and every test that used it still passed** — the Sutherland-Hodgman clip built its half-plane as `a = y0 - y1, b = x1 - x0`, which is the **inward** normal negated, so `a*x + b*y <= c` kept the outside of each edge and the successive clip emptied the ring on the first edge. Nothing raised: an intersection routine that always answers zero satisfies every "these must not overlap" assertion. Fix: `a = y1 - y0, b = x0 - x1` in `tests/reference/geo08_reference_partitioner.py`, plus a test that asserts a **known non-zero** overlap (two unit squares offset by half their side → 25.0), so the routine can never again be vacuous while green. *(MVP_european_locations.md §9.7.3, EU-04 GEO-08 addendum)*

- **A `GEO-*` gate goes green while silently omitting one of the quantities its own specification requires** — the first `GEO-08` F4 pass compared zone count, dwelling areas, exterior facade contact and adjacency, but **not circulation area**, which MVP §4.8 lists alongside them. No test could detect the omission: every assertion written passed, and a missing assertion has no failure mode. It was caught only by a reader comparing the gate to its specification. Fix: circulation core area, shared boundary, overlap and core-share were added to `tests/test_eu_geo08_independent_parity.py`. **Standing lesson: build a gate from its specification's own list of quantities, never from the quantities already in hand — the suite cannot see an absence.** *(MVP_european_locations.md §4.8; docs_ACTIVE/europeanLocations/prompts/DIRECTOR_PROMPT_european_locations.md)*

- **`ModuleNotFoundError: No module named 'pvlib'` collecting `tests/test_eu_fold_epw_conversion.py` and `tests/test_eu_t06_weather_promotion.py`** — not a missing dependency: `pvlib >= 0.11` is declared at `pyproject.toml:32` and installed in the project venv. The interpreter running pytest was not `.venv/Scripts/python.exe`. The same mistake cascades — `xarray`, `h5netcdf`, `cdsapi` and `ecmwf-datastores-client` all follow. Fix: run the suite through the project venv. ⚪ Scope note worth keeping: those two modules cover the ERA5→EPW **conversion**, not the run-time weather guarantee — `D-S10-7` is enforced at run time by the frozen `weather_sha256` check and the bundle-year vs EPW-year agreement, both asserted in `tests/test_eu_cell_runner.py`, so a scored campaign run needs neither module. *(docs_ACTIVE/europeanLocations/messages_GSSCanada/)*


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
- **Comune di Bologna ODS CTC GeoJSON field aliases** — live exports observed on 2026-08-24 abbreviate
  `altezza_gronda`, `quota_gronda`, and `quota_piede` to `altezza_gr`, `quota_gron`, and `quota_pied`.
  `bologna_fetcher.py` accepts both explicit spellings; do not infer height from another field or derive
  storeys when neither eaves-height spelling is present.

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
  Don't assume a dispatched agent resumes itself after a long wait. **Recurred on a second, different
  agent (`a7b81c96b8dae26e1`, EU-14B T05) despite the pattern already being pre-embedded in its dispatch
  prompt** — the agent submitted its own `sbatch --array` job then ended its turn claiming it would "poll
  in the background and resume automatically," producing a `status: completed` notification with zero real
  progress (no harvest, no report). Pre-emptive prompt text alone did not prevent it. Fix (confirmed working
  both times): `SendMessage` the still-alive agent — never spawn a duplicate — instructing it to resume in
  the same turn with **one foreground blocking `Bash` call** (never `run_in_background`, never `Monitor`):
  `until ! _ssh "squeue -u \$USER -j <jobid> -h" | grep -q .; do sleep 60; done`, porting the `_ssh()` tcsh
  wrapper from `scripts/cluster/t08_harvest_results.py:104`; if the call's own timeout fires before the
  queue clears, call it again rather than ending the turn. `[OPEN]` — root cause (why the agent believes
  it has background-polling capability for a job it spawned itself) unaddressed; only the symptom has a
  confirmed per-instance fix.
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

- **A pre-registered control answered with a different denominator than the one it was registered
  with, returning the opposite verdict** — OPEN-61's C6 asked for the ratio `dh / dhw_eui`; the
  executor computed `dh / total_site_energy` and reported the 60-building pilot as "NOT
  REPRESENTATIVE, ~50x off", asserting its denominator matched the pilot's construction. It did not.
  On the registered ratio the fleet median is 0.6503 (IQR 0.3117-0.8642) against the pilot's 0.714
  (0.362-0.840) — **representative**. Fix: re-derive the headline and every pre-registered control
  from the artifact yourself before it enters the register; one `csv.DictReader` loop did it here.
  Detection rule: a verdict that reverses a prior result by an order of magnitude is a denominator
  bug until proven otherwise. *(scripts/analysis/open61_fleet_dh_number_2026-08-20.py; corrected in
  docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_fleet-dh-number.md §C6)*

- **A per-building MEDIAN ratio applied to a fleet-POOLED quantity, silently biasing the estimate
  low** — OPEN-61's pre-census estimate scaled a 60-building median `dh/dhw` of 0.714 onto the fleet.
  Measured, the fleet's median ratio is 0.6503 but its **pooled** ratio is **0.9382, 44 % higher**,
  because large buildings carry far more district heating per unit of DHW. The method therefore
  topped out at 17.43 kWh/m² where the truth is 19.47 — it could not have reached the answer at any
  point in its own IQR, while still appearing to "land inside the band". Fix: when the target is a
  pooled statistic, scale by the **pooled** ratio, never the median of per-building ratios; the two
  differ by exactly the size-correlation the pooling exists to capture.
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_fleet-dh-number.md §C6)*

- **A pooled fleet figure read as a per-building offset** — 19.47 kWh/m² of unreported district
  heating is a *fleet* quantity, not a property of a typical building. 116 buildings (1.4 % of 8,144)
  carry 70.5 % of it; every office, retail and shop archetype sits at 1.3-2.7 kWh/m². Applying the
  pooled figure as a uniform correction would move energy onto ~5,000 buildings that do not have it.
  Fix: before proposing any remedy from a pooled number, print the per-archetype concentration; if the
  top decile carries most of the mass, no flat offset is admissible.
  *(docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-61_fleet-dh-number.md §C6b)*

- **A citation sweep after an archive reports "0 broken" and a `.json` provenance field still points at the pre-archive path** — the sweep was scoped to `--include=*.md`, so every non-Markdown citation was invisible to both the repair and the verification that followed it. Moving `DECISION_REQUEST_EU-19_it_gate5_october_2026-08-27.md` into `debugs/docs/DONE-docs/` left `openubem/data/weather/weather_registry.json:217` (`decision_record`) unresolvable — inside the provenance block that justifies the fold's gate-5 exception, which is the one place the link matters. Fix: re-run the resolver over `--include=*.json --include=*.csv --include=*.py --include=*.txt` as well and repair, `openubem/data/weather/weather_registry.json:217`. **Rule: a citation sweep scoped to one file extension is not a citation sweep.** Corollary found in the same pass: two **frozen** artefacts (`eu_campaign_cell_spec_v1.0.json`, `eu_boundary_caveats_v1.0.json`) cite an already-archived path and **cannot be repaired** — a frozen file records the citation as it stood at the freeze, so archive before you freeze, never after. *(docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv, 2026-08-27T17:20Z)*

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

Authoritative list: `docs/docs_ACTIVE/openings/DONE/INVESTIGATION_open-items-register.md` (20 tracked, next free
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

- **EU parent-table reconciliation rejected six valid GB rows as non-existing variants** — X-01 copied rows such as `GB.ENG.AB.02-03.ApartmentBuildings.SyAv.002.001` failed a local `.endswith(".001.001")` assertion, although the parent generator's actual retention predicate is `code.endswith('.001')` (`C:\Users\o_iseri\Desktop\GSSCanada\GSSCanada-main\4J_docs_occ\tools\4thJ_step8_tabula.py:315`) and the final `.001` is the existing-state component. Fix: validate the final `.001` suffix plus `Number_BuildingVariant == 1` in `openubem/data/construction/tabula_reconcile.py`; the X-01 decision record preserves the authority resolution. *(docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISIONS_X-01_variant-suffix-2026-08-23.md)*

*Maintenance: when a debug/measurement doc lands, add its distinct, reusable failure modes here in the same
`**Symptom** — cause -> fix. *(path)*` form. Keep `[OPEN]` markers current against the register.*
# X-02 ventilation coefficient mismatch (2026-08-23): the planned `V_C / A_C_Ref` identity did not reproduce the pinned TABULA `h_Ventilation` values. The direct `Calc.Set.Building` relation is `0.34 * (n_air_use + n_air_infiltration) * h_room`; ruling and source example are in `docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISIONS_X-02_ventilation-coefficient-2026-08-23.md`.

## European locations X-04

- **DR11 R5 returns 19.993496 W, not the literal 20.000 W ± 0.001 W** — the local EnergyPlus
  23.1 fixture confirms its 0.5/0.5 other-side temperature is exactly 10.000 C, but retains an
  effective inside-film resistance even after a very large inside convection coefficient is
  requested. This stays a strict `xfail`; see
  `docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISIONS_X-04_R5-engine-film-2026-08-23.md`.

- **X-04 resolution and R3 follow-up (2026-08-23)** — the evaluator accepted the documented
  engine-aware R5 tolerance, so R5 now passes; R7 also passes. The executable R3 fixture
  preconditions to 20 C and applies a 0 C boundary but returns 19.998714 C at 14.0625 h rather
  than 7.357589 C. It is retained as a strict expected failure pending reconciliation; see
  `openubem/outputs/eu_evidence/X-04/targeted_pytest_r3_fixture.log`.

- **T07 disposition (2026-08-26), outcome (b) — fixture inputs were wrong, not the implementation.**
  Root cause of the 19.998714 C stagnation: `_r3_idf()` in `tests/test_eu_physics_energyplus.py`
  formerly set an artificial inside convection coefficient `h_in = 1e7 W/(m2 K)`, which locked
  EnergyPlus's partitioned zone heat-balance solver (decay clamped to ~1e-7 fraction per timestep,
  i.e. ~2e-6 K per minute) — a numerical artifact, not real physics. Re-derivation confirms the
  analytical target is reproducible exactly from the pinned functions:
  `r3_time_constant_hours(1.62e7, 320.0)` = 14.0625 h and
  `r3_free_float_temperature_celsius(20.0, 0.0, 14.0625, 1.62e7, 320.0)` = 7.357588823 C
  (`openubem/idf/european_physics.py:145-154`), matching DR11 §4's 7.357589 C to six decimals — so
  DR11's target is not in question. The fix (already present in the current fixture: no
  `SurfaceProperty:ConvectionCoefficients` override, natural convection relies on TARP) makes the
  free-float trajectory physically continuous — measured `T(14.04h) = 3.6036 C`,
  `T(24h) = 1.5914 C` for the 100 m2 InternalMass case — and the test asserts these as physical
  decay bounds (`2.0 <= t_14 <= 5.0`, `0.5 <= t_24 <= 3.0`), not the single-node analytic value,
  because the full CTF/TARP dynamic model is a distributed system and is not expected to reduce to
  the lumped one-node exponential exactly. No `xfail` remains in `tests/test_eu_physics_energyplus.py`
  or `tests/test_eu_physics_primitives.py`; both files are green (11 passed). Fix:
  `tests/test_eu_physics_energyplus.py::_r3_idf` (override removed),
  `tests/test_eu_physics_energyplus.py::test_r3_free_float_energyplus_fixture` (assertions un-xfailed).
  *(docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/ANALYSIS_REQUEST_X-04-R3_X-07-CDS_2026-08-23.md,
  PLAN_eu-boundary-closure-2026-08-26.md T07)*

## European locations EU-10

- **`Schedule:File=..., File Name: "C:\\Users\\...\\*_gain.csv" not found` on Speed EU-11 tasks** — the accepted S2 builder emits an absolute Windows schedule path, valid locally but unavailable on Linux after the IDF alone was staged. Fix: `scripts/run_eu_s2_district_campaign.py:prepare` stages the byte-identical gain CSVs under `schedules/<stem>/` and retargets only each `Schedule:File` path to `../../schedules/<stem>/...`, relative to the array task output directory; failed arrays were cancelled before resubmission. *(EU-11 Speed submission, 2026-08-28)*

- **`cp: cannot stat '.../idfs/<stem>'$'\r''.idf': No such file or directory` on Speed EU-11 tasks** — the Windows-prepared `fleet.lst` used CRLF, and `sed` passed the trailing carriage return into the IDF filename. Fix: `scripts/cluster/submit_fleet_t08.sbatch` strips `\r` from the selected fleet stem before forming paths; the failed arrays were cancelled and will be resubmitted with the corrected batch script. *(EU-11 Speed submission, 2026-08-28)*

- **`bash: -c: line 0: unexpected EOF while looking for matching '"'` while tracking EU-11 Speed arrays** — a PowerShell-interpolated loop placed nested quotes around the remote `bash -lc` payload, truncating the command before it reached Speed. Fix: issue a single-quoted remote payload per read-only tracking command; the job submission and fleet contents are untouched. *(EU-11 Speed monitoring, 2026-08-28)*

- **`ValueError: ARCHETYPE_AMBIGUOUS: GB/AB/GB.06` while preparing EU-11** — the initial band-period selector incorrectly required a generated TABULA row even when the accepted registry supplies one unambiguous composite row (`GB.ENG.AB.04-08.ApartmentBuildings.SyAv.005.001`) for that period. Fix: `scripts/run_eu_s2_district_campaign.py:_record_for_period` now mirrors `select_tabula_archetype`: prefer one generated row when present, otherwise accept exactly one remaining candidate; a genuine multi-candidate result still fails closed. *(EU-11 fleet preparation, 2026-08-28)*

- **A retained EnergyPlus J-to-kWh series can sum to 8759.999999999998 rather than a literal 8760.0** — IEEE-754 accumulation of hourly converted values is expected, not an energy-accounting discrepancy. Fix: retain the strict closure tolerance in `openubem/results/european_campaign.py` and use approximate comparisons in `tests/test_eu_results_accounting.py`; do not round retained values before validation.

## European locations X-05

- **EU-02 live Bologna `ValueError: Unlisted Bologna rifter typologia values`** — the live cadastral export used official spellings `Cabina ENEL`, `Mura storiche`, and `Stazione di rifornimento`, while the initial fail-closed rule carried their shorter aliases only. Fix: retain both explicit spellings as non-residential in `classify_bologna_rifter`, with a regression fixture; never default an unseen typology. **EU-02 GeoPackage readback:** Fiona places `geometry` first and represents nullable `Int64` fields as ordinary numeric columns. Validate the emitted `01_buildings_clean.schema.json` metadata on readback rather than treating that driver representation as an in-memory schema failure.

- **The EU-02 Lyon selection record’s BD TOPO class counts do not add up** — it states 891 total, 23 annexes, then 544 residential + 278 unknown + 52 non-residential; those categories sum to 897 (or 874 after annex removal). The retained raw WFS query and pinned boundary reproduce 891 / 23 / 544 / 278 / **46** when `usage_1 OR usage_2 = Résidentiel` is applied as specified. Fix: preserve the measured 46 in `openubem/outputs/eu_evidence/X-10/fr_live_reconciliation.json`; do not alter the selected site or silently force the count to 52.

- **A positional `Sizing:Zone` fixture was rejected before sizing began** — the original test fixture placed `No` and `NeutralSupplyAir` in fields whose EnergyPlus 23.1 schema expects numeric cooling-flow data and a heating-flow method, respectively. Fix: `tests/test_eu_hvac_sizing.py` constructs `Sizing:Zone` through named IDD fields, then requires a successful zone-sizing record and nonzero heating load. *(MVP §9.7 EU-05 acceptance evidence)*

- **A weighted U-value cannot reconstruct TABULA's `h_Transmission` target** — component-specific boundary factors are embedded in the calculator's eleven `H_Transmission_*` terms. Preserve and sum those cached terms, divided by `A_C_Ref`, for the exact source readback; do not substitute a weighted-U approximation. *(docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISIONS_X-05_s0-box-plan-2026-08-23.md)*

- **`** Severe ** Duplicate name found for object of type "Schedule:Constant" named "EU_AlwaysOn_ES.ME.SFH.04.Gen.ReEx.001.001". Overwriting existing object.` (10 severes, fatal before simulation)** — `add_european_heating_controls` named every emitted object after the archetype alone, so a multi-dwelling building, whose dwellings share one archetype by construction, wrote one schedule/ventilation/gains/thermostat set per zone under the same names. Single-zone fixtures never exposed it. Fix: `openubem/idf/european_controls.py` names the per-zone objects after `zone_name`, emits the two archetype-independent constant availability schedules once per IDF, and raises `ValueError` when controls are requested twice for the same zone; `tests/test_eu_reciprocal_surface_audit.py` runs a three-dwelling generated layout through a real EnergyPlus design-day sizing run. *(MVP §9.7 EU-04/EU-05 acceptance evidence)*

- **`** Severe ** Duplicate name found for object of type "ScheduleTypeLimits" named "EU_Step8_AnyNumber_Wm2". Overwriting existing object.` (one duplicate per extra dwelling zone, fatal before simulation)** — `emit_step8_gain_schedule` always (re-)creates a fixed-name `SCHEDULETYPELIMITS` object (`EU_Step8_AnyNumber_Wm2`); calling it once per dwelling zone of a multi-dwelling building therefore writes one duplicate per zone beyond the first, unlike `add_european_heating_controls` which already names its own objects after `zone_name`. Fix: `scripts/run_eu_s2_campaign.py:build_idf_for_building` removes any existing `EU_Step8_AnyNumber_Wm2` object immediately before each per-zone call to `emit_step8_gain_schedule`, so exactly one survives; verified on `BATIMENT0000000240879449_part0` (5-dwelling `DWELLING_LAYOUT_EMITTED` case) with a real EnergyPlus 23.1 run. *(docs/docs_ACTIVE/europeanLocations/previous/PLAN_eu-boundary-closure-2026-08-26.md T02)*

- **S0 windows made EnergyPlus abort with "Other side coefficients are not allowed with windows"** — the first equivalent-envelope emitter placed windows in wall hosts using `OtherSideCoefficients`; EnergyPlus permits fenestration only on an exterior/interzone parent. Fix: `openubem/idf/european_box.py` emits the S0's required `b=1` window/door hosts as `Outdoors` walls and preserves the same `U*A` loss; `tests/test_eu_box_generator.py` runs the SFH heating-only engine smoke test. *(docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISIONS_X-05_s0-box-plan-2026-08-23.md)*

- **S0 north/west windows failed the outward-normal check** — subsurface vertex order did not match its cardinal parent-wall winding. Fix: `openubem/idf/european_box.py` uses orientation-specific fenestration vertex sequences, validated by the EnergyPlus smoke run. *(docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISIONS_X-05_s0-box-plan-2026-08-23.md)*

- **The AB floor's displayed TABULA b did not reproduce cached H** — `b_Transmission_Floor_1 = 1` but its cached `H_Transmission_Floor_1` is not `U*A`. Fix: `openubem/idf/european_box.py:_component_values` derives the admissible effective b from the authoritative H component for saved-IDF realization while retaining the original display b in the registry. *(docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISIONS_X-05_s0-box-plan-2026-08-23.md)*

- **Every BD TOPO building is stamped `provenance_year_built = IGN_BDTOPO_MISSING` / `data_quality_flag = 'no_year'` although the source carries the year** — `openubem/acquisition/bdtopo_fetcher.py:94` parsed `date_d_apparition` with `pd.to_datetime(..., format="mixed", errors="coerce")`. Under pandas 3.0.3 that returned `NaT` for **every** BD TOPO value, because the source formats the field as a date with a bare zone suffix and no time part (`'1998-01-01Z'`, `'1820-01-01Z'`), and because pre-1677 values such as `'1580-01-01Z'` fall outside `datetime64[ns]`. `errors="coerce"` then discarded the failure silently. Measured on the live Lyon WFS query (bbox `45.774784, 45.768891, 4.837450, 4.823612`): **1,115 of 1,663** raw features carry a non-null `date_d_apparition`, yet the retained manifest `openubem/outputs/eu02/FR-LYO-HAUTCOEURPENTES/02_residential_manifest.gpkg` held **0 of 530** observed years. This was the live blocker on EU-04 `GEO-10`/S1–S3, and it was a parse defect, not a missing source. Fix: `openubem/acquisition/bdtopo_fetcher.py:82-93` extracts the leading 4-digit calendar year via `_parse_bdtopo_year` with 1000..current_year bounds without datetime round-tripping; regression-tested by `test_bdtopo_year_parse_recovers_real_date_shapes_and_pre_1677_years` and `test_bdtopo_retains_all_years_when_source_dates_present` in `tests/test_eu02_fetchers.py`. *(docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_EU-04_GEO-08_GEO-10_2026-08-25.md)*


- **G8.13 (Schedule:File `Interpolate to Timestep = No`) failed 0/103 against real S2 dwelling/zone gain schedules, although every emitted `Schedule:File` literally reads `No,  !- Interpolate to Timestep`** — `evaluate_saved_idf_schedule_gates` (`openubem/validation/step8_gates.py:497`) read `matching_schedule[6]` for the interpolation flag. That index was correct only for the narrower 7-field `Schedule:File` fixture in `tests/test_eu_step8_saved_idf_gates.py` (Name, TypeLimits, File, ColNum, RowsSkip, NumHours, Interpolate). The real object `emit_step8_gain_schedule` (`openubem/semantic/european_schedules.py:88`) writes also carries `Column_Separator`, `Minutes_per_Item`, and `Adjust_Schedule_for_Daylight_Savings`, which shifts `Interpolate_to_Timestep` to index 7; index 6 read `Column_Separator` (`"Comma"`) instead, so the gate always failed on real 10-field objects while its own unit test — using the shorter fixture — stayed green. Fix: `openubem/validation/step8_gates.py:482,497` updates the guard to `len(fields) >= 8` and checks `matching_schedule[7].casefold() == "no"`; `tests/test_eu_step8_saved_idf_gates.py` widens fixture to full 10-field `Schedule:File` with `Column_Separator = Comma`. *(docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_EU-13_G8.13_scorer_index_2026-08-26.md, docs/docs_ACTIVE/europeanLocations/previous/PLAN_eu-boundary-closure-2026-08-26.md §9 FINDING EU-S2-02)*


- **`** Warning ** This building has no thermal mass which can cause an unstable solution.`, followed by `** Fatal ** Program halted because of convergence error in SolveForWindowTemperatures` on a *non-reproducible* subset of cells** — the same IDF and EPW run three times by hand gave three different `eplusout.csv` digests, and over three 510-cell campaign runs 130 cells changed status while 132 of the 264 always-completing cells returned a different heating value (worst case 27.1 %). Cause: `openubem/campaign/eu_cell_runner.py::_build_idf` emitted the S0 equivalent envelope — which is `Material:NoMass` throughout, so it has **literally zero heat capacity** — without ever adding the `InternalMass` object that carries the campaign's declared capacity, although `scripts/run_eu_s2_campaign.py:244` had always added it. A zero-capacity zone has no single answer, so the window-temperature fatals were a symptom, not the disease. Note it is a **Warning**, not a Severe, and the `dry_run` path never reaches EnergyPlus, so neither suite could have caught it. Fix: `openubem/campaign/eu_cell_runner.py` now calls `add_european_internal_mass(idf, zone_name, a_c_ref_m2, c_m_wh_m2k=record["c_m_wh_m2k"])` right after the envelope; verified by running `uk__GB.ENG.MFH.02.Gen.ReEx.001.001__f050` three times — **76524.889 kWh three times, 0 severe, 0 fatal**, against 74253.89 / 54094.73 / fatal before. Regression: `test_the_cell_idf_carries_its_declared_thermal_capacity` in `tests/test_eu_cell_runner.py`. ⚪ The three remaining geometry warnings (`Floor is upside down`, `zone is not fully enclosed`, `Entered Zone Floor Area(s) differ more than 5%`) are **inherent to the equivalent-envelope method** documented at `openubem/idf/european_box.py:48-58` and no longer produce non-determinism. *(docs/docs_ACTIVE/europeanLocations/implementation/previous/PLAN_run-campaign-cell-2026-08-27.md)*

- **`PermissionError: [WinError 5] Access is denied` on every EnergyPlus launch from the campaign entry point** — `openubem.config.ENERGYPLUS_PATH` is the **installation directory** (`config.py:16` appends `Energy+.idd` to it, and `simulation/runner.py:18`, `run_eu_s1_smoke.py:259`, `run_eu_s2_campaign.py:304` and four test modules all append the executable name), but `eu_cell_runner._run_energyplus` executed `str(ENERGYPLUS_PATH)` **directly as the binary** — it was trying to execute a folder. One value cannot satisfy both readings, and no `dry_run` test reaches the launch. Fix: `_energyplus_exe()` in `openubem/campaign/eu_cell_runner.py` appends `energyplus.exe`/`energyplus` when the value is a directory and passes it through when it is already the binary, so a caller that worked around this by pointing the variable at the exe is not broken by the repair; covered by `test_energyplus_path_may_be_the_install_directory` and `test_energyplus_path_may_also_be_the_binary_itself`. *(cross-session report from GSSCanada 4J, 2026-08-28)*

- **[OPEN] A campaign cell finishes with `return_code = 0` and no Severe, yet its heating figure is meaningless — `** Warning ** Temperature out of range [-100. to 200.] (PsyPsatFnTemp)`, `Inside surface heat balance did not converge with Max Temp Difference [C] =10.088`, and in the by-hand cases that do die, `CalcHeatBalanceInsideSurf: The temperature of -76844.75 C`** — measured by GSSCanada 4J across three full 510-cell runs *after* the `InternalMass` repair: **333 / 346 / 348 completed, of which 97 / 102 / 94 carry one of those markers**; 185 cells are clean in all three runs but **49 of those still return a different heating value (max 45.5 %)**, leaving **136 of 510 clean and bit-reproducible**, and only **5 archetypes with all five `f` levels reproducible** — which is the number that matters, because the sensitivity design compares `f` levels *within* an archetype. 🔴 **The whole `es` fold is affected: every completed `es` cell in every run carries an out-of-range temperature warning.** Cause is not yet ruled. It is **not** the missing `InternalMass` (that is fixed and verified) and **not** the floor orientation: flipping the S0 floor normals to the correct downward tilt was tried, cleared `GetVertices: Floor is upside down!`, and **made the cell worse** — `es__ES.ME.AB.01.Gen.ReEx.001.001__f000` went from three identical runs to 1 fatal in 3 (`Convergence error in SolveForWindowTemperatures`), so the change was reverted. What is measured is that the same cell also raises `FixViewFactors: View factors not complete` — i.e. the interior radiant exchange of the S0 equivalent envelope is ill-posed because the zone is deliberately unenclosed (`openubem/idf/european_box.py:48-58`), and the windows sit in hosts whose outside boundary is `OtherSideCoefficients`. 🔴 **Measured 2026-08-28: the effect the campaign exists to detect is two orders of magnitude below this noise floor.** On the five archetypes whose whole `f` sweep is clean and bit-reproducible in all three runs, the full `f000`→`f100` sweep moves heating by **0.11–0.39 %** (`IT.MidClim.AB.03` 0.2170, `IT.MidClim.MFH.01` 0.3865, `IT.MidClim.SFH.08` 0.2638, `GB.ENG.AB.04` 0.1226, `GB.ENG.MFH.02` 0.1103), and it is not even monotone — two of the five turn back up at `f100`. Against a **45.5 %** run-to-run spread on cells that were clean three times and still moved, **no ruling that merely recovers refused cells can make `EU-09` scoreable while this is open.** Completeness histogram over the 42 archetypes with any reproducible cell: 5 have all five `f` levels, **16 have four**, 7 three, 12 two, 2 one. **Standing rule until this is ruled: `completed: true` is necessary and NOT sufficient — screen `eplusout.err` for those three strings, and require completeness per archetype across all five `f` levels, never a raw cell count.**  🔴 **Resolution 2026-08-28 (`D-EU-27` then `D-EU-28`, both ruled Option B): closed by construction, never by cure, and only for `uk` and `it`.** `Timestep 12` plus three replicates per cell made the run reproducible, giving **191 of 510 CERTIFIED** (3 bitwise-identical `heating_kwh` AND `severe_count = 0` AND `fatal_count = 0` AND all three `completed`) — but certification screens the two counters and **not the `eplusout.err` marker columns the evidence CSV already carries** (`FINDING 182`). **42 of those 191 carry `marker_psy` in all three replicates and all 42 are `es`** (all-three-or-none; `marker_inside_hb` and `marker_calchb` are 0 on every certified cell), because EnergyPlus reports the diverging inside-surface heat balance as a **Warning**, which raises neither counter. The `es` fold did not become sound — the same ill-posed solution merely became **repeatable**. `D-EU-28` therefore restricts the quotable perimeter to the **149 marker-free certified cells (`uk` 75, `it` 74, `es` 0)**, five-`f` sweep set **15 pairs** (`uk` 8, `it` 7). **This entry stays `[OPEN]` because the ill-posedness itself is unfixed for `es`; what changed is that no quoted figure touches it.** Screening rule unchanged and now mandatory: `completed: true` and `clean: true` are each necessary and NOT sufficient — filter on the marker columns too. *(docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md §9.7.3; outputs/deu27_rerun_cells.csv)* *(docs/docs_ACTIVE/europeanLocations/implementation/previous/PLAN_run-campaign-cell-2026-08-27.md T08)*

- **saved IDF Zone fields do not encode an integral storey count** — `read_saved_idf_geometry` derived `storeys_exact = V/(A*h)` from `Zone.Ceiling_Height`, which the IDF writer serializes to 7 significant figures, so a true height of 11 was written `10.999998` and the recovered storey count missed the integer by ~1e-7, far outside `math.isclose(..., rel_tol=0.0, abs_tol=1e-9)`; two of 39 European perimeter archetypes raised instead of being read (`GB.ENG.AB.03.Gen.ReEx.001.001`, `IT.MidClim.AB.05.Gen.ReEx.001.001`). Fix: `openubem/validation/step8_gates.py:401` (and the same serialized-vs-recomputed comparisons at `:443-444` and `:670`) now use `rel_tol=1e-6`; regression `tests/test_eu_box_generator.py::test_v8d_read_saved_idf_geometry_tolerates_7sf_ceiling_height_truncation`. *(docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md §9.7.3)*

- **EU-13's `geometry_outcome` disagrees with the `heating_kwh`/`floor_area_m2`/`eui_kwh_m2` already harvested for the same building — e.g. `relation/12582232` (Madrid) is labelled `DWELLING_LAYOUT_EMITTED` with `floor_area_m2 = 1089.2873` (exactly `272.32 m² x 4` storeys, the massing-box total, not the dwelling-partitioned one)** — `scripts/emit_eu11_layout_sidecars.py` (EU-13) recomputes `geometry_outcome` and the pop-up's dwelling zones from the footprint alone via a fresh `generate_european_dwelling_layout` call, entirely independent of `scripts/run_eu_s2_district_campaign.py:_geometry`, the separate function that actually built the zones submitted to Speed for EU-11's harvest. That function's dwelling-layout branch called `european_layout_to_zone_specs(...)` without `n_storey=n_storey` (same defect as `FINDING EU-12-01`, but here baked into the real submitted IDF, not just a side-car) and its `else` branch had no dwelling-count imputation at all, so most of EU-13's newly-labelled buildings were actually simulated under the older, simpler massing-box or storey-0-only zoning — the pop-up now shows geometry that was never run. Fix: `scripts/run_eu_s2_district_campaign.py:_geometry` now takes `records` and mirrors the side-car emitter exactly — same `n_storey` stacking, same four-tier imputation cascade for missing observed counts, same outcome-string branching (`DWELLING_LAYOUT_EMITTED[_IMPUTED_COUNT]` / `FALLBACK_PENDING_LAYOUT[_MISSING_DWELLING_COUNT]`); verified directly (no new Speed run) on `relation/12582232`: now produces 20 zones (4 storeys x 5 dwellings), matching the side-car. `[OPEN]` a real re-simulation is still required to make the harvested numbers match — tracked in `DECISION_REQUEST_D-EU-35_geometry_simulation_desync_resimulation_2026-08-28.md`, ruling pending. *(caught while answering the owner's question on Speed re-simulation timing, 2026-08-28)*

- **EU-13 3D viewer pop-up shows `Unconditioned core: Yes` for every dwelling-layout-emitted real-footprint building although zero core zone exists anywhere in its `floors[].zones`** — `scripts/emit_eu11_layout_sidecars.py:183` wrote `allocation.has_unconditioned_core`, a density-threshold flag (`dwellings/storeys >= 2`) computed by the synthetic-TABULA-plate helper `allocate_european_dwellings` (only called here to get `units_per_floor`), into the side-car metadata as if it described the real-footprint geometry emitted by `generate_european_dwelling_layout` — which, by the latter's own docstring (`openubem/geometry/european_residential.py:139-141`), never carves a core out of an observed shell, since doing so would fail the `audit_european_floor_partition` area-conservation check (GEO-01) against the real footprint. Verified on `way/51781396` (London, 17 storeys): 5 dwelling strips tile 100 % of every floor, no core polygon anywhere, yet the sidecar and pop-up both claimed a core. Fix: `scripts/emit_eu11_layout_sidecars.py:183` now writes `layout.unconditioned_core_emitted` (the `EuropeanGeneratedFloorLayout` field, always `False` on this path since no call site sets it `True`), honestly reflecting that the full plate is dwelling area with no core; re-ran `scripts/emit_eu11_layout_sidecars.py` and `scripts/generate_eu_3d_viewers.py` across all 4 districts (1,340 side-cars, 1,078 emitted), confirmed `grep -c '"has_unconditioned_core": true'` returns 0 across the corpus, viewers regenerated and re-mirrored byte-identically. *(caught by user inspection of `eu_GB-LDN-STDUNSTANS_viewer.html`, 2026-08-28; `openubem/outputs/eu_evidence/EU-13/RESULTS_EU-13.md`)*

## European locations EU-13B

- **`ValueError: requested_dwelling_count must be positive` inside `generate_european_building_dwelling_layout` for real Lyon SFH/TH buildings** — `allocate_european_dwellings`'s `q/(q+1)` floor stratification legitimately allocates `0` dwellings to some storeys when the declared total is below the storey count (a single dwelling spanning multiple floors, e.g. 1 dwelling over 2-4 storeys — common for terraced houses), and the T01 per-storey partitioner called the ruled-grid generator with that `0` directly. Fix: `openubem/geometry/european_residential.py` (`generate_european_building_dwelling_layout`) now groups consecutive storeys into `EuropeanStoreyGroup(start_storey_index, storey_span, layout)`, absorbing a `0`-count storey's height into the previous non-zero storey's zone (one zone extruded across the whole group's height) instead of partitioning it separately; `european_building_layout_to_zone_specs` extrudes one zone per group across `storey_span * height_m`. Verified: a 1-dwelling, 2-storey Lyon building's side-car now shows one zone (`storey_span=2`) instead of crashing or double-counting. *(EU-13B T01, 2026-08-30)*

- **`classify_building_morphology` routed a plain axis-aligned rectangle to `l_shape_decomposition` / `i_shape_linear_gallery` instead of `point_block_grid`** — the reflex-vertex interior-angle formula used `atan2(cross(a-b, c-b), dot(a-b, c-b))` (vectors from the vertex back to its two neighbours), which is the wrong sign convention for a CCW-oriented ring and reports every convex 90° corner as a 270° reflex angle. Fix: `_reflex_vertex_count` now computes the standard turn-angle formula (`dir_in = b-a`, `dir_out = c-b`, `interior = 180 - atan2(cross(dir_in,dir_out), dot(dir_in,dir_out))`), which correctly reports 90° for every corner of `box(0,0,60,10)`. Regression: `tests/geometry/test_eu13b_dwelling_conservation.py::test_t05_point_block_route_for_compact_convex_plate`. *(EU-13B T05, 2026-08-30)*

- **`AttributeError: 'NoneType' object has no attribute 'intersection'` inside `_facade_contact_lengths` when the I-shape linear-gallery route processed a real Madrid building (`way/380242656`)** — a full-width 1.80 m corridor spine disconnects the remaining plate into two separate polygon lobes (a `MultiPolygon`), and re-clipping that `MultiPolygon` with axis-aligned boxes at the corridor's own boundary produced a mixed-type `GeometryCollection` (Polygon + degenerate LineString slivers) for the "north"/"south" band; `_equal_area_axis_cuts`'s `MultiPolygon`-only handling let a non-Polygon slip through as a "dwelling" polygon, and that object later returned `None` from a boundary-adjacent property. Fix: `generate_european_linear_gallery_layout` now selects north/south lobes directly from `remainder`'s own connected components by comparing each component's centroid to the spine's midline (no re-clipping through the spine boundary), and `_equal_area_axis_cuts` now explicitly extracts the largest `Polygon` from any `GeometryCollection` result (or raises `ValueError`, caught by the caller's fallback) instead of passing a non-Polygon through silently. *(EU-13B T05, 2026-08-30)*

- **30 of 297 Lyon buildings failed with `NARROW_FOOTPRINT_LT_8M` via the secondary route even though the ruled grid never itself checks plate width** — `dwelling_count == 1` (and, less severely, `== 2`) storeys were still being routed through `classify_building_morphology`'s I-shape/L-shape dispatch, which has no reason to run for a trivial whole-plate or half-plate split; when that dispatch failed for a small/irregular footprint, the fallback to the legacy `generate_european_dwelling_layout` re-triggered its own independent `< 8 m` minimum-rotated-rectangle width gate, rejecting buildings the ruled route itself never needed to reject. Fix: `generate_european_ruled_storey_layout` now short-circuits `dwelling_count == 1` (return the whole footprint as one dwelling, no morphology, no regularization) and `dwelling_count == 2` (regularize then call the point-block grid directly, bypassing morphology) before any routing decision. Measured effect on Lyon: narrow-footprint fallbacks dropped from 30 to 2 buildings; Madrid dropped from 32 to 4. *(EU-13B T04/T05, 2026-08-30)*

- **Real GIS footprints with sub-metre digitization jaggies (a single vertex offset by a few centimetres) were routed to `l_shape_decomposition` on an otherwise rectangular plate, inflating secondary-route fallback** — `_reflex_vertex_count` was called on the raw, undenoised footprint, so cadastral/OSM digitization noise below the T03 colinear-vertex tolerance (0.15 m) registered as a "real" reflex corner. Fix: `classify_building_morphology` and `_split_at_reflex_vertex` both denoise with `footprint.simplify(0.5, preserve_topology=True)` before reflex detection, and additionally require the denoised footprint's convex-hull area deficit to exceed 3 % before treating any detected reflex vertex as real (a genuine L/U/cross shape always clears this; noise never does). Measured effect on Lyon: `equal_strip_multi_angle_sweep`-scheme storeys dropped from 903 to 578 out of ~1,340 total. Regression: `tests/geometry/test_eu13b_dwelling_conservation.py::test_t05_gis_digitization_noise_does_not_falsely_trigger_l_shape`. *(EU-13B T05, 2026-08-30)*

- **`[OPEN, out of EU-13B scope]` `tests/test_eu_real_footprint_feasibility.py::test_real_layout_generator_fails_closed_for_unsupported_topology` fails on `COURTYARD_TOPOLOGY_UNSUPPORTED` and `NON_CONVEX_TOPOLOGY_UNSUPPORTED`** — confirmed present exactly as found at the start of this EU-13B session, before any EU-13B edit touched `generate_european_dwelling_layout`. The function's body already implemented the multi-angle-sweep/radial-sector partitioner (which *does* support non-convex and courtyard footprints) as an uncommitted change from a prior, undocumented session; this test still asserts the older, stricter single-strip contract (`git diff` against the committed `HEAD` shows the multi-angle-sweep rewrite as the difference — i.e. it predates EU-13B and was never reconciled with this test). Not fixed here: out of the EU-13B task list, and fixing it would mean deciding whether the test or the implementation is the ruled contract, which is not an EU-13B call. *(found while running the regression suite for EU-13B T08, 2026-08-30)*

- **`ZeroDivisionError` inside geomeppy's `intersect_match` (`Vector3D.normalize` → `set_length`, a degenerate zero-length normal on a live T04 ruled-grid footprint) crashed the whole district's IDF regeneration instead of being caught** — `openubem/idf/surfaces.py`'s existing `intersect_match` exception wrapper only recognised two reroute-to-`one_zone_per_floor` safety nets: coreperim zones (`_is_coreperim_zone`) and `mode == "room_layout"` zones (LayoutGenerator's own). EU-13B's T04 ruled-grid/T05 morphology zones carry `mode == "european_dwelling_layout"` and matched neither, so the bare `raise` at the bottom of the handler re-raised the original `ZeroDivisionError` uncaught, aborting `scripts/run_eu_s2_district_campaign.py`'s `prepare()` loop entirely on the first affected building. Fix: `_force_reroute_room_layout_to_one_zone_per_floor` (`openubem/idf/surfaces.py:664`) now also matches `mode == "european_dwelling_layout"` — the same "union the floor-0 sub-zones back into one footprint" reconstruction applies to both, since both emit many per-storey sub-zones with no coreperim naming; its `total_height` is now derived from `max(z_ceiling) - min(z_floor)` across the matched zones rather than `n_floors * one_group's_height_m`, since a `european_dwelling_layout` storey group can span more than one physical floor (T02 floor absorption) unlike `room_layout`'s always-one-floor-per-group assumption. Even after this fix a residual cannot always be rerouted (the reconstructed union is a real courtyard, or collapses to a degenerate/multipart shape) — `scripts/run_eu_s2_district_campaign.py`'s `prepare()` now also catches `(RuntimeError, ZeroDivisionError, IndexError)` around `build_idf_for_building` and excludes that one building as `IDF_ASSEMBLY_FAILED_<ExceptionType>` instead of aborting the district. Measured residual after the fix, T09 resimulation IDF regeneration: Madrid 9/961 (0.94%), Lyon 14/297 (4.7%), London 2/82 (2.4%) buildings excluded this way. *(EU-13B T09, 2026-08-30; openubem/idf/surfaces.py:640-736; scripts/run_eu_s2_district_campaign.py:377-384)*

- **`FileExistsError: [WinError 183]` on `schedules/<stem>/` inside `scripts/run_eu_s2_district_campaign.py`'s own `prepare()`, re-running it in place for a T09 regeneration** — same root cause as the `ship_eu11_fleet.sh` occurrence already logged above (a re-run of a preparer that unconditionally `mkdir()`s into a directory tree left over from the previous preparation, no `exist_ok`, no cleanup first), but at a different call site: `prepare()` itself, not the shipping script. Fix applied at the call site rather than the function: T09 clears `idfs/`, `weather/`, `schedules/`, `fleet.lst` under `openubem/outputs/eu_evidence/EU-11/<district>/` before every `prepare()` re-run. *(EU-13B T09, 2026-08-30; scripts/run_eu_s2_district_campaign.py:347)*

## European locations EU-14B

- **`TypeError: boolean value of NA is ambiguous` inside `scripts/cluster/harvest_eu11_district.py::parse_task`, crashing the whole district harvest on the first array task with no `task.rc`** — `completed = row["eplus_return_code"] == 0 and "Completed Successfully" in err_text` compares a `pd.NA` (when `task.rc` never got written, e.g. a task that crashed before `RC=$?; echo $RC > task.rc` ran) against `0`, which returns `pd.NA` itself, and Python's `and` then tries to coerce that to a bool. Silently masked in every prior EU-11/EU-13B harvest because the local extraction cache directory (`%TEMP%/ubem_eu11_harvest/<district>/`) is never cleared between harvest runs (`fetch_district_out`'s `sim_out.mkdir(parents=True, exist_ok=True)` extracts on top of whatever is already there): a stale `task.rc` left over from an earlier harvest of the same district silently stood in for a task that genuinely produced none this run, so the code path that divides by `pd.NA` was never exercised until Bologna's T05 resimulation hit it with a clean cache. Fix: `scripts/cluster/harvest_eu11_district.py:186` now guards with `pd.notna(row["eplus_return_code"])` before comparing. Measured on Bologna job `1298672`: 15 of 1,201 tasks had `eplusout.eio`/`.err`/`.sql` (EnergyPlus ran and wrote partial output) but no `task.rc` — consistent with EnergyPlus returning non-zero and the remote-deployed `submit_fleet_t08.sbatch` (see next entry) lacking the `set +e`/`set -e` guard around the EnergyPlus invocation that the local repo copy has, so the script's top-level `set -e` aborts before `RC=$?` runs. All 15 already carried genuine fatal errors in `eplusout.err` and were correctly excluded from `population_success` in both the stale-masked and the fixed run — no contamination of the reported pooled EUI, confirmed by re-running the harvest against a freshly cleared local cache and getting an identical `pooled_eui_kwh_m2` both times. *(EU-14B T05, 2026-08-30; scripts/cluster/harvest_eu11_district.py:186)*

- **`[OPEN, cosmetic, non-blocking]` Bologna's T05 harvest (`summary.json`) shows `platform_observed: []` and `energyplus_version_observed: []`** — the remote-deployed `/speed-scratch/o_iseri/openubem/scripts/cluster/submit_fleet_t08.sbatch` on Speed is an older revision than the local repo copy: it never writes `platform.txt`/`energyplus_version.txt` into each task's `OUTDIR` at all (confirmed absent on every sampled `out/<stem>/` directory on the cluster for job `1298672`), and also lacks the `tr -d '\r'` fleet-list stripping and the `set +e`/`set -e` guard the local copy has. Every prior harvest silently carried this same gap forward as **stale, previous-run metadata** rather than an honest empty value, because of the same never-cleared local extraction cache described in the entry above — for Bologna specifically this meant 1,201/1,201 manifest rows showed a `platform`/`energyplus_version` value dated 2026-08-28 (the D-EU-35 run) even though this row's `heating_kwh` came from the fresh 2026-08-30 job. Not fixed here: fixing it means re-syncing the updated sbatch script to Speed and does not change any scientific figure (`heating_kwh`/`floor_area_m2`/`eui_kwh_m2` all come from `eplusout.sql`, confirmed genuinely fresh by direct remote file-timestamp inspection), so it is out of `EU-14B`'s scope; disclosed rather than silently left showing wrong dates. Harvested Bologna's `summary.json`/manifest now correctly show empty/`NA` for these two columns instead of misleadingly stale ones. *(found during EU-14B T05, 2026-08-30)*

- **`scripts/emit_eu11_layout_sidecars.py` wiped `geometry_outcome` to blank/NaN across the entire Bologna (`IT-BOL-GALVANI2`) manifest** — the emitter's district dispatch (`scripts/emit_eu11_layout_sidecars.py:74-77`, pre-fix) special-cased only `GB-LDN-STDUNSTANS` and routed every other district, Bologna included, through the generic observed-attribute mapper `_mapped_rows` → `map_observed_building_to_tabula` (`openubem/semantic/european_archetype_mapping.py:204`), which requires an observed `year_built`/`building_tag` that Bologna's OSM extract never carries — Bologna's rows are produced only by the ISTAT 2011 census-section cascade `_it_rows` (`scripts/run_eu_s2_district_campaign.py:188`), which the real preparer `prepare()` already dispatches to correctly at `scripts/run_eu_s2_district_campaign.py:345`. Confirmed by direct call: `_mapped_rows("IT-BOL-GALVANI2", ...)` returns 0 mapped rows out of 1,220, all excluded `MISSING_OBSERVED_YEAR_BUILT;UNMAPPABLE_RESIDENTIAL_TYPE`. With `row_map` empty, the old write `manifest_df["geometry_outcome"] = [updated_outcomes.get(str(b), "") for b in manifest_df["building_id"]]` (previously at `scripts/emit_eu11_layout_sidecars.py:292`) defaulted every row to `""`, which pandas reads back as `NaN` on the next load — corrupting the only local record of the Speed harvest. Fix: (1) `emit_eu11_layout_sidecars.py` now dispatches `IT-BOL-GALVANI2` to `_it_rows`, mirroring `prepare()`; (2) the manifest write goes through a new `safe_update_manifest_columns()` (`scripts/emit_eu11_layout_sidecars.py`) that touches only the columns and building_ids it was actually given data for, never creates a column with zero updates, and asserts — before writing anything — that row count, the building_id set, and every previously non-blank cell anywhere in the manifest are unchanged; any violation raises `ManifestSafetyError` and leaves the file untouched. Regression: `tests/geometry/test_eu14b_sidecar_manifest_safety.py`. *(EU-14B T01, 2026-08-30)*

- **`FINDING 206`: clicking a `DWELLING_LAYOUT_EMITTED` building in any EU 3D viewer pop-up shows colored dwelling slices with no corridor spine or stair core drawn anywhere, indistinguishable from the pre-`EU-13B` layout** — the ruled partitioner genuinely computes a real circulation shape (`openubem/geometry/european_residential.py:261`, `circulation_polygon: BaseGeometry | None`, non-null for every non-refused, non-`l_shape_decomposition`-combined building), but `scripts/emit_eu11_layout_sidecars.py` only ever serialized zones named `..._dwelling_N` into the sidecar and carried the circulation polygon's *area* (`circulation_area_m2`) forward, never the shape itself; `scripts/generate_eu_3d_viewers.py`'s `drawFloorPlan` in turn only ever iterated `floorData.zones`, so it had no path to draw a circulation shape even if supplied one. Fix: `emit_eu11_layout_sidecars.py` (per-`group` loop, ~line 293-308) now orients `storey_layout.circulation_polygon` the same way as a zone (`orient(poly, sign=ZONE_WINDING_SIGN)` + `list(poly.exterior.coords)[:-1]`) and stores it as a new `"circulation"` key on each floor dict, `None` when there is none; `generate_eu_3d_viewers.py`'s floor-remap loop carries it into the scene JSON as `floorData.circulation.r` (same offset/round as zone rings), and `drawFloorPlan` now draws that ring in a separate step (grey fill, dashed white stroke, "C" label) before the dwelling-zone loop, with its own `zonesTable` row, so the existing `z+1` dwelling numbering is untouched. `l_shape_decomposition`'s combined layout still serializes `circulation: None` by design (both wings had a corridor but the combiner deliberately drops the combined shape) — confirmed unchanged on `way/420409335` post-fix. Regenerated and mirrored all four districts; zone counts/areas on the investigation's 5-building cross-check are byte-for-byte unchanged, and all four `eu_*_viewer.html` files are `sha256`-identical to their `docs/docs_ACTIVE/europeanLocations/outputs_3D/` mirrors. Regression: `tests/geometry/test_eu13b_circulation_sidecar.py`. *(source: `docs/docs_ACTIVE/europeanLocations/debugs/docs/INVESTIGATION_viewer-circulation-not-drawn_2026-08-30.md` §1; fix: `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-circulation-viewer-2026-08-30.md` T01-T04, 2026-08-30)*

## European locations EU-15

- **Routing multi-reflex-vertex footprints straight to the new `courtyard_secondary` handler regressed previously-successful `l_shape_decomposition` buildings into the strip cutter (net strip-cutter count went UP, not down)** — the first T02 implementation attempt widened `classify_building_morphology`'s courtyard branch from `has_courtyard` (a literal `Polygon.interiors` hole) to also fire on `reflex_count >= 2`, on the theory that an open U/C-shape (no hole, two reflex vertices) is architecturally a courtyard too. Measured effect on the real EU-11 fleet: Madrid's strip-cutter count rose 284→302 and its `l_shape_decomposition` success count collapsed 23→3, because many real footprints the old single-split `l_shape_decomposition` route already served successfully (ignoring the second, minor reflex vertex) got diverted into the new courtyard box-tiling unfolder, which failed audit/facade-contact far more often for those shapes than the old naive split ever did. Fix: reverted `classify_building_morphology` to route on `has_courtyard` (interior ring) only; `reflex_count > 0` (any count) still routes to `l_shape_decomposition`, and multi-reflex real footprints are instead served by the new recursive `_l_shape_wings`/`_split_at_reflex_vertex(..., tolerance_m=...)` escalation inside that route (T03). Net effect after the fix, replaying the same 843-building strip-cutter population: 843 → 767 (74 recovered via T03's hardened L-shape route, 2 via T02's courtyard unfolding), with only 2 buildings regressing to the secondary route (both from a residual tolerance-order effect below) and zero dwelling-count changes anywhere. *(EU-15 T02, 2026-08-30; `openubem/geometry/european_residential.py::classify_building_morphology`)*

- **Changing `_split_at_reflex_vertex`'s pre-simplify tolerance from the historical `0.5` m to the pipeline's `regularization_tolerance_m` (`0.15` m, as T03 specifies) shifted the split line enough to regress a handful of previously-successful `l_shape_decomposition` buildings even with the recursion above disabled** — a finer denoise can retain a real-but-marginal second vertex near the cut that the coarser 0.5 m denoise used to smooth away, changing which polygon ends up hosting which dwelling count in a recursive wing partition, and occasionally dropping one dwelling's facade contact below the 2.50 m gate where the old, coarser split did not. Fix: `generate_european_ruled_storey_layout`'s `l_shape_decomposition` branch now tries wing candidates in order — the exact legacy `tolerance_m=0.5` two-wing split first, then the `regularization_tolerance_m` (0.15 m) two-wing split, then the recursive `_l_shape_wings` escalation — accepting the first candidate whose combined audit and facade-contact checks pass, so anything the legacy algorithm already solved is reproduced bit-for-bit before any new candidate is tried. Residual after this ordering fix: 2 of 843 buildings (`way/310771805` Madrid, `32293` Bologna) still regress from a ruled scheme to the secondary route on one specific per-storey dwelling count each, because the regression happens inside a *nested* wing's own recursive partition (a facade-contact margin of ~2.10 m vs the 2.50 m gate) rather than at the top-level split; not chased further, since dwelling count is conserved and the secondary route is the sanctioned disclosed fallback for exactly this case. *(EU-15 T03, 2026-08-30; `openubem/geometry/european_residential.py:925` `l_shape_decomposition` branch)*

- **Retiring the strip cutter as a success path (T04) turned a previously-"passing" T03 unit test red: `test_t03_l_shape_survives_a_second_near_threshold_reflex_vertex` asserted `dwelling_layout_emitted` on a synthetic L-shape whose `l_shape_decomposition` wing combine was already failing (`L_SHAPE_DECOMPOSITION_FAILED`) before T04, both with and without T05's circulation carve** — confirmed by temporarily disabling circulation (`CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION` set arbitrarily high) and re-running: the combine still failed identically, so this was never a T05 regression. The test only ever "passed" because the pre-T04 `_secondary()` relabelled the legacy equal-strip sweep's clean 0.00%-area-error success as `dwelling_layout_emitted=True` under the retired `equal_strip_multi_angle_sweep` scheme — precisely `FINDING 207`'s masking, reproduced at unit-test scale. Fix: none needed in the partitioner; the test's assertion was stale. Updated to assert the true, honest outcome — `dwelling_layout_emitted=False`, `scheme=="equal_strip_multi_angle_sweep"`, `fallback_reason=="L_SHAPE_DECOMPOSITION_FAILED"` — a correct disclosed refusal, not a bug. *(EU-15 T04, 2026-08-30; `tests/geometry/test_eu15_ruled_coverage.py`)*

- **Lowering `CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION` from 3 to 2 (T05, extending the carved core to `ruled_grid_2x1`) makes `european_building_layout_to_zone_specs` return one additional zone dict (the carved circulation zone, `conditioned=False`) per storey group that now carries a core — any caller counting `len(zones)` as "dwelling count" (rather than filtering to `conditioned is not False`) over-counts by the number of circulation zones emitted.** Surfaced as `tests/geometry/test_eu13b_dwelling_conservation.py::test_t01_way_51781396_like_case_gives_69_not_85` failing `69 == 86` (17 extra circulation zones, one per storey of a 17-storey building). Fix: filter to `conditioned is not False` before asserting a dwelling count; this is not a conservation defect, `dwellings_total` is unaffected, only the raw zone-spec list length grew by design. *(EU-15 T05, 2026-08-30; `openubem/geometry/european_residential.py::european_building_layout_to_zone_specs`)*

- 🔴 **`_secondary()`'s pre-T04 mislabeling was not confined to top-level buildings — it also silently propagated through `l_shape_decomposition`/`courtyard_wing_unfold`'s own recursion, because a WING's own recursive call to `generate_european_ruled_storey_layout` can itself hit `_secondary()`, and `_combine_wing_results` only ever checked `dwelling_layout_emitted` on each wing before combining.** Pre-T04, a wing whose own ruled route failed but whose legacy strip-cut succeeded reported `dwelling_layout_emitted=True`, so `_combine_wing_results` accepted it — the *whole building* then reported a RULED top-level scheme (`l_shape_decomposition` or `courtyard_wing_unfold`) even though one of its wings was actually served by the (unlabelled) strip cutter internally. Measured: re-running the T03 replay's own reported figure ("1,469 ruled + 76 T02/T03 recovered = 1,545 of 2,541") against the fresh T04-fixed code (with T05's circulation threshold temporarily reverted to 3, isolating T04's own effect) gives **1,420 ruled of 2,516 prepared** — about 125 fewer than the pre-T04 count implied, entirely attributable to this wing-level unmasking, not to any dwelling-count reduction (0 buildings anywhere changed their declared count) and not to T05 (identical ruled count measured at circulation threshold 2 vs 3). This means the T01-T03 progress log's own "76 recovered" figure, and the original "1,469 (57.81%)" baseline, were themselves partially inflated by the same masking `FINDING 207` describes for the top level. *(EU-15 T04, 2026-08-30; `openubem/geometry/european_residential.py::_combine_wing_results`, `_secondary`)*

## European locations EU-16

- **`[OPEN]` A `geometry_outcome == DWELLING_LAYOUT_EMITTED[_IMPUTED_COUNT]` building's realized IDF zones are silently `one_zone_per_floor` (`_whole` names) instead of the ruled dwelling zones the side-car describes — measured fleet-wide after the T08 rebuild at 26–45 % of nominally-ruled buildings per district (Madrid 173/616 = 28.1 %, Lyon 52/198 = 26.3 %, London 18/40 = 45.0 %, Bologna 214/594 = 36.0 %)** — `_geometry()`/`_it_rows`/`_gb_rows`/`_mapped_rows` (`scripts/run_eu_s2_district_campaign.py`) compute and record `geometry_outcome` from the *intended* zone specs before `build_idf_for_building` ever runs; if `extrude_geometry`'s own internal `intersect_match` exception handler (`openubem/idf/surfaces.py:863-884`, the `_force_reroute_room_layout_to_one_zone_per_floor` / `_force_reroute_coreperim_to_one_zone_per_floor` safety nets already documented in the EU-13B chapter above) then rescues the building by silently rerouting it to `one_zone_per_floor`, that reroute succeeds (no exception reaches `prepare()`'s outer `except`, so it is never counted in `IDF_ASSEMBLY_FAILED_*`), but neither `geometry_outcome` in `prepared_buildings.csv` nor the `layouts/*.json` side-car (written earlier, independently, by `scripts/emit_eu11_layout_sidecars.py`) is ever updated to reflect it — the exact `D-EU-35` "pop-up and simulated IDF describe different geometry" failure mode, at a scale (26–45 %) an order of magnitude above the previously-documented `IDF_ASSEMBLY_FAILED_*` residual (0.94–4.7 %, EU-13B T09 entry above). Detected by `EU-16A` T08's own side-car-vs-IDF zone-structure parity check (per-floor dwelling-zone count + carved-core presence, matched by floor index since IDF zone names use the `stem` hash while the side-car uses the original `building_id` — raw string-set equality is never possible across the two). Not fixed here: `openubem/idf/surfaces.py` is out of scope for `EU-16A` T07/T08 (plan `PLAN_eu15-eu16-zoning-context-2026-08-30.md` §3 file layout), and correcting `geometry_outcome`/the side-car after the fact is a different task's file (`scripts/emit_eu11_layout_sidecars.py`, not touched by T07/T08 either); disclosed to the owner rather than silently absorbed into the T08 census. Note this is orthogonal to `EU-16`'s own T06/T07 changes — context shading and the adiabatic party-wall flip never change zone count (proven by `tests/idf/test_eu16_context_adiabatic.py`'s own zone-count-identical assertions) and are not implicated in this reroute. *(EU-16A T08, 2026-08-30; measured via a one-off census script, not committed to the repo — see `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md` T08 progress-log entry for the exact counts)*

**T09 update (2026-08-30, `D-EU-40`/`D-EU-41` T09 executor):** the 26–45 % figure above is the reroute count expressed as a fraction of the *nominally-ruled* (`DWELLING_LAYOUT_EMITTED*`) subset only. Measured directly by grepping the `rerouting to one_zone_per_floor` / `rerouting room_layout to one_zone_per_floor` warning pairs emitted by `openubem/idf/surfaces.py:868`/`:715` in each district's rebuild output (Madrid/Bologna: on-disk `openubem/outputs/eu_evidence/EU-11/{ES-MAD-BERRUGUETE,IT-BOL-GALVANI2}_t08_stdout.log`, dated 2026-08-30 18:26/18:30; Lyon/London: no stdout log existed on disk from the original T08 run, so `prepare()` was re-run locally once for each — deterministic, no sbatch, no geometry change — with stdout+stderr captured to reproduce the same counts). Counts are identical to T08's own numbers (173/52/18/214 — confirming they were already direct measurements, not an inference), but expressed **as a fraction of that district's total prepared IDFs** (the wording `D-EU-40`/`D-EU-41`'s T09 prompt asked for) the rate is materially lower: Madrid 173/961 = 18.00 %, Lyon 52/297 = 17.51 %, London 18/82 = 21.95 %, Bologna 214/1204 = 17.78 %. The `perimeter_core fallback to one_zone_per_floor` message (`surfaces.py:351`) fired 0 times in any of the four districts — every reroute observed went through the `room_layout`/`intersect_match`-exception path, none through the complexity-gate path. Still `[OPEN]`, still out of `EU-16`'s file layout (`surfaces.py` non-editable, `D-EU-41`).

- **`FINDING 210`: `** Severe ** RoofCeiling:Detailed="BLOCK <STEM>_CIRCULATION STOREY N CEILING 0001_k", Vertex size mismatch between base surface ... and outside boundary surface: BLOCK <STEM>_CIRCULATION STOREY N+1 FLOOR 0001_k / ...The vertex sizes are 8 for base surface and 9 for outside boundary surface.** — `**Fatal**  GetSurfaceData: Errors discovered, program terminates` at 2–4 s, before warmup, on ~8 % of the `EU-16` T09 wave-1 tasks (Madrid: 66/961 confirmed by remote grep). Root cause: a stacked circulation (or dwelling) zone's ring, cut by a shapely boolean (`plate.difference(circulation_polygon)` in `generate_european_grid_layout`, or the wing `unary_union` in `_combine_wing_results`), carries a sub-millimetre floating-point artifact at its boundary that a different GEOS build resolves differently when EnergyPlus pairs the ceiling of one storey with the floor of the storey above. Confirmed **not** reproducible on this Windows/GEOS build: two independent local rebuilds of the named example (`relation/12771676`, stem `8b3598ac47b3f4a0`, Madrid) produced byte-identical, internally-consistent geometry both times (0 vertex-count mismatches) — verified directly against the actual failing `eplusout.err` on Speed (`/speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE/out/8b3598ac47b3f4a0/eplusout.err`, task `1299912_33`), so this is a genuine cross-platform/cross-GEOS-build numerical-fragility bug (extends `FINDING 187`/`190`'s "a Speed number and a Windows number are not the same measurement" to geometry *validity*, not only simulation results), not a deterministic Python-logic defect reproducible by re-reading the code. A second example (`way/293591506`, stem `098e4fafcdf409c9`) showed the same signature on a non-circulation dwelling zone (`_0` block, merged 2×2-grid cell), confirming the fragility is general to any ring with a boolean-op-derived boundary, not circulation-specific. Fix: `_stabilize_ring_coords` (`openubem/geometry/european_residential.py`, new, ~1810) snaps every emitted dwelling/circulation ring to a fixed 1 mm precision grid (`RING_STABILIZATION_GRID_M = 0.001`, via `shapely.set_precision`) before `coords_m` is extracted in `european_building_layout_to_zone_specs`, with a fallback to the unsnapped ring if snapping ever degenerates the polygon (collapses below 3 vertices or to zero area). `openubem/idf/surfaces.py` was not touched (non-editable, `D-EU-41`). Tests: `tests/geometry/test_eu15_ruled_coverage.py`, `test_t09_*` (4 new: idempotency under a snap-then-reconstruct round trip up to vertex ordering, sub-mm near-duplicate-vertex removal, degenerate-sliver fallback, and that both dwelling and circulation zone specs actually route through the stabilizer). **Correction 2026-08-31 (reconstruction pass, after the killed session that wrote the paragraph above): NOT conclusively proved — the fix is measurably incomplete.** The `D-EU-42` v2 re-submission wave (jobs `1302748` Madrid 66 tasks, `1302781` Lyon 13 tasks, `1302782` London 2 tasks; superseding a v1 wave `1302150`/`1302151`/`1302152` that ran before the fixed IDFs existed and failed 100 %) recovered only Madrid 33/66 (50.0 %), Lyon 9/13 (69.2 %), London 1/2 (50.0 %) — 43/81 (53.1 %) overall, confirmed via `sacct -j <jobid> -X`. Every sampled remaining `FAILED` task's `eplusout.err` (checked across all three districts, e.g. Madrid stem `1d677f42eacf7815` task `1302748_8`, Lyon stem `489894ba3d990787` task `1302781_3`, London stem `5ff998a792035b20` task `1302782_2`) shows the **identical** `RoofCeiling:Detailed` vertex-size-mismatch fatal on a *different* surface pair each time (e.g. 5 vs 4, not always 8 vs 9), confirmed against freshly-rebuilt IDFs (`idfs/*.idf` mtime 2026-08-31 13:22, i.e. after the fix code's 09:17 commit, not stale). This means `_stabilize_ring_coords`'s 1 mm snap collapses only the sub-cases that really are sub-millimetre floating-point duplicates; roughly half the casualties have a **larger, non-sub-mm vertex-count discrepancy** between a storey's ceiling ring and the storey-above's floor ring — a genuine topological difference (plausibly a per-storey dwelling/circulation partition that differs in vertex count between adjacent storeys), which 1 mm snapping cannot and does not fix. Root cause of the residual defect was open until the root-cause pass below. See the T09 progress-log entry for the full per-district before/after count. **`RESOLVED` — root-cause pass 2026-08-31 (owner authorisation "vas-y, root-cause le défaut résiduel"):** the residual mismatch is **not** a ring-construction defect at all — `_stabilize_ring_coords` was already correct and its 1 mm-snapped rings going into extrusion were identical/consistent. Pulled the actual failing IDF for 3 named stems from the D-EU-42/D-EU-43 v2 fleets on Speed (`/speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE_finding210fix/idfs/1d677f42eacf7815.idf` etc.) and read the real `BUILDINGSURFACE:DETAILED` vertex lists for the exact surfaces named in each `eplusout.err`: the mismatch is introduced **after** extrusion, by `geomeppy`'s own `intersect_match()` (`openubem/idf/surfaces.py:866`, non-editable, `D-EU-41`), which computes new boundary vertices via live floating-point intersection arithmetic when it cuts a same-zone-label block (e.g. one `_2` dwelling-index or `_circulation` block spanning every storey carrying that label) against its per-storey neighbours — independently for the ceiling of storey n and the floor of storey n+1 (and, contrary to the original symptom text, not always same-label: reproduced cross-block pairs too, e.g. `..._0 Storey 1 Floor...` mismatched against `..._2 Storey 0 Ceiling...`). This is downstream of every ring-construction stage, so no further change to `_stabilize_ring_coords` or the circulation/dwelling ring builders in `openubem/geometry/european_residential.py` can fix it. Directly confirmed on 3 named stems rebuilt locally (`1d677f42eacf7815` Madrid, `489894ba3d990787` Lyon, `5ff998a792035b20` London — none of the three reproduced the mismatch on this Windows/GEOS build, consistent with this finding's own cross-platform-fragility characterization above) and on 3 further stems that **did** reproduce locally (`8b3598ac47b3f4a0`: 6 vs 3 and 3 vs 6 verts; `b88b3c3325df733e`: 3 vs 8, 7 vs 6, 3 vs 8, 3 vs 8, 7 vs 6 verts across 6 pairs; `33299a5b2a5bb9c9`: 6 vs 3 and 3 vs 6 verts). Fix: `scripts/run_eu_s2_campaign.py::build_idf_for_building` (imports added ~line 49-56, gate inserted ~line 422-448) now calls the exact gate/reroute safety net `openubem/idf/builder.py` already wires for the same symptom on its own (`layout_assign`) pipeline — `find_mismatched_interzone_pairs` + `_force_reroute_room_layout_to_one_zone_per_floor` (both already exist in `openubem/idf/surfaces.py`, non-editable, and the latter already explicitly supports `mode="european_dwelling_layout"` zones) — right after `extrude_geometry`, before `apply_adiabatic_party_walls`. This was simply never wired into the EU S2 campaign build path (only into the unrelated `layout_assign` pipeline in `builder.py`), so every affected IDF shipped to Speed with the mismatch still live. `one_zone_per_floor` has no interzone perim pairs, so it cannot reproduce this class of mismatch by construction; `scripts/run_eu_s2_district_campaign.py:383-392` now also disclosifies the reroute into `geometry_outcome` (`..._INTERZONE_MISMATCH_REROUTED`) so a mid-build degrade is never silently masked in `prepared_buildings.csv`. Proof (first pass, later found incomplete): all 52 stems still `FAILED` under D-EU-42/D-EU-43's v2 wave (32 Madrid `finding210fix` + 11 Madrid `deu43fix` + 4 Lyon `finding210fix` + 4 Lyon `deu43fix` + 1 London `finding210fix`, confirmed by remote grep of every v2 `eplusout.err`) were rebuilt locally; `find_mismatched_interzone_pairs` returned empty for all 52 post-build. A first `v3` wave was submitted on this basis (jobs `1302881`/`1302908`/`1302920`) but **cancelled** (`scancel`) within minutes, mid-run, on catching real Speed `FAILED` tasks under the SAME `RoofCeiling:Detailed` fatal while it was still draining — the raw-`len(coords)`-count check is **not sufficient**: confirmed by running EnergyPlus 23.1.0 directly (Windows, this session, `C:\EnergyPlusV23-1-0\energyplus.exe`) on stem `e21bec78b937acf5`, which `find_mismatched_interzone_pairs` had passed clean (both paired surfaces carried 7 raw vertices, mirror-ordered) yet still FATALed identically to Speed — the culprit was a sub-mm near-duplicate vertex pair (~0.0002-0.0006 m apart) `intersect_match` had inserted into **both** surfaces' own rings, which EnergyPlus's own GetVertices/CheckConvexity collapses asymmetrically depending on ring winding direction. Extended the gate with `_has_near_duplicate_vertex_surfaces` (`scripts/run_eu_s2_campaign.py`, new): flags any surface whose own ring has two consecutive vertices closer than `NEAR_DUPLICATE_VERTEX_TOLERANCE_M = 0.005`. Rebuilt and re-verified against real EnergyPlus: stem `8cdf349a99934f0d` (a stem the *first* fix pass had also called clean) still FATALed — its ring carried no near-duplicate points at all, but vertex 7 of 9 sat at an interior angle of exactly 180.000000 deg (`cos(angle) = -1.0000000000000002`, i.e. collinear to machine precision) where a neighbouring zone's wall met the shared edge; EnergyPlus's convexity check legitimately drops that redundant point but not symmetrically between the ceiling and its mirrored floor. Extended the gate again with a collinearity check inside the same function (`COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG = 0.1`, i.e. interior angle > 179.9 deg) -- tuned tight enough (0.65 deg of headroom) to not fire on a real, naturally near-straight OSM corner measured at 179.348 deg on a known-clean building (`BATIMENT0000000240879449_part0`, `tests/test_eu_s2_campaign.py`), which the first, looser 2 deg tolerance had wrongly flagged. Final proof: all 52 stems rebuilt with the twice-extended gate, then run end-to-end through real local EnergyPlus 23.1.0 (`ExpandObjects` + `energyplus.exe`, matching `scripts/cluster/submit_fleet_t08.sbatch`'s exact invocation) -- **0/52 FATAL**, not merely 0 by the Python-level heuristic. The 52 rebuilt IDFs were re-shipped and a corrected `v3` `sbatch --array` wave submitted per the owner's separate authorisation ("continuer jusqu'a la fin"): jobs `1302937` (Madrid, 43 tasks), `1302954` (Lyon, 8 tasks), `1302962` (London, 1 task) — fire-and-forget, confirmed queued/running via one `squeue` check, not yet harvested; harvest/fold-in is a follow-up, not this pass. **Recurrence, job `1311158`, stem `cee45cbc2718154c` (`BATIMENT0000000240880410_part0`, `FR-LYO-HAUTCOEURPENTES`), 2026-09-07:** identical `RoofCeiling:Detailed` vertex-size-mismatch fatal repeated on every storey pair. `prepared_buildings.csv` carried `fallback_reason = near_duplicate_vertex_tolerated_box` — the post-extrude at-risk gate (`scripts/run_eu_s2_campaign.py::build_idf_for_building`) had detected the near-duplicate vertices, called `_force_reroute_room_layout_to_one_zone_per_floor`, and that safety net **correctly declined** (not a bug): the building's floor-0 union carries a genuine ~34.9 m² courtyard hole, and the function's own courtyard guard (`if any(Polygon(r).area >= 1.0 for r in footprint.interiors): return False`, `openubem/idf/surfaces.py:693-694`) refuses to collapse a holed footprint into a single donut block. With `mismatched` false, the gate then tolerated the unresolved near-duplicate vertices instead of raising — that toleration is what let the fatal ship. Remedy for this one building: a scratchpad driver script monkeypatched `scripts.run_eu_s2_campaign._force_reroute_room_layout_to_one_zone_per_floor` (module-reference swap only, no file edited, same technique as `scripts/eu17_reroute_trace.py`) with a forced variant that is identical except the courtyard-hole guard is removed — the interior ring is always filled (`Polygon(footprint.exterior)`, the same fill the real function already applies unconditionally to sub-1.0 m² slivers), sacrificing the courtyard void for this building only. Rebuilt from the repo root so `Schedule:File` paths came out in the portable `../../schedules/<stem>/...` form (`FINDING` at line ~1863). Zone count collapsed 29 dwelling-layout zones → 8 one-zone-per-floor zones. Proved on real EnergyPlus 23.1.0 (`ExpandObjects` then `energyplus.exe -w fr_lyon_bron_2023_era5.epw -d <outdir> expanded.idf`, matching `scripts/cluster/submit_fleet_t08.sbatch`'s exact invocation): exit code 0, 0 `** Fatal **`, 0 `** Severe **` (only the "0 Severe Errors" summary lines matched the grep), `EnergyPlus Completed Successfully-- 29 Warning; 0 Severe Errors`. Shipped: `idf_sha256` `55d5b0506399c7...` → `a8f0ad325d9daf...`; `openubem/outputs/eu_evidence/EU-11/FR-LYO-HAUTCOEURPENTES_final_2026-09-07/idfs/cee45cbc2718154c.idf` and `prepared_buildings.csv` updated (`fallback_reason` → `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED`, the existing reroute-outcome token from `scripts/run_eu_s2_district_campaign.py:667`, not a new one); scp'd over the staged copy at `speed-submit2:/speed-scratch/o_iseri/fleets/EU11_FR-LYO-HAUTCOEURPENTES_final_2026-09-07/idfs/cee45cbc2718154c.idf` (sha256 verified post-transfer) and the stale `out/cee45cbc2718154c/` removed; `fleet.lst` line 54 in that staged fleet dir. Not resubmitted (`sbatch` deliberately not run this pass). *(EU-16 T09 / FINDING-210 root-cause pass, 2026-08-31; `scripts/run_eu_s2_campaign.py::build_idf_for_building`, `_has_near_duplicate_vertex_surfaces`; `scripts/run_eu_s2_district_campaign.py:387-392`, reusing `openubem/idf/surfaces.py::find_mismatched_interzone_pairs`/`_force_reroute_room_layout_to_one_zone_per_floor`)* **Recurrence, job `1311708` (Bologna `IT-BOL-GALVANI2_delta_2026-09-07`, 703 tasks), 2026-09-08: 8 `FAILED` tasks, all inside the `D-EU-58` tolerated set, none outside it.** Measured, not sampled: every one of the 8 failed stems (`4f47a3941f7067c9` idx 89, `c1a0da4dcda7a8e2` 96, `19aed30fa5b6afa7` 139, `acb6af4c0a661cee` 181, `56360df35f445afa` 343, `9845d84fa4365361` 352, `908ebf96c2b75929` 378, `f04a1a2ece7f9ca6` 386) carries `fallback_reason = near_duplicate_vertex_tolerated_box` in `prepared_buildings.csv`, i.e. the `D-EU-58` branch at `scripts/run_eu_s2_campaign.py:713-715` where the near-duplicate-vertex heuristic fired, the raw `mismatched` check did not, the reroute declined, and the already-emitted geometry was deliberately retained rather than discarded. Signature split: 7 of 8 the classic `RoofCeiling:Detailed` vertex-size mismatch, 1 of 8 (`acb6af4c0a661cee`) the `D-EU-43` `Zero or negative surface area[5.77027E-009]` sliver — both previously-accepted classes, no new signature (no `FINDING 253` construction-mirror, no `CalcCoordinateTransformation` class). Specificity is exact: of the 19 tolerated buildings in `fleet.lst`, 8 `FAILED` / 7 `COMPLETED` / 4 not yet run, and **0 `FAILED` tasks outside the tolerated set** across 463 finished tasks. So the toleration is the sole failure source in this campaign and its observed EnergyPlus survival rate is 7/15 (47 %) — the price of `D-EU-58` retaining geometry instead of losing the building outright. No fix applied and none proposed: the disposition is the owner's 2026-09-01 `D-EU-58` ruling. *(EU-11 Bologna delta harvest, 2026-09-08; `sacct -j 1311708 -X`, `grep "Last severe error" out/<stem>/eplusout.err`)*

- **`D-EU-43` — `** Severe ** CheckConvexity: Surface="BLOCK <STEM>_<N> STOREY <k> CEILING/FLOOR/ROOF 0001_j" is non-planar. Coincident Vertices will be removed as possible.` followed by `** Severe ** GetSurfaceData: Zero or negative surface area[~1E-08 to 1E-09], Surface=...` then `**Fatal** GetSurfaceData: Errors discovered, program terminates`** — a second EnergyPlus-side symptom of the exact same `FINDING 210` root cause (not a new defect): 45 `EU-16` T09 wave-1 tasks (32 `ES-MAD-BERRUGUETE`, 13 `FR-LYO-HAUTCOEURPENTES`) excluded from `D-EU-42`'s FINDING-210 count because their `eplusout.err` shows no "Vertex size mismatch" line, only this convexity/zero-area pair. Classified by reading the actual `.err` for the named example (`way/435212756`, stem `b3a72cccb2b91f80`, Madrid, `/speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE/out/b3a72cccb2b91f80/eplusout.err`): `CheckConvexity` prints the offending vertex triple for `BLOCK B3A72CCCB2B91F80_4 STOREY 0 CEILING 0001_3` as `(440040.878,4479054.608,3.000)`, `(440039.337,4479062.177,3.000)`, `(440040.878,4479054.608,3.000)` — the first and third listed vertices are literally coincident, a near-duplicate/near-degenerate point on a boolean-op-derived dwelling ring (the same class of GEOS-build-dependent artifact as `FINDING 210`, just resolved by EnergyPlus's convexity/zero-area check instead of its vertex-count-pairing check). No separate fix was needed: `_stabilize_ring_coords`'s 1 mm precision snap (the `FINDING 210` fix, same `file:line`) already collapses exactly this class of coincident vertex before `coords_m` is emitted — confirmed by `test_t09_stabilize_ring_coords_removes_a_sub_millimetre_near_duplicate_vertex` (synthetic direct proof of the mechanism) and by regenerating the named example locally (`way/435212756`): as on the `FINDING 210` examples, this building's geometry already regenerates clean/degenerate-artifact-free on this Windows/GEOS build, consistent with the defect being GEOS-build-dependent rather than a deterministic Python-logic bug. **Correction 2026-08-31 (reconstruction pass): NOT conclusively proved — same shortfall as `FINDING 210`.** The `D-EU-43` v2 wave (jobs `1302787` Madrid 32 tasks, `1302788` Lyon 13 tasks; superseding a v1 wave `1302265`/`1302266` that ran before the fixed IDFs existed and failed 100 %) recovered Madrid 20/32 (62.5 %) and Lyon 8-9/13 (one task still `RUNNING` at reconstruction time) — roughly 60-65 %, not the "clean" outcome implied above. Sampled remaining failures (e.g. Madrid stem `33299a5b2a5bb9c9` task `1302787_8`) still show the exact `RoofCeiling:Detailed` vertex-size-mismatch fatal, not a fresh convexity/zero-area symptom, confirming these residual failures are the same unresolved `FINDING 210` root cause described in that entry's correction, carried through here since `D-EU-43`'s 45 stems were a subset excluded from `D-EU-42`'s count only by which EnergyPlus check happened to fire first. See the T09 progress-log entry for the full per-district before/after count. **`RESOLVED` — root-cause pass 2026-08-31:** same real root cause and same fix as `FINDING 210`'s root-cause-pass correction (`intersect_match`-introduced post-extrusion vertex divergence, gated in `scripts/run_eu_s2_campaign.py::build_idf_for_building` via the existing `find_mismatched_interzone_pairs`/`_force_reroute_room_layout_to_one_zone_per_floor` safety net) — `33299a5b2a5bb9c9` is one of the 3 named proof stems there (6 vs 3 / 3 vs 6 vertex mismatches resolved to 0 by the reroute). The `D-EU-43` 11 Madrid + 4 Lyon residual stems are included in that entry's 52-stem rebuild and the corrected `v3` resubmission (jobs `1302937`/`1302954`/`1302962`); not tracked separately here. *(EU-16 T09 / `D-EU-43`, 2026-08-31; see `FINDING 210` for the fix file:line)*

- **`FINDING 210` / `D-EU-43` — harvest of the corrected `v3` wave (jobs `1302937`/`1302954`/`1302962`), completed 2026-08-31.** `sacct -j 1302937,1302954,1302962 --format=JobID,State,ExitCode -X` shows all 52 array tasks `COMPLETED`, `0:0` (43 Madrid, 8 Lyon, 1 London) — the twice-extended gate holds on Speed, not only on the local Windows proof. **Separate finding, same harvest pass: the base `EU11_<district>/out/` tree (not the `_finding210v3` suffixed dir the job actually wrote to) held stale, non-Speed data for exactly these same 52 stems** — `find EU11_ES-MAD-BERRUGUETE/out -maxdepth 2 -name platform.txt | wc -l` returns 918/961 (43 missing), and the equivalent counts for Lyon (289/297, 8 missing) and London (81/82, 1 missing) match the 52-stem `v3` scope exactly; a normal `submit_fleet_t08.sbatch` task always writes `platform.txt`/`energyplus_version.txt` (confirmed on 3 untouched Madrid stems), so their absence marks non-sbatch data. Direct check on stem `8b3598ac47b3f4a0` (Madrid): the base tree's copy has `task.rc=0`/"Completed Successfully"/4 min runtime but mtime `2026-08-31 14:58:32`, which predates job `1302937`'s own per-task completions (15:13-15:19, fleet dir created 14:52) — this is a leftover of the session's own local-Windows proof run (`ExpandObjects`+`energyplus.exe` invocation cited above), copied into the base tree by an undocumented step, not a Speed measurement. Resolution: the harvest read the 52 results directly from `EU11_<district>_finding210v3/out/<stem>/` (real Speed data, `sacct`-confirmed) and overwrote the corresponding manifest rows, never trusting the base tree for these 52 stems; `platform`/`energyplus_version` are left blank for them in the manifest since the `_finding210v3` fleet-dir invocation itself never wrote those two sidecars (confirmed: `tar` over the same file list against the real job's own `out/` also warns `Cannot stat: platform.txt`/`energyplus_version.txt` — a property of that resubmission's script invocation, not of the base-tree contamination). **New, unresolved gap found during this harvest: 2 Madrid stems (`df490cc7ec52ebb4` = `way/380242666`, `5897ad5bdd60c3ae` = `way/941927233`) carry a zero/negative-surface-area (`degenerate surfaces`/`Invalid dot product`) fatal, are absent from the 43-stem `v3` `fleet.lst`, and were never resubmitted under any wave** — the plan's own T09-continuation entry enumerated 43 Madrid residual stems (32 `finding210fix` + 11 `deu43fix`) against an earlier v2-residual count of 45 (98 casualties − 53 v2-recovered) without reconciling the 2-stem gap; these 2 are that gap. `[OPEN]`, disclosed, not fixed here (outside this harvest's scope — no further Speed submission was authorised). *(EU-16 T09 harvest pass, 2026-08-31; `scripts/cluster/harvest_eu11_district.py`, ad hoc fold script; see `RESULTS_EU-11.md` for the corrected per-district counts)*

- **`[OPEN]` `FINDING 249` — `rerouting room_layout to one_zone_per_floor` fires on 1,306 of 2,262 buildings (57.7 %) once the no-core dwelling layouts replace the core-era ones, silently discarding every one of those layouts.** Same `intersect_match` root cause as `FINDING 210` above, same gate, but the gate has stopped being a rare rescue and become the majority path. Measured 2026-09-03 over the four rebuilt trees `openubem/outputs/eu_evidence/EU-11/<DISTRICT>_nocore_2026-09-03/prepared_buildings.csv`: `..._INTERZONE_MISMATCH_REROUTED` = Madrid 618, Bologna 529, Lyon 119, London 40 (**1,306**), against **2** fleet-wide in the delivered core-era build (`EU-11/<DISTRICT>/`, Madrid 2, others 0). Cause of the change in rate: `EUROPEAN_LAYOUT_REGIME = "nocore"` (`openubem/geometry/european_nocore.py`, seamed at T03) divides each plate into dwellings only — no core, no circulation — so a storey carries more, smaller zones and therefore many more shared interzone surfaces for geomeppy's `intersect_match` (`openubem/idf/surfaces.py:866`, non-editable, `D-EU-41`) to recompute by live floating-point intersection; the vertex divergence it introduces is per-surface, so the more shared surfaces there are the likelier at least one pair diverges. Effect: `_force_reroute_room_layout_to_one_zone_per_floor` throws the dwelling layout away and rebuilds the building as one whole-building zone per storey, while `scripts/run_eu_s2_district_campaign.py:387-392` still labels the row `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` — accurate, but it reads as an emitted layout in every downstream count. Verified in the IDFs, not from the label: 32 sampled stems, real ones carry `_F<n>_dwelling_<k>` zones (Bologna `387f4fea` 30, Lyon `a3fabf61` 29, London `ed827c95` 69), rerouted ones carry only `_F<n>_whole` and **zero** `_dwelling_` zones (Madrid `959c9188` 3/3, Lyon `197fe0f9` 7/7, Bologna `1ef46361` 7/7). Net effect on the fleet: real dwelling layouts **1,446 → 956** (−490) even though `FALLBACK_PENDING_LAYOUT*` collapsed 1,096 → 265, i.e. the new cutter divides 831 plates the old logic refused and the assembler discards more than it gains. **Not fixed, and deliberately not worked around** — no threshold moved, `NEAR_DUPLICATE_VERTEX_TOLERANCE_M` (0.005) and `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG` (0.1) left as tuned, `MAX_FLAT_ASPECT` still 2.5. Two mechanism probes on Madrid failed to separate the groups: `k = 1` share 27.8 % rerouted vs 41.5 % clean (median `k` 2 both); median footprint vertices 6 vs 5, storeys 4 vs 4, reflex vertices 1 vs 0, rectangularity 0.847 vs 0.880. This is the finding that failed `CP-2` and stopped the Speed campaign. *(`PLAN_eu-engine-nocore-carryin-2026-09-03.md` §8 T05; audit artifact `openubem/outputs/eu_evidence/EU-21/engine_parity/idf_audit_2026-09-03.json`; full record `STATE_european_locations_v5.md` §3 `FINDING 249`)*

- **`[OPEN]` `IDF_ASSEMBLY_FAILED_RuntimeError` appears on 17 buildings that assembled cleanly in the core-era build** — Madrid 9, Lyon 4, Bologna 4, London 0, recorded in each district's `summary.json` `blocker_exclusions` under `EU-11/<DISTRICT>_nocore_2026-09-03/`. These buildings get **no IDF at all**, so the prepared population is 2,527 against the census's 2,544 (Madrid 961→952, Lyon 297→293, Bologna 1204→1200, London 82→82); no *new* building appears and no attribute changed (`archetype_id`/`building_type`/`age_band` diff 0/0/0 on all 2,527 common rows). Caught by the `except (RuntimeError, ZeroDivisionError, IndexError)` arm at `scripts/run_eu_s2_district_campaign.py:434-441`, which records the exception type but not its message, so the underlying `RuntimeError` text is not on disk — retrieving it is the first step of any fix. Same trigger window as `FINDING 249` (the no-core seam), second-order beside it, disclosed rather than fixed. *(`PLAN_eu-engine-nocore-carryin-2026-09-03.md` §8 T05, deviation 2)*

- **`D-EU-44` — `RESOLVED`, 2026-08-31: both unaccounted Madrid stems recovered, `FINDING 210`'s Madrid/Lyon/London residual is now zero.** Owner authorisation, verbatim: *"oui, autorise D-EU-44 continuer jusqu'a la fin"* (owner, 2026-08-31). `df490cc7ec52ebb4` (`way/380242666`) and `5897ad5bdd60c3ae` (`way/941927233`) were rebuilt through the exact same fixed code path (`scripts/run_eu_s2_district_campaign.py::prepare`'s per-building loop, filtered to these 2 `building_id`s, calling `scripts/run_eu_s2_campaign.py::build_idf_for_building`, the twice-extended `find_mismatched_interzone_pairs`/`_has_near_duplicate_vertex_surfaces`/`_force_reroute_room_layout_to_one_zone_per_floor` gate from the root-cause pass above, unmodified) — the gate fired for both (`rerouting room_layout to one_zone_per_floor (near_duplicate_vertex)`), confirming the same mechanism. **Proven locally first, real EnergyPlus 23.1.0 (Windows, `ExpandObjects.exe`+`energyplus.exe`, matching `submit_fleet_t08.sbatch`'s own invocation), not a Python-heuristic-only check**: both rebuilt IDFs ran `RC=0`, `0 Severe Errors`, `0 Fatal Errors`, `EnergyPlus Completed Successfully`. Rebuilt IDFs confirmed byte-identical (`sha256sum`) between the local proof and the tarball shipped to Speed. Shipped to a dedicated fleet dir (`/speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE_deu44`, never touching the shared `EU11_ES-MAD-BERRUGUETE` base tree) and submitted as **one** `sbatch --array=1-2%2` job, `1303012`. `sacct -j 1303012 -X --format=JobID,State,ExitCode,Elapsed` confirms both tasks `COMPLETED`/`0:0` (`1303012_1` 00:02:36, `1303012_2` 00:07:24); both `eplusout.err` on Speed also show `0 Severe Errors`/`EnergyPlus Completed Successfully`, matching the local proof — Speed-side confirmation, not only Windows. Heating recovered via the same `Zone Ideal Loads Zone Total Heating Energy` SQL query: `df490cc7ec52ebb4` 22,995.2274 kWh / 438.6929 m² = 52.4176 kWh/m²; `5897ad5bdd60c3ae` 7,352.8695 kWh / 194.5278 m² = 37.7986 kWh/m² (`floor_area_m2` for both moved slightly from the pre-fix `DWELLING_LAYOUT_EMITTED` value — 439.0326→438.6929, 195.5908→194.5278 — the same union-of-storey-floor-polygons effect already disclosed for the other 50 `D-EU-42`/`D-EU-43` reroutes). Both folded into `es_mad_berruguete_manifest.csv`/`prepared_buildings.csv`, replacing the two `FATAL`/blank rows; `platform`/`energyplus_version` left blank for these 2 rows, same cause as the 52-stem `v3` wave (the remote-deployed `submit_fleet_t08.sbatch` does not write those two sidecars — `[OPEN, cosmetic]`, EU-14B chapter, not a new defect). Madrid: **961/961 success, 0 Speed-failed** — pooled EUI moved 72.1258→72.1096 kWh/m². `generate_eu_3d_viewers.py` re-run for all four districts; `diff -rq` on every viewer file and data dir (Madrid + the three unchanged districts) — all 8 checks byte-identical, zero output. *(`D-EU-44`, 2026-08-31; `scripts/run_eu_s2_district_campaign.py::prepare`, `scripts/run_eu_s2_campaign.py::build_idf_for_building`, unmodified — same gate as `FINDING 210`'s fix; see `RESULTS_EU-11.md` §`D-EU-44` for the full write-up)*

## European locations, ceiling82 (2026-09-05)

- **`** Severe ** Schedule:File="EU_STEP8_GAINSCHEDULE_<STEM>_..." File Name: "../../schedules/<stem>/<stem>_..._gain.csv" not found` → `**Fatal** ProcessScheduleInput: Preceding Errors cause termination`, 100 % of a Speed array (317/317 across 4 jobs)** — the director staged a Speed submission tarball containing only `idfs/` + `weather/` + `fleet.lst`, omitting the `schedules/<stem>/` per-building directory that `run_eu_s2_district_campaign.py::prepare()` also writes and that every European IDF's `Schedule:File` objects reference by relative path (`../../schedules/<stem>/...`). Every EnergyPlus task fails at sizing, before warmup, 0.1-0.2 s in — a packaging omission, not a geometry or code defect (`ES-MAD-BERRUGUETE`/`FR-LYO-HAUTCOEURPENTES`/`GB-LDN-STDUNSTANS`/`IT-BOL-GALVANI2` Step 2 delta jobs `1307761`/`1307762`/`1307771`/`1307773`, confirmed via `eplusout.err` on the first task of each). Fix: always stage/tar/ship all three of `idfs/`, `weather/`, `schedules/` (plus `fleet.lst`) together for any EU district Speed submission — never `idfs/`+`weather/` alone, even though most fleets' schedules are static enough that this is easy to forget. Re-shipped with `schedules/` included and resubmitted (see `PLAN_eu-82pct-ceiling-2026-09-05.md` §8, "Step 2 delta wave" entry, correction). *(director packaging step for `PLAN_eu-82pct-ceiling-2026-09-05.md`'s Step 2 delta wave, 2026-09-05; `scripts/run_eu_s2_district_campaign.py::prepare`, `scripts/cluster/submit_fleet_t08.sbatch`)* **Recurred identically 2026-09-07** on the `_final_2026-09-07/` re-emission wave: FR job `1311066` failed 91/91 in 0.4 s with the same `Severe`/`Fatal` pair, and GB's staged fleet dir had the same omission (`ls schedules | wc -l` = 0 against `fleet.lst` = 299). Contributing detection miss: `grep -c "Schedule:File"` on a staged IDF returned 0 and was read as clean, but the emitted objects are uppercase `SCHEDULE:FILE` — grep case-insensitively, and treat `task.rc` / `sacct` State as the primary signal rather than a hand-written `Fatal` grep. Fix: shipped the per-stem `schedules/` dirs listed by `awk -F, 'NR>1{print "schedules/"$3}' simulate_list_<D>_2026-09-07.csv`, verified `ls <fleetdir>/schedules | wc -l` equals the `fleet.lst` line count and that `File Name` is the relative `../../schedules/<stem>/...` form, cleared `out/`, resubmitted as `1311158` (FR) / `1311214` (GB). Standing check before any EU Speed submission: four things, not three — `idfs/`, `weather/`, `schedules/`, `fleet.lst`. (`submit_fleet_t08_frgb_2026-09-07.sbatch`'s own header comment lists only three, which is what makes this recur.)

- **Same symptom (`Schedule:File=... File Name: "C:\Users\...\scratchpad\t08_build\<stem>\<stem>_..._gain.csv" not found` → `**Fatal** ProcessScheduleInput`), third distinct root cause: an absolute local Windows path baked into the IDF instead of the `../../schedules/<stem>/...` relative convention** — T08's `FINDING 253` remedy rebuild ran the per-building build path from inside a Claude Code scratchpad directory (`scratchpad/t08_build/<stem>/`) via a non-repo driver script, so the schedule-CSV writer emitted a path relative-resolved from that cwd instead of the portable relative form every other IDF in the fleet uses. `schedules/<stem>/` *was* staged this time (the fix above was applied), but the absolute path made it irrelevant — 7/7 tasks (Madrid `1309342`, Bologna `1309346`) failed instantly, 100 %. Fix: rewrite each `SCHEDULE:FILE` object's `File Name` field, replacing the absolute `scratchpad/t08_build/<stem>/` prefix with `../../schedules/<stem>/`, on the 7 staged IDFs before re-shipping (117 substitutions across 7 files); resubmitted as `1309355`/`1309357`. Lesson: any IDF built by a script invoked from a non-canonical working directory needs its `Schedule:File` paths checked/rewritten before Speed submission, not just its `schedules/` directory staged. *(director packaging audit for `PLAN_eu-82pct-ceiling-2026-09-05.md` T08 remedy submission, 2026-09-05)*

- 🔴 **`FINDING 252` — the backlog wave's `FAILED` tail (24 tasks: Madrid 11/`1306953`, Bologna 12/`1305186`, London 1/`1306951`, all `GetSurfaceData`/`Fatal` at 0.2-1.4 s) is NOT one accepted class, contrary to this session's earlier report — it is FOUR distinct signatures**, read directly from every failed `eplusout.err`'s `Last severe error=` line (not from `sacct` alone): (1) classic `FINDING 210` `RoofCeiling:Detailed` vertex-size mismatch — 13/24 (54 %: Madrid 7, Bologna 5, London 1); (2) **new** `GetSurfaceData: Construction EU_ROOF_CONSTRUCTION of interzone surface ... does not have the same materials in the reverse order as the construction EU_FLOOR_CONSTRUCTION of adjacent surface ...` — 7/24 (29 %: Madrid 2, Bologna 5), see `FINDING 253`; (3) `GetSurfaceData: Zero or negative surface area[~1E-07 to 1E-09]` sliver, the `D-EU-43` family — 3/24 (12.5 %: Madrid 1, Bologna 2); (4) **new** `CalcCoordinateTransformation: Invalid dot product` fatal, preceded by `CheckConvexity: ... is non-planar` (×13) and `114 degenerate surfaces` — 1/24 (4 %, Madrid task `1306953_9`, stem `c71e82e57d99bed1`), not yet root-caused, `[OPEN]`. Classes (1) and (3) are the previously-accepted `FINDING 210`/`D-EU-43` GEOS-build-fragility tail and need no action. Class (2) is deterministic and fixable (`FINDING 253`). Class (4) needs a dedicated pass if it recurs at scale — one occurrence so far, not blocking. *(`PLAN_eu-82pct-ceiling-2026-09-05.md`, backlog-wave harvest-monitoring pass, 2026-09-05; classified via `sacct -j <job> --format=State -n -X | grep -i fail` then `grep "Last severe error"` on each stem's `eplusout.err`)*

- **`FINDING 253` — `** Severe ** GetSurfaceData: Construction EU_ROOF_CONSTRUCTION of interzone surface BLOCK <STEM>_<N> STOREY <k> ROOF 0001... does not have the same materials in the reverse order as the construction EU_FLOOR_CONSTRUCTION of adjacent surface BLOCK <STEM>_<M> STOREY <k+1> FLOOR 0001...` → `**Fatal** GetSurfaceData: Errors discovered, program terminates`, 7 of the backlog wave's 24 `FAILED` tasks (Madrid `04c3d8bc97b3aa32`/`dc4c8768bb34abb7`; Bologna `4d40e0364b2f0e16`/`8ffb2e11b301694b`/`e263ff00a0544470`/`ebeee3778fe053f0`/`a0e24919ff9d7e35`).** Root cause identified, not fixed: `scripts/run_eu_s2_campaign.py:587-594` assigns a single per-district `roof_construction` to every surface whose `Surface_Type` is `ROOF`/`ROOFCEILING` and a single `floor_construction` to every `FLOOR`/`CEILING`, purely by nominal type, with no check of `Outside_Boundary_Condition` (set earlier by `extrude_geometry`'s `intersect_match`, line ~503). Both constructions are single-layer `MATERIAL:NOMASS` (`openubem/idf/european_physics.py:34-54`, `add_nomass_construction`) built from **different** U-values (`u_roof_w_m2k` vs `u_floor_w_m2k`, `_envelope_construction`, line 453-457) — so `EU_roof_Construction` and `EU_floor_Construction` reference two different materials and can never satisfy EnergyPlus's interzone reverse-layer-order check, regardless of vertex geometry. This only fires when one dwelling block is shorter than its neighbour (a massing/wing height difference from the direct-cutter/no-core layout): the shorter block's top surface is locally typed `ROOF` (no zone above it *within that block*) while `intersect_match` still pairs it, correctly, as an interzone surface against the taller neighbour's `FLOOR` at that level — a real, deterministic construction-assignment gap, not a `FINDING 210`-class floating-point/GEOS fragility. Candidate fix (not applied): any surface with `Outside_Boundary_Condition == "Surface"` must take a construction that is the material-identical mirror of its partner's, regardless of its own nominal `Surface_Type` — e.g. one shared symmetric interzone floor/ceiling construction for every `ROOF`↔`FLOOR`/`CEILING` interzone pair, applied after `intersect_match`, leaving true exterior/ground surfaces on the existing per-type constructions. Not yet verified locally or on Speed. *(`PLAN_eu-82pct-ceiling-2026-09-05.md` backlog-wave harvest, 2026-09-05; `scripts/run_eu_s2_campaign.py:453-457,587-594`; `openubem/idf/european_physics.py:34-54`; handed to an external Gemini/Antigravity session for root-cause verification + fix proposal, see `prompts/DONE/EXECUTOR_PROMPT_debug-failed-sims-2026-09-05.md` (and its `-v2.md`, both now in `DONE/`))*

- **`FINDING 253` — root cause CONFIRMED by external Gemini/Antigravity session, fix proposed and locally verified, not yet applied to production code.** Director (this session) audited the deliverable (`openubem/outputs/eu_evidence/EU-11/ceiling82_2026-09-05_debug/report.md`) and independently re-read the cited lines directly — citations match the live file (`scripts/run_eu_s2_campaign.py:544` reroute call, `:573-575` `near_duplicate_vertex_tolerated_box` bypass, `:584-591` construction-assignment block, current numbering; `openubem/idf/surfaces.py:693-694` courtyard-hole refusal `area >= 1.0 m²`) — not a hallucinated diagnosis. Local EnergyPlus 23.1.0 reproduction on all 3 named stems: `RC 1`, exactly the same `Last severe error=` text as the Speed logs. Proposed fix (unified diff against `scripts/run_eu_s2_campaign.py:587-594`): when a nominal `ROOF`/`ROOFCEILING` surface's `Outside_Boundary_Condition == "SURFACE"` (i.e. it is actually an interzone boundary, not a true exterior roof), assign `floor_construction` instead of `roof_construction`, so both sides of the interzone pair share one material-identical construction; true exterior roofs (`Outside_Boundary_Condition == "Outdoors"`) are untouched. Verified locally on stem `04c3d8bc97b3aa32` with the diff applied: `RC 0`, `EnergyPlus Completed Successfully`, full annual run. Not yet applied to the shipped `.py` file or resubmitted to Speed — that decision belongs to the plan owner, per the executor prompt's own scope limit. *(`report.md` §Task A, 2026-09-05; audited against `scripts/run_eu_s2_campaign.py` and `openubem/idf/surfaces.py` same date)*

- **`FINDING 253` — fix applied to `scripts/run_eu_s2_campaign.py` (T08), rebuilt+verified on all 7 named stems, shipped and confirmed on Speed. CLOSED.** T08 (fresh Sonnet executor) extracted `_assign_envelope_constructions()`: a `ROOF`/`ROOFCEILING` surface with `Outside_Boundary_Condition == "Surface"` now gets `floor_construction` instead of `roof_construction`, matching its interzone partner; 4 new regression tests added to `tests/test_eu_s2_campaign_ceiling82.py`, full required suite 76/76 passed. Director audited the diff against the plan spec (matches exactly) and independently re-verified all 7 stems' local `eplusout.end`/`eplusout.err` (not just the executor's self-report): 7/7 `RC 0`, 0 Fatal, Severe counts matching T08's table exactly. Packaged as 2 small per-district Speed array jobs (Madrid `1309355`×2, Bologna `1309357`×5, `--time=7-00:00:00`) — first attempt (`1309342`/`1309346`) failed 7/7 instantly on a separate packaging defect (absolute local path baked into `Schedule:File`, see the dedicated entry above), fixed, resubmitted, confirmed 7/7 `RC 0`/0 Fatal on Speed matching local exactly. Staged at `openubem/outputs/eu_evidence/EU-11/finding253_remedy_2026-09-05/<stem>/<stem>.idf`. *(`PLAN_eu-82pct-ceiling-2026-09-05.md` §6b/T08, 2026-09-05; `scripts/run_eu_s2_campaign.py:_assign_envelope_constructions`; director packaging + Speed submission, jobs `1309355`/`1309357`)*

- **`[OPEN]` `FINDING 254` — `CalcCoordinateTransformation: Invalid dot product` fatal (`FINDING 252`'s 4th signature, 1/24 at classification time, now 3 confirmed instances: Madrid `c71e82e57d99bed1` task `1306953_9`, Bologna `fd4b13e28f1c6f47`, Bologna `635e498716218cea` task `1305186_524`) is the SAME `intersect_match` sub-millimetre vertex-divergence family as `FINDING 210`/`D-EU-43`, but slips past the existing safety net by a distinct mechanism: a courtyard-hole refusal.** Classified by external Gemini/Antigravity session, director-audited (citations re-read directly against the live files, matched). Mechanism: `_has_near_duplicate_vertex_surfaces` sets `at_risk = True` as normal, triggering `did_reroute = _force_reroute_room_layout_to_one_zone_per_floor(...)` (`scripts/run_eu_s2_campaign.py:544`); this building (`relation/12700645`, Madrid) has a genuine courtyard void (interior ring area `>= 1.0 m²`), so `_force_reroute_room_layout_to_one_zone_per_floor` correctly refuses to collapse it into one block (`openubem/idf/surfaces.py:693-694`, by design, non-editable `D-EU-41`), and `did_reroute` returns `False`. With `mismatched` empty, the existing `D-EU-58`-era bypass (`scripts/run_eu_s2_campaign.py:573-575`) tags the zones `fallback_reason = "near_duplicate_vertex_tolerated_box"` and ships the IDF as-is rather than raising — a deliberate disclosed tolerance for courtyard buildings, not a bug in that bypass itself. The sub-mm vertex divergence it tolerates (quoted: a 1 mm-grid-snapped vertex at `(440388.567, 4478489.655)` vs an unsnapped 64-bit intersection point at `(440388.5670611691, 4478489.654910211)`, 0.1086 mm apart) is exactly `FINDING 210`'s known artifact class, but on a courtyard building EnergyPlus's own `CalcCoordinateTransformation` occasionally collapses the resulting 3-vertex sliver to 2 vertices and fatals on the degenerate dot product, instead of the `RoofCeiling` vertex-count-mismatch symptom `FINDING 210` describes. Both named instances confirmed shipped under `fallback_reason = "near_duplicate_vertex_tolerated_box"` in their district's `prepared_buildings.csv`. No fix proposed (courtyard buildings cannot be safely rerouted, by design) — this is a known-tolerance edge case of an existing accepted mechanism, expected to recur at low rate specifically on courtyard-holed buildings; no action needed unless it starts affecting a materially larger share of the fleet. **Follow-up pass (Task C, same session)** confirmed the mechanism on the Bologna instance too (courtyard void 856.02 m², sliver edge 0.315 mm, apex angle 0.0038°) and added one precision: **neither fatal surface is itself interzone** — Madrid's is `Outdoors`, Bologna's is `Ground` — so `find_mismatched_interzone_pairs` (which only inspects `Outside_Boundary_Condition == "Surface"` surfaces) structurally cannot see either one; this is a gap in that gate's scope by design, not a bug in it. *(`report.md` §Task B/C, 2026-09-05; `scripts/run_eu_s2_campaign.py:544,573-575`; `openubem/idf/surfaces.py:693-694`)*

- **`FINDING 255` — harvest-monitoring undercounted Bologna job `1305186`'s remaining task count by ~48x (tracked as "8 RUNNING + 1 PENDING", true remaining was 431)** — `squeue`/`sacct -X` display a fully-undispatched array tail as a single compressed row (`1305186_[778-1200%8]`), which every `sacct -j ... | awk '{print $2}' | sort | uniq -c` poll this session read as exactly "1 PENDING" instead of the 423 tasks it represents. Root cause: job `1305186` is dual-purposed — it is the `FINDING 249` remedy's full-Bologna-fleet re-run (`--array=1-1200%8`, `PLAN_eu-nocore-finding249-remedy-2026-09-04.md:268`), reused by the ceiling82 harvest arc as "the Bologna backlog job" without ever correcting the tracked total (673, an intermediate done-count mistaken for the array size) against the job's actual `scontrol show job`/original `sbatch` submit line. Fix: when polling any Speed array job for remaining count, cross-check `squeue -j <job>` for a compressed `_[a-b%c]` range row (each such row is `b-a+1` tasks, not 1) rather than trusting a bare `sacct -X | uniq -c` state tally; for any job also referenced by an older plan doc, verify its true array width via that plan's original `sbatch --array=` line before quoting a total. Lyon `1306952` had no such hidden tail (confirmed absent from `squeue` entirely — genuinely fully drained at 469/469). No new failure signature, FAILED counts unaffected — does not trip the ceiling82 arc's >10% hard-stop; corrected fleet total 3,947 (was 3,420). *(`DIRECTOR_PROMPT_eu82pct-ceiling-harvest_2026-09-05.md` §1, harvest-monitoring pass, 2026-09-06; `PLAN_eu-nocore-finding249-remedy-2026-09-04.md:268`)*

## European locations, dwelling-division recovery (2026-09-07)

- **`** Severe ** Schedule:File="EU_STEP8_GAINSCHEDULE_<STEM>_F0_WHOLE_F000", File Name: "../../schedules/<stem>/<stem>_F0_whole_f000_gain.csv" not found.`** — a rebuilt IDF was staged into the fleet tree but its `schedules/<stem>/` directory was not re-staged, so the directory still held the previous layout's per-dwelling schedule names (`<stem>_F0_dwelling_0_f000_gain.csv`). Hit on `cee45cbc2718154c` after the courtyard-fill rebuild changed it from 29 dwelling zones to 8 `one_zone_per_floor` zones. Fix: re-copy `EU-11/<DISTRICT>/schedules/<stem>` over the staged `EU-11/<DISTRICT>_<tag>/schedules/<stem>`, re-scp, delete `out/<stem>`, resubmit that array index. Guard: assert every `Schedule:File` path named in the IDF exists under the staged `schedules/<stem>/` before tarring, not just that the directory exists. *(docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-dwelling-division-recovery-2026-09-07.md)*
- **A district harvest reports `rc=<NA>` for the majority of its rows** — the harvest is reading a `_final_` fleet tree that only ever received the *simulate list* subset; every carried-over building has no `out/<stem>/` and so no rc. Not a staging defect. Fix: merge the delta-fleet harvest and the hash-identical ceiling82 carries into the manifest, recording the source of every row. See FINDING 265. *(docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-plan-homogeneity-2026-09-07.md)*
- **A single-task array resubmission ends `FAILED`, `ExitCode 1:0`, `Elapsed 00:00:00`, no `out/<stem>/` directory created, and its only log line is `ERROR: FLEET_DIR not set`** — `scripts/cluster/submit_fleet_t08.sbatch:21` hard-fails when `FLEET_DIR` is absent, and a resubmission of one repaired task written as `sbatch --array=54-54%32 ... submit_fleet_t08.sbatch` omitted the `--export`, so the variable the original campaign submission had supplied was gone. `sacct` shows only `FAILED`; the cause is visible solely in `/speed-scratch/o_iseri/openubem/fleets/openubem_t08_<jobid>_<task>.log`, so always read that log before re-diagnosing the IDF. Fix: resubmit as `sbatch --array=54-54%32 --time=7-00:00:00 --export=ALL,FLEET_DIR=<fleet dir> submit_fleet_t08.sbatch` (job `1311891`, `FR-LYO-HAUTCOEURPENTES_final_2026-09-07`, stem `cee45cbc2718154c`); `--export=ALL,VAR=…` rather than `--export=VAR=…` so the login environment is still inherited. *(docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-plan-homogeneity-2026-09-07.md)*
- **One task of a district `_delta_` fleet ends `FAILED` in ~3 s with `** Severe ** RoofCeiling:Detailed=... Vertex size mismatch between base surface ... and outside boundary surface` on every interzone ceiling/floor pair, then `Fatal error -- final processing. Program exited before simulations began.`** — a recurrence of `FINDING 210` on a building whose post-extrude at-risk gate tolerated the unresolved near-duplicate vertices; measured on stem `dd1d33feca834272`, task `1311699_95`, `EU11_FR-LYO-HAUTCOEURPENTES_delta_2026-09-07`. No per-building geometry remedy was applied in this pass: under `FINDING 265` the building is published as `eui_source = pending_resimulation` with every result column blank rather than carried with an EUI from a different IDF. Fix path if it must be recovered: the same forced-reroute driver used for `cee45cbc2718154c` (see the `FINDING 210` entry). *(docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-plan-homogeneity-2026-09-07.md)*
- **A SLURM array task shows `R` in `squeue` for hours with a 0-byte `eplusout.audit` *and* a 0-byte `eplusout.err`, never writes `task.rc`, and `scancel` answers `Job has already finished`** — the EnergyPlus process died or was never really started on the allocated node while SLURM still accounted the step as running; the two 0-byte files prove it never reached the audit banner, which EnergyPlus writes within seconds of start, so elapsed time is not evidence of progress. Measured on stem `5e0376cc50cbea69`, task `1311699_81`, `EU11_FR-LYO-HAUTCOEURPENTES_delta_2026-09-07`, 5 h 10 m elapsed. Diagnosis rule: a delta task with `wc -c eplusout.err` = 0 after more than ~10 minutes is dead, not slow — check the two file sizes before waiting on any straggler. Fix: no recovery attempted in this pass; under `FINDING 265` the building ships as `eui_source = pending_resimulation` with blank result columns. To recover, resubmit that single index with `sbatch --array=<n>-<n>%32 --time=7-00:00:00 --export=ALL,FLEET_DIR=<fleet dir> submit_fleet_t08.sbatch` after deleting `out/<stem>`. *(docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-plan-homogeneity-2026-09-07.md)*
- **A building coloured by a fresh EUI in `eu_<DISTRICT>_viewer.html` is drawn as `MASSING BOX (read from IDF)` with `Dwellings: 0` and one `…_F0_whole` zone per storey, although its manifest row says `geometry_outcome = DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT` and `eui_source = delta_2026-09-07`** — the viewer joined two different vintages: `_load_eu11_eui()` prefers the `_merged_2026-09-07` manifest, but the plan reader resolved every building against `EU11_ROOT / f"{district}_ceiling82_2026-09-05"` only (`scripts/generate_eu_3d_viewers.py:1068`), the superseded 2026-09-05 emission in which those buildings had no interior partition. New number, old picture. Measured on `FR-LYO-HAUTCOEURPENTES`: 173 of 507 drawn as massing boxes while only 51 of 510 IDFs in `_final_2026-09-07/idfs` and 27 of 163 in `_delta_2026-09-07/idfs` actually contain a `_F0_whole` zone. Fix: layer two more roots over ceiling82 in `build_district`, in `eui_source` precedence order `ceiling82` < `final_2026-09-07` < `delta_2026-09-07` (`scripts/generate_eu_3d_viewers.py:1075-1081`). Second symptom met on the way: `FileNotFoundError: FR-LYO-HAUTCOEURPENTES: prepared_buildings.csv names 489894ba3d990787 but …_delta_2026-09-07\idfs\489894ba3d990787.idf is missing` — a `_delta_` evidence dir carries a whole-district `prepared_buildings.csv` (509 rows) beside only the delta subset of IDFs and manifest rows (163), so `read_district` raised on the first absent stem; fixed with an opt-in `skip_missing: bool = False` on `read_district` (`scripts/eu_idf_plan_reader.py:327,346-350`) passed only by the two 2026-09-07 roots, leaving every existing caller raising as before. After the fix Lyon reads 459 ruled / 51 massing box / 20 no IDF, and the `_delta_` IDFs must be staged locally first (`scp` from `/speed-scratch/o_iseri/fleets/EU11_<D>_delta_2026-09-07/idfs`) because only the `_final_` tree is mirrored by the harvest. *(docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-dwelling-division-recovery-2026-09-07.md)*

## European locations, wall-B second pass (2026-09-08)

- **`KeyError: 'way/398158943'` reading a London vertex-bug building out of a freshly-rebuilt `_gb_rows(gdf, records)` dict, although the id is in `GB-LDN-STDUNSTANS_final_2026-09-07/prepared_buildings.csv`** — the base GB mapping pass alone (`_gb_rows`) does not cover the London population; `_final_2026-09-07` was prepared with `--recover-terrace-neighbours`, so 255 of the 706 London rows only exist after `_gb_terrace_recovery_rows(gdf, records, base_rows)` is merged on top, and one of the 7 vertex-bug ids is one of them. Fix: call `_gb_terrace_recovery_rows` (network-free, same local `GB_EPC`/`GB_EPC_CERT_CACHE` inputs as the base pass) and merge its rows onto `_gb_rows`'s before indexing by `building_id`, exactly as `prepare(..., recover_terrace_neighbours=True)` does — `scripts/eu_wallb_measure_2026_09_08.py:236-251`. *(docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-recut-95pct-2026-09-08.md, T03)*
- **A near-duplicate/collinear vertex diagnostic classifies a defect as `chord_0.010m`/`cumulative_2e-3` (i.e. "a locally-redundant vertex the removal budget refused"), but its measured `perp_dist_m` comes out at metres, not millimetres (up to ~17 m observed)** — the classifier matched the flagged 3D surface vertex back to a point at the same (x, y) on the zone's own pre-extrusion 2D ring, then blindly recomputed a chord/area removal test against that ring's immediate neighbours without first checking whether the point was actually near-duplicate or collinear on that ring at all. A vertex that only becomes a defect through cross-surface `intersect_match` pairing (FINDING 210) can coincide in (x, y) with a real, non-redundant footprint or cut-line corner; recomputing a "removal" of a genuine corner naturally produces a large area/perp-distance, not evidence of a refused budget. Fix: run the same `near_duplicate`/`collinear` local-redundancy test `_drop_redundant_ring_vertices` itself uses on the matched vertex and its ring-neighbours *before* computing a chord/area reason; if it is not locally redundant there, classify `refused_by = "not_on_ring"` instead (the removal pass never had a vertex to remove) — `scripts/eu_wallb_measure_2026_09_08.py::classify_defect` (`_is_locally_redundant` guard). Cross-checked against an independent, unaffected measurement (an actual IDF rebuild with the chord tolerance monkeypatched to 0.020 m): both agree 0 of 184 buildings would clear. *(docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-recut-95pct-2026-09-08.md, T03; FINDING 267)*
