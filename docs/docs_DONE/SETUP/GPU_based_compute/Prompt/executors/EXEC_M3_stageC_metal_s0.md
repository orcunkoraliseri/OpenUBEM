# EXEC M3 — gpusim Stage C: fast chunked GPU kernel for rung S0 on the Mac

## 1. Header
- **Slug:** `gpusim-M3`. **Date:** 2026-11-22. **Approved by owner:** 2026-11-22 ("write M2 and M3").
- **Starts only after M2 is done** (`EXEC_M2_stageB_spike_mps.md` CP2 audited by the manager) **and** the owner has ruled D-09.
- **D-09 (Stage C framework):** ruled by the owner 2026-11-22: `D-09 = (a) PyTorch + shared C header on Metal`. Use only the option (a) files in §3 (`s0_common.h`, `s0_metal.py`); do not create the option (b) files. Basis: M2 spike CP2 (both pass at about 1e-5 K; (a) launches 2–5× faster and keeps a CUDA path through the same header).
- **Spec (the DESIGN for this work):** `docs/docs_ACTIVE/GPU_based_compute/BUILD_SPEC_gpu_heat_balance_engine.md` rev. 3: §3 (architecture), §3.0 (timestep order and constants), §3.1 (chunking, thread layout), §3.2 (precision), §3.3 (faithfulness), §4 (float32 gate, S0 gates, P1/P2 tiers), §5 row M3 and the speed-up section, §6 (layout).
- **Executor:** a Gemini session with repo access, run by the owner through `EXEC_MASTER_gpusim_m2_m3.md`. **NO sub-agents.**
- **What M3 delivers:** Stage C, the fast S0 engine: the whole year runs inside GPU kernels launched in chunks, one thread per building, float32, checked against Stage A, then timed against EnergyPlus.
- **Last Mac milestone.** After M3 the owner moves gpusim to the Windows CUDA machine (M4, owner plan 2026-11-22).

## 2. Hard rules for the executor
1. Execute the tasks in order. Do not write plans, do not redesign. If the spec and the E+ 23.1.0 source disagree, the **E+ source wins**: STOP, quote both, and wait.
2. **No fudge.** No fitted multipliers, tuned iteration counts, or loosened tolerances. A failed gate is reported with diagnostics and STOP.
3. **Frozen:** everything M1 and M2 built (`openubem/gpusim/physics/`, `backends/numpy_ref.py`, `backends/torch_batched.py`, `backends/xp_torch.py`, the spike files, `compile.py`, `weather.py`, `schedules.py`, `ctf.py`, `viewfactors.py`, `subset.py`, `writer.py`). Stage C reads `BatchSpec`, `WeatherSeries` and the CTF from them; it does not change them. If Stage C needs a field `BatchSpec` lacks, STOP and name it.
4. Touch only the files in §3, and only the D-09 option's kernel files. Never edit golden fixtures, the certified rerun folder, or any frozen path in `CLAUDE.md`.
5. **No EnergyPlus runs in M3.** References: Stage A (M1), the M0 golden fixtures (Mac E+), `openubem/outputs/gpusim_m1_fleet.csv`, `openubem/outputs/gpusim_m1_recheck.csv`, `openubem/outputs/gpusim_m0_timing.csv`.
6. Python env is `uv`; tests with `pytest`. No new dependencies beyond M2's. Kernel source carries one comment line per routine citing the E+ file and function; no other comments.
7. Each kernel launch must finish in under 1.0 s at every benchmarked B, largest B = 1,000 (macOS command-buffer watchdog, spec §3.1). If a run-period chunk is slower, shorten it and record the chunk length used.
8. Do not commit. Report measured numbers with the command that produced them. Paths are relative to `/Users/orcunkoraliseri/Desktop/OpenUBEM/`.
9. **Short tests only (owner 2026-11-22):** run only the test named in the task, never the whole `tests/gpusim` suite; M1 and M2 code is frozen and the manager checks it by checksum. Stage A reference results for the 12 P1 cases are computed once in T03 and cached (hourly heating and zone air temperature, float64) in `tests/fixtures/gpusim/stage_a_p1/<cell>.npz`; later runs read the cache. Each test should take under 10 minutes; past 20 minutes, stop it, report the elapsed time, and STOP.

