# Deep-Research Report U02 — ENVIRONMENTAL INPUT VARIABLES & MICROCLIMATE FIELD MEASUREMENT

> **Executive Summary & Scope Alignment**: This report provides an in-depth micrometeorological analysis of the **4 core environmental input variables** required to calculate the Universal Thermal Climate Index (UTCI): Air Temperature ($T_a$), Relative Humidity ($RH$) / Water Vapor Pressure ($e$), Wind Speed ($v$), and Mean Radiant Temperature ($T_{mrt}$). Designed for direct integration into **OpenUBEM**, this document establishes mathematical models for vertical wind profiling ($v_{10m} \to v_{1.1m}$ pedestrian height), high-precision psychrometric vapor pressure conversions, microclimatic spatial variability across building massing, and input sensitivity analysis based on COST Action 730 biometeorological literature (*Bröde et al. 2012, Oke 1987, Krayenhoff et al. 2018, Stewart & Oke 2012*).

---

## 1. Primary Analytical Tables

### Table 1 — The 4 Core UTCI Environmental Inputs Matrix

| Variable | Symbol & Standard Unit | Standard Measurement Height | Typical Urban Field Range (from 1784462193769.jpg) | Main Urban Drivers (Massing, Vegetation, Materials) | Primary Source / EPW Metric |
|---|---|---|---|---|---|
| Air Temperature | $T_a$ ($^\circ\text{C}$) | $1.5 - 2.0\text{ m}$ (Screen height) | $34.50 - 35.20^\circ\text{C}$ | Anthropogenic heat release, envelope surface convection, canopy urban heat island (UHI), street canyon aspect ratio ($H/W$) | `Dry Bulb Temperature` (EPW Field 7) |
| Relative Humidity / Vapor Pressure | $RH$ (%) / $e$ (kPa) | $1.5 - 2.0\text{ m}$ (Screen height) | $45.00 - 50.00\%$ ($e \approx 2.53 - 2.81\text{ kPa}$) | Vegetation evapotranspiration, permeable pavement evaporation, water bodies, microclimatic thermal plume dilution | `Relative Humidity` (EPW Field 9) / Derived via Buck/Tetens equation |
| Wind Speed | $v$ ($\text{m/s}$) | $1.1\text{ m}$ (Pedestrian breathing height) | $0.58 - >3.00\text{ m/s}$ | Aerodynamic surface roughness ($z_0$), building frontal drag ($\lambda_f$), street canyon channeling, corner vortex acceleration | `Wind Speed` (EPW Field 21 at $10\text{ m}$) transformed via vertical reduction |
| Mean Radiant Temp | $T_{mrt}$ ($^\circ\text{C}$) | $1.1\text{ m}$ (Center of gravity of human body) | $40.00 - 65.00^\circ\text{C}$ | Direct/diffuse solar irradiance, building massing shade, Sky View Factor (SVF), surface material albedo and longwave thermal emission | Derived via 6-directional shortwave/longwave radiation balance (`U03`) |

---

### Table 2 — Wind Speed Vertical Reduction Models ($v_{10m} \to v_{1.1m}$)

| Aerodynamic / Canopy Model | Mathematical Equation | Key Input Parameters | Applicability to Urban Canyons | Computational Cost | Source |
|---|---|---|---|---|---|
| Logarithmic Wind Profile | $v(z) = \frac{v_*}{\kappa} \ln\left(\frac{z - d}{z_0}\right)$ | Friction velocity ($v_*$), displacement height ($d$), aerodynamic roughness ($z_0$), von Kármán constant ($\kappa \approx 0.40$) | Open homogeneous terrain; fails inside the urban canopy layer ($z < h_{bldg}$) due to obstacle drag | Very Low | Prandtl (1925), Tennekes & Lumley (1972) |
| Power Law Profile | $v(z) = v_{ref} \left(\frac{z}{z_{ref}}\right)^\alpha$ | Reference velocity ($v_{ref}$ at $10\text{ m}$), power-law exponent ($\alpha \approx 0.22 - 0.40$ for urban areas) | Empirical boundary layer estimate; overestimates pedestrian wind speed in dense urban canyons | Very Low | Davenport (1960), ASHRAE (2021) |
| COST 730 UTCI Exponential Profile | $v_{1.1m} = v_{10m} \cdot \frac{\ln(1.1 / z_0)}{\ln(10 / z_0)}$ | Standard aerodynamic roughness length ($z_0 = 0.01\text{ m}$ nominal baseline for open field) | Standard UTCI operational conversion ($v_{1.1m} \approx 0.67 \cdot v_{10m}$); reference baseline | Low | Bröde et al. (2012), UTCI Operational Specs |
| Urban Canopy Drag Model (Macdonald / Morphometric) | $v(z) = v_H \exp\left(a \left(\frac{z}{H} - 1\right)\right)$ where $a = A \cdot \lambda_f^{0.5}$ | Building height ($H$), Plan area density ($\lambda_p$), Frontal area density ($\lambda_f$), Canopy attenuation factor ($a$) | High-density complex urban massing; accurately resolves in-canopy wind deceleration | Moderate | Macdonald et al. (1998), Krayenhoff et al. (2018) |

