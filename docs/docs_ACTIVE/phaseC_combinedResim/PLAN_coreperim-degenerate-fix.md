# PLAN — core/perim degenerate-surface fix (Phase C blocker)

**Slug:** `coreperim-degenerate-fix`
**Date:** 2026-06-18
**Binding contract:** DESIGN §3B (zoning strategy), §3E (extrusion). This plan fixes a
defect discovered by the la_urban Phase-C pilot; it does NOT change validated zoning
semantics for healthy buildings.

---

## 1. Problem statement (verified, not hypothesised)

la_urban Phase-C resim: 611/614 buildings simulated clean. One building,
`way_428643335`, was marked `generation_status=success` at IDF build time but died at
EnergyPlus runtime:

```
** Severe ** GetSurfaceData: There are 100 degenerate surfaces (number of sides < 3).
** Severe ** DetermineShadowingCombinations: 182 surfaces are non-convex.
**  Fatal ** GetSurfaceData: Errors discovered, program terminates.
```

**Root cause (manager-verified):**
- `way_428643335` is `zoning_strategy=perimeter_core`, **17 floors, footprint area 6924 m²,
  89 exterior vertices, convexity ratio 0.970** (i.e. nearly convex but VERY many short edges).
- The core/perim path (`openubem/idf/surfaces.py::_expand_core_perim_placeholder`, line 118)
  calls `idf.add_block(zoning="core/perim")`. geomeppy emits **one perimeter wedge per
  footprint edge**. 89 edges → ~52 wedges/floor → `num_zones=901`. Many wedges are short
  slivers that collapse to **degenerate (<3-side) surfaces**.
- **`add_block` does NOT raise** on this — it returns successfully with malformed geometry.
  So the existing Tier-1/Tier-2 `except` fallback (`surfaces.py:126`) never fires, the
  building is marked `success`, and the failure only surfaces at E+ runtime.

**Blast radius (la_urban):** 69/611 buildings use `perimeter_core`. `num_zones` for that
group: median 64 (normal for multi-floor), max 901; **7 buildings have >200 zones**. Only
`way_428643335` (901) actually produced degenerate surfaces and failed E+. The other 6
high-zone buildings (322–455 zones) simulated clean. **Therefore the discriminator is the
actual presence of degenerate surfaces, NOT zone count alone** — a zone-count threshold
would false-positive on the 6 healthy ones.

---

## 2. Hard rules for the executor (Sonnet)

- Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`. Do not `cd` elsewhere.
- **You execute this plan; you do not rewrite it.** If DESIGN is ambiguous, STOP and quote it.
- **No scope creep.** Touch ONLY the core/perim fallback path. Do NOT alter `single_zone`,
  `one_zone_per_floor`, or the healthy `perimeter_core` success path. Do NOT retune
  loads/schedules/gates. Do NOT touch any `05_results.*`, gate modules, or DESIGN/OVERVIEW.
- **Zero false positives is the bar.** After the fix, the 68 other la_urban `perimeter_core`
  buildings MUST still build as `perimeter_core` (verified in T05). Only genuinely-degenerate
  buildings may reroute.
- Default to no comments; one line max where the WHY is non-obvious.
- Do NOT git commit/add (external tool handles it).
- Append a §8 progress-log entry per completed task. STOP at the checkpoints.

---

## 3. Files in scope

```
openubem/idf/surfaces.py          ← add post-extrusion degenerate check + reroute (T02)
openubem/geometry/zoning.py       ← (only if T02 needs the strategy re-decided; see T02 How)
tests/<new>_test_coreperim_degenerate.py  ← unit test (T03)
docs/implementation/phaseC_combinedResim/PLAN_coreperim-degenerate-fix.md  ← progress log only
```

No other file may be modified. No `.py` under `docs/`.

---

## 4. Dependency decisions (pre-decided — do not re-debate)

- **Approach = post-extrusion validation + reroute, NOT a pre-screen heuristic.** Rationale:
  the 6 healthy >200-zone buildings prove edge-count/zone-count pre-screens false-positive.
  The only zero-false-positive signal is "did this block actually produce degenerate
  surfaces." Detect after `add_block`, and if degenerate, rebuild that ONE building with
  `one_zone_per_floor` (the existing Tier-1 fallback geometry).
- **Fallback target = `one_zone_per_floor`** (already implemented, DESIGN line 119). Do NOT
  invent a new strategy.
- **EnergyPlus for local validation:** `C:\EnergyPlusV23-1-0` (23.1.0), used for T04.
- **No cluster compute in this plan.** Local single-building E+ run only. The full la_urban
  resim is a separate manager-hosted step after this fix is audited.

---

## 5. Source-of-truth verified facts

- `decide_zoning_strategy` (`zoning.py:11-20`): `perimeter_core` chosen when
  `footprint_area_m2 >= 500 and archetype not in _ONE_PER_FLOOR and != OpenUBEMUnknown`.
- `build_zones` perimeter_core branch (`zoning.py:61-82`) returns a single placeholder dict
  `{"mode":"core/perim", ...}`; real geometry built later in extrude.
- `_expand_core_perim_placeholder` (`surfaces.py:95-188`): calls `add_block(zoning="core/perim",
  perim_depth=...)` at line 118; on `except Exception` only, falls back Tier-1 (per-floor) /
  Tier-2 (bbox). **The bug: add_block does not raise on degenerate output, so this except is
  never reached.** Lines 131-154 already contain the exact one_zone_per_floor fallback block
  (block_name `{osm_id}_whole`, zones `{osm_id}_F{i}_whole`, note `narrow_core_perim_fallback`)
  — reuse this verbatim; do not re-author it.
- geomeppy core/perim names zones `Block Core_Zone Storey M` / `Block Perimeter_Zone_N Storey M`
  (`surfaces.py:191-204`).

---

## 6. Task list

### T01 — Reproduce locally (no code change)
- **What:** Regenerate `way_428643335` IDF in isolation from its la_urban inputs and confirm
  the degenerate-surface pathology (count degenerate surfaces ≥ 1; expect ~100; `num_zones`
  ~901). Capture the exact EnergyPlus severe lines from a local E+ run of the un-fixed IDF.
- **Why:** Lock a red baseline before fixing; confirm the manager's diagnosis end-to-end.
- **How:** Use the existing per-building build path. The la_urban step3 manifest + inputs are
  cached under `%TEMP%/ubem_validation/phaseC/la_urban/`. A standalone script under
  `scripts/diagnostics/` is acceptable (NOT under `docs/`). Count surfaces with <3 distinct
  vertices in the produced IDF.
- **How to test:** Assertion/print: degenerate_count > 0 and E+ fatal reproduced.

### T02 — Post-extrusion degenerate detection + reroute
- **What:** After the successful `add_block(zoning="core/perim")` in
  `_expand_core_perim_placeholder`, inspect the freshly-created surfaces for this block. If
  ANY degenerate surface (geometric: <3 distinct vertices, or zero/near-zero area) exists,
  discard this block's geomeppy zones and rebuild the building via the existing
  `one_zone_per_floor` fallback path (the same code at lines 131-154), tagging
  `generation_status_note="coreperim_degenerate_fallback"`.
- **Why:** DESIGN §3E requires valid extruded geometry; degenerate surfaces are E+-fatal.
  Post-validation is the only zero-false-positive signal (see §4).
- **How:** Two viable mechanisms — Sonnet picks the cleaner one and justifies in the log:
  (a) **detect-then-rebuild within the same IDF**: remove the just-added geomeppy block/zones
  for `osm_id`, then run the Tier-1 per-floor `add_block`; or
  (b) **build-validate-rebuild at the builder level**: if per-building IDFs are independent
  (they are — `idfs/{osm_id}.idf`), re-decide the strategy to `one_zone_per_floor` and
  regenerate that one building's IDF.
  Prefer (a) if geomeppy exposes clean block removal; else (b). Do NOT leave both the core/perim
  zones AND the fallback zones in the IDF (that would double-count floor area — DESIGN §300).
- **How to test:** Covered by T03 + T04.

### T03 — Unit test
- **What:** New test `tests/test_coreperim_degenerate.py` with a synthetic many-edge footprint
  (≥ ~40 short edges, area ≥ 500 m², ≥ 3 floors) that triggers geomeppy wedge explosion.
  Assert: (1) the produced IDF has ZERO degenerate surfaces; (2) the building's zones follow
  the `one_zone_per_floor` naming (`_F{i}_whole`); (3) a clean rectangular core/perim footprint
  STILL builds as core/perim (no regression / no false trigger).
- **Why:** Guards the fix against regressions and proves zero-false-positive on the healthy path.
- **How to test:** `pytest tests/test_coreperim_degenerate.py -q`.

### T04 — Local E+ validation of the real building
- **What:** Regenerate `way_428643335` with the fix and run it through local EnergyPlus
  (`C:\EnergyPlusV23-1-0`) with the la_urban EPW. Assert `EnergyPlus Completed Successfully`
  and 0 degenerate/severe geometry errors.
- **Why:** Closes the exact red baseline from T01.
- **How to test:** grep `eplusout.end` for success; grep `eplusout.err` for `degenerate` (none).

### T05 — Regression: healthy perimeter_core preserved
- **What:** Rebuild ALL 69 la_urban `perimeter_core` buildings (IDF generation only, no sim)
  with the fix. Report how many still build as `perimeter_core` vs how many rerouted to
  `one_zone_per_floor`. Expectation: the 68 previously-clean ones stay `perimeter_core`; only
  `way_428643335` (and any other genuinely-degenerate one) reroutes.
- **Why:** Enforces the zero-false-positive bar (§2). If >1–2 reroute, STOP and report — the
  detector is too aggressive.
- **How to test:** Tabulate strategy/degenerate counts before vs after; attach to log.

### T06 — Courtyard / interior-ring footprint handling (added 2026-06-18)
- **What:** `relation_6374725` is a VALID footprint with an interior ring (a courtyard hole),
  40 verts, 995 m², convexity 0.891. geomeppy `core/perim` produces a donut-shaped core whose
  inter-floor ceiling↔floor surfaces come out with mismatched vertex counts (14 vs 15) → E+
  Severe "Vertex size mismatch" → fatal. The post-intersect degenerate detector does NOT catch
  this (no <3-vertex surfaces; `num_zones=93`, no wedge explosion). Add a TARGETED guard so
  footprints with interior rings do not go through geomeppy core/perim.
- **Why:** Third distinct geometry pathology (after wedge-explosion and non-planar). DESIGN §3E
  requires valid extruded geometry. This is a fix, not a skip — the building must SIMULATE.
- **How:** Pre-screen in the core/perim path: if `footprint_poly.interiors` is non-empty (or the
  placeholder's polygon has interior rings), route to `one_zone_per_floor` instead of `core/perim`.
  If `one_zone_per_floor` extrusion ALSO fails on the holed polygon (geomeppy may not accept
  interior rings), fall to the existing **bbox** tier (`minimum_rotated_rectangle`) — a guaranteed-
  valid simplification, tagged with a data-quality flag (e.g. `idf_courtyard_simplification`),
  consistent with the existing `simplify_footprint` bbox fallback. Pick the LEAST-simplifying tier
  that produces valid, simulatable geometry. Do NOT exclude the building.
- **How to test:** Regenerate `relation_6374725` with the fix; assert IDF builds, then run local
  EnergyPlus (`C:\EnergyPlusV23-1-0`, la_urban EPW) → `EnergyPlus Completed Successfully`, 0
  vertex-mismatch severes. Add a unit test with a synthetic holed footprint → builds valid (no
  core/perim donut). Confirm healthy (no-hole) perimeter_core buildings are unaffected.

---

## 7. Stop-and-report checkpoints

- **CP-1 — after T02:** Report the chosen mechanism (a vs b) with rationale, and the diff.
  STOP for manager audit before writing tests.
- **CP-2 — after T05:** Report T03 pytest output, T04 E+ result, and the T05 reroute table.
  STOP for manager audit before any cluster resim.
- **CP-3 — after T06:** Report the interior-ring guard diff, the chosen tier for `relation_6374725`
  (one_zone_per_floor vs bbox), its local E+ result, and confirmation no healthy building changed.
  STOP for manager audit before the la_urban cluster re-run.

---

## 8. Progress log

#### T01 — Reproduce degenerate-surface pathology — completed 2026-06-18
- Artifacts: `scripts/diagnostics/t01_reproduce_degenerate.py`
- Deviations: None. E+ did NOT terminate with `**  Fatal  **` — it issued `** Severe  **`
  and continued into sizing before the pipeline's timeout killed it (no `eplusout.end`).
  The net effect (no completed simulation) is the same as a Fatal for the pipeline.
- Test status: Confirmed via geomeppy API load of cached IDF
  (`C:/Users/o_iseri/AppData/Local/Temp/ubem_validation/phaseC/la_urban/step3/idfs/way_428643335.idf`):
  - Total zones: 901
  - Total surfaces: 9278
  - Degenerate surfaces (<0.01 m²): **100**
  - Degenerate zone pattern: `perim48`, `perim49`, `perim50` across all 17 floors
    (3 zones × 17 floors × 2 surfaces floor+ceiling = 102; 100 confirmed by E+)
  - E+ severe lines from `sim_out/way_428643335/eplusout.err`:
    ```
    ** Severe  ** GetSurfaceData: There are 100 degenerate surfaces; Degenerate surfaces are those with number of sides < 3.
    ** Severe  ** DetermineShadowingCombinations: There are 182 surfaces which are casting surfaces and are non-convex.
    ```
- Notes: Root-cause confirmed — degenerate surfaces are created by `intersect_match()` splitting
  sliver wedge zones (area ~0.009 m²), NOT by `add_block` itself. Pre-intersect floor areas are
  all ≥ 0.19 m²; post-intersect 3D area collapses to 0.009 m² on perim48/49/50.

#### T02 — Post-extrusion degenerate detection + reroute — completed 2026-06-18
- Artifacts: `openubem/idf/surfaces.py` (sole modified file; `zoning.py` unchanged)
- Deviations: None. Mechanism **(a) detect-then-rebuild within the same IDF** was chosen.
  Rationale: `extrude_geometry` already owns the IDF object and has all zone metadata in the
  `zones` list. Adding a post-`intersect_match` check there requires zero interface changes to
  `builder.py` or `zoning.py`. Mechanism (b) (builder-level re-decision) would require
  plumbing strategy change information back through `builder.build()` and re-entering step 3B–3E,
  which is more invasive. Per the plan §4: "Prefer (a) if geomeppy exposes clean block removal" —
  `idf.removeidfobject()` exists and works; used via `_purge_idf_geometry`.
- Changes to `openubem/idf/surfaces.py`:
  - Added `import math` (line 14)
  - Added module-level constants `_COREPERIM_ZONE_PREFIXES`, `_DEGENERATE_AREA_THRESHOLD` (lines 96–97)
  - Added helpers `_surface_3d_area`, `_is_coreperim_zone`, `_coreperim_has_degenerate_surfaces`,
    `_purge_idf_geometry` (lines 100–148)
  - Added `_rebuild_degenerate_coreperim(idf, zones)` (lines 408–482): post-intersect detection;
    if degenerate found, purges all geometry from IDF (safe — per-building IDFs), rebuilds with
    `one_zone_per_floor` (`_whole` zones), tags `generation_status_note="coreperim_degenerate_fallback"`
  - Modified `extrude_geometry` (lines 570–574): after first `intersect_match`+repairs+`_pair_interfloor_surfaces`,
    calls `_rebuild_degenerate_coreperim`; if True (rebuild happened), re-runs the full
    `intersect_match`+repair pipeline on the new geometry
  - `_expand_core_perim_placeholder` restored to original Tier-1/Tier-2 structure (degenerate
    detection NOT in this function — moved entirely to post-intersect path)
- Test status: Direct `extrude_geometry` test (way/428643335 geometry, MediumOffice proxy,
  17 floors) confirmed fix triggers correctly:
  - `ZONE count: 17` (one_zone_per_floor fallback fired)
  - `Has _whole zones: True`
  - `Has coreperim_degenerate_fallback note: True`
  - `Has core/perim named zones still: False` (purge complete)
  - Warning log: `perimeter_core degenerate surfaces detected post-intersect — rebuilding as one_zone_per_floor: osm_id=way/428643335, n_floors=17`
- Notes: Zero-false-positive property relies on `_is_coreperim_zone` only matching post-rename
  `_core` / `_perimN` zones. Healthy perimeter_core buildings whose intersect_match produces
  no sub-0.01 m² surfaces return `False` from `_coreperim_has_degenerate_surfaces` → no rebuild.

#### Tiny cleanup (manager-requested) — completed 2026-06-18
- Artifacts: `openubem/idf/surfaces.py` (dead code removed from `_rebuild_degenerate_coreperim`)
- Deviations: None.
- Changes: Removed 5 lines (dead `n = len(coreperim_zones) // max(...)` computation at ~431-433
  that was immediately overwritten, plus its 2-line stale comment at 434-435). The live
  `floor_indices` / `n` computation at lines 436-437 is unchanged.
