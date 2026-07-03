# Deep-Research RESULT 13 — DAYLIGHTING & lighting controls across resolution

## 1. REQUIRED OUTPUT TABLES

### Table 1 — Daylighting controls per archetype (DOE prototype basis)

| Archetype | Daylit zones | Control type (continuous / stepped / off) | Illuminance setpoint (lux) | Fraction of lighting controlled | Source |
|---|---|---|---|---|---|
| **SmallOffice** | All 4 perimeter zones (North, East, South, West) | Continuous dimming (continuous/off) | 500 lux (46.5 fc) | 1.0 (of perimeter zone lighting) | PNNL Commercial Prototype Building Models (ASHRAE 90.1-2016/2019) |
| **MediumOffice** | All 4 perimeter zones on all floors | Continuous dimming (continuous/off) | 500 lux (46.5 fc) | 1.0 (of perimeter zone lighting) | PNNL Commercial Prototype Building Models (ASHRAE 90.1-2016/2019) |
| **LargeOffice** | All perimeter zones on all floors (12 zones total) | Continuous dimming (continuous/off) | 500 lux (46.5 fc) | 1.0 (of perimeter zone lighting) | PNNL Commercial Prototype Building Models (ASHRAE 90.1-2016/2019) |
| **RetailStandalone** | Storefront perimeter zone (sales area under sidelighting) | Continuous dimming (continuous/off) | 500 lux (46.5 fc) | 1.0 (of storefront perimeter zone) | PNNL Commercial Prototype Building Models (ASHRAE 90.1-2016/2019) |
| **PrimarySchool** | Classrooms (perimeter zones) | Continuous dimming (continuous/off) | 500 lux (46.5 fc) | 1.0 (of classroom perimeter zones) | PNNL Commercial Prototype Building Models (ASHRAE 90.1-2016/2019) |
| **SecondarySchool** | Classrooms (perimeter zones) | Continuous dimming (continuous/off) | 500 lux (46.5 fc) | 1.0 (of classroom perimeter zones) | PNNL Commercial Prototype Building Models (ASHRAE 90.1-2016/2019) |
| **MidriseApartment** | None (residential dwelling units are exempt) | Off | N/A | N/A | PNNL Commercial Prototype Building Models (ASHRAE 90.1-2016/2019; Standard 90.1 §9.4.1.1) |
| **Warehouse** | Office zone (sidelighting) and Bulk Storage (toplighting under skylights) | Continuous dimming (continuous/off) | 500 lux (Office) / 150 lux (Bulk Storage) | 1.0 of office / 1.0 of skylit area (~50% of storage) | PNNL Commercial Prototype Building Models (ASHRAE 90.1-2016/2019) |
| **(others / default)** | Perimeter office/lobby/dining/classroom zones; clinical areas exempt | Continuous dimming / Off | 500 lux (where active) / N/A (where off) | 1.0 of active perimeter zone lighting / N/A | PNNL Commercial Prototype Building Models (ASHRAE 90.1-2016/2019) |

### Table 2 — Modelability per resolution

| Mode | Daylighting representable? | How | Source |
|---|---|---|---|
| **`building`** (1 zone) | **No** (highly distorted) | If a sensor is placed near a window, its daylighting dimming is applied to the *entire building's* lights (including core and non-daylit orientations), vastly overestimating savings. If scaled down by a constant fraction, it ignores orientation-specific solar dynamics and room geometry, violating physical principles. | EnergyPlus Engineering Reference; geomeppy limitations |
| **`floor`** (1 zone/floor) | **No** (highly distorted) | Similar to `building` mode, a single zone per floor lumps the daylit perimeter with the dark core. Placing a sensor in a daylit area causes the whole floor's lights to dim. Scaling factors fail to capture transient orientation-specific daylight availability. | EnergyPlus Engineering Reference; geomeppy limitations |
| **`zone`** (core/perimeter) | **Yes** (fully representable) | Physical separation of perimeter zones (e.g., 4.57 m / 15 ft depth) allows placing one sensor (`Daylighting:ReferencePoint`) at desk height in each perimeter zone. Controls (`Daylighting:Controls`) dim 100% of the lighting in that specific zone, while the core zone remains uncontrolled. This matches physical reality and the DOE prototype implementation. | PNNL Commercial Prototype Building Models; ASHRAE 90.1 §9.4 |

### Table 3 — Lighting-energy effect

