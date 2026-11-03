# Deep-Research Prompt U02 — ENVIRONMENTAL INPUT VARIABLES & MICROCLIMATE FIELD MEASUREMENT

> SCOPE GUARD — READ FIRST. This prompt focuses on the **4 core environmental input variables** required to calculate UTCI: Air Temperature ($T_a$), Relative Humidity ($RH$) / Vapor Pressure ($e$), Wind Speed ($v$), and Mean Radiant Temperature ($T_{mrt}$). It covers vertical profiling (scaling wind speed from 10 m weather stations to 1.1 m pedestrian level), microclimatic spatial variability across urban massing, and input sensitivity analysis. Do NOT cover physiological thermo-regulation (`U01`), MRT radiative ray-tracing detail (`U03`), software engines (`U04`), or polynomial algorithms (`U05`). See `00_README_utci_prompt_set.md`.

---

## What this document is

A microclimatic input specification. As demonstrated in `docs/examples/UTCI/1784462193769.jpg`, calculating UTCI across an urban footprint requires high-resolution spatial fields of four distinct environmental variables. Standard EnergyPlus Weather (EPW) files provide macro-scale meteorological data measured at open rural airports ($10\text{ m}$ wind height, unshaded solar radiation). This prompt investigates how macro-scale weather parameters must be transformed into micro-scale pedestrian-level inputs ($1.1\text{ m}$ height, urban canopy flow, building shade, surface emissions) suitable for spatial UTCI mapping in OpenUBEM.

## Role

Urban microclimate & meteorological data integration analyst. Ground input scaling laws, atmospheric boundary layer physics, and sensitivity metrics in peer-reviewed micrometeorological literature (Oke 1987; Krayenhoff et al. 2018; Stewart & Oke 2012 / LCZ classification; COST Action 730).

## Why this matters (so you scope correctly)

Using $10\text{ m}$ airport wind speed directly in a UTCI equation will severely overestimate convective cooling at the pedestrian level, causing false comfort predictions during heat waves. Similarly, neglecting relative humidity gradients or microclimatic air temperature shifts near building envelopes distorts thermal risk assessments. OpenUBEM requires rigorous, automated input scaling functions to process EPW weather files and microclimate grid outputs into valid UTCI inputs.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — The 4 Core UTCI Environmental Inputs Matrix

| Variable | Symbol & Standard Unit | Standard Measurement Height | Typical Urban Field Range (from 1784462193769.jpg) | Main Urban Drivers (Massing, Vegetation, Materials) | Primary Source / EPW Metric |
|---|---|---|---|---|---|
| Air Temperature | $T_a$ ($^\circ\text{C}$) | $1.5 - 2.0\text{ m}$ | $34.50 - 35.20^\circ\text{C}$ | Anthropogenic heat, envelope convection, urban heat island (UHI) | `Dry Bulb Temperature` |
| Relative Humidity | $RH$ (%) / $e$ (kPa) | $1.5 - 2.0\text{ m}$ | $45.00 - 50.00\%$ | Vegetation evapotranspiration, surface moisture, water bodies | `Relative Humidity` |
| Wind Speed | $v$ ($\text{m/s}$) | $1.1\text{ m}$ (Pedestrian level) | $0.58 - >3.00\text{ m/s}$ | Aerodynamic roughness, building drag, street canyon channeling | `Wind Speed` ($10\text{ m}$) |
| Mean Radiant Temp | $T_{mrt}$ ($^\circ\text{C}$) | $1.1\text{ m}$ (Centroid of body) | $40.00 - 65.00^\circ\text{C}$ | Direct/diffuse solar irradiance, surface albedo, building shade, SVF | Derived via radiation balance (`U03`) |

### Table 2 — Wind Speed Vertical Reduction Models ($v_{10m} \to v_{1.1m}$)

