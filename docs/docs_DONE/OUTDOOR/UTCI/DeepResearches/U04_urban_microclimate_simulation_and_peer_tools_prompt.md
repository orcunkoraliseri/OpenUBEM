# Deep-Research Prompt U04 — URBAN MICROCLIMATE SIMULATION ENGINES & PEER TOOL BENCHMARKING

> SCOPE GUARD — READ FIRST. This prompt delivers a rigorous comparative benchmark of **peer microclimate simulation software engines** and open-source frameworks used to model outdoor microclimates and calculate UTCI. Software covered includes ENVI-met, Ladybug Tools (Ladybug/Honeybee/Dragonfly), SOLWEIG, RayMan, CitySim, and PALM. Do NOT cover basic physiological definitions (`U01`), manual MRT physics (`U03`), or raw code implementations (`U05`). See `00_README_utci_prompt_set.md`.

---

## What this document is

A software engine & peer-tool architectural appraisal. As illustrated in `docs/examples/UTCI/1784462193769.jpg`, high-performance urban microclimate design relies on specialized simulation tools to compute spatial distribution maps of wind speed, air temperature, relative humidity, mean radiant temperature, and UTCI. This prompt evaluates how peer tools model urban microclimates, their computational scalability, data interchange formats, and how OpenUBEM should interface with or incorporate these microclimate engines.

## Role

Urban microclimate software architect & simulation engine specialist. Ground engine capabilities, governing physical equations, input requirements, and performance characteristics in official tool documentation and peer-reviewed validation studies (Bruse & Fleer 1998; Roudsari et al. 2013; Lindberg et al. 2008, 2018; Matzarakis et al. 2007, 2010; Kämpf & Robinson 2007; Maronga et al. 2015, 2020).

## Why this matters (so you scope correctly)

UBEM engines (like EnergyPlus or OpenStudio) traditionally simulate building thermal loads assuming uniform, macro-scale EPW weather inputs. However, outdoor microclimates are heavily modified by building massing, wall surface heat rejection, and vegetation. To deliver spatial UTCI maps, OpenUBEM must either couple with external microclimate engines (like SOLWEIG or ENVI-met) or execute an internal fast-approximation microclimate solver. Understanding peer tool trade-offs is essential for this architectural decision.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Peer Microclimate Software Engines Catalogue

| Engine / Tool | Primary Developer / Inst. | Microclimate Physics Model (CFD, Ray-tracing, Empirical) | Primary Purpose / Output Metrics | UTCI Calculation Native? | Software License | Source |
|---|---|---|---|---|---|---|
| ENVI-met | ENVI-met GmbH / Bruse | 3D non-hydrostatic CFD + plant canopy + surface energy balance | High-resolution 3D urban microclimate | Yes (via Biomet module) | Commercial / Proprietary |  |
| SOLWEIG | Univ. of Gothenburg (Lindberg) | 2.5D radiation geometry + 3D shadow casting | High-speed spatial $T_{mrt}$ & UTCI mapping | Yes (Native core output) | Open Source (GPL) |  |
| Ladybug Tools (Ladybug / Dragonfly) | Ladybug Tools LLC (Roudsari) | Radiance ray-tracing + EnergyPlus / UWG coupling | Environmental design & thermal comfort | Yes (`ladybug_comfort.utci`) | Open Source (GPL) |  |
| RayMan | Univ. of Freiburg (Matzarakis) | Point-based radiation balance + fisheye canopy | Single-point microclimate & PET/UTCI | Yes (Point analysis) | Free Academic |  |
| CitySim | EPFL (Kämpf & Robinson) | 3D radiation exchange + simplified canopy flow | Urban building energy + microclimate | Limited / Via export | Open Source |  |
| PALM-4U | Leibniz Univ. Hannover | 3D Large-Eddy Simulation (LES) atmospheric model | City-scale atmospheric boundary layer | Yes (via Maronga et al.) | Open Source (GNU) |  |

### Table 2 — Input/Output Data Exchange & Mesh Formats

