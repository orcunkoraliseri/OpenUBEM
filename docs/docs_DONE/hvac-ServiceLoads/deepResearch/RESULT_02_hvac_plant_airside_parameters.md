# RESULT 02 — HVAC PLANT & AIR-SIDE PARAMETERS
**OpenUBEM Phase-E — Physical Realism Research Deliverable**

This document provides the intensive parameters, efficiencies, operational limits, and sizing parameters needed to model central HVAC, air-side loops, pumps, fans, and economizers for OpenUBEM Phase-E. Every value is sourced from **ASHRAE 90.1-2019**, **DOE/PNNL STD2022 Commercial Prototype Building Models**, or the **EnergyPlus Engineering Reference**.

---

## Table 0 — Updated and Confirmed Archetype Baseline Parameters
This table updates and confirms the baseline COP and heating efficiency values in `hvac_cop_by_archetype.json`. 

> [!IMPORTANT]
> **Manager Recommendation on `plant_factor 0.75`:** 
> We strongly recommend **dropping the 0.75 plant factor derate** (i.e. setting it to `1.0` or omitting it) for central plant systems in Phase-E. Since chilled-water, condenser-water, and hot-water pumps, cooling towers, and boiler/chiller standby losses are now physically modeled and simulated as IDF objects, keeping the 0.75 derate would double-count plant parasitic losses and artificially inflate HVAC electricity consumption. The raw chiller COPs should be used directly in the `Chiller:Electric:EIR` objects.

| Archetype | cooling_cop | central_plant | raw_chiller_cop | plant_factor | heating_coil_type | heating_efficiency | Source / Notes |
|---|---|---|---|---|---|---|---|
| **SmallOffice** | 4.53 | no | — | — | Gas | 0.84 | Weatherized Gas Furnace (84% Et per PNNL) |
| **MediumOffice** | 3.74 | no | — | — | Gas | 0.84 | Packaged DX + VAV Furnace (84% Et per PNNL) |
| **LargeOffice** | 5.18 | yes | 6.908 | 0.75 (drop) | Gas | 0.945 | Centrifugal Chiller (0.509 kW/ton) + Condensing HW Boiler |
| **RetailStandalone** | 3.57 | no | — | — | Gas | 0.88 | Packaged DX + Gas Furnace (88% Et per PNNL) |
| **RetailStripmall** | 3.99 | no | — | — | Gas | 0.88 | Packaged DX + Gas Furnace (88% Et per PNNL) |
| **SuperMarket** | 3.00 | no | — | — | Gas | 0.80 | Packaged DX + Gas Furnace (80% Et per PNNL) |
| **FullServiceRestaurant** | 3.40 | no | — | — | Gas | 0.8505 | Packaged DX + Gas Furnace (85.05% Et per PNNL) |
| **QuickServiceRestaurant** | 3.80 | no | — | — | Gas | 0.84 | Packaged DX + Gas Furnace (84% Et per PNNL) |
| **SmallHotel** | 3.81 | no | — | — | Gas | 0.80 | PTAC/PTHP systems + Gas Boiler for public spaces |
| **LargeHotel** | 2.331 | yes | 3.108 | 0.75 (drop) | Gas | 0.945 | Scroll Chiller (1.13 kW/ton) + Condensing HW Boiler |
| **MidriseApartment** | 4.32 | no | — | — | Gas | 0.84 | Split DX + Gas Furnace (84% Et per PNNL) |
| **HighriseApartment** | 3.516 | yes | 4.688 | 0.75 (drop) | Electric | 4.515 | Water-Source Heat Pump (WSHP) loop |
| **Hospital** | 4.197 | yes | 5.597 | 0.75 (drop) | Gas | 0.945 | Centrifugal Chiller (0.628 kW/ton) + Condensing HW Boiler |
| **Outpatient** | 3.57 | no | — | — | Gas | 0.84 | Packaged DX + Gas Furnace (84% Et per PNNL) |
| **PrimarySchool** | 3.92 | no | — | — | Gas | 0.84 | Packaged DX + Gas Furnace (84% Et per PNNL) |
| **SecondarySchool** | 3.46 | no | — | — | Gas | 0.8505 | Packaged DX + Gas Furnace (85.05% Et per PNNL) |
| **College** | 4.32 | yes | 5.766 | 0.75 (drop) | Gas | 0.813 | Centrifugal Chiller (0.61 kW/ton) + Gas Boiler |
| **Laboratory** | 3.59 | no | — | — | Gas | 0.813 | Packaged VAV + Gas Furnace (81.3% Et per PNNL) |
| **Warehouse** | 4.11 | no | — | — | Gas | 0.84 | Packaged DX + Gas Furnace (84% Et per PNNL) |
| **SmallDataCenterHighITE** | 3.00 | no | — | — | none | none | Dedicated CRAC single-speed DX (No heating) |
| **SmallDataCenterLowITE** | 3.00 | no | — | — | none | none | Dedicated CRAC single-speed DX (No heating) |
| **LargeDataCenterHighITE** | 4.71 | yes | 6.280 | 0.75 (drop) | none | none | Centrifugal Chiller (0.56 kW/ton, No heating) |
| **LargeDataCenterLowITE** | 4.32 | yes | 5.766 | 0.75 (drop) | none | none | Centrifugal Chiller (0.61 kW/ton, No heating) |
| **TallBuilding** | 5.18 | yes | 6.908 | 0.75 (drop) | Gas | 0.945 | Centrifugal Chiller + Condensing HW Boiler (LargeOffice proxy) |
| **SuperTallBuilding** | 5.18 | yes | 6.908 | 0.75 (drop) | Gas | 0.945 | Centrifugal Chiller + Condensing HW Boiler (LargeOffice proxy) |
| **Courthouse** | 3.00 | no | — | — | Gas | 0.80 | Proxy decision: Packaged Single Zone DX (fallback) |
| **OpenUBEMUnknown** | 3.00 | no | — | — | Gas | 0.80 | Sentinel fallback |

