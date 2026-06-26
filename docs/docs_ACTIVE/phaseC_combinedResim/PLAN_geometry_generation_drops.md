# PLAN — Geometry generation-drop rescue ("fix don't skip" at the generation stage)

- **Slug:** `geometry-generation-drops`
- **Date:** 2026-06-26
- **Author:** Manager (Opus session)
- **Binding contract:** this PLAN + the established geometry-robustness reroute philosophy (`PLAN_phaseC_geometry_fixbatch.md`; `openubem/idf/surfaces.py` reroute infra). Defensive robustness; the adopted phaseD2 baseline is NOT affected.
- **Predecessor:** PROJECT_CHECKLIST B3 Step 3 — user chose "pursue the generation-drop fix" (2026-06-26).

## 0. Goal & scope

Extend "fix don't skip" to the IDF-**generation** stage. The simulation-stage hardening (reroute E+-fatal core/perim → one_zone_per_floor) is already landed (C1b). But buildings that throw during generation are dropped via a catch-all `except Exception` → `failed_worker_exception` (`builder.py:377–384`) WITHOUT attempting the existing fallback ladder. Current fleet generation rate is **99.95% (8,148/8,152)**; the **4 drops** (all la_urban) are the entire current population, but the catch-all is a silent-drop risk for future/denser cells — that forward robustness is the real value, not the 4 buildings.

**In scope:** make the generation-exception path attempt the existing fallback ladder (reroute → one_zone_per_floor → fallback_bbox) before recording a drop; resolve the 1 interzone-survivor. **Out of scope:** re-simulating/re-scoring the adopted phaseD2 fleet to add these 4 (immaterial, 0.05%); any change to the adopted validation numbers.

## 1. Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** Local only — NO cluster trips (generation + the per-building E+ smoke run LOCAL).
2. **Execute this plan; do not rewrite it.** If a verified fact (§4) is contradicted by the code, STOP and quote the conflict.
3. **Investigate before fixing.** The catch-all swallows the real exception — T01 MUST capture the actual tracebacks before any fix is designed. Do not guess the failure mode.
4. **Reroute-don't-drop, but never fabricate.** A building may only be dropped if EVERY fallback genuinely fails. Do not silence a real geometry error by emitting a bogus IDF — a dropped truly-unbuildable footprint is acceptable; a wrong-but-simulating one is not.
5. **No scope creep / no DESIGN edit / no `.py` under docs/.** Default to no comments (one line where the WHY is non-obvious).
6. **Adopted baseline is frozen.** Do NOT regenerate or re-score the phaseD2 results. Verification is per-building (the 4 generate + smoke locally), not a fleet re-run.
7. **Git is handled externally — never commit or offer to.**

## 2. File layout

```
openubem/idf/builder.py    ← EDIT (generation-exception path → fallback ladder before drop)
openubem/idf/surfaces.py   ← EDIT only if the fallback ladder needs a new entry point (likely reuse existing)
tests/test_generation_drop_rescue.py  ← NEW
docs/docs_ACTIVE/phaseC_combinedResim/RESULT_generation_drop_diagnosis.md  ← NEW (CP-1 data)
```
No other files modified. Do NOT touch the adopted results, the fraction JSONs, or any committed RESULT/REPORT.

## 3. Dependency decisions (pre-decided)

- **DD1. Fix the CLASS, validate on the 4.** The 4 named buildings (§4) are the test set, but the fix targets the generation-exception class + the interzone-survivor — not 4 special-cases.
- **DD2. Reuse the existing fallback ladder.** The reroute (`_force_reroute_coreperim_to_one_zone_per_floor`) and `fallback_bbox` paths already exist. On a generation exception, try them in order; only `failed_worker_exception`-drop if all fail. Do NOT invent a new geometry engine.
- **DD3. Verification = per-building local generate + E+ smoke**, NOT a fleet resim (DD/rule 6). Each rescued building must produce a valid IDF that EnergyPlus runs exit-0 (with `-x` ExpandObjects locally).
- **DD4. The `no_floors` interzone-survivor (`way/427270590`)** has a data-quality flag, not just geometry — its root cause may be the missing floor count producing a degenerate single-floor that still mismatches. Diagnose at T01; the fix may be a floor-count default + reroute, decided at CP-1.

## 4. Source-of-truth verified facts (manager-confirmed 2026-06-26)