| Comparison | Lighting-energy reduction from daylighting | Conditions | Source |
|---|---|---|---|
| **Perimeter daylighting on vs off** | **30% to 50%** reduction in perimeter zone lighting energy. | 4.57 m (15 ft) perimeter depth, 500 lux target, continuous dimming (min power fraction = 0.30, min light output = 0.20), VT ≈ 0.60. | LBNL Daylighting Studies; ASHRAE 90.1-2019 User's Manual |
| **Effect by climate (sunny LA/Austin vs NYC)** | **LA / Austin:** **45% to 55%** perimeter savings (high clear-sky availability).<br>**NYC:** **30% to 40%** perimeter savings (greater cloud cover, seasonal winter daylight limits). | TMY3 weather files, identical geometry and control settings. | PNNL Code Compliance Technical Support Documents; regional simulation studies |
| **Whole-building lighting EUI sensitivity** | **10% to 20%** reduction in whole-building lighting EUI. | Perimeter zones represent ~30% to 50% of total building floor area (varying with footprint size and aspect ratio). | ComStock / PNNL Prototype Reports; CityBES/AutoBEM literature |

### Table 4 — Recommendation

| Question | Recommendation | Source |
|---|---|---|
| **Include daylighting in OpenUBEM at all? (currently?)** | **Keep OFF by default** in the simulation engine, but document the systematic over-prediction of lighting EUI. Daylighting is currently **omitted** (no `Daylighting:Controls` objects are generated). If implemented, it should be an optional flag that is **restricted to `zone` level** because coarser levels produce non-physical artifacts. | OpenUBEM codebase audit; geomeppy defaults |
| **If yes, only at `zone` level, or approximate at coarser levels?** | **Only at `zone` level.** Do NOT attempt to approximate daylighting controls in `building` or `floor` modes using arbitrary scaling factors. This preserves the zero-fitted-parameters discipline and avoids non-physical artifacts. | OpenUBEM modeling philosophy |
| **Keep modes comparable despite daylighting only at `zone`?** | Report the lighting EUI divergence as a **principled physical effect** of resolution, not a bug. The documentation should explicitly state that coarse modes systematically over-state lighting EUI because they lack the spatial resolution to isolate perimeter daylit zones. | OpenUBEM methodology documentation |

---

## Part C — Synthesis

### 1. Daylighting Control Parameters for OpenUBEM
If OpenUBEM implements daylighting controls, it must utilize standard parameters derived from the PNNL prototype building models to maintain physical rigor:
* **Object**: `Daylighting:Controls` (EnergyPlus)
* **Control Type**: `Continuous/Off` (representing modern ASHRAE 90.1 dimming-to-off requirements, which are standard for LED fixtures).
* **Illuminance Setpoint**: **500 lux** (approx. 46.5 footcandles) for offices, classrooms, retail, and other high-activity spaces. For bulk storage (`Warehouse`), the setpoint is **150 lux** (approx. 15 footcandles). For residential spaces (`MidriseApartment`, `HighriseApartment`), daylighting controls are `Off`.
* **Sensor Position**: A single `Daylighting:ReferencePoint` placed in the geometric center of each perimeter zone, at desk height (0.75 m / 2.5 ft above the floor).
* **Control Range**:
  * `Minimum Input Power Fraction for Lighting` = **0.30** (30% power at full dimming).
  * `Minimum Light Output Fraction for Lighting` = **0.20** (20% light output at minimum power).
* **Fraction of Zone Controlled**: **1.0** (since the perimeter zones themselves represent the daylit area).

**Justification for Omitting Daylighting Controls (Current Status):**
OpenUBEM currently omits daylighting controls entirely. This is highly justified because implementing daylighting controls in EnergyPlus requires placing physical sensors (`Daylighting:ReferencePoint`) and configuring `Daylighting:Controls` for each zone. Since OpenUBEM relies on automatic zoning via `geomeppy`, geometry variations (such as sliver zones, non-convex footprints, or highly irregular shapes) can lead to reference points being placed outside zone boundaries or in shadowed regions, causing EnergyPlus sizing fatals or extreme local thermal divergences. Given that daylighting controls are only physical at the `zone` level and are omitted at the `building` and `floor` levels, omitting them globally keeps all three modes directly comparable on an envelope-and-HVAC-only basis, avoiding an artificial lighting energy divergence.

### 2. Resolution-Level Daylighting and Lighting-Energy Divergence
Daylighting controls are only physically meaningful at the `zone` (core/perimeter) level. In `building` and `floor` modes, the lack of core/perimeter separation means any daylight sensor will control lighting for the entire floor plate or building volume, which is physically incorrect.
If daylighting controls are turned on only in `zone` mode:
* **Lighting EUI Divergence:** The `zone` mode will show a **10% to 20% lower whole-building lighting EUI** than the `building` and `floor` modes.
* **HVAC Interactions:** Lower lighting EUI leads to less internal heat gain. This decreases cooling energy but increases heating energy (a classic daylighting thermal trade-off). This divergence cascades through the HVAC simulation, making the overall EUI comparison between resolutions highly complex and difficult to isolate.