| Aerodynamic / Canopy Model | Mathematical Equation | Key Input Parameters | Applicability to Urban Canyons | Computational Cost | Source |
|---|---|---|---|---|---|
| Logarithmic Wind Profile | $v(z) = \frac{v_*}{\kappa} \ln\left(\frac{z - d}{z_0}\right)$ | Friction velocity ($v_*$), displacement ($d$), roughness ($z_0$) | Open terrain / rural boundary layer | Very Low |  |
| Power Law Profile | $v(z) = v_{ref} \left(\frac{z}{z_{ref}}\right)^\alpha$ | Power law exponent ($\alpha \approx 0.22 - 0.40$) | Standard urban canopy estimate | Very Low |  |
| COST 730 UTCI Exponential Profile | $v_{1.1m} = v_{10m} \cdot \frac{\ln(1.1 / z_0)}{\ln(10 / z_0)}$ | Roughness length ($z_0 = 0.01\text{ m}$ nominal) | Standard UTCI operational conversion | Low | Bröde et al. 2012 |
| Urban Canopy Drag Model (Macdonald / Morphometric) |  | Building Plan Area Density ($\lambda_p$), Frontal Density ($\lambda_f$) | High-density complex urban massing | Moderate |  |

### Table 3 — Relative Humidity ($RH$) vs. Water Vapor Pressure ($e$) Conversions

| Formulation | Mathematical Equation | Input Requirements | Temperature Range | Precision / Standard | Source |
|---|---|---|---|---|---|
| Tetens Equation | $e_s(T_a) = 0.61078 \exp\left(\frac{17.27 T_a}{T_a + 237.3}\right)$ | $T_a$ ($^\circ\text{C}$), $RH$ (%) | $0\text{ to }50^\circ\text{C}$ | Standard meteorological approximation |  |
| Buck Equation |  | $T_a$ ($^\circ\text{C}$), $P_{atm}$ (hPa) | $-50\text{ to }+50^\circ\text{C}$ | High-precision ASHRAE/ISO standard |  |
| Goff-Gratch Equation |  | $T_a$ (K), $P_{atm}$ | Wide meteorological boundary | WMO reference standard |  |

### Table 4 — Sensitivity Analysis of Environmental Inputs on UTCI Output ($\Delta \text{UTCI} / \Delta \text{Input}$)

| Variable Perturbation | Base Condition ($T_a=35^\circ\text{C}, RH=50\%, v=1\text{m/s}, T_{mrt}=55^\circ\text{C}$) | $\Delta \text{UTCI}$ Response ($^\circ\text{C}$) | Relative Impact (Rank 1-4) | Key Physical Insight |
|---|---|---|---|---|
| $+5^\circ\text{C}$ in Air Temp ($T_a$) | $35 \to 40^\circ\text{C}$ |  |  |  |
| $+20^\circ\text{C}$ in Mean Radiant Temp ($T_{mrt}$) | $55 \to 75^\circ\text{C}$ (Shade to Sun shift) |  |  | High radiant heat sensitivity outdoors |
| $+2.0\text{ m/s}$ in Wind Speed ($v$) | $1.0 \to 3.0\text{ m/s}$ |  |  | Convective cooling enhancement |
| $+20\%$ in Relative Humidity ($RH$) | $50 \to 70\%$ |  |  | Reduced evaporative cooling capacity |

---

## Part C — Synthesis (Input Pipeline & Scaling Recommendation)

Give:
1. A recommended workflow for converting EPW weather file inputs ($10\text{ m}$ wind, dry bulb temp, relative humidity) into pedestrian-level ($1.1\text{ m}$) UTCI inputs for OpenUBEM.
2. The most robust wind speed vertical reduction formula from Table 2 for automated execution.
3. An evaluation of the relative dominance of $T_{mrt}$ vs. $T_a$ in driving summer outdoor heat stress based on Table 4.

## Output Format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C synthesis.
3. Include exact mathematical formulations for wind reduction and vapor pressure.
4. **"Confidence and caveats":** discuss limitations of single-point EPW data when modeling microclimatic urban canyons.
5. **Reference list** — complete citations with DOIs.

## Hard Requirements

- **Fill every cell in Tables 1–4.**
- **Specify height conversion formulations explicitly ($10\text{ m} \to 1.1\text{ m}$).**
- **Quantify sensitivity metrics in Table 4.**
