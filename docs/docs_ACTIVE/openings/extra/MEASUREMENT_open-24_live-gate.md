# MEASUREMENT — open-24-live-gate

> **Slug:** `open-24-live-gate` · **Date:** 2026-08-13 · **Register item:** OPEN-24
> **Task:** T03 of `implemenation/PLAN_five-more-items-2026-08-13.md`. **Measurement only — no code
> changed.** No document was edited except this file.

---

## 1. Verdict

**The gate is not parked. It ran real EnergyPlus 23.1 on this machine, in this session, and 6 of 7
tests passed on real EnergyPlus execution.** The one failure is not an EnergyPlus problem — it is an
IDF-generation/filesystem-race bug in the Step-3 fleet-build path (`openubem/idf/builder.py`), hit
*before* EnergyPlus is ever invoked for that test. The register's current line —
*"partly superseded, not parked"* (`INVESTIGATION_open-items-register.md:658,4088`) — is confirmed and
can be tightened: it is **running, not parked, with one unrelated failure**, not merely "environment-gated."

---

## 2. Binary confirmation

`C:\EnergyPlusV23-1-0\energyplus.exe` exists:

```
$ ls -la "/c/EnergyPlusV23-1-0/energyplus.exe"
-rwxr-xr-x 1 o_iseri 197121 14336 Mar 28 2023 /c/EnergyPlusV23-1-0/energyplus.exe
```

Version, via the exact command `_version_handshake()` runs (`openubem/simulation/runner.py:21-36`,
`subprocess.run([exe, "--version"], ...)`, parsed with `Version\s+([\d.]+)`):

```
$ "/c/EnergyPlusV23-1-0/energyplus.exe" --version
EnergyPlus, Version 23.1.0-87ed9199d4, YMD=2026.08.13 22:38
```

This is a cheap, direct reproduction of the handshake, not a guess — and it is independently confirmed
by `test_version_handshake_real_binary` passing in §3 below (it asserts `ver.startswith("23.1")`).

---

## 3. Pytest run — verbatim

Command run, exactly as pinned:
`./.venv/Scripts/python.exe -m pytest tests/test_sim_integration.py -q -rs --tb=short`

Wall time: **12.67s** (not "several minutes" — see §7, "what I could not determine," for why this may
be lower than expected).

Full output:

```
.F.....                                                                  [100%]
================================== FAILURES ===================================
______________________ test_synthetic_fleet_full_annual _______________________
tests\test_sim_integration.py:110: in test_synthetic_fleet_full_annual
    manifest_03 = _build_step3_fleet(synthetic_10_gdf, synthetic_schedule_library, step3_dir)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\test_sim_integration.py:54: in _build_step3_fleet
    return run_step3(gdf, schedule_library, out_dir)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
openubem\idf\builder.py:706: in run_step3
    manifest_df.to_parquet(output_dir / "03_idf_manifest.parquet", engine="pyarrow", index=False)
.venv\Lib\site-packages\pandas\core\frame.py:3135: in to_parquet
    return to_parquet(
.venv\Lib\site-packages\pandas\io\parquet.py:490: in to_parquet
    impl.write(
.venv\Lib\site-packages\pandas\io\parquet.py:199: in write
    path_or_handle, handles, filesystem = _get_path_or_handle(
.venv\Lib\site-packages\pandas\io\common.py:797: in get_handle
    check_parent_directory(str(handle))
.venv\Lib\site-packages\pandas\io\common.py:656: in check_parent_directory
    raise OSError(rf"Cannot save file into a non-existent directory: '{parent}'")
E   OSError: Cannot save file into a non-existent directory: 'C:\Users\o_iseri\Desktop\OpenUBEM\.pytest_tmp\test_synthetic_fleet_full_annu0\step3'
----------------------------- Captured log setup ------------------------------
WARNING  openubem.geometry:zoning.py:108 osm_id=way/R7 narrow building: perimeter_core \u2192 one_zone_per_floor
---------------------------- Captured stdout call -----------------------------
[hvac] single-zone downgrade: way/R10 archetype=OpenUBEMUnknown 'Packaged VAV w/ Hot Water Reheat' -> 'PSZ-AC w/ Gas Furnace'
------------------------------ Captured log call ------------------------------
WARNING  openubem.geometry:zoning.py:108 osm_id=way/R7 narrow building: perimeter_core \u2192 one_zone_per_floor
ERROR    openubem.idf:builder.py:642 osm_id=way/R7 worker exception: ...eppy\modeleditor.py", line 1046, in save
    with open(filename, "wb") as idf_out:
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\o_iseri\\Desktop\\OpenUBEM\\.pytest_tmp\\test_synthetic_fleet_full_annu0\\step3\\idfs\\way_R7.idf'

ERROR    openubem.idf:builder.py:642 osm_id=way/R8 worker exception: (same FileNotFoundError, way_R8.idf)
ERROR    openubem.idf:builder.py:642 osm_id=way/R9 worker exception: (same FileNotFoundError, way_R9.idf)
WARNING  openubem.idf.hvac:hvac.py:686 single-zone HVAC downgrade: bld=way/R10 archetype=OpenUBEMUnknown 'Packaged VAV w/ Hot Water Reheat' -> 'PSZ-AC w/ Gas Furnace'
ERROR    openubem.idf:builder.py:642 osm_id=way/R10 worker exception: (same FileNotFoundError, way_R10.idf)
1 failed, 6 passed in 12.67s
```

