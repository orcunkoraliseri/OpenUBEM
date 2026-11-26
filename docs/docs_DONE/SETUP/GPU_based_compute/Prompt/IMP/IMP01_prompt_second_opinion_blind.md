# IMP01 — Second opinion (blind): how to build GPU-based EnergyPlus-equivalent computation

**Purpose:** an independent architecture proposal. This prompt deliberately does **not** include our build spec, so the answer is not anchored to it. Compare the result against `../BUILD_SPEC_gpu_heat_balance_engine.md` afterwards.
**Run with:** Gemini (Deep Research or 2.5/3 Pro with search). Paste everything under PROMPT.
**Save output to:** `results/IMP01_result.md`

---

## PROMPT

You are a senior engineer in **building energy simulation internals** (EnergyPlus heat balance, CTF, zone air predictor-corrector, HVAC managers) and **GPU scientific computing** (CUDA, Metal, PyTorch, JAX, Taichi, Warp, CuPy). I want an **engineering design you could hand to a developer**, not a literature survey.

### Problem
EnergyPlus (we pin **v23.1**) has **no GPU port**. Its core is serial C++. One building runs per CPU process, and its only GPU feature is PixelCounting shadow calculation. We run urban building energy models: hundreds to tens of thousands of buildings, times scenario variants (retrofits, weather years, occupancy samples, sensitivity factors). We want to **build** GPU-based computation that gives **EnergyPlus-equivalent results** (same algorithms, close numerical agreement), at least for a subset of building models, and is much faster in aggregate. We treat "EnergyPlus has no GPU port" as the problem to solve, not as a reason to stop.

### Our models (facts)
- **Workload A (European campaign).** Each case is one zone, generated as an IDF from TABULA archetype data. It contains:
  - `Material:NoMass` single-layer constructions on all opaque surfaces;
  - `SurfaceProperty:OtherSideCoefficients` boundaries with film coefficient 0, i.e. outside face temperature = b·T_out + (1−b)·T_zone;
  - two `WindowMaterial:SimpleGlazingSystem` windows on `Outdoors` host walls;
  - one `InternalMass` (a 0.10 m massive layer; the only construction with thermal mass);
  - `ZoneVentilation:DesignFlowRate` at constant ACH;
  - convective internal gains from an hourly `Schedule:File`;
  - heating-only `HVACTemplate:Zone:IdealLoadsAirSystem` with a constant setpoint and no capacity limit;
  - `Timestep 12`, CTF conduction, default convection algorithms (TARP inside, DOE-2 outside), third-order backward-difference zone air, no shading objects.

  E+ takes about 4 s per case (M2 Pro, under Rosetta). The output we use is hourly ideal-loads heating energy.
- **Workload B (city models).** Multi-zone geomeppy block geometry, layered massive constructions, `Shading:Site:Detailed` neighbour context (up to hundreds of shading surfaces), and HVACTemplate systems: PTAC, PSZ-AC, PSZ-HP, packaged VAV, VAV with chiller/boiler plants, fan coils and water-loop heat pumps. Some buildings take about 900 s each.
- **Hardware:** develop on an **Apple M2 Pro** (Metal/MPS; no float64 on the GPU); then a **Windows workstation with an NVIDIA CUDA GPU**. We want **macOS first, then Windows**.
- **Code base:** Python (eppy/geomeppy) that writes IDFs; downstream code reads `eplusout.csv`. Licence Apache-2.0 OR MIT, so no GPL/AGPL code can be vendored.

### Questions
1. **Feasible strategies, compared.** Analyse at least these:
   - (a) porting or recompiling EnergyPlus C++ to GPU (CUDA/HIP/SYCL/OpenACC/stdpar);
   - (b) running many EnergyPlus instances with only sub-components offloaded;
   - (c) a **from-scratch GPU-native re-implementation of E+ algorithms for a declared subset of objects**, batched across buildings;
   - (d) the Modelica/OpenModelica, Spawn-of-EnergyPlus or FMU route;
   - (e) a reduced-order RC model on GPU;
   - (f) a learned surrogate.

   For each: achievable fidelity against E+, engineering effort in person-months with stated assumptions, expected speed-up, and what fails. Recommend one, or a combination, **per workload** (A and B separately).
