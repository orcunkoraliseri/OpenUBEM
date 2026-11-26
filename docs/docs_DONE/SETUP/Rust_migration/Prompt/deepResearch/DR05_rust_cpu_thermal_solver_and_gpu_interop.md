# DR05 — Rust CPU Thermal Solver & GPU Interop (`gpusim` Co-Design)

**Feeds:** Plan §4 (R4), Phase 4 (T12, T14), and Owner Decision D-RS-05
**Save output to:** `results/DR05_result.md`

---

## PROMPT

You are a high-performance scientific-computing architect specialising in Rust numerical simulation (`rayon`, portable SIMD), GPU compute interop (`CUDA`, `Metal`, `wgpu`, `cudarc`, `cubecl`), and differential numerical verification across CPU float64 and GPU float32 backends. Produce a rigorous, source-cited architectural report.

### Context
OpenUBEM already has a working, validated GPU heat-balance engine (`openubem/gpusim/`) implementing EnergyPlus 23.1 equations (S0–S3/S2b, modal diagonal state-space conduction `MAX_MODES = 12`, TARP/DOE-2/ISO-15099 convection, ScriptF longwave exchange, 3rd-order backward-difference zone air & humidity corrector, HVAC sub-stepping, warm-up convergence):
- **Stage A (`openubem/gpusim/backends/numpy_ref.py`):** Executable float64 NumPy specification. Runs in **274 s** for 12 single-zone cells (`MANAGER_prompt_gpusim.md:94`) because of a 105,120-step Python loop.
- **Stage C (`openubem/gpusim/backends/general_cuda.py` + `kernel/general_common.h` + `kernel/s0_metal.py`):** C/CUDA/Metal fused kernels running in chunked launches. On Windows RTX A400 (4 GB VRAM, CUDA), M8 simulated **3,832 homes / 43,989 zones / 523,530 surfaces** in **2,274.8 s (37.9 min)** of GPU kernel time (`max_launch = 0.861 s`, zero TDR resets).
- **HPC constraint:** Concordia's Speed HPC cluster gives us 32-core CPU SLURM arrays easily, whereas GPU nodes are scarce (`max 4 GPUs/user`). A fast multi-core CPU solver in Rust would make Speed HPC and local M2 Pro 12-core runs dramatically faster while also replacing the 274 s Stage-A Python reference.

### Questions
1. **Pure-Rust CPU thermal solver (`openubem-sim`) performance & layout.** Given OpenUBEM's flat CSR `GeneralBatch` structure (zones × surfaces × timesteps, sequential 8,760 × 6–12 timesteps per building, inner surface iteration up to 500 iters, 12-mode exponential decay), what memory layout (AoS per-building vs SoA-across-SIMD-lanes `[lane=4|8]` batched buildings) and SIMD crates (`wide`, `pulp`, `std::simd` status in 2026) maximize CPU throughput across 12-core M2 Pro (NEON) and 32-core x86_64 HPC (AVX2/AVX-512)? Estimate realistic speedup vs Python `numpy_ref.py` (274 s) and vs 1-core EnergyPlus (~4 s/cell, ~20–40 s/multi-zone EU building).
2. **Co-existence with `gpusim` GPU kernels (D-RS-05).** Compare three architectures for keeping CPU and GPU physics in sync without maintaining divergent copies of equations:
   - **Option A (Pragmatic hybrid):** Rust CPU solver (`openubem-sim`, dual float64/float32) + Rust compiler (`openubem-idf`), while keeping existing CUDA/Metal C headers (`general_common.h`) launched via Python/PyTorch or Rust `cudarc` / `metal-rs`.
   - **Option B (`wgpu` / WGSL):** Rewrite Stage-C kernels into a single WGSL compute pipeline driven from Rust (cross-platform Metal + Vulkan/DX12, float32 only). Note: our M2 spike (`MANAGER_prompt_gpusim.md:95`) previously found `wgpu-py` launches were 2–5× slower than `torch.mps.compile_shader` (2.6–3.9 ms vs 0.55–1.02 ms), and WebGPU caps storage buffers per kernel — does native Rust `wgpu` solve the launch overhead?
   - **Option C (Rust-on-GPU ecosystems in 2026):** Evaluate maturity, production readiness, and Mac Metal + Windows CUDA support of **`cubecl`** (Burn's GPU compute crate), **`rust-cuda`**, **`rust-gpu`** (SPIR-V/Vulkan/Metal), and **`candle`/`burn`**. Are any ready for stateful chunked ODE/surface-iteration kernels with dynamic convergence masks and float64 diagnostic fallback?
3. **Float64 vs float32 diagnostic parity.** How do Rust's `f64`/`f32` generic traits (`num_traits::Float`) let one generic Rust physics module compile both the exact float64 reference (replacing `numpy_ref.py` + `physics/*.py`) and a float32 twin that mirrors Metal/CUDA arithmetic (`fma`, `exp`, factored $T_i^4 - T_j^4$) for catching device bugs before GPU launch?
4. **Testing & conformance against EnergyPlus.** How to wire `openubem-sim` into `gpusim`'s conformance hash (`router.py:43-53`), P1–P4 parity suites, and chunked warm-up convergence checks.
5. **Recommendation.** Clear decision advice for D-RS-05 (Option A vs B vs C) and exact Rust crate choices for `openubem-sim`.

### Required output format
- **Executive summary** (≤10 bullets).
- **Table: CPU+GPU architecture options (A vs B vs C)** across portability (Mac/Win/HPC), float64 support, launch overhead, register/buffer limits, ecosystem maturity (2026), and engineering risk.
- **Table: Rust SIMD & GPU compute crates** (`wide`, `pulp`, `cudarc`, `wgpu`, `cubecl`, `rust-gpu`): licence, latest version, last commit, production readiness (1–5).
- Sections answering Q1–Q5.
- **Gaps & negative results**.

### Rules
- Cite every factual claim (URL / DOI / crate release + date). Mark anything uncited `UNVERIFIED`.
- Distinguish measured benchmarks from estimates, stating exact hardware and precision (`f32` vs `f64`).
- Search terms to include: "rust cubecl cuda metal 2025 2026", "rust-gpu wgpu compute shader launch overhead", "cudarc rust cuda driver", "rust portable simd wide pulp f64", "SIMD across instances SOA AOS ODE solver".
