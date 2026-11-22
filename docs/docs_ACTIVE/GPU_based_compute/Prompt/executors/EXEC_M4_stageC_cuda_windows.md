# EXEC M4 — gpusim Stage C on Windows CUDA, rung S0

## 1. Header
- **Slug:** `gpusim-M4`. **Date:** 2026-11-22. **Approved by owner:** 2026-11-22 ("write the M4 plan and copy list").
- **Starts only after** M3 is done (`EXEC_M3_stageC_metal_s0.md` CP2 audited by the manager), the M2/M3 code is committed and pushed, and the copy list below is done on the Windows machine.
- **D-10 (Windows EnergyPlus recheck):** ruled by the owner 2026-11-22: `D-10 = (a)`, run the T04 EnergyPlus 23.1 runs (65 + 3 cells) locally on the Windows machine, one pool of at most 10 processes. Basis: the published fleet values are wrong for 65 cells (M1 recheck), and Speed runs Linux, so it cannot measure the Windows platform gap that D6 asks for. This is the only exception to the "always on Speed" rule in M4.
- **Spec (the DESIGN):** `docs/docs_ACTIVE/GPU_based_compute/BUILD_SPEC_gpu_heat_balance_engine.md` rev. 3: §3.1 (chunking, timeouts, framework line 159), §3.2 (precision; CUDA `--fp64` line 176), §4 (gates, P1/P2 tiers, lines 218–242), §5 row M4 (line 254), risk table (line 305), §9 D6 (lines 13, 324, 340).
- **D-09 (ruled 2026-11-22):** PyTorch host + the shared C header `s0_common.h`. M4 compiles the **same header** for CUDA; the physics in it does not change.
- **Executor:** one session with repo access on the Windows CUDA machine, repo root `C:\Users\o_iseri\Desktop\OpenUBEM\`. **NO sub-agents.**
- **What M4 delivers:** Stage C running on the NVIDIA GPU, passing P1 and the P2 fleet gates, and a benchmark table on that GPU.
- **After M4 (owner 2026-11-22):** with the Windows desktop and the Speed cluster both reachable, a larger test on more buildings follows. The manager plans it after M4 CP2; nothing in M4 runs on Speed. Speed GPU jobs use whatever GPU is free (A100 MIG slices, V100 or smaller); never wait for a large card (owner 2026-11-22).

### Copy list (done by the owner and the manager before T01; sizes measured on the Mac 2026-11-22)
1. **Mac, after M3 CP2:** the manager commits and pushes the M2/M3 code (`openubem/gpusim/`, `scripts/gpusim/`, `tests/gpusim/`, `pyproject.toml`, `uv.lock`, result CSVs `openubem/outputs/gpusim_m2_*.csv`, `gpusim_m3_*.csv`, and this folder). Today these are untracked, so a clone without this step has no M2/M3 code.
2. **Windows:** `git clone` (or `git pull`) the repo to `C:\Users\o_iseri\Desktop\OpenUBEM\`. This brings the code, the golden Parquet fixtures, and the EPW folder `openubem/data/weather/` (64 MB, 692 files).
3. **By hand (USB or cloud drive), not on GitHub:**
   - `tests/fixtures/gpusim/` whole folder (279 MB today plus the M3 Stage A cache): all `*.npz` files are gitignored, so the spike inputs (`spike/`, 15 files) and the Stage A cache (`stage_a_p1/`, 12 files) only arrive this way. Copy over the cloned folder.
   - `openubem/outputs/eu_certified_rerun_2026-08-28/rep2/` whole folder (195 MB: `manifests/` with 395 files, `schedules/`, and 396 cell folders, 346 of them complete with `eplusout.expidf`, `eplusout.csv`, `eplusout.eio`). GitHub has only the manifests, so the fleet check cannot run from the clone alone.
4. **Not needed:** `openubem/outputs/gpusim_golden_runs/` (8.7 GB raw Mac E+), `rep1/`, `rep3/`.
5. **On the Windows machine already or installed by the owner:** NVIDIA driver, EnergyPlus 23.1.0 (used for the published rerun), `uv`, git.

## 2. Hard rules for the executor
1. Execute the tasks in order. Do not write plans, do not redesign. If the spec and the E+ 23.1.0 source disagree, the **E+ source wins**: STOP, quote both, and wait.
2. **No fudge.** No fitted multipliers, tuned iteration counts, or loosened tolerances. A failed gate is reported with diagnostics and STOP.
3. **Frozen:** everything M1–M3 built, except the exact changes §3 allows. The physics in `s0_common.h` does not change: only compiler qualifier macros for CUDA may be added (the manager diffs it against the M3 CP2 checksum).
4. Touch only the files in §3. Never edit golden fixtures, the certified rerun folder, or any frozen path in `CLAUDE.md`.
5. **EnergyPlus runs only in T04, only as T04 says (D-10 = (a)).** Raw E+ output goes under `openubem/outputs/gpusim_golden_runs/m4_windows/` (already gitignored); only the CSV of §3 is kept in the repo.
6. Python env is `uv`; tests with `pytest`. Kernel source keeps one comment line per routine citing the E+ function; no other comments.
7. **GPU timeout (spec §3.1, risk table line 305):** Windows resets the GPU after 2 s by default (TDR). Each kernel launch must finish in under 0.2 s at B = 10,000 (10× margin). If a run-period chunk is slower, shorten it and record the length used. If a single warm-up-day launch is slower, STOP and report.
8. Do not commit. Report measured numbers with the command that produced them. Paths are relative to the repo root.
9. **Short tests only (owner 2026-11-22):** run only the test named in the task, never the whole `tests/gpusim` suite. Stage A results come from the cache (`tests/fixtures/gpusim/stage_a_p1/`) and `openubem/outputs/gpusim_m1_fleet.csv`; never rerun Stage A on the fleet. Each test should take under 10 minutes; past 20 minutes, stop it, report the elapsed time, and STOP.

## 3. File layout (only these may be created or changed)
```
pyproject.toml, uv.lock                                    (T01, CUDA torch wheel and cupy on win32 only)
openubem/gpusim/backends/kernel/s0_common.h                (T02, CUDA qualifier macros only)
openubem/gpusim/backends/kernel/s0_cuda.py                 (T02, compile and launch on CUDA)
openubem/gpusim/backends/stage_c.py                        (T02, add device="mps"|"cuda", default "mps")
scripts/gpusim/run_fleet_stage_c.py                        (T05, add --device and --out)
scripts/gpusim/bench_stage_c.py                            (T06, add --device and --out)
scripts/gpusim/recheck_windows.py                          (T04)
tests/gpusim/test_windows_setup.py                         (T01)
tests/gpusim/test_stage_c_cuda.py                          (T02, T03)
openubem/outputs/gpusim_m4_setup.csv                       (T01)
openubem/outputs/gpusim_m4_cells.csv                       (T03)
openubem/outputs/gpusim_m4_win_eplus.csv                   (T04)
openubem/outputs/gpusim_m4_fleet.csv                       (T05)
openubem/outputs/gpusim_m4_bench.csv                       (T06)
this file, §8 only                                         (progress log)
```

## 4. Pinned dependencies
- Reference engine: EnergyPlus **23.1.0** on Windows (native, not Rosetta). Record its path and build string in T01.
- `torch==2.7.1` stays. On `sys_platform == 'win32'` only, take it from the PyTorch CUDA 12.6 index (`https://download.pytorch.org/whl/cu126`); if the GPU is an RTX 50-series (compute capability 12.x), use the CUDA 12.8 index instead. The Mac lock entries must not change.
- `cupy-cuda12x`, latest release at T01, pinned exactly, win32 only. It compiles the header at run time (NVRTC), so no MSVC and no CUDA toolkit are needed if it works (spec line 159 allows CuPy `RawKernel`). Buffers pass between torch and CuPy without copies (DLPack).
- Hardware: unknown until T01 (GPU model, memory, compute capability, driver, CPU cores).