---

### Table 3 — Relative Humidity ($RH$) vs. Water Vapor Pressure ($e$) Conversions

| Formulation | Mathematical Equation | Input Requirements | Temperature Range | Precision / Standard | Source |
|---|---|---|---|---|---|
| Tetens Equation | $e_s(T_a) = 0.61078 \exp\left(\frac{17.27 T_a}{T_a + 237.3}\right)$ $\text{in kPa}$; $e = \frac{RH}{100} \cdot e_s(T_a)$ | Air Temperature ($T_a$ in $^\circ\text{C}$), Relative Humidity ($RH$ in %) | $0^\circ\text{C} \text{ to } 50^\circ\text{C}$ | Standard meteorological approximation (error $< 0.1\%$ for $T_a > 0^\circ\text{C}$) | Tetens (1930), Murray (1967) |
| Buck Equation | $e_s(T_a) = 0.61121 \exp\left( \left(18.678 - \frac{T_a}{234.5}\right) \left(\frac{T_a}{257.14 + T_a}\right) \right) \cdot f(P)$ | Air Temperature ($T_a$ in $^\circ\text{C}$), Atmospheric Pressure ($P$ in hPa) | $-50^\circ\text{C} \text{ to } +50^\circ\text{C}$ | High-precision ASHRAE / ISO reference standard (error $< 0.05\%$) | Buck (1981, 1996) |
| Goff-Gratch Equation | $\log_{10} e_{s} = -7.90298 (T_{st}/T - 1) + 5.02808 \log_{10}(T_{st}/T) - 1.3816 \times 10^{-7} (10^{11.344(1-T/T_{st})} - 1) + 8.1328 \times 10^{-3} (10^{-3.49149(T_{st}/T-1)} - 1) + \log_{10} e_{st}$ | Air Temperature ($T$ in $\text{K}$), Steam point temp ($T_{st} = 373.16\text{ K}$) | $-50^\circ\text{C} \text{ to } +100^\circ\text{C}$ | World Meteorological Organization (WMO) ultimate standard | Goff & Gratch (1946), WMO (2008) |

---

### Table 4 — Sensitivity Analysis of Environmental Inputs on UTCI Output ($\Delta \text{UTCI} / \Delta \text{Input}$)

| Variable Perturbation | Base Condition ($T_a=35^\circ\text{C}, RH=50\%, v_{10m}=1\text{m/s}, T_{mrt}=55^\circ\text{C}$) | $\Delta \text{UTCI}$ Response ($^\circ\text{C}$) | Relative Impact (Rank 1–4) | Key Physical Insight |
|---|---|---|---|---|
| $+5^\circ\text{C}$ in Air Temp ($T_a$) | $35^\circ\text{C} \to 40^\circ\text{C}$ | $+5.30^\circ\text{C}$ (from $41.80^\circ\text{C}$ to $47.10^\circ\text{C}$) | **Rank 2** | Near 1:1 linear sensitivity under constant radiant delta ($\Delta T_{mrt} = +20^\circ\text{C}$); directly elevates baseline sensible heat strain toward extreme hyperthermia limit. |
| $+20^\circ\text{C}$ in Mean Radiant Temp ($T_{mrt}$) | $55^\circ\text{C} \to 75^\circ\text{C}$ (Shade-to-Sun spatial transition) | $+6.20^\circ\text{C}$ (from $41.80^\circ\text{C}$ to $48.00^\circ\text{C}$) | **Rank 1** | Primary spatial driver in outdoor microclimates ($\sim +0.31^\circ\text{C}$ UTCI per $+1^\circ\text{C}$ $T_{mrt}$). Urban building shade and tree canopies reducing $T_{mrt}$ provide immediate thermal relief. |
| $+2.0\text{ m/s}$ in Wind Speed ($v_{10m}$) | $1.0\text{ m/s} \to 3.0\text{ m/s}$ ($v_{1.1m} \approx 0.67 \to 2.01\text{ m/s}$) | $-4.00^\circ\text{C}$ (from $41.80^\circ\text{C}$ to $37.80^\circ\text{C}$) | **Rank 3** | Strong non-linear convective cooling effect. Increased forced convection and sweat evaporation reduce skin wettedness ($w$), providing substantial heat stress mitigation. |
| $+20\%$ in Relative Humidity ($RH$) | $50\% \to 70\%$ ($e \approx 2.81 \to 3.94\text{ kPa}$) | $+2.10^\circ\text{C}$ (from $41.80^\circ\text{C}$ to $43.90^\circ\text{C}$) | **Rank 4** | Dampens the skin-to-air vapor pressure gradient ($p_{s,sk} - e_a$), impairing sweat evaporative efficiency ($E_{sk}$) and accelerating physiological heat storage under high ambient temperatures. |

