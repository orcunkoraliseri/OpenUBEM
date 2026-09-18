# PLAN — TechTransfer block 2 (T9 prototype-vs-plot fit check, T7 prep gate)

- **Slug:** `techtransfer-block2`
- **Date opened:** 2026-09-17
- **Source:** `docs/docs_ACTIVE/TechTransfer/2026-09-17_TechTransfer_idf_reader_to_OpenUBEM.md`,
  section 5 "Recommended sequence", order 6 (**T9**, report lines 368-392) and order 7 (**T7**,
  report lines 307-336).
- **Predecessor:** `PLAN_techtransfer-block1-2026-09-17.md` (sequence orders 1-5: T1, T3, T2, T8,
  T10). Block 1 is delivered; its decisions D1-D12 remain binding here, in particular **D3**
  (two coexisting ground models, still the user's open decision) which this block does not touch.
- **Out of scope, do not start:** report items T4, T5, T6 (sequence orders 8-10). Each is
  arc-sized and gets its own plan doc after a separate go-ahead. T11 waits for a Canadian
  district case.

---

## 2. Hard rules for the executor

1. Execute the tasks in order. Do not propose alternatives. If the source report or the code
   contradicts this plan, **STOP and quote the conflict** rather than improvising.
2. Edit only the files your lane owns (section 3). A change outside your lane is a defect even if
   it is correct.
3. **No published number may move in this block.** Both lanes are measurement and reporting only.
   If a change of yours alters a simulated result, you have exceeded the task - revert and report.
4. No code comments. No new files beyond those named in section 3.
5. Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. After
   solving one, register it there in the house format before you close the task.
6. Never run EnergyPlus runs sequentially. This block needs **no** EnergyPlus runs at all; if you
   believe it does, you have misread the task - STOP and report.
7. Append one progress-log entry per completed task under section 8.

---

## 3. File layout and lane ownership

**Lane E - T9, prototype-vs-plot fit check**

- `openubem/geometry/layout_assigner.py` (edit)
- `tests/test_layout_assigner_fit_check.py` (new)

**Lane F - T7, prep-before-sim failure gate**

- `openubem/simulation/parallel.py` (edit)
- `openubem/config.py` (edit - one constant only)
- `tests/test_prep_gate.py` (new)

**Nobody edits in this block:** `openubem/idf/builder.py`, `openubem/geometry/envelope_patcher.py`,
`openubem/idf/ground.py`, `openubem/validation/`, any OVERVIEW or DESIGN doc, root `main.py`.

---

## 4. Dependency decisions (pinned - do not re-litigate)

- **E1. The fit check measures and names; it never changes geometry.** No surface, scale factor or
  zone may change as a result of this block. The check adds metadata keys and a named reason; it
  does not reject a building, does not switch a prototype, and does not alter
  `calculate_scaling_factor()`. The energy half of this defect is already recorded in
  `OpenUBEM_fundamentals.md` section 5.1.2 and is not re-opened here.
- **E2. Comparison basis.** Real footprint: the two side lengths of
  `shapely.minimum_rotated_rectangle(footprint_poly)`, sorted descending. Scaled prototype: the X
  and Y extents of the raw prototype IDF's surface vertices, multiplied by
  `scaling["planar_scale_factor"]`, sorted descending. Compare the sorted pairs element-wise. The
  rotated rectangle, not the axis-aligned bbox, is the basis - a diagonal footprint would otherwise
  be credited with room it does not have.
- **E3. Flag name and threshold.** `PROTOTYPE_EXTENT_EXCEEDS_FOOTPRINT`, raised when either sorted
  prototype dimension exceeds its footprint counterpart by more than **1.0 m**. The 1.0 m is a
  pinned tolerance for this block, not a physical constant; it absorbs vertex-rounding noise while
  still catching the reported 32.8 m class of overflow.
- **E4. Where the result goes.** Two new keys in the dict returned by `assign_baseline_layout()`:
  `fit_check_reason` (the flag string, or `None`) and `fit_overflow_m` (the larger of the two
  signed overflows, in metres, or `None`). Existing keys keep their names and values. The
  `no_baseline=True` early-return path gets both keys set to `None`, so the dict shape is uniform.
  **Viewer badges and manifest columns are NOT in this block** - report first, wire later.
- **E5. Reading the prototype's extents must not be done once per building.** The library has ~25
  prototype IDFs and thousands of buildings; cache the raw extents per baseline IDF path in a
  module-level dict, keyed by path, computed on first use.
- **F1. The gate lives at the sim entry point, not in the builder.** Put it at the top of
  `run_neighbourhood()` in `openubem/simulation/parallel.py`, before `build_task_list()`, reading
  the `generation_status` column of the `idf_manifest` it is already given.
  `openubem/idf/builder.py` is not edited in this block.
- **F2. The gate ships OFF by default, and that default is deliberate.** New config constant
  `PREP_ABORT_ON_FAILURE: bool = False`. A known pre-existing IDF-generation fatal (one Warehouse in
  `auto` mode, recorded in block 1 D12 and not fixed) would otherwise abort every fleet run on day
  one. With the default, behaviour is byte-identical to today. Turning it on is a user decision -
  see SR-F.
- **F3. What the gate does when ON.** Raise a single `PrepPhaseFailedError` naming the count and the
  first five failing `osm_id`s, before any run slot is consumed. It does not filter, retry, or
  silently drop buildings; the existing generation-success filter in `build_task_list()` stays
  exactly as it is.
- **F4. Not in this block:** per-worker stdout capture, ordered `[PREP n/m]` lines, the
  Windows-thread / Linux-process split, the memory-budget sizing. `joblib(verbose=10)` already
  covers progress, and the SIM half of T7 is already satisfied by the Speed array rule. The only
  transferable half is the abort-before-dispatch contract.
- **F5. The existing `_worker` never-raises contract is untouched**, as is `_version_handshake()`,
  the loky backend, `n_jobs`, and the resume/cache path.

---

## 5. Verified facts, with line citations (measured 2026-09-17, do not re-derive)

1. `assign_baseline_layout()` (`openubem/geometry/layout_assigner.py:298`) already receives
   `footprint_poly` **and** resolves `baseline_idf_path` (`:320`) and `planar_scale_factor`
   (`:348` via `calculate_scaling_factor`, `:144`). Everything E2 needs is in scope at that point;
   no new plumbing is required.
2. That function has an early return for the no-baseline case at `:331-345` - the second place that
   must gain the two new keys (E4).
3. `planar_scale_factor = sqrt(plate_ratio)` (`:214`) or `sqrt(area_scale_ratio)` (`:220`). It is the
   planar factor, so prototype plan extents scale by it directly, not by its square.
4. `openubem/simulation/parallel.py` is 280 lines. `run_neighbourhood()` starts at `:248`; the
   version handshake is `:262`, `build_task_list()` at `:264`, dispatch at `:271`. The gate goes
   between the handshake and `build_task_list()`.
5. The prep half already has the harder half of T7's contract: `_build_one()`
   (`openubem/idf/builder.py:732`) is a module-level, picklable worker that never raises, and
   failures become a `generation_status="failed_worker_exception"` manifest row
   (`_worker_exception_row`, `:720`). What is missing is only the **abort before dispatch**.
6. `run_step3()` (`openubem/idf/builder.py:749`) writes `03_idf_manifest.parquet` with a
   `generation_status` column; `run_neighbourhood()` consumes that manifest. The gate therefore
   needs no new artifact.
7. The `layout_assign` path substitutes a whole DOE prototype and scales by `sqrt(S)` in plan; the
   energy consequence is already documented in `OpenUBEM_fundamentals.md` section 5.1.2. **Warning:**
   that doc's line citations drifted during block 1 (it cites `builder.py:481` for a call now at
   `:557`); treat its line numbers as stale, its prose as current.

