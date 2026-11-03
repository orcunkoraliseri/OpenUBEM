# PLAN — check the test suite, then register the 28 remaining crashes — 2026-09-30

## 1. Header

- **Slug:** `tests-and-crashes-2026-09-30`
- **Date:** 2026-09-30. **Author:** director (manager session).
- **Authority:** user, 2026-09-30, verbatim: *"oki go with a, continue to the end"*, answering the director's
  recommendation (a): "first check the code's tests, then list the 28 crashes as open items".
- **Pointers:** register `docs/docs_DONE/openings/INVESTIGATION_open-items-register-II.md` (0 live, next
  free OPEN-67 when this plan opened); closed predecessor `implemenation/previous/PLAN_three-rulings-2026-09-30.md`; crash classes in its
  T05 entry and in `openubem/outputs/comparisons/open38_fix_rerun_2026-09-30.csv` (`cause_class`, `terminal`).

## 2. Hard rules for the executor

1. Execute your task only. Do not propose alternatives. If this plan or a cited line is wrong, STOP and quote it.
2. Measure and report; **fix nothing** in T01. No edits to `openubem/`, `tests/` or `scripts/`.
3. At most 10 local worker processes (`-n 8`). No Speed cluster actions.
4. Do not touch any process running `eu_rulebook_dryrun_2026-09-30.py`; it belongs to another project.
5. Append one progress-log entry per task under §8; numbers measured, never estimated.

## 3. File layout

- Suite log: `%TEMP%/suite_2026-09-30.log` (not in the repo).
- No new files in the repo other than this plan's progress log entries.

## 4. Dependency decisions (pinned)

- **D1 — command.** `.venv\Scripts\python.exe -m pytest -q -n 8 tests/ -p no:cacheprovider -rfE`
  (xdist 3.8.0, installed 2026-08-28). One run, foreground or background, no competing pytest run.
- **D2 — baseline.** Last full run 2026-09-09: **2,654 passed / 40 skipped / 25 failed**; the 25 failures live
  in 7 EU-arc files (`implemenation/previous/PLAN_accuracy-restatement-2026-09-09.md:654-661`):
  `tests/test_generation_drop_rescue.py`, `tests/geometry/test_eu14b_bologna_layout_binding.py`,
  `tests/geometry/test_eu15_ruled_coverage.py`, `tests/test_eu18c_viewer_geometry_only.py`,
  `tests/test_eu_observed_archetype_mapping.py`, `tests/test_eu_real_footprint_feasibility.py`,
  `tests/test_eu_s2_campaign_ceiling82.py`.
- **D3 — files this arc changed** (three-rulings plan T02, T06): `openubem/geometry/footprint.py`,
  `openubem/idf/builder.py`, `openubem/idf/cooking.py`, `openubem/results/aggregator.py`,
  `openubem/results/parser.py`, `tests/test_open35_option_a.py`, `tests/test_cooking.py`,
  `tests/test_step3_orchestrator.py`. The working tree also holds other arcs' uncommitted edits
  (`git status --short`), so a new failure is not automatically this arc's.
- **D4 — crash items.** One register item per failure mode (house rule: one entry per failure mode), five items,
  OPEN-67 … OPEN-71: laundry room (7), sliver zone (6), sizing divergence (13), non-convex shading (1),
  out of memory at 32G (1). The 28 runs are 19 buildings; only 6 are outside the adopted 8,139 (corrected
  2026-09-30, see T02 entry). They change no published number.

## 5. Facts with line citations