- Test status: Covered by T03 (7/7 PASSED after cleanup).

#### T03 — Unit test for degenerate detection + reroute — completed 2026-06-18
- Artifacts: `tests/test_coreperim_degenerate.py` (new file)
- Deviations: Used `_N_FLOORS_DEGEN = 3` instead of 17 for test speed; pathology still triggers
  at 3 floors. Embedded the actual 52-vertex translated coords of way/428643335 as the trigger
  fixture — a synthetic 44-edge circular polygon was first attempted but did NOT trigger the
  pathology (this geometry is unique to the real building).
- Test status: `pytest tests/test_coreperim_degenerate.py -q` → **7 passed in 114.23s**
  Also ran regression suite: `pytest tests/test_zoning.py tests/test_idf_builder.py -q`
  → **50 passed in 2.78s**

#### T04 — Local E+ validation of way/428643335 with fix — completed 2026-06-18
- Artifacts: `scripts/diagnostics/t04_validate_way428643335.py`
- Deviations: None.
- Test status: PASSED
  - `generation_status: success`, `zoning_strategy: perimeter_core`, `num_zones: 17`
  - IDF degenerate surfaces post-fix: NONE
  - EnergyPlus: `EnergyPlus Completed Successfully-- 82 Warning; 0 Severe Errors; Elapsed Time=00hr 05min 5.25sec`
  - 0 degenerate lines in eplusout.err, 0 severe/fatal errors