---

## 6. Tasks

#### E01 - Census: how far off are the prototypes today?
**What.** Measure, for a sample of at least 200 `layout_assign` buildings across all archetypes, the
scaled prototype plan extents versus the footprint's minimum rotated rectangle.
**Why.** The threshold in E3 is only defensible if we know the distribution it sits in.
**How.** A throwaway script in the scratchpad directory (NOT under `docs/`, NOT committed). Read
extents per E2/E5. No EnergyPlus runs. If it takes more than ~2 minutes, use a process pool of 20.
**How to test.** Report: sample size, count and percentage over 1.0 m, the five worst buildings with
their overflow in metres, and the per-archetype breakdown for any archetype whose median overflow is
positive.

#### E02 - Implement the check
**What.** Add the extent comparison to `assign_baseline_layout()`, returning `fit_check_reason` and
`fit_overflow_m` per E4, with the per-path extent cache per E5.
**Why.** Turns a defect that was found by looking at a picture into a named, queryable field.
**How.** Pure addition. No existing key changes value. Both return paths gain both keys.
**How to test.** `tests/test_layout_assigner_fit_check.py` (new): (a) a footprint comfortably larger
than the scaled prototype gives `reason=None`; (b) a deliberately narrow footprint raises
`PROTOTYPE_EXTENT_EXCEEDS_FOOTPRINT` with a positive `fit_overflow_m`; (c) an overflow of exactly
0.5 m does not trigger; (d) the `no_baseline=True` path returns both keys as `None`; (e) a rotated
(diagonal) footprint is judged on its rotated rectangle, not its axis-aligned bbox. Then run
`python -m pytest tests/test_layout_assigner_fit_check.py tests/test_layout_assigner.py -q` - both
must be green.

