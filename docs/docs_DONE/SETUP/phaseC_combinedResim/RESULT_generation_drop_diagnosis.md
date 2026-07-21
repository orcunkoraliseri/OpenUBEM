# RESULT — Generation-Drop Diagnosis (T01) + Fix (T02–T04)

- **Date:** 2026-06-26
- **Author:** Sonnet executor
- **Plan:** `PLAN_geometry_generation_drops.md`
- **Stop point:** CP-2 (diagnosis + fix landed; manager writes verdict)

> **TRUE HEAD generation-drop count = 1, not 4.** The "4 drops" in the la_urban
> step3 manifest came from a **cached pre-C1b manifest** (commit `7635ce2` code; the
> pipeline loads the cached manifest and never regenerated it after the Phase D / C1b
> geometry guards landed in `075934c`). At HEAD, 3 of the 4 are already rescued by
> existing code; only `way/427274629` (the computational hang) was a real HEAD drop —
> now fixed by the complexity gate (T02a). The adopted phaseD2 baseline reused the
> cached generation and is unaffected (valid as shipped; NOT regenerated, rule 6).

---

## 1. Context: why the manifest shows `failed_worker_exception`

The la_urban fleet was generated via `v12_cell_pipeline.py` with `n_jobs=4` (commit `7635ce2`).
The `_build_one` loky worker wraps each call in `except Exception` → `failed_worker_exception`.
That catch-all was the only exception handler in the generation path at the time of the run.

Between `7635ce2` (la_urban fleet) and `075934c` (Phase D, current HEAD), `openubem/idf/surfaces.py`
received three new guards:
1. **T03 `intersect_match` exception wrapper** — wraps `idf.intersect_match()` in try/except, rerouting
   on `IndexError` / any Exception to `one_zone_per_floor`.
2. **`_rebuild_degenerate_coreperim`** — post-intersect degenerate surface detector + reroute.
3. **`_coreperim_has_degenerate_surfaces` / `_coreperim_has_tiny_zone_area` helpers** used by (2).

These guards are what makes 3 of the 4 buildings succeed in the current code.

---

## 2. Per-building diagnosis

### B1: `way/388772955` — LargeOffice, 4 floors, 22 vertices

| Field | Value |
|---|---|
| Archetype | LargeOffice |
| Raw geometry | Polygon, 22 exterior vertices, area 3703.84 m², valid |
| Simplified | dp_05 → 22 vertices |
| Derived floors | 4 (from `levels=4`) |
| Zoning strategy | perimeter_core |
| `data_quality_flag` | (empty) |

**Original failure (commit 7635ce2):**
`idf.intersect_match()` was called bare (no try/except). A core/perim 22-vertex polygon raised
`NotImplementedError` inside geomeppy's `break_polygons` path. The exception propagated out of
`extrude_geometry`, was caught by `_build_one`'s `except Exception`, logged (truncated to −300 chars),
and recorded as `failed_worker_exception`.

**Current code (HEAD):**
The T03 `intersect_match` exception wrapper catches `NotImplementedError`, calls
`_force_reroute_coreperim_to_one_zone_per_floor`, which succeeds (4 whole-floor zones created).
IDF generates with `generation_status=success`, `zoning_strategy=perimeter_core` (reported),
`data_quality_flag=narrow_perimeter_fallback`.

**Rescuable?** YES — **already rescued by existing code at HEAD**. The T03 intersect_match handler
(added in `075934c`) is the fix. No further change needed for this building.

---

### B2: `way/427274629` — LargeOffice, 15 floors, 113 raw / 97 simplified vertices

| Field | Value |
|---|---|
| Archetype | LargeOffice |
| Raw geometry | Polygon, 113 exterior vertices, area 1868.78 m², valid |
| Simplified | dp_05 → 97 vertices (still above 80; geomeppy warns `>120 vertices` on surface count) |
| Derived floors | 15 (from `height_m=49.8`, `levels=NaN` → `ceil(49.8/3.5)=15`) |
| Zoning strategy | perimeter_core |
| `data_quality_flag` | `generic_tag,no_floors,no_function` |

**Original failure (commit 7635ce2):**
`idf.add_block(zoning='core/perim')` on the 97-vertex footprint succeeded (producing the
`>120 surface vertices` warning), but `idf.intersect_match()` called bare then entered an
O(n²) surface-pair comparison loop that never terminates within any practical wall-clock
budget. The loky worker was killed (timeout / OOM) → `WorkerLostError` caught by joblib,
then by `_build_one`'s `except Exception` → `failed_worker_exception`.

