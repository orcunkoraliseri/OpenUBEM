# GPU-Based EnergyPlus-Equivalent Computation — Independent Engineering Design

*Prepared blind (without reference to any internal build specification). Verification dates for external repositories, framework releases, and hardware specs: **2026-11-22**.*

---

## Executive Summary

- **Workload A (TABULA single-zone European campaign):** Build **(c) a from-scratch GPU-native re-implementation** of the exact EnergyPlus v23.1.0 heat-balance subset (1 zone, `Material:NoMass` envelope, 1 massive `InternalMass` CTF, `OtherSideCoefficients`, `SimpleGlazingSystem`, TARP/DOE-2, ScriptF, 3rd-order backward-difference air balance, `IdealLoadsAirSystem`, `Timestep 12`). Target agreement: **≤0.5% annual heating energy** (achievable to ≤0.2% with proper FP32 numerics).
- **Workload B (multi-zone city models with detailed `Shading:Site:Detailed` and full `HVACTemplate` plant/air loops):** Use **(b) multi-process CPU EnergyPlus (native ARM64 on macOS, multi-core on Windows) with GPU-offloaded exterior shading** (`PixelCounting` or an external GPU rasterizer pre-pass), plus optional GPU-(c) envelope pre-screening for ideal-loads cases. **Do not** port E+'s full HVAC/plant loop solver (`SimHVAC`, chillers, boilers, WLHP, VAV) to GPU—engineering cost explodes while fidelity collapses.
- **Framework ("macOS first, then Windows CUDA", one codebase, Apache-2.0/MIT):** **Primary: `wgpu-py` (WebGPU / WGSL compute shaders, v0.33.0)**—runs natively on Apple Metal and Windows DX12/Vulkan from a single `pip`-installable codebase with fused multi-day megakernels and built-in hardware rasterization for Workload B shading. **Fallback: Macro-shared C-family physics header (`hb_core.h`) compiled at runtime via `pyobjc-framework-Metal` (macOS) and `cupy.RawKernel` (Windows CUDA)** if native FP64 on Windows or CUDA-only optimizations become mandatory.
- **Architecture:** **1 GPU thread per building**, Structure-of-Arrays (SoA) memory layout, **chunked 1-day (288-timestep) or 5-day (1,440-timestep) fused megakernels** to collapse 105,120 annual timesteps to 73–365 launches (<10 ms launch overhead) while staying under the 2 s Windows WDDM TDR watchdog.
- **Estimated Speed-up (Workload A, FP32, batch 10k–100k, compute-only, ESTIMATE):**
  - **Apple M2 Pro (19-core GPU):** ~1,500–2,500 building-years/s → **~6,000–10,000× vs. 1 Rosetta CPU core** (4 s/case), or **~600–1,000× vs. 10 native/Rosetta CPU cores**.
  - **NVIDIA RTX 4080 / 4090 (Windows):** ~8,400–20,000 / ~12,000–30,000 building-years/s → **~50,000–120,000× vs. 1 Rosetta core** (~100k cases in 3–12 s compute). End-to-end throughput will be **I/O-bound** unless IDF text parsing (`eppy`) and per-case CSV writes are bypassed.

---

## 1. Feasible Strategies Compared

### Table 1: Strategies (a)–(f)

| Strategy | Achievable Fidelity vs. E+ v23.1 | Engineering Effort (Person-Months)* | Expected Aggregate Speed-up (ESTIMATE) | Main Blocker / What Fails | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **(a) Port / recompile E+ C++ to GPU** (CUDA/HIP/SYCL/OpenACC/stdpar) | Exact (~0.001%) if completed | **36–60+ PM** (infeasible for small team) | 0.2×–3× (often *slower* on GPU) | E+ is ~1M LOC of pointer-chasing OOP (`EnergyPlusData& state`), virtual dispatch, dynamic `Array1D` allocations, deep call graphs, and string lookups inside hot loops. Zero SIMT coherence; massive warp divergence across branches. | **Reject** for both A & B |
| **(b) Multi-process CPU E+ with GPU sub-component offload** (native ARM64 + GPU shading) | Exact (0.0% core; ≤0.5% with `PixelCounting` shading) | **1–2 PM** (native build, batch orchestrator, GPU shading pipeline) | **Workload A:** 10–30× (native ARM64 + 10–32 CPU cores; removes Rosetta penalty).<br>**Workload B:** 5–20× (CPU parallelism + ~2×–5× shading acceleration on heavy `Shading:Site:Detailed`). | Still bound by CPU core count for thermal/HVAC stepping; cannot reach 1k+ bldg-yr/s for Workload A. | **Reject** for A (too slow for 10k–100k sweeps); **Recommend (Primary)** for B |
| **(c) From-scratch GPU-native E+ algorithm re-implementation (declared subset)** | **Workload A:** ≤0.2–0.5% annual heating (≤0.05% in FP64).<br>**Workload B (envelope only):** ≤1–2%; full HVAC impractical. | **Workload A:** **3–5 PM** (physics + WGSL/CUDA + verifier + batch I/O).<br>**Workload B (full HVAC):** **30–50+ PM**. | **Workload A:** **600–1,000×** (M2 Pro) to **5,000–15,000×** (RTX 4080/4090) vs. 10-core CPU E+.<br>**Workload B (envelope/ideal loads):** 100–1,000×. | Scope creep: every added E+ object (air loops, plant loops, coil curves, controls, complex fenestration) multiplies edge cases and divergence. FP32 cancellation risks on heavy walls without care. | **Recommend (Primary)** for A; **Partial (envelope/shading)** for B |
| **(d) Modelica / OpenModelica / Spawn of EnergyPlus / FMU** | **Spawn:** Exact envelope (calls E+ internally!), divergent HVAC.<br>**AixLib/Buildings:** 2–10% vs. E+ | **4–8 PM** (translation, FMI orchestration, compiler pipeline) | **0.2×–1.5×** (often *slower* than raw E+ due to DAE solver overhead & FMI IPC; no native GPU batching) | Spawn still runs serial CPU EnergyPlus under the hood (`Buildings.ThermalZones.EnergyPlus`). OpenModelica/Dymola compiles to CPU C code (SUNDIALS/CVODE), not GPU SIMT kernels. | **Reject** for GPU throughput (useful only for controls co-simulation) |
| **(e) Reduced-order RC model on GPU** (5R1C ISO 13790 / 7R2C / ISO 52016) | **5–25% annual heating error** vs. E+ (worse on peak loads & solar gains; 2–8% only *after* per-archetype calibration) | **1.5–2.5 PM** | **2,000–5,000×** (M2 Pro) to **20,000–50,000×** (RTX 4090) | Cannot replicate TARP/DOE-2 convection, ScriptF longwave, SimpleGlazing angular optics, or 3OBD air balance. Fails "EnergyPlus-equivalent results" requirement without fragile calibration. | **Reject** as E+ replacement; optional ultra-fast pre-filter only |
| **(f) Learned surrogate** (GBDT / MLP / GNN / FNO trained on E+ runs) | **1–5% in-distribution** (annual); **5–20% hourly**; unpredictable out-of-distribution | **2–4 PM** (sampling, E+ training set generation, feature engineering, UQ) | **10,000–100,000×** at inference (amortized speed-up drops to 5–50× including E+ training runs) | Breaks on unseen retrofits, weather years, occupancy schedules, or geometry outside training support. Requires thousands of E+ runs upfront for every new campaign schema. | **Reject** for A (physics engine (c) is nearly as fast and exact); **Optional add-on** for B parametric sweeps |

*\*Effort assumptions: 1 senior engineer fluent in Python, GPU compute shaders (WGSL/CUDA/Metal), and building physics; includes unit verification against E+ v23.1.0 golden outputs.*

### Recommendation per Workload
- **Workload A → Strategy (c):** The declared object set is small, clean, and has zero HVAC plant complexity. Re-implementing the exact E+ v23.1.0 physics in a batched GPU kernel takes ~3–5 person-months, hits ≤0.5% fidelity without calibration, generalizes to arbitrary weather/schedules/retrofits, and delivers 10,000 building-years in seconds.
- **Workload B → Strategy (b) + GPU Shading Pre-pass (+ optional (f) surrogate for sensitivity):** First, switch to **native ARM64 EnergyPlus** on M2 Pro and multi-process workers on Windows, and offload `Shading:Site:Detailed` to a GPU rasterizer (`PixelCounting` or a custom `wgpu` orthographic shadow-map pre-pass writing sunlit fraction schedules). Because Workload B buildings take up to 900 s largely due to hundreds of shading polygons + multi-zone plant/HVAC iterations, GPU shading plus CPU multiprocessing recovers major speed-up with 100% HVAC fidelity. Only move Workload B's *envelope-only / IdealLoads* studies onto the GPU engine (c).

---

## 2. Exact Algorithm Inventory for Workload A (EnergyPlus v23.1.0)

> **Verification note:** Source file paths correspond to `NREL/EnergyPlus` (`src/EnergyPlus/`, tag `v23.1.0`). Function names confirmed in public source/issue references are given verbatim; internal helper symbols not directly verified in `v23.1.0` source lines are explicitly marked `UNVERIFIED` per project rules.

### Table 2: Workload A Algorithm Inventory