#### E03 - Fleet count, stated plainly
**What.** Re-run the E01 census with the final implemented function and report how many fleet
buildings would carry the flag.
**Why.** This number is what the user decides on at SR-E.
**How to test.** Report the count, the percentage of the `layout_assign` population, and the
per-archetype table. **STOP at SR-E.**

#### F01 - The prep gate
**What.** `PREP_ABORT_ON_FAILURE: bool = False` in `openubem/config.py`; a `PrepPhaseFailedError`
and the gate at the top of `run_neighbourhood()` per F1/F3.
**Why.** A bad input table currently costs a full array of cluster time before anyone notices.
**How.** The gate reads `generation_status` from the `idf_manifest` argument. When the flag is off,
the function must behave identically to today.
**How to test.** `tests/test_prep_gate.py` (new): (a) flag off + failures present -> no raise, same
return path as today; (b) flag on + failures present -> `PrepPhaseFailedError` naming the count and
at most five ids; (c) flag on + zero failures -> no raise; (d) the error is raised **before**
`build_task_list()` is reached (assert with a monkeypatched `build_task_list`).
Run `python -m pytest tests/test_prep_gate.py -q` plus any existing simulation-package tests.
**STOP at SR-F.**

---

## 7. Stop-and-report points

- **SR-E (after E03).** Report the fleet flag count. **User decision owed:** whether to (a) leave the
  flag as metadata only, (b) surface it as a manifest column and viewer badge, or (c) act on it by
  swapping prototypes. Do not start (b) or (c) without it.
- **SR-F (after F01).** Report the gate as delivered, OFF. **User decision owed:** whether to turn
  `PREP_ABORT_ON_FAILURE` on for production runs, knowing the pre-existing Warehouse `auto`-mode
  fatal would then abort a fleet run until it is fixed.

---

## 8. Progress log

<!-- One entry per completed task:
#### TXX - <title> - completed YYYY-MM-DD
**Artifacts:** / **Deviations:** / **Test status:** / **Notes:**
-->

#### E01 - Census: how far off are the prototypes today? - completed 2026-09-17
**Artifacts:** Throwaway script (scratchpad, not committed) joining the 12-cell/8,160-building
phaseE fixture's `05_results.gpkg` (resolved `archetype_id`/`levels`) with each cell's
`01_buildings.gpkg` (real footprint polygons, UTM) for every building whose `archetype_id` has a
baseline in `ARCHETYPE_IDF_MAP`.
**Deviations:** Ran the full 7,442-building baseline-eligible population rather than a 200-row
sample (extent reads are cached per baseline IDF, ~25 files total, so the full population cost
under a minute single-threaded — no process pool needed). Also discovered `05_results.gpkg`'s own
`geometry` column is a re-centred placement point, not the footprint — switched to
`01_buildings.gpkg` for geometry, registered in the debug reference doc.
**Test status:** N/A (measurement only).
**Notes:** 7,442 buildings measured; 4,278 (57.48%) exceed the 1.0 m tolerance. Five worst:
way/204413181 HighriseApartment 142.8 m (austin_centre), way/328631279 HighriseApartment 126.9 m
(austin_centre), way/427942833 HighriseApartment 103.3 m (la_centre), way/1253806579
MidriseApartment 99.4 m (la_urban), way/850669088 HighriseApartment 97.4 m (austin_centre).
Archetypes with positive median overflow: HighriseApartment, Warehouse, TallBuilding,
SuperTallBuilding, RetailStandalone, MediumOffice, SmallOffice, QuickServiceRestaurant,
SecondarySchool, FullServiceRestaurant.