## 5. Spec facts this work relies on (with citations)
- **Same source (spec §5 row M4, line 254):** Stage C CUDA is built from the same header as Metal; gates pass on CUDA, including the P2 fleet gates against the Windows reference; recheck the Mac–Windows gap; benchmark table on that GPU.
- **Order, constants, chunking, buffers, precision:** as in M3 §5. One thread per building. Float32 by default; float64 is available on CUDA but is a diagnosis switch only (spec line 176), not built in M4.
- **Float32 gate (spec §4):** annual heating ≤ 0.05 % or ≤ 0.01 kWh/m²; zone air ΔT p99.9 ≤ 0.02 K, max ≤ 0.10 K; warm-up day count locked to Stage A.
- **S0 single-cell gates vs Mac E+ (spec §4):** annual ≤ 0.5 % or ≤ 0.05 kWh/m²; hourly CV(RMSE) ≤ 1 %, |NMBE| ≤ 0.1 % over active hours; zone air p99.9 ≤ 0.03 K, max ≤ 0.25 K.
- **S0 fleet gates (spec §4, P2 enforced on Windows by D6):** annual heating vs E+: median ≤ 0.05 % or ≤ 0.02 kWh/m²; p99 ≤ 0.2 %; worst cell ≤ 0.5 % or ≤ 0.05 kWh/m².
- **D6 and the published values:** Mac E+ gives +0.659 % more heating than the published Windows rerun on one cell (spec line 340). M1 found Stage A vs published > 0.5 % on 65 of 346 cells (`gpusim_m1_fleet.csv`, `rel_diff`; median 1.2e-5, p99 0.32); the 5 worst re-run on Mac E+ were 32–92 % above published, with Stage A within 0.004 % of Mac E+ (`gpusim_m1_recheck.csv`). So the published values alone cannot be the P2 reference: T04 re-runs those cells on Windows E+.
- **Benchmark (spec §5):** building-years per second against B ∈ {1, 10, 100, 1,000, 10,000}, and against E+ on all cores.

