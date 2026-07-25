# Outdoor Thermal Comfort & UTCI Microclimate Analysis — Deep-Research Prompt Set (INDEX)

> READ FIRST. This prompt set addresses the theoretical, computational, and spatial methodologies for calculating, mapping, and integrating the **Universal Thermal Climate Index (UTCI)** within Urban Building Energy Modeling (UBEM) and high-performance urban microclimate design. Grounded in biometeorological literature, thermal comfort standards (ISO 7730, ASHRAE 55, COST Action 730), and spatial microclimate field analysis, this prompt set guides deep research to establish an auditable, high-resolution UTCI calculation and mapping pipeline for OpenUBEM.

---

## Visual & Conceptual Anchor (Reference Artifacts)

This prompt set directly operationalizes the microclimate physics, human heat balance models, and spatial mapping workflows depicted in the project reference diagrams:

1. **Fundamental UTCI Model & Heat Stress Scale** (`docs/examples/UTCI/1784462193210.jpg`):
   - **Definition**: UTCI assesses human thermal perception ("how hot or cold it feels to the human body") based on the Fiala multi-node thermo-physiological model.
   - **4 Primary Environmental Drivers**:
     1. Air Temperature ($T_a$, °C)
     2. Relative Humidity ($RH$, %) / Water Vapor Pressure ($e$, kPa)
     3. Wind Speed ($v$, m/s) at 10 m / 1.1 m pedestrian level
     4. Thermal / Mean Radiant Temperature ($MRT$ / $T_{mrt}$, °C), driven by direct, diffuse, and surface-reflected solar radiation + surface longwave emission.
   - **Physiological Heat Stress Categories**:
     - $< 26^\circ\text{C}$: No heat stress (Thermal comfort zone)
     - $26 - 32^\circ\text{C}$: Moderate heat stress
     - $32 - 38^\circ\text{C}$: Strong heat stress
     - $38 - 46^\circ\text{C}$: Very strong heat stress
     - $> 46^\circ\text{C}$: Extreme heat stress

2. **Spatial Microclimate Field Coupling** (`docs/examples/UTCI/1784462193769.jpg`):
   - **Inputs Spatial Maps**:
     - Wind Speed ($v$, m/s): Aerodynamic drag and wind acceleration around building masses and urban tree canopies (0.58 to >3.00 m/s).
     - Air Temperature ($T_a$, °C): Local thermal variations across shaded and exposed building zones (34.50 to 35.20°C).
     - Mean Radiant Temperature ($T_{mrt}$, °C): Solar radiation exposure vs. building and tree shade (40.00 to 65.00°C).
     - Relative Humidity ($RH$, %): Moisture distribution across microclimatic zones (45.00 to 50.00%).
   - **Output Spatial Map**: High-resolution UTCI spatial grid (33.00 to >44.00°C) mapping localized microclimatic thermal comfort zones influenced by urban geometry, materials, and vegetation.

---

## Prompt Roster & Research Scope

| # | File | Core Research Focus | Key Input / Output Metrics |
|---|------|---------------------|----------------------------|
| **U01** | `U01_utci_fundamentals_and_biometeorology_prompt.md` | Physiological basis, Fiala 2-node / multi-node thermo-physiological model, heat balance equations, and heat stress thresholds. | UTCI scale, skin temperature, sweat rate, core temperature, biometeorological validity limits. |
| **U02** | `U02_environmental_input_variables_and_microclimate_prompt.md` | Measurement, vertical profiling, spatial variation, and sensitivity analysis of the 4 core environmental inputs ($T_a, RH, v, MRT$). | $T_a$, $RH$, $v_{10m} \to v_{1.1m}$ power/log laws, solar irradiance components. |
| **U03** | `U03_mean_radiant_temperature_mrt_calculation_prompt.md` | Radiative heat flux modeling in urban canyons: Shortwave (direct/diffuse/reflected), Longwave emission, Sky View Factor (SVF), and tree canopy shade. | $T_{mrt}$, SVF, solar vector, surface temperatures ($T_{surf}$), vegetation transmissivity. |
| **U04** | `U04_urban_microclimate_simulation_and_peer_tools_prompt.md` | Benchmarking peer microclimate engines (ENVI-met, Ladybug/Honeybee/Dragonfly, SOLWEIG, RayMan, CitySim, PALM) and UBEM coupling. | Grid resolution, runtime performance, spatial coupling interfaces, boundary conditions. |
| **U05** | `U05_utci_polynomial_approximation_and_computational_methods_prompt.md` | Mathematical computation: Bröde et al. 6th-degree operational polynomial, Look-Up Tables (LUT), fast vectorization, Python/C/Fortran libraries. | Polynomial coefficients, operational limits, computational throughput, error bounds. |
| **U06** | `U06_spatial_mapping_gis_and_ubem_integration_prompt.md` | Spatial GIS raster/mesh mapping, OpenUBEM integration, coupling building envelope heat release with outdoor thermal stress, and urban heat mitigation strategies. | Spatial raster grids, thermal comfort maps, mitigation efficacy (cool roofs, urban trees, shade structures). |

---

## Shared Conventions for All UTCI Prompts

1. **Lead with populated tables**: Every prompt requires structured markdown tables synthesizing physics, equations, peer tools, and benchmarks before prose explanations.
2. **Rigorous academic citations**: Cite primary literature (e.g., Fiala et al. 2012, Bröde et al. 2012, Havenith et al. 2012, Jendritzky et al. 2012, Lindberg et al. 2008 / SOLWEIG, Bruse & Fleer 1998 / ENVI-met, Roudsari et al. / Ladybug Tools).
3. **Traceability & OpenUBEM Fit**: Connect theoretical findings directly to OpenUBEM's building geometry (OSM footprint, height, envelope U-values, surface temperatures) and spatial weather data (EPW / microclimate grids).
4. **No Fabricated Precision**: Explicitly state operational boundaries (e.g., wind speed limits $0.5 - 17\text{ m/s}$, $T_a$ range $-50^\circ\text{C}$ to $+50^\circ\text{C}$) and flag gaps requiring manager decisions.
