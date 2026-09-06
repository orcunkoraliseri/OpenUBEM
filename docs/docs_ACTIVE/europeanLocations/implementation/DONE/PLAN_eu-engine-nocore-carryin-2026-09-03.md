# PLAN — `eu-engine-nocore-carryin` — make the engine draw the plans the owner accepted

**Slug:** `eu-engine-nocore-carryin` · **Opened:** 2026-09-03 · **Director:** this session · **Executor:** fresh Sonnet
**Specs (read-only):** `docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v5.md` §4 (rulings `D-EU-79`…`D-EU-94`)
and §3 (findings through `FINDING 245`, and the `_r5` acceptance table).
**Predecessor:** `PLAN_eu21-colour-repair-2026-09-03.md` (closed, `CP-4` accepted, produced `_r5`).
**Owner authorisation carried into this plan (verbatim, 2026-09-03):**
*"lets go, to the end, no more ask, when you are satisfied, start simulations, i will go out i please continue"* and
*"ok once we reach 95, we will immediately start simulation on the speed cluster cloud computing"*.

---

## 1. Why this plan exists

`_r5` is accepted. 2,353 of 2,544 census plates (92.5 %) pass all seven no-core checks, Madrid crosses the 95 %
bar at 95.3 %, and `D-EU-91`/`D-EU-94` therefore authorise a Speed campaign. **But the campaign cannot run yet,
and the reason is not the census.**

The plans that were reviewed and accepted were drawn by `scripts/eu21/07_nocore_tests.py`. The IDFs that a Speed
campaign would simulate are drawn by `openubem/geometry/european_residential.py`. Measured 2026-09-03:

```
grep -c "core\|corridor" openubem/geometry/european_residential.py   -> 100
grep -c "nocore"         openubem/geometry/european_residential.py   ->   0
```

The engine is still core-era. It carves a circulation polygon out of every plate
(`generate_european_grid_layout` → `_centred_circulation_region`, `CIRCULATION_FRACTION_OF_PLATE = 0.09`), emits it
as an extra unconditioned zone (`european_building_layout_to_zone_specs`, the `circulation_polygon is not None`
branch), and partitions with a ruled `nu × nv` grid plus the group-scheme chain — **not** with the cutter ladder
that produced `_r5`. Submitting today would simulate a fleet of buildings nobody has ever reviewed.

**This plan closes exactly that gap and nothing else.** Its acceptance test is not "the engine looks right"; it is
**bit-parity with `_r5`**: for every one of the 2,544 census plates, the engine must produce the same flats and
the same verdict as the accepted build, plate for plate.

**`D-EU-95` (director, 2026-09-03) — the carry-in is an extraction, never a re-implementation.** The proven
algorithm moves into the engine as copied source with its behaviour intact; it is not "ported in spirit",
re-derived, tidied, refactored, optimised or improved on the way. Any behavioural difference from `_r5`, however
small and however defensible, is a defect of this plan, not an improvement. The reason is `D-EU-54`: the owner
reviewed *those* plans, not plans that resemble them.

---

## 2. Hard rules for the executor — non-negotiable

1. 🔴 **Never edit `scripts/eu21/07_nocore_tests.py`.** Its sha256 `fe75c96ed0ad8512a72c93fccd27b7e46b05c325911163bb47e41b1932a85717`
   is the recorded provenance of all four `_r5` JSONs. Read it, copy from it, never write to it. The same holds
   for `01`–`06` and `08` in that folder.
2. 🔴 **Never regenerate or overwrite a delivered artifact** (`D-EU-85`). The four `*_nocore_2026-09-03_r5.json`
   files, the four `PLANS_*_r5.html` viewers and everything under `plans3D/archive/` are read-only inputs.
3. 🔴 **`MAX_FLAT_ASPECT` stays `2.5`.** Copy the constant; never change it, never make it per-group, per-`k` or
   configurable. `D-EU-84`, `D-EU-86`, `D-EU-89` clause 2.
4. 🔴 **No exemption, no named-building list, no per-morphology carve-out.** A plate that fails in `_r5` must fail
   in the engine, with the same failing check. Parity is two-sided: the engine may not pass a plate `_r5` failed
   any more than it may fail one `_r5` passed.
5. 🔴 **No EnergyPlus run from this plan's tasks `T01`–`T05`** (`D-EU-55`). `T06` is the only task that submits,
   it runs only after `CP-2` is signed by the director, and only the director runs it.
6. 🔴 **Never run compute on the Speed login node.** `sbatch --array` only, `--time=7-00:00:00` minimum, `_ssh()`
   helper from `scripts/cluster/t08_harvest_results.py:104` for every remote command (the remote shell is tcsh).