| # | Physics Item | E+ v23.1.0 Source File :: Function | Core Equations (Short) | GPU Difficulty | Disagreement Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | **Weather ingestion & sub-hourly interpolation** | `WeatherManager.cc` :: `ManageWeather` *(interpolation helper: `UNVERIFIED` in v23.1.0)* | Linear interpolation of hourly EPW values ($T_{\text{db}}, T_{\text{dp}}, P_{\text{atm}}, W_{\text{spd}}, \text{DNI}, \text{DHI}$) to sub-hourly step $m \in \{1..12\}$ using weight $w = m / N_{\text{ts}}$ between hour $h-1$ and $h$ (careful: E+ EPW hour $h$ represents interval $(h-1, h]$; state variables like $T_{\text{db}}$ interpolate between `PrevHour` and `CurrHour`, while solar is interpolated/centered per E+ solar step convention). | **Low** (precompute once on CPU per EPW; broadcast via constant/read-only GPU buffer) | **HIGH** — half-step / end-of-hour shift in EPW solar & dry-bulb interpolation causes systematic 1–3% diurnal heating shifts. |
| 2 | **Solar position, Perez anisotropic sky & incident solar** | `SolarShading.cc` :: `InitSolarCalculations` *(exterior solar & Perez sky helpers: `UNVERIFIED` in v23.1.0)* | Sun vector $(\alpha_s, \gamma_s)$ at mid-timestep; Perez 1990 diffuse sky model ($I_{\text{diff}} = \text{DHI}[(1-F_1)\frac{1+\cos\Sigma}{2} + F_1\frac{a}{b} + F_2\sin\Sigma]$); ground reflection $\rho_g \text{GHI}\frac{1-\cos\Sigma}{2}$; incidence angle $\cos\theta_i$. **Note:** Even with *no shading objects*, Workload A has `Outdoors` walls and 2 windows receiving full solar! | **Low–Medium** (sun vector & Perez $F_1, F_2$ precomputed on CPU per step; per-surface $\cos\theta_i$ trivial on GPU) | **HIGH** — omitting Perez anisotropic diffuse or using isotropic sky shifts winter south-window gains by 1–4%. |
| 3 | **Sky & ground longwave radiation** | `WeatherManager.cc` :: `CalcSkyTemperature` *(exact v23.1.0 signature `UNVERIFIED`)*; `HeatBalanceSurfaceManager.cc` :: `CalcHeatBalanceOutsideSurf` | $T_{\text{sky}} = (I_{\text{IR,horiz}}/\sigma)^{1/4} - 273.15$ (or Clark-Allen cloud correlation if EPW IR missing); $\beta = \sqrt{(1+\cos\Sigma)/2}$; $F_{\text{sky}} = \frac{1+\cos\Sigma}{2}$, $h_{r,\text{sky}} = \varepsilon\sigma F_{\text{sky}}\beta (T_{so}^4 - T_{\text{sky}}^4)/(T_{so}-T_{\text{sky}})$, $h_{r,\text{air}} = \varepsilon\sigma F_{\text{sky}}(1-\beta)\dots$, $h_{r,\text{gnd}} = \varepsilon\sigma\frac{1-\cos\Sigma}{2}\dots$ with $T_{\text{gnd}} = T_{\text{db}}$ for exterior air-facing surfaces. | **Low** (pure scalar math per outdoor surface) | **Medium** — missing the $\beta = \sqrt{(1+\cos\Sigma)/2}$ split between $T_{\text{sky}}$ and $T_{\text{air}}$ causes ~0.5–1.5% roof/wall error. |
| 4 | **Outside surface heat balance & iteration** | `HeatBalanceSurfaceManager.cc` :: `CalcHeatBalanceOutsideSurf` | For `Outdoors` opaque surfaces (`Material:NoMass`, $Y_0=X_0=Z_0=1/R$): $T_{so} = \frac{q''_{\text{sol,abs}} + h_{c,o} T_{\text{db}} + h_{r,\text{sky}} T_{\text{sky}} + h_{r,\text{air}} T_{\text{db}} + h_{r,\text{gnd}} T_{\text{gnd}} + Y_0 T_{si}}{h_{c,o} + h_{r,\text{sky}} + h_{r,\text{air}} + h_{r,\text{gnd}} + X_0}$. Note: E+ uses lagged $T_{si}$ from previous timestep/iteration and updates $h_{c,o}, h_r$ across outer/inner sweeps. | **Low** (closed-form algebraic update per iteration; small loop) | **Medium** — coupling order between outside face, inside face, and `NoMass` $T_{si}$ lag. |
| 5 | **OtherSideCoefficients (OSC) with $C_1 = 0$** | `HeatBalanceSurfaceManager.cc` :: `CalcHeatBalanceOutsideSurf` *(OSC helper symbol `UNVERIFIED` in v23.1.0)* | When `Combined Convective/Radiative Film Coefficient` $C_1 \le 0$, E+ sets outside face temperature directly: $T_{so} = C_2 C_3 + C_4 T_{\text{db}} + C_5 T_{\text{gnd}} + C_6 W_{\text{spd}} T_{\text{db}} + C_7 T_z + C_8 T_{\text{past}}$ (for Workload A: $T_{so} = b \cdot T_{\text{db}} + (1-b) \cdot T_z$). Bypasses exterior convection/radiation completely! | **Trivial** (2 FMA ops; branchless via `is_osc` mask or separate surface group) | **Medium** — confirm whether $T_z$ in OSC uses previous-timestep $T_z^{t-\Delta t}$ or current predicted $T_z^t$ in E+ v23.1.0. |
| 6 | **Exterior convection (DOE-2) & wind height correction** | `ConvectionCoefficients.cc` :: *(exact v23.1.0 DOE-2 & wind-profile helper names `UNVERIFIED`)* | Local wind speed at surface centroid height $z$: $V_z = V_{\text{met}} (\delta_{\text{met}}/z_{\text{met}})^{\alpha_{\text{met}}} (z/\delta)^\alpha$. DOE-2 combines natural $h_n$ (TARP) with MoWiTT smooth forced $h_{c,\text{glass}} = \sqrt{h_n^2 + (a V_z^b)^2}$ (windward vs. leeward by $|\gamma_{\text{surf}} - \gamma_{\text{wind}}| \le 100^\circ$), scaled by roughness multiplier $R_f$: $h_{c,o} = h_n + R_f (h_{c,\text{glass}} - h_n)$. | **Low–Medium** (windward/leeward branch + roughness table; 1 `pow` op) | **Medium** — forgetting terrain wind-height scaling ($z$ vs. 10 m met tower) or roughness multiplier $R_f$ shifts wall/roof losses by 1–2%. |
| 7 | **Interior convection (TARP)** | `ConvectionCoefficients.cc` :: *(exact v23.1.0 TARP helper name `UNVERIFIED`)* | Natural convection based on tilt $\Sigma$ and sign of $\Delta T = T_{si} - T_z$: vertical ($h_c = 1.31 |\Delta T|^{1/3}$); horizontal enhanced (warm floor / cool ceiling: $h_c = 9.482 |\Delta T|^{1/3} / (7.283 - |\cos\Sigma|)$); horizontal reduced (cool floor / warm ceiling: $h_c = 1.810 |\Delta T|^{1/3} / (1.382 + |\cos\Sigma|)$); clamped to minimum $h_{c,\min}$. | **Low** (branchless `select` on $\Delta T \cdot \cos\Sigma$; fast `cbrt`) | **Low–Medium** — floor/ceiling sign-flip branch and minimum $h_c$ floor; small discontinuity near $\Delta T = 0$. |
| 8 | **Interior longwave exchange (ScriptF)** | `HeatBalanceIntRadExchange.cc` :: `InitInteriorRadExchange`, `FixViewFactors`, `CalcInteriorRadExchange` | Precompute area-weighted approximate view factors $F_{ij} \approx A_j / (\sum_k A_k - A_i)$ (corrected by `FixViewFactors`), invert $(I - R F)$ to obtain Hottel's $\mathcal{F}_{ij}$ (`ScriptF`) matrix once on CPU (in FP64). Per iteration: $q''_{\text{LW},i} = \sum_j \sigma \mathcal{F}_{ij} (T_{si,j}^4 - T_{si,i}^4)$ (linearized in E+ as $h_{r,ij}(T_{si,j} - T_{si,i})$). | **Medium** ($S \times S$ dense matvec per iteration; $S \le 12 \Rightarrow 144$ FMAs; watch L1/register footprint of $\mathcal{F}_{ij}$) | **Medium** — `InternalMass` inclusion in ScriptF enclosure area and `FixViewFactors` adjustments can shift MRT and heating by 0.5–1.5%. |
| 9 | **Simple Glazing conversion & Window Heat Balance** | `WindowManager.cc` :: `InitWindowOpticalCalculations`, `CalcWindowHeatBalance` *(SimpleGlazing conversion helper name `UNVERIFIED` in v23.1.0)* | **Precompute on CPU (Arasteh et al. 2009):** Strip NFRC winter films ($R_{i,w}, R_{o,w}$) from $U_{\text{sys}}$ to get $R_{l,w}$; fictitious thickness $d = 0.002\text{ m}$ if $1/R_{l,w} > 7$ else $0.05914 - 0.00714/R_{l,w}$; $\lambda_{\text{eff}} = d/R_{l,w}$; regression split of SHGC into normal $T_{\text{sol}}, R_{\text{sol}}$ + angular curves.<br>**Per step on GPU:** Transmitted beam/diffuse solar + absorbed solar on equivalent single glass layer; 2-node steady-state heat balance ($T_{wo}, T_{wi}$) coupled to DOE-2 outside, sky/ground LW, TARP inside, and ScriptF LW. | **Medium** (precompute angular tables on CPU; 2×2 linear solve per window inside HB loop on GPU) | **HIGH** — SimpleGlazing's piecewise Arasteh regressions (U-factor/SHGC regime splits) and inward-flowing absorbed solar fraction + interior solar distribution (`FullExterior`: beam to floor, diffuse area-weighted by $1-\rho$) are a top error source (1–5% if approximated). |
| 10 | **CTF generation & history (`InternalMass`)** | `Construction.cc` :: `calculateTransferFunction`; `HeatBalanceManager.cc` :: `InitConductionTransferFunctions`; `HeatBalanceSurfaceManager.cc` :: `UpdateThermalHistories` | **Precompute on CPU (FP64):** State-space discretization of 0.10 m massive layer → exact CTF coefficients $X_k, Y_k, Z_k$ ($k=0..N$) and $F_k$ ($k=1..M$). For `Material:NoMass`, $X_0=Y_0=Z_0=1/R$, $N=M=0$.<br>**Per step on GPU:** For symmetric `InternalMass` ($T_{so} = T_{si}$), $q''_{ki,t} = (Z_0 - Y_0)T_{si,t} + \sum_{k=1}^N (Z_k - Y_k)T_{si,t-k} + \sum_{k=1}^M F_k q''_{ki,t-k}$; shift ring buffer once per converged timestep. | **Low** (only 1 massive surface per building in Workload A; ring buffer of $M \le 10$ floats in registers) | **HIGH** — verify exact `InternalMass` symmetry/area convention (both faces exposed to zone vs. adiabatic midplane) and CTF initialization during warmup. |
| 11 | **Inside surface heat balance & convergence** | `HeatBalanceSurfaceManager.cc` :: `ManageSurfaceHeatBalance`, `InitSurfaceHeatBalance`, `CalcHeatBalanceInsideSurf` | Gauss-Seidel / Jacobi inner iteration solving $q''_{ki} + q''_{\text{conv}} + q''_{\text{LW}} + q''_{\text{SW}} = 0$ for all surfaces $i = 1..S$ until $\max_i |T_{si}^{(k)} - T_{si}^{(k-1)}| < 0.01^\circ\text{C}$ (max 20–30 iters, with under-relaxation if oscillating). Note: `CalcHeatBalanceOutsideSurf` and `CalcHeatBalanceInsideSurf` execute per timestep with `NoMass` surfaces coupling $T_{so}$ and $T_{si}$ tightly. | **Medium** (inner `while` loop causes SIMT divergence if iterations vary across lanes; mitigated by active mask & fixed-upper-bound check) | **Medium** — under-relaxation behavior on low-mass / `NoMass` surfaces and coupling between `T_so` and `T_si` inside the same step. |
| 12 | **Ventilation, internal gains, 3OBD zone air & IdealLoads** | `HeatBalanceAirManager.cc` *(helper `UNVERIFIED`)*; `InternalHeatGains.cc` :: `ManageInternalHeatGains`; `ZoneTempPredictorCorrector.cc` :: `ManageZoneAirUpdates`, `CalcZoneAirTempSetPoints`, `PredictSystemLoads`, `CorrectZoneAirTemp`; `PurchasedAirManager.cc` :: `SimPurchasedAir`, `CalcPurchAirLoads` | Ventilation mass flow $\dot{m}_v = \rho_a \cdot \text{ACH} \cdot V_z / 3600$ (note: check `ZoneVentilation:DesignFlowRate` constant/temp/wind coefficients; default $A=1, B=C=D=0$, $\rho_a$ evaluated at standard or outdoor/zone air). Internal gain $Q_{\text{int,conv}}$ from hourly `Schedule:File`.<br>**3OBD:** $C_z \frac{11 T_z^t - 18 T_z^{t-1} + 9 T_z^{t-2} - 2 T_z^{t-3}}{6\Delta t} = \sum h_{c,i} A_i (T_{si,i} - T_z^t) + \dot{m}_v c_p (T_{\text{db}} - T_z^t) + Q_{\text{int,conv}} + Q_{\text{sys}}$.<br>**Predictor-Corrector (IdealLoads, heating-only, unlimited capacity):** Compute floating $T_{z,\text{float}}$ with $Q_{\text{sys}}=0$; if $T_{z,\text{float}} < T_{\text{set}}$, set $T_z^t = T_{\text{set}}$ and compute exact $Q_{\text{heat}} = \left(\frac{11 C_z}{6\Delta t} + \sum h_{c,i}A_i + \dot{m}_v c_p\right)(T_{\text{set}} - T_{z,\text{float}})$; else $Q_{\text{heat}} = 0, T_z^t = T_{z,\text{float}}$. | **Low** (pure scalar arithmetic; closed-form because IdealLoads has unlimited heating capacity!) | **Medium** — psychrometric air density $\rho_a$ & specific heat $c_p$ (moist air `PsyCpAirFnW` vs. constant 1005 J/kg·K) and `ZoneCapacitanceMultiplier` (default 1.0) can shift loads by 0.2–0.8%. Also note E+ updates zone air temp *after* inside surface HB, then may re-run if load/temp changes. |
| 13 | **Warm-up convergence** | `HeatBalanceManager.cc` :: `CheckWarmupConvergence` | Repeat Day 1 (Jan 1) weather up to `MaxWarmupDays` (default 25, min 6 in E+ unless overridden) until both $\max_t |T_{z,d} - T_{z,d-1}| \le 0.04^\circ\text{C}$ and relative peak load change $\le 0.04$ (or 0.004 W/m² floor). | **Medium** (different buildings converge on different days → warp idle lanes if exiting early) | **Low** (for 0.10 m `InternalMass`, warmup converges in ~4–8 days; running a fixed warmup count of e.g. 10–12 days across the batch matches converged state within <0.01% annual heating!). |
| 14 | **Output aggregation** | `OutputProcessor.cc` :: `UpdateDataandReport` | Sum/average 12 sub-hourly heating energy values $E_{\text{heat,hr}} = \sum_{m=1}^{12} Q_{\text{heat},m} \cdot \Delta t$ [J] (or average rate [W]) per hour for 8,760 hours. | **Trivial** (register accumulator flushed once every 12 steps) | **Low** — watch E+ unit conventions (J vs. W) and `Schedule:File` hour indexing (1-based hour ending vs. 0-based). |