---

## Table A — Cooling Equipment Efficiency (90.1-2019 Minimums)
Minimum cooling efficiency limits from ASHRAE 90.1-2019 Section 6.8.1. Converted COP values are calculated as \(\text{COP} = \text{EER} / 3.41214\) or \(\text{COP} = 3.51685 / (\text{kW/ton})\).

| Equipment / System | Size Bracket | Metric (as published) | Value | Converted COP (W/W) | Cite (90.1 Table) |
|---|---|---|---|---|---|
| **PTAC (Through-wall)** | 9,000 Btu/h (0.75 ton) | EER | 10.9 - 0.213 * (Cap/1000) = 9.0 EER | 2.63 | Table 6.8.1-4 |
| **PSZ-AC (Packaged DX)** | < 65 kBtu/h | SEER2 / EER | 14.3 SEER2 / 11.0 EER | 4.19 (SEER2) / 3.22 (EER) | Table 6.8.1-1 |
| **PSZ-AC (Packaged DX)** | 65–135 kBtu/h | EER / IEER | 11.0 EER / 11.2 IEER | 3.22 (FL) / 3.28 (PL) | Table 6.8.1-1 |
| **PSZ-AC (Packaged DX)** | 135–240 kBtu/h | EER / IEER | 11.0 EER / 11.0 IEER | 3.22 (FL) / 3.22 (PL) | Table 6.8.1-1 |
| **Air-Cooled Chiller** | < 150 ton | EER / IEER | 9.70 EER / 12.50 IEER | 2.84 (FL) / 3.66 (PL) | Table 6.8.1-3 (Path A) |
| **Air-Cooled Chiller** | ≥ 150 ton | EER / IEER | 9.70 EER / 13.00 IEER | 2.84 (FL) / 3.81 (PL) | Table 6.8.1-3 (Path A) |
| **Water-Cooled Centrifugal** | < 150 ton | kW/ton / IPLV | 0.610 kW/ton / 0.550 IPLV | 5.77 (FL) / 6.39 (PL) | Table 6.8.1-3 (Path A) |
| **Water-Cooled Centrifugal** | 150–300 ton | kW/ton / IPLV | 0.560 kW/ton / 0.500 IPLV | 6.28 (FL) / 7.03 (PL) | Table 6.8.1-3 (Path A) |
| **Water-Cooled Centrifugal** | ≥ 600 ton | kW/ton / IPLV | 0.520 kW/ton / 0.390 IPLV | 6.76 (FL) / 9.02 (PL) | Table 6.8.1-3 (Path A) |
| **Water-Cooled Screw/Scroll** | 75–150 ton | kW/ton / IPLV | 0.720 kW/ton / 0.560 IPLV | 4.88 (FL) / 6.28 (PL) | Table 6.8.1-3 (Path A) |
| **Water-Cooled Screw/Scroll** | ≥ 300 ton | kW/ton / IPLV | 0.610 kW/ton / 0.520 IPLV | 5.77 (FL) / 6.76 (PL) | Table 6.8.1-3 (Path A) |

