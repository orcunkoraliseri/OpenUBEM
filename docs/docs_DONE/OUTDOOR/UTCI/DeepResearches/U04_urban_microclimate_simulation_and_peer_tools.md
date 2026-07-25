# Deep-Research Report U04 — URBAN MICROCLIMATE SIMULATION ENGINES & PEER TOOL BENCHMARKING

> **Executive Summary & Scope Alignment**: This document delivers a comprehensive architectural appraisal and technical benchmark of peer microclimate simulation software engines and open-source frameworks used to model outdoor microclimates and calculate spatial Universal Thermal Climate Index (UTCI). Grounded in peer-reviewed validation studies (*Bruse & Fleer 1998, Lindberg et al. 2008/2018, Matzarakis et al. 2007/2010, Roudsari et al. 2013, Kämpf & Robinson 2007, Maronga et al. 2015/2020*), this report evaluates ENVI-met, SOLWEIG, Ladybug Tools, RayMan, CitySim, and PALM-4U across governing physics, computational scalability, input/output data formats, and multi-scale coupling strategies for **OpenUBEM**.

---

## 1. Required Output Tables

### Table 1 — Peer Microclimate Software Engines Catalogue

| Engine / Tool | Primary Developer / Inst. | Microclimate Physics Model (CFD, Ray-tracing, Empirical) | Primary Purpose / Output Metrics | UTCI Calculation Native? | Software License | Source |
|---|---|---|---|---|---|---|
| **ENVI-met** | ENVI-met GmbH / Michael Bruse | 3D non-hydrostatic CFD ($k-\epsilon$ turbulence model) + 3D plant canopy drag model + surface energy balance with explicit soil/building thermal inertia | High-resolution 3D urban microclimate ($T_a, v, q, T_{mrt}, T_{surf}$) and micro-scale air quality mapping | Yes (via integrated Biomet module / direct UTCI output) | Commercial / Proprietary (Free basic version available with grid limits) | Bruse & Fleer (1998), Huttner & Bruse (2009) |
| **SOLWEIG** | Univ. of Gothenburg (Fredrik Lindberg et al.) | 2.5D radiation geometry + 3D shadow casting algorithm + empirical wall/sky view factor calculation | High-speed spatial $T_{mrt}$ & UTCI mapping across complex urban raster domains | Yes (Native core output via built-in UTCI polynomial solver) | Open Source (GNU GPL v3) | Lindberg et al. (2008, 2018) |
| **Ladybug Tools (Ladybug / Dragonfly)** | Ladybug Tools LLC (Mostapha Sadeghipour Roudsari, Chris Mackey) | Radiance backwards ray-tracing + EnergyPlus building heat balance / Urban Weather Generator (UWG) coupling | Environmental building design, urban canyon thermal comfort, & microclimate modeling workflows | Yes (`ladybug_comfort.utci` module / Native components) | Open Source (GNU GPL v3 / AGPL) | Roudsari et al. (2013), Mackey et al. (2017) |
| **RayMan** | Univ. of Freiburg (Andreas Matzarakis et al.) | Point-based radiation balance model + fisheye photography canopy geometry + shortwave/longwave flux solver | Single-point microclimate analysis & human biometeorological thermal indices ($T_{mrt}$, PET, UTCI, SET*) | Yes (Point analysis via Biomet interface) | Free Academic / Proprietary Freeware | Matzarakis et al. (2007, 2010) |
| **CitySim** | EPFL (Jérôme Kämpf & Darren Robinson) | 3D simplified radiation exchange model (simplified radiosity algorithm) + simplified urban canopy flow model | Urban building energy modeling (UBEM), exterior surface temperatures, & district energy demands | Limited / Via export (Computes exterior surface $T$ & irradiance; UTCI computed via external script) | Open Source (GNU GPL v3) | Kämpf & Robinson (2007), Robinson et al. (2009) |
| **PALM-4U** | Leibniz Univ. Hannover / DWD (Siegfried Raasch, Björn Maronga et al.) | 3D Large-Eddy Simulation (LES) / Reynolds-Averaged Navier-Stokes (RANS) atmospheric boundary layer model + 3D urban surface model (USM) | City-scale atmospheric turbulence, urban heat island dynamics, air quality, & human thermal comfort mapping | Yes (via integrated Maronga et al. biometeorology module) | Open Source (GNU GPL v3) | Maronga et al. (2015, 2020), Khan et al. (2021) |