### Top Disagreement Traps (Prioritize During Verification)
1. **Window SimpleGlazing + Interior Solar Distribution:** Even without external shading objects, the two windows admit direct beam and Perez diffuse solar. EnergyPlus's Arasteh block-model optical regressions and `FullExterior` interior solar distribution (all transmitted beam solar hits the floor, reflected fraction diffuses area-weighted by absorptance across all interior surfaces including `InternalMass`) must match v23.1.0 closely—shortcuts here easily create 2–5% annual error.
2. **EPW Sub-Hourly Interpolation & Timestamp Alignment:** EnergyPlus defines EPW Hour $H$ (1..24) as the interval ending at $H$:00, and interpolates dry-bulb/wind linearly between previous and current hour while evaluating solar position at the midpoint of the sub-hourly step. A 30-minute phase error skews morning heating warm-up peaks.
3. **Moist-Air Properties ($\rho_a, c_p$) & Ventilation Density:** `ZoneVentilation:DesignFlowRate` converts volumetric ACH to mass flow using standard air density (`StdRhoAir` at site elevation) or outdoor/zone density depending on E+ convention, and $c_p(W)$ varies with humidity ratio (~1006–1020 J/kg·K). Hard-coding $\rho = 1.2$, $c_p = 1005$ introduces ~0.5–1.5% bias at non-sea-level sites.
4. **Predictor–Corrector Coupling Order:** In E+, `CalcHeatBalanceInsideSurf` uses the *previous* timestep's (or predicted) $T_z$, then `PredictSystemLoads` + `SimPurchasedAir` + `CorrectZoneAirTemp` solves $T_z^t$. Reversing this order (solving $T_{si}$ and $T_z$ simultaneously in one step) changes transient response during night setback or morning solar spikes.

---

## 3. GPU Mapping Strategy

### 3.1 Parallel Axis: Building-Level (1 Thread = 1 Building)
- **Why not parallelize over time?** Heat balance with CTF history and 3OBD air capacitance is strictly sequential in time ($t \to t+1$).
- **Why not parallelize over surfaces within a building for Workload A?** Workload A has only $S \approx 8\text{--}12$ surfaces per building—smaller than a single SIMD group (32 threads on NVIDIA warps and Apple Silicon SIMD groups). Assigning 1 thread per surface wastes 60–75% of SIMD lanes and forces barrier synchronization (`workgroupBarrier`) inside every Gauss-Seidel/Jacobi iteration.
- **Optimal mapping:** **1 GPU thread = 1 building** (batch axis $B \in [10^3, 10^5]$). At $B \ge 4{,}096$, both M2 Pro (19 GPU cores × ~1,024 resident threads ≈ 20k threads) and RTX 4090 (128 SMs × ~1,024–1,536 threads ≈ 130k–196k threads) reach high occupancy with zero inter-thread synchronization!
- *(For Workload B multi-zone buildings with $S = 100\text{--}500$ surfaces, switch to 1 workgroup = 1 building, parallelizing over surfaces in shared memory.)*

### 3.2 Fused Megakernel vs. Batched Tensor Ops with Python Time Loop
- **Batched tensor ops (PyTorch/NumPy-style Python `for t in range(105120):`) FAIL catastrophically here.** Each timestep has ~15–25 distinct small operations (TARP, DOE-2, ScriptF, window solve, CTF, 3OBD, IdealLoads). Over 105,120 steps, that is **~2 million kernel launches**. At 10–30 µs/launch (MPS/CUDA + Python overhead), launch latency alone burns **20–60 seconds** regardless of GPU speed, and every op round-trips intermediate tensors (`T_si`, `h_c`, `q_lw`) to DRAM (~1.5–3 KB/building-step).
- **Fused chunked megakernel (Recommended):** Put the sub-hourly time loop **inside a single GPU compute shader**, processing **1 day (288 timesteps)** or **5 days (1,440 timesteps)** per dispatch:
  - Total launches per year: **365 (daily)** or **73 (5-day)** → **<5–10 ms total launch overhead**!
  - All dynamic state (`T_si`, `T_so`, `T_z_hist`, `CTF_hist`) stays in registers/L1 cache across all 288–1,440 steps.
  - Stays safely below the **2-second Windows WDDM TDR** and **macOS GPU command-buffer watchdog** timeouts (a 5-day chunk for 100k buildings takes ~50–200 ms).

### 3.3 Inner Iteration Loops & SIMT Divergence
- Inside each timestep, `CalcHeatBalanceInsideSurf` iterates until $\max_i |T_{si}^{(k)} - T_{si}^{(k-1)}| < 0.01^\circ\text{C}$ (typically 2–4 iterations at `Timestep 12`; cap at `MAX_ITER = 15`).
- On SIMT hardware (32-lane warps / Apple SIMD groups), all 32 buildings in a warp execute in lockstep until the *slowest* building in that warp converges.
- **Mitigation:**
  1. Sort/group buildings in the batch by **climate file + surface-count bucket + similar thermal mass/U-value**, so neighboring lanes in a warp converge on the same iteration.
  2. Guard updates with a boolean `converged` flag (or exit `break` when all lanes finish—GPU compilers automatically mask converged lanes and exit the loop once the warp mask is zero). Because `Timestep 12` steps are only 5 minutes apart, convergence spreads are tiny (typically 2 vs. 3 iters → <15% divergence overhead).