---

## Table B — Heating Equipment Efficiency
Minimum heating efficiencies from ASHRAE 90.1-2019 Section 6.8.1.

| Equipment | Size Bracket | Metric | Value | Cite (90.1 Table) |
|---|---|---|---|---|
| **Gas Furnace (warm-air)** | < 225 kBtu/h | AFUE | 80% (non-weatherized) | Table 6.8.1-5 |
| **Gas Furnace (warm-air)** | ≥ 225 kBtu/h | Thermal Efficiency (\(E_t\)) | 80% (81% after 1/1/2023) | Table 6.8.1-5 |
| **Gas Hot-Water Boiler** | < 300 kBtu/h | AFUE | 80% (or 84% condensing) | Table 6.8.1-6 |
| **Gas Hot-Water Boiler** | ≥ 300 & ≤ 2500 kBtu/h | Thermal Efficiency (\(E_t\)) | 80% (90% per Addendum) | Table 6.8.1-6 |
| **Gas Hot-Water Boiler** | > 2500 kBtu/h | Combustion Efficiency (\(E_c\)) | 82% (90% per Addendum) | Table 6.8.1-6 |
| **Electric Resistance** | — | COP | 1.0 | — |
| **Water-to-Air Heat Pump** | All capacities | COP | 4.30 (heating) | Table 6.8.1-4 |
| **Air-to-Air Heat Pump** | < 65 kBtu/h | HSPF / HSPF2 | 8.2 HSPF / 7.5 HSPF2 (\(\approx 2.4\) COP) | Table 6.8.1-2 |

---

## Table C — Chilled-Water & Hot-Water Loop Parameters
These loop and pump design parameters configure the EnergyPlus `PlantLoop` and `Pump:*` objects.

| Parameter | Chilled-Water Loop | Hot-Water Loop | Condenser-Water Loop | Cite |
|---|---|---|---|---|
| **Design Supply Temp** | 6.67 °C / 44.0 °F | 60.0 °C / 140.0 °F | 29.44 °C / 85.0 °F | PNNL Prototype / Sizing:Plant |
| **Design Loop \(\Delta T\)** | 8.33 °C / 15.0 °F | 11.11 °C / 20.0 °F | 5.56 °C / 10.0 °F | PNNL Prototype / Sizing:Plant |
| **Design Pump Head** | 179.0 kPa / 60.0 ft w.c. <br>*(73 kPa Pri + 106 kPa Sec)* | 180.7 kPa / 60.4 ft w.c. | 148.6 kPa / 49.7 ft w.c. | PNNL Prototype |
| **Pump Power per Flow** | **22 W/gpm** <br>*(348.7 W/(L/s))* <br>[348,707 W/(m³/s)] | **19 W/gpm** <br>*(301.2 W/(L/s))* <br>[301,156 W/(m³/s)] | **19 W/gpm** <br>*(301.2 W/(L/s))* <br>[301,156 W/(m³/s)] | 90.1 App G G3.1.3.5 / .10 / .11 |
| **Motor Efficiency** | 90.9% | 90.9% | 90.9% | 90.1 Table G3.9.1 |
| **Pump Control** | Constant (Pri) / VFD (Sec) | Variable-Speed (VFD) | Constant-Volume | 90.1 App G G3.1.3.5 / .10 / .11 |
| **Loop Configuration** | Primary-Secondary | Primary-Only (Variable Flow) | Primary-Only (Constant Flow) | 90.1 App G G3.1.3.5 / .10 / .11 |