---

### Table 2 — Input/Output Data Exchange & Mesh Formats

| Engine / Tool | Required Geometry Format | Meteorological Input Format | Vegetation / Surface Material Format | Output Spatial Data Format | Source |
|---|---|---|---|---|---|
| **ENVI-met** | 3D Area Input File (`.INX` / `.INPX` XML-based structured 3D grid) | EnergyPlus Weather File (`.EPW`) / Full boundary forcing text file (`.EBF` / `.DAT`) | Internal material database (`database.xml`) & 3D plant canopy database (`plants.xml`) | Proprietary binary grid (`.EDX/.EDI`), NetCDF4 (`.nc`), ASCII grid | Bruse & Fleer (1998), ENVI-met Manual (2023) |
| **SOLWEIG** | 2D/2.5D Raster DEM/DSM (Digital Elevation Model / Digital Surface Model in GeoTIFF / ASCII grid) | Meteorological text file (`.txt` formatted with $T_a, RH, K_{down}, D_{down}, I_{dir}, v$) / `.EPW` | Land cover raster (Canopy DEM `CDSM` / Trunk Zone DEM `TDSM` + Albedo/Emissivity lookup grid) | GeoTIFF spatial raster grids (`.tif`), ASCII grid (`.asc`), spatial NumPy arrays | Lindberg et al. (2008, 2018) |
| **Ladybug Tools** | Rhino 3D NURBS/Mesh Geometry, Honeybee JSON (`.hbjson`), Dragonfly JSON (`.dfjson`) | EnergyPlus Weather File (`.EPW`), STAT weather file | EnergyPlus Construction & Material Definitions, Radiance Material Modifiers (`.mat`) | Ladybug Data Collections, VTK (`.vtk`), CSV / Pandas DataFrames, HDF5 | Roudsari et al. (2013), Mackey et al. (2017) |
| **RayMan** | Single-point obstacle file (`.obs`), hemispherical fisheye image (`.jpg`/`.bmp`), or free-horizon elevation profile | Meteorological text table (`.txt`/`.csv` with timestamp, $T_a, RH, v, K_{down}$) | Surface albedo, emissivity, & obstacle obstruction angle tables | Text tabular report (`.txt`), single-point tabular export, graphics export (`.wmf`) | Matzarakis et al. (2007, 2010) |

---

### Table 3 — Computational Performance & City-Scale Scalability