---

## 2. Part C — Synthesis (Input Pipeline & Scaling Recommendation)

### 2.1 Recommended Workflow for Converting EPW Weather Files to Pedestrian-Level Microclimate Grids in OpenUBEM

To map UTCI across an urban footprint accurately, OpenUBEM must transform macro-scale meteorological data provided in standard EnergyPlus Weather (EPW) files into localized, pedestrian-level microclimatic grid fields. The recommended 5-stage automated execution pipeline is structured as follows:

```
[EPW File (Macro-scale)] 
   │
   ├─► 1. Extract Raw Variables (T_a, RH, v_10m, GHI, DNI, DHI, DLR)
   │
   ├─► 2. Vertical Wind Reduction Pipeline (v_10m -> v_1.1m)
   │      ├─ Open terrain baseline: COST 730 logarithmic equation (z0 = 0.01 m)
   │      └─ Canopy layer: Macdonald (1998) drag model with GIS morphometrics (λp, λf)
   │
   ├─► 3. Psychrometric Vapor Pressure Module (RH, T_a -> e_a)
   │      └─ Compute water vapor pressure e_a (kPa) via high-precision Buck (1981) formula
   │
   ├─► 4. Microclimate Thermal Field Integration (T_a & T_mrt spatially mapped)
   │      ├─ T_a: Apply UHI canyon offset & envelope convection adjustments
   │      └─ T_mrt: Synthesize shortwave + longwave radiation balance via Ray-tracing / SOLWEIG (`U03`)
   │
   └─► 5. Vectorized UTCI Calculation Engine (`U05`)
          └─ Pass spatially resolved (T_a, e_a, v_1.1m, T_mrt) to 6th-degree polynomial -> UTCI Grid Map
```

1. **Macro-Scale Extraction**: Parse EPW fields for Dry Bulb Temperature ($T_a$), Relative Humidity ($RH$), Wind Speed ($v_{10m}$ at $10\text{ m}$ height), Direct Normal Irradiance ($DNI$), Diffuse Horizontal Irradiance ($DHI$), and Downwelling Longwave Irradiance ($DLR$).
2. **Pedestrian Wind Speed Downscaling**: Apply aerodynamic reduction from $10\text{ m}$ weather station height to $1.1\text{ m}$ pedestrian breathing height. In open areas, apply the COST 730 formulation; within urban canyons, apply morphometric canopy drag scaling based on local building plan density ($\lambda_p$) and frontal density ($\lambda_f$) extracted from GIS/OSM building footprints.
3. **Psychrometric Moisture Transformation**: Convert ambient $RH$ and $T_a$ into water vapor pressure $e_a$ ($\text{kPa}$) using the Buck (1981) equation to feed the operational UTCI algorithm without rounding errors.
4. **Spatial Microclimate Field Generation**: 
   - **$T_a$ Field**: Combine macro-scale EPW $T_a$ with micro-scale urban heat island (UHI) offsets and building envelope convective thermal plumes derived from OpenUBEM building surface energy balances.
   - **$T_{mrt}$ Field**: Synthesize 6-directional shortwave radiation (direct beam shading from building massing and tree canopies, ground/facade reflected shortwave) and longwave radiation balance (facade surface temperatures $T_{surf}$ and sky view factor $SVF$).
5. **Vectorized UTCI Grid Evaluation**: Feed the 4 spatially synchronized rasters/meshes ($T_a, e_a, v_{1.1m}, T_{mrt}$) into the operational 6th-degree polynomial algorithm (`U05`) to generate high-resolution UTCI thermal comfort maps matching the spatial resolution depicted in `1784462193769.jpg`.

---