## 3. File layout (only these may be created or changed)
```
openubem/gpusim/backends/kernel/__init__.py
openubem/gpusim/backends/kernel/pack.py                   (T01, structure-of-arrays buffers)
option (a): openubem/gpusim/backends/kernel/s0_common.h, s0_metal.py
option (b): openubem/gpusim/backends/kernel/s0.wgsl, s0_wgpu.py
openubem/gpusim/backends/stage_c.py                       (T02, chunk driver and public entry point)
scripts/gpusim/run_fleet_stage_c.py                       (T04)
scripts/gpusim/bench_stage_c.py                           (T05)
tests/gpusim/test_stage_c_pack.py                         (T01)
tests/gpusim/test_stage_c.py                              (T03, T04)
tests/gpusim/test_isolation.py                            (T06)
tests/fixtures/gpusim/stage_a_p1/                         (T03, Stage A cache, .npz)
openubem/outputs/gpusim_m3_cells.csv                      (T03)
openubem/outputs/gpusim_m3_fleet.csv                      (T04)
openubem/outputs/gpusim_m3_bench.csv                      (T05)
this file, §8 only                                        (progress log)
```

## 4. Pinned dependencies
- Reference engine: EnergyPlus **23.1.0** (source under `/tmp/gpusim_ep231/`, as in M1 §4).
- From `uv.lock` (M2): numpy, pandas, pyarrow, `torch==2.7.1`, the pinned `wgpu`.
- Hardware: Apple M2 Pro (8 performance + 4 efficiency cores), macOS 13. EnergyPlus 23.1 on this Mac runs under Rosetta, so its timings are Rosetta numbers.

## 5. Spec facts this work relies on (with citations)
- **Order per zone timestep:** spec §3.0 steps 1–9, the same order Stage A implements (`backends/numpy_ref.py:247` `_step_one`). Stage C follows that order exactly.
- **Constants:** as in M1 §5 (`IterDampConst = 5.0`; convection re-evaluation at iteration > 0 and % 30 == 0; 1–500 iterations; `MaxAllowedDelTemp = 0.002` K; windows only on iteration 0; initial 23.0 °C; warm-up loads floor 100 W; warm-up 1–25 days with tolerances 0.04 and 0.4 °C; `MaxZoneTempDiff = 0.3` K sub-stepping).
- **Chunking** (spec §3.1): warm-up = one launch per day, convergence checked on the CPU between days (per-building mask; converged buildings stop changing); run period = one launch per 1 to 7 days; state stays in device buffers between launches.
- **Buffers** (spec §3.1): a few structure-of-arrays buffers `[field, building]`, building index contiguous: static building data, weather (shared per site, indexed by a per-building site id), schedules, state, hourly output.
- **Thread layout** (spec §3.1): S0 = one thread per building; ScriptF in device memory.
- **Precision** (spec §3.2): float32; temperatures stored as deviations from 20 °C; `T_i⁴ − T_j⁴` factored as `(T_i − T_j)(T_i + T_j)(T_i² + T_j²)` in ScriptF and exterior longwave; third-order backward difference in difference form; internal-mass CTF in direct form with coefficients rounded so their sums are preserved; hourly energy summed in float32 on the device, annual totals in float64 on the CPU.
- **Float32 gate** (spec §4): annual heating ≤ 0.05 % or ≤ 0.01 kWh/m²; zone air ΔT p99.9 ≤ 0.02 K, max ≤ 0.10 K; warm-up day count locked to Stage A.
- **S0 single-cell gates vs Mac E+** (spec §4): annual ≤ 0.5 % or ≤ 0.05 kWh/m²; hourly CV(RMSE) ≤ 1 %, |NMBE| ≤ 0.1 % over active hours; zone air p99.9 ≤ 0.03 K, max ≤ 0.25 K.
- **Tiers** (spec §4 level 4): P1 = 3 golden cells + 9 S0 variants (as in M2 T03). P2 = the 346 completed fleet cells; on the Mac it is reported against the published Windows values, not gated (owner ruling D6). M1 found the published values wrong on the 5 worst cells (`gpusim_m1_recheck.csv`: Mac E+ 32–92 % above published; Stage A within 0.004 % of Mac E+).
- **Benchmark** (spec §5 row M3): building-years per second against batch size {1, 10, 100, 1,000} and against E+ (owner 2026-11-22: B = 10,000 is skipped on the Mac and measured on Windows in M4) with sizing off. The fair CPU baseline is E+ with sizing off (spec §5 speed-up section); its measured single-run time is in `gpusim_m0_timing.csv` (rows `sizing_off`). The owner caps local E+ at 4 processes.