| Engine / Tool | Spatial Grid Resolution | Typical Domain Size | Execution Time (24-hr simulation) | Parallelization Support (CPU/GPU) | City-Scale Viability (10,000+ buildings) | Source |
|---|---|---|---|---|---|---|
| **ENVI-met** | $0.5 - 2.0\text{ m}$ (structured 3D Cartesian mesh) | $100 \times 100 \times 30$ to $250 \times 250 \times 40$ cells ($0.05 - 0.25\text{ km}^2$) | 6 - 24 hours (depending on grid size & CFD sub-iterations) | Multi-core CPU (OpenMP shared memory); No GPU acceleration | Very Low (Micro-scale focus only; computationally intractable for city-scale domains) | Huttner & Bruse (2009), Tsoka et al. (2018) |
| **SOLWEIG** | $1.0 - 5.0\text{ m}$ (2.5D spatial raster grid) | District to City-Scale ($2 \times 2\text{ km}$ to $10 \times 10\text{ km}$) | 2 - 15 minutes (for a $1000 \times 1000$ grid cell domain) | Multi-core CPU (Python multiprocessing / NumPy vectorized operations) / Experimental GPU CUDA rasterization | High (Ultra-fast 2.5D shadow casting & vectorized 6-directional radiation solver; ideal for whole-city spatial raster mapping) | Lindberg et al. (2018), Wallenberg et al. (2020) |
| **Ladybug Tools** | Discrete sensor test points ($1.0 - 5.0\text{ m}$ point grid) | Building to District scale ($500 \times 500\text{ m}$) | 10 - 60 minutes (depending on Radiance ray count and EnergyPlus simulation steps) | Multi-processor parallel ray-tracing (Radiance `rtrace` multi-core CPU) | Moderate (Viable for sample districts via Dragonfly decomposition; heavy memory footprint for large point grids) | Mackey et al. (2017), Roudsari et al. (2013) |
| **PALM-4U** | $1.0 - 10.0\text{ m}$ (3D nested Cartesian grid) | Whole City ($10 \times 10\text{ km}$ to $30 \times 30\text{ km}$) | 12 - 48 hours (on High-Performance Computing clusters) | High-Performance HPC (MPI domain decomposition + OpenMP hybrid parallelization) | High (Highly viable, but strictly requires HPC supercomputing clusters & large memory bandwidth) | Maronga et al. (2015, 2020), Resler et al. (2017) |

---

### Table 4 — OpenUBEM Coupling Strategies & Fit Assessment

| Coupling Approach | Target Microclimate Tool | Data Flow Mechanism | Strengths | Weaknesses / Limitations | Final Architectural Verdict |
|---|---|---|---|---|---|
| **Offline One-Way Coupling** | SOLWEIG (via GeoTIFF grids / UMEM toolbox) | OpenUBEM exports building footprint + height rasters (DSM/DEM) $\to$ SOLWEIG generates spatial $T_{mrt}$ and UTCI GeoTIFF grids using EPW forcing weather data. | Ultra-fast, highly decoupled, scalable to 100,000+ buildings across entire metropolitan regions; simple file-based data pipeline. | Ignores dynamic building surface heat rejection ($Q_{wall}, Q_{roof}$) and anthropogenic HVAC waste heat feedback onto ambient air temperature ($T_a$). | **Recommended Primary GIS Pipeline** |
| **Dynamic Two-Way Coupling** | ENVI-met or UWG (Urban Weather Generator) / PALM-4U | OpenUBEM passes dynamic hourly wall/roof surface temperatures ($T_{wall}$) and HVAC reject heat ($Q_{HVAC}$) $\leftrightarrow$ Microclimate engine updates localized 3D air temperature ($T_a$), relative humidity ($RH$), and wind speed ($v$) fields for OpenUBEM. | Highest physical fidelity; captures urban heat island microclimate feedback loops, building heat discharge, and canopy air circulation. | Massive computational burden; high memory overhead; difficult execution control across multi-thousand building domains. | **Research & Validation Tier Only** |
| **Native Embedded Fast Solver** | Internal OpenUBEM Python/C++ Microclimate Module (Native Ray-tracing + SVF Raster Kernel) | OpenUBEM computes building sky view factor (SVF) matrices and shortwave/longwave 6-direction flux balance directly in-memory alongside building thermal load solvers. | Zero external software binary dependencies; seamless memory coupling with UBEM data structures; ultra-fast parallel execution on C++ / GPU backends. | Requires custom implementation and validation of 3D spatial shadow casting and vegetation shortwave transmission routines. | **Recommended Future Production Feature** |

---

## 2. Part C — Synthesis (Software Engine Recommendation for OpenUBEM)

### 2.1 Single Most Viable Open-Source Engine Selection for OpenUBEM

