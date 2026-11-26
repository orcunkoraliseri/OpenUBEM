# EXEC M2 — gpusim Stage B on the Mac GPU (MPS) + framework spike for Stage C

## 1. Header
- **Slug:** `gpusim-M2`. **Date:** 2026-11-22. **Approved by owner:** 2026-11-22 ("write M2 and M3").
- **Starts only after M1 is done** (M1 CP5 audited by the manager on 2026-11-22, commit `8c33f1c7b`).
- **Spec (the DESIGN for this work):** `docs/docs_ACTIVE/GPU_based_compute/BUILD_SPEC_gpu_heat_balance_engine.md` rev. 3: §3.0 (timestep order), §3.1 (backends, chunking, framework candidates, spike exit criterion), §3.2 (precision), §4 (float32 gate, row "Stage C float32 vs Stage A"), §5 row M2, §6 (layout).
- **Executor:** a Gemini session with repo access, run by the owner through `EXEC_MASTER_gpusim_m2_m3.md`. **NO sub-agents.**
- **What M2 delivers:** (a) Stage B: the Stage A engine running on the Mac GPU in float32 through PyTorch, as a check that the shared physics works on a GPU device; no speed target. (b) The framework spike: the same small kernel written in the two candidate frameworks, so the owner can choose the Stage C framework (decision D-09) at CP2.
- **Mac only.** The Windows CUDA machine is not available until M4 (owner plan 2026-11-22). Where the spec's spike criterion says "runs on both machines", M2 checks the Mac half and a CUDA-portability proxy (T05); the CUDA half is checked in M4.

## 2. Hard rules for the executor
1. Execute the tasks in order. Do not write plans, do not redesign. If the spec and the E+ 23.1.0 source disagree, the **E+ source wins**: STOP, quote both, and wait.
2. **No fudge.** No fitted multipliers, tuned iteration counts or loosened tolerances. A failed gate is reported with diagnostics and STOP. Tolerances change only in spec §4, by the manager.
3. **The physics files are shared and frozen:** do not edit anything under `openubem/gpusim/physics/`, nor `backends/numpy_ref.py`, `compile.py`, `weather.py`, `schedules.py`, `ctf.py`, `viewfactors.py`, `subset.py`, `writer.py`. Stage B calls the physics functions unchanged through an `xp` namespace shim (T02). If a physics function cannot run through the shim, STOP and quote the function and the error.
4. Touch only the files in §3. Never edit `tests/fixtures/gpusim/golden/` (read only), the certified rerun folder (read only), or any frozen path in `CLAUDE.md`.
5. **No EnergyPlus runs in M2.** The references are Stage A (float64, M1) and the M0 golden fixtures (Mac E+).
6. Python env is `uv`; tests with `pytest`. The only new dependencies are the ones T01 adds. Kernel source files (`.metal`, `.h`, `.wgsl`) carry one comment line per routine citing the E+ file and function; no other comments. Python follows the M1 docstring rule (one-line E+ citation per physics routine).
7. Arrays are batched with the building on the first axis (`[B, ...]`). Per-building convergence uses masks, never a Python loop over buildings.
8. MPS has no float64. On `mps`, Stage B runs float32. Float64 runs use `device="cpu"`.
9. Do not commit. Report measured numbers with the command that produced them. Paths are relative to `/Users/orcunkoraliseri/Desktop/OpenUBEM/`.
10. **Short tests only (owner 2026-11-22, after CP1):** from T04 on, run only the test named in the task, never the whole `tests/gpusim` suite. T04–T06 add new files only, so the M1 and T03 results cannot change; the manager checks this. Each test should take under 10 minutes; past 20 minutes, stop it, report the elapsed time, and STOP.

## 3. File layout (only these may be created or changed)
```
pyproject.toml, uv.lock                                   (T01, via uv add only)
openubem/gpusim/backends/xp_torch.py                      (T02)
openubem/gpusim/backends/torch_batched.py                 (T02, T03)
openubem/gpusim/backends/kernel/spike_common.h            (T04)
openubem/gpusim/backends/kernel/spike_metal.py            (T04)
openubem/gpusim/backends/kernel/spike_iter.wgsl           (T05)
openubem/gpusim/backends/kernel/spike_wgpu.py             (T05)
scripts/gpusim/capture_spike_inputs.py                    (T04)
scripts/gpusim/run_spike.py                               (T06)
tests/gpusim/test_stage_b.py                              (T02, T03)
tests/gpusim/test_spike.py                                (T04, T05)
tests/fixtures/gpusim/spike/                              (T04, captured inputs, .npz, ≤ 20 MB total)
openubem/outputs/gpusim_m2_stage_b.csv                    (T03)
openubem/outputs/gpusim_m2_spike.csv                      (T06)
this file, §8 only                                        (progress log)
```