## 6. Tasks

### T01 — Structure-of-arrays packing
- **What:** `kernel/pack.py`: `pack(batch, weather_by_site, site_index, ctf) -> PackedBatch` and `unpack_state(...)`. Builds the static, weather, schedule, state and output buffers of §5 as float32 (temperatures as deviations from 20 °C) plus int32 index buffers. Weather is stored once per distinct site.
- **Why:** spec §3.1 buffers; spec §3.2 deviation storage.
- **How to test:** `tests/gpusim/test_stage_c_pack.py`: for the 3 golden cells plus V10 and V11 (two extra sites), every packed field converted back to float64 equals the `BatchSpec` / weather source within float32 rounding (relative ≤ 1e-6, or absolute ≤ 1e-5 K for temperatures); the site index maps each building to its own EPW. Report the packed byte size per building.

### T02 — Stage C kernel and chunk driver
- **What:** the S0 step of spec §3.0 (steps 1–9, including sub-stepping and the inside-surface iteration with its per-building convergence) as GPU code in the D-09 framework, one thread per building, looping over the timesteps of one chunk inside the kernel. Start from the M2 spike kernel for step 5. `backends/stage_c.py`: `run_stage_c_batch(batch, weather, ctf=None, record_zone_temp=False, force_warmup_days=None, run_chunk_days=1) -> SimulationResult` (same result type as Stage A): uploads once, runs warm-up day by day with the convergence test on the CPU, then the run period in chunks, downloads the hourly sums, and forms float64 annual totals on the CPU.
- **Why:** spec §5 row M3: Stage C is the speed target; spec §3.1 chunking.
- **How:** follow Stage A routine by routine; each kernel routine's one comment line names the E+ function (and the Stage A function it mirrors). Apply every §3.2 rule.
- **How to test:** a smoke run on the 3 golden cells finishes and returns 8,760 hourly values per cell with no NaN; report the warm-up days and the wall time. Gates come in T03.

### T03 — Parity tier P1 (single cells)
- **What:** run the 12 P1 cases through Stage C twice: (1) with `force_warmup_days` = Stage A's warm-up days, against Stage A; (2) free warm-up, against the Mac E+ golden data.
- **Why:** spec §4 float32 gate and S0 single-cell gates; spec §5 row M3 exit criterion.
- **How:** `tests/gpusim/test_stage_c.py::test_stage_c_p1`. Write `openubem/outputs/gpusim_m3_cells.csv`: cell, annual_stage_a_kwh, annual_stage_c_kwh, rel_c_vs_a, dt_p999_k, dt_max_k (vs Stage A), annual_eplus_kwh, rel_c_vs_eplus, cv_rmse, nmbe, dt_p999_eplus_k, dt_max_eplus_k (vs E+), warmup_days_stage_a, warmup_days_stage_c_free, wall_seconds.
- **Gates:** run (1): the float32 gate per case. Run (2): the S0 single-cell gates per case, and free warm-up days equal to Stage A's.
- **How to test:** `uv run pytest tests/gpusim/test_stage_c.py::test_stage_c_p1 -q` only. Report the worst case for each gate column and the pytest summary line. On a failure: the first timestep where ΔT exceeds 0.02 K, the variables there, and STOP.