Based on an empirical trade-off analysis between microclimate physical fidelity, execution speed, data interchange formats, and municipal-scale computational scalability, **SOLWEIG (Solar and Long Wave Environmental Irradiance Geometry model)** is selected as the primary external microclimate engine for **OpenUBEM**.

**Key Architectural Justifications:**
1. **Computational Speed and Raster Scalability**: SOLWEIG evaluates mean radiant temperature ($T_{mrt}$) and UTCI on continuous 2.5D spatial raster grids using optimized 3D shadow-casting algorithms and fast 6-direction radiant flux balances. It processes a $1\text{ km} \times 1\text{ km}$ urban district at $1\text{ m}$ spatial resolution ($1,000,000$ grid cells) in under 5 minutes for a 24-hour simulation, compared to 12–24 hours in ENVI-met.
2. **GIS-Native Data Pipelines**: SOLWEIG natively operates on GeoTIFF Digital Elevation Models (DEM), Digital Surface Models (DSM), and Canopy Digital Surface Models (CDSM). This aligns perfectly with OpenUBEM's spatial GIS architecture (GDAL, GeoPandas, Rasterio).
3. **Validated Biometeorological Accuracy**: Extensive validation studies (*Lindberg et al. 2008, 2018*) demonstrate that SOLWEIG predicts $T_{mrt}$ under clear-sky conditions with an root-mean-square error (RMSE) of $2.5 - 4.2^\circ\text{C}$ ($R^2 > 0.92$) compared to field radiometer measurements.
4. **Open-Source License & Python Accessibility**: As part of the UMEP (Urban Multi-scale Environmental Predictor) suite under GNU GPL v3, SOLWEIG's Python codebase can be directly invoked via API bindings or headless script execution within OpenUBEM's execution workflow.

---

### 2.2 Technical Evaluation: SOLWEIG vs. Ladybug Tools for Large-Scale Urban Raster Grid Execution

| Architectural Criterion | SOLWEIG (UMEP / Raster Engine) | Ladybug Tools (Ladybug + Radiance Engine) | OpenUBEM Comparative Assessment |
|---|---|---|---|
| **Underlying Ray/Radiation Geometry Engine** | 2.5D Raster shadow casting + 6-direction flux balance ($K_{up}, K_{down}, K_{side}, L_{up}, L_{down}, L_{side}$) | Radiance 3D backward Monte Carlo ray-tracing | **SOLWEIG** avoids 3D ray intersection overhead across millions of pixels, enabling dense spatial grid execution. |
| **Spatial Grid & Data Representation** | Continuous 2.5D GeoTIFF raster arrays | Discrete 3D sensor point grids (vector points) | **SOLWEIG** natively outputs spatially continuous maps; **Ladybug** requires spatial interpolation post-processing. |
| **Vegetation Canopy Representation** | Explicit 3D Canopy height raster (`CDSM`) + Trunk zone height (`TDSM`) + Leaf Area Index (LAI) / Transmissivity ($\psi$) | Radiance translucent material modifiers / Mesh geometries | **SOLWEIG** efficiently models seasonal leaf-on / leaf-off transmittance and trunk space solar penetration without complex 3D CAD geometry creation. |
| **Memory & Process Footprint** | Low ($< 1.5\text{ GB}$ RAM for $2\text{ km} \times 2\text{ km}$ grid) | High ($> 16\text{ GB}$ RAM for large sensor grids due to Radiance process memory) | **SOLWEIG** can run concurrently on standard server nodes; **Ladybug** hits memory bottlenecks on dense urban domains. |
| **Execution Bottleneck** | Raster shadow-casting iterations over solar position angles | Radiance `rtrace` sub-processes & EnergyPlus JSON file I/O | **SOLWEIG** execution time scales linearly with grid pixel count $\mathcal{O}(N)$; **Ladybug** scales non-linearly with scene polygon count and ray bounces $\mathcal{O}(N \log M)$. |

---

### 2.3 Proposed Data Coupling Pipeline & Architecture Workflow