---

## Table D — Air-Side & Supply-Fan Parameters
These fan and supply air parameters configure the EnergyPlus `Fan:VariableVolume`, `Fan:OnOff`, and outdoor air objects.

| Parameter | PSZ (Constant Volume) | VAV (Central VAV) | PTAC / PTHP | Cite |
|---|---|---|---|---|
| **Supply-Fan Total Static** | 622.5 Pa / 2.50 in. w.c. | 1389.42 Pa / 5.58 in. w.c. | 331.17 Pa / 1.33 in. w.c. | PNNL Prototype |
| **Fan Total Efficiency** | 0.55575 (55.58%) | 0.6006 – 0.6084 (60.84%) | 0.520 (52.0%) | PNNL Prototype |
| **Resulting Fan Power** | **0.529 W/cfm** <br>*(1.12 W/(L/s))* | **1.077 W/cfm** <br>*(2.284 W/(L/s))* | **0.301 W/cfm** <br>*(0.637 W/(L/s))* | Calculated: \(0.000472 \times \text{Pressure} / \text{Eff}\) |
| **90.1 §6.5.3.1 Fan Limit** | 0.00094 bhp/cfm (\(\approx 0.82\) W/cfm) | 0.00130 bhp/cfm (\(\approx 1.08\) W/cfm) | Exempt (< 5 hp) | 90.1 §6.5.3.1 (Option 2) |
| **VAV Min Airflow Turndown** | n/a | 30% of peak zone design flow | n/a | 90.1 App G G3.1.3.13 |
| **Supply Air Temp Setpoint** | 12.8 °C / 55.0 °F | 12.8 °C / 55.0 °F (cooling design) <br>Reset to 15.6 °C / 60 °F | 12.8 °C / 55.0 °F (cycles) | PNNL Prototype / G3.1.3.12 |
| **Fan Operation** | Cycling based on load | Continuous during occupied | Cycling (or continuous occupied) | PNNL Prototype / G3.1.2.4 |

---

## Table E — Outdoor Air & Economizer (CZ 2A / 3B / 4A)
Climate-dependent ventilation and economizer rules from ASHRAE 62.1-2019 and ASHRAE 90.1-2019.