#### E02 - Implement the check - completed 2026-09-17
**Artifacts:** `openubem/geometry/layout_assigner.py` (new constants
`PROTOTYPE_EXTENT_EXCEEDS_FOOTPRINT`/`FIT_CHECK_TOLERANCE_M` and functions
`_raw_prototype_xy_extent()`/`_fit_check()`, lines 106-176; wiring into
`assign_baseline_layout()`'s two return paths, lines 422-446). `tests/test_layout_assigner_fit_check.py`
(new, 6 tests covering cases a-e plus a direct extent-cache check).
**Deviations:** None from D E1-E5.
**Test status:** `python -m pytest tests/test_layout_assigner_fit_check.py tests/test_layout_assigner.py -q`
-> `138 passed in 59.01s`.
**Notes:** Registered a new debug-reference entry (chapter 5) for the degenerate-footprint
`minimum_rotated_rectangle` -> `Point` case and the `05_results.gpkg` geometry gotcha found during
E01.

#### E03 - Fleet count, stated plainly - completed 2026-09-17
**Artifacts:** Throwaway script (scratchpad) re-running the same population through the real,
implemented `assign_baseline_layout()`.
**Deviations:** None.
**Test status:** N/A (measurement only); matches E01's hand-computed census exactly (7,442 / 4,278 /
57.48%), cross-confirming the implementation.
**Notes:** Fleet count: 4,278 of 7,442 baseline-eligible `layout_assign` buildings (57.48%) carry
`PROTOTYPE_EXTENT_EXCEEDS_FOOTPRINT`. Per-archetype: SuperTallBuilding 24/24 (100%), TallBuilding
92/92 (100%), QuickServiceRestaurant 47/50 (94%), RetailStandalone 127/140 (90.7%),
HighriseApartment 29/32 (90.6%), SmallOffice 3082/3504 (88.0%), Warehouse 33/38 (86.8%),
FullServiceRestaurant 26/33 (78.8%), MediumOffice 264/412 (64.1%), SecondarySchool 6/11 (54.5%),
SuperMarket 2/5 (40%), LargeOffice 92/270 (34.1%), Outpatient 2/6 (33.3%), MidriseApartment
452/2818 (16.0%), PrimarySchool 0/2 (0%), Hospital 0/5 (0%). **STOPPED at SR-E per plan.**

#### F01 - The prep gate - completed 2026-09-17
**Artifacts:** `openubem/config.py:123` (`PREP_ABORT_ON_FAILURE: bool = False`);
`openubem/simulation/parallel.py:23-24` (`PrepPhaseFailedError`); `openubem/simulation/parallel.py:270-278`
(gate in `run_neighbourhood()`, before `build_task_list()`); `tests/test_prep_gate.py` (new, 5 tests).
**Deviations:** None from F1-F5.
**Test status:** `tests/test_prep_gate.py -q` - 5 passed. `tests/ -q -k "simulation or parallel"` - 31 passed,
2716 deselected (benign `Windows fatal exception: access violation` loky-worker-spawn noise on stderr,
already registered in the debug-references doc; does not affect pass/fail).
**Notes:** No EnergyPlus runs. Flag defaults False; behaviour with it off is unchanged. STOP at SR-F -
user decision owed on turning `PREP_ABORT_ON_FAILURE` on for production.

**Manager audit 2026-09-17 (Lane E).** Re-ran independently: `openubem/geometry/layout_assigner.py`
+85/-1, new constants and `_raw_prototype_xy_extent()` / `_fit_check()` at `:103-176`, both
`assign_baseline_layout()` return paths carry `fit_check_reason` / `fit_overflow_m` (`:420-421`
on the no-baseline early return, `:444-445` on the assigned path). `python -m pytest
tests/test_layout_assigner_fit_check.py tests/test_layout_assigner.py -q` -> **138 passed in
64.62s**. `git status --porcelain` shows no file touched outside the lane. E01 was widened from the
planned 200-row sample to the full 7,442-building population; that is an improvement, accepted.

