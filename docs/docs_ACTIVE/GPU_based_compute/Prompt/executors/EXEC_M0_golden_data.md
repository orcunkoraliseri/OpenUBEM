# EXEC M0 — gpusim golden data, licence file and timing pair

## 1. Header
- **Slug:** `gpusim-M0`. **Date:** 2026-11-22. **Approved by owner:** D3 (2026-11-22).
- **Owner rule (2026-11-22): M0 and M1 run entirely on this Mac.** No Speed cluster (no access now). The simulation count is kept small: 3 golden cells + 10 variants = 13 runs, plus the 6-run timing pair.
- **Owner ruling D6 (2026-11-22, after CP1):** Mac E+ gives +0.66 % more heating than the published Windows values on identical inputs (spec §9). The golden reference is the Mac E+ output. Published values are recorded in `meta.json`, never gated.
- **Spec (the DESIGN for this work):** `docs/docs_ACTIVE/GPU_based_compute/BUILD_SPEC_gpu_heat_balance_engine.md` rev. 3: §1, §4, §5 row M0, §6.
- **Executor:** a Gemini session with repo access, run by the owner. **NO sub-agents.**
- **Kickoff (paste into the executor session):**
  ```
  Read /Users/orcunkoraliseri/Desktop/OpenUBEM/docs/docs_ACTIVE/GPU_based_compute/Prompt/executors/EXEC_M0_golden_data.md.
  Execute T01 through T03 in order. Stop at checkpoint CP1, append one progress-log entry per
  completed task under §8 of that file, run the tests the tasks call for, and report results before continuing.
  Do not propose alternatives — execute the plan. If the spec is ambiguous, STOP and quote the conflict.
  ```
  After the manager audits CP1, the owner sends the "Next kickoff" below.
- **Next kickoff (T04 size stop audited 2026-11-22: all 13 runs pass, size gate raised to 300 MB, fixtures stay local):**
  ```
  Read /Users/orcunkoraliseri/Desktop/OpenUBEM/docs/docs_ACTIVE/GPU_based_compute/Prompt/executors/EXEC_M0_golden_data.md again (T04 size gate changed).
  Do not re-run any E+ run or redo T01–T04. Execute T05. If every CP2 check passes, write the CP2 report into the progress log
  and go straight on: read /Users/orcunkoraliseri/Desktop/OpenUBEM/docs/docs_ACTIVE/GPU_based_compute/Prompt/executors/EXEC_M1_stageA_numpy_s0.md
  and follow its §1 kickoff (T01 through T06, report at CP4). STOP only if a test or gate fails, the spec is ambiguous,
  or the E+ source disagrees with the spec; then quote the problem and wait.
  Do not propose alternatives — execute the plan.
  ```

## 2. Hard rules for the executor
1. Execute the tasks in order. Do not write plans, do not redesign, do not "improve" the spec. If something does not work as written, STOP and quote the problem.
2. Touch only the files listed in §3. Never edit `openubem/campaign/`, `openubem/idf/`, `docs/docs_main/`, `docs/docs_stepN/`, `docs/docs_VALIDATION/`, root `main.py`, or anything under `openubem/outputs/eu_certified_rerun_2026-08-28/` (read only).
3. **EnergyPlus runs, all local on this Mac:** the timing pair in T03 runs one at a time with nothing else heavy running. The 13 golden runs in T04 run as one local process pool of **at most 4 E+ processes at once** (the owner keeps working on this machine). No loop of one run after another, no Speed cluster.
4. No code comments. Python env is `uv`; tests run with `pytest` (testpaths = `tests`).
5. Do not commit. Do not push. Do not install new dependencies (pandas, numpy, pyarrow are already in `pyproject.toml`).
6. Report numbers you measured, with the command that produced them. Never write "verified" without the value.
7. Paths in this file are relative to the repo root `/Users/orcunkoraliseri/Desktop/OpenUBEM/`.

