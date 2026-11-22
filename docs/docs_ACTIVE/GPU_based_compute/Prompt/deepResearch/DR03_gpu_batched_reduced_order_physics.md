# DR03 — GPU-Batched Reduced-Order Physics (RC / ISO 52016-1) Calibrated to EnergyPlus

**Feeds:** Phase 3 (the GPU fast tier, the main source of large speedups)
**Save output to:** `results/DR03_result.md`

---

## PROMPT

You are a researcher in building physics, reduced-order modelling, and scientific computing on GPUs (JAX, PyTorch, CuPy). Produce a design-oriented, source-cited report.

### Context
OpenUBEM is an open-source Python UBEM platform. For each building in a district (300–1,200 buildings; US DOE/ASHRAE and European TABULA archetypes) it already derives: footprint geometry, envelope areas by orientation, window areas and properties, constructions (U-values, thermal mass), dwelling zones, internal-gain and occupancy schedules, infiltration, HVAC family and setpoints, and EPW weather (ERA5 / TMYx). It then simulates each building with **EnergyPlus 23.1**, one CPU process per building.

The goal is an **optional fast tier**: a physics-based reduced-order model (ROM) that runs **thousands of buildings × many scenarios** (retrofits, climate years, setpoints) **simultaneously on a GPU**. It is calibrated against EnergyPlus, and EnergyPlus remains the reference. Hardware: Apple M2 Pro (Metal/MPS, no CUDA) for development, and a **Windows workstation with an NVIDIA CUDA GPU** for GPU runs (WSL2/Linux on that machine is possible if needed).

### Questions
1. **Model classes.** Compare candidate ROMs for annual hourly heating/cooling demand and energy use at building scale:
   - ISO 52016-1:2017 hourly method (and the ISO 13790 5R1C simple hourly method)
   - multi-node RC networks (e.g. 2R1C, 3R2C, 4R3C, per-orientation walls) and grey-box models
   - existing open-source implementations (e.g. ISO 52016 Python packages, CEA (City Energy Analyst) demand model, TEASER (RC from Modelica AixLib), RC_BuildingSimulator, PyBuildingEnergy, eppy/geomeppy-derived ROMs, etc.; verify they exist)
   For each: physics captured, inputs required, typical accuracy against EnergyPlus (EUI, peak loads, hourly CV(RMSE)), and limitations (HVAC detail, latent loads, multi-zone coupling, solar distribution, ground coupling).
2. **HVAC and energy use.** How do ROM studies turn loads into delivered or site energy for different HVAC families (efficiency curves, part-load ratios, heat pump COP vs outdoor temperature)? What is the accuracy loss compared with full E+ HVAC simulation?
3. **GPU batching.** Existing work that vectorises building thermal models across many buildings or scenarios on GPU/TPU. Implementation patterns: state-space discretisation (exact ZOH via matrix exponential vs explicit Euler), `jax.lax.scan` / `vmap`, PyTorch batched matmul, handling heterogeneous model sizes (padding/bucketing), handling thermostat/HVAC nonlinearity (deadband, capacity limits) without branching. Reported throughput (building-years per second) and hardware.
4. **Differentiable calibration.** Literature on calibrating RC/grey-box models to EnergyPlus or measured data using automatic differentiation (JAX/PyTorch), e.g. PNNL NeuroMANCER, physics-informed / differentiable building models, Bayesian calibration. Identifiability problems, and how much E+ training data per archetype is needed.
5. **Parameter derivation from IDF/geometry.** Methods to derive RC parameters automatically from an EnergyPlus IDF or from geometry plus construction data (e.g. VDI 6007, ISO 52016 node rules, TEASER's method). Recommend one for OpenUBEM.
6. **Framework choice.** JAX vs PyTorch vs CuPy vs Taichi vs Warp (NVIDIA) for this workload. Consider **native Windows + CUDA support** (e.g. JAX's CUDA builds are Linux-only and need WSL2 on Windows, while PyTorch supports CUDA on Windows natively; verify current status), Apple Silicon support (PyTorch MPS, jax-metal maturity, MLX), float32 vs float64 needs for stiff thermal ODEs, ecosystem, and long-term maintenance.
7. **Validation protocol.** How published ROM studies validate against detailed simulation. Recommended acceptance metrics and thresholds for a screening tier.

### Required output format
- **Executive summary** with a recommended model class + framework + calibration approach for OpenUBEM, and expected speedup vs E+ (with assumptions).
- **Table: ROM candidates**: model, physics, inputs, accuracy vs E+ (with citation), open-source implementation (URL, licence, maintained?), GPU-friendliness.
- **Table: GPU/batched implementations found**: URL/DOI, framework, throughput, hardware.
- **Reference architecture**: tensor shapes (buildings × nodes × timesteps), time-stepping scheme, how HVAC control is handled branch-free, calibration loop, a pseudo-code sketch.
- **Risks & limitations**, especially where a ROM will systematically diverge from E+ (many-zone dwellings, context shading, complex HVAC).
- **References**.

### Rules
- Cite everything; mark uncited `UNVERIFIED`. Verify that each named repo exists and give its last commit date.
- State precision (float32/float64) and hardware for every throughput number.
- Be explicit about fidelity loss; do not oversell.