**Current code (HEAD):**
**STILL HANGS.** The T03 wrapper is `except (IndexError, Exception)`, which catches
exceptions — but `intersect_match` does NOT raise here; it simply never returns. The 97-vertex
× 15-floor building produces ~1 455 surface pairs for `intersect_match` to process;
experimentally, the process consumed >393 s of CPU time with no output before being killed.

**Rescuable by existing fallback?** NO — no existing fallback addresses a computational hang
(as opposed to an exception). The `_force_reroute_coreperim_to_one_zone_per_floor` path is
reached only AFTER `intersect_match` raises; since `intersect_match` hangs instead of raising,
the reroute is never triggered.

**Classification:** `genuinely-unbuildable-without-new-handling` — needs a pre-intersect-match
complexity gate (e.g., surface count > threshold → skip `intersect_match`, reroute directly)
or a thread/process timeout around `intersect_match`. The reroute fallback itself (one_zone_per_floor)
would work once triggered; the problem is getting past the hang.

**Note on `no_floors` flag:** The `levels=NaN` → `height_m=49.8` → `ceil(49.8/3.5)=15` derivation
is correct per `derive_num_floors`. The `no_floors` flag is informational (data-quality, not a
defect in the floor-count derivation). The real root cause is complexity (vertices × floors), not
the floor count itself.

---

### B3: `relation/6356830` — Courthouse, 14 floors, 45 raw / 38 simplified vertices

| Field | Value |
|---|---|
| Archetype | Courthouse |
| Raw geometry | Polygon, 45 exterior vertices, area 1935.76 m², valid |
| Simplified | dp_05 → 38 vertices |
| Derived floors | 14 (from `height_m=47.3`, `levels=NaN` → `ceil(47.3/3.5)=14`) |
| Zoning strategy | perimeter_core |
| `data_quality_flag` | `no_floors` |

**Original failure (commit 7635ce2):**
Same class as B1: `intersect_match` raised a geomeppy exception (geometry zoning variant —
the geometry module warning confirms `interior ring (courtyard): perimeter_core → one_zone_per_floor`
fired at the zoning stage). In the old code, `zoning.py` detected the courtyard and attempted
`perimeter_core` anyway; the resulting broken geometry caused an exception inside `intersect_match`
(bare call), caught by `_build_one` → `failed_worker_exception`.

**Current code (HEAD):**
Current `openubem/geometry/zoning.py` already routes interior-ring polygons to `one_zone_per_floor`
before geometry extrusion (the WARNING: `interior ring (courtyard): perimeter_core → one_zone_per_floor`
fires during `build_zones`). IDF generates cleanly: 14 whole-floor zones, no mismatch,
`generation_status=success`.

**Rescuable?** YES — **already rescued by existing code at HEAD**. The courtyard-routing in
`zoning.py` (present in current code) handles this before extrusion. No further change needed.

---

### B4: `way/427270590` — RetailStandalone, 6 floors, 62 raw / 41 simplified vertices

| Field | Value |
|---|---|
| Archetype | RetailStandalone |
| Raw geometry | Polygon, 62 exterior vertices, area 5792.60 m², valid |
| Simplified | dp_05 → 41 vertices |
| Derived floors | 6 (from `height_m=18.6`, `levels=NaN` → `ceil(18.6/3.5)=6`) |
| Zoning strategy | perimeter_core (initial) → one_zone_per_floor (after reroute) |
| `data_quality_flag` | `no_floors` |