## 4. Pinned dependencies
- Reference engine: EnergyPlus **23.1.0** (read the source under `/tmp/gpusim_ep231/` as in M1 §4; re-download if missing).
- Existing: numpy, pandas, pyarrow from `uv.lock`.
- **New (T01):** `torch==2.7.1` (MPS backend and `torch.mps.compile_shader`); `wgpu` pinned to the newest release published at least 2 weeks before today (write the exact version into the T01 progress-log entry).
- Hardware: Apple M2 Pro (8 performance + 4 efficiency cores), macOS 13 (Darwin 22.6).

## 5. Spec facts this work relies on (with citations)
- **Stage B role** (spec §3.1 table): PyTorch, same structure as Stage A, `device ∈ {mps, cuda, cpu}`; verification bridge only; not a speed target.
- **Spike** (spec §3.1 "Framework"): candidates (a) PyTorch host + one shared C header compiled as Metal (`torch.mps.compile_shader`) and later CUDA (`load_inline` or CuPy `RawKernel`); (b) wgpu-py / WGSL. Taichi, JAX, MLX, Warp are dropped. Exit criterion: the S0 kernel step from Stage A runs from one source and the float32 gate passes on 5 cells.
- **Thread layout** (spec §3.1): S0 = one thread per building; ScriptF in device memory.
- **Precision** (spec §3.2): temperatures as deviations from 20 °C; `T_i⁴ − T_j⁴` factored as `(T_i − T_j)(T_i + T_j)(T_i² + T_j²)`; third-order backward difference in difference form; hourly energy summed in float32, annual totals in float64 on the CPU; S0 internal-mass CTF in direct form. These bind the spike kernels (T04, T05). Stage B (T02, T03) runs the shared physics unchanged and is not required to apply them.
- **Inside-surface iteration** (spec §3.0 step 5; `HeatBalanceSurfaceManager.cc::CalcHeatBalanceInsideSurf2CTFOnly`): windows only on iteration 0; ScriptF exchange each iteration; damping `IterDampConst = 5.0`; stop when max change ≤ `MaxAllowedDelTemp = 0.002` K, at least 1 and at most 500 iterations; inside convection re-evaluated when iteration > 0 and iteration % 30 == 0. The Stage A implementation is `backends/numpy_ref.py:365` onward.
- **Float32 gate** (spec §4): annual heating ≤ 0.05 % or ≤ 0.01 kWh/m²; zone air ΔT p99.9 ≤ 0.02 K, max ≤ 0.10 K; warm-up day count locked to Stage A in this test.
- **S0 single-cell gates vs Mac E+** (spec §4, as in M1 T05): annual ≤ 0.5 % or ≤ 0.05 kWh/m²; hourly CV(RMSE) ≤ 1 %, |NMBE| ≤ 0.1 % over active hours (either engine > 1 W/m²); zone air p99.9 ≤ 0.03 K, max ≤ 0.25 K.
- **P1 cases** (spec §4 level 4): the 3 golden cells and the 9 S0 variants V01, V03, V04, V06, V07, V09, V10, V11, V14 under `tests/fixtures/gpusim/golden/`; V15 is S1 and is not run. M1 results for them: `openubem/outputs/gpusim_m1_cells.csv`.
- **Stage A entry point:** `openubem/gpusim/backends/numpy_ref.py:122` `run_stage_a_batch(batch, weather, ctf=None, record_zone_temp=False, xp=np)`. The physics modules call these namespace names (measured 2026-11-22): `abs, any, asarray, clip, concatenate, exp, float64, full_like, log, maximum, minimum, power, sqrt, stack, sum, where`.

## 6. Tasks

### T01 — Pin the GPU dependencies
- **What:** add `torch==2.7.1` and the pinned `wgpu` with `uv add`.
- **Why:** Stage B and candidate (a) need PyTorch with MPS; candidate (b) needs wgpu-py (spec §3.1).
- **How:** `uv add torch==2.7.1 wgpu==<version>`. Then run `uv run python -c "import torch, wgpu; print(torch.__version__, torch.backends.mps.is_available(), hasattr(torch.mps, 'compile_shader'), wgpu.__version__)"` and `uv run python -c "import wgpu; print(wgpu.gpu.request_adapter_sync().info)"`.
- **How to test:** the first command prints `2.7.1 True True <version>`; the second names the Apple M2 Pro adapter with the Metal backend. Anything else: STOP and quote the output. Report the `uv.lock` diff as a count of added packages.