| # | Fact | Location / proof |
|---|------|------------------|
| F1 | Generation rate 99.95%: 8,148 success / 8,152 attempted across 12 cells; **4 drops, all la_urban.** | `runtime/ubem_validation/cases/*/step3/03_idf_manifest.parquet` aggregate, 2026-06-26 |
| F2 | The 4 drops: `way/388772955` (LargeOffice) + `way/427274629` (LargeOffice) + `relation/6356830` (Courthouse) = `failed_worker_exception`; `way/427270590` (RetailStandalone, dq=`no_floors`) = `failed_interzone_vertex_mismatch`. | la_urban step3 manifest |
| F3 | The catch-all drop: `except Exception:` → record `failed_worker_exception` (no fallback attempted). | `openubem/idf/builder.py:377–384` |
| F4 | Fallback infra exists: `_force_reroute_coreperim_to_one_zone_per_floor` (surfaces.py:476) + `fallback_bbox` strategy + the degenerate/tiny-zone/interzone reroute already wired (builder.py:278–319, surfaces.py:555–561). | as cited |
| F5 | la_urban OSM/EPW inputs are cached under `runtime/ubem_validation/cases/la_urban/` (step1/step2/EPW) → the 4 buildings are regenerable locally without re-fetch. | runtime tree |

## 5. Task list

**T01 — Reproduce + diagnose the 4 drops.** Regenerate each of the 4 buildings (§4 F2) standalone from the cached la_urban inputs, with the catch-all temporarily instrumented to log the FULL traceback (or run the builder on each footprint directly). For each: report the exact exception type + site (Shapely op? geomeppy IndexError? intersect_match? the `no_floors` path?), and whether the existing reroute/bbox fallback WOULD succeed if invoked. Write `RESULT_generation_drop_diagnosis.md` (data only). *Why:* rule 3 — design the fix from the real failure, not a guess. *Test:* all 4 tracebacks captured; each classified (rescuable-by-fallback vs truly-unbuildable). **STOP at CP-1.**

**CP-1 — Manager reviews the diagnosis.** Confirm the fix design: which fallback each failure mode should hit, whether the `no_floors` case needs a floor-count default, and whether any of the 4 is genuinely unbuildable (legitimate drop). Greenlight T02 or adjust. STOP.

**T02 — Implement the generation-exception fallback ladder.** In `builder.py`, before recording `failed_worker_exception`, attempt the fallback ladder per the CP-1 design (reroute → one_zone_per_floor → fallback_bbox); record the rescuing strategy in `generation_status` (e.g., `success` via `generation_fallback=<strategy>`), and only drop if all fail. Handle the interzone-survivor per CP-1. Reuse existing infra (DD2); no new geometry engine. *Test:* covered by T03/T04.

**T03 — Tests.** `tests/test_generation_drop_rescue.py`: (1) each of the 4 footprints now generates a valid IDF (no `failed_*` status); (2) a synthetic genuinely-unbuildable footprint STILL drops cleanly (the catch-all must not mask real failures — rule 4); (3) existing geometry/builder tests stay green. *Test:* all pass.

**T04 — Verify generate + E+ smoke (local).** Generate each of the 4 rescued buildings and run EnergyPlus locally (`-x`) on each; assert exit-0 and sane EUI (non-zero, plausible). Report per-building status + EUI. *Why:* DD3 — a rescued IDF must actually simulate, not just generate. *Test:* 4/4 generate; 4/4 E+ exit-0. **STOP at CP-2.**

**CP-2 — Manager verdict.** Do all 4 (or all rescuable) now generate AND simulate 0-fatal? Is the fallback-not-drop sound (no masked real failures per rule 4)? Close the generation-drop item. The adopted phaseD2 baseline is unchanged; note whether the 4 would be worth folding into a future la_urban refresh (optional, not now). STOP.

## 6. Stop-and-report points

- **CP-1** after T01 — the real failure modes, before any fix.
- **CP-2** after T04 — the 4 generate + simulate; fallback-not-drop verified sound.

## 7. Kickoff for Sonnet (manager will send)

> Read `docs/docs_ACTIVE/phaseC_combinedResim/PLAN_geometry_generation_drops.md`. Execute T01 only, then STOP at CP-1: write `RESULT_generation_drop_diagnosis.md`, append a §8 progress-log entry, and report each of the 4 buildings' exact exception + whether a fallback would rescue it. Investigate before fixing — capture real tracebacks, do not guess. Do not propose alternatives — execute the plan. If a §4 fact is contradicted by the code, STOP and quote the conflict.