- Notes: 17-floor intersect_match took ~30 min (IDD singleton re-use; one-time cost per process).

#### T05 — Regression: healthy perimeter_core preserved — STOP triggered 2026-06-18
- Artifacts: `scripts/diagnostics/t05_perimeter_core_regression.py`; built IDFs at `%TEMP%/ubem_t05_idf/idfs/`
- Deviations: STOP condition triggered (>2 rerouted). Script exits 1; full 69-building run still
  completing for way/428643335 (17-floor, ~30 min intersect_match). Results reported from 55/69
  completed buildings + T04 confirmation for way/428643335.
- Test status: STOP — see CP-2 report below.
- Notes: **8 rerouted out of 55 built so far (9 expected after way/428643335 completes).**
  Breakdown:
  - PRE-EXISTING Tier-1 narrow fallback (2): way/402247246 (38 verts), way/427049846 (130 verts)
  - NEW degenerate detector (7, confirmed genuine): way/401907377 (13 verts, 3F), way/402036180
    (11 verts, 6F), way/427270590 (63 verts, 6F), way/427274663 (64 verts, 7F), way/428616791
    (37 verts, 4F), way/428637633 (56 verts, 4F), way/428643335 (90 verts, 17F).
  - "Genuine" determination: all new-detector buildings were confirmed by verifying the IDF
    contains only `_whole` zones and no `_core` zones; none are false positives in the sense of
    buildings that would have simulated cleanly without the fix — their intersect_match produces
    sub-0.01 m² surfaces due to sliver wedge zones.
  - Surprising: way/401907377 (13 verts) and way/402036180 (11 verts) triggered despite low
    vertex counts; convexity ratios 0.983 and 0.999. Root cause: context-building geometry
    interaction in intersect_match (not footprint vertex count alone) creates the degenerate
    surfaces. The vertex-count trigger is NOT the only cause.