To seamlessly connect OpenUBEM building geometry and thermal output with the SOLWEIG microclimate engine, OpenUBEM implements an automated 4-stage data coupling pipeline:

```mermaid
flowchart TD
    subgraph Input_Layer ["1. Input Data Layer"]
        GIS["GIS Building Footprints & Heights (GeoJSON / CityJSON)"]
        LiDAR["LiDAR Elevation Data (DEM / DSM GeoTIFF)"]
        EPW["EnergyPlus Weather File (.EPW)"]
        Veg["Urban Tree Canopy & Land Cover Rasters"]
    end

    subgraph OpenUBEM_Core ["2. OpenUBEM Geometry & Urban Thermal Pre-Processor"]
        GeoEngine["OpenUBEM Spatial Rasterizer"]
        EnergyEngine["EnergyPlus / UBEM Thermal Load Solver"]
        GeoEngine --> GroundDEM["Ground DEM (GeoTIFF)"]
        GeoEngine --> BuildingDSM["Building DSM (GeoTIFF)"]
        GeoEngine --> CanopyDSM["Canopy CDSM & TDSM (GeoTIFF)"]
        EnergyEngine --> WallTemp["Dynamic Wall Surface Temp (T_wall)"]
    end

    subgraph Microclimate_Engine ["3. Microclimate Engine (SOLWEIG / UMEM Solver)"]
        SVF["Sky View Factor (SVF) Raster Solver"]
        Shadow["3D Shadow Casting Algorithm (Solar Azimuth/Zenith)"]
        FluxSolver["6-Direction Shortwave & Longwave Radiant Flux Engine"]
        UTCI_Calc["UTCI Operational Polynomial Routine (Bröde et al. 2012)"]
        
        SVF --> FluxSolver
        Shadow --> FluxSolver
        FluxSolver --> TmrtMap["Hourly T_mrt Spatial Raster Grid"]
        TmrtMap --> UTCI_Calc
    end

    subgraph Output_Layer ["4. OpenUBEM Spatial Thermal Risk Analytics"]
        UTCI_GeoTIFF["Hourly & Peak UTCI GeoTIFF Grids"]
        ExposureIndex["Pedestrian Thermal Vulnerability Mapping"]
        MitigationSim["UHI Mitigation Planning (Cool Roofs / Tree Canopy Optimization)"]
    end

    GIS --> GeoEngine
    LiDAR --> GeoEngine
    Veg --> GeoEngine
    EPW --> EnergyEngine
    EPW --> FluxSolver

    GroundDEM --> SVF
    BuildingDSM --> SVF
    CanopyDSM --> SVF

    GroundDEM --> Shadow
    BuildingDSM --> Shadow
    CanopyDSM --> Shadow

    UTCI_Calc --> UTCI_GeoTIFF
    UTCI_GeoTIFF --> ExposureIndex
    UTCI_GeoTIFF --> MitigationSim
```

---

## 3. Confidence & Caveats

1. **CFD vs. Empirical/2.5D Radiation Trade-off**:
   - SOLWEIG assumes a uniform or simplified downscaled wind velocity field ($v_{1.1m}$) across the canopy domain. In deep urban canyons or complex high-rise clusters, localized CFD wind acceleration (venturi effects, corner vortices) significantly affects convective heat exchange. When precise wind field microclimates are required, OpenUBEM must couple SOLWEIG with a fast CFD downscaling model (such as OpenFOAM or UrbaWind).
2. **Dynamic Building Surface Heat Rejection ($Q_{wall}$)**:
   - Standard offline one-way coupling assumes building exterior wall surfaces are at ambient air temperature ($T_{wall} \approx T_a$). In heavy masonry urban canyons, nighttime longwave radiation from sun-heated building facades elevates ambient $T_{mrt}$ by $2.0 - 4.5^\circ\text{C}$. Integrating OpenUBEM's dynamic exterior surface temperatures ($T_{wall}$) into SOLWEIG's longwave flux balance ($L_{side}$) resolves this boundary condition gap.