### T02 — Namespace shim and Stage B on CPU float64
- **What:** `backends/xp_torch.py`: a namespace object that maps the 16 names in §5 to torch for a given `device` and `dtype` (for example `power → torch.pow`, `concatenate → torch.cat`, `clip → torch.clamp`, `asarray → torch.as_tensor(..., device, dtype)`, `float64 →` the working dtype). `backends/torch_batched.py`: `run_stage_b_batch(batch, weather, ctf=None, record_zone_temp=False, device="mps", dtype=torch.float32, force_warmup_days=None, capture_steps=None)`, a line-by-line port of `run_stage_a_batch` that keeps its loop structure and calls the same physics functions through the shim. It returns the same `SimulationResult` (arrays moved to NumPy float64). `force_warmup_days` (`[B]` ints) makes each building take exactly that many warm-up days. `capture_steps` (T04) records the inputs and outputs of the inside-surface iteration at the listed run-period step indices.
- **Why:** spec §3.1 and §6: Stage B shares the equations with Stage A; running it in float64 on the CPU first separates porting errors from float32 errors.
- **How:** copy the order of `numpy_ref.py` exactly. Host-side work that Stage A does in NumPy before the loop (schedules, gains, weather stacking) may stay NumPy and be moved to the device once. Convergence checks may call `.item()` (no speed target).
- **How to test:** `tests/gpusim/test_stage_b.py::test_stage_b_cpu_float64_equals_stage_a`: the 3 golden cells as one batch, `device="cpu"`, `dtype=torch.float64`, against `run_stage_a_batch` on the same inputs. Gate: annual heating relative difference ≤ 1e-9, hourly heating max abs difference ≤ 1e-3 J, zone air temperature max abs difference ≤ 1e-8 K, identical warm-up days. Report the three measured maxima. On a failure, report the first timestep and variable that diverge, and STOP.

### T03 — Stage B float32: full year on CPU, one week on MPS (rewritten 2026-11-22)
- **Rewritten by the manager at owner request (2026-11-22):** the first version ran the full year for all 12 cases on MPS and was stopped after 1 h 40 min without finishing. Tests must be short. The full-year float32 check now runs on the CPU; MPS runs one week and is compared with Stage A on that week.
- **What:**
  1. Add `run_days=None` to `run_stage_b_batch`: when set, the run period stops after that many days (warm-up unchanged), and the returned hourly arrays have `run_days × 24` hours. No other change to `torch_batched.py`.
  2. **Year test (CPU float32):** the 12 P1 cases as one batch (B = 12, per-building weather) on `device="cpu"`, `dtype=torch.float32`, full year, `force_warmup_days` = Stage A's warm-up days. Stage A runs the same 12 as the reference in the same test.
  3. **Week test (MPS float32):** the same 12 cases, same batch, on `device="mps"`, `dtype=torch.float32`, `run_days=7`, same `force_warmup_days`. Reference: Stage A's full-year results from step 2, sliced to the first 7 × 24 hours (the first week does not depend on later days).
- **Why:** spec §5 row M2 exit criterion (Stage B matches Stage A to the float32 gate). The year test checks float32 rounding over a whole year; the week test checks that the GPU device gives the same numbers as Stage A.
- **How:** `tests/gpusim/test_stage_b.py::test_stage_b_cpu_float32_year_p1` and `::test_stage_b_mps_float32_week_p1` (replace `test_stage_b_mps_float32_p1`). Compute the S0 single-cell gates vs Mac E+ on the year test, as in M1 T05. Write `openubem/outputs/gpusim_m2_stage_b.csv`, one row per cell: cell, annual_stage_a_kwh, annual_stage_b_kwh, rel_b_vs_a, dt_p999_k, dt_max_k (year, CPU float32 vs Stage A), annual_eplus_kwh, rel_b_vs_eplus, cv_rmse, nmbe (year vs E+), week_stage_a_kwh, week_mps_kwh, week_rel_mps_vs_a, week_dt_p999_k, week_dt_max_k (week, MPS vs Stage A), warmup_days_stage_a, year_cpu_wall_seconds, week_mps_wall_seconds.
- **Gates:** year: the float32 gate (§5) per case vs Stage A, and the S0 single-cell gates vs Mac E+ per case. Week: the same float32 gate thresholds applied to the week's heating total and the week's zone air ΔT.
- **Time limit:** each test should take under 15 minutes. Run each test alone first (`uv run pytest tests/gpusim/test_stage_b.py::<name> -q`). If one passes 30 minutes, stop it, report the elapsed time, and STOP.
- **How to test:** then `uv run pytest tests/gpusim -q` (all M1 tests must still pass). Report the worst case for each gate column, both wall times, and the full pytest summary line. A failure: report the first timestep where ΔT exceeds 0.02 K, the variables there, and STOP. Do not apply the §3.2 rules to the shared physics to make it pass; report.

