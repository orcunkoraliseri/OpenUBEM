# DR06 — GPU Acceleration of Urban Microclimate & Solar Geometry (SVF, Shadow, MRT, Irradiance)

**Feeds:** Phase 5 (Step 6 microclimate side track); possibly pre-computed shading for Phase 2/3
**Save output to:** `results/DR06_result.md`

---

## PROMPT

You are an expert in urban climatology computation, solar geometry, and GPU computing (CUDA, CuPy, JAX, PyTorch, OptiX/Embree ray tracing). Produce a source-cited technical report.

### Context
OpenUBEM (open-source Python UBEM) has an optional **Step 6 outdoor microclimate** module. It computes rasters over a neighbourhood domain from building massings (DSM-like height grids) and EPW/ERA5 hourly weather:
- sky-view factor (SVF), using horizon-angle scanning on a height raster
- hourly shadow masks (sun-position ray marching over the height grid)
- direct/diffuse/reflected shortwave and longwave fluxes → **mean radiant temperature (MRT)**
- thermal comfort indices **UTCI** and **PET**
- simple wind and air-temperature adjustments

It is implemented in NumPy (CPU) in modules `svf.py`, `shadow.py`, `solar.py`, `mrt.py`, `utci.py`. Domains are up to a few km² at ~1 m resolution; runs cover selected windows up to annual hourly. Development hardware is Apple M2 Pro (Metal/MPS, no CUDA); GPU runs will use a **Windows workstation with an NVIDIA CUDA GPU** (WSL2 possible).

Separately, the EnergyPlus models for the same buildings spend time on exterior shading from 20 m context buildings. GPU-precomputed shading or irradiance could be fed to EnergyPlus (e.g. via `Schedule:File` shading fractions or `SurfaceProperty:...` objects), so that is in scope as well.

### Questions
1. **Existing GPU tools.** GPU implementations of SVF / shadow casting / MRT / UTCI: e.g. SOLWEIG/UMEP (any GPU versions), Accelerad (GPU Radiance), Ladybug/Honeybee GPU options, PALM-4U radiation (GPU/OpenACC), ENVI-met, CityFFD, NVIDIA Warp/OptiX-based solar tools, pvlib-adjacent GPU projects, SEBE. For each: URL, licence, maturity, speedup vs CPU reference, accuracy.
2. **Algorithms.** Best GPU-suited algorithms for: SVF on a raster (horizon scanning vs ray casting vs hemispherical sampling), shadow volumes vs ray marching on DSMs, view-factor computation for building surfaces, and irradiance with reflections (Radiance-style). Complexity and memory for km²-scale domains at 1 m.
3. **Framework fit.** CuPy (NumPy drop-in), JAX, PyTorch (incl. MPS on Mac), Numba CUDA, Taichi, NVIDIA Warp, Mitsuba/OptiX/Embree for ray tracing. Which allows a single code path for Apple Silicon (macOS) and NVIDIA on **Windows** (native vs WSL2 support for each)? The Python array API standard as a portability layer.
4. **E+ coupling.** Published workflows that compute exterior shading or incident irradiance outside EnergyPlus (Radiance, ray tracers, GPU) and feed it back into E+ (e.g. `Schedule:File` shading fractions, `SurfaceProperty:LocalEnvironment`, `SurfaceProperty:IncidentSolarMultiplier`, external shading calculation method `ImportedShading`/"Scheduled"). Accuracy and runtime impact on E+.
5. **Recommendation** for porting OpenUBEM Step 6 hotspots and, optionally, a GPU shading precompute for EnergyPlus.

### Required output format
- **Executive summary** with recommended framework and algorithm per component.
- **Table: tools/repos**: name, URL, what it computes, GPU backend, licence, last activity, speedup evidence.
- **Table: algorithms**: component, algorithm, complexity, GPU suitability, accuracy notes, source.
- **E+ coupling dossier**: relevant IDF objects (E+ 23.1 field names), workflow, pitfalls.
- **References**.

### Rules
- Cite everything; mark uncited `UNVERIFIED`. Verify repos exist; give last-commit dates.
- Separate measured speedups (hardware + baseline) from claims.