3. **LiDAR & Vegetation Data Quality**:
   - SOLWEIG raster calculations depend heavily on accurate high-resolution LiDAR Digital Surface Models (DSM) and Canopy Height Models (CHM). Incomplete, noisy, or outdated vegetation rasters directly distort shortwave shadow projections and radiant flux predictions.

---

## 4. Reference List

1. Bruse, M., & Fleer, H. (1998). Simulating surface–plant–air interactions inside urban environments with a three-dimensional numerical model. *Environmental Modelling & Software*, 13(3-4), 373-384. https://doi.org/10.1016/S1364-8152(98)00042-5
2. Lindberg, F., Holmer, B., & Thorsson, S. (2008). SOLWEIG 1.0 – Modelling spatial variations of 3D radiant fluxes and mean radiant temperature in complex urban settings. *International Journal of Biometeorology*, 52(7), 697-713. https://doi.org/10.1007/s00484-008-0162-7
3. Lindberg, F., Grimmond, C. S. B., Gabey, A., Huang, B., Kent, C. W., Sun, T., ... & Wallenberg, N. (2018). Urban Multi-scale Environmental Predictor (UMEP): An integrated tool for urban climatology applications. *Environmental Modelling & Software*, 99, 70-87. https://doi.org/10.1016/j.envsoft.2017.09.020
4. Matzarakis, A., Rutz, F., & Mayer, H. (2007). Modelling radiation flux densities in thermal biometeorology—taking RayMan as an example. *International Journal of Biometeorology*, 51(4), 323-338. https://doi.org/10.1007/s00484-006-0061-8
5. Matzarakis, A., Rutz, F., & Mayer, H. (2010). Modelling radiation flux densities in thermal biometeorology—application of RayMan model. *International Journal of Biometeorology*, 54(2), 131-141. https://doi.org/10.1007/s00484-009-0261-0
6. Roudsari, M. S., Pak, M., & Smith, A. (2013). Ladybug: a parametric environmental plugin for grasshopper to help designers create an environmentally-conscious design. *Proceedings of the 13th International IBPSA Conference*, Chambéry, France, 3128-3135.
7. Kämpf, J. H., & Robinson, D. (2007). A simplified thermal model to support the design of low energy cities. *Energy and Buildings*, 39(4), 445-453. https://doi.org/10.1016/j.enbuild.2006.09.002
8. Maronga, B., Gryschka, M., Heinze, R., Hoffmann, F., Kanani-Sühring, F., Keck, M., ... & Raasch, S. (2015). The Large-Eddy Simulation Model PALM 4.0: Overview and Recent Developments. *Geoscientific Model Development*, 8(8), 2515-2551. https://doi.org/10.5194/gmd-8-2515-2015
9. Maronga, B., Banzhaf, S., Burmeister, C., Esch, T., Forkel, R., Fröhlich, D., ... & Raasch, S. (2020). Overview of the PALM model system 6.0. *Geoscientific Model Development*, 13(3), 1335-1372. https://doi.org/10.5194/gmd-13-1335-2020
10. Huttner, S., & Bruse, M. (2009). Numerical modeling of the urban climate - a preview on ENVI-met v4. *Proceedings of the 7th International Conference on Urban Climate*, Yokohama, Japan.
11. Robinson, D., Haldi, F., Kämpf, J., Leroux, P., Perez, D., Rasheed, A., & Wilke, U. (2009). CitySim: Comprehensive micro-simulation of resource flows for sustainable urban planning. *Proceedings of the 11th IBPSA Conference*, Glasgow, Scotland, 1083-1090.
12. Mackey, C., Galanos, T., & Sadeghipour Roudsari, M. (2017). Dragonfly: A tool for modeling large-scale urban microclimates. *Proceedings of Building Simulation 2017*, San Francisco, CA.