### CP1 — STOP and report
- [x] T01 versions printed (`torch 2.7.1`, MPS available, `compile_shader` present, wgpu version, Metal adapter)
- [x] T02 three CPU-float64 maxima within gate, warm-up days identical
- [x] T03 year (CPU float32): all 12 cases pass the float32 gate and the S0 gates vs Mac E+; week (MPS float32): all 12 pass the float32 gate thresholds (worst values and both wall times listed)
- [x] pytest summary line; `git status --short -- openubem scripts tests pyproject.toml uv.lock` lists only §3 files

### T04 — Spike candidate (a): PyTorch + shared C header on Metal
- **What:** one kernel `inside_surface_iterate` that performs spec §3.0 step 5 for one timestep, one thread per building, with the §3.2 precision rules, reading its inputs from device buffers laid out `[field, building]` (building index contiguous). Physics in `spike_common.h` (plain C, functions only, no Metal or CUDA keywords; address-space and kernel qualifiers come from macros defined by the wrapper); `spike_metal.py` builds the Metal source (the header plus a thin `kernel void` wrapper) with `torch.mps.compile_shader` and launches it on MPS tensors.
- **Inputs:** `scripts/gpusim/capture_spike_inputs.py` runs Stage B on `device="cpu"`, float64, with `capture_steps` for 5 cells (the 3 golden cells, V10, V11) at 3 run-period steps each: step 0 (first step after warm-up), the first January step at 07:00 with heating > 0, and the first July step at 14:00. It saves, per cell and step, every input of step 5 and its float64 outputs (inside face temperatures, iteration count), using `run_days` so the run stops right after the July step, to `tests/fixtures/gpusim/spike/<cell>__<step>.npz`.
- **Why:** spec §3.1 spike, candidate (a), IMP02's pick.
- **How to test:** `tests/gpusim/test_spike.py::test_spike_metal`: for each of the 15 captures, max |ΔT| of inside face temperatures vs the float64 capture ≤ 0.002 K (`MaxAllowedDelTemp`, the E+ convergence tolerance), and iteration count within ±1. Portability proxy: `clang++ -std=c++17 -fsyntax-only -x c++ -DGPUSIM_HOST spike_common.h` exits 0 (no Metal-only constructs in the physics). Report max |ΔT|, iteration-count differences, and the median of 20 launch times at B = 346 and B = 10,000 (inputs tiled from the 5 cells).

### T05 — Spike candidate (b): wgpu-py / WGSL
- **What:** the same kernel and the same buffer layout in `spike_iter.wgsl`, launched from `spike_wgpu.py` on the Metal adapter.
- **Why:** spec §3.1 spike, candidate (b), IMP01's pick.
- **How to test:** `tests/gpusim/test_spike.py::test_spike_wgpu`, same 15 captures, same gates, same timings as T04.

### T06 — Spike report
- **What:** `scripts/gpusim/run_spike.py` writes `openubem/outputs/gpusim_m2_spike.csv`: one row per candidate with max_dt_k, max_iter_diff, gate_pass, launch_ms_b346, launch_ms_b10000, kernel_lines, driver_lines, cuda_path (text: "same header via load_inline" for (a); "WGSL via DX12/Vulkan, no CUDA" for (b)), install_notes.
- **Why:** gives the owner the measured basis for decision D-09.
- **How to test:** the CSV has 2 rows and no empty gate columns; run `uv run pytest tests/gpusim/test_spike.py -q` only.