2. **If (c): exact algorithm inventory.** For Workload A, list every EnergyPlus 23.1 algorithm we must reproduce to get, for example, ≤0.5% annual heating difference. For each, name the **E+ source file and function** in the NREL/EnergyPlus repository (tag v23.1.0). Cover at least:
   - inside and outside surface heat balance, and their iteration and convergence;
   - OSC handling;
   - TARP and DOE-2 convection;
   - interior longwave exchange (ScriptF);
   - sky and ground longwave radiation;
   - simple glazing conversion and window heat balance;
   - CTF generation and history;
   - zone air third-order backward difference and predictor-corrector;
   - ideal loads;
   - warm-up convergence;
   - weather interpolation from hourly EPW to sub-hourly timesteps;
   - output aggregation.

   Flag the parts most likely to cause disagreement.
3. **GPU mapping.** How to map that algorithm set to GPU:
   - parallel axis (building vs surface vs time);
   - thread-per-building fused kernel vs batched tensor ops with a Python time loop;
   - inner iteration loops with per-lane convergence masks;
   - warm-up loops of different length per building;
   - padding and bucketing of different surface counts;
   - memory layout (SoA vs AoS);
   - kernel-launch overhead for about 105k timesteps per year;
   - float32 vs float64 (Apple GPUs lack float64; what errors to expect in CTF and zone-air updates, and how to mitigate them).
4. **Framework for "macOS first, then Windows CUDA" from one code base.** Compare:
   - PyTorch (MPS + CUDA);
   - JAX (jax-metal maturity; CUDA only via Linux/WSL2);
   - MLX (Apple only);
   - Taichi (Metal + CUDA backends; maintenance status);
   - NVIDIA Warp (CUDA/CPU only);
   - WebGPU/wgpu-py (WGSL on Metal, Vulkan, DX12);
   - custom Metal plus custom CUDA kernels;
   - SYCL/Kokkos.

   Verify current versions, release dates and Windows/macOS support. Recommend one, with a fallback.
5. **Prior art.** Find any project that re-implemented EnergyPlus (or another detailed BEM engine) algorithms outside E+: Python, Julia, JAX, GPU or vectorised ports of the CTF/heat-balance method, BESTEST/ASHRAE 140 replications, CitySim, SimStadt, TEASER/AixLib, Modelica Buildings Library `ThermalZones.EnergyPlus`, CEA, ISO 52016 implementations. Also find any GPU or batched building-physics engine with reported throughput. For each give the URL, licence, last commit date, and what can be reused.
6. **Verification strategy.**
   - How to prove equivalence with E+: golden-output design; per-equation tests that feed E+ intermediate outputs into the new code; ASHRAE 140 / BESTEST; tolerance tables.
   - Which E+ output variables expose the intermediate quantities needed.
7. **Throughput estimate.** For Workload A on an M2 Pro GPU and on a mid/high-end NVIDIA card: estimated building-years per second for batch sizes 1k–100k. Show the arithmetic: FLOPs and bytes per building-timestep, bandwidth- vs compute-bound, launch overhead. Label it as an estimate.
8. **Roadmap.** A milestone plan from Workload A (simplest) toward Workload B: solar, multi-zone, layered CTF, exterior shading via a GPU rasteriser, simple DX HVAC. Say where to **stop** and leave cases to EnergyPlus on the CPU.

### Required output format
- **Executive summary** (≤ 15 lines): the recommended strategy per workload, the framework, and the expected speed-up with assumptions.
- **Table 1: strategies (a)–(f)**: fidelity, effort, speed-up, main blocker, verdict.
- **Table 2: algorithm inventory for Workload A**: physics item, E+ source file::function, equations (short), GPU difficulty, disagreement risk.
- **Table 3: frameworks**: macOS GPU, Windows CUDA native, float64, kernel fusion, maturity/maintenance (with dates), verdict.
- **Table 4: prior art**: URL, licence, last commit, reusable parts.
- **Reference design**: data structures with tensor shapes, kernel pseudo-code for one timestep and for the year loop, the warm-up handling, and the I/O path from IDF in to CSV out.
- **Verification plan** and **milestone roadmap**.
- **Risks**, then **References**.

### Rules
- Cite sources. Mark anything uncited or uninspected as `UNVERIFIED`. Do not invent E+ function names: if you cannot confirm a function in the v23.1.0 source, give the file only and mark the function `UNVERIFIED`.
- Give a repository's star count or last commit date only if you checked it, and say when.
- State precision and hardware for every throughput number. Separate measured numbers from estimates.
- Prefer concrete engineering detail over general discussion.
