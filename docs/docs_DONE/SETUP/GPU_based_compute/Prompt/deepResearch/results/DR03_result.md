# DR03 — GPU-Batched Reduced-Order Physics (RC / ISO 52016-1) Calibrated to EnergyPlus

**Target System:** OpenUBEM (Phase 3 Fast Screening Tier)  
**Reference Engine:** EnergyPlus 23.1 (1 CPU process per building)  
**Target Hardware:** Apple M2 Pro (macOS, Metal/MPS dev) & Windows Workstation with NVIDIA CUDA GPU (WSL2/Linux available)

---

## Executive Summary

**Recommended Stack for OpenUBEM:**
1. **Model Class:** **7R2C / Two-Capacitance Zone Thermal Network (VDI 6007-1 / EUReCA-style)** as the default per-zone thermal core—separating fast indoor air/convective thermal mass ($C_{\text{air}}$) from slow envelope/internal structural thermal mass ($C_{\text{wall}}$) and exterior/interior wall resistances—coupled with a **branch-free algebraic HVAC capacity/deadband clamp** (ISO 13790 / ISO 52016-1 linear response) and **EnergyPlus-consistent temperature/PLR performance curves** (`CAPFT`, `EIRFT`, `EIRFPLR`) for heat pumps, boilers, and chillers. For multi-zone dwellings that cannot be aggregated to one zone, bucket buildings by zone count ($Z \in \{1, 2, 4, 8\}$) with inter-zone conductive/air-exchange couplings.
2. **Parameter Derivation & Calibration:** **Hybrid Physics-Analytical Initialization + Differentiable Grey-Box Calibration.** Initialize $(R, C, gA)$ analytically from OpenUBEM's existing geometry and EnergyPlus IDF constructions using **VDI 6007-1 / TEASER** rules (ensuring physical priors and identifiability), then fine-tune archetype-level correction multipliers and effective solar/infiltration/HVAC parameters via **reverse-mode automatic differentiation** (Adam + physical positivity/stability constraints) against a small set of EnergyPlus 23.1 reference simulations per archetype.
3. **Framework:** **JAX** (running via **WSL2 + CUDA 12/13** on the Windows workstation; **CPU `float64` / experimental `jax-metal` `float32`** on the Apple M2 Pro), utilizing **exact Zero-Order Hold (ZOH) matrix-exponential discretization precomputed in `float64`** and a **`float32` `jax.lax.scan` + `jax.vmap` rollout** over 8,760 hourly steps.
   * *Alternative if native Windows without WSL2 is mandatory:* **PyTorch 2.x** (native Windows CUDA + Apple Silicon MPS + direct compatibility with PNNL's [`pnnl/neuromancer`](https://github.com/pnnl/neuromancer)), noting that PyTorch lacks a production-stable equivalent to `jax.lax.scan` and therefore requires custom Triton/CUDA/Warp kernels or `torch.compile` loop handling to avoid Python overhead over 8,760 sequential steps.
4. **Expected Speedup vs. EnergyPlus 23.1:**
   * **Negative Result on Published GPU Benchmarks:** As detailed in Q3 and the GPU Implementations table, **no open-source, peer-reviewed GPU-batched building-stock RC simulator reporting measured `building-years/s` on NVIDIA CUDA or Apple MPS was found.** Published RC speedups are predominantly CPU-based: TEASER (VDI 6007) reports up to **97% computational effort reduction** vs. detailed models (DOI: [10.26868/25222708.2019.210431](https://doi.org/10.26868/25222708.2019.210431) / DLR report), and EUReCA / CEA simulate districts on standard multi-core laptop CPUs in **seconds to minutes** vs. hours/days in EnergyPlus.
   * **Projected OpenUBEM Fast-Tier Speedup (`UNVERIFIED — theoretical`):** If an EnergyPlus 23.1 single-building annual run takes ~5–30 s on 1 CPU core (`UNVERIFIED`, depends on IDF complexity), a 1,000-building × 20-scenario sweep (20,000 building-years) requires ~28–167 CPU core-hours. In a GPU-batched ZOH 7R2C solver (e.g., 4–8 states per zone, $8,760 \times B$ matmuls in `float32` on a modern NVIDIA RTX workstation GPU), the thermal rollout is memory-bandwidth bound at tiny tensor sizes and is expected to execute **20,000 building-years in seconds to ~1 minute (`UNVERIFIED — theoretical`, excluding IDF parsing and first-run XLA JIT compilation)**—representing a **~10³×–10⁴×** speedup over single-process EnergyPlus, at the cost of explicit fidelity loss in multi-zone stratification, dynamic shading, and detailed HVAC hydraulics.

---

## Q1. Model Classes & Open-Source Implementations

### 1.1 Candidate Reduced-Order Model Classes

| Model Class | Physics Captured | Inputs Required | Typical Accuracy vs. EnergyPlus / TRNSYS | Key Limitations |
| :--- | :--- | :--- | :--- | :--- |
| **ISO 13790:2008 5R1C** (Simple Hourly Method) | Single lumped thermal mass node ($C_m$) coupled to internal surface ($T_s$) and indoor air ($T_{\text{air}}$) via 5 conductances ($H_{tr,w}$, $H_{tr,em}$, $H_{tr,ms}$, $H_{tr,is}$, $H_{ve}$). | Effective mass $C_m$, internal area $A_m$, glazing/opaque $U$-values & areas, $g$-values, ventilation/infiltration $H_{ve}$, internal/solar gains, setpoints. | **Hourly indoor $T_{\text{air}}$:** CV(RMSE) **< 3%** (2.7–3.1%), RMSE **< 0.69 °C**, MAE 0.45–0.52 °C vs. EnergyPlus ([MDPI](https://www.mdpi.com)).<br>**Annual energy:** typically within **10–17%** (up to ±20% across climates/masses vs. TRNSYS, Vivian et al. 2017).<br>**Peak heating:** overestimated up to **~8–10%** ([MDPI](https://www.mdpi.com)); cooling peaks degrade in lightweight/high-solar buildings. | Single capacitance smooths fast vs. slow mass; fails in lightweight or heavily glazed buildings during cooling; no latent loads, no multi-zone coupling, fixed $h_c$/$h_r$, angle-independent window $g$-values. |
| **ISO 52016-1:2017** (Hourly Method; plus **ISO 52016-3** adaptive elements) | Multi-node RC discretization **per opaque building element** (typically 5 nodes / 4R5C-style chain per wall/roof/floor) coupled to zone air/radiant nodes, longwave sky radiation, and dynamic hourly surface balances. | Element-by-element areas, orientations, tilt, layer-by-layer thermal resistance & mass class distribution, window $U_w$/$g_{gl}$, shading factors, schedules. | **Annual needs (uncalibrated):** deviations up to **40% (heating)** and **18% (cooling)** vs. EnergyPlus/TRNSYS depending on climate & national annex (Zakula et al. 2019, DOI: [10.1016/j.apenergy.2019.113553](https://doi.org/10.1016/j.apenergy.2019.113553); Ballarini et al. 2019, DOI: [10.26868/25222708.2019.210431](https://doi.org/10.26868/25222708.2019.210431)).<br>**Italian National Annex fix** (Mazzarella et al. 2020, DOI: [10.1016/j.enbuild.2020.110272](https://doi.org/10.1016/j.enbuild.2020.110272)): cuts internal heat flux amplitude error by **up to 67%** (external flux error ~**3%**). | Standardized constant $h_c$ (EN ISO 6946) vs. E+ wind/temp-dependent convection (De Luca et al. 2021, DOI: [10.3390/en15031030](https://doi.org/10.3390/en15031030)); angle-independent glazing properties; many more states per building (20–40+ nodes) if modeled per orientation, creating heterogeneous state sizes for GPU batching. |
| **VDI 6007-1 7R2C** (and multi-zone 7R2C variants like TEASER / EUReCA / RCBldEng) | Separates **asymmetric exterior walls** (outer/inner mass $C_{1,\text{AW}}$) from **adiabatic/symmetric interior walls/slabs** ($C_{1,\text{IW}}$) plus fast indoor air/radiant exchange (7 resistances, 2 capacitances per zone). | Layer thicknesses, $\lambda, \rho, c_p$ per wall/roof/slab/interior partition, window areas & $g$-values by orientation, ventilation/internal gains. | **Vivian et al. (2017)** (*Energy & Buildings*, 150, 447–465): 7R2C cuts transient/peak RMSE by **up to ~53%** vs. 5R1C against TRNSYS, especially in cooling & lightweight buildings.<br>**EUReCA (Prataviera et al. 2021, DOI: [10.1016/j.renene.2021.03.144](https://doi.org/10.1016/j.renene.2021.03.144)):** ~**7%** aggregate district overestimation.<br>**RCBldEng multi-zone 7R2C** (Shen 2026, DOI: [10.1016/j.energy.2026.140260](https://doi.org/10.1016/j.energy.2026.140260)): $R^2 \approx \mathbf{99\%}$ vs. EnergyPlus DOE office prototypes. | Still lumps exterior orientations unless extended to per-orientation wall nodes; assumes well-mixed zone air; relies on separate models for latent loads, ground coupling (ISO 13370), and HVAC plants. |
| **Lower-Order / Per-Orientation RC** (2R1C, 3R2C, 4R3C, per-orientation walls) | Minimalist 2–4 state ODEs (air + envelope + optional slab/core mass), or $1 + N_{\text{orient}}$ nodes to capture phase lag of East/South/West facades. | Effective $R_i, C_i$, effective solar aperture $A_{\text{sol}}$ (typically identified from data rather than pure physical calculation). | **Calibrated 3R2C/4R3C:** Can match single-zone E+ hourly air temperature within **< 0.5–1.0 °C RMSE** (`UNVERIFIED` general bound; see Q4 for specific PINN/grey-box RMSEs). | **Severe structural non-identifiability** if unregularized; poor extrapolation to envelope retrofits unless $R,C$ are tied to physical wall properties. |
| **Grey-Box / Physics-Constrained ML** (CTSM-R, PCNN, NeuroMANCER) | Linear RC state-space backbone + learned neural residual / disturbance / solar-gain nonlinear terms, enforcing dissipativity & eigenvalue bounds. | Geometric priors ($R,C$ bounds) + 10 days to 4 weeks of high-res training telemetry or E+ output per building/archetype. | **PCNN** (Di Natale et al. 2022, DOI: [10.1016/j.apenergy.2022.119806](https://doi.org/10.1016/j.apenergy.2022.119806)): **40–50% lower RMSE** over 3-day horizons vs. pure RC.<br>**Drgoňa et al. (2021, DOI: [10.1016/j.enbuild.2021.110992](https://doi.org/10.1016/j.enbuild.2021.110992)):** generalizes 20–30 days from 10 days of 15-min data. | Black-box residual terms risk **physical breakdown under unseen retrofit scenarios** (e.g., changing wall U-value or window SHGC) unless parameterized structurally by physical inputs. |

### 1.2 Open-Source Implementations Audit

| Repository / Tool | URL | Language | Licence | Stars | Last Commit / Activity Status | Maintained? | GPU-Friendliness |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TEASER** (`RWTH-EBC/TEASER`) | https://github.com/RWTH-EBC/TEASER | Python | MIT | ~148 | Active through **2025–2026** (Python 3.12 tested; exact commit date `UNVERIFIED`) | **Yes** | **Low** (generates Modelica/AixLib files; CPU Modelica solver, though VDI 6007 parameter math is easily ported). |
| **CityEnergyAnalyst** (`architecture-building-systems/CityEnergyAnalyst`) | https://github.com/architecture-building-systems/CityEnergyAnalyst | Python (>93%) | MIT | ~287 | Active through **Oct 2025+** (CEA-4 active; CEA Series 3 EOL 30 Jun 2025; exact latest commit `UNVERIFIED`) | **Yes** | **Low** (pandas/NumPy CPU pipeline + DAYSIM subprocesses; 5R1C logic is portable). |
| **pyBuildingEnergy** (`EURAC-EEBgroup/pyBuildingEnergy`) | https://github.com/EURAC-EEBgroup/pyBuildingEnergy | Python | BSD-3-Clause (GitHub) / MIT (docs) | ~56 | Active through **2026** (ASHRAE 140-2023 & ISO 52016-3 updates; exact commit date `UNVERIFIED`) | **Yes** | **Low–Medium** (clean Python ISO 52016-1 reference engine; scalar/per-building CPU loops, good reference oracle). |
| **EUReCA** (`BETALAB-team/EUReCA`) | https://github.com/BETALAB-team/EUReCA | Python | MIT | ~41 | Active releases (`v1.0.0-beta`, pyproject/docs updates; exact last commit date `UNVERIFIED`) | **Yes** (`UNVERIFIED` exact recency) | **Low–Medium** (CPU NumPy/SciPy per-building loop, but clean 5R1C & 7R2C state-space math ideal for porting). |
| **RC_BuildingSimulator** (`architecture-building-systems/RC_BuildingSimulator`) | https://github.com/architecture-building-systems/RC_BuildingSimulator | Python | MIT | ~133 | Core repo largely static for **>2 years** (peak ~2017–2020; exact last commit `UNVERIFIED`). Fork `rcbsim` on PyPI updated **late 2024**. | **No (Flagged: >2 yrs inactive)** | **Low** (scalar Python hourly loop; simple reference for 5R1C). |
| **ModestPy** (`sdu-cfei/modest-py`) | https://github.com/sdu-cfei/modest-py | Python | BSD-2-Clause | ~52 | Development ceased; tested on Ubuntu 18.04 / Python 3.6–3.7 (`>2 yrs` inactive) | **No (Archived / Flagged)** | **Low** (CPU FMI/FMU black-box/local-global parameter estimation). |
| **epymcr** (`zixiaoshawnshi/epymcr`) | https://github.com/zixiaoshawnshi/epymcr | Python | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | **Low** (uses `eppy` to cluster/reduce EnergyPlus IDFs, then runs EnergyPlus). |
| **RCBldRH / RCBldEng** (`andersonspy/RCBldRH`) | https://github.com/andersonspy/RCBldRH | Python / GH (`.gha`) | `UNVERIFIED` | `UNVERIFIED` | Companion to 2025–2026 papers (`UNVERIFIED` exact commit) | `UNVERIFIED` | **Low** (wraps compiled Windows `RCBldEng.exe` CPU binary). |
| **NeuroMANCER** (`pnnl/neuromancer`) | https://github.com/pnnl/neuromancer | Python | BSD-2-Clause | ~1,400 | Active through **2025–2026** (exact latest commit date `UNVERIFIED`) | **Yes** | **High** (native PyTorch tensors, CUDA/MPS GPU-batched differentiable ODE/MPC calibration). |
| **UrbanSolarCarver** (`avarth/UrbanSolarCarver`) | https://github.com/avarth/UrbanSolarCarver | Python | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | `UNVERIFIED` | **High** (PyTorch + NVIDIA Warp GPU ray tracing + 5R1C urban workflow). |

---

## Q2. HVAC & Energy Use in ROMs

Reduced-order thermal networks compute **sensible thermal loads** ($\Phi_{H,\text{nd}}, \Phi_{C,\text{nd}}$ in W). Converting loads into **delivered / site energy** (electricity, gas, district heat) requires mapping system efficiency, capacity derating, and part-load behavior without solving full psychrometric and hydraulic loops.

### 2.1 Methods Used in ROM & UBEM Literature
1. **Static / Seasonal Factors (SCOP / SEER):** Simplest approach ($\dot{E} = \Phi / \text{SCOP}$). Ignores capacity collapse at low outdoor temperatures and cycling losses; unsuitable when peak electric demand or hourly heat-pump performance under climate scenarios is evaluated.
2. **Standardized Bin / Calculation Methods (EN 15316-4-2 & EN 14825):** Used in EPBD-aligned tools (`pyBuildingEnergy`, European UBEMs). EN 15316-4-2 computes hourly/bin heat pump COP via **Path A** (EN 14511 full-load test points interpolated by source/sink temperature + part-load degradation factor $C_c$ and standby losses) or **Path B** (EN 14825 part-load bin data).
3. **EnergyPlus-Style Bi-Quadratic / Cubic Performance Curves (`CAPFT`, `EIRFT`, `EIRFPLR`):** Directly mirrors EnergyPlus DX coil and `HeatPump:PlantLoop:EIR` models as pure algebraic tensor operations:
   - Available capacity: $Q_{\text{cap}}(T_{\text{in}}, T_{\text{out}}) = Q_{\text{rated}} \cdot \text{CAPFT}(T_{\text{wb/db}}, T_{\text{odb}})$
   - Energy Input Ratio (inverse COP) modifier by temperature: $\text{EIRFT}(T_{\text{wb/db}}, T_{\text{odb}})$
   - Part-Load Ratio: $\text{PLR} = \text{clip}(\Phi_{\text{nd}} / Q_{\text{cap}}, 0, 1)$
   - Cycling / inverter degradation: $\text{EIRFPLR}(\text{PLR})$ (or fixed-speed cycling loss $\text{PLF} = 1 - C_d(1 - \text{PLR})$, $\text{RTF} = \text{PLR} / \text{PLF}$).
   - Electric power: $P_{\text{el}} = (Q_{\text{cap}} / \text{COP}_{\text{rated}}) \cdot \text{EIRFT} \cdot \text{EIRFPLR} \cdot \text{RTF} + P_{\text{aux}}$ (with backup electric resistance or boiler engaged if $\Phi_{H,\text{nd}} > Q_{\text{cap}}$).

### 2.2 Accuracy Loss vs. Full EnergyPlus HVAC Simulation
* **EN 15316 / EN 14825 vs. field/detailed dynamics:** Part-load COP discrepancies vs. measured field performance range **2–7%** for EN 14825 (Path B) and **4–13%** for EN 15316 when cycling frequency and standby losses deviate from default norm assumptions ([E3S Web of Conferences](https://www.e3s-conferences.org)).
* **Curve-based DX/HP models:** Within manufacturer catalog bounds, bi-quadratic curve fits match full-load capacity/COP within **±1–3%** ([OSTI](https://www.osti.gov)); however, integrated whole-building heat pump system hourly CV(RMSE)/NRMSE typically sits at **10–15%** (MBE ±5%) even after calibration ([MDPI](https://www.mdpi.com)).
* **Urban ROMs (CEA / EUReCA) vs. detailed E+ HVAC:** Simplified bin/lookup HVAC models exhibit **5–15%+ hourly peak electricity errors**, narrowing to **5–8%** for monthly/seasonal aggregated COP ([search synthesis of EN 15316/UBEM studies]).
* **Systematic Sources of Fidelity Loss vs. EnergyPlus:**
  1. **Latent cooling & coil bypass factor:** Sensible-only RC networks omit indoor humidity balance ($w_{\text{air}}$) and DX coil Sensible Heat Ratio (SHR) variation at low air-flow/part-load, under-predicting cooling electricity in humid climates unless a separate humidity-balance equation or calibrated latent multiplier is added.
  2. **Air-loop & hydronic coupling:** ROMs omit variable-air-volume (VAV) duct static pressure fan laws, economizer outdoor-air damper enthalpy switching, supply-water reset curves, and plant-loop thermal capacitance/pumping power.
  3. **Defrost & minimum unloading:** Air-source heat pump frost/defrost penalties ($T_{\text{odb}} \in [-5, +5]\,^\circ\text{C}$, high RH) and compressor minimum speed limits must be explicitly encoded in `CAPFT`/`EIRFPLR` or calibrated against E+.

---

## Q3. GPU Batching of Building Thermal Models

### 3.1 Existing Implementations & Negative Result

| Project / Paper | URL / DOI | Framework | Reported Throughput | Precision & Hardware | Notes / Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **No pure GPU-batched UBEM RC thermal solver with `building-years/s` benchmark found** | *Negative result* | — | Not reported | — | Literature & GitHub search found no open-source GPU-batched multi-building RC energy simulator reporting measured `building-years/s`. |
| **UrbanSolarCarver** (`avarth/UrbanSolarCarver`) | https://github.com/avarth/UrbanSolarCarver | PyTorch + NVIDIA Warp | `UNVERIFIED` (not reported in search) | `UNVERIFIED` | GPU ray-tracing solar analysis + ISO 13790 5R1C urban digital twin; throughput not benchmarked publicly in search results. |
| **NeuroMANCER** (`pnnl/neuromancer`) | https://github.com/pnnl/neuromancer | PyTorch | Not reported as UBEM `building-years/s` | `float32` (default PyTorch CUDA/MPS) | Differentiable constrained optimization & DPC for single/multi-zone control, not a district UBEM batch runner. |
| **GUST1.0** | DOI: [10.5194/gmd-18-10143-2025](https://doi.org/10.5194/gmd-18-10143-2025) / Zenodo: [10.5281/zenodo.15074365](https://doi.org/10.5281/zenodo.15074365) | CUDA | Not reported in building-years/s | CUDA GPU (`UNVERIFIED` precision) | 3D urban surface temperature via GPU Monte Carlo reverse ray-tracing; urban microclimate, not building HVAC energy. |
| **UBEM.io / CNS Shading** | DOI: [10.26868/25222708.2023.1389](https://doi.org/10.26868/25222708.2023.1389) | GPU shading (`UNVERIFIED` framework) | **>1000× speedup** claimed vs. EnergyPlus shading | GPU (`UNVERIFIED` precision/model) | Accelerates urban shading/PV ray-casting, not the RC ODE solver itself. |
| **RCBldEng / RCBldGH** | DOI: [10.1016/j.energy.2026.140260](https://doi.org/10.1016/j.energy.2026.140260), [10.1016/j.buildenv.2025.113116](https://doi.org/10.1016/j.buildenv.2025.113116) | Python / `.exe` CPU | **Seconds** vs. minutes (Grasshopper parametric runs) | CPU (`UNVERIFIED` hardware) | Multi-zone 7R2C CPU engine; not GPU-batched. |
| **EUReCA / TEASER** | [EUReCA](https://github.com/BETALAB-team/EUReCA) / [TEASER](https://github.com/RWTH-EBC/TEASER) | Python (NumPy/SciPy) / Modelica | **Seconds to minutes** for districts (~6–12 s small neighborhoods); TEASER **97% effort reduction** | Multi-core laptop CPU (`float64` standard) | CPU-bound urban RC tools; useful as physical parameterization references, not GPU engines. |

### 3.2 GPU Implementation Patterns for OpenUBEM
1. **State-Space Discretization (ZOH vs. Explicit Euler vs. Crank-Nicolson):**
   - **Explicit Euler** ($x_{k+1} = (I + \Delta t A)x_k + \Delta t B u_k$) is **unsuitable at $\Delta t = 3600\text{ s}$**: building RC systems are **stiff** because indoor air nodes ($C_{\text{air}}$) have time constants of minutes whereas massive masonry/concrete walls ($C_{\text{wall}}$) have time constants of days. Explicit Euler violates $\Delta t < 2/|\lambda_{\max}|$ and diverges.
   - **Crank-Nicolson** ($x_{k+1} = (I - \frac{\Delta t}{2}A)^{-1}(I + \frac{\Delta t}{2}A)x_k + \dots$) is unconditionally stable and $O(\Delta t^2)$, but exhibits **spurious numerical ringing** on fast/stiff modes at $\Delta t = 3600\text{ s}$ ([Wikipedia — Stiff equation / Crank-Nicolson](https://en.wikipedia.org/wiki/Crank%E2%80%93Nicolson_method)).
   - **Exact Zero-Order Hold (ZOH) via Matrix Exponential:** For constant $\Delta t = 3600\text{ s}$, precompute per building/scenario using block-matrix exponential (`scipy.linalg.expm` on an $(n+m)\times(n+m)$ augmented matrix $\begin{bmatrix} A & B \\ 0 & 0 \end{bmatrix} \Delta t$):
     $$A_d = e^{A\Delta t}, \qquad B_d = \int_0^{\Delta t} e^{A\tau}\,d\tau\, B$$
     ZOH is **exact** for piecewise-constant inputs over $[t_k, t_k + \Delta t]$, completely **immune to stiffness and ringing**, and reduces each hourly step on the GPU to a pure dense matrix-vector multiply $x_{k+1}^{\text{free}} = A_d x_k + B_d u_k$ with no linear solves inside the 8,760-step time loop!
2. **Time-Stepping Compilation (`jax.lax.scan` + `jax.vmap` vs. PyTorch):**
   - Python `for t in range(8760)` inside `@jax.jit` unrolls 8,760 copies of the graph, causing OOM and multi-minute XLA compile times. **`jax.lax.scan`** compiles the loop into a single XLA `WhileOp` kernel on GPU. Wrapping the single-building rollout in **`jax.vmap`** over `[buildings × scenarios]` yields coalesced batched tensor ops.
   - In PyTorch, a Python loop over 8,760 steps incurs 8,760 kernel launch overheads (~5–15 µs/launch = ~45–130 ms CPU dispatch overhead per run regardless of GPU speed) unless fused via `torch.compile` (which may unroll or hit graph limits on long loops) or a custom Triton/Warp/CUDA kernel.
3. **Handling Heterogeneous Model Sizes (Padding & Archetype Bucketing):**
   - Single-zone buildings ($N=2$–$5$ states) and multi-zone buildings ($N=10$–$40$ states) cannot share a single unpadded dense tensor.
   - **Recommended pattern:** Bucket buildings by zone/state tier (e.g., `bucket_S`: $N_{\text{states}}=4$ [1 zone], `bucket_M`: $N_{\text{states}}=12$ [3–4 zones], `bucket_L`: $N_{\text{states}}=28$ [up to 10 zones]). Within each bucket, **pad unused nodes** with diagonal $A_d$ entries $= 0$ and zeroed $B_d$ rows/columns so unused states stay identically zero, triggering at most 3–4 XLA static-shape compilations across an entire city.
4. **Branch-Free Thermostat Deadband & Capacity Limits:**
   - Following the ISO 13790 / ISO 52016-1 linear response ("building behaviour line"), first advance the **free-floating** state ($\Phi_{HC,k} = 0$) using precomputed ZOH matrices:
     $$x_{k+1}^{\text{free}} = A_d x_k + B_d u_{k,\text{exo}}$$
   - Let $c = B_{d,\text{hvac}}$ be the step-response vector of node temperatures to unit HVAC power $\Phi_{HC,k}$ (for 1-zone, $c_0 = \partial T_{\text{air},k+1} / \partial \Phi_{HC,k} > 0$). Compute the unconstrained heating/cooling power required to hold deadband $[T_{H,\text{set},k}, T_{C,\text{set},k}]$:
     $$\Phi_{H,\text{req}} = \max\!\left(0,\; \frac{T_{H,\text{set},k} - T_{\text{air},k+1}^{\text{free}}}{c_0}\right), \qquad \Phi_{C,\text{req}} = \max\!\left(0,\; \frac{T_{\text{air},k+1}^{\text{free}} - T_{C,\text{set},k}}{c_0}\right)$$
   - Clamp branch-free to time-varying available equipment capacities $[\Phi_{H,\max,k}, \Phi_{C,\max,k}]$:
     $$\Phi_{HC,k} = \min(\Phi_{H,\text{req}},\, \Phi_{H,\max,k}) - \min(\Phi_{C,\text{req}},\, \Phi_{C,\max,k})$$
   - Update all state nodes linearly (exact superposition of linear ZOH!):
     $$x_{k+1} = x_{k+1}^{\text{free}} + c \cdot \Phi_{HC,k}$$
   - This handles all 5 ISO operating regimes (heating-limited, heating-at-setpoint, deadband free-floating, cooling-at-setpoint, cooling-limited) **with zero `if/else` branching, zero inner iterations, and piecewise-differentiable gradients** (or softplus-smoothed transitions during gradient calibration).

---

## Q4. Differentiable Calibration

### 4.1 Differentiable Building Physics & Bayesian Literature
* **PNNL NeuroMANCER & Physics-Constrained Deep Learning** (Drgoňa et al. 2021, *Energy & Buildings* 243, DOI: [10.1016/j.enbuild.2021.110992](https://doi.org/10.1016/j.enbuild.2021.110992); [`pnnl/neuromancer`](https://github.com/pnnl/neuromancer)): Encodes structured multi-zone RC state-space dynamics inside PyTorch autograd with Perron-Frobenius eigenvalue/dissipativity penalties. Trained on **only 10 days** of 15-minute data (20-zone commercial office benchmark), it generalizes accurately over **20–30 consecutive days** of open-loop rollout.
* **Control-Oriented Building PINNs & PCNNs:**
  - Gokhale et al. (2022, *Applied Energy* 314, DOI: [10.1016/j.apenergy.2022.118852](https://doi.org/10.1016/j.apenergy.2022.118852)): Couples RC latent thermal mass states ($T_m$) with neural encoders to achieve higher multi-step rollout accuracy than black-box MLPs under limited training data.
  - Di Natale et al. (2022, *Applied Energy* 325, DOI: [10.1016/j.apenergy.2022.119806](https://doi.org/10.1016/j.apenergy.2022.119806); 2023, DOI: [10.1016/j.apenergy.2023.121071](https://doi.org/10.1016/j.apenergy.2023.121071)): **Physically Consistent Neural Networks (PCNN)** embed linear RC priors alongside neural terms, cutting 3-day prediction RMSE by **40–50%** vs. pure RC grey-box models.
* **Bayesian Calibration & Identifiability** (Chong & Menberg; Kristensen; Bacher & Madsen CTSM-R):
  - **Identifiability failure:** In 3R2C+ networks, resistances and capacitances multiply/divide into shared time constants ($\tau_i = R_i C_i$), creating flat likelihood ridges and equifinality where unphysical $(R, C)$ pairs match training temperatures while failing under envelope retrofits (e.g., adding wall insulation).
  - **Mitigation:** Pre-screen parameters via sensitivity analysis (Morris/FAST), enforce strict physical positivity & bounded correction multipliers $\theta \in [0.5, 2.0]$ around VDI 6007 analytical priors, and add $L_2$ log-prior regularization $\lambda \|\log(p / p_{\text{VDI}})\|^2$ (MAP / Bayesian estimation).

### 4.2 How Much EnergyPlus Training Data per Archetype Is Needed?
* **Pure envelope thermal identification ($R, C, A_{\text{sol}}$):** Grey-box/Bayesian literature recommends **2–4 weeks** of hourly/sub-hourly data containing sufficient dynamic excitation (diurnal outdoor swings, solar peaks, setpoint setbacks, and free-floating decay) to separate fast air time constants from slow wall time constants ([IBPSA / grey-box literature](https://www.ibpsa.org)). Drgoňa et al. (2021) achieved convergence with **10 days** at 15-min resolution.
* **OpenUBEM Archetype Calibration (Recommended):** Because EnergyPlus 23.1 takes only seconds to ~1 minute to run **one full year (8,760 h)** for a single representative archetype IDF, generating **1 full-year E+ simulation (or 4–6 stratified design weeks covering winter heating, summer cooling, peak solar, and shoulder free-floating periods)** per archetype (plus 1–2 retrofit perturbations such as wall insulation and window SHGC upgrade) is trivial computationally and eliminates seasonal extrapolation bias across both envelope dynamics and HVAC part-load/outdoor-temperature curves.
* **Crucial Constraint:** Calibrate **dimensionless physical correction factors** (e.g., $\alpha_R, \alpha_C, \alpha_{\text{sol}}, \alpha_{\text{inf}}$ applied to each building's analytical VDI 6007 parameters) per archetype rather than raw $R,C$ values per building, so that geometry/U-value changes during retrofit scenarios still propagate physically!

---

## Q5. Parameter Derivation from IDF / Geometry

| Method | How Parameters Are Derived | Pros for OpenUBEM | Cons / Gaps |
| :--- | :--- | :--- | :--- |
| **ISO 52016-1 Node Rules** (5 nodes per opaque element) | Discretizes each wall/roof/floor into 5 capacitances & 4 resistances based on mass position class (internal/external/uniform) or layer-by-layer (Italian Annex). | Official EPBD standard; preserves per-orientation phase lag and surface radiant balances. | Produces ~20–40+ state nodes per zone (large dense $A_d$ matrices); fixed EN ISO 6946 $h_c$ causes up to 18–40% uncalibrated discrepancy vs. E+. |
| **VDI 6007-1 / TEASER Method** (7R2C) | Analytically collapses all exterior walls into one asymmetric 2R1C chain ($C_{1,\text{AW}}, R_{1,\text{AW}}, R_{\text{rest,AW}}$) and all interior walls/slabs/floors into one symmetric 1R1C element ($C_{1,\text{IW}}, R_{1,\text{IW}}$) via complex thermal impedance (frequency-domain) matching at 24 h period, coupled to zone air node. | **Directly compatible with OpenUBEM's existing inputs** (areas by orientation, constructions, U-values, thermal mass); compact fixed state size (**3 nodes/zone**: $T_{\text{air}}, T_{\text{wall,ext}}, T_{\text{wall,int}}$); proven ~53% lower peak/transient RMSE than 5R1C (Vivian et al. 2017). | Frequency-matched at 1-day period; lumps orientations unless exterior walls are optionally split into 4 cardinal nodes (N/E/S/W) for solar-dominated zones. |
| **IDF-Direct Extraction (`eppy`/`geomeppy`/`epymcr`)** | Parses `BuildingSurface:Detailed`, `FenestrationSurface:Detailed`, `Construction`, and `Material` from E+ IDF to compute $U A$, $\sum \rho c_p d A$, SHGC, and internal gains. | Extracts exact E+ ground-truth geometry and construction properties already generated by OpenUBEM. | `epymcr` still runs E+ on reduced IDFs rather than an analytical RC ODE; requires pairing with VDI 6007 or ISO 52016 formulas to build $A, B$. |

**Recommendation for OpenUBEM:** Implement a **pure-Python VDI 6007-1 (7R2C) parameter generator** directly fed by OpenUBEM's geometry/construction data structures (or parsed from IDF `Construction`/`Material`/`BuildingSurface:Detailed` objects using TEASER's open-source MIT-licensed VDI 6007 formulas). Optionally expand exterior wall mass from 1 lumped node to 4 cardinal nodes ($T_{w,N}, T_{w,E}, T_{w,S}, T_{w,W}$) for heavily glazed commercial/passive-solar archetypes—giving a compact, uniform **3-to-6 state vector per zone**.

---

## Q6. Framework Choice

| Criterion | **JAX** (Recommended) | **PyTorch 2.x** (Alternative) | **CuPy** | **Taichi** | **NVIDIA Warp** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Native Windows + CUDA** | **No** (CPU-only on native Windows; CUDA requires **WSL2**, officially marked experimental by JAX, though widely used). | **Yes** (official pip/conda Windows CUDA 12.x/13.x wheels). | **Yes** (Windows CUDA wheels). | **Yes** (CUDA / Vulkan). | **Yes** (Windows CUDA via `warp-lang`). |
| **Apple Silicon (M2 Pro)** | **Experimental (`jax-metal`)**; lags upstream JAX releases; **no `float64` support** (`jax_enable_x64` fails on Metal). Community `metaljax` wraps MLX. CPU works in `float64`. | **Yes (MPS)** natively in PyTorch; **no `float64` on MPS** (Metal hardware/MSL limitation — throws `TypeError`). CPU works in `float64`. | **No** (CUDA-only). | **Yes** (`ti.metal`). | **CPU-only on macOS** (no Metal GPU). |
| **8,760-Step Temporal Loop** | **Excellent:** `jax.lax.scan` compiles to a single XLA `WhileOp` kernel; `vmap` batches cleanly across `[B, S]`. | **Moderate:** Python `for` loop incurs 8,760 kernel-launch overheads unless fused by `torch.compile` or custom Triton/CUDA kernel. | Requires writing custom RawKernel CUDA C++ for 8,760-step fusion. | Excellent for custom fused kernels, but lacks ML autograd ecosystem. | Excellent fused CUDA kernels, PyTorch/JAX interop, but no Mac GPU. |
| **Differentiable Calibration** | **Best-in-class:** `jax.grad` / `value_and_grad` differentiates through `lax.scan` + `expm` + Optax natively. | **Strong:** `autograd` + Adam + direct **`pnnl/neuromancer`** integration. | **No built-in autograd.** | Limited (tape-based autodiff for kernels, not full ML optimizers). | Differentiable kernels, less mature for end-to-end ODE calibration. |
| **Licence & Ecosystem** | Apache-2.0; SciML (`Diffrax`, `Optax`, `Equinox`). | BSD-3-style; ~85k+ stars; `NeuroMANCER`. | MIT; NumPy drop-in. | Apache-2.0; ~28.5k stars. | Apache-2.0; ~7.1k stars. |

### Precision Analysis (`float32` vs. `float64` for Stiff Thermal ODEs)
* **Where `float64` is mandatory:** Computing the matrix exponential $A_d = e^{A\Delta t}$ and $B_d$ (or Crank-Nicolson matrix inversion) for stiff thermal networks with widely separated eigenvalues ($\tau_{\text{air}} \sim 10^2\text{ s}$ vs. $\tau_{\text{wall}} \sim 10^5\text{ s}$) **must** be done in **`float64`** to avoid catastrophic cancellation in scaling-and-squaring Padé approximations.
* **Hardware reality on consumer GPUs & Apple Silicon:**
  - Consumer NVIDIA RTX GPUs (RTX 3090/4080/4090) throttle FP64 throughput to **1/64th of FP32** (e.g., RTX 4090: ~82.6 TFLOPS FP32 vs. ~1.29 TFLOPS FP64).
  - Apple Silicon Metal (`jax-metal` and PyTorch MPS) **does not support `float64` at all**.
* **Recommended Split-Precision Strategy:**
  1. Perform parameter derivation and ZOH matrix-exponential discretization ($A, B \rightarrow A_d, B_d$) in **`float64` on CPU** (`scipy.linalg.expm` or JAX CPU `x64`, vectorized via `numpy.linalg` / batch CPU or fast on a few thousand archetypes in milliseconds), OR during calibration on Windows CUDA FP64 (where $N_{\text{states}} \le 8$ per zone makes FP64 `expm` over ~20 archetypes tiny).
  2. Cast the resulting stable contraction matrices $(A_d, B_d)$ and weather tensors (temperatures expressed in $^\circ\text{C}$ rather than K to preserve mantissa bits) to **`float32`** for the 8,760-step GPU `lax.scan` rollout across thousands of buildings × scenarios. Verify `float32` vs. `float64` rollout drift on a 50-building test set on CPU (`float64` oracle should stay within $< 10^{-3}\,^\circ\text{C}$ and $< 0.01\%$ EUI).

---

## Q7. Validation Protocol & Acceptance Thresholds

Published ROM/UBEM studies validate against EnergyPlus and empirical data using **ASHRAE Guideline 14 / IPMVP** statistical metrics alongside **ANSI/ASHRAE Standard 140 (BESTEST)** sanity tests (`pyBuildingEnergy` uses Standard 140 & ISO 52016 verification cases):

| Validation Metric | Standard Calibration Target (ASHRAE Guideline 14 / IPMVP) | Recommended OpenUBEM Screening-Tier Acceptance Threshold | Validation Scope & Notes |
| :--- | :--- | :--- | :--- |
| **Monthly / Annual Energy Bias (NMBE)** | **$\le \pm 5\%$** (monthly) | **$\le \pm 5\%$** per archetype; **$\le \pm 3\%$** district aggregate EUI (`UNVERIFIED` target) | Separate **heating** and **cooling** EUI so opposite biases do not cancel in total EUI. |
| **Monthly CV(RMSE)** | **$\le 15\%$** (15–20% across editions) | **$\le 10$–$15\%$** per archetype vs. E+ 23.1 | Checked on held-out weather year and held-out buildings within the archetype. |
| **Hourly NMBE** | **$\le \pm 10\%$** | **$\le \pm 10\%$** | Evaluated separately for space heating, space cooling, and electricity. |
| **Hourly CV(RMSE)** | **$\le 30\%$** | **$\le 20$–$30\%$** (total HVAC load); **$\le 5\%$** on free-floating $T_{\text{air}}$ (RMSE $< 1.0\,^\circ\text{C}$) | Hourly CV(RMSE) inflates when mean hourly load is near zero in shoulder seasons; report RMSE (W/m²) alongside CV(RMSE). |
| **Peak Load Error** | Not fixed in Guideline 14 | **$\le \pm 15\%$** on annual peak heating/cooling kW (`UNVERIFIED` target) | Critical for grid/district-heating screening; 7R2C outperforms 5R1C here. |
| **Retrofit Ranking Consistency** | — | **Spearman $\rho \ge 0.90$** on ECM EUI savings (`UNVERIFIED` target) | Validate on **out-of-sample retrofit runs** (wall insulation, glazing SHGC/U, HP swap, setpoint shift), not just baseline! |

---

## Reference Architecture (OpenUBEM Phase 3 Fast Tier)

### 1. Tensor Shapes & Bucketing
Group buildings into fixed state-size buckets (e.g., `B_S`: 1-zone 7R2C with $N_s = 3$ or $N_s = 6$ if split by orientation; `B_M`: up to 4 zones with $N_s = 12$). For a single bucket of $B$ buildings and $S$ scenarios ($M = B \times S$ total trajectories), over $T = 8760$ hours:
* State trajectory carried in `lax.scan`: `x` $\in \mathbb{R}^{M \times N_s}$ (`float32`, node temperatures in °C)
* Precomputed ZOH matrices (computed in `float64`, cast to `float32`):
  * `A_d` $\in \mathbb{R}^{M \times N_s \times N_s}$
  * `B_d` $\in \mathbb{R}^{M \times N_s \times N_u}$ (where $N_u$ exogenous inputs: $T_{\text{odb}}$, $T_{\text{sky/sol-air}}$, $Q_{\text{sol}}$, $Q_{\text{int}}$, $H_{\text{ve}} T_{\text{sup}}$)
  * `c_hvac` $\in \mathbb{R}^{M \times N_s}$ (unit HVAC heat injection step response, i.e., column of $B_d$ for $\Phi_{HC}$)
* Time-varying forcing (shared across buildings via broadcasting or indexed by climate/orientation): `U` $\in \mathbb{R}^{T \times M \times N_u}$, setpoints `T_set_H, T_set_C` $\in \mathbb{R}^{T \times M}$, capacity limits `Q_H_max, Q_C_max` $\in \mathbb{R}^{T \times M}$ (`float32`). *(Memory tip: store shared EPW weather `[T, N_w]` once and compute orientation solar projections inside the scan or per orientation group to keep VRAM $< 2\text{ GB}$ even for $M = 20,000$.)*

### 2. Pseudo-Code Sketch (JAX: `float64` ZOH Precompute + `float32` `lax.scan` Rollout + Calibration)

```python
import jax
import jax.numpy as jnp
from jax.scipy.linalg import expm
import optax

# --- 1. Analytical ZOH Discretization (run in float64) ---
def discretize_zoh_f64(A_c: jnp.ndarray, B_c: jnp.ndarray, dt: float = 3600.0):
    """Exact ZOH via block matrix exponential in float64.
    A_c: (Ns, Ns), B_c: (Ns, Nu) -> returns A_d, B_d in float32.
    """
    Ns, Nu = B_c.shape
    M = jnp.zeros((Ns + Nu, Ns + Nu), dtype=jnp.float64)
    M = M.at[:Ns, :Ns].set(A_c.astype(jnp.float64) * dt)
    M = M.at[:Ns, Ns:].set(B_c.astype(jnp.float64) * dt)
    EM = expm(M)
    return EM[:Ns, :Ns].astype(jnp.float32), EM[:Ns, Ns:].astype(jnp.float32)

# --- 2. Branch-Free Hourly Step + HVAC Energy Conversion ---
def rc_hvac_step(x_k, step_inputs, A_d, B_d, c_hvac, hp_params):
    """x_k: (Ns,), step_inputs: (u_exo, T_h_set, T_c_set, Q_h_max, Q_c_max, T_odb)"""
    u_exo, T_h_set, T_c_set, Q_h_max, Q_c_max, T_odb = step_inputs

    # Free-floating state at k+1 (no HVAC)
    x_free = A_d @ x_k + B_d @ u_exo
    T_air_free = x_free[0]  # index 0 = zone air node
    c0 = jnp.maximum(c_hvac[0], 1e-6)

    # Branch-free ISO 13790 / 52016 5-regime deadband & capacity clamp
    q_h_req = jnp.maximum(0.0, (T_h_set - T_air_free) / c0)
    q_c_req = jnp.maximum(0.0, (T_air_free - T_c_set) / c0)
    phi_hc = jnp.minimum(q_h_req, Q_h_max) - jnp.minimum(q_c_req, Q_c_max)

    # Exact linear superposition update
    x_next = x_free + c_hvac * phi_hc

    # Heat pump / HVAC curve conversion (EIR = f(T_odb, PLR))
    q_h = jnp.maximum(phi_hc, 0.0)
    cap_avail = Q_h_max * hp_capft(T_odb, hp_params)
    plr = jnp.clip(q_h / jnp.maximum(cap_avail, 1e-3), 0.0, 1.0)
    cop = hp_params["cop_nom"] / (hp_eirft(T_odb, hp_params) * hp_eirfplr(plr, hp_params))
    p_hp_el = jnp.minimum(q_h, cap_avail) / jnp.maximum(cop, 0.5)
    p_backup = jnp.maximum(q_h - cap_avail, 0.0)  # auxiliary electric/gas backup
    return x_next, (x_next[0], phi_hc, p_hp_el + p_backup)

# --- 3. Batched Annual Rollout across Buildings x Scenarios ---
def sim_one_trajectory(x0, forcing_T, A_d, B_d, c_hvac, hp_params):
    _, outputs = jax.lax.scan(
        lambda x, inp: rc_hvac_step(x, inp, A_d, B_d, c_hvac, hp_params),
        x0, forcing_T
    )
    return outputs  # (T_air[8760], Q_hc[8760], P_el[8760])

# Batch across M = B * S trajectories simultaneously on GPU
batched_sim = jax.jit(jax.vmap(sim_one_trajectory, in_axes=(0, 0, 0, 0, 0, 0)))

# --- 4. Differentiable Archetype Calibration Loop ---
def calibrate_archetype(theta_init, vdi_priors, eplus_ref, forcing_train):
    optimizer = optax.adam(learning_rate=1e-2)
    opt_state = optimizer.init(theta_init)

    def loss_fn(log_mult):
        # Strictly positive bounded multipliers around VDI 6007 physical priors
        mult = jnp.exp(jnp.clip(log_mult, -0.7, 0.7))
        A_c, B_c = build_7r2c_matrices(vdi_priors, mult)
        # Note: for calibration on small archetype batches (e.g. B=10), CPU/CUDA f64
        # or Padé expm gradient propagates directly through ZOH discretization
        A_d, B_d = discretize_zoh_f64(A_c, B_c)
        T_air, Q_hc, P_el = jax.vmap(sim_one_trajectory)(...)
        fit_loss = jnp.mean((Q_hc - eplus_ref["Q_hc"])**2) + 0.5 * jnp.mean((T_air - eplus_ref["T_air"])**2)
        prior_reg = 1e-2 * jnp.sum(log_mult**2)  # mitigates R*C equifinality
        return fit_loss + prior_reg

    # Standard optax update steps using jax.value_and_grad(loss_fn)
    ...
```

*(Note on differentiable `expm` in JAX on Apple Metal / `float32`: during calibration of a single archetype's ~5–15 multipliers, running the `expm` + calibration loop on **CPU in `float64`** takes seconds and avoids Metal's lack of `float64`; the resulting calibrated parameters are then discretized in `float64` and pushed to GPU in `float32` for the 10,000+ scenario UBEM sweeps.)*

---

## Risks & Limitations

1. **Multi-Zone Dwellings & Inter-Zone Air Coupling:** Aggregating a multi-story or split-setpoint building (e.g., heated living room + unheated garage/attic + bedrooms on separate schedules) into a single 7R2C zone introduces systematic bias in peak loads and solar redistribution. Even with zone-count bucketing, ROMs assume well-mixed air per zone and omit inter-zone airflow driven by buoyancy/stack effect unless explicitly added.
2. **Urban Context Shading & Angle-Dependent Glazing:** Standardized ROMs (ISO 52016-1, 5R1C, 7R2C) treat solar transmittance $g$ as constant and use pre-calculated shading factors rather than hourly per-window incident-angle modifiers and reflected/diffuse urban canyon shading. In dense districts, **context shading must be precomputed externally** (e.g., via GPU ray-tracing or EnergyPlus PixelCounting/view factors) and passed into the ROM as hourly attenuated incident irradiance per facade!
3. **Complex HVAC, Latent Loads, & Hydronic Loops:** Sensible RC networks cannot directly simulate latent dehumidification, VAV reheat/economizer logic, chiller-tower condenser water loops, or heat pump defrost cycling. Expect **5–15%+ hourly peak electrical divergence** vs. EnergyPlus for complex commercial HVAC (though residential split/heat-pump systems track much closer once `CAPFT`/`EIRFPLR` curves are calibrated).
4. **Calibration Overfitting & Retrofit Extrapolation Risk:** If an unconstrained neural residual (e.g., black-box MLP correction) absorbs missing physical effects during baseline calibration, changing the wall $U$-value or window SHGC in a retrofit scenario can fail silently. Always constrain calibration to **multiplicative adjustments on physical VDI 6007 terms** and validate on held-out EnergyPlus **retrofit perturbations**, not just the baseline year.
5. **Dual-Hardware Precision & Toolchain Friction:**
   - **Windows + JAX:** Native Windows lacks JAX CUDA wheels; the Windows workstation requires **WSL2** (with NVIDIA CUDA passthrough) or Linux dual-boot.
   - **Apple M2 Pro:** Both `jax-metal` (experimental) and PyTorch MPS prohibit `float64`. Never run `expm` or ill-conditioned matrix inversions in `float32` on Metal; run ZOH `expm` on CPU `float64` and validate `float32` rollout drift.
   - **Consumer NVIDIA GPUs:** RTX cards execute `float64` at 1/64th speed of `float32`; keeping the 8,760-step scan in `float32` after `float64` ZOH precomputation is essential to realize GPU speedups.

---

## References

1. **Zakula, T., Bagaric, M., Ferdelji, N., Milovanovic, B., Mudrinic, S., & Ritosa, K. (2019).** *Comparison of dynamic simulations and the ISO 52016 standard for the assessment of building energy performance.* Applied Energy, 254, 113553. DOI: [10.1016/j.apenergy.2019.113553](https://doi.org/10.1016/j.apenergy.2019.113553)
2. **Ballarini, I., Costantino, A., Fabrizio, E., & Corrado, V. (2019).** *The Dynamic Model of EN ISO 52016-1 for the Energy Assessment of Buildings Compared to Simplified and Detailed Simulation Methods.* Proceedings of Building Simulation 2019 (IBPSA). DOI: [10.26868/25222708.2019.210431](https://doi.org/10.26868/25222708.2019.210431)
3. **De Luca, G., Ballarini, I., Bianco Mauthe Degerfeld, F., & Corrado, V. (2021/2022).** *Accuracy of Simplified Modelling Assumptions on External and Internal Driving Forces in the Building Energy Performance Simulation.* Energies, 15(3), 1030. DOI: [10.3390/en15031030](https://doi.org/10.3390/en15031030)
4. **Mazzarella, L., Scoccia, R., Colombo, P., & Motta, M. (2020).** *Improvement to EN ISO 52016-1:2017 hourly heat transfer through a wall assessment: The Italian National Annex.* Energy and Buildings, 210, 110272. DOI: [10.1016/j.enbuild.2020.110272](https://doi.org/10.1016/j.enbuild.2020.110272)
5. **Campana, J. P., & Morini, G. L. (2019).** *BESTEST and EN ISO 52016 Benchmarking of ALMABuild, a New Open-Source Simulink Tool for Dynamic Energy Modelling of Buildings.* Energies, 12(15), 2938. DOI: [10.3390/en12152938](https://doi.org/10.3390/en12152938)
6. **Vivian, J., Zarrella, A., Emmi, G., & De Carli, M. (2017).** *An evaluation of the suitability of lumped-capacitance models in calculating energy needs and thermal behaviour of buildings.* Energy and Buildings, 150, 447–465.
7. **Prataviera, E., Romano, P., Carnieletto, L., Pirotti, F., Vivian, J., & Zarrella, A. (2021).** *EUReCA: An open-source urban building energy modelling tool for the efficient evaluation of cities energy demand.* Renewable Energy, 173, 544–560. DOI: [10.1016/j.renene.2021.03.144](https://doi.org/10.1016/j.renene.2021.03.144)
8. **Shen, P. (2026).** *RCBldEng - a computationally efficient RC network modeling method and engine for multizone building simulation.* Energy, 346, 140260. DOI: [10.1016/j.energy.2026.140260](https://doi.org/10.1016/j.energy.2026.140260) (and IBPSA 2025: DOI: [10.26868/25222708.2025.1957](https://doi.org/10.26868/25222708.2025.1957); *RCBldGH*: *Building and Environment*, 2025, DOI: [10.1016/j.buildenv.2025.113116](https://doi.org/10.1016/j.buildenv.2025.113116))
9. **Jayathissa, P., et al. (2017).** *Optimising building net energy demand with dynamic BIPV shading.* Applied Energy, 202, 726–735. (Repo: https://github.com/architecture-building-systems/RC_BuildingSimulator)
10. **Drgoňa, J., Tuor, A. R., Chandan, V., & Vrabie, D. L. (2021).** *Physics-constrained deep learning of multi-zone building thermal dynamics.* Energy and Buildings, 243, 110992. DOI: [10.1016/j.enbuild.2021.110992](https://doi.org/10.1016/j.enbuild.2021.110992) (Repo: https://github.com/pnnl/neuromancer)
11. **Gokhale, G., Claessens, B., & Develder, C. (2022).** *Physics informed neural networks for control oriented thermal modeling of buildings.* Applied Energy, 314, 118852. DOI: [10.1016/j.apenergy.2022.118852](https://doi.org/10.1016/j.apenergy.2022.118852)
12. **Di Natale, L., Svetozarevic, B., Heer, P., & Jones, C. N. (2022/2023).** *Physically Consistent Neural Networks for building thermal modeling: theory and analysis.* Applied Energy, 325, 119806. DOI: [10.1016/j.apenergy.2022.119806](https://doi.org/10.1016/j.apenergy.2022.119806) & Scalable multi-zone follow-up: DOI: [10.1016/j.apenergy.2023.121071](https://doi.org/10.1016/j.apenergy.2023.121071)
13. **Open-Source Repositories Cited:**
    - `RWTH-EBC/TEASER`: https://github.com/RWTH-EBC/TEASER
    - `architecture-building-systems/CityEnergyAnalyst`: https://github.com/architecture-building-systems/CityEnergyAnalyst
    - `EURAC-EEBgroup/pyBuildingEnergy`: https://github.com/EURAC-EEBgroup/pyBuildingEnergy
    - `BETALAB-team/EUReCA`: https://github.com/BETALAB-team/EUReCA
    - `architecture-building-systems/RC_BuildingSimulator`: https://github.com/architecture-building-systems/RC_BuildingSimulator
    - `sdu-cfei/modest-py`: https://github.com/sdu-cfei/modest-py
    - `zixiaoshawnshi/epymcr`: https://github.com/zixiaoshawnshi/epymcr
    - `jamiebull1/geomeppy`: https://github.com/jamiebull1/geomeppy
    - `andersonspy/RCBldRH`: https://github.com/andersonspy/RCBldRH
    - `pnnl/neuromancer`: https://github.com/pnnl/neuromancer
    - `avarth/UrbanSolarCarver`: https://github.com/avarth/UrbanSolarCarver
14. **GPU Urban Ray-Tracing / Shading & Framework Documentation:**
    - GUST1.0: DOI: [10.5194/gmd-18-10143-2025](https://doi.org/10.5194/gmd-18-10143-2025)
    - UBEM.io / CNS Shading: DOI: [10.26868/25222708.2023.1389](https://doi.org/10.26868/25222708.2023.1389)
    - NVIDIA Warp: https://github.com/NVIDIA/warp | Taichi: https://github.com/taichi-dev/taichi
    - PyTorch MPS `float64` limitation: https://pytorch.org/docs/stable/notes/mps.html | JAX Windows WSL2 & `jax-metal` status: https://docs.jax.dev/en/latest/installation.html