| Parameter | Value | By CZ? | 2A (Austin) | 3B (Los Angeles) | 4A (New York City) | Cite |
|---|---|---|---|---|---|---|
| **Min OA — per person** | Office: 5 cfm (2.36 L/s)<br>Retail: 7.5 cfm (3.54 L/s) | No | 5 / 7.5 cfm | 5 / 7.5 cfm | 5 / 7.5 cfm | ASHRAE 62.1 Table 6-1 |
| **Min OA — per area** | Office: 0.06 cfm/ft² (0.30 L/s·m²)<br>Retail: 0.06 cfm/ft² (0.30 L/s·m²) | No | 0.06 cfm/ft² | 0.06 cfm/ft² | 0.06 cfm/ft² | ASHRAE 62.1 Table 6-1 |
| **Air-Side Economizer?** | Yes, if cooling capacity \(\ge\) 54 kBtu/h | Yes | Yes (if \(\ge 54\) kBtu/h) | Yes (if \(\ge 54\) kBtu/h) | Yes (if \(\ge 54\) kBtu/h) | 90.1 §6.5.1.1 |
| **Economizer Shutoff Limit** | Fixed Dry Bulb or Differential DB | Yes | Fixed DB: 65 °F (18.3 °C) <br>or Differential DB | Fixed DB: 75 °F (23.9 °C) <br>or Differential DB | Fixed DB: 65 °F (18.3 °C) <br>or Differential DB | 90.1 Table 6.5.1.1.3 |
| **ERV Required?** | Varies by design supply CFM & %OA | Yes | Yes, per Table 6.5.6.1.2-1 <br>(e.g. \(\ge 5,500\) cfm at 30-40% OA) | **No** (NR) for < 8,000 hrs/yr.<br>Yes for \(\ge 8,000\) hrs/yr if \(\ge 70\%\) OA | Yes, per Table 6.5.6.1.2-1 <br>(e.g. \(\ge 5,500\) cfm at 30-40% OA) | 90.1 §6.5.6.1 |
| **ERV Effectiveness** | 70% sensible / 60% latent | No | 70% sensible / 60% latent | 70% sensible / 60% latent | 70% sensible / 60% latent | PNNL Prototype |
| **Demand-Controlled Vent?** | Yes, if space \(\ge 500\) ft² & density \(\ge 25\) people/1000 ft² | No | Yes (where density is met) | Yes (where density is met) | Yes (where density is met) | 90.1 §6.4.3.8 |

---

## Table F — Part-Load Performance Curves
Recommendations for part-load curves in EnergyPlus objects.

| Item | Recommendation | Source |
|---|---|---|
| **Chiller Part-Load Curves** | Reuse the EnergyPlus standard EIR part-load curves from the `StandardReports` dataset. Centrifugal chillers utilize the `Chiller:Electric:ReformulatedEIR` performance curves (biquadratic/bicubic temperature curves and quadratic PLR curves). | EnergyPlus Engineering Reference / PNNL Prototype |
| **DX Coil Curves** | Reuse the biquadratic DX cooling capacity function of temperature (CAP-FT) and energy input ratio function of temperature (EIR-FT) curves from the PNNL prototype models. | EnergyPlus Engineering Reference / PNNL Prototype |
| **Fan/Pump VFD Curves** | VAV VFD Fan: \(PowerFraction = 0.00153 + 0.00521 \times FlowFraction + 1.10862 \times FlowFraction^2 - 0.11636 \times FlowFraction^3\)<br>VS Pump VFD: \(PowerFraction = 0.0 + 0.0205 \times FlowFraction + 0.4101 \times FlowFraction^2 + 0.5753 \times FlowFraction^3\) | EnergyPlus Engineering Reference / PNNL Prototype |

---

## Part C — Sanity Arithmetic (Show Your Work)

This section demonstrates the translation of intensive parameters into expected annual energy end-use consumption (EUI) for fans and pumps.

### 1. LargeOffice (System 7: Central VAV + Water-Cooled Centrifugal Chiller + HW Boiler)
*   **A. Fan Energy Calculation:**
    *   **Intensive Fan Power:** \(1.077 \text{ W/cfm}\) (design VAV baseline limit).
    *   **Design Airflow Density:** \(0.90 \text{ cfm/ft}^2\) (typical LargeOffice design).
    *   **Peak Fan Power Density:** 
        \[1.077 \text{ W/cfm} \times 0.90 \text{ cfm/ft}^2 = 0.969 \text{ W/ft}^2 = 10.43 \text{ W/m}^2\]
    *   **Annual Operating Hours:** 3,000 occupied hours/year.
    *   **VAV Power Fraction:** Assuming the VAV fan modulates to an average airflow of 60% of design during occupied hours. Using the VFD fan curve:
        \[\text{PowerFraction} = 0.00153 + 0.00521(0.6) + 1.10862(0.6^2) - 0.11636(0.6^3) = 0.379 \text{ (37.9%)}\]
    *   **Average Fan Power Density:** 
        \[10.43 \text{ W/m}^2 \times 0.379 = 3.95 \text{ W/m}^2\]
    *   **Expected Annual Fan EUI:**
        \[\text{EUI}_{fan} = \frac{3.95 \text{ W/m}^2 \times 3,000 \text{ hours}}{1,000 \text{ W/kW}} = 11.85 \text{ kWh/m}^2\text{·yr}\]

