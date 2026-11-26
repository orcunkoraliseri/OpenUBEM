# DR02 — EnergyPlus Runtime Anatomy, PixelCounting (GPU Shading) & Speed Settings

**Feeds:** Phase 0 (profiling design), Phase 1C (numerics), Phase 2 (PixelCounting)
**Save output to:** `results/DR02_result.md`

---

## PROMPT

You are an expert in EnergyPlus internals and simulation performance tuning. Produce a technical, source-cited report.

### Context
My platform (OpenUBEM) runs **EnergyPlus 23.1** once per building (CLI: `energyplus -w EPW -d DIR -x -r in.idf`; `-x` runs ExpandObjects for HVACTemplate objects, `-r` runs ReadVarsESO). The IDFs have:
- `Timestep, 6;`, annual RunPeriod, `Building` Solar Distribution = `FullExterior`
- **no `ShadowCalculation` object** (so E+ defaults apply)
- real footprint geometry, dwelling-level zones (many buildings 20–340 zones), detailed context: neighbouring buildings within 20 m as `Shading:Building:Detailed` / `Shading:Site:Detailed` surfaces
- HVACTemplate systems across ~10 families (VAV, fan coils, heat pumps, …)
- outputs mostly RunPeriod meters to SQLite, optional hourly zone variables

Runtime distribution: median 3.2 s, p99 233 s, max 907 s per building (Apple M2 Pro, 1 thread each). Available hardware: the M2 Pro (macOS) and a **Windows workstation with an NVIDIA CUDA GPU**. I want to know **where the time goes** and **which settings or features cut it, with what accuracy cost**, including the GPU-based `PixelCounting` shading method.

### Questions
1. **Runtime anatomy.** What does the literature and NREL documentation say about how E+ runtime splits across: shading/sun-position calculations, interior solar distribution, surface heat balance / CTF, zone air heat balance, HVAC system/plant iteration, warm-up days, sizing runs, and output writing (ESO/SQL/ReadVars)? How does runtime scale with zone count, surface count, and shading-surface count (linear? quadratic in shading surfaces)? Cite benchmark studies.
2. **Profiling E+.** Practical ways to profile a run: built-in timing reports (e.g. the `eplusout.err` timing summary, `Output:Diagnostics` options, "DisplayExtraWarnings", the timers/`--debug` build options), and external profilers (perf, VTune, Instruments). What is a fair, reproducible way to estimate the *shading share* of runtime?
3. **PixelCounting / Penumbra.**
   - Which E+ version introduced it, and how is it configured (`ShadowCalculation` fields: method, update frequency method/period, pixel counting resolution, maximum figures, polygon clipping algorithm, sky diffuse modelling)?
   - Hardware/software requirements: OpenGL version, does it work **headless** on Linux HPC (EGL/OSMesa/Xvfb), on macOS (OpenGL 4.1 deprecated), on Windows with an NVIDIA GPU (our target: does the official Windows E+ 23.1 build use the discrete GPU, and how do we confirm it did)? What happens if no GPU is available (silent fallback to PolygonClipping? warning text?)
   - Published speed and accuracy results versus PolygonClipping, especially for many shading surfaces. Known bugs or limitations (e.g. interaction with `FullInteriorAndExterior`, non-convex surfaces, timestep shading).
   - The Penumbra library itself (bigladder/penumbra): maturity, licence, maintenance.
4. **Other speed levers, with accuracy impact.** Quantify (with sources) the effect of: timestep (6 vs 4 vs 2), `ShadowCalculation` update frequency (periodic 20 days vs other), `Maximum Figures in Shadow Overlap Calculations`, `Solar Distribution` options, `SimulationControl` (sizing periods, `Do HVAC Sizing Simulation for Sizing Periods`), warm-up day limits and convergence tolerances, `ZoneAirHeatBalanceAlgorithm` (ThirdOrderBackwardDifference vs AnalyticalSolution vs EulerMethod), `HeatBalanceAlgorithm`, `Zone Multiplier` / `ZoneList` multipliers for identical floors, geometry simplification (merging coplanar surfaces, shading surface reduction / transmittance), `Output:SQLite` vs ESO, skipping ReadVarsESO, ExpandObjects precompute vs runtime.
5. **Version performance.** Documented runtime improvements from E+ 23.1 → newer releases (24.x, 25.x and any later). Release-note citations.
6. **In-process API.** Does running via `pyenergyplus` (EnergyPlus Python API, `run_energyplus` in-process, state reuse) reduce overhead versus spawning a process? Is reusing state across buildings possible?

### Required output format
- **Executive summary** with a ranked list of levers: lever, expected speedup range, accuracy risk, evidence quality.
- **Table: E+ settings**: object/field, value options, speed effect, accuracy effect, source.
- **PixelCounting dossier**: config snippet (IDF text for E+ 23.1), requirements, headless recipe, fallback behaviour, known issues, benchmarks.
- **Profiling recipe**: concrete steps to measure the shading share and per-module time on macOS and Linux.
- **References** list.

### Rules
- Cite every claim (EnergyPlus I/O Reference, Engineering Reference, GitHub issues/PRs, papers). Mark uncited claims `UNVERIFIED`.
- Give IDF field names exactly as in the E+ 23.1 IDD where possible, and flag fields that changed between versions.
- Distinguish measured vs claimed effects, and state the test building or model size for each number.