## 6. Tasks

### T01 — Windows setup and copy check
- **What:** add the win32 CUDA torch source and `cupy-cuda12x` to `pyproject.toml`, `uv sync`. `tests/gpusim/test_windows_setup.py`: (1) `torch.cuda.is_available()`; (2) a one-line CuPy `RawKernel` compiles and runs; (3) file counts of the copied folders: `tests/fixtures/gpusim/spike/` 15 `.npz`, `tests/fixtures/gpusim/stage_a_p1/` 12 `.npz`, `rep2/manifests/` 395 files, 346 cell folders with `eplusout.expidf`, `eplusout.csv` and `eplusout.eio`, and `rep2/schedules/` non-empty; (4) Stage A on CPU for the golden cell `it__IT.MidClim.SFH.02.Gen.ReEx.001.001__f100`, annual heating vs the Mac Stage A cache ≤ 1e-6 relative (same float64 code on another platform). Write `openubem/outputs/gpusim_m4_setup.csv` with one row: gpu_name, gpu_memory_gb, compute_capability, driver_version, cuda_runtime, torch_version, cupy_version, cpu_cores, tdr_delay_s (from `reg query HKLM\System\CurrentControlSet\Control\GraphicsDrivers /v TdrDelay`; absent = 2), eplus_path, eplus_build, stage_a_rel_win_vs_mac.
- **Why:** §1 copy list; spec line 159; rule 7.
- **How to test:** `uv run pytest tests/gpusim/test_windows_setup.py -q` only. If CuPy fails to compile because CUDA libraries are missing, STOP and quote the error (the manager decides between installing the CUDA 12 toolkit and `load_inline`).

### T02 — Stage C on CUDA from the same header
- **What:** `kernel/s0_cuda.py` compiles `s0_common.h` with CuPy `RawKernel` and launches it on torch CUDA buffers (DLPack, no copies). In the header, add only the qualifier macros CUDA needs (for example kernel and device function qualifiers, address-space words mapped to nothing). `stage_c.py`: `run_stage_c_batch(..., device="mps")` gains `device="cuda"`, which routes packing output to CUDA buffers and launches through `s0_cuda.py`; the chunk driver, warm-up test and totals stay as in M3.
- **Why:** spec §5 row M4 ("from the same source"); D-09.
- **How to test:** `uv run pytest tests/gpusim/test_stage_c_cuda.py::test_smoke -q`: the 3 golden cells finish on CUDA, 8,760 hourly values each, no NaN; report warm-up days, wall time, and the longest single launch. Report `git diff --stat` of `s0_common.h` (macro lines only).

### T03 — Parity tier P1 on CUDA
- **What:** the 12 P1 cases through Stage C on CUDA twice, as M3 T03: (1) warm-up locked to Stage A, against the Stage A cache; (2) free warm-up, against the Mac E+ golden data. Write `openubem/outputs/gpusim_m4_cells.csv` with the M3 T03 columns plus `annual_stage_c_metal_kwh` and `rel_cuda_vs_metal` (from `gpusim_m3_cells.csv`, information only).
- **Gates:** run (1) the float32 gate per case; run (2) the S0 single-cell gates per case, and free warm-up days equal to Stage A's.
- **How to test:** `uv run pytest tests/gpusim/test_stage_c_cuda.py::test_p1 -q` only. Report the worst case per gate column and the pytest summary line. On a failure: the first timestep where ΔT exceeds 0.02 K, the variables there, and STOP.