- Adopted figure 171.38 kWh/m² / 1,146,454 t over 8,139: `openubem/outputs/comparisons/open38_fix_summary_2026-09-30.json`.
- The 28 cases: `open38_fix_rerun_2026-09-30.csv` rows with `group` in (`open38`, `oom`) and `terminal != completed`.
- Debug-reference entries already written: ch. 1 (sliver, non-convex), ch. 2 (laundry, sizing divergence),
  ch. 12 (out of memory) of `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.

## 6. Tasks

### T01 — Full test suite, classified *(executor)*

**What.** Run D1 once. Classify every failing or erroring test by file into: (i) in the D2 list of 7 files;
(ii) new, and the test file or the module it imports is in D3; (iii) new, other.
**Why.** The suite was last run 2026-09-09; three plans changed code since.
**How.** Run D1 with output to the log. Then `grep -E "^(FAILED|ERROR)" <log> | sed 's/::.*//' | sort | uniq -c`.
For each class (ii)/(iii) file: the first assertion or exception line (one line each), and for (ii)
`grep -nE "cooking|footprint|derive_num_floors|parser|aggregator|builder" <test file> | head -5`.
**How to test.** Counts passed / skipped / failed / errors and wall time copied from the log's last line;
per-file failure counts sum to the failed + error total. STOP after T01 and report.

### T02 — Register the 28 crashes *(director)*

**What.** Open OPEN-67 … OPEN-71 per D4: §1 current-state row, §2 rows, §6 item section, §7 entry; debug
reference §18 table; director prompt box; both boards; memory. Each row names its cases (osm_id, cell,
mode) from the CSV and links its debug-reference entry.
**How to test.** Register counts add up (live + retired = total, next free ID) in every place that states them.

### T03 — Act on T01 *(director, after CP-1)*

**What.** Class (i): nothing. Class (ii): a fix task for a fresh executor, written here. Class (iii): one
register item per failure mode if no other arc's plan owns it.

### T04 — Update the stale golden answers for building R1 *(executor, written at CP-1)*

**What.** Make the 8 class (ii) tests pass by correcting the test answers only, not the code.
**Why.** Since 2026-09-25 (commit `84832042`, "FLEET-06c-FIX") `resolve_simulated_floor_area()` in
`openubem/results/parser.py` takes the floor area from the SQL `Zones` table (`"sql_simulated"`). The golden
file `tests/fixtures/golden_sql/r1_single_zone.sql` holds one 196 m² zone, while `golden_expected.json` R1 was
computed on 392 m² (196 × 2 floors). Measured 2026-09-30: `parse_building()` on R1 returns
`floor_area_m2 = 196.0`, `floor_area_provenance = sql_simulated`, heating 335.7026 = 2 × 167.8513. The
three-rulings edit of `_derive_num_floors_wired` is not the cause (R1 has `levels = 2`, which wins either way).
**How.** Edit `tests/fixtures/golden_sql/golden_expected.json` only, block `R1`: `floor_area_m2` → `196.0`; every
value under `eui` and `gwp` → old value × 392 / 196 (exactly × 2); append to `R1.description` the sentence
"Floor area is the SQL simulated area (one 196 m2 zone) since FLEET-06c-FIX, 2026-09-25." Leave `R2`, `R6`,
`iod`, `iod_token`, `provenance` and every file under `openubem/` untouched.
**How to test.** `.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests/test_results_parser.py
tests/test_results_carbon.py tests/test_parser_open61_district_heating.py` → 0 failed. Then
`git diff --stat` shows `golden_expected.json` as the only changed test file. Register the fix in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (chapter on results parsing), house format. STOP and report.

## 7. Stop-and-report points

- **CP-1 (director)** after T01: audit the classification; write T03.
- **CP-2 (director)** after T04: audit the diff and the three test files.

## 8. Progress log

#### T02 — Register the 28 crashes — completed 2026-09-30

- **Artifacts:** register §1 current-state row (5 live / 66 retired / 71 total, next free OPEN-72), §2 rows
  OPEN-67 … OPEN-71, §6 section "OPEN-67 … OPEN-71 — OPENED 2026-09-30 (night)", §7 entry; debug reference
  §18 table (5 live) and the five `[OPEN]` entries (ch. 1, 2, 12); director prompt START HERE box; `MEMORY.md`,
  `project_current_baseline.md`. Boards: done with T03 so they change once.
- **Deviations:** D4 said the 28 are "outside the adopted 8,139". Wrong: the 28 runs are 19 buildings; 13 crash
  only in the diagnostic modes and their production (`auto`) result is in the figure. Only 6 buildings are
  missing from the 8,139 (5 la_rural Warehouses — OPEN-69 ×4, OPEN-70 ×1 — and la_centre `way/319507579`,
  OPEN-71). OPEN-69 is 13 runs over 7 buildings, not 9. Corrected in register, director prompt, debug
  reference, both board sources and memory.
- **Test status:** counts agree (5 + 66 = 71; next free OPEN-72) in register §1/§2, debug reference §18,
  director prompt and `MEMORY.md`.
- **Notes:** no published number changes.

#### T01 — Full test suite, classified — completed 2026-09-30

- **Artifacts:** suite log `%TEMP%/suite_2026-09-30.log` (outside the repo). No repo file changed except this entry.
- **Deviations:** none. D1 run once, `-n 8`.
- **Test status:** last line: `40 failed, 2757 passed, 111 skipped, 1343 warnings, 4 errors in 4437.99s (1:13:57)`. Per-file counts sum to 44 = 40 failed + 4 errors. Baseline 2026-09-09 was 2,654 / 40 / 25.
  - **(i) in the D2 list, 24 failures, 6 of the 7 files:** `tests/test_eu18c_viewer_geometry_only.py` 12, `tests/test_eu_s2_campaign_ceiling82.py` 4, `tests/geometry/test_eu14b_bologna_layout_binding.py` 3, `tests/test_eu_observed_archetype_mapping.py` 2, `tests/test_eu_real_footprint_feasibility.py` 2, `tests/geometry/test_eu15_ruled_coverage.py` 1. `tests/test_generation_drop_rescue.py` no longer fails.
  - **(ii) new, in D3, 8 failures (parser doubles heating):** `tests/test_results_parser.py` 4 and `tests/test_results_carbon.py` 3 (R1 golden heating EUI got 335.70, expected 167.85, exactly 2x; GWP heating 70.22 vs 35.11), `tests/test_parser_open61_district_heating.py` 1 (same 335.70 vs 167.85). Grep hits in these files are only `openubem.results.parser` imports and `footprint_area_m2` fields.
  - **(iii) new, other, 12 failures:** `tests/test_pv_injection.py` 6 and `tests/test_scenario_campaign_wiring.py` 4 errors (`FileNotFoundError` for `C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231\ASHRAE901_OfficeMedium_STD2022_Buffalo.idf`, a missing external file); `tests/test_prep_gate.py` 1 (`config.PREP_ABORT_ON_FAILURE` is True, test expects False); `tests/test_sim_parallel.py` 1 (`PrepPhaseFailedError: 1 building(s) failed IDF generation before simulation: ['C']`).
- **Notes:** class (i) also carries new kinds of assertion text (for example `test_t02_one_sidecar_per_simulated_building` 1204 vs 1201), same files as D2. Working tree holds other arcs' edits, so (ii) cause (parser heating 2x) is not yet tied to this arc's change. Nothing fixed.

#### T03 — Act on T01 — completed 2026-09-30

- **Artifacts:** T04 written in §6; register items OPEN-72 and OPEN-73 (§1 row, §2 rows, §6 section, §7
  entry); debug reference §18 and two `[OPEN]` entries; director prompt box; both boards; memory.
- **Deviations:** the T01 executor's first report came back empty; the director classified from the log, then the
  executor's own entry arrived with the same numbers, which the director audited (CP-1): 24 + 8 + 12 = 44 =
  40 failed + 4 errors. Class (ii) is in a D3 file but not caused by this arc: the cause is the SQL floor-area
  source added 2026-09-25 (`84832042`), see T04. Every class (iii) cause is also a TechTransfer commit; that arc
  is closed (docs in `docs/docs_DONE/TechTransfer/`), so no other plan owns them and they are registered here.
- **Test status:** class (i) 24 in 6 of the 7 D2 files, nothing to do (EU arc). Class (ii) 8 → T04. Class (iii):
  OPEN-72 = 10 tests (`test_pv_injection.py` 6, `test_scenario_campaign_wiring.py` 4) need
  `C:\Users\o_iseri\Desktop\idf_reader\Content\00.BaselineBuildings_NUs_v231\`, which no longer exists
  on this machine; OPEN-73 = 2 tests (`test_prep_gate.py` 1, `test_sim_parallel.py` 1) fail because
  `openubem/config.py:123` has `PREP_ABORT_ON_FAILURE = True` (set in `ab4d7707`, 2026-09-18) while the TechTransfer
  block-2 plan (`docs/docs_DONE/TechTransfer/implementation/PLAN_techtransfer-block2-2026-09-17.md:159`) and the
  tests say `False`; with `True` the deliberately broken test building "C" stops the whole run.
- **Notes:** no published number moves: T04 changes test answers only, and OPEN-72/73 change nothing in the
  code that produced 171.38 kWh/m² / 8,139. OPEN-73 is not fixed here because the flag changes how production runs react
  to a failed building; that is a choice for its owner.

#### T04 — Update the stale golden answers for building R1 — completed 2026-09-30

- **Artifacts:** `tests/fixtures/golden_sql/golden_expected.json` (block `R1` only: `floor_area_m2` 196.0, all `eui` and `gwp` values x2, description sentence appended); one bullet in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` ch. 8 (line 1349).
- **Deviations:** none. The description sentence follows a period added after "footprint)" so the text reads as two sentences.
- **Test status:** `pytest -q -p no:cacheprovider tests/test_results_parser.py tests/test_results_carbon.py tests/test_parser_open61_district_heating.py` -> 81 passed, 0 failed. `git diff --stat` on the json: 1 file changed, 12 insertions(+), 12 deletions(-).
- **Notes:** nothing under `openubem/` touched; R2, R6, iod, iod_token, provenance unchanged.

#### CP-2 — director audit of T04 — 2026-09-30

- `git diff` on `tests/fixtures/golden_sql/golden_expected.json`: 12 lines changed, all in `R1` (description,
  `floor_area_m2` 392 → 196, 5 EUI and 5 GWP values × 2). No file under `openubem/` changed by T04.
- Debug reference ch. 8 bullet present (line 1349). **Plan complete:** T01–T04 done; 32 red tests remain
  (24 EU-arc, 10 OPEN-72, 2 OPEN-73); register 7 live / 66 retired / 73 total, next free OPEN-74.