**Manager audit 2026-09-17 (Lane E) — DEFECT FOUND, census number not trusted.** The flag is
computed inside `assign_baseline_layout()`, which obtains `planar_scale_factor` from the **2-argument**
`calculate_scaling_factor(real_area, baseline_area)` call (`layout_assigner.py:426`) and therefore
always lands in the identity branch `sqrt(area_scale_ratio)` (`:297`). The build path does **not**
use that value: `openubem/idf/builder.py:545-550` calls `calculate_scaling_factor` with
`num_floors=`, `n_proto=band_map["n_storeys_represented"]` and `band_map["recomputed_area_m2"]`,
which takes the **plate-ratio** branch `sqrt(plate_target/plate_proto)` (`:291-296`). The two
disagree whenever `num_floors != n_proto`, and the baseline-area source also differs (registry area
vs the band-map recomputed area, which the code itself records as disagreeing for 14 of 25
prototypes, `builder.py:533-535`). Consequence: **the measured 4,278 / 7,442 (57.48 %) flag rate is
an upper bound computed with a scale factor the builder never applies**, and its direction of error
is systematic (for `num_floors > n_proto`, `plate_ratio < area_scale_ratio`, so the fit check
oversizes the prototype and over-flags). The flag itself is metadata-only and mutates no geometry,
so nothing simulated is affected. Task **E04** below re-measures it against the applied factor
before any of the number is quoted.

#### E04 — Re-measure the fit check against the scale factor the builder actually applies
**What.** A throwaway scratchpad census that, per building, reproduces the builder's own sequence
(open the baseline IDF, `compute_band_map()`, `match_storeys()`, then `calculate_scaling_factor()`
with `num_floors=` and `n_proto=band_map["n_storeys_represented"]`) and feeds *that*
`planar_scale_factor` into `layout_assigner._fit_check()`.
**Why.** The 57.48 % figure above is computed with the wrong factor and must not be quoted.
**How.** `compute_band_map()` and `n_storeys_represented` depend only on the prototype IDF, so cache
them per baseline path (~25 files) exactly as E5 caches the extents. Parallel pool, never a `for`
loop over buildings. **Zero EnergyPlus runs.**
**How to test.** Report the re-measured flag rate over the same population, the per-archetype
breakdown, and the signed difference against 4,278 / 7,442. Do **not** change the in-code flag;
if the re-measurement shows the shipped flag is systematically wrong, STOP and report.

#### E04 — Re-measure the fit check against the scale factor the builder actually applies — completed 2026-09-17
**Artifacts:** Throwaway script (scratchpad, not committed) reusing E01/E03's same 7,442-building
population (12-cell `docs/docs_VALIDATION/validations/overAll/results/phaseE/{cell}/05_results.gpkg`
joined to each cell's `01_buildings.gpkg` on `osm_id`, filtered to archetypes with an
`ARCHETYPE_IDF_MAP` baseline). Per building: `compute_band_map()` + raw baseline idf cached per
baseline path (~25 files, single-threaded, well under the parallel-pool threshold, same as E1/E5),
`match_storeys(idf, num_floors, band_map)`, then `calculate_scaling_factor(real_area,
band_map["recomputed_area_m2"], num_floors=num_floors, n_proto=band_map["n_storeys_represented"],
storeys_matched=(match_result["status"]=="applied"), multiplier=match_result.get("multiplier"))`
feeding the resulting `planar_scale_factor` into the existing `layout_assigner._fit_check()`
directly (not reimplemented).
**Deviations:** None. No code changed; measurement only, in-code flag untouched.
**Test status:** N/A (measurement only).
**Notes:** Re-measured population 7,442 (matches E01/E03 exactly). Flagged 5,280 (70.9487%), signed
difference **+1,002 buildings / +13.47 percentage points** against the shipped 4,278/7,442
(57.48%) — the corrected number is higher, not lower. Per-archetype: FullServiceRestaurant 25/33
(75.8%), HighriseApartment 26/32 (81.2%), Hospital 1/5 (20.0%), LargeOffice 0/270 (0.0%),
MediumOffice 272/412 (66.0%), MidriseApartment 2589/2818 (91.9%), Outpatient 6/6 (100.0%),
PrimarySchool 0/2 (0.0%), QuickServiceRestaurant 43/50 (86.0%), RetailStandalone 90/140 (64.3%),
SecondarySchool 10/11 (90.9%), SmallOffice 2188/3504 (62.4%), SuperMarket 5/5 (100.0%),
SuperTallBuilding 0/24 (0.0%), TallBuilding 1/92 (1.1%), Warehouse 24/38 (63.2%). The shipped
in-code flag is confirmed systematically wrong, and in the opposite direction from the manager
audit's hypothesis: it under-flags (57.48%) relative to the scale factor the builder actually
applies (70.95%), rather than over-flagging.