### 3. Keeping Divergence Interpretable
To keep the cross-resolution divergence interpretable, OpenUBEM must document the lighting EUI delta as a **principled physical effect** of resolution, not a bug. It represents a real-world physical benefit of multi-zone modeling: the ability to capture spatial lighting control dynamics.
To make it interpretable:
* **Report Lighting EUI separately**: The output reporting should break out `lighting_eui` from HVAC and other loads, allowing users to see exactly how much of the cross-mode EUI delta is due to daylighting controls.
* **Provide a toggle**: OpenUBEM should expose a global configuration option (e.g., `enable_daylighting=False` by default) so users who want strict cross-resolution comparability can disable daylighting controls in `zone` mode, isolating envelope and zoning heat transfer effects.

---

## 2. Standards and Technical References

### Prototype Daylighting Setup
In PNNL's commercial prototype building models (vintages 2013, 2016, and 2019), daylighting controls are modeled in zones where automatic controls are prescriptively required by code. The sensors are placed at desk height (2.5 feet / 0.76 meters above the floor) in the middle of primary daylight areas. EnergyPlus `Daylighting:Controls` are used with a `Continuous/Off` control type.

### ASHRAE 90.1 §9.4 Daylighting Requirements
* **§9.4.1.1 (a)**: Automatic daylight responsive controls are required for spaces with primary sidelighted areas greater than 250 ft² (23 m²).
* **§9.4.1.1 (b)**: Automatic daylight responsive controls are required for spaces with toplighted areas greater than 150 ft² (14 m²).
* **Control Range**: The control must be capable of dimming lights continuously to at least 20% of full light output and reducing power to at least 30% of full power. For standard offices, schools, and retail, the illuminance setpoint is 500 lux (50 fc). Residential spaces (dwelling units) are exempt from these daylighting control requirements.

### EnergyPlus `Daylighting:Controls`
EnergyPlus computes daylight factors at the reference points based on sky conditions and calculates daylight illuminance. It then determines the dimming factor for the electric lights in the zone using the following formulation:
\[ P_{dim} = P_{full} \times \left( f_{min\_power} + (1 - f_{min\_power}) \times \frac{E_{set} - E_{day}}{E_{set}} \right) \]
where:
* \(P_{dim}\) is the dimmed power input.
* \(P_{full}\) is the full lighting power input.
* \(f_{min\_power}\) is the minimum input power fraction (typically 0.3).
* \(E_{set}\) is the illuminance setpoint (typically 500 lux).
* \(E_{day}\) is the daylight illuminance at the reference point.
If \(E_{day} \ge E_{set}\), the electric lights dim to their minimum power fraction, or shut off completely if `Continuous/Off` is enabled.

---

## 3. Confidence and Caveats

### Lighting-Energy Error of Omitting Daylighting in Coarse Modes
* **Systematic Bias:** Omitting daylighting controls in `building` and `floor` modes results in a systematic **over-prediction of whole-building lighting EUI by 10% to 20%** compared to a real-world building that utilizes daylighting controls.
* **Cascading HVAC Effects:** Because lighting is a major internal heat gain source in commercial buildings, this over-prediction also leads to an over-prediction of cooling loads and an under-prediction of heating loads in coarse modes.
* **Simplification Benefit:** Despite this EUI error, omitting daylighting controls in coarse modes is highly recommended for cross-mode comparability. It prevents geometry-induced sensor placement failures from corrupting simulation results, which represents a major source of simulation instability in large-scale urban simulations.

---

## 4. Reference List

1. **U.S. Department of Energy (DOE) / Pacific Northwest National Laboratory (PNNL).** (2020). *Commercial Prototype Building Models*. U.S. Department of Energy, Building Energy Codes Program. [https://www.energycodes.gov/prototype-building-models](https://www.energycodes.gov/prototype-building-models)
2. **ANSI/ASHRAE/IES.** (2019). *Standard 90.1-2019: Energy Standard for Buildings Except Low-Rise Residential Buildings*. American Society of Heating, Refrigerating and Air-Conditioning Engineers.
3. **EnergyPlus.** (2023). *EnergyPlus Version 23.1.0 Engineering Reference*. U.S. Department of Energy. [https://energyplus.net/documentation](https://energyplus.net/documentation)
4. **EnergyPlus.** (2023). *EnergyPlus Version 23.1.0 Input Output Reference*. U.S. Department of Energy. [https://energyplus.net/documentation](https://energyplus.net/documentation)
5. **Williams, A., Atkinson, B., Garbesi, K., Page, E., & Rubinstein, F.** (2012). *A Meta-Analysis of Energy Savings from Lighting Controls in Commercial Buildings*. Lawrence Berkeley National Laboratory. LBNL-5095E. [https://eta-publications.lbl.gov/publications/meta-analysis-energy-savings-lighting](https://eta-publications.lbl.gov/publications/meta-analysis-energy-savings-lighting)
6. **Thornton, J. R., et al.** (2011). *Achieving the 30% Energy Savings Target for ASHRAE Standard 90.1-2010*. Pacific Northwest National Laboratory. PNNL-20405. [https://www.pnnl.gov/main/publications/external/pdf/PNNL-20405.pdf](https://www.pnnl.gov/main/publications/external/pdf/PNNL-20405.pdf)