7. **Never `git add` / `commit` / `stash` / `restore` / `checkout` / `reset` / `clean`.** The dirty tree is the owner's.
8. **Never write into `EU-17/` or `EU-20/`.**
9. **Do not edit root `main.py`, OVERVIEW or DESIGN docs.** No `.py` files under `docs/`, ever.
10. **Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` first; after solving
    any error, register it there before closing the task.**
11. If the plan and the code disagree, **stop and quote the conflict**. Do not invent a resolution.

---

## 3. File layout

| path | action |
| --- | --- |
| `openubem/geometry/european_nocore.py` | **new** — the extracted cutter + the seven checks. Pure geometry. |
| `openubem/geometry/european_residential.py` | **edited** — one new function + one routing switch. Nothing deleted. |
| `scripts/eu21/09_engine_parity.py` | **new** — the parity harness against the four `_r5` JSONs. |
| `scripts/eu21/10_engine_census.py` | **new** — the engine's own building-level census (`T05a`, `FINDING 246`). |
| `openubem/outputs/eu_evidence/EU-21/engine_parity/` | **new** — parity reports (JSON). |
| `scripts/eu21/07_nocore_tests.py`, `01`–`06`, `08` | **read-only.** |
| `openubem/outputs/eu_evidence/EU-21/district_plans/*_r5.json` | **read-only** — the parity oracle. |
| `tests/geometry/`, `tests/test_eu*.py` | **edited only where §6 T04 names them.** |

---

## 4. Dependency decisions (pinned)

1. **`openubem/geometry/european_nocore.py` imports nothing from `scripts/`.** No `importlib` path loading, no
   `sys.path.insert`, no `ROOT` constant, no HTML, no `argparse`. The engine must not depend on a script folder.
2. **The eight helpers the cutter imports from `04`/`05`/`02` are copied into the new module verbatim**, because
   those scripts themselves load each other by file path and cannot be imported from library code:
   - from `scripts/eu21/05_group_cutters.py`: `_normalize` (`:76-81`), `frame` (`:84-95`), `to_local` (`:98-99`),
     `to_world` (`:102-103`), `equal_area_x` (`:106-126`)
   - from `scripts/eu21/04_group_tests.py`: `NARROW_PROBES_M` (`:296`), `widest_fit` (`:299-303`)
   - from `scripts/eu21/02_one_core_per_plate.py`: `SQUARE`, `sbuf` (`:19-23`), `NECK_R` (`:497`), `LOBE_MIN_M2`,
     `lobes_of` (`:501-…`) and `lobes_of`'s own closure (`parts`, and anything else the AST walk in §6 T01 finds).
3. **`_reflex_vertices`, `_reflex_vertex_count` and `_split_at_reflex_vertex` are imported from
   `openubem.geometry.european_residential`**, exactly as `07_nocore_tests.py:91-95` already does — they already
   live in the engine, so there is nothing to copy and no risk of drift.
4. **shapely only.** `set_precision`, `LineString`, `MultiPolygon`, `Point`, `Polygon`, `box`,
   `shapely.ops.split`, `shapely.ops.unary_union`, `shapely.affinity.rotate/translate`,
   `shapely.validation.make_valid`. No new third-party dependency.
5. **`STAGE = "t03"`** is copied as a module constant and never changed — it is the stage that produced `_r5`.
6. **Circulation is not carried in.** No constant, no polygon, no zone, no fraction. `D-EU-79`.

---

## 5. Facts with line citations — read these before writing anything

1. `build_flats(poly, k)` is the whole cutter — `scripts/eu21/07_nocore_tests.py:1269`. It returns
   `(poly, flats, stuck, rows_chosen)` (4-tuple) or `(poly, flats, stuck)` (3-tuple, `rows_chosen` then `1`);
   `build_plate` handles both at `:1673-1677`. **The returned `poly` is the plate the checks are measured against**
   (it is `_normalize`d), not the caller's input polygon.
2. `run_checks(rec, flats, poly)` is the whole verdict — `:1604-1655`. It scores `C1 C3 C4 C5 C6 C10 C11` and sets
   `rec["verdict"]` to `PASS` only when all seven pass. It reads `rec["drawn_per_floor"]` for `C3`.
3. `C11` is not evaluated at `k = 1` — `:1643-1647`, `D-EU-93`. Copy that branch exactly, including the
   `(k=1, D-EU-93)` marker string.
4. `MAX_FLAT_ASPECT = 2.5` — `:1512`. `flat_aspect` `:1521`. `pinch_area` `:1597`. `rings_of` `:1531`.
5. The reachable closure of `build_flats` + `run_checks` inside `07_nocore_tests.py` is **exactly 69 names**,
   computed by the AST walk in §6 T01. Of those, six are the `_M04`/`_M05` re-exports (`widest_fit`, `sbuf`,
   `frame`, `to_local`, `to_world`, `equal_area_x`, `_normalize`, `lobes_of`) and three are the loader plumbing
   (`ROOT`, `_load_module`, `_M04`, `_M05`) which is **dropped**, not copied.
6. The engine's single per-storey seam is `generate_european_ruled_storey_layout(footprint, *, dwelling_count, …)
   -> EuropeanGridLayout` — `openubem/geometry/european_residential.py:1083`. Everything above it is
   regime-agnostic:
   - `generate_european_building_dwelling_layout` `:2585` calls it once per distinct dwelling count (`_layout_for`, `:2619`)
   - `european_building_layout_to_zone_specs` `:2701` emits one zone per dwelling polygon, **and an extra
     unconditioned circulation zone only when `group.layout.circulation_polygon is not None`** (`:2751`)
   - `european_building_layout_area_summary` `:2767` adds `circulation_area_m2` to gross only
   So a layout with `circulation_polygon=None` and `circulation_area_m2=0.0` already produces a no-core building
   through the existing IDF path, with **no edit to the zone-spec writer at all**.
7. `EuropeanGridLayout` is the return contract — `:265-289`. Required fields: `scheme`, `grid`, `nu`, `nv`,
   `dwelling_polygons`, `circulation_polygon`, `circulation_area_m2`, `circulation_pct_of_plate`,
   `circulation_outside_ruled_absolute_band`, `facade_contact_lengths_m`, `habitability_rotation_applied`,
   `habitability_downgrade_applied`, `partition_audit`, `fallback_reason`, `dwelling_layout_emitted`.
8. The `> 12` per-floor refusal is applied **by the caller**, at building level —
   `generate_european_building_dwelling_layout:2603-2609`, token `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_12`.
   `_r5` shows 15 buildings refused this way fleet-wide (Madrid 6 · Lyon 2 · London 7 · Bologna 0). **Leave that
   refusal exactly where it is and exactly as it is**, so the engine's refusal set matches `_r5`'s.
9. 🔴 **The census cuts one `k` per building; the engine cuts one `k` per storey** — `FINDING 246`.
   `08_district_viewer.py:146` uses `k = r["_n"] = max(1, round(dwellings_total / storeys))`, a single count for
   the whole building, on a `usable_polygon`-repaired and **`centred`** footprint (`:180`).
   `generate_european_building_dwelling_layout:2585` uses `allocate_european_dwellings`'s conserved per-storey
   allocation — `tot // storeys`, with the first `tot % storeys` storeys getting one more — so 2,064 of the 2,544
   buildings (81.1 %) are cut at **two** distinct counts and pass only if both do. Consequences: `_r5`'s 2,353
   `PASS` is a per-plate number and is **not** the IDF outcome (`T05a` measures that separately); `_r5` is not
   dwelling-conserving and the engine must **not** be changed to match it, because conservation is a real
   guarantee (`tests/geometry/test_eu13b_dwelling_conservation.py`) and the census's uniform `round()` is not.
10. The `_r5` JSON schema, per district file:
   `district`, `tag`, `built`, `cutter_sha256`, `max_flat_aspect`, `summary`, `plates[]`; each plate carries
   `building_id`, `k`, `drawn_per_floor`, `footprint` (list of rings, exterior first), `dwellings` (list of
   flats, each a list of rings), `checks` (per-check `pass`/`show`), `verdict`, `status`, `rows`.
   `status` is one of `direct`, `REFUSED_K_GT_12`, `GENERIC_NO_CENSUS`, `unusable_footprint`, `ERROR`.

---

## 6. Tasks

### T01 — extract the cutter into `openubem/geometry/european_nocore.py`

**What.** Create the new module holding the accepted no-core algorithm and its seven checks, importable from
library code, behaviourally identical to `07_nocore_tests.py`.

**Why.** The engine cannot import a script that loads its own siblings by absolute Windows path. Copying is the
only way to move the proven code without touching the delivered generator (`D-EU-95`, rule 1).

**How.**
1. Compute the closure yourself, do not trust this list blindly — run exactly:
   ```
   python - <<'PY'
   import ast, pathlib
   src = pathlib.Path("scripts/eu21/07_nocore_tests.py").read_text(encoding="utf-8")
   tree = ast.parse(src)
   defs = {n.name: n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
   assigns = {t.id: n for n in tree.body if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Name)}
   names = set(defs)|set(assigns)
   seen, stack = set(), ["build_flats","run_checks","flat_aspect","pinch_area","rings_of","_opening_lost"]
   while stack:
       f = stack.pop()
       if f in seen or f not in names: continue
       seen.add(f); node = defs.get(f) or assigns.get(f)
       for x in ast.walk(node):
           if isinstance(x, ast.Name) and x.id in names and x.id not in seen: stack.append(x.id)
   for ln,n in sorted(((defs.get(x) or assigns.get(x)).lineno, x) for x in seen):
       node = defs.get(n) or assigns.get(n); print(f"{ln:5d}-{node.end_lineno:<5d} {n}")
   PY
   ```
   Repeat the same walk on `05_group_cutters.py` (roots `frame to_local to_world equal_area_x _normalize lobes_of`),
   `04_group_tests.py` (roots `widest_fit sbuf`) and `02_one_core_per_plate.py` (roots `sbuf lobes_of`) to pick up
   the last hop.
2. Copy every reachable function and module constant **verbatim, body-for-body, comment-for-comment**, into the
   new module, in source order. Drop only `ROOT`, `_load_module`, `_M04`, `_M05`, `_M02`, `_M02_T05B`,
   `_load_frozen_t05b` — the loader plumbing — replacing the eight re-export assignments with the copied
   definitions from §4.2.
3. Keep `STAGE = "t03"` and `MAX_FLAT_ASPECT = 2.5` as module constants with their existing comments.
4. Import `_reflex_vertices`, `_reflex_vertex_count`, `_split_at_reflex_vertex` from
   `openubem.geometry.european_residential`. **Guard against a circular import**: `european_residential` will
   import `european_nocore` in T03, so do that import *inside* the functions that need it, or place the three
   helpers behind a module-level lazy accessor. Do not move the three helpers.
5. Add a module docstring naming `D-EU-79`…`D-EU-95`, the source file, and its sha256.
6. Export a single public entry point:
   ```python
   def cut_storey_nocore(footprint, dwelling_count):
       """Return (plate, flats, checks, verdict) for one storey. Never raises for
       geometry reasons -- a cutter exception is re-raised to the caller unchanged,
       exactly as build_plate:1668 lets it surface."""
   ```
   It calls `build_flats`, normalises the 3-/4-tuple exactly as `build_plate:1673-1677` does, drops empty flats
   exactly as `:1679` does, builds the minimal `rec` (`{"drawn_per_floor": dwelling_count}`), calls `run_checks`,
   and returns `(poly, live, rec["checks"], rec["verdict"])`.
7. 🔴 **Reproduce the census's own preprocessing, and put it inside `cut_storey_nocore`.** The census does not
   hand `build_flats` a raw footprint: `08_district_viewer.py:180` passes `M07.centred(M07.usable_polygon(g))`,
   i.e. `buffer(0)`-repair (`04_group_tests.py:196-203`) then **translate the centroid to the origin**
   (`:206-207`). The engine will hand it a raw UTM polygon at ~4.5 × 10⁶ m, where `set_precision`'s millimetre
   grid does not land on the same bits. So `cut_storey_nocore` must, in this order: apply the `usable_polygon`
   repair, record `(cx, cy) = footprint.centroid`, translate by `(-cx, -cy)`, cut, and then **translate the
   returned plate and every flat back by `(+cx, +cy)`** before returning. Copy `usable_polygon` and `centred`
   verbatim alongside the other helpers. `FINDING 246`.
8. 🔴 **The whole cut and all seven checks run in the centred frame; the translate-back is the last statement
   before `return` and nothing is recomputed after it.** Every check is evaluated on centred geometry, exactly as
   `07_nocore_tests.py` evaluates it, so the verdict cannot depend on where the building sits in UTM. The
   translate-back exists only because `european_building_layout_to_zone_specs` writes the returned coordinates
   straight into the IDF and they must be in the same frame as the `footprint` argument the engine was handed.
   Ruled by the director 2026-09-03, mid-T01, after the executor reported round-trip drift: the centred frame and
   the engine's frame are two different frames, and that is a frame question, never a numerical defect to isolate.

**How to test.** `python -c "from openubem.geometry.european_nocore import cut_storey_nocore; print('ok')"` from
the repo root, and the T02 harness. Do **not** hand-write unit tests for individual cutters — parity is the test.

---

### T02 — the parity harness `scripts/eu21/09_engine_parity.py`

**What.** Replay `cut_storey_nocore` over every plate in the four `_r5` JSONs and prove it reproduces them.

**Why.** This is the acceptance gate of the whole plan and the evidence that the buildings Speed simulates are the
buildings the owner reviewed (`D-EU-54`, `D-EU-95`).

**How.**
1. For each of the four `*_nocore_2026-09-03_r5.json`, for every plate with `status == "direct"`:
   take the plate's **input geometry**, call `cut_storey_nocore(g, plate["drawn_per_floor"])`, and compare:

   🔴 **Corrected 2026-09-03 by the director, after the first `CP-1` failed. The original instruction here —
   "rebuild the plate polygon from `plate["footprint"]`" — was wrong, and it was the harness that was wrong,
   not the extraction.** Two faults, both mine:
   - `plate["footprint"]` is the cutter's **output** plate, not its input. The census fed
     `M07.centred(M07.usable_polygon(g))` (`08_district_viewer.py:160,181`).
   - It is stored **rounded to 3 decimals** (millimetres). `build_flats` picks its winning candidate by a strict
     `>` over a score tuple that is itself rounded to 3 decimals (`07_nocore_tests.py:970`), so when two
     structurally different candidates land inside that band, sub-millimetre input precision decides the winner.

   So the harness must reproduce the census's own input, at full precision:
   `geoms, rows, *_ = M07.load_universe()` → `g = geoms[(district, building_id)]` → pass **that raw `g`** to
   `cut_storey_nocore`, which applies the `usable_polygon` repair and the centring itself, once (T01 step 7).
   Loading `07_nocore_tests.py` by path is allowed **in the harness** — rule 4.1 binds
   `openubem/geometry/european_nocore.py`, which still imports nothing from `scripts/`.

   Measured by the director before this correction was written, on the two buildings the first run named:

   ```
   way/232618736  k=3  _r5 rows=1 PASS | from stored footprint: PASS | from raw geometry: PASS
   way/391270221  k=5  _r5 rows=1 FAIL | from stored footprint: PASS | from raw geometry: FAIL  <- matches _r5
   ```

   The single verdict mismatch of the first run is an artefact of the rounded input and disappears against the
   real one. Re-run the whole harness this way. **The gate does not move: still 0 mismatches of all four kinds.**
   - **verdict** — must equal `plate["verdict"]` exactly;
   - **flat count** — `len(live)` must equal `len(plate["dwellings"])`;
   - **each check's `pass` and `show`** — must equal `plate["checks"][c]` for all seven, string-for-string;
   - **geometry** — `symmetric_difference` area between the union of the produced flats and the union of the
     stored flats must be `<= 1e-6 m²`, and per-flat area must match to `1e-6 m²` after matching flats by
     representative point. 🔴 **Compare in the centred frame**: translate the returned plate and flats by
     `(-cx, -cy)` — the same centroid `cut_storey_nocore` recorded — before differencing, because `_r5` stores
     centred geometry (`08_district_viewer.py:180`) and the engine returns the caller's frame (T01 step 8).
     Never modify `_r5` to make a comparison work.
2. Plates with `status != "direct"` are counted and skipped (they carry no `dwellings`), and the harness asserts
   the counts of each status equal the JSON `summary.status_counts`.
3. Write `openubem/outputs/eu_evidence/EU-21/engine_parity/parity_<district>_2026-09-03.json` with, per district:
   `plates_compared`, `verdict_mismatches`, `count_mismatches`, `check_mismatches`, `geometry_mismatches`,
   and the first 20 mismatching `building_id`s with the field that differed.
4. Print a fleet summary line: `compared N · mismatches V/C/K/G`.
5. `--jobs` with `concurrent.futures.ProcessPoolExecutor` is allowed (the cutter is pure); default to 8.

**How to test.** **The gate is 0 mismatches of all four kinds, on all four districts, 2,353 `PASS` and 176 `FAIL`
reproduced exactly.** Anything above 0 is a defect in T01 — fix T01, never the harness, and never the tolerance.

**Stop here and report (`CP-1`).**

---

### T03 — the engine seam

**What.** Add `generate_european_nocore_storey_layout` to `openubem/geometry/european_residential.py` and route
`generate_european_building_dwelling_layout` through it.

**Why.** This is the actual carry-in: the IDF path stops drawing cores and starts drawing the accepted flats.

**How.**
1. New function, placed immediately after `generate_european_ruled_storey_layout`'s definition ends:
   ```python
   def generate_european_nocore_storey_layout(
       footprint, *, dwelling_count, minimum_facade_contact_m=2.5,
   ) -> EuropeanGridLayout:
   ```
   It calls `openubem.geometry.european_nocore.cut_storey_nocore(footprint, dwelling_count)` inside a
   `try/except Exception`, and returns an `EuropeanGridLayout` with:
   - `scheme = "nocore_equal_area"`, `grid = f"nocore_{dwelling_count}"`, `nu = dwelling_count`, `nv = 1`
   - `dwelling_polygons = tuple(live)` when the verdict is `PASS`, else `()`
   - **`circulation_polygon = None`, `circulation_area_m2 = 0.0`, `circulation_pct_of_plate = 0.0`,
     `circulation_outside_ruled_absolute_band = False`** — always, unconditionally (`D-EU-79`)
   - `facade_contact_lengths_m = _facade_contact_lengths(plate, live)`
   - `habitability_rotation_applied = False`, `habitability_downgrade_applied = False`
   - `partition_audit = audit_european_floor_partition(plate, tuple(live), expected_dwelling_count=dwelling_count,
     topology_tolerance_fraction=EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION)` when the verdict is `PASS`, else `None`
   - `dwelling_layout_emitted = (verdict == "PASS")`
   - `fallback_reason = None` on `PASS`; on `FAIL`, `"NOCORE_CHECK_FAILED_" + "_".join(failed check ids)`;
     on a cutter exception, `"NOCORE_CUTTER_" + type(exc).__name__`.
2. **The refusal is honest.** A `FAIL` plate must return `dwelling_layout_emitted=False` so the building falls back
   to the existing `one_zone_per_floor` massing box, exactly as any other unlayoutable building does today. Never
   emit a failing partition, never repair it here, never relax a check.
3. Add a module-level regime switch, defaulting to the no-core regime:
   ```python
   EUROPEAN_LAYOUT_REGIME = "nocore"   # D-EU-79/D-EU-95. "ruled" = the parked corridor path.
   ```
   In `generate_european_building_dwelling_layout._layout_for`, dispatch on it: `"nocore"` →
   `generate_european_nocore_storey_layout(...)`; `"ruled"` → the existing
   `generate_european_ruled_storey_layout(..., carve_circulation=carve_circulation)` call, byte-unchanged.
4. **Delete nothing.** `generate_european_ruled_storey_layout`, the group schemes, `generate_european_grid_layout`,
   `generate_external_unconditioned_core` and every circulation constant stay in the file, reachable through
   `"ruled"`. The corridor path is parked, not removed (`D-EU-79`).
5. `carve_circulation` keeps being threaded to the `"ruled"` branch and is ignored by the `"nocore"` branch — a
   no-core storey has no circulation to suppress. Do not delete the parameter.

**How to test.**
- `python -c` on one Madrid `PASS` footprint from `_r5`: assert the returned layout has
  `circulation_polygon is None`, `dwelling_layout_emitted is True`, and `len(dwelling_polygons) == k`.
- On one `_r5` `FAIL` footprint: assert `dwelling_layout_emitted is False`.
- `grep -n "circulation" ` the new function: **zero hits other than the four `None`/`0.0` assignments.**

---

### T04 — regression sweep

**What.** Run the EU geometry test suite and reconcile every failure.

**Why.** ~30 modules import this engine. A regime switch that silently breaks the fleet path is worse than no
carry-in.

**How.**
1. `python -m pytest -q -n 8 tests/geometry/ tests/test_eu*.py` — record the full pass/fail/skip counts before
   touching anything, on a clean checkout of the pre-T03 file if needed for comparison.

   **The pre-seam baseline is already measured — the director ran it 2026-09-03, before `european_residential.py`
   was touched. Do not re-derive it; compare against it.**

   ```
   6 failed, 613 passed in 24.77s
   FAILED tests/geometry/test_eu15_ruled_coverage.py::test_t03_l_shape_survives_a_second_near_threshold_reflex_vertex
   FAILED tests/geometry/test_eu14b_bologna_layout_binding.py::test_t02_one_sidecar_per_simulated_building
   FAILED tests/geometry/test_eu14b_bologna_layout_binding.py::test_t03_both_provenance_tags_present_on_every_sidecar
   FAILED tests/geometry/test_eu14b_bologna_layout_binding.py::test_t03_construction_period_badge_appears_in_generated_viewer
   FAILED tests/test_eu_real_footprint_feasibility.py::test_real_layout_generator_fails_closed_for_unsupported_topology[footprint1-COURTYARD_TOPOLOGY_UNSUPPORTED]
   FAILED tests/test_eu_real_footprint_feasibility.py::test_real_layout_generator_fails_closed_for_unsupported_topology[footprint2-NON_CONVEX_TOPOLOGY_UNSUPPORTED]
   ```

   Those six are class **(c)** by construction — they failed before the engine was touched. Any *seventh* failure,
   or any of the 613 turning red, is yours to classify and resolve.
2. Classify every failure into exactly one of:
   - **(a) asserts the corridor regime** (expects a circulation zone, a ruled `nu × nv` grid, a core, a
     `circulation_pct_of_plate` band). Fix by pinning that test to `EUROPEAN_LAYOUT_REGIME = "ruled"` explicitly —
     the parked path still works and the test still means something. Note it in the progress log.
   - **(b) a genuine defect in T03.** Fix T03.
   - **(c) pre-existing failure, unrelated.** Prove it by running the same test on the pre-T03 file and quoting
     both results. Leave it alone; list it in the progress log.
3. **Never** fix a test by loosening an assertion about the seven checks, about `MAX_FLAT_ASPECT`, or about
   dwelling conservation.
4. Register any error you debug in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, house format.

**How to test.** The suite's own output, quoted in full counts, plus the (a)/(b)/(c) classification of every
failure by name.

---

### T05a — the engine's own building-level census (`FINDING 246`)

**What.** Before any IDF is written, measure how many buildings the **engine** can serve, at the engine's own
per-storey dwelling allocation, and compare that number honestly with `_r5`'s per-plate census.

**Why.** `FINDING 246`: the district census cuts each building once at `k = round(dwellings_total / storeys)`;
the engine cuts each **storey** at its own conserved allocation. Measured: **1,814 of 2,544 buildings (71.3 %)**
carry more than one distinct dwelling count — Madrid 524 · Lyon 184 · London 68 · Bologna 1,038 — so the engine
cuts them at both `q` and `q + 1` and they carry floor plans only if **both** pass. So `_r5`'s 2,353 `PASS` is a
per-plate figure and **is not a prediction of the IDF outcome**. Nobody may quietly substitute one for the other,
in either direction. The totals themselves agree (`morphology_census.csv`'s `dwellings_total` is read from the
engine's own side-cars, `eu20_morphology_atlas.py:149-154`), and the `> 12` refusal barely moves — **2 buildings**
fleet-wide, both Madrid, reach `> 12` on the engine's larger count while the census's `k` stayed `<= 12`.

**How.**
1. New script `scripts/eu21/10_engine_census.py`. For every one of the 2,544 census rows: read the footprint from
   the same manifest the census reads (`01_cut_group_plans.py:136-146`, `02_residential_manifest.gpkg` per
   district), take `storeys` and `dwellings_total` from `EU-20/morphology_census.csv`, build the engine's own
   `floor_allocations` via `allocate_european_dwellings`, and evaluate `cut_storey_nocore` once per **distinct**
   dwelling count in that allocation (cache by count per building — the engine caches the same way,
   `european_residential.py:2619`).
2. Classify each building: `EMITTED` (every distinct count passes, and `max(count) <= 12`),
   `REFUSED_K_GT_12` (`max(count) > 12`, the caller-level refusal at `:2603`), or `FALLBACK` (at least one count
   fails the seven checks) — with the failing counts and failing check ids recorded.
3. Write `openubem/outputs/eu_evidence/EU-21/engine_parity/engine_census_2026-09-03.json`: per district and
   fleet, `census_rows`, `EMITTED`, `REFUSED_K_GT_12`, `FALLBACK`, `fail_by_check`, and the **delta against
   `_r5`'s `PASS`**, with the buildings that changed side listed by id and reason.
4. 🔴 **Report both numbers side by side. Never quote the engine number as the census number, and never quote
   the census number as the engine number.** `D-EU-91`'s gate was ruled and met on the census reading and that
   stands; this is additional information about what will actually be simulated, not a re-reading of the gate.
5. **Change nothing to make the two agree.** Not `k`, not the allocation, not the checks, not
   `MAX_FLAT_ASPECT`. Dwelling conservation (`tests/geometry/test_eu13b_dwelling_conservation.py`) is a real
   guarantee and the census's uniform `round()` is not — the engine keeps conservation (`D-EU-88` clause 1).

**How to test.** `EMITTED + REFUSED_K_GT_12 + FALLBACK` must equal `census_rows` in every district. The script is
a measurement and has no pass/fail threshold of its own.

---

### T05 — rebuild the four districts' IDFs through the engine

**What.** Run `scripts/run_eu_s2_district_campaign.py` in prepare-only mode for all four districts and audit what
it wrote.

**Why.** This is the artifact Speed will actually simulate.

**The "before" number, measured by the director 2026-09-03 from the delivered core-era build's own
`prepared_buildings.csv` files** — this is what a campaign submitted *without* the carry-in would simulate:

| district | prepared | carries a real dwelling layout | massing-box fallback |
| --- | ---: | ---: | ---: |
| `ES-MAD-BERRUGUETE` | 961 | **616** (64.1 %) | 345 |
| `FR-LYO-HAUTCOEURPENTES` | 297 | **198** (66.7 %) | 99 |
| `GB-LDN-STDUNSTANS` | 82 | **40** (48.8 %) | 42 |
| `IT-BOL-GALVANI2` | 1,204 | **594** (49.3 %) | 610 |
| **FLEET** | **2,544** | **1,448 (56.9 %)** | **1,096** |

`geometry_exclusions` is `{}` in all four — no building was lost to an IDF-assembly crash in the delivered
build, so the `ZeroDivisionError` / `IndexError` demotion path (`run_eu_s2_district_campaign.py:434`) was never
taken there. If T05 produces a non-empty `geometry_exclusions`, that is new and must be reported, not absorbed:
an excluded building gets **no IDF at all**, it is not demoted to a massing box.

**How.**
1. Run the district campaign's IDF preparation for each of the four districts (it is an IDF *preparer*, not a
   runner — `scripts/run_eu_s2_district_campaign.py:1-8`). Use its existing CLI; **add no new flags.**
   🔴 **`D-EU-85`, ruled by the director before this task: the output directory is repointed, never reused.**
   The existing `openubem/outputs/eu_evidence/EU-11/<DISTRICT>/` directories are the delivered core-era build
   (961 · 297 · 82 · 1,204 IDFs) and are **read-only**. Write to:
   ```
   --out openubem/outputs/eu_evidence/EU-11/<DISTRICT>_nocore_2026-09-03
   ```
   for each of `ES-MAD-BERRUGUETE`, `FR-LYO-HAUTCOEURPENTES`, `GB-LDN-STDUNSTANS`, `IT-BOL-GALVANI2`. If the
   script refuses to create a directory that does not exist, create it first — do not point it at the old one.
2. Audit the emitted IDFs, fleet-wide:
   - 🔴 **zero** `Zone` objects whose name ends `_circulation`, in every IDF of all four districts;
   - the per-district count of `geometry_outcome == "DWELLING_LAYOUT_EMITTED*"` in `prepared_buildings.csv`
     **equals `T05a`'s own `EMITTED` count exactly** — that is the oracle, not `_r5`'s `PASS`
     (`FINDING 246`);
   - every other building took the `one_zone_per_floor` massing-box route, and the two counts sum to the
     district's prepared row count;
   - for a random sample of 20 `EMITTED` buildings per district, the conditioned zone count equals the sum of
     that building's `floor_allocations`, i.e. dwelling conservation holds end to end;
   - `european_building_layout_area_summary`'s gross and conditioned areas are **equal** for every `EMITTED`
     building — the arithmetic proof that no circulation area was carved anywhere.
3. 🔴 **Bologna reaches a live API; prove it did not change anything but the geometry.** `_it_rows`
   (`run_eu_s2_district_campaign.py:198-226`) fetches CTC eaves heights and ISTAT 2011 census sections from
   `opendata.comune.bologna.it` **uncached**, so a rebuild can pick up different upstream data and silently move
   an archetype or an age band — a change that has nothing to do with this carry-in. Do not edit the script and
   do not add a cache. Instead, **diff `prepared_buildings.csv` old vs new** for all four districts and assert
   that `archetype_id`, `building_type` and `age_band` are **identical row for row**; only `geometry_outcome`
   and `idf_sha256` may differ. Any other difference is contamination — stop and report it, do not absorb it.
   (Director checked 2026-09-03: the ISTAT sections endpoint answers `200`, 4.68 MB. That says reachable, not
   unchanged — the diff is still required.)
4. Write the audit as `openubem/outputs/eu_evidence/EU-21/engine_parity/idf_audit_2026-09-03.json`, and include
   the `_r5` `PASS` figures alongside as a labelled comparison — never as the pass/fail criterion.

**How to test.** Every bullet in step 2, each reported as a number. The zero-circulation-zone assertion and the
`EMITTED == T05a.EMITTED` identity are the two that gate `CP-2`.

**Stop here and report (`CP-2`). Do not proceed to T06.**

---

### T06 — the Speed campaign (director only, after `CP-2`)

**What.** Ship the audited IDFs to Speed and submit one `sbatch --array` campaign per district.

**Why.** `D-EU-91`/`D-EU-94`: the owner's condition (95 % in a district) is met, and the owner's own sentence
authorises the run.

**How.**
1. Only after `CP-2` is signed. Executor does **not** run this task.
2. 🔴 **`--time=7-00:00:00` minimum on every submission, given on the CLI.** `scripts/cluster/submit_fleet.sbatch`
   bakes in `#SBATCH --time=01:30:00`; that file is shared and is **not** edited — the CLI override wins:
   ```
   sbatch --time=7-00:00:00 --array=1-N%8 --export=FLEET_DIR=<remote fleet dir> submit_fleet.sbatch
   ```
3. Never `srun`, never `ssh … python`. Login node is for `mkdir` / `scp` / `tar` / `squeue` / `sacct` only.
4. Every remote command through the `_ssh()` helper (`scripts/cluster/t08_harvest_results.py:104`) — the remote
   shell is tcsh and bare bash syntax fails silently.
5. `scripts/cluster/ship_eu11_fleet.sh` hard-codes `LOCAL_DIR=…/EU-11/${DISTRICT}` (`:15`). T05 writes to
   `…/EU-11/${DISTRICT}_nocore_2026-09-03`, so the ship step must take the new directory —
   pass the suffixed name as `$1`, which resolves correctly without editing the script, and use a distinct
   remote fleet dir (`EU11_${DISTRICT}_nocore_2026-09-03`) so no delivered remote fleet is overwritten.
6. Submit in waves if the array exceeds Speed's ~20k task cap. Four districts total ≤ 2,544 tasks, so one array
   per district is within the cap.
7. Fire and forget; harvest from the output files later.

**How to test.** One real job placed and observed in `squeue` before leaving the campaign unattended.

**Pre-flight, measured by the director 2026-09-03 (login-node read-only commands only):**
- `squeue -u o_iseri` → **0 jobs**. The queue is empty; the CHECKLIST's "confirm the Speed queue is empty before
  `EU-19` is prepared" item is satisfied as of this date and must be re-checked immediately before submitting.
- EnergyPlus present: `/speed-scratch/o_iseri/openubem/tools/EnergyPlus-23.1.0-87ed9199d4-Linux-Ubuntu20.04-x86_64`
  (and the Ubuntu22.04 build). `submit_fleet.sbatch` resolves the 20.04 one first — unchanged, correct.
- `/nfs/speed-scratch` → 27 TB available of 121 TB (79 % used). A 2,544-task campaign fits.
- Key-based SSH works from this machine with `BatchMode=yes`; no password prompt.

---

## 7. Stop-and-report points

- **`CP-1`** — after T02. Report: the parity numbers (compared / verdict / count / check / geometry mismatches),
  per district and fleet. **The plan does not continue at anything but 0 mismatches.**

  ✅ **SIGNED by the director, 2026-09-03, on the second run.** The first run failed (1/0/53/51) on a harness
  input defect, corrected in `T02` §1; the re-run is clean.

  ```
  ES-MAD-BERRUGUETE       compared  955 · mismatches 0/0/0/0
  FR-LYO-HAUTCOEURPENTES  compared  295 · mismatches 0/0/0/0
  GB-LDN-STDUNSTANS       compared   75 · mismatches 0/0/0/0
  IT-BOL-GALVANI2         compared 1204 · mismatches 0/0/0/0
  FLEET                   compared 2529 · mismatches 0/0/0/0     input_missing 0
  ```

  **Director's own audit, not the executor's word:**
  - `plates_compared` equals each district's `status == "direct"` count read straight from the `_r5` JSONs —
    955 / 295 / 75 / 1,204 = **2,529**. Nothing was silently skipped, and `input_missing` is 0 everywhere.
  - The harness was re-read: `GEOM_TOLERANCE_M2 = 1e-6` unchanged (`09_engine_parity.py:53`), all seven
    `CHECK_IDS` compared on both `pass` and `show`, no skip list, no per-building exemption, no
    `MAX_FLAT_ASPECT` reference.
  - Geometry parity is exact rather than approximate because the cutter's output is `set_precision`-snapped to
    the millimetre grid: all 14,116 stored Madrid footprint coordinates lie exactly on it, so the `_r5` file is a
    lossless record and the `1e-6 m²` bound is never being leaned on.

  **`D-EU-95` is satisfied on its own terms.** `openubem/geometry/european_nocore.py` reproduces the accepted
  build plate for plate, verdict for verdict, check-string for check-string. T03 may proceed.
- **`CP-2`** — after T05a and T05. Report: the test-suite counts with every failure classified (a)/(b)/(c),
  `T05a`'s engine census per district **side by side with `_r5`'s per-plate census** and the delta explained,
  the IDF audit's route counts against `T05a`'s own `EMITTED`, and the zero-circulation-zone assertion.
  **Director signs before T06.**

---

## 8. Progress log

*(one entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations / Test status / Notes)*

#### T01 — extract the cutter into `openubem/geometry/european_nocore.py` — completed 2026-09-03

Artifacts: `openubem/geometry/european_nocore.py` (new, 1731 lines).

Deviations:
- The AST closure walk (§6 T01 how, step 1) was also run on `04_group_tests.py` (roots `widest_fit sbuf`)
  as instructed. `widest_fit` (`:299-303`) and its constant `NARROW_PROBES_M` (`:296`) are genuinely defined
  in `04_group_tests.py` itself (not re-exported from elsewhere) and are called by `_sweep_boundaries`
  (build_flats's swept-boundary candidate). First assembly pass omitted both — `_sweep_boundaries` would have
  raised `NameError` at runtime, silently swallowed by `build_flats`'s own per-candidate `try/except`, quietly
  removing that whole candidate from the search. Caught before T02 by inspecting the assembled module's
  top-level name list against the AST closure; both were added (module lines ~176-182).
- `LOBE_MIN_M2` (`02_one_core_per_plate.py:498`) was copied incidentally — it sits between `NECK_R` (`:497`)
  and `lobes_of` (`:501-527`) in the source and the contiguous line-range copy picked it up. It is unused by
  the reachable closure (`unsnake`, its only caller in `02`, is not reachable from `build_flats`/`run_checks`);
  harmless, left in place rather than surgically excised, matching D-EU-95's verbatim-copy spirit.
- `_reflex_vertices` is imported lazily inside the two functions that call it (`_reflex_theta_offsets`,
  `_reflex_points_world`) rather than via a module-level lazy-accessor function; `_reflex_vertex_count` and
  `_split_at_reflex_vertex` (also named in §4 point 3) are not called anywhere in the reachable closure
  (confirmed by `grep` on the extracted range) and were not imported, to avoid two dead imports.
- Step 7 (`usable_polygon`/`centred` carried in, `FINDING 246`) and step 8 (checks scored in the centred frame,
  translate-back as the last statement) were added by the director mid-task and implemented as specified;
  `usable_polygon`/`centred` copied verbatim from `04_group_tests.py:196-207`.

Test status:
- `python -c "from openubem.geometry.european_nocore import cut_storey_nocore; print('ok')"` → `ok`.
- Spot check on one Madrid `PASS` plate (`way/100704656`, `_r5`) reproduced `verdict`, flat count exactly.

Notes: module docstring names `D-EU-79`…`D-EU-95`, `FINDING 246`, source file and its sha256
`fe75c96ed0ad8512a72c93fccd27b7e46b05c325911163bb47e41b1932a85717`.

#### T02 — the parity harness `scripts/eu21/09_engine_parity.py` — completed (harness), gate NOT met — 2026-09-03

Artifacts: `scripts/eu21/09_engine_parity.py` (new); `openubem/outputs/eu_evidence/EU-21/engine_parity/parity_<district>_2026-09-03.json`
(4 files, one per district, each with `first_20_mismatches`).

Test status — **CP-1 gate not met.** `python scripts/eu21/09_engine_parity.py --jobs 8`, tolerance `1e-6 m²`
unchanged, `_r5` JSONs untouched:
```
ES-MAD-BERRUGUETE: compared 955 · mismatches 1/0/25/22
FR-LYO-HAUTCOEURPENTES: compared 295 · mismatches 0/0/2/3
GB-LDN-STDUNSTANS: compared 75 · mismatches 0/0/2/2
IT-BOL-GALVANI2: compared 1204 · mismatches 0/0/24/24
compared 2529 · mismatches 1/0/53/51   (verdict/count/check/geometry)
```
1 verdict mismatch: `way/391270221` (Madrid) — `_r5` `FAIL`, engine `PASS` — the exact two-sided-parity
violation §2 rule 4 forbids.

🔴 FINDING (not yet numbered by the director): the harness cannot reach 0 mismatches by construction, and
`european_nocore.py`'s own extraction is not the cause. Root-caused on `way/232618736` (Madrid, `k=3`,
`_r5` `PASS`): stored `rows=1`, flat areas `108.72 / 110.42 / 112.14 m²`; engine's winning candidate
`rows=2`, flat areas `82.82 / 82.82 / 165.63 m²` — a genuinely different partition, not a rounding artefact
(confirmed by re-running `build_flats` directly and reading `rows_chosen`). `_r5`'s stored `footprint`/
`dwellings` coordinates are JSON-serialized to 3 decimal places; re-deriving `cx, cy` from that already-rounded,
already-once-centred polygon and re-running the full `usable_polygon`→centre→cut→translate-back path (T01
steps 7-8) does not reproduce the exact floating-point input the original census run computed (which centred
a full-precision raw UTM footprint exactly once, never JSON-round-tripped). `build_flats`'s own candidate
search picks a winner by strict `>` over a score tuple that rounds `pinch_total`, `min_c6` and `max_aspect`
to 3 decimals (`_plate_score`); when two structurally different candidates land inside that rounding band of
each other, sub-millimetre input precision decides which one is evaluated first and therefore wins. Verified
this is not the translate round-trip itself: the earlier (director-flagged) frame mismatch was fixed first
(harness now compares in the centred frame, `(-cx, -cy)` on the engine's own output before differencing,
per the director's ruling and plan §6 T02 step 1) and confirmed 0 residual on 14/15 sampled plates before
the fleet run surfaced this second, distinct, unresolved mechanism.

Per §2 rule 11 and the director's rule ("a drift you cannot explain is a `CP-1` failure and the plan stops"):
stopped here. Tolerance (`1e-6 m²`), `MAX_FLAT_ASPECT`, and the seven checks were not touched. Not proceeding
to T03.

Deviations: none beyond the frame fix already specified in plan §6 T02 step 1 (translate the engine's return
by `(-cx, -cy)` before differencing) — implemented in `_check_one_plate`.

#### T02 — parity harness, corrected input — completed 2026-09-03

Artifacts: `scripts/eu21/09_engine_parity.py` (edited, input source only);
`openubem/outputs/eu_evidence/EU-21/engine_parity/parity_<district>_2026-09-03.json` (4 files, overwritten).

Deviations: none from the director's corrected §6 T02 step 1. `plate["footprint"]` (rounded 3-decimal cutter
output) replaced as the harness's input source by the raw census geometry: `M07 = _load_module(...)` loads
`07_nocore_tests.py` by path (same pattern as `08_district_viewer.py:29-37`), `geoms, *_ = M07.load_universe()`
runs once in the parent process before task construction, `cut_storey_nocore` is left to apply the
`usable_polygon` repair and centring itself (T01 step 7) — nothing pre-applied. A plate whose
`(district, building_id)` is absent from `geoms` is skipped and counted separately as `input_missing`
(none occurred). `--jobs` workers receive geometry as WKB bytes (`g.wkb` / `wkb_loads`), never call
`load_universe()` themselves. Tolerance (`1e-6 m²`) and the centred-frame comparison are byte-unchanged.

Test status — **CP-1 gate met.** `python scripts/eu21/09_engine_parity.py --jobs 8`:
```
ES-MAD-BERRUGUETE: compared 955 · mismatches 0/0/0/0 · input_missing 0
FR-LYO-HAUTCOEURPENTES: compared 295 · mismatches 0/0/0/0 · input_missing 0
GB-LDN-STDUNSTANS: compared 75 · mismatches 0/0/0/0 · input_missing 0
IT-BOL-GALVANI2: compared 1204 · mismatches 0/0/0/0 · input_missing 0
compared 2529 · mismatches 0/0/0/0 · input_missing 0
```
0 mismatches of all four kinds (verdict/count/check/geometry), all four districts, `input_missing` 0 fleet-wide.
The single verdict mismatch (`way/391270221`) from the prior run does not recur.

Notes: `usable_polygon`'s `buffer(0)` raised `RuntimeWarning: divide by zero/invalid value encountered in
buffer` on stderr for a handful of plates during the run; the run still produced 0 mismatches, so left
uninvestigated — not a fix-worthy error, not registered in the debug reference doc.

#### T03 — the engine seam — completed 2026-09-03

Artifacts: `openubem/geometry/european_residential.py` (edited: one new import, one new function
`generate_european_nocore_storey_layout`, one new module constant `EUROPEAN_LAYOUT_REGIME`, one dispatch
in `generate_european_building_dwelling_layout._layout_for`).

Deviations:
- `from openubem.geometry.european_nocore import cut_storey_nocore` was added as a top-level import
  (not inside the function). Safe per `european_nocore.py`'s own module docstring and T01's step-4
  deviation log: `european_nocore` imports `_reflex_vertices` etc. from `european_residential` lazily,
  inside the two functions that call them, never at its own module top level, so there is no cycle at
  import time. Verified: `python -c "from openubem.geometry.european_residential import
  generate_european_nocore_storey_layout, EUROPEAN_LAYOUT_REGIME"` → `ok nocore`, no
  `ImportError`/`AttributeError`.
- `EUROPEAN_LAYOUT_REGIME = "nocore"` (module constant, per §6 T03 step 3) was placed immediately above
  `generate_european_building_dwelling_layout`, the one function that reads it — placement was not
  specified by the plan beyond "module-level".

Test status:
- `python -c` spot check, Madrid `way/100704656` (`_r5` `k=3`, stored `PASS`), raw census geometry via
  `M07.load_universe()`: `circulation_polygon is None`, `dwelling_layout_emitted is True`,
  `len(dwelling_polygons) == 3`.
- `way/287696590` (`_r5` `k=1`, stored `FAIL`): `dwelling_layout_emitted is False`,
  `fallback_reason == "NOCORE_CHECK_FAILED_C4"`.
- `grep -n "circulation"` over the new function body: hits are the docstring sentence plus the two
  blocks of four `None`/`0.0` field assignments (one block per return path — the cutter-exception early
  return and the normal return) — no other reference.

Notes: `facade_contact_lengths_m = _facade_contact_lengths(plate, live)` (§6 T03 step 1 bullet) runs
unconditionally on the normal return path, so it is populated on a `FAIL` verdict too, unlike
`dwelling_polygons`/`partition_audit` which are gated to `PASS` — implemented exactly as the plan's
bullet list states it, not as a symmetry choice.

#### T04 — regression sweep — completed 2026-09-03

Artifacts: `tests/geometry/test_eu15_ruled_coverage.py` (edited, 4 tests pinned to `"ruled"`),
`tests/test_eu17_relaxed_layout.py` (edited, 2 tests pinned to `"ruled"`).

Deviations: none from §6 T04.

Test status — `python -m pytest -q -n 8 tests/geometry/ tests/test_eu*.py --tb=no`:
- Immediately after T03, before reconciliation: `12 failed, 607 passed` — 6 new failures beyond the
  pinned pre-seam baseline (`613 passed, 6 failed`), no baseline test flipped from failing to passing.
- After reconciliation: `6 failed, 613 passed in 26.34s` — identical count and identical six names to
  the pinned pre-seam baseline. No seventh failure.

Classification, every failure:
- **(c) pre-existing, unrelated, unchanged** — the six pinned in §6 T04 step 1, re-observed unchanged:
  `test_eu15_ruled_coverage.py::test_t03_l_shape_survives_a_second_near_threshold_reflex_vertex`,
  `test_eu14b_bologna_layout_binding.py::test_t02_one_sidecar_per_simulated_building`,
  `test_eu14b_bologna_layout_binding.py::test_t03_both_provenance_tags_present_on_every_sidecar`,
  `test_eu14b_bologna_layout_binding.py::test_t03_construction_period_badge_appears_in_generated_viewer`,
  `test_eu_real_footprint_feasibility.py::test_real_layout_generator_fails_closed_for_unsupported_topology[footprint1-COURTYARD_TOPOLOGY_UNSUPPORTED]`,
  `test_eu_real_footprint_feasibility.py::test_real_layout_generator_fails_closed_for_unsupported_topology[footprint2-NON_CONVEX_TOPOLOGY_UNSUPPORTED]`.
- **(a) asserts the corridor regime** — fixed by adding a `monkeypatch` fixture and
  `monkeypatch.setattr(module, "EUROPEAN_LAYOUT_REGIME", "ruled")` (module imported locally as
  `from openubem.geometry import european_residential as module`, the pattern already used at
  `tests/geometry/test_eu13b_dwelling_conservation.py:154`) at the top of each test body — the parked
  path still runs and each test still means something:
  `test_eu15_ruled_coverage.py::test_t05_building_layout_area_summary_conditioned_less_than_gross_when_core_present`,
  `test_eu15_ruled_coverage.py::test_t05_zone_specs_tag_circulation_zones_unconditioned_with_infiltration_rate`,
  `test_eu15_ruled_coverage.py::test_t05_circulation_zone_has_no_hvac_and_the_ruled_infiltration_rate`,
  `test_eu15_ruled_coverage.py::test_t09_zone_specs_use_stabilized_coords_for_both_dwellings_and_circulation`,
  `test_eu17_relaxed_layout.py::test_t08_multi_storey_building_still_carries_circulation_at_2_plus_dwellings`,
  `test_eu17_relaxed_layout.py::test_t08_named_madrid_building_way_340701289_like_case_loses_its_core`.
- **(b) genuine T03 defect**: none.

Notes: no assertion about the seven checks, `MAX_FLAT_ASPECT`, or dwelling conservation was touched or
loosened anywhere. No debug-reference entry registered — the six new (a) failures were the plan's own
anticipated regime-default breakage (§1, §6 T03), not a novel error with a symptom/cause/fix shape.

#### T05a — the engine's own building-level census (`FINDING 246`) — completed 2026-09-03

Artifacts: `scripts/eu21/10_engine_census.py` (new);
`openubem/outputs/eu_evidence/EU-21/engine_parity/engine_census_2026-09-03.json`.

Deviations: none from §6 T05a. `cut_storey_nocore` called directly (never
`generate_european_nocore_storey_layout`), single-threaded (no `--jobs`, not
specified by the plan), `M07.load_universe()` loaded once for `geoms`+`rows`
(same read-only pattern as `09_engine_parity.py`).

Test status — gate met in every district (`EMITTED + REFUSED_K_GT_12 + FALLBACK ==
census_rows`):
```
ES-MAD-BERRUGUETE       census 961  · EMITTED 905  · REFUSED_K_GT_12  9 · FALLBACK  47 · r5_pass 916  · delta  -11 · multi_k 524  · changed_side 11
FR-LYO-HAUTCOEURPENTES  census 297  · EMITTED 280  · REFUSED_K_GT_12  3 · FALLBACK  14 · r5_pass 281  · delta   -1 · multi_k 184  · changed_side  1
GB-LDN-STDUNSTANS       census  82  · EMITTED  62  · REFUSED_K_GT_12 13 · FALLBACK   7 · r5_pass  71  · delta   -9 · multi_k  68  · changed_side  9
IT-BOL-GALVANI2         census 1204 · EMITTED 1032 · REFUSED_K_GT_12  0 · FALLBACK 172 · r5_pass 1085 · delta  -53 · multi_k 1038 · changed_side 53
FLEET                   census 2544 · EMITTED 2279 · REFUSED_K_GT_12 25 · FALLBACK 240 · r5_pass 2353 · delta  -74 · multi_k 1814 · changed_side 74
wall time 2288.3 s
```
`multi_k` (buildings cut at >1 distinct storey count) reproduces `FINDING 246`'s own
figures exactly (524/184/68/1038, fleet 1814/2544 = 71.3%) — an internal cross-check,
not re-derived independently. `delta` = `EMITTED - r5_pass`, always negative: some
plates `_r5` passed at its single census `k` fail the engine at the *second* distinct
per-storey count the building also carries (sample, Madrid `way/286685222`: `_r5 k=6`
PASS, engine counts `[5,6]`, `k=5` FAILs one check → whole building FALLBACK). Per
§6 T05a step 5, nothing was changed to close this gap — the delta is reported, not
resolved. Engine `REFUSED_K_GT_12` (25) is not directly comparable to `_r5`'s own
"refused, k>12" count (15, Facts §5.8): the census attempts a cut at k>12 and only
marks `REFUSED_K_GT_12` if that attempt also fails (`08_district_viewer.py:165-180`,
`D-EU-92`); the engine refuses outright at the caller level whenever any per-storey
count exceeds 12 (`european_residential.py:2657`, no attempt made), so the two
"refused" sets are built by different rules and are not set-equal — reported as
measured, not reconciled.

#### T05 — rebuild the four districts' IDFs through the engine — executor's entry — 2026-09-03

> 🔴 **Director's audit of this entry: its measurements are sound and none is retracted, but its conclusion is
> not accepted and `CP-2` is NOT signed.** The entry treats
> `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` as a known convention inherited from the delivered
> build (see its dwelling-conservation bullet) and therefore reports the gate-2 gap as **−17**. It never
> compares the *rate*: the reroute fires **1,306** times here against **2** fleet-wide in the delivered
> core-era build, and each firing discards the dwelling layout. Counted that way the emitted set contains
> **956** real layouts, not 2,262 — fewer than the delivered build's 1,446. See the director's own `T05`
> entry below and `STATE` §3 `FINDING 249`. Nothing was submitted to Speed.

Artifacts: `openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE_nocore_2026-09-03/`,
`.../FR-LYO-HAUTCOEURPENTES_nocore_2026-09-03/`, `.../GB-LDN-STDUNSTANS_nocore_2026-09-03/`,
`.../IT-BOL-GALVANI2_nocore_2026-09-03/` (each: `idfs/`, `weather/`, `schedules/`,
`prepared_buildings.csv`, `<slug>_manifest.csv`, `fleet.lst`, `summary.json` — new
directories, `D-EU-85`, existing `EU-11/<DISTRICT>/` untouched);
`openubem/outputs/eu_evidence/EU-21/engine_parity/idf_audit_2026-09-03.json`.

Deviations: none from §6 T05's own instructions (no new CLI flags; `--out` pointed at
the four new suffixed directories). The audit itself was computed by a throwaway
script kept outside the repo (scratchpad, not named in plan §3) and only its result
JSON was written to the named `engine_parity/` output path.

Test status:
```
                          idfs  circ  emitted(prep) t05a_EMITTED delta  massing  gross==cond   conservation  diff(arch/type/age)  only_old  idf_asm_failed  mapping(new/old)
ES-MAD-BERRUGUETE         952    0        896            905     -9       56      896/896        20/20            0/952             9        RuntimeError:9   233/233 match
FR-LYO-HAUTCOEURPENTES    293    0        276            280     -4       17      276/276         20/20            0/293             4        RuntimeError:4   233/233 match
GB-LDN-STDUNSTANS          82    0         62             62      0       20       62/62          20/20             0/82             0        {}                1160/1160 match
IT-BOL-GALVANI2           1200   0       1028           1032     -4      172    1028/1028         20/20            0/1200            4        RuntimeError:4   16/16 match
FLEET                     2527   0       2262           2279    -17      265    2262/2262         80/80            0/2527           17        (17 total)        —
```
- **Zero `_circulation` zones** in all 2,527 IDFs, all four districts (`CP-2` gate 1, met).
- **`DWELLING_LAYOUT_EMITTED*` vs `T05a.EMITTED`**: does not land at 0 in any district
  (`CP-2` gate 2) — the gap is exactly and fully explained by a new, previously-absent
  exclusion category, not by any disagreement in the geometry step itself (see below).
- 🔴 **New finding: 17 buildings fleet-wide (Madrid 9 · Lyon 4 · Bologna 4 · London 0)
  hit `IDF_ASSEMBLY_FAILED_RuntimeError` and got no IDF at all**, a category that was
  `{}` in every delivered core-era build (`prerun_blocker_exclusions`, confirmed from
  each old `summary.json`). This is the caught-exception safety net at
  `run_eu_s2_district_campaign.py:434`, downstream of `_geometry()`'s own layout call —
  the no-core cutter itself already succeeded (these buildings are `T05a.EMITTED`);
  geomeppy's later full IDF assembly then raised on them. `delta_census_scoped_minus_t05a`
  equals `-idf_assembly_failed_total` exactly in every district (9/4/0/4), so the
  identity gap has one fully-identified cause, not an unexplained residual. Not
  investigated further or fixed — out of `T05`'s scope, reported per the plan's own
  "Why" instruction ("that is new and must be reported, not absorbed").
- **Mapping-stage exclusions (archetype/EPC/census-section, excludes the new
  `IDF_ASSEMBLY_FAILED_*`) are identical old vs new in every district**: Madrid 233/233,
  Lyon 233/233, London 1160/1160, Bologna 16/16. For Bologna specifically this is the
  live-API drift check (`T05` step 3): the ISTAT/CTC data returned the same exclusion
  counts on rebuild as it did for the delivered build.
- **`prepared_buildings.csv` diff, old vs new, all four districts**: 0 mismatches on
  `archetype_id`/`building_type`/`age_band` across all 2,527 building_ids common to
  both; only `geometry_outcome`/`idf_sha256` differ (as permitted). 17 building_ids
  present in old only (exactly the new `IDF_ASSEMBLY_FAILED_RuntimeError` set); 0
  present in new only.
- **Dwelling conservation sample, 20 `EMITTED` buildings per district (80 total),
  20/20 every district**, once the sample is restricted to buildings whose actual IDF
  carries `_dwelling_` zones. `geometry_outcome == "DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED"`
  (pre-existing, `FINDING 210`, `run_eu_s2_district_campaign.py:387-392`) starts with
  `"DWELLING_LAYOUT_EMITTED"` but its own zones are the `one_zone_per_floor` massing
  route (geomeppy's `intersect_match` failed and rerouted after the layout step
  already succeeded) — excluded from this specific sample as out of scope for it
  (still counted inside the `DWELLING_LAYOUT_EMITTED*` prefix bucket everywhere else,
  same convention the delivered core-era build already used). The expected total per
  sampled building was recomputed by replaying `run_eu_s2_district_campaign.py`'s own
  `_geometry()` dwellings-value derivation (`_mapped_rows`/`_gb_rows` for ES/FR/GB,
  local only; `_it_rows` for Bologna, same live call `T05` step 1 already made, no
  extra network beyond it) — `EU-20/morphology_census.csv`'s own `dwellings_total` was
  tried first and rejected as ground truth: it is a *different*, historically-sourced
  number (`eu20_morphology_atlas.py:149-154`, read from the delivered build's own
  sidecars) that disagrees with the campaign's live `observed_dwellings`/imputed count
  on buildings where the two provenances diverge.
- **Gross == conditioned area for every `EMITTED` building: 2,262/2,262 (100%)**,
  fleet-wide — the arithmetic proof no circulation area was carved anywhere,
  unaffected by the `INTERZONE_MISMATCH_REROUTED` cases (massing-box zones carry no
  circulation concept either, so gross==conditioned holds there too, trivially).

Notes: two bugs caught and fixed in the (out-of-repo, scratchpad-only) audit script
before trusting its output — neither is a project/engine defect, so neither is
registered in the debug-reference doc: (1) an unanchored zone-name regex
(`\S+_F\d+_dwelling_\d+,\s*!- Name`) also matched the IDF's own
`HVACTemplate:Zone:*` object names (`EU_ConstantAir_<stem>_F..._dwelling_...`,
`EU_HeatOnly_<stem>_F..._dwelling_...`), inflating the dwelling-zone count 3x —
fixed by anchoring to the specific building's own `stem` prefix; (2) the first
conservation-sample pass used census `dwellings_total` as "expected", which is not
always the number the campaign actually used (see above) — fixed by re-deriving the
true value from the campaign's own code path.

---

#### T05a — director's addendum to the entry above (same task, same run, no second execution)

Written independently by the director while the executor's entry was being appended; kept because it carries
the §6 deviation the executor's entry does not. The two describe **one** run of `10_engine_census.py` and
report identical numbers.

Artifacts: `scripts/eu21/10_engine_census.py` (201 lines, new),
`openubem/outputs/eu_evidence/EU-21/engine_parity/engine_census_2026-09-03.json`.
Wall time 2,288.3 s over all 2,544 census rows. Nothing was regenerated: the four `_r5` district JSONs
were read as a read-only oracle (`D-EU-85`), and no `_r5` artifact, no check, no `k` and no threshold
was touched.

Result — the engine's own building-level outcome, **reported beside `_r5`'s per-plate `PASS`, never in
place of it** (§6 T05a step 4):

| district | census rows | `EMITTED` | `REFUSED_K_GT_12` | `FALLBACK` | `_r5` `PASS` | delta | multi-`k` |
|---|---|---|---|---|---|---|---|
| ES-MAD-BERRUGUETE | 961 | 905 | 9 | 47 | 916 | **−11** | 524 |
| FR-LYO-HAUTCOEURPENTES | 297 | 280 | 3 | 14 | 281 | **−1** | 184 |
| GB-LDN-STDUNSTANS | 82 | 62 | 13 | 7 | 71 | **−9** | 68 |
| IT-BOL-GALVANI2 | 1,204 | 1,032 | 0 | 172 | 1,085 | **−53** | 1,038 |
| **fleet** | **2,544** | **2,279 (89.6 %)** | **25** | **240** | **2,353 (92.5 %)** | **−74** | **1,814** |

Test status — the §6 T05a invariant `EMITTED + REFUSED_K_GT_12 + FALLBACK == census_rows` holds in every
district and at fleet level (961 · 297 · 82 · 1,204 · 2,544). The script has no pass/fail threshold of
its own; it is a measurement.

The delta is **one-directional**. All 74 buildings that changed side moved from `_r5` `PASS` to a
non-emitting engine outcome — 65 to `FALLBACK`, 9 to `REFUSED_K_GT_12`. **Not one building moved the
other way**: the engine's per-storey allocation is strictly harder than the census's single
`k = round(dwellings_total / storeys)`, exactly as `FINDING 246` predicted, and now quantified —
**2.9 points of the fleet, 92.5 % → 89.6 %**.

Failing checks across the 240 `FALLBACK` buildings (counted per failing distinct count, so a building
with two failing counts contributes twice):

| district | `C1` | `C3` | `C4` | `C5` | `C6` | `C10` | `C11` |
|---|---|---|---|---|---|---|---|
| ES-MAD-BERRUGUETE | 0 | 0 | 2 | 6 | 3 | 34 | 16 |
| FR-LYO-HAUTCOEURPENTES | 0 | 0 | 1 | 7 | 1 | 6 | 7 |
| GB-LDN-STDUNSTANS | 0 | 0 | 0 | 0 | 0 | 7 | 3 |
| IT-BOL-GALVANI2 | 0 | 0 | 15 | 43 | 11 | 50 | 143 |

`C1` and `C3` never fail — coverage and flat count are always satisfied at the engine's counts. The
residual is `C11` (169) and `C10` (97), i.e. the *second*, off-by-one dwelling count on a plate whose
first count passes. This is the signature of the engine cutting the same plate at both `q` and `q + 1`.

Deviations: one. §6 T05a's "Why" estimated that the `> 12` refusal "barely moves — **2 buildings**
fleet-wide, both Madrid". Measured, **9** buildings moved from `_r5` `PASS` to `REFUSED_K_GT_12`
(Madrid 9 · Lyon 3 · London 13 · Bologna 0 are the *totals* per district; the 9 are the ones that
changed side). The estimate was low; the measured figure stands and the estimate is superseded. Nothing
was changed to reconcile them (§6 T05a step 5).

Notes for `CP-2`: `FALLBACK` here means only that at least one distinct per-storey count fails the seven
checks — it does **not** say which route `generate_european_building_dwelling_layout` then takes for that
building. **240 buildings fleet-wide take that route, 172 of them in Bologna.** The zero-`*_circulation`
assertion in T05's IDF audit is what settles whether any of them lands back in a core-and-corridor
layout; `EMITTED` (2,279), not `_r5`'s `PASS` (2,353), is the oracle the IDF route counts are audited
against. No debug-reference entry registered — no error occurred.

#### T05 — rebuild the four districts' IDFs and audit them — `CP-2` **FAILED** — 2026-09-03

**Artifacts.** `openubem/outputs/eu_evidence/EU-11/<DISTRICT>_nocore_2026-09-03/` for all four districts
(`idfs/`, `schedules/`, `weather/`, `<slug>_manifest.csv`, `fleet.lst`, `prepared_buildings.csv`,
`summary.json`) — Madrid 21:16, London 21:22, Lyon 21:27, Bologna 21:54. Audit output as required by §6 T05
step 4: `openubem/outputs/eu_evidence/EU-21/engine_parity/idf_audit_2026-09-03.json`.

**Verdict: `CP-2` is not signed.** Four of the five gates pass exactly; the fifth — that the emitted IDFs
actually carry the no-core dwelling layouts — fails on **1,306 of 2,262** emitted-family buildings. Full
record in `STATE_european_locations_v5.md` §3 as **`FINDING 249`**. Nothing was submitted to Speed; no
`sbatch` was issued; the queue is untouched. `D-EU-98` clause 2 governs.

**Gate results.**

| gate (§6 T05 / §7 `CP-2`) | result |
|---|---|
| 🔴 zero `*_circulation` zones in every `idfs/` tree | **PASS** — 0 in all four districts |
| route counts == `T05a`'s `EMITTED` (`FINDING 246`) | **PASS** — fleet 2,279 = 2,279, exact per district |
| `conditioned_floor_area_m2 == floor_area_m2` for every `EMITTED` | **PASS** — 2,262 of 2,262, worst rel. dev. 0.0000 |
| old-vs-new diff: `archetype_id` / `building_type` / `age_band` identical row for row | **PASS** — 0 / 0 / 0 on 2,527 common rows, no new building |
| the dwelling layout is actually written into the IDF | 🔴 **FAIL** — `FINDING 249` |

**Route identity, per district** (`real + rerouted + IDF_ASSEMBLY_FAILED` vs `T05a`'s `EMITTED`):
Madrid 278+618+9 = 905 · Lyon 157+119+4 = 280 · London 22+40+0 = 62 · Bologna 499+529+4 = 1032.
Fallback 56+17+20+172 = **265** = `T05a`'s `REFUSED_K_GT_12` 25 + `FALLBACK` 240.

**The failure.** `FINDING 210`'s reroute safety net
(`_force_reroute_room_layout_to_one_zone_per_floor`, `scripts/run_eu_s2_campaign.py::build_idf_for_building`)
fires on **1,306** buildings against **2** in the delivered core-era build, because geomeppy's
`intersect_match` cannot resolve interzone vertex mismatches on the finer no-core subdivision. Each time it
fires the dwelling layout is discarded and the building becomes one whole-building zone per storey, while
`geometry_outcome` still reads `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED`. Real dwelling layouts:
delivered **1,446** → rebuilt **956**, i.e. **−490**, even though `FALLBACK` collapsed 1,096 → 265 (the
extracted cutter divides 831 plates the core-era logic refused). Confirmed by counting zones in 32 sampled
IDFs: rerouted buildings carry only `_F<n>_whole`, zero `_dwelling_` zones.

**Deviations from §6.** (1) §6 T05 assumed the audit's risk was the 240 `FALLBACK` buildings writing a
corridor zone; none did — the failure came from the `EMITTED` side instead, via the `FINDING 210` gate the
plan did not anticipate firing at scale. (2) §6 T05 did not budget for `IDF_ASSEMBLY_FAILED_RuntimeError`;
**17** buildings (Madrid 9, Lyon 4, Bologna 4) get no IDF at all where the delivered build lost none, so the
prepared rows are 2,527, not 2,544. (3) T06 was not started — see the verdict.

**Test status.** No new tests. The audit is measurement over the delivered trees; every number above is
recomputed in `idf_audit_2026-09-03.json` from `prepared_buildings.csv` + `summary.json` + the IDFs
themselves, never from an agent's report.

**Notes.** No threshold was moved, `NEAR_DUPLICATE_VERTEX_TOLERANCE_M` was not relaxed, `MAX_FLAT_ASPECT` is
still 2.5, and nothing under `EU-17/` or `EU-20/` was touched. `FINDING 210` already exists in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1791` and was searched before this audit began; its entry
is extended rather than duplicated once the root cause is found — no new entry is registered here, because
nothing has been fixed yet.