## 3. File layout (only these may be created or changed)
```
openubem/gpusim/__init__.py                 (empty)
openubem/gpusim/LICENSE-ENERGYPLUS          (T01)
scripts/gpusim/make_golden.py               (T02, T04)
scripts/gpusim/time_pair.py                 (T03)
openubem/outputs/gpusim_golden_runs/        (T02: run folders + run_list.txt; T03: timing folders)
openubem/outputs/gpusim_m0_timing.csv       (T03)
tests/fixtures/gpusim/golden/<cell_id>/     (T04: Parquet + copies of inputs + meta.json)
tests/fixtures/gpusim/golden/variants/       (T04: 10 variants)
tests/gpusim/__init__.py                    (empty)
tests/gpusim/test_golden_fixtures.py        (T05)
this file, §8 only                          (progress log)
```

## 4. Pinned dependencies
- EnergyPlus **23.1.0** only. Mac: `/Applications/EnergyPlus-23-1-0/energyplus` (x86_64 under Rosetta). Never 24.2.
- Python from `uv.lock`: numpy, pandas, pyarrow (Parquet, zstd compression).

## 5. Spec facts this work relies on (with citations)
- Golden outputs list: spec §4 "Golden data". Add `Output:Surfaces:List,Details;` (surface geometry in the `.eio`; the object may repeat) and `Output:Surfaces:List,ViewFactorInfo;` (writes E+ view factors and ScriptF to the `.eio`; key exists at `/Applications/EnergyPlus-23-1-0/Energy+.idd:101014`) and `Output:Constructions,Constructions;` (CTF dump).
- Golden cells must include one with a door and one with the thermal-bridge face (spec §4, §5 row M0).
- Timing pair: as built vs sizing off; annual heating must match (spec §1 "Runtime", §5 row M0). The sizing flags are in `openubem/campaign/eu_cell_runner.py:58–59`.
- S0 reproduces the IDF **as built** (spec §1 F1, F2). Do not fix F1 or F2 in the 3 golden cells or in V01–V11. The only exception is the decision variants V14 and V15 (spec §4, rev. 3), which apply the fixes recommended in spec §1 as test inputs; they change no campaign code.
- Source of the inputs: the certified rerun `openubem/outputs/eu_certified_rerun_2026-08-28/rep2/`:
  - `idfs/<cell_id>.idf` (unexpanded, as run), `schedules/<cell_id>.csv` (gain schedule), `manifests/<cell_id>.json` (has `epw_path`, `gain_csv_path`, `heating_kwh`), `<cell_id>/eplusout.csv` (hourly heating as published).
  - Paths inside IDFs and manifests are **Windows paths** (`C:\Users\o_iseri\Desktop\OpenUBEM\...`). Map them to this repo by the part after `OpenUBEM\`. Example: `...\openubem\data\weather\es_madrid_2009_2010_y2010.epw` → `openubem/data/weather/es_madrid_2009_2010_y2010.epw`.

**The 3 golden cells (fixed; do not change the selection):**
| # | cell_id | Why |
|---|---|---|
| 1 | `it__IT.MidClim.SFH.02.Gen.ReEx.001.001__f100` | door + thermal-bridge face, full gains, Bologna; base of all variants and of the timing pair |
| 2 | `uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000` | door + bridge, no gains, UK climate |
| 3 | `es__ES.ME.AB.01.Gen.ReEx.001.001__f000` | no door, no gains, Madrid |

## 6. Tasks

### T01 — Package skeleton and licence file
- **What:** create `openubem/gpusim/__init__.py` (empty) and `openubem/gpusim/LICENSE-ENERGYPLUS`.
- **Why:** spec §0 (licence row) and §6: files that translate E+ logic carry the E+ notice.
- **How:** `LICENSE-ENERGYPLUS` = one first line `Portions of openubem/gpusim translate algorithms from EnergyPlus version 23.1.0. The EnergyPlus licence follows.`, a blank line, then the full text of `/Applications/EnergyPlus-23-1-0/LICENSE.txt` copied byte for byte.
- **How to test:** the file minus its first two lines equals `LICENSE.txt` (`diff <(tail -n +3 openubem/gpusim/LICENSE-ENERGYPLUS) /Applications/EnergyPlus-23-1-0/LICENSE.txt` prints nothing). `uv run python -c "import openubem.gpusim"` works.

### T02 — Golden run folders and run list (no E+ runs here)
- **What:** `scripts/gpusim/make_golden.py prepare` builds one folder per golden cell under `openubem/outputs/gpusim_golden_runs/<cell_id>/` and writes `openubem/outputs/gpusim_golden_runs/run_list.txt`.
- **Why:** spec §4 golden data; local-run rule in §2 rule 3.
- **How:** for each of the 3 cells:
  1. Copy `rep2/idfs/<cell_id>.idf` to `<folder>/in.idf`. Copy the EPW (from the manifest `epw_path`, mapped) to `<folder>/in.epw`. Copy `rep2/schedules/<cell_id>.csv` to `<folder>/` under its original basename.
  2. In `in.idf`, replace every `Schedule:File` file-name field with the bare basename (no directory). Change nothing else in the existing objects.
  3. Append to `in.idf`: `Output:Constructions,Constructions;`, `Output:Surfaces:List,Details;` (surface areas, tilts, azimuths in the `.eio`), `Output:Surfaces:List,ViewFactorInfo;`, and one `Output:Variable,*,<name>,Timestep;` for each name below (exact E+ names):
     `Zone Mean Air Temperature`, `Zone Air Temperature`, `Zone Air Humidity Ratio`, `Surface Inside Face Temperature`, `Surface Outside Face Temperature`, `Surface Inside Face Convection Heat Gain Rate`, `Surface Inside Face Convection Heat Transfer Coefficient`, `Surface Inside Face Net Surface Thermal Radiation Heat Gain Rate`, `Surface Outside Face Convection Heat Transfer Coefficient`, `Surface Outside Face Thermal Radiation to Sky Heat Transfer Coefficient`, `Surface Outside Face Thermal Radiation to Air Heat Transfer Coefficient`, `Surface Outside Face Thermal Radiation to Ground Heat Transfer Coefficient`, `Surface Window Inside Face Glazing Zone Convection Heat Gain Rate`, `Zone Ideal Loads Zone Sensible Heating Rate`, `Zone Ideal Loads Zone Total Heating Energy`, `Zone Ventilation Sensible Heat Loss Energy`, `Zone Ventilation Sensible Heat Gain Energy`, `Zone Ventilation Mass Flow Rate`, `Site Outdoor Air Drybulb Temperature`, `Site Outdoor Air Humidity Ratio`, `Site Outdoor Air Barometric Pressure`, `Site Sky Temperature`, `Site Horizontal Infrared Radiation Rate per Area`.
     Keep the existing hourly heating output as it is.
  4. **Variants (parity tier P1, spec §4 level 4).** For base cell 1 only, make one extra folder per variant under `openubem/outputs/gpusim_golden_runs/variants/<base_cell_id>__<Vnn>/`, starting from cell 1's prepared `in.idf` (with the outputs from step 3) and changing **only** what the variant names. The numbers keep the original IDs; the gaps are variants dropped to keep the run count small.
     - V01 ventilation design flow ×3 (field used by `ZoneVentilation:DesignFlowRate` in that IDF);
     - V03 heating setpoint +2 K (the constant heating setpoint of the thermostat);
     - V04 every opaque `Material:NoMass` thermal resistance ÷0.3 (U ×0.3);
     - V06 every `WindowMaterial:SimpleGlazingSystem` U-factor ×0.5;
     - V07 `InternalMass` surface area ×4;
     - V09 every `SurfaceProperty:OtherSideCoefficients`: outdoor dry-bulb coefficient = 1 and zone air coefficient = 0 (all b = 1);
     - V10–V11 climate: replace `in.epw` with `openubem/data/weather/fi_helsinki_tmyx_2009_2023.epw` (V10) or `ca_montreal_tmyx_2009_2023.epw` (V11), and set `Site:Location` name, latitude, longitude, time zone and elevation from that EPW's `LOCATION` line. If the IDF has a `RunPeriod` or other field tied to the EPW year, leave it unchanged and report it.
     - **Decision variants (spec §1 F1/F2, §4 rev. 3):**
       - V14 (D2 fix): `InternalMass` surface area ×2. Nothing else changes.
       - V15 (D1 fix, option c): (1) every `BuildingSurface:Detailed` whose outside boundary condition is `Outdoors`: `Sun_Exposure` = `SunExposed` (keep `Wind_Exposure` as it is); (2) every `Material:NoMass` used by a construction of an `Outdoors` surface: `Solar_Absorptance` = 0, written explicitly (the IDD default is 0.7); leave the floor material as built (manager ruling at CP2 stop 2026-11-22: zeroing the floor too makes E+ refuse the run with a severe error, because all window solar is placed on the floor); (3) every `WindowMaterial:SimpleGlazingSystem`: `Solar_Heat_Gain_Coefficient` ×0.42. Also append `Output:Variable,*,Surface Outside Face Incident Solar Radiation Rate per Area,Timestep;` and `Output:Variable,*,Zone Windows Total Transmitted Solar Radiation Rate,Timestep;`.
     That is 10 variant folders. If a variant's target field does not exist in the base IDF, STOP and report.
  5. Write one line per cell and per variant to `run_list.txt` (13 lines): the folder path relative to `openubem/outputs/gpusim_golden_runs/`.
- **Also:** scan every EPW referenced by the 395 `rep2/manifests/*.json` (mapped paths, unique set) and count hours with horizontal infrared ≤ 0 or ≥ 9999 (EPW field 13, 1-based, after the 8 header lines). Print one line per EPW: name, count.
- **How to test:** `uv run python scripts/gpusim/make_golden.py prepare` creates 3 cell folders and 10 variant folders (13 lines in `run_list.txt`); print a diff summary per variant showing that only the named fields changed. The 3 cell folders each have `in.idf`, `in.epw` and the schedule CSV; `grep -c "Output:Variable" in.idf` gives 23 more than in the source IDF; `grep -c "C:\\\\" in.idf` gives 0. Report the EPW infrared counts.

### T03 — Timing pair on this Mac (local, serial)
- **What:** `scripts/gpusim/time_pair.py` times cell 1 as built and with sizing off.
- **Why:** spec §1 "Runtime" and §5 row M0: reproduce IMP02's split before anyone relies on it.
- **How:**
  1. Two folders under `openubem/outputs/gpusim_golden_runs/timing/`: `as_built/` = cell 1's original `rep2/idfs` IDF with only the `Schedule:File` path made a bare basename (no extra outputs) plus EPW and schedule CSV; `sizing_off/` = the same, with `SimulationControl,Yes,Yes,Yes,No,Yes,No,1;` replaced by `SimulationControl,No,No,No,No,Yes,No,1;`. Nothing else changes.
  2. Run E+ exactly as the campaign runs it (`-x -r`, same as `openubem/campaign/eu_cell_runner.py:433–450`; read that function, do not import or change it). Run order: as_built, sizing_off, repeated 3 times (6 runs, one at a time, nothing else heavy running).
  3. Record per run: variant, repeat, wall seconds (`time.perf_counter` around the subprocess), E+ "Elapsed Time" from `eplusout.end` or `eplusout.err`, annual heating kWh (sum of the hourly heating column ÷ 3.6e6).
  4. Write `openubem/outputs/gpusim_m0_timing.csv`.
- **How to test:** the CSV has 6 rows; all 6 annual heating values are identical (Mac repeatability; `as_built` = `sizing_off`); report the difference to cell 1's manifest `heating_kwh` as information only (D6); report median wall time per variant and the difference.

### CP1 — STOP and report
Report: T01–T03 results, the EPW infrared counts, the timing medians and heating values. Then wait for the owner's "continue".

### T04 — Run the golden simulations locally and convert them to Parquet
- **What:** `scripts/gpusim/make_golden.py run` runs the 13 folders in `run_list.txt` with E+ 23.1 on this Mac; `scripts/gpusim/make_golden.py collect` turns each run folder's outputs into `tests/fixtures/gpusim/golden/<cell_id>/`.
- **Why:** spec §4 golden data.
- **How:** first `run`: one `concurrent.futures` pool with `max_workers=4`, one E+ process per folder, run in the folder with the same command line as the campaign (`-x -r`, see T03); print each folder's exit code and wall time; any failed run → STOP and report. Then `collect`, per cell:
  1. Refuse the cell if `eplusout.err` has a severe or fatal error (warnings are allowed; the warning that `Surface Window Inside Face Glazing Zone Convection Heat Gain Rate` was not generated is expected in every run, record it in meta.json, no action), or `eplusout.end` does not say "EnergyPlus Completed Successfully".
  2. `timestep.parquet`: every timestep row of the run period from `eplusout.csv` (drop warm-up and sizing rows; expect 105,120 rows), all `(TimeStep)` columns as float64; drop every `(Hourly)` column (it is empty on 11 of 12 rows and is the sum of the timestep values), plus `month, day, hour, minute` integer columns parsed from Date/Time. zstd compression.
  3. Copy `in.idf`, `eplusout.eio`, `eplusout.err`, `eplusout.expidf` into the fixture folder (refuse the cell if it is missing).
  4. **Variants** go to `tests/fixtures/gpusim/golden/variants/<base_cell_id>__<Vnn>/` with a smaller `timestep.parquet` (only the date columns, `Zone Mean Air Temperature`, `Zone Ideal Loads Zone Sensible Heating Rate`, `Zone Ideal Loads Zone Total Heating Energy`, and the five `Site` columns listed in T02 step 3; for V15 also the two solar columns), plus `in.idf`, `eplusout.expidf`, `eplusout.eio`, `eplusout.err` and `meta.json` (as below, with `variant` and the changed fields; there is no published value to compare, so leave the manifest fields empty).
  5. `meta.json`: cell_id, source manifest path, EPW file name and sha256, `in.idf` sha256, E+ version line from `eplusout.eio`, row count, annual heating kWh from this run, manifest `heating_kwh` (Windows, information only, D6), relative difference.
- **How to test:** report the total wall time of `run`; 3 cell fixtures and 10 variant fixtures; each `timestep.parquet` has 105,120 rows; report each variant's annual heating next to its base cell (the direction must make physical sense, e.g. V01 above base, V04 below base, V15 below base, V14 within a few percent of base; report any that do not); report per cell the annual heating vs the manifest value (information only, D6; cell 1 is expected near +0.66 %) and the total fixture size in MB. If the total is above 300 MB, STOP and report before going on (raised from 60 MB on 2026-11-22: the fixtures are local test data, never committed to git without an owner ruling).

### T05 — Fixture tests (the harness starts red)
- **What:** `tests/gpusim/test_golden_fixtures.py`.
- **Why:** spec §5 row M0 exit: "harness runs (all red)" means the fixtures load and the gpusim tests that need the engine are marked expected-to-fail until M1.
- **How:** tests that pass now: each fixture (cells and variants) loads; 105,120 rows; no NaN in the heating and zone-temperature columns; cell 1's annual heating equals the T03 Mac value 23,275.422744 kWh within 1e-6 relative (the added outputs must not change results); every `meta.json` has the manifest value and difference fields (no gate on them, D6); the `.eio` contains a `Construction CTF` block for `EU_INTERNALMASS_CONSTRUCTION`, `HeatTransfer Surface` lines and a view-factor block. One test `test_stage_a_matches_golden` marked `pytest.mark.xfail(strict=True, reason="M1 not built")` that imports `openubem.gpusim.backends.numpy_ref` (does not exist yet).
- **How to test:** `uv run pytest tests/gpusim -q` → all pass except the one xfail. Paste the summary line.

### CP2 — STOP and report
Report T04–T05: per-cell heating difference vs the published value (information only, D6), fixture size, pytest summary line. M0 is done when all of these hold:
- [ ] `LICENSE-ENERGYPLUS` matches `LICENSE.txt` (T01 diff empty)
- [ ] 3 cell fixtures, 105,120 rows each; cell 1 heating equals the T03 Mac value within 1e-6; difference vs the published Windows value reported for all 3 (no gate, D6)
- [ ] 10 variant fixtures, 105,120 rows each, heating direction vs base reported
- [ ] `.eio` CTF, surface-detail and view-factor blocks present in all 3
- [ ] timing CSV with 6 rows, heating identical between variants
- [ ] pytest: all pass, 1 xfail
- [ ] only files from §3 touched (`git status --short -- openubem scripts tests` lists nothing else)

## 7. Stop-and-report points
- **CP1** after T03 (run folders ready, timing pair measured).
- **CP2** after T05 (M0 done).

## 8. Progress log
<!-- Append one entry per completed task, in this format:
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none, or what and why>
- Test status: <command and measured result>
- Notes: <anything the manager must know>
-->

#### T01 — Package skeleton and licence file — completed 2026-11-22
- Artifacts: `openubem/gpusim/__init__.py`, `openubem/gpusim/LICENSE-ENERGYPLUS`
- Deviations: `uv` binary is not on PATH, so `.venv/bin/python` (the project's `uv.lock` virtualenv) was used instead of `uv run python`.
- Test status: `diff <(tail -n +3 openubem/gpusim/LICENSE-ENERGYPLUS) /Applications/EnergyPlus-23-1-0/LICENSE.txt` exited 0 (0 bytes diff); `.venv/bin/python -c "import openubem.gpusim; print('OK')"` exited 0 (`OK`).
- Notes: `openubem/gpusim/__init__.py` is 0 bytes; `openubem/gpusim/LICENSE-ENERGYPLUS` carries the 2-line header plus the exact byte-for-byte 3,167-byte E+ 23.1.0 licence.

#### T02 — Golden run folders and run list — completed 2026-11-22
- Artifacts: `scripts/gpusim/make_golden.py`, `openubem/outputs/gpusim_golden_runs/run_list.txt`, 3 cell folders and 10 variant folders under `openubem/outputs/gpusim_golden_runs/`
- Deviations: Run via `.venv/bin/python scripts/gpusim/make_golden.py prepare` (`uv` not on PATH).
- Test status: `.venv/bin/python scripts/gpusim/make_golden.py prepare` exited 0; `run_list.txt` has 13 lines (3 cells + 10 variants); each of the 3 cell folders has `in.idf`, `in.epw`, and `<cell_id>.csv`; `grep -c "Output:Variable" in.idf` increased from 0 to 23 (case-insensitive 1 to 24); `grep -c 'C:\\' in.idf` is 0 for all 3; per-variant unified diffs confirmed only the named fields changed (plus 2 solar outputs on V15).
- Notes: EPW horizontal infrared scan across all 395 `rep2/manifests/*.json` found 3 unique EPWs, all with 8,760 of 8,760 hours having field 13 <= 0 or >= 9999 (`es_madrid_2009_2010_y2010.epw`: 8760, `it_bologna_2013_2014_y2014.epw`: 8760, `uk_london_2014_2015_y2014.epw`: 8760). For V10/V11, `RunPeriod1` has `begin_year=''`, `end_year=''`, `start_day=''` (left unchanged).

#### T03 — Timing pair on this Mac (local, serial) — stopped at gate failure 2026-11-22
- Artifacts: `scripts/gpusim/time_pair.py`, `openubem/outputs/gpusim_golden_runs/timing/as_built/`, `openubem/outputs/gpusim_golden_runs/timing/sizing_off/`, `openubem/outputs/gpusim_m0_timing.csv`
- Deviations: Run via `.venv/bin/python scripts/gpusim/time_pair.py` (`uv` not on PATH); stopped at gate failure without loosening tolerance.
- Test status: FAIL on the 0.01 % heating parity gate vs manifest. All 6 serial E+ 23.1.0-87ed9199d4 runs exited 0 with 0 severe/0 fatal errors (`openubem/outputs/gpusim_m0_timing.csv` has 6 rows). Medians: `as_built` wall 4.177 s (E+ elapsed 3.87 s), `sizing_off` wall 2.592 s (E+ elapsed 2.29 s), savings 1.585 s wall (37.9 %) / 1.58 s E+ elapsed (40.8 %). All 6 runs produced identical annual heating 23,275.422744 kWh (`as_built` vs `sizing_off` delta = 0.000000 %), which is +152.3335 kWh (+0.658794 %) above the `rep2` manifest (23,123.089232 kWh).
- Notes: Diagnostic evidence on the +0.658794 % gap: `in.epw` SHA-256 (`ab631c60...`) is byte-identical to `rep2` manifest; `in.idf` and schedule CSV match manifest SHA-256s (`891773f4...`, `0ecf2acb...`) under CRLF; `eplusout.expidf` is byte-identical except line 86 (`Schedule:File` path); `eplusout.eio` shows identical build `23.1.0-87ed9199d4` and identical lines 2–94 and 96–106 (`Zone Sizing Information` differs: 11379.98335 W in `rep2` vs 11381.41812 W local). Hourly `local - rep2` heating diff is never negative (min = 0.0 J, mean = +62,602.8 J/hr, max = +588,167.3 J/hr = +163.38 W on 04/17 14:00) and correlates strongly with GHI (`corr = +0.9408` on active hours, e.g. `10.27 W` at `dni=0, ghi=50.5` on Jan 1 10:00 and `163.38 W` at `ghi=874.2, dni=920.3` on Apr 17 14:00, decaying overnight from `10.95 W` to `3.51 W` when `ghi=0`) despite `NoSun` in both `eplusout.expidf` files.
- Manager note (2026-11-22): CP1 audited. T01–T02 pass. T03's gate was changed by owner ruling D6 (Mac E+ is the reference; published Windows value is information only). Under the new gate T03 **passes**: 6 identical heating values, `as_built` = `sizing_off`. Not re-run.

#### T04 — Run the golden simulations locally and convert them to Parquet — stopped at 60 MB size gate 2026-11-22
- Artifacts: `scripts/gpusim/make_golden.py`, `openubem/outputs/gpusim_golden_runs/variants/it__IT.MidClim.SFH.02.Gen.ReEx.001.001__f100__V15/`, `tests/fixtures/gpusim/golden/` (3 cell fixtures + 10 variant fixtures)
- Deviations: Run via `.venv/bin/python` (`uv` not on PATH). Rebuilt and re-ran only V15 per kickoff instructions (12 passing runs untouched). Stopped before T05 because total fixture size (272.04 MB) exceeds the 60 MB stop gate in T04.
- Test status: V15 rebuild & single E+ run exited 0 in 45.898 s (`10 Warning; 0 Severe Errors; Elapsed Time=00hr 00min 45.33sec`; 4 `Outdoors` surfaces `SunExposed`, 5 `Outdoors` `Material:NoMass` `Solar Absorptance=0`, floor/roof/thermal-bridge unchanged, 3 `SHGC` x0.42). `.venv/bin/python scripts/gpusim/make_golden.py collect` exited 1 at the 60 MB gate: all 13 runs passed completion/0-severe checks and produced `105,120`-row zstd Parquets (`float64` `(TimeStep)` columns, `(Hourly)` dropped, `int32` date columns, zero NaN). Golden cells (Mac vs Windows `rep2` manifest, D6 info only): cell 1 (`it`, 94 cols) `23,275.422744` vs `23,123.089232 kWh` (`+0.658794%`), cell 2 (`uk`, 82 cols) `429,473.855275` vs `429,473.855275 kWh` (`+0.000000%`), cell 3 (`es`, 91 cols) `177,989.483486` vs `177,989.483486 kWh` (`+0.000000%`). Variants vs base cell 1 (`23,275.422744 kWh`): V01 `33,370.107485` (`+43.3706%`), V03 `29,736.671567` (`+27.7600%`), V04 `12,457.574054` (`-46.4776%`), V06 `22,520.366158` (`-3.2440%`), V07 `21,853.525829` (`-6.1090%`), V09 `25,687.962893` (`+10.3652%`), V10 `56,814.989355` (`+144.0986%`), V11 `54,500.513144` (`+134.1548%`), V14 `23,165.462717` (`-0.4724%`), V15 `21,574.927433` (`-7.3060%`, 21 cols). Total fixture size: `272.04 MB` (`285,258,027 bytes`) > `60.0 MB`.
- Notes: Size breakdown under `tests/fixtures/gpusim/golden/`: `.parquet` files account for `270.28 MB` (3 cells: `78.42` + `75.07` + `66.78` = `220.27 MB`; 10 variants: `3.40`–`9.03 MB` each, `50.01 MB` total); non-parquet files (`.eio`, `.expidf`, `.idf`, `.err`, `.json`) total `1.76 MB`. `pyarrow.parquet.ParquetFile` metadata confirms `ZSTD` compression is active (`PLAIN`/`RLE_DICTIONARY` on `float64` columns: `88,471,942` uncompressed -> `82,112,265` compressed bytes for cell 1). T05 not started pending owner ruling on the 60 MB gate.
- Manager note (2026-11-22): T04 audited. All 13 runs exit 0 with 0 severe errors; 105,120 rows each; cell 1 = 23,275.422744 kWh (equals T03); variant directions correct (V01 +43.4 %, V04 −46.5 %, V15 −7.3 %, V14 −0.47 %). The only stop was the size gate (272.04 MB > 60 MB). Ruling: the 3 cell Parquets keep all float64 columns because M1 compares them; the gate is raised to 300 MB and the fixtures stay local and uncommitted. T04 **passes**. Not re-run.

#### T05 — Fixture tests (the harness starts red) — completed 2026-11-22
- Artifacts: `tests/gpusim/__init__.py`, `tests/gpusim/test_golden_fixtures.py`
- Deviations: Run via `.venv/bin/pytest tests/gpusim -q` (`uv` not on PATH).
- Test status: `.venv/bin/pytest tests/gpusim -q` -> `17 passed, 1 xfailed, 1 warning in 0.76s` (all 13 fixtures load with `105,120` rows, zero NaN in heating/zone-temperature/date columns, `manifest_heating_kwh` and `relative_difference` present in every `meta.json`; cell 1 annual heating matches T03 Mac reference `23,275.422744 kWh` within `1e-6`; all 3 golden cell `.eio` files contain `Construction CTF` for `EU_INTERNALMASS_CONSTRUCTION`, `HeatTransfer Surface`, and `Solar View Factor` blocks; `test_stage_a_matches_golden` strictly xfails with `M1 not built`).
- Notes: **CP2 PASS (M0 complete).** All 7 CP2 checks verified: (1) T01 `LICENSE-ENERGYPLUS` diff empty; (2) 3 cell fixtures `105,120` rows each, cell 1 matches T03 within `1e-6`, Mac vs Windows manifest diffs reported (cell 1 `+0.658794%`, cell 2 `+0.000000%`, cell 3 `+0.000000%`, D6 info only); (3) 10 variant fixtures `105,120` rows each, all heating directions physically consistent, total fixture size `272.04 MB` (`<= 300 MB`); (4) `.eio` CTF/surface-detail/view-factor blocks verified in all 3; (5) timing CSV 6 rows identical heating; (6) pytest `17 passed, 1 xfailed`; (7) `git status --short -- openubem scripts tests` lists only §3 paths (`openubem/gpusim/`, `openubem/outputs/gpusim_golden_runs/`, `openubem/outputs/gpusim_m0_timing.csv`, `scripts/gpusim/`, `tests/fixtures/gpusim/`, `tests/gpusim/`). Proceeding directly to M1 per owner kickoff.