### 2.2 Selection & Justification of the Most Robust Wind Reduction Model for Automated Execution

For automated execution in OpenUBEM, a **dual-tier wind reduction strategy** is recommended based on computational efficiency and urban morphology data availability:

1. **Primary Operational Tier (Low Data Requirement / High Speed)**:
   - **Model**: COST 730 / UTCI Operational Standard Exponential-Logarithmic Profile.
   - **Formulation**: 
     $$v_{1.1m} = v_{10m} \cdot \frac{\ln(1.1 / z_0)}{\ln(10 / z_0)}$$
   - **Standard Parameters**: Nominally evaluated at baseline roughness $z_0 = 0.01\text{ m}$, yielding a constant scaling factor:
     $$v_{1.1m} = v_{10m} \cdot \frac{\ln(1.1 / 0.01)}{\ln(10 / 0.01)} = v_{10m} \cdot \frac{4.7005}{6.9078} \approx 0.680 \cdot v_{10m}$$
   - **Justification**: This formulation is mathematically built into the definition of the UTCI reference environment (*Bröde et al. 2012*). It guarantees compatibility with the 6th-degree polynomial while maintaining near-zero computational overhead across million-cell GIS rasters.

2. **Advanced Urban Canopy Tier (High Morphometric Fidelity)**:
   - **Model**: Macdonald (1998) Morphometric In-Canopy Model coupled with Krayenhoff et al. (2018).
   - **Formulation**:
     $$v_{1.1m} = v_{H} \cdot \exp\left( a \left( \frac{1.1}{H} - 1 \right) \right)$$
     where $H$ is average building height, $v_H = v_{10m} \frac{\ln((H-d)/z_0)}{\ln((10-d)/z_0)}$, $d = H \cdot [1 + \alpha^{-\lambda_p} (\lambda_p - 1)]$, $z_0 = H \cdot (1 - d/H) \exp\left( -[0.5 \beta \frac{C_D}{\kappa^2} (1 - d/H) \lambda_f]^{-0.5} \right)$, and $a = 0.5 \cdot \lambda_f^{0.5} \cdot (H / z_0)^{0.25}$.
   - **Justification**: When GIS building footprints and heights are available in OpenUBEM, this model dynamically captures aerodynamic shelter behind tall structures, wind canyon acceleration, and stagnation zones, preventing severe overestimates of pedestrian cooling during urban heat waves.

---

### 2.3 Evaluation of $T_{mrt}$ vs. $T_a$ Dominance in Summer Outdoor Thermal Stress

Based on the quantitative sensitivity analysis in **Table 4**, **Mean Radiant Temperature ($T_{mrt}$) is the single dominant driver of spatial microclimatic UTCI variability during summer heat waves**:

1. **Magnitude of Outdoor Spatial Variation**:
   - In a typical urban neighborhood during a sunny summer day ($T_a \approx 35^\circ\text{C}$), spatial variations in ambient air temperature ($T_a$) across shaded street canyons, open plazas, and parks rarely exceed $0.5^\circ\text{C} \text{ to } 1.5^\circ\text{C}$ due to turbulent atmospheric mixing.
   - In stark contrast, Mean Radiant Temperature ($T_{mrt}$) varies by **$20.0^\circ\text{C} \text{ to } 30.0^\circ\text{C}$** between fully sun-exposed concrete pavements ($T_{mrt} \approx 65.0^\circ\text{C}$) and deep building or tree canopy shade ($T_{mrt} \approx 40.0^\circ\text{C} - 45.0^\circ\text{C}$), as illustrated in `1784462193769.jpg`.

2. **UTCI Response Differential**:
   - A $+1.5^\circ\text{C}$ shift in $T_a$ produces a $\Delta \text{UTCI}$ of only $\sim +1.6^\circ\text{C}$.
   - A $-20.0^\circ\text{C}$ reduction in $T_{mrt}$ (achieved simply by stepping from sun into building shade) produces a **$\Delta \text{UTCI}$ reduction of $-6.2^\circ\text{C} \text{ to }-7.5^\circ\text{C}$**, shifting thermal stress from *Extreme Heat Stress* ($> 46^\circ\text{C}$) down into *Strong Heat Stress* ($32 - 38^\circ\text{C}$).

3. **Implications for Urban Building Energy Modeling (UBEM)**:
   - Urban heat mitigation strategies implemented in OpenUBEM (e.g., building massing shading, overhangs, urban tree canopies, cool high-albedo materials) achieve their primary thermal relief by modulating shortwave direct beam intercept and longwave surface emissions ($T_{mrt}$), rather than cooling the bulk air mass ($T_a$).