### CP1 — STOP and report
- [ ] T01 round-trip within float32 rounding; bytes per building
- [ ] T02 smoke run: no NaN, 8,760 hours per cell
- [ ] T03 all 12 cases pass the float32 gate (locked) and the S0 gates vs Mac E+ (free), worst values listed
- [ ] pytest summary line; `git status --short -- openubem scripts tests` lists only §3 files

### T04 — Parity tier P2 (fleet, 346 cells)
- **What:** `scripts/gpusim/run_fleet_stage_c.py` runs all 346 completed fleet cells (inputs exactly as M1 T06: `eplusout.expidf` + schedules + manifest EPW from `openubem/outputs/eu_certified_rerun_2026-08-28/rep2/`) as one Stage C batch, warm-up locked to `warmup_days_stage_a` from `gpusim_m1_fleet.csv`. Write `openubem/outputs/gpusim_m3_fleet.csv`: cell, annual_published_kwh, annual_stage_a_kwh, annual_stage_c_kwh, rel_c_vs_a, rel_c_vs_published, warmup_days_stage_a.
- **Why:** spec §4 P2 tier (report on the Mac, D6); the Stage C vs Stage A annual check uses our own float64 reference, so it is gated here.
- **Gates:** every cell: Stage C vs Stage A annual heating ≤ 0.05 % or ≤ 0.01 kWh/m² (float32 gate, annual part). Stage C vs published: reported only (median, p99, worst, count > 0.5 %). For the 5 cells in `gpusim_m1_recheck.csv`, also report Stage C vs `mac_eplus_kwh`.
- **How to test:** report the worst rel_c_vs_a with its cell, the fleet wall time, and the published-comparison statistics. A failing cell: STOP and report its first diverging hour.