(The four repeated `FileNotFoundError` worker-exception blocks are abbreviated above to their distinct
`osm_id` — the actual captured-log text repeats the full traceback per building; nothing was omitted
from the summary line, the assertion path, or the outer `OSError`.)

**Counts: 1 failed, 6 passed, 0 skipped, 0 errors (outer).** 7 test functions in the file, all
collected, all ran (none skipped — the module-level `pytest.skip(allow_module_level=True)` guard at
`test_sim_integration.py:27-31` did not fire, because the binary is present).

**No skip reasons to report** — `-rs` prints a "short test summary info" section only when at least one
test is skipped; none appeared, consistent with the 1-failed/6-passed/0-skipped count above.

---

## 4. What each test actually exercises (read, not guessed)

| Test | IDF source | Runs real EnergyPlus? | Result |
|---|---|---|---|
| `test_version_handshake_real_binary` | none — `energyplus.exe --version` only | yes (handshake only) | **passed** |
| `test_synthetic_fleet_full_annual` | **Step-3-built IDFs** — `_build_step3_fleet` → `run_step3()` on `synthetic_10_gdf` (`test_sim_integration.py:51-54,107-110`) | no — fails at Step-3 IDF-write, before `run_neighbourhood`/EnergyPlus is reached | **failed** (infra bug, §5) |
| `test_adversarial_corrupted_idf_gives_failed_fatal` | a hand-written minimal IDF string built in the test body (`test_sim_integration.py:212-224`) — not Step-3, not an EnergyPlus example | yes | **passed** |
| `test_adversarial_missing_epw_gives_valueerror` | none — asserts `ValueError` is raised by `build_task_list` before any dispatch | no (by design) | **passed** |
| `test_adversarial_precompleted_work_dir_gives_success_cached` | `tests/fixtures/sim/1zone_with_sql.idf` — a **repo fixture**, confirmed present (`ls`: 20,142 bytes, `Jun 10 18:04`) | yes | **passed** |
| `test_adversarial_timeout_gives_failed_timeout` | `C:\EnergyPlusV23-1-0\ExampleFiles\ASHRAE901_HotelSmall_STD2019_Denver.idf` — a genuine **EnergyPlus-installation example IDF** | yes | **passed** |
| `test_determinism_same_host_reproducible` | `tests/fixtures/sim/1zone_with_sql.idf` — same repo fixture as above | yes | **passed** |