### CP2 — STOP and report (M2 done when all hold; owner decides D-09)
- [x] no file from T01–T03 changed since CP1 (the manager compares checksums taken at the CP1 audit; do not rerun the T02–T03 tests)
- [x] both candidates: max |ΔT| ≤ 0.002 K and iteration count ±1 on all 15 captures, or the failing captures listed
- [x] the portability proxy result for (a)
- [x] spike CSV rows quoted with launch times
- [x] pytest summary line; `git status --short -- openubem scripts tests pyproject.toml uv.lock` lists only §3 files
- Do not choose the framework. STOP and wait: the owner rules D-09 and the manager records it in `EXEC_M3_stageC_metal_s0.md` §1.

## 7. Stop-and-report points
- CP1 after T03 (Stage B passes the float32 gate on P1: year on CPU, week on MPS).
- CP2 after T06 (spike measured; M2 done; owner decision D-09).

## 8. Progress log
Format (append only):
```
#### TXX — <title> — completed YYYY-MM-DD
- Artifacts: <files>
- Deviations: <none, or what and why>
- Test status: <command> -> <summary line>; <measured gate values>
- Notes: <short>
```

#### T01 — Pin the GPU dependencies — completed 2026-11-22
- Artifacts: `pyproject.toml`, `uv.lock`
- Deviations: `uv` was not installed on this Mac, so installed `uv 0.13.9` to `$HOME/.local/bin/uv`. `wgpu==0.33.0` (`2026-11-06`), `0.32.0`, and `0.31.1` declare `requires-python >= 3.11`, which fails `uv` resolution against `pyproject.toml`'s `requires-python = ">=3.10"`; pinned `wgpu==0.31.0` (`2026-03-02`, newest release compatible with `>=3.10` and published ≥ 2 weeks before 2026-11-22). Full `uv sync` fails on macOS 13.5.2 because pre-existing `uv.lock` entries `pyproj==3.7.2` and `rasterio==1.4.4` lack `macosx_13_0_arm64` wheels and `proj` is not installed; ran `uv add --no-sync torch==2.7.1 wgpu==0.31.0` to update `pyproject.toml` and `uv.lock`, then `uv pip install --python .venv/bin/python torch==2.7.1 wgpu==0.31.0` (+10 packages into `.venv`) and ran checks with `uv run --no-sync`.
- Test status: `uv run --no-sync python -c "import torch, wgpu; print(torch.__version__, torch.backends.mps.is_available(), hasattr(torch.mps, 'compile_shader'), wgpu.__version__)"` -> `2.7.1 True True 0.31.0`; `uv run --no-sync python -c "import wgpu; print(wgpu.gpu.request_adapter_sync().info)"` -> `device='Apple M2 Pro', adapter_type='IntegratedGPU', backend_type='Metal'`.
- Notes: `uv.lock` diff: +62 `[[package]]` entries (119 -> 181), 0 removed.

#### T02 — Namespace shim and Stage B on CPU float64 — completed 2026-11-22
- Artifacts: `openubem/gpusim/backends/xp_torch.py`, `openubem/gpusim/backends/torch_batched.py`, `tests/gpusim/test_stage_b.py`
- Deviations: none
- Test status: `uv run --no-sync pytest tests/gpusim/test_stage_b.py::test_stage_b_cpu_float64_equals_stage_a -s -v` -> `1 passed, 1 warning in 362.40s (0:06:02)`; `max_ann_rel=1.719e-15` (gate ≤ 1e-9), `max_hourly_j=4.184e-05 J` (gate ≤ 1e-3 J), `max_dt_k=1.624e-12 K` (gate ≤ 1e-8 K), `warmup_days=[3, 3, 3]` (identical).
- Notes: Frozen physics modules under `openubem/gpusim/physics/` ran unchanged via `TorchNamespace`; HVAC sub-stepping vectorized over `[B]` with masks (no Python loop over buildings).