### 3.4 Warm-Up Loops of Different Length
- In CPU E+, each building exits warmup on a different day (typically days 6–12 for Workload A's 0.10 m `InternalMass`).
- On GPU, per-building variable warmup lengths cause massive warp under-utilization if buildings wait for one slow outlier.
- **Recommended hybrid approach:**
  1. Run a **fixed warmup pass** of $D_{\text{fixed}} = 10$ repeated Day-1 chunks (only ~2.7% of an annual run!) with zero divergence, recording max day-over-day $|\Delta T_z|$ and $|\Delta Q_{\text{heat}}|$ on day 10 into a `warmup_converged[B]` flag array.
  2. If *any* buildings fail convergence after Day 10 (rare for Workload A; <1% of cases), compact their indices into a small `unconverged_ids` list on the host and run additional Day-1 chunks **only** for those unconverged buildings (up to `MaxWarmupDays = 25`). Zero wasted compute on the 99% that converged, and 100% faithful to E+'s convergence criterion!

### 3.5 Padding & Bucketing of Different Surface Counts
- TABULA Workload A models have a narrow surface count distribution (typically $S \in [7, 14]$: 4 walls + roof + floor + 2 windows + 1 InternalMass = 9; sometimes split walls/roofs up to 14–16).
- **Bucket by padded surface count** $S_{\text{pad}} \in \{10, 12, 16\}$ (or a single fixed `S_MAX = 12` if >95% of cases have $\le 12$, spilling larger cases into a `S_MAX = 20` bucket).
- Padded dummy surfaces have `area = 0.0`, `is_active = 0`, and zero rows/columns in `ScriptF`. Because `S_MAX` is a compile-time specialization constant (`override S_MAX: u32` in WGSL / template parameter in CUDA/MSL), inner loops unroll cleanly and registers stay predictable.

### 3.6 Memory Layout: Structure-of-Arrays (SoA)
- **Always use SoA** indexed as `[field][surface_idx * B + b]` (stride = batch size `B`, padded to a multiple of 32/64) rather than AoS (`Building[b].surf[s].field`).
- Why: When 32 consecutive threads `b, b+1, ..., b+31` read `surf_R[s * B + b]`, the memory transaction coalesces into a **single 128-byte cache line** (100% bus utilization). With AoS, threads stride by ~1.5 KB apart, wasting ~90% of DRAM bandwidth.
- For `ScriptF[i, j]` ($S \times S$ per building), store as `[i * S + j][B]` (or symmetric upper triangle `[tri_idx][B]`, cutting storage by ~45% from $S^2$ to $S(S-1)/2$ since $\mathcal{F}_{ii} = 0$ and $A_i \mathcal{F}_{ij} = A_j \mathcal{F}_{ji}$!).

### 3.7 Float32 vs. Float64 Precision Analysis & Mitigations
Apple M2 Pro GPUs have **no hardware FP64** (`float64` is unsupported in Metal/MSL and WebGPU/WGSL). Here is where FP32 ($\epsilon \approx 1.19 \times 10^{-7}$, ~7.2 decimal digits) introduces errors and how to eliminate them so FP32 matches FP64 E+ to **<0.05%**:

| Calculation | FP32 Failure Mode | Exact Mitigation (Required for M2 Pro & WGSL) |
| :--- | :--- | :--- |
| **CTF coefficient generation** | Catastrophic cancellation in matrix exponential / Faddeev-Leverrier polynomial. | **Always run on CPU in FP64** during preprocessing (takes <1 ms per unique construction). Never generate CTFs in FP32. |
| **Longwave $T_i^4 - T_j^4$** | In Kelvin ($T \approx 300\text{ K}$), $T^4 \approx 8.1 \times 10^9$; subtracting close surfaces loses ~4 digits. | **Factor algebraically:** $(T_i - T_j)(T_i + T_j)(T_i^2 + T_j^2)$, computing $(T_i - T_j)$ directly in Celsius (no $+273.15$ cancellation!). |
| **CTF steady-state flux balance** | Rounding $X_k, Y_k, Z_k$ to FP32 breaks $\sum X_k = \sum Y_k = \sum Z_k$, causing a constant DC energy leak! | 1. **Shift all surface/zone temperatures by $T_{\text{ref}} = 20^\circ\text{C}$** ($\tilde{T} = T - 20$) inside CTF convolution.<br>2. **FP32 sum-preserving rounding:** Adjust $X_0, Y_0, Z_0$ in FP64 before casting so $\sum \text{fl}_{32}(Z_k) = \sum \text{fl}_{32}(Y_k) = \sum \text{fl}_{32}(X_k)$ exactly.<br>3. For stiff Workload B walls ($1 - \sum F_k < 10^{-3}$), use **Dekker/TwoSum double-float (`vec2<f32>`, 48-bit mantissa)** for the CTF dot-product accumulator. |
| **3OBD zone air derivative** | $11 T_z^t - 18 T_z^{t-1} + 9 T_z^{t-2} - 2 T_z^{t-3}$ cancels near constant setpoint. | Rewrite in **difference form:** $11(T_z^t - T_z^{t-1}) - 7(T_z^{t-1} - T_z^{t-2}) + 2(T_z^{t-2} - T_z^{t-3})$. |
| **Annual energy accumulation** | Summing 105,120 positive steps into one FP32 scalar loses ~4–5 bits of precision. | Accumulate **hourly** (only 12 steps/hr) on GPU in FP32; sum 8,760 hourly values to annual on CPU in **FP64** (or use Kahan summation if accumulating annually on GPU). |

---

## 4. Framework Selection: "macOS First, Then Windows CUDA"

### Table 3: GPU Compute Frameworks (Verified 2026-11-22)

| Framework | Latest Verified Version & Date | macOS GPU (M2 Pro) | Windows CUDA Native | Float64 (GPU) | Fused Stateful Megakernel (288-step loop) | Maintenance / Maturity | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`wgpu-py` (WebGPU / WGSL)** | **`v0.33.0`** (2026-11-06) | **Yes** (native Metal via `wgpu-native`) | **Yes** (native Vulkan / DX12 on NVIDIA; no CUDA SDK needed) | **No** (WGSL is FP32; `shader-f64` non-portable & absent on Metal) | **Excellent** — full `@compute` shaders with loops, branches, local arrays, specialization constants | **Active** (`pygfx/wgpu-py` + Mozilla/gfx-rs `wgpu`); MIT/BSD-2-Clause | **RECOMMENDED (Primary)** |
| **Macro-shared C-header + `pyobjc-Metal` / `cupy.RawKernel`** | Metal (macOS SDK) + CuPy (CUDA 12/13) | **Yes** (100% native MSL) | **Yes** (100% native CUDA C++) | **Windows CUDA: Yes**; macOS Metal: No | **Best possible** — full control over registers, shared memory, warp ops, runtime JIT compilation | **Rock-solid** (vendor first-party compilers, zero middleware abandonment risk) | **RECOMMENDED (Fallback / Phase-2 FP64 upgrade)** |
| **PyTorch** | **`v2.15.0`** (2026-10-28) | **Yes** (MPS backend) | **Yes** (official CUDA wheels) | **Windows CUDA: Yes**; MPS: **No** (`TypeError`) | **Poor** — eager Python time loop suffers ~2M launches; `torch.compile` lacks first-party Windows Triton (relies on community `triton-windows`) and has limited MPS dynamic-loop fusion | **Very Active** (BSD-3-Clause) | **Reject** as core kernel; use only if wrapping ML surrogates |
| **JAX** | `0.5.x+` rolling (2026) | **Broken / Stagnant** (`jax-metal` unmaintained since late 2024; `metaljax` is early community beta) | **No** (experimental CPU-only Windows wheels; CUDA requires **WSL2**) | CUDA/CPU: Yes; Metal: No | **Good on Linux CUDA** (`jax.lax.scan`), fails platform requirements on both macOS GPU & native Windows | **Very Active** (Apache-2.0) on Linux/TPU, poor macOS/Windows GPU story | **Reject** (violates both macOS GPU and native Windows constraints) |
| **MLX** | **`v0.32.4`** (2026-10-14) | **Excellent** (Apple first-party, unified memory, `mx.fast.metal_kernel`) | **No** (Apple Silicon only) | No (Metal limit) | **Excellent on macOS** (`metal_kernel`), zero Windows portability | **Very Active** (MIT) | **Reject** (single-vendor lock-in) |
| **Taichi** | **`v1.7.4`** (2025-07-31) | **Yes** (Metal backend, lags CUDA; occasional macOS 15+ quirks) | **Yes** (Tier-1 CUDA backend) | CUDA/CPU: Yes; Metal: No | **Very Good** (`@ti.kernel` fuses loops cleanly + SoA SNode fields) | **Maintenance mode** (core team shifted focus; infrequent releases since 2025) | **Reject as primary** (maintenance risk); acceptable for quick throwaway prototype |
| **NVIDIA Warp** | **`v1.19.0`** (Nov 2026) | **No** (official PyPI macOS wheels are **CPU-only**; `innate-inc/warp-metal` is unofficial fork) | **Yes** (Tier-1 CUDA + built-in BVH ray tracing) | CUDA/CPU: Yes | **Excellent** on CUDA/CPU | **Very Active** (Apache-2.0, NVIDIA-backed) | **Reject** for macOS-first GPU; strong candidate *only* if macOS GPU is dropped |
| **SYCL (AdaptiveCpp) / Kokkos** | Kokkos **`v5.2.1`** (2026-08-18); AdaptiveCpp (2026) | **Experimental** (Kokkos has no native Metal; relies on AdaptiveCpp experimental `-DWITH_METAL_BACKEND=ON` + `metal-cpp`) | **Yes** (AdaptiveCpp CUDA/PCUDA + Kokkos CUDA) | CUDA: Yes; Metal: No | **Excellent** in C++, heavy build toolchain & awkward Python bindings | **Active** in HPC C++ (BSD/Apache), immature on macOS Metal | **Reject** (excessive build complexity + experimental Metal) |

### Framework Recommendation
1. **Primary: `wgpu-py` (WebGPU / WGSL).**
   - Single WGSL compute kernel runs identically on **Apple M2 Pro (Metal)** and **Windows NVIDIA GPUs (Vulkan/DX12)** via `pip install wgpu`—zero C++ compiler toolchain, zero Xcode/MSVC/CUDA version drift.
   - Supports full fused 288-step/1,440-step megakernels and SoA buffers.
   - Bonus for **Workload B**: `wgpu-py` natively exposes hardware **graphics rasterization pipelines** (`RenderPipeline`), allowing a `PixelCounting`-style orthographic solar shading pre-pass on the exact same GPU context.
   - Because FP32 mitigations (factored $T^4$, shifted-Celsius CTF, difference-form 3OBD, CPU FP64 CTF precompute) are already mandatory for Apple M2 Pro, WGSL's FP32-only constraint adds zero extra algorithmic burden.
2. **Fallback: Macro-Shared C-Family Kernel (`hb_core.h`) + `pyobjc-framework-Metal` (macOS) + `cupy.RawKernel` (Windows CUDA).**
   - Trigger this fallback if (a) Workload B requires **native FP64** on Windows CUDA for ultra-thick multi-layer CTFs where double-float in WGSL becomes awkward, or (b) profiling shows WGSL→SPIR-V/DXIL loses >30% throughput vs. native CUDA on NVIDIA.
   - Both Apple Metal (`newLibraryWithSource`) and CuPy (`RawKernel`) JIT-compile source strings directly from Python—keeping ~90% of the physics code in one shared `.h` file with ~80 lines of backend macros (`#ifdef __METAL_VERSION__` vs. `#ifdef __CUDACC__`) and zero CMake build overhead.

---

## 5. Prior Art

### Table 4: Prior Art & Reusable Components (Checked 2026-11-22)

| Project | URL | Licence | Latest Release / Activity (Checked 2026-11-22) | Physics / Architecture | Reusable Parts (Apache-2.0 / MIT compatible?) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EnergyPlus** (reference implementation) | https://github.com/NREL/EnergyPlus | BSD-3-Clause-LBNL (permissive, verify specific notice) | Active (`v23.1.0` pinned by user) | Serial C++ full BEM; GPU `PixelCounting` shading (`SolarShading.cc`) | **Reference equations, constants, IDD schemas, unit-test cases.** Do not vendor C++; port specific equations cleanly. |
| **pyBuildingEnergy** (Eurac Research) | https://github.com/EURAC-EEBgroup/pyBuildingEnergy | BSD-3-Clause | Active commits on `master` (2025–2026, ISO 52016-3 work) | Python EN ISO 52016-1 & ISO 52010 hourly thermal solver + ASHRAE 140-2023 harness | **Reusable (BSD-3):** ASHRAE 140 / BESTEST automated test harness structure & EPW/solar helper patterns. *(Physics is ISO 52016 RC, not E+ CTF/TARP/ScriptF.)* |
| **OpenSimula** | https://github.com/jfCoronel/OpenSimula | MIT | Active commits (2025–2026) | Component-based Python BEM validated against ASHRAE 140-2023 | **Reusable (MIT):** Pure-Python heat-balance / BESTEST validation patterns & component schemas for CPU reference testing. |
| **OpenBES-py** | https://github.com/openBES-ecosystem/OpenBES-py | `UNVERIFIED` (check repo LICENSE before vendoring) | Active PyPI/GitHub (`UNVERIFIED` exact date) | Modular Python BEM with optional Numba JIT & standard test suites | **Reference only** until licence verified; useful pattern for vectorized Python heat-balance testing. |
| **City Energy Analyst (CEA)** | https://github.com/architecture-building-systems/CityEnergyAnalyst | MIT | Active: `v4.0.0-beta.9` (Oct 2026) | Python UBEM using ISO 13790 5R1C thermal demand + urban solar/network tools | **Reusable (MIT):** Urban archetype/schedule I/O & solar workflow utilities. *(5R1C physics is too coarse for ≤0.5% E+ equivalence.)* |
| **CitySim-Solver** (EPFL / kaemco) | https://github.com/kaemco/CitySim-Solver | BSD-3-Clause | Active `main` commits (`UNVERIFIED` exact latest date) | C++ urban BEM using resistor-capacitor (RC) walls + shortwave/longwave urban radiation | **Reference (BSD-3):** Urban canyon radiation / shading concepts for Workload B. *(RC model, not E+ CTF.)* |
| **SimStadt** (HFT Stuttgart) | https://www.hft-stuttgart.de / open-source repos (`UNVERIFIED` canonical GitHub URL) | MIT | Active (`UNVERIFIED` exact commit date) | Java CityGML UBEM (monthly DIN V 18599 / ISO 13790 + optional EnergyPlus export) | Minimal code reuse (Java / monthly balance); workflow pattern for CityGML→E+ only. |
| **TEASER** (RWTH Aachen) | https://github.com/RWTH-EBC/TEASER | MIT | Active (`UNVERIFIED` exact commit date) | Python archetype-to-reduced-order Modelica (2R1C–4R2C) generator | **Reusable (MIT):** Archetype parameter enrichment logic; not a heat-balance solver. |
| **AixLib** (RWTH Aachen) | https://github.com/RWTH-EBC/AixLib | BSD-3-Clause | Active (`UNVERIFIED` exact commit date) | Modelica building/HVAC component library | Not directly reusable for GPU kernels (Modelica DAE equations). |
| **Modelica Buildings Library (`ThermalZones.EnergyPlus` / Spawn)** | https://github.com/lbl-srg/modelica-buildings | BSD-3-Clause | **`v14.0.0`** (2026-10-05) | Modelica HVAC + co-simulation coupling to native CPU EnergyPlus envelope (Spawn) | Not reusable for GPU speedup (still executes serial CPU E+ for envelope). |
| **GPU-accelerated RC / JAX thermal papers & prototypes** | Various arXiv / IBPSA papers (no widely adopted open-source GPU E+ CTF port found as of 2026-11-22) | Varies | 2023–2026 research | Batched 4R1C/7R2C models in CUDA/JAX reporting 10–100×+ speedups and $10^4\text{--}10^6$ building-hours/s | Confirms **no off-the-shelf Apache/MIT GPU port of EnergyPlus CTF/TARP/ScriptF exists**—building (c) fills a real gap. *(Exact third-party benchmark numbers vary by RC order and hardware; not directly comparable to full E+ CTF.)* |

---

## 6. Reference Design (Workload A GPU Engine)

### 6.1 Data Structures & Tensor Shapes (SoA Layout)
Let:
- $B$ = number of buildings in batch (padded to multiple of 64 for coalescing; e.g., $B = 16{,}384$).
- $S$ = padded surface count per building (compile-time specialization constant `S_MAX`, e.g., $S = 12$).
- $W$ = max windows per building (`W_MAX = 2` for Workload A; each window is also an entry in `0..S-1` for interior ScriptF/TARP).
- $M$ = max CTF history length for `InternalMass` (`M_MAX = 10`).
- $D = 288$ timesteps per day (`Timestep 12`), $H = 24$ hours/day.

All arrays are `float32` (unless noted `uint32`), stored in **Structure-of-Arrays (SoA)** with the **batch index `b` as the fastest-varying (innermost) dimension**:

```text
# 1. Shared Read-Only Weather Buffer (per EPW climate, precomputed on CPU in FP64 -> FP32)
#    Shape: [N_STEPS_CHUNK, 12]  (for 1-day chunk: [288, 12] = 13.8 KB -> fits in L1/constant cache!)
weather_chunk[t]:
  T_db, T_sky, W_spd, W_dir_rad, P_atm, W_hum_ratio,
  DNI, DHI, GHI, sun_x, sun_y, sun_z, perez_F1, perez_F2, ...  # pad to 16 floats [288, 16] = 18.4 KB

# 2. Static Building / Zone Parameters (read once per day chunk)
#    Shape: [B] each
zone_vol[B]           # Zone air volume [m^3]
zone_C_air[B]         # Effective air capacitance rho * cp * V * mult [J/K]
zone_m_vent_cp[B]     # Constant ventilation m_dot * cp [W/K] (or per-step if rho varies)
zone_T_set[B]         # Constant heating setpoint shifted by T_ref=20 [degC]
zone_n_surf[B]        # uint32 actual active surface count <= S
zone_im_idx[B]        # uint32 surface index of InternalMass in 0..S-1
zone_floor_idx[B]     # uint32 surface index of floor (beam solar target under FullExterior)

# 3. Static Surface Parameters (SoA: stride B along innermost axis)
#    Shape: [S, B] each  (accessed as arr[s * B + b])
surf_area[S, B]       # Exposed area [m^2] (0.0 for padded dummy surfaces)
surf_nx[S, B], surf_ny[S, B], surf_nz[S, B]  # Outward unit normal (nz = cos(tilt))
surf_z_cent[S, B]     # Centroid height above ground [m] (for DOE-2 wind profile)
surf_R_inv[S, B]      # 1 / R_nomass [W/m^2-K] (for Material:NoMass opaque surfaces)
surf_eps_in[S, B], surf_eps_out[S, B]        # Thermal emittances
surf_abs_sol_out[S, B], surf_abs_sol_in[S, B]# Solar absorptances
surf_rough_mult[S, B] # DOE-2 exterior roughness multiplier R_f
surf_btype[S, B]      # uint32: 0=PAD, 1=OUTDOORS_OPAQUE, 2=OSC, 3=WINDOW, 4=INTERNAL_MASS
surf_osc_b[S, B]      # OSC outdoor weight b (T_so = b*T_db + (1-b)*T_z; 0 if non-OSC)

# 4. Precomputed ScriptF Symmetric Matrix (CPU FP64 -> FP32)
#    Shape: [S*(S-1)/2, B]  (for S=12: [66, B] = 264 B/building!)
#    Stores sigma * ScriptF_ij / A_i? Better: store symmetric G_ij = sigma * A_i * ScriptF_ij = sigma * A_j * ScriptF_ji
#    so one entry serves both i->j and j->i, dividing by A_i at use!
scriptF_G[66, B]

# 5. Precomputed InternalMass CTF Coefficients (CPU FP64 -> FP32, sum-normalized)
#    Shape: [M, B] each  (M = 10)
ctf_ZY_diff[M, B]     # (Z_k - Y_k) for symmetric InternalMass (T_so == T_si)
ctf_F[M, B]           # Flux history coefficients F_1..F_M (F_0 unused)
ctf_len[B]            # uint32 active CTF history length <= M

# 6. Precomputed SimpleGlazing Parameters (CPU FP64 Arasteh conversion -> FP32)
#    Shape: [W_MAX, B]  (W_MAX = 2)
win_surf_idx[W_MAX, B]   # uint32 index into 0..S-1
win_U_glass[W_MAX, B]    # Equivalent layer conductance lambda_eff / d [W/m^2-K]
win_Tsol_0[W_MAX, B]     # Normal solar transmittance
win_Abs_0[W_MAX, B]      # Normal solar absorptance (front)
win_Tsol_diff[W_MAX, B]  # Hemispherical diffuse transmittance
win_Abs_diff[W_MAX, B]   # Hemispherical diffuse absorptance
win_ang_coeffs[W_MAX, 4, B] # Polynomial / LUT coefficients for angular T_sol(cos theta) & Abs(cos theta)

# 7. Per-Building Dynamic State (persisted between day chunks; held in registers/local memory inside chunk)
#    Shape: [S, B] or [3, B] or [M, B]
state_T_si[S, B]         # Inside surface temp shifted (T - 20) [degC]
state_T_so[S, B]         # Outside surface temp shifted (T - 20) [degC]
state_T_z_hist[3, B]     # [T_z^{t-1}, T_z^{t-2}, T_z^{t-3}] shifted [degC]
state_im_T_hist[M, B]    # InternalMass past surface temps (shifted)
state_im_q_hist[M, B]    # InternalMass past conduction fluxes [W/m^2]

# 8. Per-Building Schedule & Output Buffers (streamed per chunk, e.g., 5 days = 120 hours)
#    Shape: [H_CHUNK, B]
sched_Q_int_conv[H_CHUNK, B]   # Convective internal gains [W]
out_E_heat_hr[H_CHUNK, B]      # Output hourly ideal-loads heating energy [J]
```

### 6.2 Kernel Pseudo-Code (WGSL / CUDA-Style)

#### A. Single Timestep (`step_building`) — Executed Inside Registers/Local Memory
```wgsl
// Runs for one building `b` at timestep `t` inside the chunk loop.
// All temperatures are shifted: t_shifted = T_celsius - 20.0 (T_K = t_shifted + 293.15).
const T_REF_K: f32 = 293.15;
const T_REF_C: f32 = 20.0;

fn lw_factor(ti_s: f32, tj_s: f32) -> f32 {
    // Exact factored (Ti^4 - Tj^4) / (Ti - Tj) = (Ti + Tj)*(Ti^2 + Tj^2)
    // Avoids FP32 T^4 catastrophic cancellation!
    let Ti = ti_s + T_REF_K;
    let Tj = tj_s + T_REF_K;
    return (Ti + Tj) * (Ti * Ti + Tj * Tj);
}

fn step_building(b: u32, w: WeatherStep, Q_int_conv: f32,
                 /* inout local arrays */ T_si: ptr<function, array<f32, S_MAX>>,
                 T_so: ptr<function, array<f32, S_MAX>>,
                 T_z_hist: ptr<function, array<f32, 3>>,
                 im_T_hist: ptr<function, array<f32, M_MAX>>,
                 im_q_hist: ptr<function, array<f32, M_MAX>>) -> f32 {

    let T_z_prev = (*T_z_hist)[0];
    let T_db_s   = w.T_db - T_REF_C;
    let T_sky_s  = w.T_sky - T_REF_C;

    // 1. Exterior solar & transmitted window solar (once per timestep)
    var q_sol_out: array<f32, S_MAX>;
    var Q_beam_in: f32 = 0.0;
    var Q_diff_in: f32 = 0.0;
    var q_win_abs: array<f32, W_MAX>;

    for (var s: u32 = 0u; s < S_MAX; s++) {
        let bt = surf_btype(s, b);
        if (bt == BTYPE_OUTDOORS_OPAQUE || bt == BTYPE_WINDOW) {
            let cos_i = max(0.0, surf_nx(s,b)*w.sun_x + surf_ny(s,b)*w.sun_y + surf_nz(s,b)*w.sun_z);
            let I_beam = w.DNI * cos_i;
            let I_diff = perez_diffuse(w, surf_nz(s,b), cos_i) + ground_refl(w, surf_nz(s,b));
            if (bt == BTYPE_OUTDOORS_OPAQUE) {
                q_sol_out[s] = surf_abs_sol_out(s, b) * (I_beam + I_diff);
            } else {
                // Window SimpleGlazing angular optical lookup
                let wi = win_idx_from_surf(s, b);
                let T_b = eval_win_Tsol(wi, b, cos_i);
                let A_b = eval_win_Abs(wi, b, cos_i);
                let area = surf_area(s, b);
                Q_beam_in += area * I_beam * T_b;
                Q_diff_in += area * I_diff * win_Tsol_diff(wi, b);
                q_win_abs[wi] = I_beam * A_b + I_diff * win_Abs_diff(wi, b);
            }
        }
    }

    // 2. Interior solar distribution (E+ FullExterior: beam -> floor, reflected + diffuse -> area*abs weighted)
    var q_sw_in: array<f32, S_MAX>;
    distribute_interior_solar(b, Q_beam_in, Q_diff_in, &q_sw_in);

    // 3. CTF history term for the single massive InternalMass surface (constant across inner iters)
    let im_s = zone_im_idx[b];
    var q_ctf_hist: f32 = 0.0;
    let m_len = ctf_len[b];
    for (var k: u32 = 1u; k < m_len; k++) {
        q_ctf_hist += ctf_ZY_diff(k, b) * (*im_T_hist)[k - 1u] + ctf_F(k, b) * (*im_q_hist)[k - 1u];
    }

    // 4. Outside surface heat balance (OSC direct; Outdoors opaque 2-pass update)
    for (var s: u32 = 0u; s < S_MAX; s++) {
        let bt = surf_btype(s, b);
        if (bt == BTYPE_OSC) {
            let ob = surf_osc_b(s, b);
            (*T_so)[s] = ob * T_db_s + (1.0 - ob) * T_z_prev;
        } else if (bt == BTYPE_OUTDOORS_OPAQUE) {
            // 2 fixed-point updates for nonlinear h_c,o (DOE-2) & h_r,sky/gnd
            let U_nm = surf_R_inv(s, b);
            for (var oi: u32 = 0u; oi < 2u; oi++) {
                let hc_o = calc_doe2_hc(s, b, (*T_so)[s], T_db_s, w.W_spd, w.W_dir);
                let hr   = calc_ext_lw_coeffs(s, b, (*T_so)[s], T_sky_s, T_db_s); // sky, air, gnd
                let num  = q_sol_out[s] + hc_o*T_db_s + hr.sky*T_sky_s + (hr.air + hr.gnd)*T_db_s + U_nm*(*T_si)[s];
                let den  = hc_o + hr.sky + hr.air + hr.gnd + U_nm;
                (*T_so)[s] = num / den;
            }
        }
    }

    // 5. Coupled Inside Surface + Window Heat Balance (Gauss-Seidel inner loop)
    var hc_in: array<f32, S_MAX>;
    var converged: bool = false;
    for (var iter: u32 = 0u; iter < 15u; iter++) {
        if (converged) { break; }
        var max_err: f32 = 0.0;

        for (var i: u32 = 0u; i < S_MAX; i++) {
            let bt = surf_btype(i, b);
            if (bt == BTYPE_PAD) { continue; }

            let Ti_old = (*T_si)[i];
            let hc = calc_tarp_hc(surf_nz(i, b), Ti_old - T_z_prev);
            hc_in[i] = hc;

            // Interior LW via symmetric ScriptF (linearized around Ti_old)
            var sum_hrT: f32 = 0.0;
            var sum_hr:  f32 = 0.0;
            let inv_Ai = 1.0 / surf_area(i, b);
            for (var j: u32 = 0u; j < S_MAX; j++) {
                if (j == i || surf_btype(j, b) == BTYPE_PAD) { continue; }
                let G_ij = read_scriptF_sym(i, j, b); // sigma * A_i * F_ij
                let hr_ij = G_ij * inv_Ai * lw_factor(Ti_old, (*T_si)[j]);
                sum_hrT += hr_ij * (*T_si)[j];
                sum_hr  += hr_ij;
            }

            var Ti_new: f32;
            if (bt == BTYPE_OUTDOORS_OPAQUE || bt == BTYPE_OSC) {
                let U_nm = surf_R_inv(i, b);
                Ti_new = (U_nm * (*T_so)[i] + hc * T_z_prev + sum_hrT + q_sw_in[i]) / (U_nm + hc + sum_hr);
            } else if (bt == BTYPE_INTERNAL_MASS) {
                let ZY0 = ctf_ZY_diff(0u, b);
                Ti_new = (-q_ctf_hist + hc * T_z_prev + sum_hrT + q_sw_in[i]) / (ZY0 + hc + sum_hr);
            } else { // BTYPE_WINDOW: 2-node equivalent glazing balance (T_so[i], T_si[i])
                let wi = win_idx_from_surf(i, b);
                let res = solve_window_2node(i, wi, b, (*T_so)[i], Ti_old, T_z_prev, T_db_s, T_sky_s,
                                             w, hc, sum_hr, sum_hrT, q_win_abs[wi], q_sw_in[i]);
                (*T_so)[i] = res.T_wo;
                Ti_new     = res.T_wi;
            }

            // Optional light damping on late iterations if oscillating
            if (iter > 8u) { Ti_new = 0.5 * (Ti_old + Ti_new); }
            (*T_si)[i] = Ti_new;
            max_err = max(max_err, abs(Ti_new - Ti_old));
        }
        converged = (max_err < 0.01);
    }

    // 6. Zone Air 3OBD Predictor-Corrector + Heating-Only IdealLoads (Difference Form)
    let dt: f32 = 300.0;
    let C_over_6dt = zone_C_air[b] / (6.0 * dt);
    var sum_hA: f32 = 0.0;
    var sum_hAT: f32 = 0.0;
    for (var s: u32 = 0u; s < S_MAX; s++) {
        if (surf_btype(s, b) == BTYPE_PAD) { continue; }
        let hA = hc_in[s] * surf_area(s, b);
        sum_hA  += hA;
        sum_hAT += hA * (*T_si)[s];
    }
    let m_cp = zone_m_vent_cp[b];
    let T1 = (*T_z_hist)[0];
    let T2 = (*T_z_hist)[1];
    let T3 = (*T_z_hist)[2];

    // Difference-form RHS for 3OBD: 11*(Tz - T1) - 7*(T1 - T2) + 2*(T2 - T3)
    // => 11*Tz = 11*T1 + 7*(T1 - T2) - 2*(T2 - T3) + (6*dt/Cz)*Q_net
    let hist_term = C_over_6dt * (11.0*T1 + 7.0*(T1 - T2) - 2.0*(T2 - T3));
    let denom     = 11.0 * C_over_6dt + sum_hA + m_cp;
    let T_z_float = (hist_term + sum_hAT + m_cp * T_db_s + Q_int_conv) / denom;

    let T_set = zone_T_set[b];
    var Q_heat: f32 = 0.0;
    var T_z_new: f32 = T_z_float;
    if (T_z_float < T_set) {
        Q_heat  = denom * (T_set - T_z_float);
        T_z_new = T_set;
    }

    // 7. Update Thermal Histories (3OBD + InternalMass CTF ring shift)
    (*T_z_hist)[2] = T2;
    (*T_z_hist)[1] = T1;
    (*T_z_hist)[0] = T_z_new;

    let q_im_now = ctf_ZY_diff(0u, b) * (*T_si)[im_s] + q_ctf_hist;
    for (var k: u32 = M_MAX - 1u; k > 0u; k--) {
        (*im_T_hist)[k] = (*im_T_hist)[k - 1u];
        (*im_q_hist)[k] = (*im_q_hist)[k - 1u];
    }
    (*im_T_hist)[0] = (*T_si)[im_s];
    (*im_q_hist)[0] = q_im_now;

    return Q_heat * dt; // Heating energy [J] for this 5-min timestep
}
```

#### B. Chunked Multi-Day Kernel & Year/Warm-up Driver (Python Host + GPU Dispatch)
```wgsl
// GPU Entrypoint: 1 thread = 1 building, runs N_DAYS (e.g., 5 days = 1440 steps) per dispatch.
@compute @workgroup_size(64)
fn run_chunk(@builtin(global_invocation_id) gid: vec3<u32>) {
    let b = gid.x;
    if (b >= uniforms.B_active) { return; }
    // Load dynamic state once from global SoA buffers into thread-private arrays
    var T_si = load_T_si(b);
    var T_so = load_T_so(b);
    var T_z_hist = load_Tz_hist(b);
    var im_T_hist = load_im_T_hist(b);
    var im_q_hist = load_im_q_hist(b);

    for (var hr: u32 = 0u; hr < uniforms.H_chunk; hr++) {
        let Q_int = sched_Q_int_conv[hr * uniforms.B_stride + b];
        var E_hr: f32 = 0.0;
        for (var sub: u32 = 0u; sub < 12u; sub++) {
            let t = hr * 12u + sub;
            let w = weather_chunk[t]; // broadcast from L1/constant cache!
            E_hr += step_building(b, w, Q_int, &T_si, &T_so, &T_z_hist, &im_T_hist, &im_q_hist);
        }
        if (uniforms.write_output == 1u) {
            out_E_heat_hr[hr * uniforms.B_stride + b] = E_hr;
        }
    }
    // Persist dynamic state back to global SoA buffers once at chunk end
    store_state(b, T_si, T_so, T_z_hist, im_T_hist, im_q_hist);
}
```

```python
# Host orchestration (Python + wgpu-py) — Warm-up + Annual Loop
def simulate_year_batch(gpu_ctx, batch_soa, epw_chunks, sched_chunks):
    # 1. Warmup: fixed 10 repeated Day-1 dispatches (zero warp divergence)
    day1_weather = epw_chunks[0]  # 288 steps
    day1_sched   = sched_chunks[0]
    for d in range(10):
        # On d == 8 and d == 9, record max T_z and peak Q_heat per building
        gpu_ctx.dispatch_chunk(day1_weather, day1_sched, H_chunk=24, write_output=(d >= 8))

    # 2. Check warmup convergence on host (vectorized NumPy, <1 ms); refine only outliers
    unconverged = find_unconverged_indices(gpu_ctx.read_warmup_metrics(), tol_T=0.04, tol_Q=0.04)
    extra_day = 10
    while len(unconverged) > 0 and extra_day < 25:
        gpu_ctx.dispatch_subset_chunk(unconverged, day1_weather, day1_sched, H_chunk=24)
        unconverged = recheck_unconverged(gpu_ctx, unconverged)
        extra_day += 1

    # 3. Annual run: 73 dispatches of 5-day chunks (1,440 steps each; ~50–150 ms/dispatch)
    #    Double-buffered async readback of hourly outputs [120, B] to pinned host memory
    hourly_E_heat = np.empty((8760, batch_soa.B), dtype=np.float32)
    for chunk_idx in range(73):
        h0 = chunk_idx * 120
        h1 = min(h0 + 120, 8760)
        gpu_ctx.dispatch_chunk(epw_chunks[chunk_idx], sched_chunks[chunk_idx],
                               H_chunk=(h1 - h0), write_output=True)
        hourly_E_heat[h0:h1, :] = gpu_ctx.read_hourly_buffer(h1 - h0)
    return hourly_E_heat  # Sum along axis=0 in float64 on CPU for annual totals
```

### 6.3 I/O Path: IDF In → CSV Out (Avoiding the Python I/O Wall)
A naive pipeline that generates 10,000 IDFs with `eppy`, parses 10,000 IDFs back in Python, runs GPU in 4 seconds, and writes 10,000 `eplusout.csv` files (~400 KB each = 4 GB of text) will spend **>95% of wall time in Python text I/O**!

- **Fast Path (Recommended for OpenUBEM campaigns):**
  1. **Bypass IDF text round-trip when generating from TABULA:** Feed the Python archetype parameter table (NumPy/Arrow/Parquet) **directly** into the GPU batch compiler (`tabula_df -> cpu_fp64_precompute(CTF, ScriptF, SimpleGlazing) -> SoA GPU buffers`). Keep an optional **IDF ingestion path** (fast regex/scanner or `epJSON` parser in Python/Rust—not `eppy`'s slow DOM) strictly for verification against EnergyPlus and legacy IDF batches.
  2. **Batch Output Storage:** Write the `[8760, B]` hourly heating matrix directly to **Apache Parquet / Zarr / compressed `.npy`** (~35 MB compressed for 10,000 buildings, written in <0.5 s).
  3. **Compatibility Adapter (`eplusout.csv`):** Provide a lightweight streaming adapter that either (a) exposes the same downstream DataFrame/reader API directly from Parquet, or (b) materializes `eplusout.csv` on demand in parallel worker processes only for selected buildings.

---

## 7. Throughput Estimate (Workload A)

> **Explicit Label: ESTIMATE (first-principles roofline model, FP32 precision).** Hardware specs verified 2026-11-22: Apple M2 Pro (19-core GPU: 6.8 TFLOPS FP32, 200 GB/s unified memory), NVIDIA RTX 4080 (48.74 TFLOPS FP32, 716.8 GB/s), NVIDIA RTX 4090 (82.58 TFLOPS FP32, 1,008 GB/s).

### 7.1 Per-Building-Timestep Arithmetic ($S_{\text{pad}} = 12$, $W = 2$, $M = 10$)
- **FLOPs per building-timestep** (assuming average 3 inner HB iterations at `Timestep 12`):
  - Exterior solar projection + simple glazing optics (6 outdoor surfaces): ~150 FLOPs
  - Outside HB (4 opaque outdoor surfaces × 2 iters × ~120 FLOPs): ~960 FLOPs
  - Inside HB (12 surfaces × 3 iters): TARP (~300) + symmetric ScriptF matvec (~288) + algebraic update (~360) = ~2,850 FLOPs
  - 2-node window solve (2 windows × 3 iters × ~120 FLOPs): ~720 FLOPs
  - CTF history + interior solar dist + 3OBD predictor-corrector + IdealLoads + shift: ~370 FLOPs
  - **Total compute:** **~5,050–5,500 FLOPs / building-timestep**.
  - Over 1 year + 10 warmup days = $105{,}120 + 2{,}880 = 108{,}000$ timesteps → **~5.94 × 10⁸ FLOPs / building-year**.
- **DRAM Bytes per building-timestep (5-day fused chunk = 1,440 steps):**
  - **Ideal L1-resident case:** Static params (~1,500 B: surf params 576 B + sym ScriptF 264 B + CTF/win/zone 660 B) + dynamic state R/W (~340 B) + 120 hr sched read (480 B) + 120 hr output write (480 B) ≈ **2,800 B per 5-day chunk** → **~1.94 B / building-timestep**.
    - Arithmetic intensity = $5{,}500 / 1.94 \approx \mathbf{2{,}835\text{ FLOP/B}}$ (far above all GPU ridge points: M2 Pro = 34, RTX 4080 = 68, RTX 4090 = 82 FLOP/B) → **Compute / register-latency bound**.
  - **Conservative L1-spill case:** If high active thread occupancy evicts `ScriptF` + surface params (~840 B) from L1 into L2/DRAM once per timestep (reused across the 3 inner iters in L1):
    - Traffic ≈ **~400–600 B / building-timestep** → Arithmetic intensity $\approx 9\text{--}14\text{ FLOP/B}$ → **L2 / DRAM bandwidth bound**.
- **Kernel Launch Overhead:**
  - 73 annual chunks + 10 warmup chunks = **83 dispatches** × ~25 µs = **~2.1 ms total** (negligible!).

### 7.2 Estimated Throughput Table (ESTIMATE, FP32, Compute Only)

| Hardware (Precision) | Roofline Compute Ceiling (100% peak) | Conservative Achieved Compute (15–25% scalar eff.) | Conservative L1-Spill DRAM Bound (75% BW @ 600 B/step) | **Estimated Throughput ($B = 1\text{k}$)** | **Estimated Throughput ($B = 10\text{k}$)** | **Estimated Throughput ($B = 100\text{k}$)** |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Apple M2 Pro (19-core, FP32)** | ~11,450 bldg-yr/s | 1,700–2,850 bldg-yr/s | ~2,315 bldg-yr/s | **400–800 bldg-yr/s** *(~1.2–2.5 s)* | **1,500–2,300 bldg-yr/s** *(~4.3–6.7 s)* | **1,600–2,300 bldg-yr/s** *(~43–63 s)* |
| **NVIDIA RTX 4080 (FP32)** | ~82,050 bldg-yr/s | 12,300–20,500 bldg-yr/s | ~8,300 bldg-yr/s | **1,500–3,000 bldg-yr/s** *(~0.3–0.7 s)* | **7,000–14,000 bldg-yr/s** *(~0.7–1.4 s)* | **8,500–18,000 bldg-yr/s** *(~5.5–12 s)* |
| **NVIDIA RTX 4090 (FP32)** | ~139,000 bldg-yr/s | 20,850–34,750 bldg-yr/s | ~11,670 bldg-yr/s | **2,000–4,000 bldg-yr/s** *(~0.25–0.5 s)* | **10,000–22,000 bldg-yr/s** *(~0.45–1.0 s)* | **12,000–30,000 bldg-yr/s** *(~3.3–8.3 s)* |

*Notes: (1) At $B = 1\text{k}$, RTX 4080/4090 SMs are under-saturated (only ~8–16 threads per SM), dropping efficiency to ~10–15%. (2) WGSL/Vulkan on Windows typically achieves ~75–90% of native CUDA on scalar kernels; both bounds above already accommodate this overhead. (3) Compare against single-core M2 Pro Rosetta E+ (0.25 bldg-yr/s) or 10-core CPU E+ (~2.5–4.0 bldg-yr/s).*

---

## 8. Verification Strategy

Proving equivalence against EnergyPlus v23.1.0 requires **bottom-up equation isolation** before end-to-end annual comparisons—otherwise cancelling errors hide bugs!

### 8.1 Three-Tier Verification Architecture
1. **Tier 1 — Per-Equation Teacher-Forcing Unit Tests (Zero Feedback Drift):**
   - Run a small set of representative Workload A IDFs through **EnergyPlus v23.1.0** with `Output:Variable` set to `Timestep` frequency (`Timestep 12`) for 1 winter week + 1 summer week.
   - Feed EnergyPlus's exact intermediate outputs (e.g., E+'s $T_{si}, T_{so}, T_z, V_z, \text{DNI}, \text{DHI}$) into **each isolated GPU/CPU kernel sub-function** (TARP, DOE-2, sky/ground LW, Perez solar, SimpleGlazing optics, ScriptF LW, CTF conduction, 3OBD IdealLoads) and assert direct agreement.
   - Catch every sign, unit, coefficient, and indexing discrepancy immediately.
2. **Tier 2 — Golden-Output Regression Suite (Workload A Archetypes):**
   - Select **25–50 stratified TABULA cases** spanning: (a) cold/mild/warm European climates, (b) uninsulated vs. deep-retrofit U-values, (c) low vs. high WWR (window area), (d) heavy vs. light `InternalMass`, (e) zero vs. high `OSC` $b$-factors, (f) intermittent vs. flat `Schedule:File` gains.
   - Also run a **CPU FP64 reference implementation** of the exact same kernel code to separate *physics discrepancies* (CPU FP64 vs. E+ v23.1.0) from *FP32 precision loss* (GPU FP32 vs. CPU FP64).
3. **Tier 3 — Standardized Diagnostic Benchmarks (ANSI/ASHRAE Standard 140 / BESTEST):**
   - Run **Cases 600 & 600FF** (low-mass envelope + solar windows), **Cases 900 & 900FF** (high-mass), and **Cases 620/640** (east/west glazing, setback) to verify envelope/window/mass physics independently of TABULA quirks, comparing against E+ v23.1.0 directly (not just the wide ASHRAE 140 inter-software band).

### 8.2 Tolerance Table (Acceptance Gates)

| Metric | Tier 1 (Teacher-Forced Step) | Tier 2 (GPU FP32 vs. CPU FP64) | Tier 2 (GPU FP32 vs. E+ v23.1.0) |
| :--- | :--- | :--- | :--- |
| **Annual IdealLoads Heating Energy** | — | **≤ 0.05%** | **≤ 0.5%** (target ≤ 0.2%) |
| **Monthly Heating Energy** (heating months >5% of annual) | — | ≤ 0.1% | ≤ 1.0% |
| **Hourly Heating Load CV(RMSE)** | — | ≤ 0.2% | **≤ 1.5%** |
| **Peak Hourly Heating Power** | — | ≤ 0.2% | ≤ 2.0% |
| **Zone Mean Air Temperature RMSE** (free-floating hours) | ≤ 0.01 °C | ≤ 0.02 °C | ≤ 0.15 °C |
| **Surface Inside/Outside Temp RMSE** | ≤ 0.05 °C | ≤ 0.05 °C | ≤ 0.3 °C |
| **Convection $h_c$ (TARP & DOE-2)** | ≤ 0.5% | ≤ 0.01% | ≤ 0.5% |
| **Window Transmitted Solar** | ≤ 1.0% | ≤ 0.01% | ≤ 1.0% |

### 8.3 Essential EnergyPlus v23.1.0 `Output:Variable` List
Request these at `Timestep` frequency in the golden-output IDFs to inspect every intermediate term:
- **Weather & Solar:** `Site Outdoor Air Drybulb Temperature`, `Site Sky Temperature`, `Site Wind Speed`, `Site Wind Direction`, `Site Direct Solar Radiation Rate per Area`, `Site Diffuse Solar Radiation Rate per Area`, `Site Solar Altitude Angle`, `Site Solar Azimuth Angle`.
- **Exterior Surface:** `Surface Outside Face Temperature`, `Surface Outside Face Convection Heat Transfer Coefficient`, `Surface Outside Face Incident Solar Radiation Rate per Area`, `Surface Outside Face Incident Beam Solar Radiation Rate per Area`, `Surface Outside Face Incident Sky Diffuse Solar Radiation Rate per Area`, `Surface Outside Face Incident Ground Diffuse Solar Radiation Rate per Area`, `Surface Outside Face Net Thermal Radiation Heat Gain Rate per Area`, `Surface Outside Face Conduction Heat Transfer Rate`.
- **Interior Surface & Window:** `Surface Inside Face Temperature`, `Surface Inside Face Convection Heat Transfer Coefficient`, `Surface Inside Face Conduction Heat Transfer Rate`, `Surface Inside Face Net Surface Thermal Radiation Heat Gain Rate`, `Surface Inside Face Solar Radiation Heat Gain Rate`, `Surface Window Transmitted Solar Radiation Rate`, `Surface Window Transmitted Beam Solar Radiation Rate`, `Surface Window Transmitted Diffuse Solar Radiation Rate`, `Surface Window Heat Gain Rate`, `Surface Window Heat Loss Rate`.
- **Zone Air & IdealLoads:** `Zone Mean Air Temperature`, `Zone Air Heat Balance Internal Convective Heat Gain Rate`, `Zone Air Heat Balance Surface Convection Rate`, `Zone Air Heat Balance Outdoor Air Transfer Rate`, `Zone Ventilation Sensible Heat Loss Energy`, `Zone Ventilation Sensible Heat Gain Energy`, `Zone Ideal Loads Supply Air Sensible Heating Energy`, `Zone Ideal Loads Supply Air Sensible Heating Rate`.
- **Precomputed Diagnostics (`.eio` file):** `Output:Constructions, Constructions;` (prints exact E+ v23.1.0 **CTF $X, Y, Z, F$ coefficients** to compare against your CPU CTF generator to 6+ digits!) and `Warmup Convergence Information`.

---

## 9. Milestone Roadmap (Workload A → Workload B, and Where to Stop)

| Milestone | Scope Added | Duration (Est.) | Exit Gate |
| :--- | :--- | :--- | :--- |
| **M0: CPU FP64 Reference & Preprocessor** | EPW parser + interpolation, CPU FP64 CTF generator (verified against `.eio`!), ScriptF + `FixViewFactors`, Arasteh SimpleGlazing converter, pure Python/NumPy FP64 Workload A engine. | **1.0 PM** | Tier 1 teacher-forced tests pass; annual heating ≤0.5% vs. E+ v23.1.0 on 10 TABULA cases. |
| **M1: `wgpu-py` Workload A GPU Engine (macOS M2 Pro)** | SoA packer, WGSL fused 5-day chunk megakernel, FP32 precision mitigations, warmup refinement pass, Parquet output + `eplusout.csv` adapter. | **1.5 PM** | ≤0.05% vs. M0 CPU FP64; ≤0.5% vs. E+ v23.1.0 on 50 TABULA cases + BESTEST 600; ≥1,000 bldg-yr/s on M2 Pro ($B=10\text{k}$). |
| **M2: Windows NVIDIA Validation & Batch I/O Pipeline** | CI & benchmarks on Windows workstation (RTX GPU via `wgpu-py` Vulkan/DX12), direct TABULA→SoA ingestion (no `eppy` round-trip), profiling (decide if CuPy/MSL fallback is needed). | **0.5–1.0 PM** | Bitwise-close (<0.05%) parity between macOS M2 Pro and Windows NVIDIA; ≥10,000 bldg-yr/s on RTX 4080/4090. |
| **M3: Layered Massive CTFs + Multi-Zone Coupling** | Generalize CTF history to all opaque surfaces (double-float accumulator for stiff walls); inter-zone partitions (`Surface` BC) + multi-zone `T_z` vector + cooling/dual-setpoint `IdealLoads`. | **2.0–2.5 PM** | ≤0.5% vs. E+ v23.1.0 on BESTEST 900 & 5-zone geomeppy blocks with IdealLoads. |
| **M4: GPU Exterior Shading (`Shading:Site:Detailed`)** | Orthographic GPU rasterizer in `wgpu` (`RenderPipeline`, `PixelCounting`-equivalent) computing sunlit fractions & sky view factors for hundreds of neighbor polygons; feeds **both** M3 GPU engine and CPU EnergyPlus (Workload B) via schedules/API! | **1.5–2.0 PM** | ≤1.0% annual heating/cooling difference vs. E+ `PolygonClipping` on dense urban blocks; ≥5× speedup on shading-heavy Workload B cases. |
| **M5 (Optional): Simple Single-Zone DX HVAC** | Constant-volume DX cooling/heating coil curves (`PTAC`, simple `PSZ-AC` / `PSZ-HP` without complex economizers/controls) as post-process or tightly coupled zone equipment. | **2.0–3.0 PM** | ≤2.0% electric/gas consumption vs. E+ v23.1.0 on single-zone DX archetypes. |

### **Where to STOP (Hard Boundary for GPU Re-Implementation)**
**STOP after M4 (or M5 for simple DX) and leave the rest of Workload B to multi-process CPU EnergyPlus (accelerated by M4 GPU shading)!**
Specifically, **do NOT re-implement on GPU:**
- Packaged VAV with reheat, multi-zone air loops, economizers, fan pressure/part-load curves, and supply air temperature reset managers;
- Chiller/boiler central plant loops (`PlantLoop`, primary/secondary pumping, cooling towers, thermal storage);
- Water-loop heat pumps (WLHP) and 4-pipe fan coils with dynamic loop temperature iteration (`SimHVAC` inner-outer loop coupling).

**Why:** EnergyPlus's HVAC/plant solver represents >60% of the codebase's algorithmic complexity, relies on irregular graph topologies, iterative mass/energy flow convergence, and dozens of empirical performance curves per component. Porting it to GPU would cost **25–40+ person-months**, suffer severe SIMT divergence across heterogeneous building systems, and constantly drift from E+ v23.1.0. Combining **M4 GPU shading** + **native multi-core CPU EnergyPlus** (plus optional **surrogate (f)** for parameter sweeps) is vastly superior ROI for complex Workload B buildings.

---

## 10. Key Risks & Mitigations

1. **Silent Physics Discrepancy in SimpleGlazing / Interior Solar Distribution (High Risk):**
   - *Mitigation:* Implement M0 CPU FP64 first and validate step-by-step against E+ `.eio` and `Timestep` `Output:Variable` dumps before writing a single line of WGSL.
2. **FP32 Drift on Stiff Multi-Layer CTFs (Medium Risk for M3; Low for Workload A):**
   - *Mitigation:* Sum-normalize CTF coeffs in FP64 before FP32 cast, shift temperatures by 20 °C, and deploy Dekker double-float (`vec2<f32>`) for CTF dot products if $1 - \sum F_k < 10^{-2}$ (or activate the CuPy FP64 fallback on Windows).
3. **Register Pressure / L1 Spilling in Fused Megakernel (Medium Risk):**
   - *Mitigation:* Store symmetric `ScriptF` as upper triangle (`S*(S-1)/2` = 66 floats instead of 144), keep `S_MAX` tight via bucketing (`10, 12, 16`), and profile occupancy on Apple Xcode Metal System Trace + NVIDIA Nsight Compute.
4. **Windows WDDM 2-Second TDR Timeout (Medium Risk):**
   - *Mitigation:* Keep chunk size configurable (default 5 days = 1,440 steps; auto-scale down to 1 day = 288 steps for huge batches $B \ge 100\text{k}$ so every dispatch finishes in <300 ms).
5. **Python `eppy` / CSV I/O Bottleneck Nullifying GPU Gains (High Operational Risk):**
   - *Mitigation:* Build a direct archetype-table → NumPy SoA path and Parquet output from Day 1; never force 10k+ GPU runs through `eppy` text parsing or 10k individual CSV files unless explicitly requested.
6. **`wgpu-py` Driver Quirks Between Metal and Vulkan/DX12 (Low–Medium Risk):**
   - *Mitigation:* Enforce strict WGSL compliance (no vendor extensions required for Workload A), run identical golden-output CI suites on both M2 Pro and Windows NVIDIA, and keep physics math cleanly modularized so translating WGSL → shared MSL/CUDA header takes <2 weeks if ever needed.

---

## 11. References

1. **EnergyPlus v23.1.0 Source Repository & Documentation (NREL / U.S. DOE):** https://github.com/NREL/EnergyPlus (tag `v23.1.0`); *EnergyPlus Engineering Reference* (Conduction Transfer Functions, Surface Heat Balance, TARP & DOE-2 Convection, ScriptF Interior Longwave, Arasteh Simple Window Model, ThirdOrderBackwardDifference Zone Air Balance, `SurfaceProperty:OtherSideCoefficients`, `ShadowCalculation:PixelCounting`).
2. **Arasteh, D., Kohler, C., & Griffith, B. (2009):** *Modeling Windows in EnergyPlus with Only U, SHGC, and Optionally VT*, LBNL / NREL (basis of `WindowMaterial:SimpleGlazingSystem` block model in EnergyPlus Engineering Reference).
3. **Jones, N. L. et al. / Hoover & Dogan:** GPU-accelerated `PixelCounting` shadow calculation in EnergyPlus (`SolarShading.cc`), IBPSA Building Simulation benchmarks (~2× shading speedup, ~0.01 accuracy tolerance).
4. **Frameworks (verified 2026-11-22):**
   - `pygfx/wgpu-py` v0.33.0 (released 2026-11-06): https://github.com/pygfx/wgpu-py
   - `pytorch/pytorch` v2.15.0 (released 2026-10-28; MPS no FP64): https://github.com/pytorch/pytorch
   - `jax-ml/jax` (no native Windows CUDA wheels; `jax-metal` unmaintained since late 2024): https://github.com/jax-ml/jax
   - `ml-explore/mlx` v0.32.4 (released 2026-10-14; Apple Silicon only): https://github.com/ml-explore/mlx
   - `taichi-dev/taichi` v1.7.4 (released 2025-07-31; maintenance mode): https://github.com/taichi-dev/taichi
   - `NVIDIA/warp` v1.19.0 (Nov 2026; macOS CPU-only): https://github.com/NVIDIA/warp
   - `kokkos/kokkos` v5.2.1 (2026-08-18) & AdaptiveCpp (experimental Metal backend): https://github.com/kokkos/kokkos
5. **Prior Art Repositories (verified 2026-11-22):**
   - `EURAC-EEBgroup/pyBuildingEnergy` (BSD-3-Clause): https://github.com/EURAC-EEBgroup/pyBuildingEnergy
   - `jfCoronel/OpenSimula` (MIT): https://github.com/jfCoronel/OpenSimula
   - `openBES-ecosystem/OpenBES-py`: https://github.com/openBES-ecosystem/OpenBES-py
   - `architecture-building-systems/CityEnergyAnalyst` (MIT, `v4.0.0-beta.9` Oct 2026): https://github.com/architecture-building-systems/CityEnergyAnalyst
   - `kaemco/CitySim-Solver` (BSD-3-Clause): https://github.com/kaemco/CitySim-Solver
   - `RWTH-EBC/TEASER` (MIT): https://github.com/RWTH-EBC/TEASER
   - `RWTH-EBC/AixLib` (BSD-3-Clause): https://github.com/RWTH-EBC/AixLib
   - `lbl-srg/modelica-buildings` (BSD-3-Clause, `v14.0.0` Oct 2026): https://github.com/lbl-srg/modelica-buildings
6. **Hardware Specifications (verified 2026-11-22):** Apple M2 Pro (19-core GPU: 6.8 TFLOPS FP32, 200 GB/s unified memory); NVIDIA GeForce RTX 4080 (48.74 TFLOPS FP32, 716.8 GB/s); NVIDIA GeForce RTX 4090 (82.58 TFLOPS FP32, 1,008 GB/s).