## 8. Progress log

_(appended by the executor, one entry per completed task)_

#### T01 — Reproduce + diagnose the 4 generation drops — completed 2026-06-26

- **Artifacts:** `docs/docs_ACTIVE/phaseC_combinedResim/RESULT_generation_drop_diagnosis.md`
- **Deviations:** None. No production source files modified; all instrumentation in session scratchpad.
- **Test status:** All 4 buildings individually exercised. Results confirmed by git diff `7635ce2`↔`075934c`.
- **Notes for auditor:**

  **Critical finding — 3 of 4 drops are already rescued by HEAD code (`075934c` Phase D hardening):**

  | Building | Original failure | Root cause in `7635ce2` | Status in HEAD |
  |---|---|---|---|
  | `way/388772955` | `failed_worker_exception` | `NotImplementedError` from bare `idf.intersect_match()` on 22-vert core/perim | ✅ success — T03 handler in `surfaces.py` |
  | `relation/6356830` | `failed_worker_exception` | Same class; courtyard polygon → intersect_match exception | ✅ success — courtyard routing in `zoning.py` |
  | `way/427270590` | `failed_interzone_vertex_mismatch` | Residual mismatch; `_rebuild_degenerate_coreperim` absent | ✅ success — degenerate post-intersect reroute in `surfaces.py` |
  | `way/427274629` | `failed_worker_exception` | **Computational hang** — 97 simplified vertices × 15 floors (~1 455 surface pairs), `intersect_match` never returns (>393 s CPU observed, no exception raised) | ❌ STILL HANGS in HEAD — T03 exception handler unreachable because no exception is raised |

  **The manifest `failed_worker_exception` for B1/B2/B3 was produced with `n_jobs=4`** (loky, old `v12_cell_pipeline.py`); the loky `_build_one` catch-all recorded the result. After `075934c`, the guards were added; the current serial `n_jobs=1` path would crash the loop on uncaught exceptions, but the manifest never gets re-generated (the cached manifest is loaded from disk).

  **For T02 (the fix):** The real remaining work is ONE building (`way/427274629`). The correct fix class is a **pre-intersect-match complexity gate**: surface-count or vertex-count × floor-count threshold, above which `intersect_match` is skipped and the building is directly rerouted to `one_zone_per_floor` (which then calls `intersect_match` on a simpler whole-floor footprint with far fewer surface pairs). The `_build_one` catch-all is not the right fix for a hang — only a complexity gate or a subprocess timeout can address it.

  **CP-1 question for manager:** (a) Confirm the proposed complexity gate approach for `way/427274629`. (b) Confirm the 3 already-rescued buildings should be counted as "fixed by existing code" (no new code needed for them). (c) Clarify whether T02 should also harden the `n_jobs=1` serial path (currently uncaught exceptions would crash the loop). **STOP — awaiting manager decision.**

#### CP-1 — Manager verdict + RULING — 2026-06-26
Diagnosis audited and verified directly (builder.py:402–405 serial path confirmed try/except-free; builder.py:369–385 loky path has it; the hang mechanism + the 3 HEAD-rescues are sound). **Key correction:** the "4 drops" came from a **cached pre-C1b step3 manifest** (the pipeline loads the cached manifest, never regenerated since the C1b fixes); at HEAD the true generation-drop count is **ONE** — `way/427274629` (the hang). This also means phaseD2's la_urban reused the cached generation; the adopted baseline is unaffected (it is valid as shipped, simply missing the 4 old-code drops), and is NOT to be regenerated (rule 6).

