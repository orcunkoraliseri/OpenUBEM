# EXEC M1 — gpusim Stage A: NumPy float64 reference engine for rung S0

## 1. Header
- **Slug:** `gpusim-M1`. **Date:** 2026-11-22. **Approved by owner:** D3 (2026-11-22).
- **Starts only after M0 is done** (`EXEC_M0_golden_data.md` CP2 passed, audited by the manager).
- **Spec (the DESIGN for this work):** `docs/docs_ACTIVE/GPU_based_compute/BUILD_SPEC_gpu_heat_balance_engine.md` rev. 3: §1 (S0 inventory), §2 row S0 and router rule, §3.0 (timestep order and constants), §3.2 (difference-form rules), §3.3 (faithfulness), §4 (tolerances), §6 (layout).
- **Executor:** a Gemini session with repo access, run by the owner. **NO sub-agents.**
- **Kickoff (paste into the executor session; one run for all of M1, owner choice 2026-11-22 after a clean M0):**
  ```
  Read /Users/orcunkoraliseri/Desktop/OpenUBEM/docs/docs_ACTIVE/GPU_based_compute/Prompt/executors/EXEC_M1_stageA_numpy_s0.md.
  Execute T01 through T06 in order. At CP1, CP2 and CP3, if every check passes, write that checkpoint's report
  into the progress log and continue without waiting. STOP only if a test or gate fails, the spec is ambiguous,
  or the E+ source disagrees with the spec; then quote the problem and wait. Append one progress-log entry per
  completed task under §8 of that file, run the tests the tasks call for, and report all results at CP4.
  Do not propose alternatives — execute the plan.
  ```

## 2. Hard rules for the executor
1. Execute the tasks in order. Do not write plans, do not redesign. If the spec and the E+ source disagree, the **E+ 23.1.0 source wins**: STOP, quote both, and wait.
2. **No fudge.** No fitted multipliers, calibration constants, tuned iteration counts or loosened tolerances. A gate that fails is reported with diagnostics, never "fixed" by tuning. Tolerances change only in spec §4, by the manager.
3. Every physics function has a one-line docstring citing the E+ file and function it translates (for example `"""ConvectionCoefficients.cc::CalcASHRAETARPNatural"""`). No other comments.
4. Touch only the files in §3. Never edit `openubem/campaign/`, `openubem/idf/`, `tests/fixtures/gpusim/golden/` (read only), the certified rerun folder (read only), or any frozen path in `CLAUDE.md`.
5. **No EnergyPlus runs** in M1. The references are the M0 golden fixtures and the published rerun outputs.
6. Python env is `uv`; tests with `pytest`. No new dependencies. All arrays float64. All physics functions take an `xp` argument (the array namespace; NumPy here) so Stage B can reuse them (spec §6).
7. Arrays are batched: the first axis is the building (shape `[B, ...]`). The time loop is Python; everything inside one step is vectorised over buildings. Per-building convergence uses masks, never a Python loop over buildings.
8. Do not commit. Report measured numbers with the command that produced them.
9. Paths are relative to the repo root `/Users/orcunkoraliseri/Desktop/OpenUBEM/`.

## 3. File layout (only these may be created or changed)
```
openubem/gpusim/subset.py
openubem/gpusim/compile.py
openubem/gpusim/weather.py
openubem/gpusim/schedules.py
openubem/gpusim/ctf.py
openubem/gpusim/viewfactors.py
openubem/gpusim/physics/__init__.py
openubem/gpusim/physics/psychro.py
openubem/gpusim/physics/convection.py
openubem/gpusim/physics/lwr.py
openubem/gpusim/physics/window.py
openubem/gpusim/physics/surface_hb.py
openubem/gpusim/physics/zone_air.py
openubem/gpusim/backends/__init__.py
openubem/gpusim/backends/numpy_ref.py
openubem/gpusim/writer.py
scripts/gpusim/run_fleet_stage_a.py          (T06)
scripts/gpusim/bench.py                      (T06)
tests/gpusim/test_weather.py, test_compile.py, test_viewfactors.py, test_physics_units.py,
tests/gpusim/test_cells.py, test_golden_fixtures.py (remove the xfail marker only, in T05)
openubem/outputs/gpusim_m1_cells.csv, gpusim_m1_fleet.csv, gpusim_m1_bench.csv
this file, §8 only                           (progress log)
```