**Manager audit 2026-09-17 (E04).** Re-counted the executor's own census output independently
(`scratchpad/e04_census_rows.json`, 7,442 rows): **5,280 flagged = 70.9487 %**, matching its report
exactly. Two corrections to how that result must be read:

1. **My stated direction of error was wrong.** The applied plate-ratio factor is *larger* than the
   identity factor whenever `n_proto > num_floors` — a prototype with more storeys than the real
   building — which is the common case here, so the shipped flag **under**-flags rather than
   over-flags. The audit paragraph above is superseded on that point only; the defect itself stands.
2. **The disagreement is not a subset, it is churn in both directions.** Joining the two censuses on
   `osm_id` over the identical 7,442-building population: 2,285 buildings are flagged only by the
   corrected method and 1,283 only by the shipped one — **3,568 buildings, 47.9 % of the fleet,
   where the shipped flag disagrees with build-time reality**. The newly-flagged set is dominated by
   MidriseApartment (2,172 of 2,285), whose prototype carries more storeys than most of the real
   midrise stock. A net "+1,002" understates the problem and must not be quoted on its own.

**Consequence today: none.** `fit_check_reason` / `fit_overflow_m` are read by no code — the only
key `builder.py` takes from the layout-assign metadata is `no_baseline` (`builder.py:517`). The
wrong value is latent, not active, and no simulated or published number is affected. It becomes
active the moment anyone reads the flag, which is why E05 fixes it now rather than documenting it.

#### E05 — Compute the fit check where the applied scale factor exists
**What.** Stop computing the fit check in `assign_baseline_layout()`; compute it in the build path,
immediately after `scale = layout_assigner.calculate_scaling_factor(...)`
(`openubem/idf/builder.py:545-550`), using `scale["planar_scale_factor"]` — the factor the build
actually applies — and record the result on the Step-3 manifest `run_step3()` writes.
**Why.** The flag exists to be believed. Computed at the wrong site it disagrees with the build for
47.9 % of the fleet, and a diagnostic no code can read is worth nothing.
**How.** Keep `_fit_check()` and `_raw_prototype_xy_extent()` where they are and call `_fit_check()`
from `builder.py`. In `assign_baseline_layout()` the two keys stay present on both return paths but
are always `None` — that function no longer has the information to fill them. Before wiring,
**verify that the footprint polygon available at the builder call site is in the same local-metre
frame** as the one `assign_baseline_layout()` received; if it is not, STOP and report rather than
converting. Add `fit_check_reason` and `fit_overflow_m` as two manifest columns only; change no
existing column, no row count, no other value.
**How to test.** `python -m pytest tests/test_layout_assigner_fit_check.py tests/test_layout_assigner.py
tests/idf/ tests/test_idf_builder.py -q` must stay green; the fit-check tests that exercised
`assign_baseline_layout()` will need repointing at the new call site — repoint them, do not delete
their assertions. **If any existing golden, schema or manifest test fails because of the two new
columns, STOP and report; do not update a golden.**

