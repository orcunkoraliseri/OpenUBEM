# Deep-Research Prompt U01 — UTCI FUNDAMENTALS & THERMO-PHYSIOLOGICAL BASIS

> SCOPE GUARD — READ FIRST. This prompt establishes the **theoretical, physiological, and biometeorological foundation** of the Universal Thermal Climate Index (UTCI). It covers the Fiala multi-node thermo-physiological model, human heat balance equations, physiological stress indicators (skin temperature, core temperature, sweat rate, skin wettedness), and the 10 physiological heat/cold stress categories. Do NOT cover spatial microclimate field modeling (`U02`/`U03`), peer software benchmarks (`U04`), or polynomial code implementations (`U05`). See `00_README_utci_prompt_set.md` for shared facts and conventions.

---

## What this document is

A deep biometeorological survey. UTCI is defined as the equivalent ambient temperature ($T_{eq}$) of a reference environment that produces the same physiological response (sweating, shivering, skin blood flow, tissue temperature) in a standardized human subject as the actual outdoor environment. Before integrating UTCI into OpenUBEM's output suite, we must establish the exact physiological mechanisms, heat exchange equations, and thermal stress thresholds that give UTCI its scientific validity over legacy indices (e.g., Heat Index, Wind Chill, PMV, PET).

## Role

Human biometeorology & thermal physiology research analyst. Ground every physiological threshold and model assumption in the primary COST Action 730 literature (Fiala et al. 2012; Bröde et al. 2012; Jendritzky et al. 2012; Havenith et al. 2012; Psikuta et al. 2012) and international standards (ISO 7730, ISO 7933, ASHRAE 55).

## Why this matters (so you scope correctly)

In urban building energy modeling, outdoor thermal comfort is frequently simplified to dry-bulb air temperature. However, as illustrated in `docs/examples/UTCI/1784462193210.jpg`, air temperature alone fails to capture heat stress under high solar radiation or low wind speed. If OpenUBEM provides outdoor comfort metrics to urban planners, it must deploy an index grounded in thermo-physiology, capable of differentiating between "Moderate Heat Stress" ($26-32^\circ\text{C}$) and "Extreme Heat Stress" ($>46^\circ\text{C}$) under varying microclimatic combinations.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — UTCI Thermal Stress Categories & Physiological Response Thresholds

| UTCI Range (°C) | Stress Category Label (as in 1784462193210.jpg) | Primary Physiological Mechanism / Strain | Mean Skin Temp (°C) | Sweat Rate (g/min) | Shivering / Vasodilation State | Source |
|---|---|---|---|---|---|---|
| $> +46$ | Extreme heat stress |  |  |  |  |  |
| $+38\text{ to }+46$ | Very strong heat stress |  |  |  |  |  |
| $+32\text{ to }+38$ | Strong heat stress |  |  |  |  |  |
| $+26\text{ to }+32$ | Moderate heat stress |  |  |  |  |  |
| $+9\text{ to }+26$ | No thermal stress (Comfort) |  |  |  |  |  |
| $+0\text{ to }+9$ | Slight cold stress |  |  |  |  |  |
| $-13\text{ to }0$ | Moderate cold stress |  |  |  |  |  |
| $-27\text{ to }-13$ | Strong cold stress |  |  |  |  |  |
| $-40\text{ to }-27$ | Very strong cold stress |  |  |  |  |  |
| $< -40$ | Extreme cold stress |  |  |  |  |  |

### Table 2 — Fiala Thermo-Physiological Model Standardization Assumptions

| Parameter | Standard Reference Value | Physical / Physiological Meaning | Sensitivity to Variation | Source |
|---|---|---|---|---|
| Metabolic Rate ($M$) | $135\text{ W/m}^2$ ($2.3\text{ MET}$) | Walking at $4\text{ km/h}$ on level ground | High / Low |  |
| Reference Wind Speed ($v_{ref}$) | $0.5\text{ m/s}$ at $1.1\text{ m}$ height | Walking speed relative to air | High |  |
| Reference Mean Radiant Temp ($T_{mrt,ref}$) | Equals Air Temp ($T_{mrt} = T_a$) | Radiative balance with surroundings | High |  |
| Reference Relative Humidity ($RH_{ref}$) | $50\%$ (for $T_a \le 29^\circ\text{C}$); $e_{ref} = 20\text{ hPa}$ ($T_a > 29^\circ\text{C}$) | Moisture availability for evaporative cooling | Moderate |  |
| Clothing Insulation ($I_{cl}$) | Self-adaptive dynamic model ($0.3\text{ to } 2.6\text{ clo}$) | Thermal resistance of clothing vs. $T_a$ | High |  |

### Table 3 — Human Body Thermal Energy Balance Equations

| Heat Balance Term | Physical Equation / Representation | Environmental Drivers | Physiological Control | Source |
|---|---|---|---|---|
| Internal Heat Production ($M - W$) |  | Activity level, mechanical work | Muscle contraction, shivering |  |
| Convective Heat Flux ($C$) |  | Air Temp ($T_a$), Wind Speed ($v$) | Skin temperature, vasodilation |  |
| Radiative Heat Flux ($R$) |  | Mean Radiant Temp ($T_{mrt}$) | Skin emissivity, body posture |  |
| Respiratory Heat Flux ($E_{res} + C_{res}$) |  | Air Temp ($T_a$), Vapor Pressure ($e$) | Pulmonary ventilation rate |  |
| Evaporative Skin Heat Flux ($E_{sk}$) |  | Relative Humidity ($RH$), Wind ($v$) | Sweat secretion rate, skin wettedness ($w$) |  |

### Table 4 — Biometeorological & Meteorological Validity Boundaries

| Environmental Variable | Minimum Valid Value | Maximum Valid Value | Behaviour Beyond Boundary | Source |
|---|---|---|---|---|
| Air Temperature ($T_a$) | $-50^\circ\text{C}$ | $+50^\circ\text{C}$ | Polynomial extrapolation error |  |
| Mean Radiant Temp ($T_{mrt} - T_a$) | $-30^\circ\text{C}$ | $+70^\circ\text{C}$ | Physiological non-equilibrium |  |
| Wind Speed at 10m ($v_{10m}$) | $0.5\text{ m/s}$ | $30.0\text{ m/s}$ ($17\text{ m/s}$ at $1.1\text{ m}$) | Convective saturation |  |
| Vapor Pressure ($e$) | $0\text{ kPa}$ | $5.0\text{ kPa}$ ($RH \le 100\%$) | Condensation regime |  |

---

## Part C — Synthesis (Physiological & Index Choice Verdict)

Give:
1. A rigorous summary of why UTCI is superior to legacy thermal indices (PMV, PET, Heat Index, Wind Chill) for outdoor urban modeling.
2. An assessment of the dynamic clothing model ($I_{cl}$) used in UTCI vs. fixed clo assumptions.
3. A clear recommendation on how OpenUBEM should categorize heat stress levels in municipal thermal risk reporting based on Table 1.

## Output Format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C synthesis.
3. Cite primary biometeorological papers for every entry.
4. **"Confidence and caveats":** highlight any physiological boundary conditions where UTCI calculation stability degrades.
5. **Reference list** — complete academic citations with DOIs.

## Hard Requirements

- **Populate every cell in Tables 1–4.**
- **Strictly maintain the 10 UTCI heat stress categories**, aligning with `1784462193210.jpg`.
- **Differentiate environmental forces from thermo-physiological responses.**