| Engine / Tool | Required Geometry Format | Meteorological Input Format | Vegetation / Surface Material Format | Output Spatial Data Format | Source |
|---|---|---|---|---|---|
| ENVI-met | 3D Area Input File (`.INX` / `.INPX`) | `.EPW` / Forced boundary conditions | Internal material & plant databases | `.EDX/.EDI` / NetCDF |  |
| SOLWEIG | 2D/2.5D Raster DEM/DSM (GeoTIFF) | Meteorological text file (`.txt`) / EPW | Land cover raster + Tree canopy DEM | GeoTIFF spatial raster grids |  |
| Ladybug Tools | Rhino 3D Geometry / Honeybee Model | `.EPW` weather file | EnergyPlus construction & vegetation | Data collections / VTK / DataFrames |  |
| RayMan | Obstacle file / Fisheye image | Meteorological text table | Surface albedo & obstruction angles | Text report / Point tables |  |

### Table 3 — Computational Performance & City-Scale Scalability

| Engine / Tool | Spatial Grid Resolution | Typical Domain Size | Execution Time (24-hr simulation) | Parallelization Support (CPU/GPU) | City-Scale Viability (10,000+ buildings) | Source |
|---|---|---|---|---|---|
| ENVI-met | $0.5 - 2.0\text{ m}$ | $100 \times 100 \times 30$ cells | 6 - 24 hours | Multi-core CPU | Very Low (Micro-scale only) |  |
| SOLWEIG | $1.0 - 5.0\text{ m}$ | City district ($2 \times 2\text{ km}$) | 2 - 15 minutes | Multi-core CPU / Python numpy | High (Rapid raster solver) |  |
| Ladybug Tools | Spatial points ($1 - 5\text{ m}$) | District scale ($500\text{ m}$) | 10 - 60 minutes | Multi-processor ray tracing | Moderate |  |
| PALM-4U | $1.0 - 10.0\text{ m}$ | Whole city ($10 \times 10\text{ km}$) | 12 - 48 hours | High-Performance HPC (MPI/OpenMP) | High (HPC required) |  |

### Table 4 — OpenUBEM Coupling Strategies & Fit Assessment

| Coupling Approach | Target Microclimate Tool | Data Flow Mechanism | Strengths | Weaknesses / Limitations | Final Architectural Verdict |
|---|---|---|---|---|---|
| Offline One-Way Coupling | SOLWEIG (via GeoTIFF grids) | OpenUBEM exports footprint/height rasters $\to$ SOLWEIG generates $T_{mrt}$ grids | Fast, decoupled, scalable to whole cities | Ignores dynamic building surface heat release | Recommended Primary GIS Pipeline |
| Dynamic Two-Way Coupling | ENVI-met or UWG | OpenUBEM surface $T_{wall}$ $\leftrightarrow$ Microclimate air $T_a, v$ | High physical fidelity | Massive computational cost; non-viable at scale | Research / Validation Tier Only |
| Native Embedded Fast Solver | Internal Python/C++ Module | OpenUBEM computes SVF + 6-direction radiation directly in-memory | Zero external software dependency, ultra-fast | Requires custom implementation of spatial ray-tracing | Future Production Feature |

---

## Part C — Synthesis (Software Engine Recommendation for OpenUBEM)

Give:
1. An evidence-based selection of the single most viable open-source microclimate engine for OpenUBEM to integrate for automated spatial UTCI generation.
2. A technical evaluation of SOLWEIG vs. Ladybug Tools for large-scale urban raster grid execution.
3. A proposed data coupling pipeline specifying how geometry, land cover, and weather data flow between OpenUBEM and the microclimate engine.

## Output Format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C synthesis.
3. Include clear architectural workflow diagrams or structured schemas.
4. **"Confidence and caveats":** address execution bottlenecks and resolution limitations.
5. **Reference list** — complete citations with DOIs.

## Hard Requirements

- **Populate every cell in Tables 1–4.**
- **Compare execution time and grid scale explicitly.**
- **Provide a clear architectural decision for OpenUBEM integration.**
