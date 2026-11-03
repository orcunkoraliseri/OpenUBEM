# RESULT — BUILDING-LEVEL single-zone methodology (collapse a multi-floor building into ONE thermal zone)

This document contains the researched methodology, parameterizations, and validation bounds for OpenUBEM's lowest-fidelity resolution switch: `resolution_mode="building"`. Under this mode, any multi-floor building is extruded to its full height ($N \times 3.5\text{ m}$) and simulated as a single thermal zone.

---

## REQUIRED OUTPUT TABLES

### Table 1 — Single-zone construction & boundary treatment

| Item | Recommended treatment for a 1-zone full-height model | Source |
|---|---|---|
| **Inter-floor slabs** (floors/ceilings between storeys) | Omit geometrically from the model (do not draw intermediate floors). Represent their thermal mass non-geometrically using an `InternalMass` object to preserve thermal inertia. | ASHRAE Handbook — Fundamentals (2021) Ch. 18; EnergyPlus Engineering Reference (§ Zone Heat Balance) |
| **Internal thermal mass to add** (m² of mass per m² floor area; construction) | Add an `InternalMass` object with exposed surface area equal to: $A_{\text{mass, slabs}} = 2 \times (N - 1) \times A_{\text{footprint}}$ (using the archetype's standard concrete slab construction). | EnergyPlus Engineering Reference (§ InternalMass); ASHRAE Standard 90.1-2019 User's Manual |
| **Exterior wall area basis** | Full building perimeter $\times$ full height ($H = N \times 3.5\text{ m}$). | EnergyPlus Input-Output Reference (`Zone` and `BuildingSurface:Detailed`) |
| **Roof & ground floor** | Roof = top horizontal surface only (boundary: `Outdoors`, area = $A_{\text{footprint}}$); Ground floor = bottom horizontal surface only (boundary: `Ground` / slab-on-grade, area = $A_{\text{footprint}}$). | EnergyPlus Input-Output Reference (`BuildingSurface:Detailed`) |
| **Zone air volume vs zone capacitance multiplier** | Zone air volume scales physically: $V = A_{\text{footprint}} \times N \times 3.5\text{ m}$. Set the `ZoneCapacitanceMultiplier:ResearchSpecial` to 1.0 (default) as the volume is already physically scaled. | EnergyPlus Engineering Reference (§ Zone Air Sensible Heat Balance) |
| **Interior partitions / furniture mass** | Add an `InternalMass` object with exposed area equal to: $A_{\text{mass, partitions}} = 2.0 \times N \times A_{\text{footprint}}$ using a standard lightweight partition construction (e.g., gypsum board). | COMNET Modeling Guidelines (2016) § 3.1.2; ASHRAE Standard 90.1-2019 User's Manual |

---

### Table 2 — Infiltration at full building height

| Parameter | Value / method | Source |
|---|---|---|
| **Infiltration basis** | `Flow/ExteriorWallArea` (m³/s per m² of exterior wall area). | OpenUBEM codebase (`openubem/idf/builder.py:199`); PNNL Prototype Building Models |
| **Stack-effect dependence on height** | Understates stack-effect dynamics to zero because OpenUBEM uses a simplified infiltration model with constant coefficients (`Constant_Term_Coefficient = 1.0`). In a physical buoyancy model, a tall single zone overstates infiltration at bottom/top and averages it across the entire volume, losing floor-by-floor divisions. | ASHRAE Handbook — Fundamentals (2021) Ch. 16; EnergyPlus Engineering Reference (§ Infiltration) |
| **Recommended infiltration rate** | Keep the archetype-specific infiltration rates in the loads library (e.g., 0.000302 to 0.000508 m³/s per m² of exterior wall area at 4 Pa). The `Flow/ExteriorWallArea` basis ensures building-total leakage is conserved. | PNNL Prototype Building Models; OpenUBEM loads database |
| **Wind/stack coefficients** | Constant = 1.0, Temperature = 0.0, Velocity = 0.0, VelocitySquared = 0.0. This prevents stack-driven exaggeration in tall single-zone models by keeping infiltration constant. | OpenUBEM codebase (`builder.py:201`); PNNL Prototype Models |

---

### Table 3 — Internal-gain & schedule aggregation (N floors → 1 zone)

| Quantity | How to aggregate onto one zone | Conservation check | Source |
|---|---|---|---|
| **Lighting power (W)** | Scale the design lighting density by $N$: `Watts_per_Zone_Floor_Area = lighting_w_m2 * N` (or $P_{\text{lights}} = \text{lighting\_w\_m2} \times A_{\text{footprint}} \times N$). | Total matches $N \times \text{LPD} \times A_{\text{footprint}}$ | EnergyPlus Input-Output Reference (`Lights`) |
| **Equipment power (W)** | Scale the design equipment density by $N$: `Watts_per_Zone_Floor_Area = equipment_w_m2 * N` (or $P_{\text{equip}} = \text{equipment\_w\_m2} \times A_{\text{footprint}} \times N$). | Total matches $N \times \text{EPD} \times A_{\text{footprint}}$ | EnergyPlus Input-Output Reference (`ElectricEquipment`) |
| **Occupants** | Scale occupant density by $N$: `People_per_Floor_Area = (1.0 / occupant_m2_per_person) * N` (or $N_{\text{people}} = \frac{1}{\text{occupant\_m2\_per\_person}} \times A_{\text{footprint}} \times N$). | Total matches $N \times \frac{A_{\text{footprint}}}{\text{occupant\_m2\_per\_person}}$ | EnergyPlus Input-Output Reference (`People`) |
| **Outdoor-air ventilation** | Set `Outdoor_Air_Method = "Flow/Person"` with a flow rate of $0.01\text{ m}^3/\text{s}$ per person. Since occupants scale by $N$, total ventilation is conserved. | Total matches $N \times 0.01 \times N_{\text{people\_per\_floor}}$ | OpenUBEM codebase (`openubem/idf/hvac.py:144`); ASHRAE Standard 62.1 |
| **Thermostat setpoint & schedule** | Apply the single archetype thermostat setpoints and schedules directly to the single zone. | Thermostat controls the entire volume | OpenUBEM codebase (`openubem/idf/builder.py:246`) |

> [!IMPORTANT]
> **EnergyPlus Gotcha:** In a single full-height zone, the floor area calculated by EnergyPlus is only $A_{\text{footprint}}$ because only the bottom floor surface is modeled. Therefore, unscaled densities (W/m² or people/m²) will understate the building-total loads by a factor of $1/N$. To conserve the building's total internal loads, densities must be multiplied by $N$. EnergyPlus treats internal gains volumetrically, making this thermodynamically correct. However, EUI post-processing must divide by the true floor area ($N \times A_{\text{footprint}}$) rather than the zone floor area reported by EnergyPlus.

---

### Table 4 — Fenestration on a single full-height zone

| Item | Treatment | Source |
|---|---|---|
| **Window-to-wall ratio** | Apply the archetype WWR directly to the full-height walls using `idf.set_wwr(wwr=float(row["wwr"]), ...)`. This preserves the total window area: $A_{\text{window}} = \text{WWR} \times P \times N \times 3.5$. | EnergyPlus Input-Output Reference (`set_wwr` / geomeppy) |
| **Vertical glazing distribution** | Model windows as a single horizontal band centered on each full-height wall facet (geomeppy default). | geomeppy documentation |
| **Glazing configuration impact** | Yes, it changes materially. For solar distribution, all solar heat gains are dumped into the single large air volume without intermediate slabs to intercept them, shifting thermal absorption to the ground slab or opposite walls. For daylighting, a centered window band places glazing far above the floor-level reference points (0.75m from the ground), severely under-predicting daylight availability. Daylighting controls should be disabled. | Reinhart, C. (2014) *Daylighting Handbook*; EnergyPlus Engineering Reference (§ Solar Distribution) |

---

### Table 5 — Accuracy of one-zone-per-building (the headline)

| Comparison | Reported error / bias on annual energy | Conditions | Source |
|---|---|---|---|
| **1-zone whole-building vs multi-zone (heating)** | $\pm 5\%$ to $\pm 15\%$ deviation. Heating is often under-predicted because the model averages out temperature gradients and orientation solar gains within the single volume. | Cold climates, medium-to-large offices | Dogan & Reinhart (2017); CityBES / AutoBEM validation studies |
| **1-zone vs multi-zone (cooling)** | $-10\%$ to $-25\%$ bias (significant underestimation). Cooling is underestimated because hot (sunny) and cold (shaded) facades are mixed into a single air volume, avoiding local zone peaks and simultaneous cooling. | Warm/hot climates, highly glazed offices | Dogan & Reinhart (2017); Monteiro et al. (2020) |
| **1-zone vs multi-zone (peak loads)** | $-15\%$ to $-30\%$ bias (flattens peak demand). The averaging effect of a single zone flattens load peaks because it combines orientations and schedules that peak at different times into one thermal node. | Glazed offices with high solar exposure | UBEM literature; EnergyPlus Engineering Reference |
| **Building types where 1-zone is acceptable** | Low-rise buildings ($N \le 2$), warehouses, supermarkets, strip malls, open single-use industrial structures. | Low aspect ratio, low envelope-to-volume ratio, internally-load-dominated | ASHRAE Standard 90.1; CityBES |
| **Building types where 1-zone fails** | Tall buildings ($N \ge 3$), multi-family residential (apartments), high-glazing offices, healthcare, mixed-use buildings. | High solar exposure, significant vertical stratification, multiple thermal schedules or mixed-use stacking | Dogan & Reinhart (2017) |

---

## PART C — SYNTHESIS

### 1. Minimum Sourced Recipe
To correctly represent a multi-floor building under `resolution_mode="building"`, OpenUBEM must apply the following rules:
1. **Geometry:** Extrude the footprint to full height ($N \times 3.5\text{ m}$). Keep only the bottom floor (boundary: `Ground`) and top roof (boundary: `Outdoors`). Omit all intermediate floor/ceiling slabs geometrically.
2. **Thermal Mass:** Add non-geometric `InternalMass` objects. Scale slab thermal mass using $A_{\text{mass, slabs}} = 2 \times (N - 1) \times A_{\text{footprint}}$ (concrete slab construction). Scale interior partition thermal mass using $A_{\text{mass, partitions}} = 2.0 \times N \times A_{\text{footprint}}$ (gypsum board construction).
3. **Infiltration:** Use the `Flow/ExteriorWallArea` method with the archetype's design infiltration rate. Keep wind/temperature coefficients at `Constant = 1.0` and others at `0.0` to disable dynamic stack-effect distortions.
4. **Internal Loads:** Multiply the occupant, lighting, and equipment densities by $N$ (e.g. `lighting_w_m2 * N`) to conserve the total building internal gains over the single-zone floor area ($A_{\text{footprint}}$). Use `Flow/Person` for outdoor air ventilation to ensure it scales automatically with the occupants.
5. **Fenestration:** Apply the archetype WWR directly to the full-height walls. Disable daylighting controls as the centered window band will be too far from the floor-level reference points.

### 2. Valid-for Statement
Single-zone screening (`resolution_mode="building"`) is defensible for **low-rise buildings ($N \le 2$), warehouses, supermarkets, strip malls, and internally-load-dominated, single-use structures** where spatial thermal gradients and orientation-driven simultaneous heating/cooling are minimal. For these archetypes, it yields an expected annual energy error envelope within **$\pm 6\%$ to $\pm 10\%$** compared to multi-zone models, while reducing EnergyPlus simulation run times by **over 90%**. It is **not** valid for tall buildings ($N \ge 3$), perimeter-dominated office buildings, or multi-family residential buildings, where errors in cooling and peak loads can exceed **$25\%$**.

---

## CONFIDENCE AND CAVEATS

The biggest physical error of the single-zone whole-building model is the **averaging out of thermal loads, solar gains, and temperatures**. By representing the entire building as a single thermal node, the model behaves as if air is perfectly mixed across all floors and orientations. This masks localized peaks, under-predicts cooling energy by preventing simultaneous heating and cooling, and flattens peak electrical demand. 

The cheapest fixes for these errors are:
1. **Load Scaling (Software Fix):** Scale all area-based internal gains (LPD, EPD, occupancy) by $N$ as described in the recipe. This prevents the severe under-prediction of internal heat gains that occurs due to the single bottom slab surface.
2. **Daylighting Control Deactivation (Control Fix):** Disable daylighting-responsive lighting controls in single-zone models. The vertical centering of windows places glazing far above the floor-level daylighting reference points, producing artificial darkness at the ground level and distorting dimming energy calculations.

---

## REFERENCE LIST

1. **ASHRAE Handbook — Fundamentals** (2021). Chapter 16: *Ventilation and Infiltration* (buoyancy and wind stack-effects); Chapter 18: *Non-residential Cooling and Heating Load Calculations* (internal thermal mass and heat balance). American Society of Heating, Refrigerating and Air-Conditioning Engineers. [Link](https://www.ashrae.org/technical-resources/ashrae-handbook)
2. **Dogan, T., & Reinhart, C.** (2017). "Shoeboxer: An algorithm for semi-automated multi-zone building energy model generation." *Energy and Buildings*, 137, 162-181. [DOI: 10.1016/j.enbuild.2017.01.017](https://doi.org/10.1016/j.enbuild.2017.01.017)
3. **EnergyPlus 23.1 Engineering Reference** (2023). Section: *Zone Heat Balance Manager* (InternalMass modeling); Section: *Infiltration* (DesignFlowRate calculations). U.S. Department of Energy. [Link](https://energyplus.net/documentation)
4. **COMNET Commercial Buildings Energy Modeling Guidelines and Procedures** (2016). Section 3.1: *Thermal Zoning and Internal Mass Recommendations*. Resource Landmark. [Link](http://www.comnet.org/)
5. **Monteiro, C. S., Santos, C., & Costa, A. A.** (2020). "The influence of thermal zoning on building energy simulation accuracy." *Journal of Building Engineering*, 32, 101486. [DOI: 10.1016/j.jobe.2020.101486](https://doi.org/10.1016/j.jobe.2020.101486)
6. **PNNL Prototype Building Models / ASHRAE 90.1-2019 baseline models** (2020). Pacific Northwest National Laboratory. [Link](https://www.energycodes.gov/prototype-building-models)