### T05 — Benchmark
- **What:** `scripts/gpusim/bench_stage_c.py`. Batches of B ∈ {1, 10, 100, 1,000} built (no B = 10,000 on the Mac, owner 2026-11-22) by cycling through the 346 fleet cells in a fixed order (each building keeps its own site's weather; compile each distinct cell once and tile the arrays). For each B: 3 repeats, report the median. Split the wall time into compile (CPU, once per distinct cell), pack + upload, GPU run (warm-up + run period), download + totals; record the longest single launch and the run-chunk length used. Write `openubem/outputs/gpusim_m3_bench.csv`: batch_size, compile_s, upload_s, gpu_s, download_s, total_s, max_launch_s, run_chunk_days, building_years_per_s, speedup_vs_eplus_1proc, speedup_vs_eplus_4proc, speedup_vs_stage_a.
- **Baselines (no new E+ runs):** E+ sizing off, 1 process = 1 / median `wall_s` of the `sizing_off` rows of `gpusim_m0_timing.csv` (measured). E+ sizing off, 4 processes = 4 × that (computed from the measurement; label it "computed" in the report). Stage A = `building_years_per_sec` at the matching or nearest batch size in `gpusim_m1_bench.csv` (B = 160 for B ≥ 1,000; say so).
- **Why:** spec §5 row M3 benchmark; the speed-up estimate of 10,000 cells in about 5–15 s is unverified; M3 measures up to B = 1,000 and M4 measures B = 10,000 on Windows.
- **How to test:** the CSV has 4 rows; every max_launch_s < 1.0; report the B = 1,000 row in full and the B at which Stage C first beats the 4-process E+ baseline.

### T06 — Portability check for the Windows move
- **What:** `tests/gpusim/test_isolation.py`: every module under `openubem/gpusim/` imports nothing from `openubem` outside `openubem.gpusim` (scan the import statements). For option (a): `clang++ -std=c++17 -fsyntax-only -x c++ -DGPUSIM_HOST openubem/gpusim/backends/kernel/s0_common.h` exits 0. Measure the size of the carry list: `openubem/gpusim/`, `scripts/gpusim/`, `tests/gpusim/`, `tests/fixtures/gpusim/`, `docs/docs_ACTIVE/GPU_based_compute/`.
- **Why:** owner plan 2026-11-22: after M3, gpusim moves to the Windows CUDA machine, ideally as a separate project; M4 compiles the same kernel source for CUDA.
- **How to test:** `uv run pytest tests/gpusim/test_isolation.py -q` only; report the import scan result, the clang result (option a), and `du -sh` of each carry-list path.

### CP2 — STOP and report (M3 done when all hold)
- [ ] no file from T01–T03 changed since CP1 (the manager compares checksums; do not rerun the T03 test)
- [ ] T04: all 346 cells pass the annual float32 gate vs Stage A (worst value and cell); published comparison statistics; the 5 re-checked cells vs Mac E+
- [ ] T05: bench CSV rows quoted; every launch under 1.0 s; B = 1,000 building-years per second and speed-ups vs both E+ baselines and Stage A
- [ ] T06: no imports outside `openubem.gpusim`; clang result (option a); carry-list sizes
- [ ] pytest summary line; `git status --short -- openubem scripts tests` lists only §3 files

## 7. Stop-and-report points
- CP1 after T03 (Stage C passes P1).
- CP2 after T06 (fleet, benchmark, portability; M3 done; Mac milestones finished).

## 8. Progress log
Format (append only):
```
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts: <files>
- Deviations: <none, or what and why>
- Test status: <command> -> <summary line>; <measured gate values>
- Notes: <short>
```

#### T01 — Structure-of-arrays packing — completed 2026-11-22
- Artifacts: `openubem/gpusim/backends/kernel/__init__.py`, `openubem/gpusim/backends/kernel/pack.py`, `tests/gpusim/test_stage_c_pack.py`
- Deviations: none
- Test status: `uv run --no-sync pytest tests/gpusim/test_stage_c_pack.py -q -s` -> `1 passed, 1 warning in 0.51s`; all static/weather/schedule/state fields round-trip within `<= 1e-6` rel (`<= 1e-5 K` temps), 5/5 sites mapped cleanly, CTF sum error `<= 5e-7`, `building_bytes_per_bldg=73084.0 B`, `amortized_total_bytes_per_bldg=1759629.6 B`, `weather_bytes_per_site=1686528.0 B`.
- Notes: Temperatures stored as float32 deviations from `20.0 C` (`293.15 K` for glazing node temperatures); CTF coefficients rounded with sum-preservation; height-lapse offsets precomputed in float64.

#### T02 — Stage C kernel and chunk driver — completed 2026-11-22
- Artifacts: `openubem/gpusim/backends/kernel/s0_common.h`, `openubem/gpusim/backends/kernel/s0_metal.py`, `openubem/gpusim/backends/stage_c.py`
- Deviations: none
- Test status: `clang++ -std=c++17 -fsyntax-only -x c++ -DGPUSIM_HOST openubem/gpusim/backends/kernel/s0_common.h` -> exit 0; smoke test on the 3 golden cells (`run_chunk_days=1`) -> `shape=(3, 8760)`, zero NaN, `warmup_days=[3, 3, 3]`, `annual_kwh=[23274.935627, 429457.456434, 177983.899679]`, `wall_s=27.1501`.
- Notes: Implements S0 §3.0 steps 1–9 and §3.2 precision rules (20 °C deviations, factored `T_i⁴ - T_j⁴`, difference-form 3rd-order backward difference, sum-preserving CTF, float32 hourly sums, float64 CPU annual totals).

#### T03 — Parity tier P1 (single cells) — completed 2026-11-22
- Artifacts: `tests/gpusim/test_stage_c.py`, `tests/fixtures/gpusim/stage_a_p1/` (12 `.npz`), `openubem/outputs/gpusim_m3_cells.csv`
- Deviations: none
- Test status: `uv run --no-sync pytest tests/gpusim/test_stage_c.py::test_stage_c_p1 -q` -> `1 passed, 1 warning in 60.70s` (cached Stage A, Stage C locked+free `wall=58.190 s`); initial Stage A cache generation + P1 run: `1 passed, 1 warning in 157.18s`; all 12 cases pass both float32 gates (locked warmup) and S0 single-cell gates vs Mac E+ (free warmup), with `warmup_days_stage_c_free == warmup_days_stage_a` on 12/12 cases (`2` on V03, `3` on the remaining 11).
- Notes: Worst values — `|rel_c_vs_a|=1.021e-04` (`V04`), `dt_p999_k=0.004657 K` (`V04`), `dt_max_k=0.005206 K` (`V04`); vs Mac E+: `|rel_c_vs_eplus|=5.966e-05` (`V07`), `cv_rmse=6.020e-05` (`V07`), `|nmbe|=5.818e-05` (`V07`), `dt_p999_eplus_k=0.001000 K` (`V07`), `dt_max_eplus_k=0.001028 K` (`V07`). Stopped at CP1.

#### T04 — Parity tier P2 (fleet, 346 cells) — completed 2026-11-22
- Artifacts: `scripts/gpusim/run_fleet_stage_c.py`, `openubem/outputs/gpusim_m3_fleet.csv`
- Deviations: none
- Test status: `uv run --no-sync python scripts/gpusim/run_fleet_stage_c.py` -> exit 0 (`346/346` pass annual float32 gate vs Stage A); worst `|rel_c_vs_a|=0.009771%` (`-9.77089123e-05`) on `uk__GB.ENG.MFH.08.Gen.ReEx.001.001__f100`; `fleet_wall_s=56.128 s` (`gpu_s=54.827 s`, `max_launch_s=0.192 s`, `compile_s=1.776 s`).
- Notes: Stage C vs published (N=346): median `|rel|=0.0033%` (signed `-0.0025%`), p99 `32.1319%`, worst `91.6283%`, count > 0.5% = `65`; re-checked 5 cells vs `mac_eplus_kwh` range `-0.002524%` to `-0.003698%`.

#### T05 — Benchmark — completed 2026-11-22
- Artifacts: `scripts/gpusim/bench_stage_c.py`, `openubem/outputs/gpusim_m3_bench.csv`
- Deviations: Owner updated spec to skip `B = 10,000` on the Mac (`B ∈ {1, 10, 100, 1,000}`, 4 rows).
- Test status: `uv run --no-sync python scripts/gpusim/bench_stage_c.py` -> exit 0 (4 rows, all `max_launch_s < 1.0`: `0.449 s`, `0.701 s`, `0.779 s`, `0.573 s`); `B=1000` (`run_chunk_days=3`): `total_s=62.651 s`, `15.961359 bldg-yr/s`, `41.38x` vs E+ 1-proc (measured `0.385768 bldg-yr/s`), `10.34x` vs E+ 4-proc (computed `1.543074 bldg-yr/s`), `36.41x` vs Stage A (`B=160` `0.438335 bldg-yr/s`).
- Notes: Stage C first beats the computed 4-process E+ baseline at `B = 100` (`2.167815 bldg-yr/s`, `1.40x`).

#### T06 — Portability check for the Windows move — completed 2026-11-22
- Artifacts: `tests/gpusim/test_isolation.py`
- Deviations: none
- Test status: `uv run --no-sync pytest tests/gpusim/test_isolation.py -q` -> `3 passed, 1 warning in 0.23s` (25 Python modules under `openubem/gpusim/`, 0 imports outside `openubem.gpusim`); `clang++ -std=c++17 -fsyntax-only -x c++ -DGPUSIM_HOST openubem/gpusim/backends/kernel/s0_common.h` -> exit 0.
- Notes: Carry-list `du -sh`: `openubem/gpusim/` `772K`, `scripts/gpusim/` `220K`, `tests/gpusim/` `500K`, `tests/fixtures/gpusim/` `279M`, `docs/docs_ACTIVE/GPU_based_compute/` `780K`. Stopped at CP2.
