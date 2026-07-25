# Deep-Research Prompt U03 — MEAN RADIANT TEMPERATURE (MRT) CALCULATION & RADIATIVE FLUX MODELING

> SCOPE GUARD — READ FIRST. This prompt delivers a deep investigation into **Mean Radiant Temperature ($MRT$ / $T_{mrt}$)** calculation methodologies within complex urban environments. It covers shortwave solar radiation (direct, diffuse, ground-reflected), longwave surface and atmospheric emissions, Sky View Factor (SVF) geometry, building envelope surface temperatures ($T_{surf}$), and tree canopy shading/transmissivity. Do NOT cover physiological thermo-regulation (`U01`), non-radiant input scaling (`U02`), peer software benchmarks (`U04`), or polynomial UTCI code (`U05`). See `00_README_utci_prompt_set.md`.

---

## What this document is

A radiative heat exchange modeling specification. As demonstrated in `docs/examples/UTCI/1784462193769.jpg`, $T_{mrt}$ exhibits extreme spatial variation across urban sites (ranging from $40.00^\circ\text{C}$ in building shadows to $>65.00^\circ\text{C}$ on exposed unshaded surfaces), serving as the single dominant driver of localized UTCI heat stress. Because standard EPW weather files report unshaded horizontal solar radiation without urban obstruction, calculating $T_{mrt}$ at pedestrian grid points requires modeling 3D urban geometry, surface materials (albedo, emissivity), envelope surface temperatures from building energy simulations, and tree shade.

## Role

Urban radiative heat transfer & solar modeling analyst. Ground all radiation balance equations, view factor geometry, and surface emission physics in established urban climate literature (Oke 1987; Robinson & Stone 2004; Lindberg et al. 2008 / SOLWEIG; Matzarakis et al. 2007 / RayMan; Kantor & Unger 2011).

## Why this matters (so you scope correctly)

$T_{mrt}$ is defined as the uniform temperature of an imaginary black enclosure in which the radiant heat transfer from the human body equals the radiant heat transfer in the actual non-uniform complex environment. A $10^\circ\text{C}$ error in $T_{mrt}$ causes approximately a $3-5^\circ\text{C}$ shift in UTCI. For OpenUBEM to generate accurate UTCI spatial maps, its $T_{mrt}$ engine must correctly resolve building geometry shading, surface albedo reflections, and tree canopy transmissivity.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Shortwave & Longwave Radiation Components in Urban Canyons

| Flux Category | Symbol & Unit | Physical Source / Flux Mechanism | Key Urban Modifiers (Geometry, Materials, Trees) | Primary Mathematical Formula | Source |
|---|---|---|---|---|---|
| Direct Solar Radiation | $K_{dir}$ ($\text{W/m}^2$) | Direct beam irradiance from sun | Solar altitude/azimuth, building shadows, tree canopy shade ($\tau$) | $K_{dir} = I_{dir} \cdot f_{p} \cdot (1 - \text{Shade})$ |  |
| Diffuse Sky Radiation | $K_{diff}$ ($\text{W/m}^2$) | Atmospheric scattered solar flux | Sky View Factor ($\Psi_{sky}$ / SVF), cloud cover | $K_{diff} = I_{diff} \cdot \Psi_{sky} \cdot f_{p}$ |  |
| Reflected Solar Radiation | $K_{refl}$ ($\text{W/m}^2$) | Solar reflection from ground & walls | Ground albedo ($\alpha_{grd}$), Wall albedo ($\alpha_{wall}$), View Factors | $K_{refl} = (K_{dir} + K_{diff}) \cdot (1 - \Psi_{sky}) \cdot \alpha_{wall}$ |  |
| Downward Sky Longwave | $L_{sky}$ ($\text{W/m}^2$) | Atmospheric thermal emission | Sky View Factor ($\Psi_{sky}$), air temp ($T_a$), sky emissivity ($\epsilon_{sky}$) | $L_{sky} = \Psi_{sky} \cdot \epsilon_{sky} \cdot \sigma T_a^4$ |  |
| Wall Surface Longwave | $L_{wall}$ ($\text{W/m}^2$) | Thermal radiation emitted by wall surfaces | Wall surface temp ($T_{wall}$), wall emissivity ($\epsilon_{wall}$), SVF | $L_{wall} = (1 - \Psi_{sky}) \cdot \epsilon_{wall} \cdot \sigma T_{wall}^4$ |  |
| Ground Surface Longwave | $L_{grd}$ ($\text{W/m}^2$) | Thermal radiation emitted by paving / ground | Ground surface temp ($T_{grd}$), ground emissivity ($\epsilon_{grd}$) | $L_{grd} = \epsilon_{grd} \cdot \sigma T_{grd}^4$ |  |

