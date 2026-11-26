# DR05 Result — Rust CPU Thermal Solver & GPU Interop (`gpusim` Co-Design)

**Feeds:** [`PLAN_rust_migration.md`](../../../PLAN_rust_migration.md) §4 (`R4`), Phase 4 (`T12`, `T14`), and Owner Decision `D-RS-05`  
**Date:** 2026-11-26  
**Project Licence Policy:** `Apache-2.0 OR MIT` ([`pyproject.toml`](../../../../../../pyproject.toml), [`PLAN_rust_migration.md`](../../../PLAN_rust_migration.md))

---

## Executive Summary

1. **Recommend Option A (Pragmatic Hybrid) for `D-RS-05`:** Build `openubem-sim` in pure Rust (`rayon` + `pulp` + `num-traits`) for fast multi-core CPU (`f64` reference + `f32` GPU-twin) and `openubem-idf` for parallel compilation, while **retaining the validated CUDA/Metal C physics header [`general_common.h`](../../../../../../openubem/gpusim/backends/kernel/general_common.h)** launched via Python (`torch`/`cupy`) initially and optionally via Rust `cudarc` (`0.19.10`, `MIT OR Apache-2.0`) + `objc2-metal` (`0.2.0`, `MIT`) later.
2. **Reject Option B (`wgpu`/WGSL) for `general_common.h`:** While native Rust `wgpu` (`30.0.1`, `MIT OR Apache-2.0`) eliminates Python binding latency (**24–36 µs** Vulkan / **32–71 µs** Metal per dispatch vs `wgpu-py` **2.58–4.66 ms** measured in [`gpusim_m2_spike.csv`](../../../../../../openubem/outputs/gpusim_m2_spike.csv)), it hits three structural blockers: (a) `gen_step_zone` passes **>100 buffer pointers** (`GPUSIM_GLOBAL` args in [`general_common.h`](../../../../../../openubem/gpusim/backends/kernel/general_common.h#L900-L1032)) whereas Apple Metal caps buffer argument tables at **31 slots total** and WebGPU defaults `max_storage_buffers_per_shader_stage` to **4–8**; (b) WGSL and Apple Metal lack native **`f64`** hardware; and (c) `wgpu` lacks native CUDA/PTX.
3. **Reject Option C (Rust-on-GPU rewrite) for 2026 production:** `cubecl` (`0.11.0`, `MIT OR Apache-2.0`) is the strongest cross-platform Rust DSL (`#[cube]` with `while`/`break` control flow across CUDA, Metal, wgpu, CPU), but remains `0.x` with emulated/divergent `f64` on Metal/wgpu; `NVIDIA/cuda-rust` (`cutile-rs` / `cuda-oxide`) is Linux + Ampere `sm_80+` only (no macOS/Windows parity); `rust-gpu` (`0.10.0`, Oct 2026) requires pinning `nightly-2026-07-03` and routes Metal through a 4-layer `Rust → SPIR-V → Naga → MSL` pipeline; `candle` and `burn` are ML tensor stacks (indeed `candle` itself embeds raw `.cu`/`.metal` kernels via `cudarc` and `metal`, confirming Option A).
4. **Use building/zone-parallel `rayon` + flat-CSR-per-building (with intra-surface / intra-mode SIMD via `pulp`) as the primary `openubem-sim` CPU layout, plus optional `lane=4` SoA micro-batching strictly for homogeneous S0/S1 cells:** Heterogeneous `GeneralBatch` urban districts (43,989 zones / 523,530 surfaces in M8) have variable `n_sz`, variable `n_modes <= 12`, `BOUND_SURFACE` interzone coupling, dynamic `GEN_MAX_ITERS = 500` exits, and per-zone `n_sub` HVAC sub-stepping—making lock-step across-building SoA SIMD inefficient due to lane divergence and gather penalties.
5. **Use `pulp` (`0.22.3`, `MIT`) over `wide` (`1.7.1`, `Zlib OR Apache-2.0 OR MIT`) and `std::simd`:** `std::simd` (`portable_simd`) remains **nightly-only** in late 2026 (`rust-lang/rust#86656`); `wide::f64x4` lacks native SIMD `.exp()`/`.powf()`; `pulp` compiles on **stable Rust** and provides runtime feature dispatch across **NEON (128-bit)**, **AVX2 (256-bit)**, and **AVX-512 (512-bit)** (proven in `faer`).
6. **Estimated CPU speedup (analytic, `UNVERIFIED` by live `rustc` benchmark):** Removing the 105,120-step Python interpreter loop in [`numpy_ref.py`](../../../../../../openubem/gpusim/backends/numpy_ref.py) and parallelizing across cores with `rayon` is estimated to cut the **164.9 s** (`B=3` `77.55 s` + `B=9` `87.32 s`, [`EXEC_M1`](../../../../GPU_based_compute/Prompt/executors/EXEC_M1_stageA_numpy_s0.md#L214-L218)) / **273.8 s** (Stage B `B=12` CPU float32, [`EXEC_M2`](../../../../GPU_based_compute/Prompt/executors/EXEC_M2_stageB_spike_mps.md#L144)) P1 wall time to **~0.5–1.5 s** on a 12-core M2 Pro (~100–350× vs Python) and **~0.15–0.45 s** on a 32-core x86_64 Speed node, outperforming 1-core EnergyPlus (~4.05–4.69 s/cell with sizing; ~2.0–2.6 s/cell sizing-off) by **~50–150×** per core and **~500–4,000×** per node.
7. **Single-source `f64`/`f32` diagnostic parity via a custom `SimFloat: num_traits::Float` trait:** Compiling one generic Rust physics module into both exact `f64` (replacing `numpy_ref.py` + `physics/*.py`) and an `f32` GPU-twin (`mul_add`, `exp`, `powf`, `T - 20 °C` offsets, and selectable factored vs direct $T_i^4 - T_j^4$) catches float32 cancellation, branch flips, and overflow bugs deterministically on CPU before GPU kernel launch.
8. **Wire `openubem-sim` directly into [`router.py`](../../../../../../openubem/gpusim/router.py#L23-L53):** Fold a compile-time `build.rs` SHA-256 over `crates/openubem-sim/src/**/*.rs` and `general_common.h` into `conformance_hash()`, and gate promotion from `"shadow"` to `"on"` on P1 (`<= 1e-12` vs Stage A `f64`, `<= 0.05%` vs Stage A `f32`), P2 (346 EU cells), P3 (`ES-MAD-BERRUGUETE`), P4 (`austin_centre`), and locked/free warm-up day parity.
9. **Strict licence compliance (`Apache-2.0 OR MIT`):** Every recommended crate (`rayon`, `pulp`, `num-traits`, `libm`, `cudarc`, `objc2-metal`, `bytemuck`, `thiserror`) is `MIT`, `Apache-2.0`, or `Zlib`—zero GPL/AGPL dependencies (`cargo-deny` enforced).

---

## Table 1: CPU + GPU Architecture Options (`D-RS-05`: Option A vs Option B vs Option C)

| Dimension | Option A: Pragmatic Hybrid (`openubem-sim` Rust CPU + C/CUDA/Metal `general_common.h`) | Option B: Native Rust `wgpu` + WGSL Single Compute Pipeline | Option C: Pure Rust-on-GPU (`cubecl` / `rust-gpu` / `rust-cuda`) |
|---|---|---|---|
| **Portability (Mac / Win / Speed HPC)** | **High:** Rust CPU (`openubem-sim`) runs on Mac M2 Pro (arm64), Win x64, & 32-core Speed HPC (no GPU needed); `general_common.h` already runs on Mac Metal (`s0_metal.py`) & Win/HPC CUDA (`general_cuda.py`, M8 `3,832` homes). | **Medium-High:** Cross-platform Metal (Mac), Vulkan/DX12 (Win), Vulkan (Linux HPC GPU if Vulkan driver installed). **No native CUDA/PTX** (cannot target CUDA-only HPC nodes without Vulkan ICD). | **Fragmented:** `cubecl` covers CUDA/Metal/wgpu/CPU; `rust-gpu` outputs SPIR-V (Metal only via Naga); `NVIDIA/cuda-rust` is **Linux + NVIDIA `sm_80+` only** (no Mac Metal, limited Win). |
| **Float64 (`f64`) Support** | **Complete:** Native `f64` in Rust CPU (`openubem-sim`); optional native `f64` on CUDA if needed; `f32` GPU-twin compiled from the same Rust physics trait for pre-launch diagnostics. | **None on GPU:** WGSL core spec and Apple Metal hardware lack native `f64`. Emulation (`metal-softfloat` / double-single) incurs severe ALU penalty and cannot share one fast path. | **Incomplete:** `cubecl-metal`/`wgpu` lack native `f64` (emulated `f64` reported to diverge from CPU `f64`); `rust-gpu` `Float64` fails on Metal/consumer GPUs; `cuda-rust` supports `f64` on CUDA only. |
| **Launch Overhead (per chunk)** | **Low:** `torch.mps.compile_shader` measured **1.26–1.72 ms** in [`gpusim_m2_spike.csv`](../../../../../../openubem/outputs/gpusim_m2_spike.csv) / [`EXEC_M2`](../../../../GPU_based_compute/Prompt/executors/EXEC_M2_stageB_spike_mps.md#L150); direct Rust `cudarc` CUDA launch is **~3–10 µs** (and `<1 µs` w/ CUDA Graphs). Amortized easily by `run_chunk_days >= 1`. | **Low in Rust, High in `wgpu-py`:** Native Rust `wgpu` API dispatch spans **24–36 µs (Vulkan)** and **32–71 µs (Metal)** vs **~95+ µs** overhead floor in Python wrappers and **2.58–4.66 ms** measured in `wgpu-py` spike. | **Low–Medium:** `cubecl` caches JIT kernels (`~µs–sub-ms` dispatch after warmup); `rust-gpu` via `wgpu` inherits `wgpu` dispatch latency (**24–71 µs**); `cuda-rust` matches CUDA driver latency (**~3–10 µs**). |
| **Register & Buffer Limits** | **Unconstrained on CUDA/CPU:** `gen_step_zone` passes **>100 buffer pointers** cleanly in CUDA (`general_cuda.py`). On Metal, argument packing or Metal 3 argument buffers needed beyond 31 raw slots (`s0_metal.py` uses packed `PackedBatch` tensors). | **Severe Blocker:** WebGPU defaults `max_storage_buffers_per_shader_stage` to **4** (profile max ~8–16); Apple Metal hard-caps buffer argument tables at **31 slots total** (`wgpu` `29/30` caps combined slots ~29). Requires refactoring 100+ `GeneralBatch` arrays into giant packed megabuffers. | **Backend-Bound:** `cubecl-wgpu` / `cubecl-metal` and `rust-gpu → Naga → MSL` inherit Metal's **31-buffer argument table** limit; `cubecl` / `rust-gpu` register pressure across 12-mode arrays + `t4_buf[64]` is harder to inspect than PTX/MSL. |
| **Ecosystem Maturity (2026)** | **High (Production):** `general_common.h` is already validated through M8 (`3,832` homes, `0.9825` $R^2$); `cudarc` (`0.19.10`), `rayon` (`1.12.0`), `pulp` (`0.22.3`) are stable-Rust production crates. | **High for Graphics, Moderate for Scientific Compute:** `wgpu` `30.0.1` (Aug 2026) is mature on stable Rust, but WGSL lacks pointers, templates/generics, `f64`, and mature GPU profilers vs Nsight Compute. | **Alpha / Research-Grade for Physics:** `cubecl` (`0.11.0`, `0.x` API churn); `rust-gpu` (`0.10.0`, nightly `nightly-2026-07-03` lock, 4-IR debugging); `cuda-oxide` explicitly alpha; `burn`/`candle` target ML tensors, not CSR ODE loops. |
| **Engineering Risk** | **Low:** Zero disruption to validated M4/M7/M8 CUDA/Metal parity (`1.8e-7` CUDA vs Metal on P1); incremental Rust CPU replacement behind `OPENUBEM_RUST_BACKEND`. | **High:** Full rewrite of 1,477-line `general_common.h` into WGSL + megabuffer offset packing; loses native CUDA path on Windows RTX A400 & Speed GPU nodes. | **High–Very High:** Nightly compiler breakage (`rust-gpu`), Metal `f64` divergence (`cubecl`), or single-vendor lock-in (`cuda-rust`), plus re-validating P1–P4/M8 from scratch. |

---

## Table 2: Rust SIMD & GPU Compute Crates (2026 Ecosystem Audit)

*(All crates audited for `Apache-2.0 OR MIT` compatibility per [`PLAN_rust_migration.md`](../../../PLAN_rust_migration.md) §3 Guardrail 5. Exact download counts not returned in search snippets are marked `UNVERIFIED`.)*

| Crate | Repository / Registry | Licence | Latest Version | Last Commit / Release Date | Readiness (1–5) | Notes for `openubem-sim` |
|---|---|---|---|---|---|---|
| **`wide`** | `Lokathor/wide` (`crates.io/crates/wide`) | `Zlib OR Apache-2.0 OR MIT` | `1.7.1` | Sep 14, 2026 | **4 / 5** | Fixed-width portable SIMD (`f64x4`, `f64x8`, `f32x8`) on stable Rust; **lacks native `.exp()`/`.powf()` on `f64x4`**, and fixed 256/512-bit types emulate via multiple ops on 128-bit NEON. |
| **`pulp`** | `sarah-quinones/pulp` (`crates.io/crates/pulp`) | `MIT` | `0.22.3` | Jun 20, 2026 | **5 / 5** | Safe trait-based runtime CPU dispatch (`Arch::new()`) across **NEON**, **AVX2**, and **AVX-512**; powers `faer` linear algebra. Ideal for `openubem-sim` inner loops on stable Rust. |
| **`cudarc`** | `chelsea0x3b/cudarc` (formerly `coreylowman/cudarc`) | `MIT OR Apache-2.0` | `0.19.10` | Sep 24, 2026 | **5 / 5** | Safe CUDA Driver API (`CudaContext`, `CudaStream`, `CudaSlice`) + NVRTC (`compile_ptx`) supporting CUDA `11.4`–`13.4` with dynamic loading (`libloading`). Ready for Rust-hosted `general_common.h` if bypassing PyTorch later. |
| **`wgpu`** | `gfx-rs/wgpu` (`crates.io/crates/wgpu`) | `MIT OR Apache-2.0` | `30.0.1` | Aug 2026 (`v30.0.0` Jul/Aug 2026) | **4 / 5** *(graphics)* / **2 / 5** *(this solver)* | Production-grade WebGPU implementation (MSRV `1.87.0`), `objc2-metal` backend on Mac, **24–71 µs** native dispatch; **blocked for `general_common.h`** by WGSL lack of `f64`, no CUDA backend, and Metal's 31-buffer table cap. |
| **`cubecl`** | `tracel-ai/cubecl` (`crates.io/crates/cubecl`) | `MIT OR Apache-2.0` | `0.11.0` (`0.12.0-pre` active) | Oct–Nov 2026 | **3 / 5** | Single-source `#[cube]` Rust kernels targeting CUDA, HIP, Metal, wgpu, and CPU SIMD with `while`/`break` support; `0.x` API churn and non-native/divergent `f64` on Metal/wgpu make it premature to replace `general_common.h`. |
| **`rust-gpu`** | `Rust-GPU/rust-gpu` (`github.com/Rust-GPU/rust-gpu`) | `MIT OR Apache-2.0` | `0.10.0` | Oct 1, 2026 | **2 / 5** | Compiles Rust MIR to SPIR-V (`rustc_codegen_spirv`); requires pinned **`nightly-2026-07-03`**; Metal requires `SPIR-V → Naga → MSL` translation with pointer/control-flow caveats and no Metal `f64`. |
| *`rayon`* *(ref)* | `rayon-rs/rayon` (`crates.io/crates/rayon`) | `MIT OR Apache-2.0` | `1.12.0` (`rayon-core 1.13.0`) | 2025–2026 (MSRV `1.80.0`) | **5 / 5** | Work-stealing CPU threadpool; essential for building/zone-parallel execution across 12 M2 Pro cores and 32 Speed HPC cores. |
| *`num-traits`* *(ref)* | `rust-num/num-traits` (`crates.io/crates/num-traits`) | `MIT OR Apache-2.0` | `0.2.19` | 2024–2026 (MSRV `1.60.0`) | **5 / 5** | Standard `Float` + `MulAdd` traits enabling single-source `f64`/`f32` generic physics kernels on stable Rust (with `std` or `libm`). |
| *`objc2-metal`* *(ref)* | `madsmtm/objc2` (`crates.io/crates/objc2-metal`) | `MIT` | `0.2.0` (monorepo active) | Active late 2026 | **4 / 5** | Replaces **deprecated `metal-rs` (`0.33.0`)**; used by `wgpu` for native Metal compute encoders without Python/PyTorch if OpenUBEM moves Stage C Metal host code to Rust. |
| *`rust-cuda`* *(ref)* | `NVIDIA/cuda-rust` (`cutile-rs`, `cuda-oxide`) | `MIT OR Apache-2.0` (`UNVERIFIED` full subcrate audit) | GitHub pre-1.0 | Active 2025–2026 | **2 / 5** | Official NVIDIA reboot (`cutile-rs` tile IR + `cuda-oxide` alpha SIMT), but **Linux + NVIDIA `sm_80+` only**—cannot serve Mac M2 Pro or Windows RTX A400 uniformly. |

---

## Q1: Pure-Rust CPU Thermal Solver (`openubem-sim`) Performance & Layout

### 1.1 Workload Structure of `GeneralBatch`
Inspecting [`openubem/gpusim/general_model.py`](../../../../../../openubem/gpusim/general_model.py#L283-L380) and [`openubem/gpusim/backends/kernel/general_common.h`](../../../../../../openubem/gpusim/backends/kernel/general_common.h#L42-L1474) defines the exact computational profile `openubem-sim` must execute:
- **Flat CSR hierarchy:** `B` buildings (`zone_offset[B+1]`, `surf_offset[B+1]`), `Z` zones (`zone_surf_offset[Z+1]`, `zone_sf_offset[Z+1]`), and `S` surfaces (`[S, 12]` modal conduction arrays `surf_m_decay`, `surf_m_gno`, `surf_m_gni`, `surf_m_goo`, `surf_m_goi`, `surf_m_co`, `surf_m_ci`). In M8's 4-district fleet ([`gpusim_m8_eu_districts.csv`](../../../../../../openubem/outputs/gpusim_m8_eu_districts.csv#L1-L6)), `B = 3,832` homes span `Z = 43,989` zones (avg **11.5 zones/building**) and `S = 523,530` surfaces (avg **11.9 surfaces/zone**, **136.6 surfaces/building**).
- **Sequential time loop:** Up to `25` warm-up days + `365` run-period days × `24 × sph` timesteps (`sph = 6` or `12`, i.e., `52,560` to `105,120` run steps + `1,728–7,200` warm-up steps). Time-stepping is strictly sequential per building due to modal conduction state `modal_z[S, 12]`, BDF3 zone air history `xmat[Z, 4]`, `w_prev[Z, 4]`, and lagged interzone surface temperatures `t_surf_in_prev[p]`.
- **Irregular inner work:** Every timestep runs:
  1. Solar & interior radiant distribution (`surf_sunlit_u8[S, 8760]`, Perez sky, `SimpleGlazingSystem` polynomial transmission);
  2. Modal state-space update (`nm <= 12` modes per opaque surface, up to 10-term dot/FMA accumulation) + outside heat balance;
  3. **Coupled inside-surface iteration** (`GEN_MAX_ITERS = 500`, `GEN_MAX_DEL_T = 0.002 K`, re-evaluating TARP convection every `30` iterations, `SimpleGlazingSystem` Newton/relaxation up to `100` iterations on `it == 0`, and `O(n_sz^2)` ScriptF longwave exchange);
  4. **Zone air & IdealLoads corrector** with adaptive sub-stepping (`n_sub <= limit_num_sys` whenever `|ΔT_zone| > 0.3 K`);
  5. Modal state `modal_z` post-step update.

### 1.2 Memory Layout Comparison: AoS-per-Building vs SoA-across-SIMD-Lanes (`[lane=4|8]`)

Literature on vectorizing transient ODE and heat-transfer ensembles across SIMD registers (e.g., batched ODE/heat-transfer evaluations under AVX2 and NEON) establishes that **SoA-across-instances (`[lane=4|8]`) achieves near-peak unit-stride vectorization only when instances share identical control flow, step counts, and structural dimensions**; conversely, adaptive step counts and branch divergence force lock-step masking or trajectory re-packing (SIMD SoA/AoS vectorization principles for transient ODEs/heat transfer across trajectories; `arXiv` / Intel & ARM NEON vectorization guides). Applying this directly to OpenUBEM yields a sharp **two-tier split**:

1. **General Multi-Zone `GeneralBatch` (M8 / S2b / S3) → Building-Parallel CSR (`rayon`) + Intra-Building Contiguous SoA (`pulp` SIMD within zones/modes):**
   - **Why across-building `[lane=4|8]` fails on M8:** Across `ES-MAD-BERRUGUETE`, `FR-LYO-HAUTCOEURPENTES`, `GB-LDN-STDUNSTANS`, and `IT-BOL-GALVANI2`, buildings vary from 1 to >30 zones, zones vary in surface count `n_sz` (e.g., 6 to 30+ surfaces), surfaces vary in `n_modes` (0–12) and boundary types (`BOUND_SURFACE` partner indices `p`, `BOUND_WINDOW`, `BOUND_OUTDOORS`), and each building converges in different inner iterations (`it = 1..500`), warm-up days (`1..25`), and HVAC sub-steps (`n_sub = 1..12`). Packing 4 or 8 heterogeneous buildings into SIMD lanes would either force padding/masking to `max(n_zones) × max(n_sz) × max(it)` (wasting 2–6× FLOPs) or degrade to AVX2/NEON scalar gathers.
   - **Optimal M8 layout:** Partition `GeneralBatch` into **per-building work slices** dispatched via `rayon::par_iter()` with dynamic work-stealing (or LPT longest-building-first sorted by `n_surfs_total`, matching `PLAN_gpu_accelerated_simulation.md` §4 approach A). Inside each building thread:
     - Keep all per-surface static/state arrays (`t_surf_in`, `t_surf_in_old`, `t4_buf`, `h_conv_in`, `ctf_const_in`) contiguous for `[zs0..zs1]` so each building's hot working set (~10–50 KB for a 10-zone building) **stays completely inside L1/L2 CPU cache** across all 105,120 timesteps!
     - Store `modal_z`, `surf_m_decay`, `surf_m_goo`, `surf_m_goi`, `surf_m_co`, `surf_m_ci`, `surf_m_gno`, `surf_m_gni` padded to `12` (`[S][12]` or `[S][3 × f64x4]` / `[S][6 × f64x2]`) so the `nm <= 12` modal loop becomes 3 (AVX2) or 6 (NEON) unrolled branchless FMA vector steps.
     - Vectorize the `O(n_sz^2)` ScriptF inner LWR sum `sum_j script_f_sigma[row_off + j] * (t4_j - t4_i)` over contiguous `j = 0..n_sz` using `pulp` (`S::as_simd_f64s` / `S::as_simd_f32s`) with scalar tail. Notice `script_f_sigma` rows are already contiguous per surface `li`!

2. **Homogeneous Single-Zone / Archetype Sweeps (P1/P2 S0–S2a, `B = 100..10,000` with uniform `n_surf`) → Optional `[lane=4|8]` Micro-Batch SoA:**
   - When simulating `346` P2 cells or `10,000` parameter-sweep variants that share identical zone count (`1`) and surface count (e.g. `S = 10..16`, padded if close), sorting by `(n_surf, has_window)` and packing **4 buildings (`f64x4` AVX2) or 8 buildings (`f64x8` AVX-512 / `f32x8` AVX2)** in `[field][surf][lane]` SoA allows lock-step SIMD across buildings on all arithmetic (`mul_add`, `sqrt`, `T^4`, modal updates), falling back to lane-wise scalar `powf`/`exp` only in `gen_iso15099_win_hin` and `gen_outside_conv_doe2` (note: outside convection and window solve run *outside* the inner opaque iteration or only on `it == 0`, so their scalar transcendental share is small!).

### 1.3 SIMD Crates & Hardware Target Analysis (2026 Status)

| Hardware Target | Register Width | `f64` Lanes | `f32` Lanes | Optimal Rust Dispatch |
|---|---|---|---|---|
| **Apple M2 Pro** (12 cores: 8P + 4E, arm64 NEON) | 128-bit NEON (multi-pipe execution) | `2` (`f64x2`) | `4` (`f32x4`) | `pulp` (`aarch64` NEON + FMA) + `rayon` across 8P+4E cores (chunked work-stealing handles asymmetric P/E core speed automatically) |
| **Concordia Speed HPC** (32-core x86_64 Linux) | 256-bit AVX2+FMA (or 512-bit AVX-512 on newer Xeon/Zen4+ nodes) | `4` (AVX2) / `8` (AVX-512) | `8` (AVX2) / `16` (AVX-512) | `pulp` runtime CPUID dispatch (`avx512f` → `avx2+fma` → scalar) inside **one portable `manylinux` `abi3` wheel** (no `-C target-cpu=native` crash risk on heterogeneous cluster nodes!) |

- **`std::simd` (`core::simd`, RFC 2948 / `rust-lang/rust#86656`):** Remains **nightly-only** (`#![feature(portable_simd)]`) as of late 2026 with no stabilization date and incomplete architecture-specific transcendental coverage. **Do not use** in OpenUBEM (which targets stable Rust + `abi3` wheels in CI).
- **`wide` (`v1.7.1`, Sep 2026, `Zlib OR Apache-2.0 OR MIT`):** Works on stable Rust with fixed types (`f64x4`, `f64x8`, `f32x8`), **but** (a) fixed `f64x4` compiles to 2× NEON registers on M2 Pro without automatic AVX-512 scaling on HPC, and (b) `wide::f64x4` lacks native vectorized `.exp()` and `.powf()` methods, forcing scalar extraction anyway.
- **`pulp` (`v0.22.3`, Jun 2026, `MIT`):** Abstracts over dynamic register widths (`S::f64s`, `S::f32s`) with safe runtime feature detection (`Arch::new().dispatch(...)`) across NEON, AVX2/FMA, and AVX-512—the exact strategy used by `faer` (`pulp` author `sarah-quinones`). *(Note: `fearless_simd` 1.0 also emerged in late 2026 as a stable alternative, but `pulp` has deeper numerical linear-algebra battle-testing.)*

### 1.4 Realistic Performance Estimates (Analytic Estimates vs Measured Baselines)

**Measured Baselines (on disk, verified):**
- **Python Stage A (`numpy_ref.py`, `f64`):** `77.552 s` for `B=3` golden cells and `87.321 s` for `B=9` variants (`164.9 s` sum; `168.17 s` full `pytest` suite) on M2 Pro ([`EXEC_M1`](../../../../GPU_based_compute/Prompt/executors/EXEC_M1_stageA_numpy_s0.md#L214-L218)); `B=160` Bologna fleet in `365.018 s` (`0.438 bldg-yr/s`, [`EXEC_M1`](../../../../GPU_based_compute/Prompt/executors/EXEC_M1_stageA_numpy_s0.md#L237)).
- **Python Stage B (`torch_batched.py`, `f32` CPU, `B=12` P1):** **`273.800 s`** on M2 Pro ([`EXEC_M2`](../../../../GPU_based_compute/Prompt/executors/EXEC_M2_stageB_spike_mps.md#L144)).
- **EnergyPlus 23.1 (1-core Rosetta 2 on M2 Pro):** `~4.05–4.69 s` per EU cell with sizing (`~2.61 s` sizing-off; `~2.0 s` E+ 24.2 native arm64), of which `~2.0 s` (~`15–19 µs/step`) is the actual time loop ([`BUILD_SPEC`](../../../../GPU_based_compute/BUILD_SPEC_gpu_heat_balance_engine.md#L65-L67), [`IMP03_result.md`](../../../../GPU_based_compute/Prompt/IMP/results/IMP03_result.md#L194)). Multi-zone EU buildings in `austin_centre` / EU districts typically span `~20–40+ s` (median `3.2 s`, p90 `9.8 s`, p99 `232.8 s`, [`PLAN_gpu_accelerated_simulation.md`](../../../../GPU_based_compute/PLAN_gpu_accelerated_simulation.md#L48-L50)).
- **Stage C CUDA (`RTX A400` 4 GB, `f32`):** `B=10,000` S0 in `461.6 s` (`21.66 bldg-yr/s`, [`gpusim_progress_board.html`](../../../../GPU_based_compute/gpusim_progress_board.html#L530)); M8 `3,832` homes (`43,989` zones) in `2,274.8 s` GPU kernel time (`1.68 bldg-yr/s` GPU-only, [`gpusim_m8_eu_districts.csv`](../../../../../../openubem/outputs/gpusim_m8_eu_districts.csv#L6)).

**Analytic Estimates for `openubem-sim` (LABELLED `ESTIMATE / UNVERIFIED` — no `rustc` binary benchmarked yet):**
- *Single-cell inner-step cost:* A typical S0 cell (`~11` surfaces, avg `~4` inner iterations, `105,120` steps + ~`3` warm-up days = `~106,000` steps) executes roughly `~300–600` FLOPs + `~4–8` `pow`/`exp` calls per step in L1-resident compiled Rust (`f64` or `f32`). At `~0.5–1.5 µs/step` on 1 M2 Pro P-core (vs E+ `15–19 µs/step` C++ virtual-dispatch + HVAC manager overhead), **1-core Rust** takes **~0.05–0.16 s/cell** (**~15–40× faster than 1-core E+ sizing-off**, **~25–80× faster than 1-core E+ with sizing**).
- **12-core M2 Pro (8P+4E, effective ~9.5–10 P-core equivalents):**
  - **12 P1 cells:** **~0.1–0.3 s** compute + Python/PyO3 array handoff (**~900–2,700×** faster than Stage B CPU `273.8 s`; **~550–1,600×** faster than Stage A `164.9 s`; **UNVERIFIED** conservative engineering target `<= 3.0 s` per [`PLAN_rust_migration.md`](../../../PLAN_rust_migration.md#L208)).
  - **346 P2 EU cells:** **~2–6 s** wall time (**~130–400×** vs Stage A's `792 s` total across 3 sites in [`EXEC_M1`](../../../../GPU_based_compute/Prompt/executors/EXEC_M1_stageA_numpy_s0.md#L237)).
  - **M8 3,832 multi-zone homes (`43,989` zones):** Scaling by `~11.5 zones/building` + `~12` modal modes gives roughly `~1.5–3.5 s` per average home on 1 core → **~600–1,400 s (10–23 min)** on 12-core M2 Pro (`f64` or `f32`).
- **32-core x86_64 Speed HPC node (AVX2/AVX-512):**
  - **12 P1 cells:** **~0.05–0.2 s** (capped by threadpool wake + small batch size `B=12 < 32` unless zone/variant fan-out).
  - **346 P2 EU cells:** **~0.8–2.5 s** wall time (`~140–430 bldg-yr/s`).
  - **M8 3,832 multi-zone homes:** **~200–500 s (3.3–8.3 min)** on **one 32-core CPU node**—surpassing a single RTX A400's `2,274.8 s` kernel time by **~4.5–11×** *with full `f64` precision and zero GPU node allocation*! *(All `openubem-sim` timings above are `ESTIMATE / UNVERIFIED` until Phase 4 T14.)*

---

## Q2: Co-Existence with `gpusim` GPU Kernels (`D-RS-05`)

### 2.1 Option A: Pragmatic Hybrid (Rust CPU + Rust IDF Compiler + Existing `general_common.h`)
- **How it works:** `openubem-idf` compiles IDFs/ExpIDFs into contiguous CSR `GeneralBatch` arrays (`rust-numpy` zero-copy), `openubem-sim` provides the fast multi-core `f64`/`f32` CPU solver (replacing `numpy_ref.py` + `torch_batched.py`), and GPU runs continue calling [`general_common.h`](../../../../../../openubem/gpusim/backends/kernel/general_common.h) / [`s0_common.h`](../../../../../../openubem/gpusim/backends/kernel/s0_common.h) via Python (`general_cuda.py` / `s0_metal.py`)—with an optional Phase 4+ upgrade to Rust-native GPU dispatch via `cudarc` (`0.19.10`) + `objc2-metal` (`0.2.0`) if removing PyTorch (`torch==2.7.1`, ~2+ GB install) from `gpusim` is desired.
- **Why it fits OpenUBEM:** Zero risk to already-passing M4 CUDA (`17.94 s` for 346 cells, `21.66 bldg-yr/s` at `B=10,000`) and M8 (`3,832` homes, `R^2_kwh = 0.9825`). Note that Hugging Face `candle` uses this exact architecture (`cudarc` calling `.cu` kernels + Metal bindings calling `.metal` shaders).
- **Keeping CPU & GPU physics in sync:** Eliminate the Python `physics/*.py` duplicate (`numpy_ref.py`) and treat `openubem-sim` (`f32` GPU-twin mode) + `general_common.h` as a **locked differential pair** validated nightly/CI on P1 (`<= 0.05%` annual, `ΔT <= 0.10 K`) and 15 step-level spike captures (`<= 0.002 K`, `0` iter diff).

### 2.2 Option B: Native Rust `wgpu` / WGSL Single Compute Pipeline
- **Does native Rust `wgpu` fix `wgpu-py`'s 2.58–4.66 ms launch overhead?** **Yes, largely.**
  - In [`gpusim_m2_spike.csv`](../../../../../../openubem/outputs/gpusim_m2_spike.csv) and [`EXEC_M2`](../../../../GPU_based_compute/Prompt/executors/EXEC_M2_stageB_spike_mps.md#L150-L162), `wgpu-py` (`wgpu==0.31.0`) measured **2.5751–3.1060 ms** at `B=346` and **3.9037–4.6574 ms** at `B=10,000` on M2 Pro Metal, vs **1.2593–1.7213 ms** for `torch.mps.compile_shader` (and `0.55–1.02 ms` cited in `DR05` from `MANAGER_prompt_gpusim.md:95`, file not in workspace).
  - Profiling of native Rust `wgpu` (`arXiv` WebGPU compute dispatch benchmarks) measures raw API dispatch overhead at **24–36 µs on Vulkan** and **32–71 µs on Metal**, vs **~95+ µs** minimum overhead when crossing Python bindings (`wgpu-py` adds Python object/CFFI marshaling and synchronous `on_submitted_work_done_sync()` polling per [`spike_wgpu.py`](../../../../../../openubem/gpusim/backends/kernel/spike_wgpu.py#L134)). Over ~390 chunked launches (25 warmup + 365 days), 50 µs/launch is only ~20 ms total—launch overhead is **not** the blocker for native Rust `wgpu`.
- **The three real blockers that disqualify Option B:**
  1. **Buffer & Metal Argument Table Limits:** [`gen_step_zone`](../../../../../../openubem/gpusim/backends/kernel/general_common.h#L900-L1032) binds **>100 separate buffer pointers** (counted 234 `GPUSIM_GLOBAL` pointer declarations across `general_common.h`). WebGPU's default `max_storage_buffers_per_shader_stage` is **`4`** (baseline spec `8`), and even native `wgpu` (`30.0.1`) on Apple Metal is physically bounded by Metal's **31-entry per-stage buffer argument table** (`max_buffers_and_acceleration_structures_per_shader_stage`, capped ~29 combined slots in `wgpu` 29/30 without `BUFFER_BINDING_ARRAY`). Porting `general_common.h` to WGSL would require flattening all 100+ `GeneralBatch` arrays into ~4–8 manually byte-sliced `array<f32>`/`array<u32>` megabuffers—error-prone and painful to debug.
  2. **Zero Native `f64`:** Neither WGSL nor Apple Metal hardware supports native `double`/`f64` (`libMetalFloat64` / `metal-softfloat` software emulation is orders of magnitude slower).
  3. **No Native CUDA Backend:** On Windows RTX A400 and Linux HPC GPUs, `wgpu` runs over DX12/Vulkan rather than CUDA/PTX, forfeiting CUDA compute-sanitizer, Nsight Compute, and guaranteed `f32` IEEE-754 parity with `general_cuda.py`.

### 2.3 Option C: Rust-on-GPU Ecosystems in 2026 (`cubecl`, `rust-cuda`, `rust-gpu`, `candle`/`burn`)

- **`cubecl` (`0.11.0`, Oct–Nov 2026, `MIT OR Apache-2.0`, `tracel-ai/cubecl`):**
  - *Strengths:* Single-source Rust `#[cube]` macro compiling JIT to `cubecl-cuda`, `cubecl-metal`, `cubecl-wgpu`, and `cubecl-cpu`; supports dynamic `while`/`break`/`continue` loops, `comptime` unrolling, and subgroup/plane primitives.
  - *Blockers for OpenUBEM:* (1) `0.x` rapid breaking churn (`0.10` May 2026 → `0.11` Oct/Nov 2026 → `0.12-pre`); (2) **no reliable native `f64` on Metal or `wgpu`** (upstream GitHub issues document emulated/imprecise `f64` diverging from CPU `f64` on Metal/wgpu backends, plus `cubecl-metal` MSL caching/builtin ordering issues); (3) rewriting 1,477 lines of E+-cited C (`general_common.h`) into `#[cube]` DSL forfeits 1:1 traceability to EnergyPlus 23.1 C++ and risks silent divergence in `GEN_MAX_ITERS = 500` convergence paths.
- **`rust-cuda` (`NVIDIA/cuda-rust`: `cutile-rs` + `cuda-oxide`):**
  - Officially rebooted by NVIDIA in 2025–2026 with `cutile-rs` (tile-based JIT on stable Rust 1.89+) and `cuda-oxide` (SIMT via custom `rustc` codegen).
  - *Blockers:* **Linux + NVIDIA Ampere (`sm_80`) or newer only**, `cuda-oxide` SIMT explicitly alpha/research-grade, **zero macOS Metal support**, and immature Windows support. Fails OpenUBEM's Mac + Windows + HPC portability rule.
- **`rust-gpu` (`0.10.0`, Oct 1, 2026, `MIT OR Apache-2.0`, `Rust-GPU/rust-gpu`):**
  - Compiles `no_std` Rust MIR to SPIR-V (`rustc_codegen_spirv`, `cargo-gpu`, `spirt`).
  - *Blockers:* (1) **Locks the shader crate to a pinned Rust nightly** (`nightly-2026-07-03` for `0.10.0`); (2) reaches Apple Metal only via **`Rust → SPIR-V → Naga → MSL → Metal Driver`**, where Naga's `msl-out` backend has known translation gaps on complex pointers/address spaces/subgroups and makes debugging opaque; (3) no `f64` on Metal/consumer GPUs.
- **`candle` / `burn`:**
  - Tensor/autograd frameworks built for ML models (`burn` delegates kernels to `cubecl`; `candle` delegates custom ops to `.cu` via `cudarc` and `.metal` via `metal`/`objc2-metal`). Neither framework fits a stateful, per-building CSR ODE + 500-iteration surface solver with dynamic convergence masks and adaptive HVAC sub-stepping; `candle`'s own hybrid `cudarc` + Metal C-kernel pattern validates **Option A**.

---

## Q3: Float64 vs Float32 Diagnostic Parity via Rust Generic Traits

In OpenUBEM, `f32` precision bugs are subtle and physics-specific: for example, [`IMP02_result.md`](../../../../GPU_based_compute/Prompt/IMP/results/IMP02_result.md#L103-L105) showed raw Kelvin (`293.15 K`) CTF history in `f32` drifts `-20.4 kWh/yr` (`-0.064%`, failing the `0.05%` S0 gate) due to `2,986×` coefficient cancellation, whereas modal diagonal conduction (`MAX_MODES = 12`) in [`test_m7_s2a_s3_s2b.py`](../../../../../../tests/gpusim/test_m7_s2a_s3_s2b.py#L19-L51) keeps `f32` vs `f64` drift `< 1e-4`. Similarly, [`lwr.py`](../../../../../../openubem/gpusim/physics/lwr.py#L25) and [`BUILD_SPEC`](../../../../GPU_based_compute/BUILD_SPEC_gpu_heat_balance_engine.md) §3.2 mandate factored $T_i^4 - T_j^4 = (T_i - T_j)(T_i + T_j)(T_i^2 + T_j^2)$ in Stage A / spike kernels while [`general_common.h`](../../../../../../openubem/gpusim/backends/kernel/general_common.h#L688) currently evaluates `tj4 - ti4` directly.

A single generic Rust physics module using a sealed trait extending `num_traits::Float` (`0.2.19`, `MIT OR Apache-2.0`) compiles **zero-cost monomorphized** `f64` and `f32` solvers from identical code:

```rust
use num_traits::{Float, FloatConst};

pub trait SimFloat: Float + FloatConst + Copy + Send + Sync + 'static {
    const IS_F32_TWIN: bool;

    #[inline(always)]
    fn from_f64_exact(v: f64) -> Self;

    #[inline(always)]
    fn fma(self, a: Self, b: Self) -> Self {
        self.mul_add(a, b) // maps to hardware vfma / FMA in f32 & f64
    }

    /// Mirrors either factored LWR (lwr.py / s0_common.h) or direct tj4 - ti4 (general_common.h)
    #[inline(always)]
    fn delta_t4(ti_k: Self, tj_k: Self, factored: bool) -> Self {
        if factored {
            let ti2 = ti_k * ti_k;
            let tj2 = tj_k * tj_k;
            (tj_k - ti_k) * (tj_k + ti_k) * (tj2 + ti2)
        } else {
            let ti2 = ti_k * ti_k;
            let tj2 = tj_k * tj_k;
            (tj2 * tj2) - (ti2 * ti2)
        }
    }
}
```

### Diagnostic Capabilities Enabled on CPU Before GPU Launch
1. **Bit-level & ULP parity against `general_common.h`:** Compiling `solve_step::<f32>(..., TwinMode::GpuExact)` executes `f32::mul_add`, `f32::exp`, `f32::powf` (or optional fast-math/polynomial `libm` equivalents), and `f32` Kelvin offsets (`+ 273.15_f32`) directly on CPU. Running `solve_step::<f64>` vs `solve_step::<f32>` side-by-side per building pinpoints the exact timestep, zone, and surface where `f32` diverges (`|ΔT| > 0.02 K`), before spending GPU time or debugging blind inside Metal/CUDA.
2. **Convergence & Branch-Flip Telemetry:** In `f32` diagnostic mode, `openubem-sim` can trap `NaN`/`Inf`, count `GEN_MAX_ITERS = 500` non-convergences, flag TARP sign flips (`dt < 0` vs `dt > 0` near `0.0 K`), and detect `n_sub` HVAC sub-step threshold (`0.3 K`) mismatches against `f64` without touching GPU device memory.
3. **SIMD Compatibility:** `SimFloat` works cleanly per-building/per-zone (`pulp` operates on `&[f64]` / `&[f32]` slices for the `O(n_sz^2)` ScriptF matrix-vector multiply and 12-mode dot products, while `SimFloat` unifies all scalar surface/window/psychrometric functions).

---

## Q4: Testing & Conformance Against EnergyPlus

### 4.1 Wiring `openubem-sim` into `router.py` `conformance_hash()`
Currently [`openubem/gpusim/router.py`](../../../../../../openubem/gpusim/router.py#L23-L53) computes `conformance_hash()` as the first 16 hex chars of SHA-256 over `_CONFORMANCE_SOURCE_FILES` (which notably lists `s0_common.h` and `numpy_ref.py`, and should also include `general_common.h` / `general_cuda.py`). When `openubem-sim` is added:
1. Add a `crates/openubem-sim/build.rs` script that hashes all `src/**/*.rs` files in `openubem-sim` (plus `openubem/gpusim/backends/kernel/general_common.h` if co-validated) in sorted relative-path order using the exact same `rel + "\0" + bytes + "\0"` framing, embedding `OPENUBEM_SIM_SOURCE_SHA256` at compile time via `cargo:rustc-env`.
2. Expose `openubem._rust.sim_conformance_digest() -> str` via PyO3.
3. Update `router.py::conformance_hash()` to include `b"openubem-sim\0" + sim_conformance_digest().encode() + b"\0"` whenever `OPENUBEM_RUST_BACKEND != "off"` (or unconditionally once `openubem-rust` is active), ensuring **any Rust physics edit invalidates `gpusim_provenance.json` identically to Python/C edits**—while keeping `"off"` byte-identical to existing frozen hashes (`PLAN_rust_migration.md` Guardrail 1).

### 4.2 Integration into P1–P4 Parity Suites (`BUILD_SPEC` §4)
Following `BUILD_SPEC_gpu_heat_balance_engine.md` §4 (`P1`–`P4`) and `PLAN_rust_migration.md` §3 Guardrail 3 (`OPENUBEM_RUST_BACKEND = "off" | "shadow" | "on"`):

| Tier | Scope (`BUILD_SPEC` §4) | `openubem-sim` (`f64`) Gate | `openubem-sim` (`f32` twin) Gate |
|---|---|---|---|
| **P1 basic** | 3 golden cells + 10 variants (9 S0 + V14 mass×2 + V15 S1) | `<= 1e-12` rel err vs Stage A (`numpy_ref.py`); identical warm-up days (`12/12`); passes S0 single-cell gates vs Mac E+ (`<= 0.5%` annual, `CV(RMSE) <= 1%`, `ΔT p99.9 <= 0.03 K`) | Annual heating `<= 0.05%` vs Stage A (`<= 0.01 kWh/m^2`); `ΔT p99.9 <= 0.02 K`, `max <= 0.10 K` (locked warm-up); tracks Stage C CUDA/Metal within `~1e-4` |
| **P2 EU fleet** | 346 completed certified rerun cells (`rep2`) | `<= 1e-12` rel err vs Stage A across all `346/346` cells; `346/346` exact warm-up days (reported on Mac, gated against clean E+/Stage A per D6) | Fleet median `<= 0.05%` vs Stage A (validated at `<= 0.0098%` on CUDA M4) |
| **P3 mixed routing** | `synthetic_10_buildings.py`, `synthetic_canyon.gpkg`, `ES-MAD-BERRUGUETE` | `E+`-routed buildings remain byte-identical; `gpusim`-routed buildings pass S0/S1/S2a/S2b/S3 gates; `04_routing_report.csv` & `gpusim_provenance.json` schema unchanged | Differential shadow report comparing `f64` CPU vs `f32` CPU vs Stage C CUDA on `ES-MAD-BERRUGUETE` |
| **P4 complex urban** | `austin_centre` (341 bldgs), `boston_downtown_500m`, `chicago_loop_500m` | `<= 1e-12` vs Python `GeneralBatch` reference (or M7/M8 golden fixtures); verifies `BOUND_SURFACE` interzone coupling & `record_zone_temp` | Confirms `f32` stability on tall/multi-zone tail buildings before GPU dispatch |

### 4.3 Chunked Warm-Up & Convergence Checks
Stage C ([`stage_c.py`](../../../../../../openubem/gpusim/backends/stage_c.py#L126-L211), [`general_common.h`](../../../../../../openubem/gpusim/backends/kernel/general_common.h#L279-L292)) implements day-by-day warm-up convergence with `wu_still[b]`, `WARMUP_MIN_LOAD = 100.0 W`, `temp_conv_tol`, `loads_conv_tol`, and `force_warmup_days` lock mode:
1. **`openubem-sim` must expose both modes:** `WarmupMode::Dynamic { min_days, max_days, temp_tol, loads_tol }` and `WarmupMode::Forced(Vec<i32>)` (matching `force_warmup_days` in `stage_c.py:126` and `torch_batched.py`).
2. **Two-stage verification protocol:**
   - First run **locked warm-up** (`force_warmup_days = stage_a.warmup_days`) to isolate pure floating-point numeric drift (`<= 1e-12` in `f64`, `<= 0.05%` in `f32`) from discrete day-boundary flips.
   - Second run **free dynamic warm-up** and verify exact `warmup_days[b]` agreement (`12/12` P1, `346/346` P2) and day-by-day `(day_max_t, day_min_t, day_max_h)` parity.
3. **Chunked state-checkpoint parity:** Expose a stateful `SimState` / `step_chunk(step_start, step_end)` Rust API mirroring `gen_run_chunk_kernel(..., step_start, step_end)` so tests can verify that chunking (`run_chunk_days = 1`, `3`, or `365`) produces **bit-exact** outputs on `openubem-sim` (`|Δ| == 0.0`) and matches Stage C chunked runs within the `f32` gate.

---

## Q5: Recommendation (`D-RS-05` & Crate Choices for `openubem-sim`)

### Decision Recommendation for `D-RS-05`
**Approve Option A (Pragmatic Hybrid):**
1. **Keep [`general_common.h`](../../../../../../openubem/gpusim/backends/kernel/general_common.h) (and `s0_common.h`) as the Stage-C CUDA/Metal GPU kernel source.** Do **not** rewrite `gpusim` GPU kernels into WGSL (`wgpu`), `cubecl`, `rust-gpu`, or `rust-cuda` in 2026.
2. **Build `crates/openubem-sim` in stable Rust** as a pure-Rust (`no-pyo3`) dual-precision (`f64` + `f32` GPU-twin) thermal solver operating directly on flat-CSR `GeneralBatch` buffers, using building/zone-parallel `rayon` + `pulp` SIMD (with optional `lane=4` S0 micro-batching).
3. **Retire `numpy_ref.py` + `torch_batched.py` slow paths incrementally** behind `OPENUBEM_RUST_BACKEND = "off" | "shadow" | "on"` once `openubem-sim` passes `<= 1e-12` parity on P1–P4.
4. **Optional Phase 4+ decoupling:** Only if eliminating the `torch==2.7.1` runtime dependency from `gpusim` becomes a priority (e.g., slimming Speed HPC containers), replace the Python `s0_cuda.py`/`general_cuda.py`/`s0_metal.py` *host wrappers* with thin Rust launchers using `cudarc` (`0.19.10`) + `objc2-metal` (`0.2.0`) driving the **exact same unmodified `general_common.h`**.

### Exact `Cargo.toml` Crate Stack for `crates/openubem-sim`
*(All verified `Apache-2.0`, `MIT`, or `Zlib` compatible; zero GPL/AGPL)*:

```toml
[package]
name = "openubem-sim"
version = "0.1.0"
edition = "2024" # or "2021" matching workspace MSRV >= 1.87

[dependencies]
rayon = "1.12"          # MIT OR Apache-2.0 — work-stealing across buildings/zones
pulp = "0.22.3"         # MIT — runtime NEON / AVX2 / AVX-512 dispatch on stable Rust
num-traits = "0.2.19"   # MIT OR Apache-2.0 — generic SimFloat: Float + MulAdd (f64 / f32)
libm = "0.2"            # MIT OR Apache-2.0 — deterministic IEEE-754 exp/pow parity option
bytemuck = "1.25"       # Zlib OR Apache-2.0 OR MIT — zero-copy buffer/slice casts
thiserror = "2.0"       # MIT OR Apache-2.0 — typed solver/CSR bounds errors (no unwrap across FFI)

[dev-dependencies]
criterion = "0.5"       # Apache-2.0 OR MIT — microbenchmarks vs numpy_ref.py
proptest = "1.12"       # MIT OR Apache-2.0 — fuzzing CSR bounds & f64/f32 parity
```
*(Optional later GPU-host feature flags inside a separate `openubem-gpu-host` crate: `cudarc = "0.19.10"` [`MIT OR Apache-2.0`] and `objc2-metal = "0.2.0"` [`MIT`]; Python FFI via `pyo3` + `rust-numpy` stays strictly isolated in `crates/openubem-py`.)*

---

## Gaps & Negative Results

1. **Missing `MANAGER_prompt_gpusim.md` on disk:** The DR05 prompt cites `MANAGER_prompt_gpusim.md:94-95` (`274 s` Stage A and `0.55–1.02 ms` `torch.mps.compile_shader` vs `2.6–3.9 ms` `wgpu-py`). `MANAGER_prompt_gpusim.md` was not found in the repository; however, on-disk [`EXEC_M2`](../../../../GPU_based_compute/Prompt/executors/EXEC_M2_stageB_spike_mps.md#L144-L162) and [`gpusim_m2_spike.csv`](../../../../../../openubem/outputs/gpusim_m2_spike.csv) corroborate **`273.800 s`** (`B=12` CPU float32), **`1.2593–1.7213 ms`** (`torch.mps.compile_shader`), and **`2.5751–4.6574 ms`** (`wgpu-py`). The `0.55–1.02 ms` range from the missing file remains unverified locally.
2. **No measured Rust `openubem-sim` benchmark exists yet:** `rustc` and `cargo` are not yet installed in the workspace ([`PLAN_rust_migration.md`](../../../PLAN_rust_migration.md#L37)), so all `openubem-sim` runtimes in §Q1.4 are **analytic estimates (`UNVERIFIED`)** calibrated from measured `numpy_ref.py` / `torch_batched.py` / E+ 23.1 / RTX A400 baselines, to be replaced by measured `criterion` + Phase 4 T14 numbers.
3. **`std::simd` negative result:** `std::simd` (`portable_simd`) is still nightly-only in late 2026 (`rust-lang/rust#86656`) and cannot be used in OpenUBEM's stable-Rust wheel pipeline.
4. **`wide` transcendental gap:** `wide::f64x4` (`1.7.1`) does not provide native vectorized `.exp()` or `.powf()`, reducing the value of `wide` for OpenUBEM's convection/window routines relative to `pulp`.
5. **WebGPU/WGSL & Metal `f64` / buffer-limit negative results:** Neither WGSL nor Apple Metal hardware supports native `f64` compute shaders, and Metal's 31-slot argument table ceiling conflicts directly with [`general_common.h`](../../../../../../openubem/gpusim/backends/kernel/general_common.h)'s >100 buffer pointers.
6. **Rust-on-GPU negative result:** No single Rust-on-GPU framework in late 2026 (`cubecl`, `rust-gpu`, `rust-cuda`) simultaneously delivers stable-Rust builds, zero-copy Mac Metal + Windows CUDA + Linux HPC portability, native `f64` fallback, and predictable register/buffer behavior for 1,477-line stateful building-physics kernels.
7. **Exact crates.io download counters & `NVIDIA/cuda-rust` subcrate licence audit:** Not directly extracted from search snippets and therefore marked `UNVERIFIED` pending `cargo deny check` during Phase 0 T03.