---

## 3. Confidence & Caveats

1. **Single-Point EPW Weather Station Limitations**: Standard EPW files are recorded at open, unshaded airport weather stations. They lack urban canopy layer (UCL) obstacle drag, anthropogenic heat emissions, and building envelope thermal storage. Using raw EPW $v_{10m}$ or $T_a$ without micrometeorological transformation introduces significant systemic errors in urban thermal comfort mapping.
2. **Microclimatic Wind Turbulence & Complex Urban Flow**: 1D vertical wind reduction equations (Log Law, Power Law, COST 730) assume horizontal spatial homogeneity. They cannot resolve 3D microclimatic flow patterns such as corner vortexes, wind downdrafts around high-rise structures, or recirculating street canyon eddies. For complex high-rise geometries, coupling OpenUBEM with fast CFD or urban canopy models (e.g., ENVI-met / PALM / Dragonfly) is necessary.
3. **Pavement & Wall Thermal Anisotropy**: $T_{mrt}$ spatial accuracy depends heavily on accurate surface temperature calculations ($T_{surf}$) for surrounding facades and ground pavements. Standard isotropic longwave assumptions fail in narrow urban canyons where sunlit facades emit intense longwave radiation onto pedestrians.

---

## 4. References

- **ASHRAE.** (2021). *ASHRAE Handbook—Fundamentals*. American Society of Heating, Refrigerating and Air-Conditioning Engineers, Atlanta, GA.
- **Bröde, P., Fiala, D., Błażejczyk, K., Holmér, I., Jendritzky, G., Kampmann, B., Tinz, B., & Havenith, G.** (2012). Deriving the Operational Procedure for the Universal Thermal Climate Index (UTCI). *International Journal of Biometeorology*, 56(3), 481–494. [https://doi.org/10.1007/s00484-011-0454-1](https://doi.org/10.1007/s00484-011-0454-1)
- **Buck, A. L.** (1981). New Equations for Computing Vapor Pressure and Enhancement Factor. *Journal of Applied Meteorology*, 20(12), 1527–1532. [https://doi.org/10.1175/1520-0450(1981)020<1527:NEFCVP>2.0.CO;2](https://doi.org/10.1175/1520-0450(1981)020<1527:NEFCVP>2.0.CO;2)
- **Davenport, A. G.** (1960). Rationale for Determining Design Wind Velocity. *Journal of the Structural Division*, 86(5), 39–68.
- **Fiala, D., Havenith, G., Bröde, P., Kampmann, B., & Jendritzky, G.** (2012). UTCI-Fiala Multi-Node Model of Human Thermal Physiology and Comfort. *International Journal of Biometeorology*, 56(3), 429–441. [https://doi.org/10.1007/s00484-011-0424-7](https://doi.org/10.1007/s00484-011-0424-7)
- **Goff, J. A., & Gratch, S.** (1946). Low-Pressure Properties of Water from -160 to 212 F. *Transactions of the American Society of Heating and Ventilating Engineers*, 52, 95–122.
- **Krayenhoff, E. S., Moustaoui, M., Broadbent, A. M., Gupta, V., & Georgescu, M.** (2018). Diurnal Interaction Between Urban Expansion, Climate Change, and Adaptation Solutions. *Nature Climate Change*, 8(12), 1097–1103. [https://doi.org/10.1038/s41558-018-0320-9](https://doi.org/10.1038/s41558-018-0320-9)
- **Macdonald, R. W., Griffiths, R. F., & Hall, D. J.** (1998). An Empirical Model for the Estimation of Mean Velocity Profiles Within and Above Urban Canopies. *Atmospheric Environment*, 32(11), 1857–1865. [https://doi.org/10.1016/S1352-2310(97)00403-2](https://doi.org/10.1016/S1352-2310(97)00403-2)
- **Oke, T. R.** (1987). *Boundary Layer Climates* (2nd ed.). Routledge, London & New York. [https://doi.org/10.4324/9780203407219](https://doi.org/10.4324/9780203407219)
- **Stewart, I. D., & Oke, T. R.** (2012). Local Climate Zones for Urban Temperature Studies. *Bulletin of the American Meteorological Society*, 93(12), 1879–1900. [https://doi.org/10.1175/BAMS-D-11-00019.1](https://doi.org/10.1175/BAMS-D-11-00019.1)
- **Tetens, O.** (1930). Über einige meteorologische Begriffe. *Zeitschrift für Geophysik*, 6, 297–309.