## 4. Pinned dependencies
- Reference engine: EnergyPlus **23.1.0** (tag `v23.1.0` of `NREL/EnergyPlus`).
- **E+ source for reading:** download once with curl from `https://raw.githubusercontent.com/NREL/EnergyPlus/v23.1.0/src/EnergyPlus/<File>` into `/tmp/gpusim_ep231/` (outside the repo, never committed). Files: `HeatBalanceSurfaceManager.cc`, `DataHeatBalSurface.hh`, `DataHeatBalance.hh`, `SurfaceGeometry.cc`, `ConvectionCoefficients.cc`, `WindowManager.cc`, `HeatBalanceManager.cc`, `HeatBalanceIntRadExchange.cc`, `ZoneTempPredictorCorrector.cc`, `ZoneEquipmentManager.cc`, `HVACManager.cc`, `PurchasedAirManager.cc`, `WeatherManager.cc`, `DataEnvironment.cc`, `Psychrometrics.hh`, `Psychrometrics.cc`, `ScheduleManager.cc`.
- Python from `uv.lock`: numpy, pandas, pyarrow.

## 5. Spec facts this work relies on (with citations)
All in spec rev. 3; the E+ line numbers were checked against v23.1.0 on 2026-11-22 (spec §9).
- **Order per zone timestep:** spec §3.0 steps 1–9. Implement in exactly this order.
- **Constants:** `IterDampConst = 5.0`, re-evaluate inside convection when iteration > 0 and iteration % 30 == 0, max 500 iterations, min 1, convergence `MaxAllowedDelTemp = 0.002` K (`DataHeatBalSurface.hh:70–90`, `DataHeatBalance.hh:1844`); windows only on iteration 0 (`HeatBalanceSurfaceManager.cc:8866`); initial temperatures 23.0 °C (`:7582–7584`); warm-up loads floor 100 W (`HeatBalanceManager.cc:3475`); warm-up 1–25 days, tolerances 0.04 (loads) and 0.4 °C (temperature) unless the IDF says otherwise; HVAC sub-stepping threshold `MaxZoneTempDiff` (`HVACManager.cc:332`; read its value from the source).
- **Surfaces:** OSC with film 0 = outside face temperature from the previous step's `MAT` (`HeatBalanceSurfaceManager.cc:7051–7092`); outdoor faces DOE-2 natural part at zero wind, sky weight `√(0.5(1+cos tilt))` (`SurfaceGeometry.cc:355`), ground at air temperature; inside TARP with −cos tilt (`ConvectionCoefficients.cc:7100`), clamp `[0.1, 1e7]` from the `HeatBalanceAlgorithm` line; floor auto-flip (`SurfaceGeometry.cc:9575`); height lapse (`DataEnvironment.cc:102–107`).
- **Window:** SimpleGlazingSystem → one equivalent layer (`HeatBalanceManager.cc:5880–5970`), two-face balance with ISO 15099 inside convection (`WindowManager.cc:3535–3715`), no sun.
- **Door:** opaque `Material:NoMass` subsurface on an `Outdoors` host wall; same outside treatment as the host.
- **Internal mass:** tilt 90°, one-side area, outside boundary = itself, both faces at the inside-face temperature (`SurfaceGeometry.cc:7400–7426`); CTF from the golden `.eio` (identical construction in every cell).
- **Ventilation:** ρ and cp at outdoor temperature and humidity (`ZoneEquipmentManager.cc:5144–5165`).
- **Zone air:** third-order backward difference for temperature and humidity ratio, in difference form (spec §3.2).
- **Weather:** end-of-hour interpolation, first hour uses hour 24 of day 1, humidity ratio and sky temperature per timestep, Clark–Allen fallback for missing infrared (spec §3.0 step 1).
- **Reporting:** E+ hourly values are sums of timestep values in the hour; reported zone temperature is the sub-step mean.
- **Gates (S0, spec §4):** see each task.
- **Inputs:** golden fixtures `tests/fixtures/gpusim/golden/<cell_id>/` (3 cells: `timestep.parquet`, `in.idf`, `eplusout.eio`, `eplusout.expidf`, `meta.json`). Fleet: `openubem/outputs/eu_certified_rerun_2026-08-28/rep2/` — use only cells whose `manifests/<cell_id>.json` has `completion_status == "COMPLETED"` (346 of 395); input = `<cell_id>/eplusout.expidf` + `schedules/<cell_id>.csv` + the EPW from the manifest (Windows path mapped to the repo by the part after `OpenUBEM\`); reference = `<cell_id>/eplusout.csv` hourly heating and the manifest `heating_kwh`. These fleet references were run on Windows; Mac E+ differs by about +0.66 % on cell 1 (owner ruling D6, spec §8–§9), so on the Mac the fleet comparison is reported, not gated.

## 6. Tasks

### T01 — Psychrometrics and weather
- **What:** `physics/psychro.py` (only the `Psy*` functions S0 needs: ρ(P,T,W), cp(W), h(T,W), W from dew point or RH and pressure, saturation pressure), and `weather.py` (EPW → per-timestep arrays: dry bulb, dew point, RH, pressure, humidity ratio, horizontal infrared, sky temperature).
- **Why:** spec §3.0 step 1.
- **How:** translate from `Psychrometrics.hh/.cc` and `WeatherManager.cc` (`SetUpInterpolationValues`, `ReadEPlusWeatherForDay`, `CalcSkyEmissivity`, sky temperature). Output arrays have 105,120 run-period steps plus the warm-up day-1 steps (day 1 repeated).
- **How to test:** `tests/gpusim/test_weather.py`: for all 3 golden cells and the 2 climate variants (V10, V11), every timestep of `Site Outdoor Air Drybulb Temperature`, `Site Outdoor Air Humidity Ratio`, `Site Outdoor Air Barometric Pressure`, `Site Sky Temperature`, `Site Horizontal Infrared Radiation Rate per Area` matches. Gate: max abs difference ≤ 1e-3 K (temperatures), ≤ 1e-6 (humidity ratio), ≤ 1 Pa, ≤ 1e-2 W/m² — these are the CSV print limits. Report the measured max per variable.

### T02 — Subset checker and compiler
- **What:** `subset.py` (S0 whitelist on the **expanded** IDF: object types and non-default field values from spec §1; returns pass or the first failing reason) and `compile.py` (expanded IDF → `BatchSpec` dataclass of `[B, ...]` arrays, padded to the max surface count in the batch with a mask).
- **Why:** spec §2 router rule, §3 architecture.
- **How:** parse the `.expidf` text directly (no eppy). BatchSpec holds per surface: type, area, tilt and cos tilt (after the floor flip), azimuth, centroid z, boundary kind (OSC / Outdoors / internal mass / window / door), U or construction id, OSC coefficients, view factor to ground, emissivities, roughness, window height; per zone: volume, floor area, centroid z (excluding internal mass), ACH, setpoint, gain schedule index; per site: EPW id. Also `BatchSpec.from_records` is **not** in M1 (only the IDF route).
- **How to test:** `tests/gpusim/test_compile.py`: (a) all 346 completed fleet `.expidf` pass `subset.py`; (b) a copy of one with an extra `People` object fails with a reason naming `People`; (c) for the 5 golden cells, area, tilt, azimuth and centroid of every surface match the `HeatTransfer Surface` lines in the golden `.eio` (≤ 1e-4 relative); the floor shows tilt 180°; (d) the `.expidf` of variant V15 (sun on, spec §4) fails `subset.py` with a reason naming `SunExposed`, and V14 passes.

### T03 — View factors, ScriptF and internal-mass CTF
- **What:** `viewfactors.py` (approximate view factors, `FixViewFactors` including the large-surface self-view branch, ScriptF) and `ctf.py` (read the internal-mass CTF from the golden `.eio`; check its timestep equals the zone timestep).
- **Why:** spec §3.0 step 5, §3.3.
- **How:** translate `HeatBalanceIntRadExchange.cc` (`CalcApproximateViewFactors`, `FixViewFactors`, `CalcScriptF`), float64, once per building. If the CTF timestep is not the zone timestep, STOP (that is S2a scope).
- **How to test:** `tests/gpusim/test_viewfactors.py`: for the 3 golden cells, the final view factors and ScriptF match the `.eio` view-factor block (≤ 1e-5 absolute); internal-mass CTF: Σ outside = Σ cross = Σ inside within the print precision, and `(Σ Z) / (1 − Σ Φ)` equals `k / L = 10 W/m²K` within 0.1 %.

### CP1 — STOP and report
T01–T03 measured maxima, test summary line, files touched.

### T04 — Physics functions with per-equation tests
- **What:** `physics/convection.py`, `lwr.py`, `window.py`, `surface_hb.py`, `zone_air.py`.
- **Why:** spec §4 test pyramid level 1: localise disagreements before the full loop.
- **How:** translate from the files in §4; each function vectorised over `[B, surfaces]`. Unit tests feed E+'s own values from `timestep.parquet` into one function and compare its output, at every timestep of the 5 golden cells:
  1. inside TARP h from golden inside-face and zone temperatures → `Surface Inside Face Convection Heat Transfer Coefficient` (opaque surfaces);
  2. outdoor face h (convection, sky, air, ground) from golden outside-face and site values → the four outside coefficients;
  3. window: from golden zone and outdoor values → window inside-face temperature and glazing convection gain;
  4. OSC outside-face temperature from the previous step's golden zone temperature → `Surface Outside Face Temperature`;
  5. zone predictor: from golden surface temperatures and convection coefficients → ideal-loads sensible heating rate.
- **How to test:** `tests/gpusim/test_physics_units.py`. Gate: p99.9 relative difference ≤ 1e-4 and max ≤ 1e-3 for each check (CSV print limit). Report p99.9 and max for each check and cell. A failing check: report the first timestep where it fails with the inputs, and STOP.

### CP2 — STOP and report
T04 table of p99.9/max per check, test summary line.

### T05 — Stage A time loop and single-cell conformance
- **What:** `backends/numpy_ref.py` (warm-up with per-building convergence mask, then the run period, §3.0 order, sub-stepping, hourly sums) and `writer.py` (hourly heating J per building; float64 annual totals; `eplusout.csv`-compatible column `EU_CELL_ZONE IDEAL LOADS AIR SYSTEM:Zone Ideal Loads Zone Total Heating Energy [J](Hourly)`).
- **Why:** spec §4 level 2.
- **How:** run the 3 golden cells as one batch (B = 3), then the 9 S0 variants (V01, V03, V04, V06, V07, V09, V10, V11, V14) in `tests/fixtures/gpusim/golden/variants/` (parity tier P1, spec §4 level 4; V15 is an S1 case and is not run in M1; their inputs are each variant fixture's `eplusout.expidf`; if one is missing, STOP and report). Remove the xfail marker in `tests/gpusim/test_golden_fixtures.py` and make `test_stage_a_matches_golden` assert the gates below. Add `tests/gpusim/test_cells.py` for per-cell trajectories.
- **Gates (S0, spec §4), per golden cell and per variant:** annual heating ≤ 0.5 % or ≤ 0.05 kWh/m² (worst-cell gate); hourly heating over active hours (either engine > 1 W/m²) CV(RMSE) ≤ 1 % and |NMBE| ≤ 0.1 %; zone air temperature p99.9 ≤ 0.03 K and max ≤ 0.25 K. Also report warm-up days per cell vs the golden `.eio` warm-up information.
- **How to test:** `uv run pytest tests/gpusim -q`; write `openubem/outputs/gpusim_m1_cells.csv` (one row per cell and variant: cell, annual E+, annual Stage A, rel diff, CV(RMSE), NMBE, ΔT p99.9, ΔT max, warm-up days both engines, wall seconds). On a failure: report which golden variable diverges first in time and by how much, and STOP. Do not tune.

### CP3 — STOP and report
T05 table, pytest summary line, Stage A wall time for B = 3.

### T06 — Fleet conformance and Stage A throughput
- **What:** `scripts/gpusim/run_fleet_stage_a.py` (all 346 completed cells, batched by EPW site) and `scripts/gpusim/bench.py`.
- **Why:** spec §4 level 3 and §5 row M1 (Stage A throughput).
- **How:** fleet: per cell, compare annual heating with the manifest `heating_kwh` and hourly heating with `<cell_id>/eplusout.csv`; write `openubem/outputs/gpusim_m1_fleet.csv` (same columns as T05 except ΔT, which has no fleet reference). Bench: building-years per second for batch sizes 1, 10, 100 and all cells of the largest site; write `openubem/outputs/gpusim_m1_bench.csv`.
- **Gates (S0 fleet, spec §4):** none on the Mac (D6). Measure and report against the spec §4 fleet thresholds (annual median ≤ 0.05 % or ≤ 0.02 kWh/m²; p99 ≤ 0.2 %; worst ≤ 0.5 % or ≤ 0.05 kWh/m²; hourly CV(RMSE) ≤ 1 % and |NMBE| ≤ 0.1 %); these are enforced on Windows in M4. Also report the signed median difference (the platform offset).
- **How to test:** report median / p99 / worst and the count of cells failing each gate, with the 5 worst cell ids. Bench table.

### CP4 — STOP and report (M1 done when all hold)
- [ ] T01–T04 unit gates pass (measured maxima listed)
- [ ] 3 golden cells and 9 S0 variants pass every T05 gate (parity tier P1); V15 rejected by `subset.py`
- [ ] fleet comparison on 346 cells reported (median, p99, worst, hourly, signed median offset) against the spec thresholds; not gated on the Mac (D6, parity tier P2)
- [ ] `gpusim_m1_cells.csv`, `gpusim_m1_fleet.csv`, `gpusim_m1_bench.csv` written; numbers in them equal the numbers in the report
- [ ] pytest: all pass, no xfail left
- [ ] only files from §3 touched (`git status --short -- openubem scripts tests`)

## 7. Stop-and-report points
- **CP1** after T03 (inputs and geometry right).
- **CP2** after T04 (each equation right on its own).
- **CP3** after T05 (the loop right on 3 cells).
- **CP4** after T06 (fleet reported; M1 done).

## 8. Progress log
<!-- Append one entry per completed task, in this format:
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts: <paths>
- Deviations: <none, or what and why>
- Test status: <command and measured result>
- Notes: <anything the manager must know>
-->

#### T01 — Psychrometrics and weather — completed 2026-11-22
- Artifacts: `openubem/gpusim/physics/__init__.py`, `openubem/gpusim/physics/psychro.py`, `openubem/gpusim/weather.py`, `tests/gpusim/test_weather.py`
- Deviations: Run via `.venv/bin/pytest` (`uv` not on PATH).
- Test status: `.venv/bin/pytest tests/gpusim/test_weather.py -q` -> `5 passed, 1 warning in 0.45s` across all 3 golden cells plus V10 (Helsinki) and V11 (Montreal). Measured max abs differences across all 5 × 105,120 timesteps: `dry_bulb = 0.000e+00 K` (gate <= 1e-3 K), `hum_rat = 1.637e-09` (gate <= 1e-6), `baro_press = 0.000e+00 Pa` (gate <= 1 Pa), `sky_temp = 5.684e-14 K` (gate <= 1e-3 K), `horiz_ir = 1.705e-13 W/m2` (gate <= 1e-2 W/m2).
- Notes: Verified `StefanBoltzmann = 5.6697e-8` from `DataGlobalConstants.hh:181` and `WeatherManager.hh:1277`; `hum_rat` 1.6e-9 residual is E+'s `EP_cache_PsyPsatFnTemp` quantization.

#### T02 — Subset checker and compiler — completed 2026-11-22
- Artifacts: `openubem/gpusim/subset.py`, `openubem/gpusim/schedules.py`, `openubem/gpusim/compile.py`, `tests/gpusim/test_compile.py`
- Deviations: Run via `.venv/bin/pytest` (`uv` not on PATH). Checked against the 3 golden cells produced in M0 (T02 text mentions "5 golden cells" from before the Mac-only cut to 3).
- Test status: `.venv/bin/pytest tests/gpusim/test_compile.py -q` -> `4 passed, 1 warning in 0.31s`. All 346 completed fleet `.expidf` pass `check_s0_subset`; injected `People` fails naming `People`; V15 fails naming `SunExposed`; V14 passes. Across the 3 golden cells vs `.eio`: `max_area_rel = 1.256e-06` (gate <= 1e-4), `max_tilt_abs = 0.000e+00 deg` (floor auto-flipped to `180.0 deg`), `max_az_abs = 0.000e+00 deg`, `max_zcen_abs = 4.059e-03 m` (within `.eio` 2-decimal print limit `0.005 m`).
- Notes: Translated Newell normal/area, floor/roof vertex flip, `DetermineAzimuthAndTilt`, and gross-area-weighted zone centroid directly from `SurfaceGeometry.cc` and `Vectors.cc`.