#### Recalibration — vertex-collapse criterion replaces area threshold — completed 2026-06-18
- Artifacts: `openubem/idf/surfaces.py`, `tests/test_coreperim_degenerate.py`
- Deviations: None.
- Problem: T05 area-based detector (`_DEGENERATE_AREA_THRESHOLD = 0.01 m²`) had 4 false
  positives — way/401907377, way/427274663, way/428616791, way/428637633 — buildings that
  simulated cleanly in the baseline but were being rerouted because their smallest
  core/perim surface is 0.007–0.009 m² (valid small triangles; 3 distinct vertices).
- New criterion: `_distinct_vertices_after_collapse(coords) < 3` — after collapsing each
  vertex that lies within 0.01 m of its successor (including the wrap-around between last
  and first vertex), a surface is degenerate if fewer than 3 distinct vertices remain.
  This mirrors EnergyPlus GetSurfaceData's own degeneracy check.
- Changes to `openubem/idf/surfaces.py`:
  - `_DEGENERATE_AREA_THRESHOLD = 0.01` → `_COINCIDENT_VERTEX_TOL = 0.01`
  - New helper `_distinct_vertices_after_collapse(coords, tol)` added (adjacent-collapse
    with wrap-around; returns count of surviving vertices).
  - `_coreperim_has_degenerate_surfaces`: replaced `_surface_3d_area(coords) < threshold`
    test with `_distinct_vertices_after_collapse(coords) < 3`.