**Original failure (commit 7635ce2):**
`intersect_match` succeeded (no exception) but left residual mismatched surface pairs.
The `_repair_mismatched_horizontal_pairs` function existed in the old code and reset the
mismatched floor↔floor pair. However, `_rebuild_degenerate_coreperim` did NOT exist yet.
`find_mismatched_interzone_pairs` was then called (in `builder.py`'s post-extrude gate) and
found remaining mismatch pairs (the degenerate perim wedges that `_repair_mismatched_horizontal_pairs`
reset to exterior, exposing new mismatches). The gate returned `failed_interzone_vertex_mismatch`.

**Current code (HEAD):**
The post-intersect sequence now includes `_rebuild_degenerate_coreperim`, which detects the
degenerate perimeter wedge surfaces and triggers `_force_reroute_coreperim_to_one_zone_per_floor`.
After the reroute, all interzone pairs are clean. `generation_status=success`,
`data_quality_flag=no_floors|narrow_perimeter_fallback`.

**Rescuable?** YES — **already rescued by existing code at HEAD**. The `_rebuild_degenerate_coreperim`
guard (added in `075934c`) handles this. No further change needed.

---

## 3. Summary classification table

| Building | Original status | Exception / failure mode | Root cause (commit 7635ce2) | Status in HEAD code | Rescue needed? |
|---|---|---|---|---|---|
| `way/388772955` (LargeOffice) | `failed_worker_exception` | `NotImplementedError` from `idf.intersect_match()` (core/perim 22-vert polygon) | No intersect_match try/except | **success** (T03 handler) | None — already fixed |
| `way/427274629` (LargeOffice) | `failed_worker_exception` | **Computational hang** — `intersect_match` never returns (97-vert × 15-floor: ~1 455 surface pairs, O(n²), >393 s CPU observed) | No complexity gate before intersect_match | **STILL HANGS** — no exception raised | Yes — new pre-intersect complexity gate needed |
| `relation/6356830` (Courthouse) | `failed_worker_exception` | `NotImplementedError` or geometry exception from `intersect_match` on courtyard polygon | No courtyard → one_zone_per_floor gate in zoning (pre-extrude) | **success** (courtyard route in `zoning.py`) | None — already fixed |
| `way/427270590` (RetailStandalone) | `failed_interzone_vertex_mismatch` | Residual mismatch after `_repair_mismatched_horizontal_pairs`; `_rebuild_degenerate_coreperim` absent | No degenerate post-intersect reroute | **success** (`_rebuild_degenerate_coreperim`) | None — already fixed |

**Net situation:** 3 of 4 drops are **already rescued** by code added in `075934c` (Phase D hardening).
The remaining 1 (`way/427274629`) is a **computational hang** that the existing catch-all cannot reach —
the T03 `intersect_match` exception wrapper is irrelevant because no exception is raised.

---

## 4. Instrumentation note (T01)

No production source file was modified during T01 diagnosis. Diagnosis was performed by:
- Calling `BuildingIDF(row).build()` directly in a standalone script
  (`scratchpad/t01_diagnose_targeted.py`) with per-process timeouts to surface hangs
- Diffing `7635ce2` vs `075934c` to identify which guards were absent at the time of the la_urban run
- Running each building individually to isolate the exception type and hang behavior

All T01 instrumentation lived in the session scratchpad only (not committed, not under `docs/`).

---

## 5. Fix (T02) — complexity gate + serial-path hardening

### 5.1 Empirical threshold derivation (T02a)

Complexity proxy `M = simplified_vertex_count × n_floors`, measured fleet-wide across all
12 cells (8,152 buildings, 597 currently-succeeding **perimeter_core** buildings):

| Quantity | Value |
|---|---|
| max(M) over **perimeter_core successes** | **465** (nyc_centre `way/266170800`, 31 verts × 15 floors) |
| M of the hang (`way/427274629`) | **1455** (97 verts × 15 floors) |
| Gap between max-success and hang | 465 … 1455 — clean, wide |
| Chosen threshold **T** | **800** (≈1.7× the max success, ≈0.55× the hang) |
| perimeter_core successes with M > 800 | **0** ✅ (zero-regression requirement met) |

The hang fires the gate (`1455 > 800`); zero currently-succeeding perimeter_core buildings
are affected. (Note: there exist `one_zone_per_floor` successes with M ≥ 1455, e.g.
austin_centre `way/328644625` M=1638 — but the gate is in the perimeter_core path ONLY;
one_zone_per_floor never hangs, so those are untouched.)

### 5.2 Gate implementation (`openubem/idf/surfaces.py`)

- `COREPERIM_COMPLEXITY_THRESHOLD = 800`.
- In `extrude_geometry`, the core/perim placeholder loop computes `M = len(coords_m) × num_floors`
  for each `mode="core/perim"` placeholder. If `M > T`, the placeholder is converted directly to
  one_zone_per_floor zone dicts (`_coreperim_placeholder_to_one_zone_per_floor`) and the expensive
  `add_block(zoning="core/perim")` + the hanging `intersect_match` on core/perim geometry are skipped.
  `intersect_match` then runs on the simple whole-floor footprint (fast).
- The gated zones carry `generation_status_note="coreperim_complexity_gate"`.
- The existing post-intersect exception/reroute handlers are unchanged (kept as a safety belt).

### 5.3 Serial-path hardening (T02b, `openubem/idf/builder.py`)

- Factored the loky `_build_one` failure-row into a shared `_worker_exception_row(...)` helper.
- The `n_jobs=1` serial loop in `run_step3` now wraps each `BuildingIDF(row).build()` in
  try/except: on exception it records a `failed_worker_exception` manifest row and **continues**
  the loop (one building can no longer crash the whole serial generation). This closes the
  regression in the T17-H1 serial default (the loky path already isolated; the serial path did not).

---

## 6. Updated summary classification table (HEAD + fix)

| Building | Cached-manifest status | HEAD status (pre-fix) | Fix (T02) | HEAD status (post-fix) |
|---|---|---|---|---|
| `way/388772955` (LargeOffice, M=88) | `failed_worker_exception` | success (T03 intersect_match handler) | none needed | **success** |
| `relation/6356830` (Courthouse, M=532) | `failed_worker_exception` | success (courtyard route in `zoning.py`) | none needed | **success** |
| `way/427270590` (RetailStandalone, M=246) | `failed_interzone_vertex_mismatch` | success (`_rebuild_degenerate_coreperim`) | none needed | **success** |
| `way/427274629` (LargeOffice, M=1455) | `failed_worker_exception` | **STILL HANGS** (no exception → reroute unreachable) | **complexity gate (T02a)** | **success** (gate → one_zone_per_floor, fast) |

**TRUE HEAD generation-drop count BEFORE fix = 1** (`way/427274629`). **AFTER fix = 0.**

---

## 7. Verification (T03 + T04)

### 7.1 Tests — `tests/test_generation_drop_rescue.py` (9 tests, all pass)

1. Regression — the 3 already-rescued real footprints extrude clean (no exception, zones produced,
   zero degenerate surfaces, zero interzone mismatches).
2. Complexity gate — the hang building (M=1455) routes to one_zone_per_floor without building any
   core/perim zones, fast (no hang); a clean low-M building stays core/perim (no false trigger);
   the gate note is recorded.
3. Genuinely-unbuildable footprint (near-zero-area sliver) still drops cleanly — empty `idf_path`,
   non-success status (rule 4 — no fabricated IDF).
4. Serial-path isolation — a monkeypatched raising building is recorded `failed_worker_exception`
   and the n_jobs=1 loop continues (all 3 rows recorded).

Existing suites green: `test_coreperim_degenerate.py` + `test_surfaces.py` + `test_zoning.py` +
`test_idf_builder.py` + `test_footprint.py` = 114 passed; `test_step3_orchestrator.py` = 9 passed
(incl. n_jobs=1↔4 byte-identity, confirming the `_worker_exception_row` refactor preserved parity).

### 7.2 E+ smoke (local, `energyplus -x`)

Hang building smoke run executed 2026-06-26 by the CP-2 close-out executor (EnergyPlus 23.1.0-87ed9199d4):

| Building | Generate time (s) | E+ result | Severe errors | Site EUI (kWh/m²) |
|---|---|---|---|---|
| `way/427274629` (LargeOffice, M=1455, 15 floors, CZ 3B) | **51.1** | EnergyPlus Completed Successfully | **0** | **90.6** |

Warnings (57): schedule type-limit validation (benign — no ScheduleTypeLimits objects in the base template) + floor/ceiling winding auto-fixes (standard for geomeppy-generated whole-floor zones). All auto-corrected by E+; no geometry fatal.

The 3 already-rescued buildings (B1/B3/B4) were smoke-run by the prior T04 executor:

| Building | Site EUI (kWh/m²) | E+ result |
|---|---|---|
| `way/388772955` (LargeOffice, 4 fl, CZ 3B) | 86.3 | Completed Successfully, 0 severe |
| `relation/6356830` (Courthouse, 14 fl, CZ 3B) | 84.6 | Completed Successfully, 0 severe |
| `way/427270590` (RetailStandalone, 6 fl, CZ 3B) | 133.1 | Completed Successfully, 0 severe |

**All 4 generate + simulate 0-fatal with plausible EUI.** T04 COMPLETE.

---

## 8. Instrumentation cleanup

No instrumentation remains in production source. All T01 diagnosis + T04 smoke scripts live in the
session scratchpad only. The only production edits are the T02 fix:
`openubem/idf/surfaces.py` (complexity gate) and `openubem/idf/builder.py` (serial try/except +
shared failure-row helper), plus the new test `tests/test_generation_drop_rescue.py`.