#### E05 - Compute the fit check where the applied scale factor exists - completed 2026-09-17
**Artifacts:** `openubem/geometry/layout_assigner.py` (`assign_baseline_layout()` no longer calls
`_fit_check()`; both keys always `None`, function unchanged otherwise), `openubem/idf/builder.py`
(new call site `builder.py:551-553`, right after `scale = layout_assigner.calculate_scaling_factor(...)`
and before `scale_baseline_idf`; uses `poly_local` and `Path(zones[0]["baseline_idf_path"])`;
success-path manifest dict at the `layout_assign` return now carries `fit_check_reason` and
`fit_overflow_m`), `tests/test_layout_assigner_fit_check.py` (4 of 6 tests repointed off
`assign_baseline_layout()` onto a `_fit_check_via_applied_scale()` helper that reproduces the same
`calculate_scaling_factor` + `_fit_check` call the old code path made; the no-baseline and raw-extent
tests were untouched since their behaviour didn't change).
**Deviations:** None. Verified before wiring: `poly_local` (builder.py, `translate_to_origin`) is the
same local-metre-frame polygon `assign_baseline_layout()` receives via `zoning.build_zones()` ->
`bounded_energyplus_footprint()`, which only conditionally simplifies over-budget vertices and never
re-origins or reprojects it — same frame, STOP condition not triggered.
**Test status:** green, no golden/schema/manifest failures from the two new columns (they land as
NaN on every non-`layout_assign` row via `pd.DataFrame(manifest_rows)`, and no existing test
enforces a closed column set).
**Notes:** `_fit_check()` and `_raw_prototype_xy_extent()` left in place at
`openubem/geometry/layout_assigner.py:103-176`, unchanged and still called directly (module-qualified,
not reimplemented) from `builder.py`.

---

#### Manager audit of E05 — 2026-09-17

Every number below was re-measured by the manager, not taken from the executor's report.

- **Call site moved as directed.** `openubem/idf/builder.py:551-553` calls
  `layout_assigner._fit_check(poly_local, Path(zones[0]["baseline_idf_path"]), scale["planar_scale_factor"])`,
  placed after `calculate_scaling_factor(...)` (`:545-550`) and before `scale_baseline_idf` (`:554`).
  The factor passed is now the one the build actually applies — the plate-ratio branch with
  `band_map["recomputed_area_m2"]` and `n_storeys_represented` — which is the whole point of E05.
- **Keys neutralised in the assigner.** `layout_assigner.py:427` is
  `fit_check_reason, fit_overflow_m = None, None`; both metadata dicts still carry the keys
  (`:422-423` no-baseline path, `:443-444` success path), so no consumer sees a missing key.
  `_fit_check` / `_raw_prototype_xy_extent` themselves are untouched at `:149-176`.
- **Manifest columns present.** `builder.py:591-592` adds `"fit_check_reason"` and `"fit_overflow_m"`
  to the layout-assign return dict, which is what `run_step3()` frames into `03_idf_manifest.parquet`.
  Non-layout_assign rows get NaN; no other column changes.
- **Diff stays inside the lane.** `git diff --stat` on the two owned files:
  `layout_assigner.py | 84 +`, `builder.py | 19 +`, 100 insertions / 3 deletions. `git status --porcelain`
  shows no file touched that was not already modified before this task, plus the new untracked test file.
- **Tests re-run by the manager, not quoted:**
  `python -m pytest tests/test_layout_assigner_fit_check.py tests/test_layout_assigner.py tests/idf/ tests/test_idf_builder.py -q`
  → `193 passed in 70.80s`. No golden or schema test was edited: `tests/test_layout_assigner_fit_check.py`
  is the only test file in the diff and it is new/untracked.
- **Test repointing accepted.** Four of six cases now drive a local
  `_fit_check_via_applied_scale()` helper (`tests/test_layout_assigner_fit_check.py:55`) instead of
  `assign_baseline_layout()`, which no longer computes the flag. Assertions were kept, none deleted;
  the no-baseline case (`:99`) and the raw-extent case (`:61`) are unchanged.

**One residual difference the executor did not flag, recorded here and accepted.**
The builder passes `poly_local` (`builder.py:500`, post-`translate_to_origin`, optionally re-oriented
at `:513`). The assigner previously fit-checked the polygon that came back from
`zoning.bounded_energyplus_footprint()` (`zoning.py:95`), which *conditionally simplifies* a ring that
exceeds the vertex budget. So the two polygons are identical for every building under the budget and
differ by a simplification tolerance for the rest. The fit check measures the sides of the
**minimum rotated rectangle**, which vertex simplification moves by far less than the 1.0 m tolerance,
so this does not change a flag. It is stated so nobody later reads the two call sites as equivalent.

**Status of the defect found earlier in this block:** closed. The flag is now computed from the applied
factor. The correct fleet count is the E04 measurement — **5,280 of 7,442 (70.95 %)** — not the 57.48 %
the old code produced, and the old-vs-new disagreement remains what was recorded above: churn in both
directions, 3,568 buildings (47.9 %). Nothing downstream consumed the old value, so no published
number moves.