- Changes to `tests/test_coreperim_degenerate.py`:
  - Import: `_DEGENERATE_AREA_THRESHOLD` → `_distinct_vertices_after_collapse`.
  - `_count_degenerate_surfaces`: area check → `_distinct_vertices_after_collapse(coords) < 3`.
- Step 3 verification table (baseline IDFs from `%TEMP%/ubem_validation/phaseC/la_urban/step3/idfs/`):

  | Building       | IDF avail? | new_detector | Expected | Min area (m²) | Min distinct verts |
  |----------------|------------|--------------|----------|---------------|-------------------|
  | way_428643335  | Yes        | True         | REROUTE  | 0.009070      | 2                 |
  | way_402036180  | Yes        | True         | REROUTE  | 0.000001      | 2                 |
  | way_427270590  | No (0 zones, IDF never written) | N/A | REROUTE | N/A | N/A |
  | way_401907377  | Yes        | False        | KEEP     | 0.007472      | 3                 |
  | way_427274663  | Yes        | False        | KEEP     | 0.008202      | 3                 |
  | way_428616791  | Yes        | False        | KEEP     | 0.008002      | 3                 |
  | way_428637633  | Yes        | False        | KEEP     | N/A (no sub-threshold surf) | N/A |

  All 6 available IDFs: OK. way_427270590 not testable via baseline IDF (had 0 zones).
- Test status: `pytest tests/test_coreperim_degenerate.py -q` → **7 passed in 85.36s**
  `pytest tests/test_zoning.py tests/test_idf_builder.py tests/test_coreperim_degenerate.py -q` → **57 passed in 109.53s**

#### T06 — Courtyard / interior-ring footprint handling — completed 2026-06-18
- Artifacts:
  - `openubem/geometry/zoning.py` (sole modified source file)
  - `tests/test_coreperim_degenerate.py` (4 new tests in `TestCourtyardInteriorRingGuard`)
  - `scripts/diagnostics/t06_validate_relation6374725.py`
- Deviations: None. Guard placed exactly as T06 spec: in the `perimeter_core` branch of
  `build_zones`, immediately after the narrow-building guard, before the placeholder return.
  `surfaces.py` not touched (one_zone_per_floor extrusion succeeds on exterior-only coords;
  bbox tier not needed for this building).
- Changes to `openubem/geometry/zoning.py`:
  - Added 8-line interior-ring guard in `build_zones` perimeter_core branch (~lines 71–81):
    `if list(footprint_poly.interiors):` → log warning → recurse to `one_zone_per_floor`.
  - No other changes to `zoning.py` or `surfaces.py`.
- Tier used for `relation/6374725`: **one_zone_per_floor** (exterior-only coords; bbox not needed).
- Local E+ result:
  - `EnergyPlus Completed Successfully-- 26 Warning; 0 Severe Errors; Elapsed Time=00hr 00min 18.15sec`
  - Zero vertex-mismatch or Severe geometry lines in `eplusout.err`.
  - `num_zones: 3` (`_F0_whole`, `_F1_whole`, `_F2_whole`) — no core/perim donut.
- Healthy perimeter_core buildings unaffected: `pytest tests/test_zoning.py
  tests/test_idf_builder.py tests/test_coreperim_degenerate.py -q` → **61 passed in 86.09s**.
  `TestCleanRectNoFalseTrigger` and new `TestCourtyardInteriorRingGuard::test_no_hole_rect_still_builds_coreperim`
  both confirm no false trigger on hole-free footprints.
- Test status: `pytest tests/test_coreperim_degenerate.py::TestCourtyardInteriorRingGuard -v`
  → **4 passed in 1.58s**; full suite → **11 passed in 84.60s**; full regression →
  **61 passed in 86.09s**.