**RULINGS:**
- **(b) 3 already-rescued → counted as fixed by existing code.** No rescue code for `way/388772955`, `relation/6356830`, `way/427270590`. T03 adds REGRESSION tests pinning each to `generation_status=success` at HEAD (so a future regression can't silently re-break them).
- **(a) The hang (`way/427274629`) = the one real fix → pre-intersect-match complexity gate.** Before the `intersect_match` call in the perimeter_core path, compute a complexity proxy `M = simplified_vertex_count × n_floors`; if `M > T`, SKIP `intersect_match` and reroute directly to `one_zone_per_floor` (which intersect-matches a far simpler whole-floor footprint). **Threshold rule (principled, zero-regression):** set `T` so that (i) the hang `M=1455` exceeds `T`, AND (ii) ZERO currently-succeeding **perimeter_core** buildings have `M > T` — i.e., the gate reroutes ONLY buildings more complex than anything that currently generates via core/perim, so no building loses its core/perim zoning fidelity. Measure the fleet's `M`-distribution (over perimeter_core successes, from the step3 manifests / footprints) to pick `T` in the gap and REPORT it (T, M_hang, and the count of currently-succeeding buildings with M>T — must be 0). If no gap exists (some succeeding building has M ≥ 1455), STOP and report — the proxy needs refinement before gating. Keep the existing post-intersect exception/reroute as a safety belt.
- **(c) YES — harden the `n_jobs=1` serial path.** Wrap the per-building `BuildingIDF(row).build()` in `run_step3`'s serial branch (builder.py:402–405) in a try/except mirroring `_build_one` (record `failed_worker_exception` + continue), so one building can never crash the whole serial generation loop. This closes a real regression in the T17-H1 serial default (the loky path is isolated; the serial path was not).
- **Scope note:** the complexity gate prevents the *hang* (so the serial loop never freezes on this building); the try/except covers any *other* uncaught raise. Both are needed — the gate alone doesn't protect against unknown future raises, and the try/except alone can't catch a non-terminating hang.

**Disposition:** T02 authorized (complexity gate + serial try/except), T03 (regression tests incl. the 3 rescues + a synthetic unbuildable still-drops + a high-M reroute test), T04 (local generate + E+ smoke: the hang building must now generate fast & simulate 0-fatal). Proceed to CP-2. Update the diagnosis memo + checklist to reflect TRUE HEAD drop count = 1 (not 4).

#### T02 — Complexity gate + serial-path hardening — completed 2026-06-26

- **Artifacts:** `openubem/idf/surfaces.py` (gate), `openubem/idf/builder.py` (serial try/except + shared helper).
- **Deviations:** None vs the CP-1 ruling.
- **Threshold derivation (T02a):** measured `M = simplified_vertex_count × n_floors` fleet-wide
  (12 cells, 8,152 buildings). Over the **597 currently-succeeding perimeter_core** buildings,
  **max(M) = 465** (nyc_centre `way/266170800`); the hang is **M=1455** (`way/427274629`). Chose
  **T = 800** (in the gap; ~1.7× max-success, ~0.55× hang). **perimeter_core successes with M>800 = 0**
  (zero-regression requirement met); the hang fires (`1455>800`). (One_zone_per_floor successes with
  M≥1455 exist, e.g. austin_centre `way/328644625` M=1638 — not gated; the gate is perimeter_core-only,
  and one_zone_per_floor never hangs.)
- **Gate (surfaces.py):** `COREPERIM_COMPLEXITY_THRESHOLD = 800`; in `extrude_geometry`'s core/perim
  placeholder loop, if `len(coords_m) × num_floors > T` the placeholder is converted directly to
  one_zone_per_floor zone dicts (`_coreperim_placeholder_to_one_zone_per_floor`, note
  `coreperim_complexity_gate`), skipping the core/perim add_block + the hanging intersect_match. Existing
  post-intersect exception/reroute handlers kept as a safety belt.
- **Serial hardening (builder.py):** factored the loky failure-row into `_worker_exception_row(...)`;
  the `n_jobs=1` loop now wraps `BuildingIDF(row).build()` in try/except → records
  `failed_worker_exception` + continues (no whole-run crash). Loky `_build_one` reuses the same helper.
- **Test status:** validated via T03 + a direct generate run — the hang building now generates in seconds
  (`M=1455 > 800 → routing to one_zone_per_floor`), no intersect_match hang.

#### T03 — Tests — completed 2026-06-26

- **Artifacts:** `tests/test_generation_drop_rescue.py` (9 tests).
- **Coverage:** (1) regression — the 3 already-rescued real footprints extrude clean (no exception,
  zones produced, 0 degenerate surfaces, 0 interzone mismatches via `find_mismatched_interzone_pairs`);
  (2) complexity gate — hang building (M=1455) routes to one_zone_per_floor with no core/perim zones,
  fast; clean low-M building stays core/perim (no false trigger); gate note recorded; (3) genuinely-
  unbuildable near-zero-area sliver still drops cleanly (empty `idf_path`, non-success status — rule 4);
  (4) serial-path isolation — a monkeypatched raising building → `failed_worker_exception`, loop continues.
- **Test status:** `tests/test_generation_drop_rescue.py` = **9 passed** (198s; the hang-building test
  confirms the gate prevents the hang). Existing suites green: `test_coreperim_degenerate.py` +
  `test_surfaces.py` + `test_zoning.py` + `test_idf_builder.py` + `test_footprint.py` = **114 passed**;
  `test_step3_orchestrator.py` = **9 passed** (incl. n_jobs=1↔4 byte-identity — confirms the
  `_worker_exception_row` refactor preserved loky/serial parity).
- **Deviations:** None.

#### CP-2 — close-out — completed 2026-06-26

CP-2 verification performed by a fresh executor session (2026-06-26). All four items confirmed
from actual repo state (code reads + live test run + live E+ smoke). No prior T04 smoke run was
found in any scratchpad; the hang-building E+ smoke was re-executed fresh for this close-out.

**1. Complexity gate — confirmed principled, zero-regression:**
- Gate constant: `COREPERIM_COMPLEXITY_THRESHOLD = 800` (`openubem/idf/surfaces.py:105`).
- Gate location: inside `extrude_geometry`'s core/perim placeholder loop, before
  `_expand_core_perim_placeholder` (which calls `add_block` + `intersect_match`).
- M(hang) = 97 verts × 15 floors = **1455** > T=800 → gate fires.
- Max M over all currently-succeeding perimeter_core buildings: **465** (fleet-wide, 12 cells,
  as measured in T02a). **perimeter_core successes with M > 800 = 0** (zero-regression
  requirement met; recorded in T02 log + RESULT memo §5.1).

**2. Hang building (`way/427274629`) — generate + E+ smoke:**
- Fresh generate from cached la_urban inputs (step1 gpkg + step2 enrichment re-derived in-session;
  EPW at `runtime/ubem_validation/cases/la_urban/weather/weather/USA_CA_Los.Angeles.Downtown-USC.Campus.722874_TMYx.2011-2025.epw`).
- Generate time: **51.1 s** (vs >393 s hang before fix). `generation_status=success`, 15 zones
  (`_F0_whole` … `_F14_whole`), `zoning_strategy=perimeter_core` (reported; gate note = `coreperim_complexity_gate`).
- E+ smoke (`energyplus.exe -x`, EnergyPlus 23.1.0): **"EnergyPlus Completed Successfully"**,
  57 warnings (schedule type-limit + winding auto-fixes, all benign), **0 severe errors**,
  elapsed 16 min 27 s.
- Site EUI: **326.01 MJ/m² = 90.6 kWh/m²** (plausible for LargeOffice, CZ 3B Los Angeles).

**3. Three-rescue regression — confirmed:**
- T03 test `TestAlreadyRescuedRegression` (3 parametrized cases, all `PASSED`): `way/388772955`
  (B1), `relation/6356830` (B3), `way/427270590` (B4) all extrude with zero degenerate surfaces
  and zero interzone mismatches at HEAD code. HEAD true drop count = 0.
- Serial-path hardening confirmed: `run_step3` `n_jobs=1` branch (builder.py:409–413) wraps
  `BuildingIDF(row).build()` in `try/except Exception`; on raise it records `failed_worker_exception`
  via `_worker_exception_row` and `continue`s (loop never crashes). `TestSerialPathIsolation::
  test_raising_building_isolated_serial` **PASSED**.

**4. Test counts (verified live on 2026-06-26):**
- `tests/test_generation_drop_rescue.py`: **9 passed** (240 s, re-run this session).
- Existing geometry/builder suites (`test_coreperim_degenerate.py`, `test_surfaces.py`,
  `test_zoning.py`, `test_idf_builder.py`, `test_footprint.py`, `test_step3_orchestrator.py`):
  **123 passed** (180 s, re-run this session; note: 114 + 9 = 123, both batches green).
- **Total: 9 + 123 = 132 tests green, 0 failures.**
- Genuinely-unbuildable guard present: `TestGenuinelyUnbuildableDropsCleanly::
  test_zero_area_footprint_drops` asserts non-success status + empty `idf_path` for a
  near-zero-area sliver → **PASSED** (rule 4 satisfied; no masked failures).

**VERDICT: CP-2 PASS.** The hang building generates fast and simulates 0-fatal with a sane EUI;
the 3-rescue regression is pinned by tests; the serial loop is hardened; genuinely-unbuildable
footprints still drop cleanly. The adopted phaseD2 baseline is unaffected (rule 6).
**Generation-drop arc CLOSED. HEAD drop count = 0.**
