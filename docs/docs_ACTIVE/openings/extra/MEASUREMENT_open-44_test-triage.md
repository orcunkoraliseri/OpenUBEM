# MEASUREMENT — OPEN-44: triage of the 106 failing/erroring tests

**Task:** T05, `PLAN_rulings-and-five-items-2026-08-12.md`
**Date:** 2026-08-12
**Scope:** every failing/erroring node across `tests/`, `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/`,
and `scripts/analysis/test_viewer_layout_assign.py` — 106 nodes total (§4.4's 70 failed + 36 errored).

## Runs (both foreground, both captured before any other executor touched a test file)

1. `python -m pytest -q -p no:cacheprovider tests/ --tb=short` → `openubem/outputs/comparisons/open44_tests_run.txt`.
   **25 failed, 1788 passed, 10 skipped, 19 errors in 1093.97s (18m14s).** 44 failing/erroring nodes.
2. `python -m pytest -q -p no:cacheprovider "docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/" "scripts/analysis/test_viewer_layout_assign.py" --tb=short` → `openubem/outputs/comparisons/open44_docs_scripts_run.txt`.
   **45 failed, 34 passed, 17 errors in 17.19s.** 62 failing/erroring nodes.

Run (1) was scoped to `tests/` per the task's explicit command and is the ~25-minute run; run (2) covers the
other two trees named in the CSV's `tree` column and in T05 step 5, and was fast (~17s). Combined: **106**,
matching §4.4 exactly (44 in `tests/`, 61 in the elevators tree, 1 in `scripts/analysis/`).

## CSV

`openubem/outputs/comparisons/open44_test_triage.csv` — one row per node, columns
`nodeid, tree, category, evidence, likely_source_line`. **106 data rows, verified by script (`len(rows)==106`
asserted).** Breakdown by tree: `tests/` 44, `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/` 61,
`scripts/analysis/` 1 — sums to 106.

## Category counts

| category | count |
|---|---|
| `artifact-missing` | 65 |
| `tests-for-code-that-never-existed` | 21 |
| `fixture-wiring` | 17 |
| `stale-expectation` | 2 |
| `REAL-DEFECT` | 1 |
| `UNTRIAGED` | 0 |

## The one REAL-DEFECT, named individually

`scripts/analysis/test_viewer_layout_assign.py::test_layout_assign_idf_ingestion` — `NameError: name
'zones_found' is not defined` at line 24. The file prints `zones_found` at
`print(f"Zones found in geometry ({len(zones_found)}):", ...)` but that name is never assigned anywhere in
the file — read in full, confirmed. It also hardcodes an absolute path into another task's scratchpad
(`scratchpad/t19_t01_t05_work/...`), so even fixing the `NameError` would not make this test portable. This
is a leftover debug script, not a regression in shipped `openubem/` code — the defect is in the test file
itself, not in `openubem/viz/geometry_extract.py`, `cityjson_emitter.py`, or `viewer_export.py`, which the
test actually calls without incident (the ingestion succeeds — see the captured stdout — the crash is only
in the debug print after that).

## `tests-for-code-that-never-existed` (21) — two distinct features, not one

**A. `IMPUTE_DEBIAS_NEWERSKEW` (5, all in `tests/test_debias.py`).** `AttributeError: module
'openubem.config' has no attribute 'IMPUTE_DEBIAS_NEWERSKEW'`. This is the exact symptom named in §4.5 of
the plan as the reason T08 exists — T08 will do the git-history proof; this task only establishes the
category and evidence.

**B. The elevator EUI breakout (16: 8 in `tests/test_parser_elevators.py`, 8 in the byte-identical
`docs/.../test_parser_elevators.py`).** `KeyError: 'elevators_eui_kwh_m2'` / `KeyError:
'Elevators:InteriorEquipment:Electricity'`. Confirmed by grep: neither string appears anywhere in
`openubem/results/parser.py` (`_compute_eui`, `_parse_meters_sql`, `_failed_row` — none of the three emit an
elevator breakout). This is a second, independent instance of the T07/T08 pattern (tests committed for a
feature that was never shipped), and it is **live**, not archived — it fails in `tests/`, not just in
`docs/`.

## `fixture-wiring` (17) — the `synthetic_10_gdf` question, resolved

All 17 are `ERROR at setup` in `docs/.../test_step3_orchestrator.py`: `fixture 'synthetic_10_gdf' not
found`. Root cause, confirmed directly:

- `tests/fixtures/synthetic_10_buildings.py` defines `synthetic_10_gdf` and `synthetic_schedule_library`
  as `@pytest.fixture(scope="session")` functions (lines 125, 167).
- `tests/conftest.py` imports both and re-exports via `__all__` — this is a normal, working pattern
  (confirmed live: `pytest tests/test_step3_orchestrator.py --fixtures` lists both fixtures correctly).
- `docs/docs_DONE/LOADS & SCHEDULES/elevators/scripts/tests/` **has no `conftest.py` of its own** (confirmed:
  `find` for `conftest.py` under that `scripts/` tree returns nothing). Pytest fixture visibility is scoped
  to the directory tree containing the defining/importing `conftest.py` and its subdirectories — a test file
  living outside that tree cannot see the fixture no matter how the fixture itself is defined.

**This is a wiring problem, not a missing file, exactly as §4.4 flagged.** The one-line fix (not applied,
per T05's scope) would be adding a `conftest.py` under the elevators `scripts/tests/` directory that imports
the same fixtures, or deleting the archived duplicate. Neither is this task's decision.

Two further `docs/.../test_step3_orchestrator.py` nodes are NOT this cause — `test_load_conservation_
across_modes` and `test_load_conservation_across_modes_multifloor` build their row dict directly (no
fixture) and fail with `ValueError: epw_path '...scripts/tests/fixtures/synthetic.epw' is missing or does
not exist`. Confirmed: `docs/.../elevators/scripts/tests/fixtures/` does not exist at all (the archived
mirror never carried a `fixtures/` subfolder). Categorized `artifact-missing`, not `fixture-wiring`.

## `artifact-missing` (65)

Three clusters:

- **26** in `tests/test_v19_basis_diagnostic.py` + `tests/test_v19_national_cbecs_rescore.py`: every one is
  a `FileNotFoundError`/`OSError`/`AssertionError` rooted in `docs/docs_DONE/phaseC_combinedResim/
  v19_validation/` **not existing locally at all** (confirmed: `ls` on that path fails). These tests both
  read and write into that directory; none of it survives on this machine.
- **5** in `tests/test_impute_montage.py`: `phase_A folder has zero PNGs`, `PLAN_input_imputation_
  implementation.md` not found beside `OUT_DIR` — source figures were never generated locally.
- **34** in the elevators tree: the archived `docs/.../scripts/openubem/` mirror is missing files its own
  tests need — `openubem/data/openstudio_archetypes.json` (1 node) and `openubem/idf/templates/
  commercial_base.idf` (all of `test_elevators.py`'s remaining 23 nodes and 8 of `test_outputs.py`'s 10
  nodes), plus the 2 `test_step3_orchestrator.py` epw-path nodes above. Confirmed by `find`: neither file
  exists anywhere under that archived `scripts/openubem/` tree.

None of these indicate broken shipped code — they indicate output directories or archived sibling files
that don't exist on this machine. Per hard rule 8, that is the cause, not a count.

## `stale-expectation` (2)

Both in `docs/.../test_outputs.py`: `test_hvac_meters_count` (`assert len(HVAC_METERS) == 14`, actual 13)
and `test_hvac_meters_phase_e_required` (an `issubset` check requiring `'Elevators:InteriorEquipment:
Electricity'`). Proof this is drift, not a live defect: the **live** twin `tests/test_outputs.py:81` asserts
`len(HVAC_METERS) == 13` against the same live `openubem/idf/outputs.py:28-42` (13 entries, no elevator
meter) — **and passes**. The archived copy was never updated after the live meter count changed.

## The 61 `docs/` failures — duplicates, drift, and what the drift is (files not touched)

Per §4.4, `docs/` holds 5 test files with `tests/` counterparts. Byte-for-byte `cmp`: **2 identical, 3
drifted** (this matches §4.4's count exactly).

**Identical:** `test_elevators.py`, `test_parser_elevators.py`.

**Drifted, and the drift is the same story in all three cases — the live `tests/` versions had elevator-
breakout expectations removed, while the archived `docs/` versions still have them** (confirmed with
`diff -b`, which ignores the CRLF-vs-LF line-ending difference that otherwise makes every line look
changed):

1. **`test_outputs.py`** — archived expects `len(HVAC_METERS) == 14` and an elevator meter in the required
   subset; live expects `== 13` and drops the elevator meter from the requirement (see `stale-expectation`
   above).
2. **`test_results_aggregator.py`** — archived's expected-row dicts include `elevators_eui_kwh_m2` and
   `gwp_elevators_kgco2_m2`; live's dicts (both the all-NaN template near line 63-70 and the populated rows
   near line 87-97) have both keys removed. This file did not fail in either run (both versions currently
   pass) — it is drift without breakage, because neither version's assertions currently touch the removed
   keys' absence.
3. **`test_step3_orchestrator.py`** — archived has one extra test, `test_medium_office_idf_contains_
   elevator_equipment` (asserts a `MediumOffice` IDF carries one `ELECTRICEQUIPMENT` object with
   `EndUse_Subcategory == "Elevators"`); live does not have this test at all — it was deleted, not just
   edited.

**Reading across all five files:** whoever last touched `tests/` tried to quiet the elevator-breakout
failures by removing or downgrading the assertions in three of five files, but missed
`test_parser_elevators.py` (still asserts `elevators_eui_kwh_m2` / the elevator meter, still fails live) and
never touched `openubem/results/parser.py` or `openubem/idf/outputs.py` to add the feature. No files under
`docs/` were modified, moved, or deleted to establish this — only read and `diff`'d.

## What T05 did not do

Did not fix `synthetic_10_gdf` wiring, did not implement the elevator breakout, did not implement
`IMPUTE_DEBIAS_NEWERSKEW`, did not regenerate any missing artifact, did not touch any file under
`docs/`, did not run the whole repo (only the three trees named in §4.4's breakdown). OPEN-44 does not
close on this pass, per §7 of the plan.