### Table 2 — Sky View Factor (SVF) Calculation Methods for Urban Grids

| SVF Method | Geometry Input | Computational Algorithm | Accuracy in Complex Massing | Execution Speed (Grids/sec) | Source |
|---|---|---|---|---|---|
| Ray-Tracing (3D Mesh) | 3D GIS/OSM Extrusions | Multi-vector intersection sampling across hemisphere | Exact / Benchmark standard | Moderate to Low |  |
| Horizon Angle Integral | Building heights & distances | Radial elevation angle integration ($16-64$ directions) | High for extruded geometry | High | SOLWEIG / Lindberg 2008 |
| Fisheye Lens Projection | Raster DSM / DEM | Pixel classification of sky vs. non-sky pixels | High for canopy + buildings | High |  |
| Canyon Aspect Ratio Formula | Street width ($W$), height ($H$) | Analytical 2D infinite canyon approximation ($\Psi_{sky} = \cos(\arctan(2H/W))$) | Low (uniform canyons only) | Ultra-High | Oke 1981 |

### Table 3 — Human Body Radiative Modeling Approaches

| Model Type | Geometry Representation | Directional Sampling | Projected Area Factor ($f_p$) Formulation | Application | Source |
|---|---|---|---|---|---|
| Integral Mean Radiant Temp | Spherical / Point receiver | 6 orthogonal flux directions (North, South, East, West, Up, Down) | $T_{mrt} = \left(\frac{S_{str}}{\sigma} - 273.15^4\right)^{0.25}$ | Standard micrometeorological field sensors & SOLWEIG | Fanger 1972; VDI 3787 |
| Cylindrical Human Model | Vertical cylinder | Radial integration + top/bottom disks | Function of solar altitude ($\theta$) and posture | RayMan / Matzarakis | Matzarakis et al. 2007 |
| Ellipsoid / Manikin Model | Anatomical multi-segment mesh | 3D view factor integration to surrounding surfaces | Detailed directional projected area table | Advanced thermoregulation | Fiala et al. 2012 |

### Table 4 — Tree Canopy & Vegetation Parameterization for MRT Reduction

| Vegetation Parameter | Typical Numerical Range | Physical Impact on Solar Irradiance | Impact on $T_{mrt}$ in Shade Zone | Source |
|---|---|---|---|---|
| Solar Transmissivity ($\tau$) | $0.10 - 0.30$ (Deciduous summer); $0.40 - 0.70$ (Winter) | Fraction of direct shortwave penetrating canopy | Reduces $T_{mrt}$ by $15-25^\circ\text{C}$ in full sun |  |
| Leaf Area Index (LAI) | $1.5 - 6.0\text{ m}^2/\text{m}^2$ | Canopy density controlling light extinction ($I = I_0 e^{-k \cdot \text{LAI}}$) | Non-linear reduction in direct beam |  |
| Crown Albedo ($\alpha_{tree}$) | $0.15 - 0.25$ | Shortwave reflection from top of canopy | Minor contribution to surrounding walls |  |
| Leaf Surface Temperature | $T_{leaf} \approx T_a + (-2\text{ to }+4^\circ\text{C})$ | Transpirational cooling vs. sensible heating | Lower longwave emission than asphalt |  |

---

## Part C — Synthesis (MRT Engine Architecture for OpenUBEM)

Give:
1. A definitive recommendation on the optimal $T_{mrt}$ calculation pipeline for OpenUBEM, balancing ray-tracing accuracy with city-scale processing speed.
2. How building envelope surface temperatures ($T_{wall}, T_{roof}$) computed by EnergyPlus / OpenUBEM should feed back into ground-level longwave radiation fluxes ($L_{wall}$).
3. A clear formulation for tree canopy shading integration over spatial raster grids.

## Output Format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C synthesis.
3. State explicit mathematical Stefan-Boltzmann energy balance equations.
4. **"Confidence and caveats":** address uncertainties in surface emissivity, albedo variations, and ground surface temperature modeling.
5. **Reference list** — complete academic citations with DOIs.

## Hard Requirements

- **Populate every cell in Tables 1–4.**
- **Provide explicit Stefan-Boltzmann formulations for $T_{mrt}$.**
- **Distinguish shortwave solar absorption from longwave thermal emission.**