### CP1 — STOP and report
- [ ] T01 setup row quoted; copy counts match; Stage A Windows vs Mac within 1e-6
- [ ] T02 smoke: no NaN, 8,760 hours per cell; header diff is macros only; longest launch
- [ ] T03 all 12 cases pass the float32 gate (locked) and the S0 gates vs Mac E+ (free), worst values listed
- [ ] pytest summary lines; `git status --short -- openubem scripts tests pyproject.toml uv.lock` lists only §3 files

### T04 — Windows EnergyPlus recheck (D6; D-10 = (a))
- **What:** `scripts/gpusim/recheck_windows.py`: the cell list is the union of (i) every cell with `abs(rel_diff) > 0.005` in `gpusim_m1_fleet.csv` (65 cells) and (ii) the 3 golden cells. Prepare each run as `scripts/gpusim/recheck_worst.py` does (reuse its preparation, error-summary and hourly-reading functions by import; do not edit it), with the Windows E+ path from T01 and the same flags (`-x -r -w … -d …`). Run as one local pool, at most 10 processes (D-10 = (a)). Write `openubem/outputs/gpusim_m4_win_eplus.csv`: cell, published_kwh, mac_eplus_kwh (from `gpusim_m1_recheck.csv` or the golden fixtures, empty if none), win_eplus_kwh, stage_a_kwh, rel_win_vs_published, rel_win_vs_mac, rel_stage_a_vs_win, warmup_days_eplus, warnings, severe, wall_s.
- **Why:** spec line 254 and D6 (recheck the Mac–Windows gap on Windows); §5 (the published values cannot be the reference for these cells).
- **How to test:** every run ends "EnergyPlus Completed Successfully" with 0 severe errors; report the count of runs, the median and worst `rel_win_vs_mac`, the median and worst `rel_win_vs_published`, and the median wall_s. If a run fails, report its error tail and STOP.

### T05 — Parity tier P2 on CUDA (fleet, 346 cells, gated)
- **What:** `run_fleet_stage_c.py --device cuda --out openubem/outputs/gpusim_m4_fleet.csv`: all 346 cells as one Stage C batch, inputs as M3 T04, warm-up locked to `warmup_days_stage_a`. Reference per cell: `win_eplus_kwh` from T04 where the cell was re-run, else the published value. Columns: cell, reference_kwh, reference_source (`win_eplus` or `published`), annual_stage_a_kwh, annual_stage_c_kwh, rel_c_vs_a, rel_c_vs_reference, floor_area_m2, warmup_days_stage_a.
- **Gates:** every cell: Stage C vs Stage A annual ≤ 0.05 % or ≤ 0.01 kWh/m². Fleet vs reference: the S0 fleet gates of §5 (median, p99, worst cell with its absolute floor).
- **How to test:** report the worst rel_c_vs_a with its cell, the fleet median / p99 / worst rel_c_vs_reference with cells, the count of cells using each reference source, and the fleet wall time. A failing gate: STOP and report the failing cells.

### T06 — Benchmark on the CUDA GPU
- **What:** `bench_stage_c.py --device cuda --out openubem/outputs/gpusim_m4_bench.csv`, same batches, repeats, time split and columns as M3 T05. Baselines (no new E+ runs): Windows E+ 1 process = 1 / median `wall_s` of T04 (as built, includes the sizing pass; label it so); all cores = cpu_cores from T01 × that (label "computed"); Mac Stage C = the matching row of `gpusim_m3_bench.csv`.
- **Why:** spec §5 row M4 benchmark table.
- **How to test:** the CSV has 5 rows; every max_launch_s < 0.2; report the B = 10,000 row in full, the speed-up vs Windows E+ on all cores, and CUDA vs Mac Stage C at B = 1,000 (the Mac skips B = 10,000, owner 2026-11-22).

### CP2 — STOP and report (M4 done when all hold)
- [ ] no file from T01–T03 changed since CP1 (the manager compares checksums; do not rerun the T03 test)
- [ ] T04: run count, 0 severe; Mac–Windows gap (median, worst); Windows vs published (median, worst)
- [ ] T05: all 346 cells pass the float32 gate vs Stage A; fleet median / p99 / worst vs reference pass, with values and cells
- [ ] T06: bench rows quoted; every launch under 0.2 s; B = 10,000 speed-ups
- [ ] `git status --short -- openubem scripts tests pyproject.toml uv.lock` lists only §3 files

## 7. Stop-and-report points
- CP1 after T03 (CUDA build works and passes P1).
- CP2 after T06 (Windows recheck, fleet gates, benchmark; M4 done).

## 8. Progress log
Format (append only):
```
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts: <files>
- Deviations: <none, or what and why>
- Test status: <command> -> <summary line>; <measured gate values>
- Notes: <short>
```