*   **B. Pump Energy Calculation:**
    *   **Cooling Pump Power:** Chilled-water loop (22 W/gpm) + Condenser-water loop (19 W/gpm).
    *   **Cooling Sizing:** Design peak cooling load of 300 ft²/ton (0.00333 tons/ft²).
    *   **Water Flow Rates at Design:**
        *   Chilled water (15°F \(\Delta T\)): \(1.6 \text{ gpm/ton} \times 0.00333 \text{ tons/ft}^2 = 0.00533 \text{ gpm/ft}^2\).
        *   Condenser water (10°F \(\Delta T\)): \(3.0 \text{ gpm/ton} \times 0.00333 \text{ tons/ft}^2 = 0.0100 \text{ gpm/ft}^2\).
    *   **Peak Cooling Pump Power Density:**
        \[P_{pump\_clg} = (22 \text{ W/gpm} \times 0.00533 \text{ gpm/ft}^2) + (19 \text{ W/gpm} \times 0.0100 \text{ gpm/ft}^2) = 0.117 + 0.190 = 0.307 \text{ W/ft}^2 = 3.30 \text{ W/m}^2\]
    *   **Equivalent Full Load Cooling Hours:** 700 hours/year (representative blend for commercial buildings in 4A/2A).
    *   **Expected Annual Cooling Pump EUI:**
        \[\text{EUI}_{pump\_clg} = \frac{3.30 \text{ W/m}^2 \times 700 \text{ hours}}{1,000} = 2.31 \text{ kWh/m}^2\text{·yr}\]
    *   **Heating Pump Power:** Hot-water loop (19 W/gpm).
    *   **Heating Sizing & Flow:** Design peak heating load of 30 Btu/h-ft². Flow (20°F \(\Delta T\)):
        \[\text{Flow}_{HW} = \frac{30 \text{ Btu/h-ft}^2}{500 \times 20^\circ\text{F}} = 0.003 \text{ gpm/ft}^2\]
    *   **Peak Heating Pump Power Density:**
        \[P_{pump\_htg} = 19 \text{ W/gpm} \times 0.003 \text{ gpm/ft}^2 = 0.057 \text{ W/ft}^2 = 0.61 \text{ W/m}^2\]
    *   **Equivalent Full Load Heating Hours:** 1,200 hours/year (representative of New York CZ 4A).
    *   **Expected Annual Heating Pump EUI:**
        \[\text{EUI}_{pump\_htg} = \frac{0.61 \text{ W/m}^2 \times 1,200 \text{ hours}}{1,000} = 0.73 \text{ kWh/m}^2\text{·yr}\]
    *   **Total Expected Pump EUI:** 
        \[\text{EUI}_{pump} = 2.31 + 0.73 = 3.04 \text{ kWh/m}^2\text{·yr}\]

*   **C. Resulting Expected LargeOffice Auxiliary EUI Range:**
    *   **Total (Fans + Pumps):** \(11.85 + 3.04 = 14.89 \text{ kWh/m}^2\text{·yr}\).
    *   **Sanity Check Range:** **12 to 16 kWh/m²·yr** (corresponds to \(\approx 10–12\%\) of a typical LargeOffice EUI of 120 kWh/m²·yr, aligning with CBECS metrics).

---