#### T03 — Stage B float32: full year on CPU, one week on MPS — completed 2026-11-22
- Artifacts: `openubem/gpusim/backends/torch_batched.py`, `tests/gpusim/test_stage_b.py`, `openubem/outputs/gpusim_m2_stage_b.csv`
- Deviations: none
- Test status: `uv run --no-sync pytest tests/gpusim/test_stage_b.py::test_stage_b_cpu_float32_year_p1 -q -s` -> `1 passed, 1 warning in 370.91s (0:06:10)` (`wall=273.800 s`); `uv run --no-sync pytest tests/gpusim/test_stage_b.py::test_stage_b_mps_float32_week_p1 -q -s` -> `1 passed, 1 warning in 240.31s (0:04:00)` (`wall=141.586 s`); `uv run --no-sync pytest tests/gpusim -q` -> `38 passed, 1 warning in 1005.06s (0:16:45)` (`year_cpu_wall_seconds=281.198 s`, `week_mps_wall_seconds=142.520 s`). Year CPU float32 worst: `|rel_b_vs_a|=1.305e-04` (`V07`), `dt_p999_ba=0.001972 K`, `dt_max_ba=0.002071 K`, `|rel_b_vs_eplus|=1.078e-04`, `cv_rmse=5.879e-04` (`V04`), `|nmbe|=1.042e-04` (`V07`), `dt_p999_ep=0.005611 K`, `dt_max_ep=0.005979 K`. Week MPS float32 worst: `|week_rel_mps_vs_a|=8.251e-05` (`V07`), `week_dt_p999=0.000004 K`, `week_dt_max=0.000004 K`.
- Notes: Stopped at CP1. All 12 P1 cells in `openubem/outputs/gpusim_m2_stage_b.csv` pass float32 gates.

#### T04 — Spike candidate (a): PyTorch + shared C header on Metal — completed 2026-11-22
- Artifacts: `openubem/gpusim/backends/kernel/spike_common.h`, `openubem/gpusim/backends/kernel/spike_metal.py`, `scripts/gpusim/capture_spike_inputs.py`, `tests/fixtures/gpusim/spike/` (15 `.npz`, 187.2 KiB), `tests/gpusim/test_spike.py`
- Deviations: none
- Test status: `clang++ -std=c++17 -fsyntax-only -x c++ -DGPUSIM_HOST openubem/gpusim/backends/kernel/spike_common.h` -> exit 0; `uv run --no-sync pytest tests/gpusim/test_spike.py::test_spike_metal -q -s` -> `1 passed, 1 warning in 1.41s`; `worst_dt=1.170156e-05 K` (gate ≤ `0.002 K`), `max_abs_iter_diff=0` (gate ≤ `1`, exact match on all 15/15 captures), `median_ms_b346=1.7213 ms`, `median_ms_b10000=1.3166 ms`.
- Notes: `capture_spike_inputs.py` captured the 5 cells (`it`, `uk`, `es`, `V10`, `V11`) at steps `0`, `83` (Jan 1 07:00, heating > 0), and `52295` (Jul 1 14:00) via Stage B CPU float64 (`B=1`, `run_days=182`, `492.35s`). Kernel uses §3.2 precision rules and `[field, building]` SoA layout.

#### T05 — Spike candidate (b): wgpu-py / WGSL — completed 2026-11-22
- Artifacts: `openubem/gpusim/backends/kernel/spike_iter.wgsl`, `openubem/gpusim/backends/kernel/spike_wgpu.py`, `tests/gpusim/test_spike.py`
- Deviations: none
- Test status: `uv run --no-sync pytest tests/gpusim/test_spike.py::test_spike_wgpu -q -s` -> `1 passed, 1 warning in 2.40s`; `worst_dt=1.313888e-05 K` (gate ≤ `0.002 K`), `max_abs_iter_diff=0` (gate ≤ `1`, exact match on all 15/15 captures), `median_ms_b346=3.1060 ms`, `median_ms_b10000=4.6574 ms`.
- Notes: Same `[field, building]` SoA layout and §3.2 precision rules on the Apple M2 Pro Metal adapter via `wgpu==0.31.0` (`workgroup_size(64, 1, 1)`).

#### T06 — Spike report — completed 2026-11-22
- Artifacts: `scripts/gpusim/run_spike.py`, `openubem/outputs/gpusim_m2_spike.csv`
- Deviations: none
- Test status: `uv run --no-sync python scripts/gpusim/run_spike.py` -> wrote 2 rows (`a_pytorch_metal_header`: `max_dt_k=1.170156e-05`, `max_iter_diff=0`, `gate_pass=True`, `launch_ms_b346=1.4679`, `launch_ms_b10000=1.2593`, `kernel_lines=579`, `driver_lines=381`; `b_wgpu_wgsl`: `max_dt_k=1.313888e-05`, `max_iter_diff=0`, `gate_pass=True`, `launch_ms_b346=2.5751`, `launch_ms_b10000=3.9037`, `kernel_lines=526`, `driver_lines=201`); `uv run --no-sync pytest tests/gpusim/test_spike.py -q` -> `2 passed, 1 warning in 2.25s`.
- Notes: Stopped at CP2; no framework chosen (awaiting owner decision D-09). No T01–T03 files changed since CP1.