**Network use: none.** The module's only imports are `os, shutil, sqlite3, tempfile, time, pathlib,
geopandas, pandas, pytest`, plus in-repo `openubem.*` modules
(`grep -n "^import\|^from" tests/test_sim_integration.py`). No `requests`, `urllib`, `socket`, or `http`
appear anywhere in the file. Every EPW is read from the local EnergyPlus install
(`C:\EnergyPlusV23-1-0\WeatherData\...`, comment at line 39: *"Real EPW from EnergyPlus installation
(P3: use shipped file, no network)"*), and every IDF is either repo-local, EnergyPlus-install-local, or
built in-memory in the test. **No STOP condition under §1.4 was triggered.**

**Correction to the module docstring's own characterization (§5 below applies here too):** the
docstring (lines 6-8) says tests needing successful runs *"use validated example IDFs from the
EnergyPlus installation."* That is true only for the timeout test (`_HOTEL_IDF`). The cache test
(`test_adversarial_precompleted_work_dir_gives_success_cached`, labelled "T09c cache" in the docstring)
and the determinism test (`test_determinism_same_host_reproducible`, "T09d") both actually use the
**repo's own fixture**, `tests/fixtures/sim/1zone_with_sql.idf` — not an EnergyPlus-installation example.
Functionally this makes no difference (both are valid, successfully-running IDFs), but the docstring's
factual claim about *which* IDFs are used is imprecise for those two tests specifically.

---

## 5. The docstring's stale claim — quoted contradiction

`tests/test_sim_integration.py:2-4` (module docstring):

> "Triage note (P5): Step-3 IDFs all fatal under EnergyPlus 23.1 due to geomeppy surface
> geometry defects (invalid sun_exposure='NoWind', missing vertex_z_coordinate)."

`docs/docs_REPORTS/REPORT_phaseE_final.md:74`:

> "All 12 matrix cells (3 cities × 4 density rings) were re-simulated on Speed SLURM. **8,160 of 8,160
> buildings succeeded (100%).**"

These are a direct contradiction on the fate of Step-3-built IDFs under EnergyPlus 23.1: the test
module's docstring asserts blanket, universal failure ("all fatal"); the Phase-E final report records
zero failures across the entire 8,160-building fleet. **Not edited, per the task's instruction — the
director rules on scope.**

(Distinct from this: `test_synthetic_fleet_full_annual`'s own in-body docstring, lines 103-105, still
describes the same "all fatal" expectation for the *synthetic 10-building* fixture set specifically,
which is a different population from the Phase-E fleet — that narrower claim was not tested here because
the test failed before reaching EnergyPlus, see §6.)

---

## 6. The one failure, in plain terms

`test_synthetic_fleet_full_annual` never reaches EnergyPlus. It fails inside `run_step3()`
(`openubem/idf/builder.py:706`) trying to write `03_idf_manifest.parquet` into
`.pytest_tmp\test_synthetic_fleet_full_annu0\step3`, a directory `to_parquet` reports as
non-existent — even though `run_step3` calls `output_dir.mkdir(parents=True, exist_ok=True)` and
`(output_dir / "idfs").mkdir(exist_ok=True)` at its own top (`builder.py:685-687`). Four of the ten
synthetic buildings (`way/R7`–`way/R10`) hit the same missing-directory `FileNotFoundError` inside
per-building worker exception handling before the outer `to_parquet` call fails outright. This looks
like a race or an environment/tmp-directory issue specific to this pytest session (`pyproject.toml:54`
pins `addopts = "--basetemp=.pytest_tmp"`, a repo-relative directory), not an EnergyPlus defect and not
something covered by the "Step-3 IDFs all fatal" docstring claim — the failure happens before any IDF is
handed to EnergyPlus. **Not diagnosed further and not fixed — out of scope for T03 (§1.4: change no
code).**

---

## 7. What I could not determine

- **Whether the `run_step3` directory failure is a one-off or reproducible.** The task pins a single
  run of the exact command; re-running it to test for flakiness was not part of T03's instructions and
  was not done. The verdict above ("6 passed, 1 failed, real EnergyPlus confirmed live") stands on this
  one run only.
- **Why the run took 12.67s rather than the "several minutes" the plan anticipated.** Plausibly because
  the one test that would have driven the bulk of the wall time — 10 buildings through full annual
  EnergyPlus simulation — never got past IDF generation. The remaining six tests are individually cheap
  (a version handshake, two IDFs that fail/succeed in ~1s, one that asserts before any run, one 1-zone
  SQL IDF run twice, one ~15s hotel IDF killed at a 3s timeout). This is a plausible reconciliation, not
  a measured one.
- **Root cause of the missing `step3` / `step3/idfs` directory at write time**, given the code visibly
  creates it earlier in the same function. Not investigated beyond reading `builder.py:685-687,706` —
  doing so would mean stepping into a debugging task, which is outside T03's "change no code, run the
  gate, report the outcome" mandate.
- **Whether this failure is new or pre-existing** (i.e., whether this test passed the last time anyone
  ran it, and when that was). No prior run log for this specific file was found in `extra/`; the
  register's OPEN-24 entries describe the test as environment-gated and existing, but do not record a
  prior pass/fail outcome for `test_synthetic_fleet_full_annual` specifically.

---

## 8. Artifacts

- This report: `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-24_live-gate.md`.
- No CSV, no code, no other file created or modified. `git status --porcelain` before and after this
  task shows no new/changed paths outside this one report (the pre-existing dirt at
  `tests/fixtures/synthetic_30_archetype_coverage.gpkg`, per §2 of the plan, was not touched).
- `.pytest_tmp/` was inspected read-only after the run (`ls -la .pytest_tmp`) and found empty —
  consistent with `tmp_path_retention_policy = "failed"` / `tmp_path_retention_count = 3`
  (`pyproject.toml:52-54`) not retaining this session's directories, or with the directory never having
  been durably created in the first place. Not resolved either way.