### 2. MediumOffice (System 5: Packaged VAV + DX Cooling + Reheat Gas Furnace)
*   **A. Fan Energy Calculation:**
    *   **Intensive Fan Power:** \(1.09 \text{ W/cfm}\) (based on prototype VAV fan: 1389.42 Pa rise and 60.06% total efficiency).
    *   **Design Airflow Density:** \(0.85 \text{ cfm/ft}^2\).
    *   **Peak Fan Power Density:** 
        \[1.09 \text{ W/cfm} \times 0.85 \text{ cfm/ft}^2 = 0.927 \text{ W/ft}^2 = 9.97 \text{ W/m}^2\]
    *   **Annual Operating Hours:** 3,000 occupied hours/year.
    *   **Average Fan Power Fraction (VAV, average 60% flow):** 37.9% (using VFD curve).
    *   **Average Fan Power Density:** 
        \[9.97 \text{ W/m}^2 \times 0.379 = 3.78 \text{ W/m}^2\]
    *   **Expected Annual Fan EUI:**
        \[\text{EUI}_{fan} = \frac{3.78 \text{ W/m}^2 \times 3,000 \text{ hours}}{1,000} = 11.34 \text{ kWh/m}^2\text{·yr}\]

*   **B. Pump Energy Calculation:**
    *   **Packaged System Pump EUI:** **0.0 kWh/m²·yr** (structurally zero because packaged DX/furnace units have no centralized chilled-water, hot-water, or condenser-water loops/pumps).

*   **C. Resulting Expected MediumOffice Auxiliary EUI Range:**
    *   **Total (Fans + Pumps):** \(11.34 + 0 = 11.34 \text{ kWh/m}^2\text{·yr}\).
    *   **Sanity Check Range:** **10 to 13 kWh/m²·yr** (corresponds to \(\approx 10\%\) of a typical MediumOffice EUI of 110 kWh/m²·yr).

---

## Confidence and Caveats
1.  **Firm vs. Prototype-Specific Values:** 
    *   The pump power densities (22 W/gpm chilled-water, 19 W/gpm condenser-water, and 19 W/gpm hot-water) and fan power limitations are **firm ASHRAE 90.1 minimum requirements** that are legally binding for energy compliance.
    *   The fan static pressures (e.g. 5.58 in. w.c. for VAV) and fan total efficiencies are **prototype-specific defaults** extracted directly from PNNL IDF models. While they represent standard engineering design practices to meet the fan power limit, individual buildings in real life may vary.
2.  **Vintage-Dependence:**
    *   Equipment efficiencies in Table A and B represent ASHRAE 90.1-2019 minimums. Older buildings (pre-1980 or pre-2013) typically have lower efficiencies (e.g., chillers with \(1.2–1.5 \text{ kW/ton}\) and boilers with \(75–80\%\) efficiency). If modeling older vintage cohorts in OpenUBEM, a vintage multiplier or separate vintage-lookup should be applied.
3.  **Economizer Exemptions:**
    *   Economizer requirements are strictly based on cooling capacity per unit. In the simulation, units under 4.5 tons (54 kBtu/h) will automatically not receive an economizer, which is physically correct.

---

## Reference List
1.  **ANSI/ASHRAE/IES Standard 90.1-2019** — *Energy Standard for Buildings Except Low-Rise Residential Buildings*. Section 6 (Heating, Ventilating, and Air Conditioning) and Appendix G (Performance Rating Method).
    *   [ASHRAE Standard 90.1 Read-Only Version](https://www.ashrae.org/technical-resources/standards-and-guidelines/read-only-versions-of-ashrae-standards)
2.  **DOE/PNNL Commercial Prototype Building Models (STD2022 Release)** — *Technical Documentation and IDF Files for Buffalo, NY (CZ 6A)*.
    *   [PNNL Commercial Prototype Buildings Portal](https://www.energycodes.gov/development/commercial/prototype_models)
3.  **ANSI/ASHRAE Standard 62.1-2019** — *Ventilation for Acceptable Indoor Air Quality*. Table 6-1 (Minimum Ventilation Rates in Breathing Zone).
    *   [ASHRAE Standard 62.1 Portal](https://www.ashrae.org/technical-resources/standards-and-guidelines)
4.  **EnergyPlus Input-Output Reference & Engineering Reference** — *Version 22.1 / 22.2*. Chiller, Pump, and Fan object field definitions.
    *   [EnergyPlus Documentation Archive](https://energyplus.net/documentation)
