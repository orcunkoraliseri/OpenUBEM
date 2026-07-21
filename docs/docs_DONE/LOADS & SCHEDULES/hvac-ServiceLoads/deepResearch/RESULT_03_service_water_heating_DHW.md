# Service Hot Water (DHW) Archetype Parameter Research

This report compiles domestic/service hot water (DHW) parameters across all 30 OpenUBEM archetypes to support transitioning from post-process estimates to physical EnergyPlus simulations using `WaterHeater:Mixed`, `WaterUse:Equipment`, and `WaterUse:Connections` objects.

---

## 1. Required Output Tables

### Table 1 — Hot-water demand intensity (per archetype)

The table below lists peak hot-water flow rates, normalized flow rates, and annual hot-water volume intensities for each of the 30 OpenUBEM archetypes. Conversions are based on baseline conditioned floor areas.

| Archetype | Peak hot-water flow (gpm) | Peak hot-water flow (L/h) | Peak flow normalized (L/h·m²) | Peak flow normalized (gal/h·ft²) | Annual HW volume EUI (L/m²·yr) | Annual HW volume EUI (gal/ft²·yr) | Source & Method |
|---|---|---|---|---|---|---|---|
| **College** | 0.5800 | 131.73 | 0.020533 | 0.000504 | 31.10 | 0.7633 | DOE Prototype (90.1-2019) |
| **Courthouse** | 1.7435 | 396.00 | 0.027785 | 0.000682 | 41.04 | 1.0073 | Proxy (LargeOffice) |
| **FullServiceRestaurant** | 2.2167 | 503.46 | 0.492473 | 0.012089 | 1352.00 | 33.1812 | DOE Prototype (STD2022) |
| **HighriseApartment** | 1.1902 | 270.32 | 0.114983 | 0.002822 | 527.97 | 12.9576 | DOE Prototype (STD2022) |
| **Hospital** | 3.3800 | 767.68 | 0.038596 | 0.000947 | 154.96 | 3.8032 | DOE Prototype (STD2022) |
| **Laboratory** | 1.1869 | 269.58 | 0.016121 | 0.000396 | 26.58 | 0.6523 | DOE Prototype (90.1-2019) |
| **LargeDataCenterHighITE** | 0.0000 | 0.00 | 0.000000 | 0.000000 | 0.00 | 0.0000 | DOE Prototype (STD2019) |
| **LargeDataCenterLowITE** | 0.0000 | 0.00 | 0.000000 | 0.000000 | 0.00 | 0.0000 | DOE Prototype (STD2019) |
| **LargeHotel** | 9.5088 | 2159.68 | 0.370219 | 0.009088 | 1073.32 | 26.3417 | DOE Prototype (STD2022) |
| **LargeOffice** | 1.7435 | 396.00 | 0.027785 | 0.000682 | 41.04 | 1.0073 | DOE Prototype (STD2022) |
| **LargeOfficeDetailed** | 1.7435 | 396.00 | 0.027785 | 0.000682 | 41.04 | 1.0073 | Inherits LargeOffice |
| **MediumOffice** | 0.8500 | 193.06 | 0.038749 | 0.000951 | 55.97 | 1.3736 | DOE Prototype (STD2022) |
| **MediumOfficeDetailed** | 0.8500 | 193.06 | 0.038749 | 0.000951 | 55.97 | 1.3736 | Inherits MediumOffice |
| **MidriseApartment** | 1.6042 | 364.34 | 0.154976 | 0.003804 | 711.60 | 17.4644 | DOE Prototype (STD2022) |
| **OpenUBEMUnknown** | 0.8500 | 193.06 | 0.038749 | 0.000951 | 55.97 | 1.3736 | Proxy (MediumOffice) |
| **Outpatient** | 1.0012 | 227.40 | 0.059779 | 0.001467 | 130.07 | 3.1923 | DOE Prototype (STD2022) |
| **PrimarySchool** | 0.8354 | 189.74 | 0.055231 | 0.001356 | 83.66 | 2.0532 | DOE Prototype (STD2022) |
| **QuickServiceRestaurant** | 1.5213 | 345.53 | 0.743567 | 0.018252 | 1669.90 | 40.9832 | DOE Prototype (STD2022) |
| **RetailStandalone** | 0.2996 | 68.04 | 0.029660 | 0.000728 | 59.67 | 1.4644 | DOE Prototype (STD2022) |
| **RetailStripmall** | 0.2097 | 47.63 | 0.022785 | 0.000559 | 36.43 | 0.8940 | DOE Prototype (STD2022) |
| **SecondarySchool** | 11.8566 | 2692.93 | 0.274901 | 0.006748 | 416.41 | 10.2196 | DOE Prototype (STD2022) |
| **SmallDataCenterHighITE** | 0.0000 | 0.00 | 0.000000 | 0.000000 | 0.00 | 0.0000 | DOE Prototype (90.1-2019) |
| **SmallDataCenterLowITE** | 0.0000 | 0.00 | 0.000000 | 0.000000 | 0.00 | 0.0000 | DOE Prototype (90.1-2019) |
| **SmallHotel** | 4.9022 | 1113.40 | 0.277409 | 0.006810 | 804.25 | 19.7382 | DOE Prototype (STD2022) |
| **SmallOffice** | 0.0642 | 14.57 | 0.013504 | 0.000331 | 27.95 | 0.6861 | DOE Prototype (STD2022) |
| **SmallOfficeDetailed** | 0.0642 | 14.57 | 0.013504 | 0.000331 | 27.95 | 0.6861 | Inherits SmallOffice |
| **SuperMarket** | 0.2996 | 68.04 | 0.029660 | 0.000728 | 59.67 | 1.4644 | Proxy (RetailStandalone) |
| **SuperTallBuilding** | 84.7354 | 19245.50 | 0.370137 | 0.009086 | 744.59 | 18.2741 | DOE Custom Prototype |
| **TallBuilding** | 61.6471 | 14001.57 | 0.409614 | 0.010055 | 824.01 | 20.2231 | DOE Custom Prototype |
| **Warehouse** | 0.1280 | 29.07 | 0.006322 | 0.000155 | 11.56 | 0.2838 | DOE Prototype (STD2022) |

---

### Table 2 — Water heater (per archetype or per archetype group)

Water heater configurations are grouped by building sector to reflect typical central service hot water systems modeled in ASHRAE 90.1 prototypes.

| Archetype (or group) | Heater fuel | Type (storage / instantaneous) | Thermal efficiency ($E_t$ or UEF) | Standby loss coefficient | Supply setpoint | Cite |
|---|---|---|---|---|---|---|
| **Residential** <br>(Midrise/Highrise Apartment) | Midrise: **Electricity** <br>Highrise: **NaturalGas** | Storage | Gas: **$E_t$ = 80%** <br>Electric: **UEF = 93% (1.00)** | Gas: **7.56 W/K** (13.6 Btu/h·F)<br>Elec: **2.01 W/K** (3.6 Btu/h·F) | **60.0°C / 140°F** | ASHRAE 90.1 Table 7.8 & baseline prototypes |
| **Lodging** <br>(Small/Large Hotel) | **NaturalGas** (with Elec Booster) | Storage | Gas: **$E_t$ = 95%** (Condensing)<br>Booster: **$E_t$ = 100%** | Main Tank: **7.56 W/K** (13.6 Btu/h·F)<br>Booster: **0 W/K** (Point-of-use) | Main: **60.0°C / 140°F**<br>Booster: **82.2°C / 180°F** | ASHRAE 90.1 Table 7.8 & baseline prototypes |
| **Healthcare** <br>(Hospital/Outpatient) | **NaturalGas** (with Elec Booster) | Storage | Gas: **$E_t$ = 95%** (Condensing)<br>Booster: **$E_t$ = 100%** | Main Tank: **7.56 W/K** (13.6 Btu/h·F)<br>Booster: **0 W/K** (Point-of-use) | Main: **60.0°C / 140°F**<br>Booster: **82.2°C / 180°F** | ASHRAE 90.1 Table 7.8 & baseline prototypes |
| **Food service** <br>(Full- / Quick-Service Rest.) | **NaturalGas** (with Elec Booster) | Storage | Gas: **$E_t$ = 95%** (Condensing)<br>Booster: **$E_t$ = 100%** | Main Tank: **7.56 W/K** (13.6 Btu/h·F)<br>Booster: **0 W/K** (Point-of-use) | Main: **60.0°C / 140°F**<br>Booster: **82.2°C / 180°F** | ASHRAE 90.1 Table 7.8 & baseline prototypes |
| **Education** <br>(Schools/College) | **NaturalGas** (with Elec Booster) | Storage | Gas: **$E_t$ = 80.5%**<br>Booster: **$E_t$ = 100%** | Main Tank: **7.56 W/K** (13.6 Btu/h·F)<br>Booster: **0 W/K** (Point-of-use) | Main: **60.0°C / 140°F**<br>Booster: **82.2°C / 180°F** | ASHRAE 90.1 Table 7.8 & baseline prototypes |
| **Office / retail / warehouse** | Mid/Large: **NaturalGas** <br>Small/Strip/Whse: **Electricity** | Storage | Gas: **$E_t$ = 80.8%**<br>Electric: **$E_t$ = 100%** | Gas: **7.56 W/K** (13.6 Btu/h·F)<br>Elec: **2.01 W/K** (3.6 Btu/h·F) | **60.0°C / 140°F** | ASHRAE 90.1 Table 7.8 & baseline prototypes |

---

### Table 3 — Mains / inlet water temperature by city (seasonal)

Calculations are based on the Craig Christensen and Jay Burch correlation method (`Site:WaterMainsTemperature` object in EnergyPlus). The input dry-bulb outdoor air temperatures are extracted directly from TMYx climate files.

$$T_{\text{mains}} = (T_{\text{avg}} + 6^{\circ}\text{F}) + \text{ratio} \times \left( \frac{\Delta T_{\text{max}}}{2} \right) \times \sin\left[0.986 \times (\text{day} - 15 - \text{lag}) - 90\right]$$

Where:
- $\text{ratio} = 0.4 + 0.01 \times (T_{\text{avg}} - 44^{\circ}\text{F})$
- $\text{lag} = 35 - 1.0 \times (T_{\text{avg}} - 44^{\circ}\text{F})$

| City (climate zone) | Annual-Avg Mains Temp (°C / °F) | Winter Low (°C / °F) | Summer High (°C / °F) | Correlation Inputs & Method | Source File |
|---|---|---|---|---|---|
| **New York City** (4A) | **16.63°C / 61.94°F** | **10.32°C / 50.58°F** | **22.94°C / 73.30°F** | $T_{\text{avg,air}}$ = 13.30°C (55.94°F)<br>$\Delta T_{\text{max,air}}$ = 24.30°C (43.74°F)<br>ratio = 0.5194, lag = 23.06 days | Central Park Obs, NY TMYx (2011-2025) |
| **Los Angeles** (3B) | **20.83°C / 69.50°F** | **18.81°C / 65.86°F** | **22.86°C / 73.14°F** | $T_{\text{avg,air}}$ = 17.50°C (63.50°F)<br>$\Delta T_{\text{max,air}}$ = 6.80°C (12.24°F)<br>ratio = 0.5950, lag = 15.50 days | LAX Airport, CA TMYx (2011-2025) |
| **Austin** (2A) | **23.73°C / 74.72°F** | **17.52°C / 63.54°F** | **29.95°C / 85.90°F** | $T_{\text{avg,air}}$ = 20.40°C (68.72°F)<br>$\Delta T_{\text{max,air}}$ = 19.20°C (34.56°F)<br>ratio = 0.6472, lag = 10.28 days | Camp Mabry ANGB, TX TMYx (2011-2025) |

---

### Table 4 — Zone-gain split & distribution losses

This table shows the split of hot-water energy used in the building zones that returns as heat gain to the zone versus going directly down the drain, along with recirculation pump characteristics.

| Parameter | Value | Notes | Source |
|---|---|---|---|
| Fraction of DHW load returned to zone as **sensible** gain | **0.20** (20%) | Converted to space heat gain (showers, sinks) | Prototype `WaterUse:Equipment` fraction schedules |
| Fraction returned as **latent** gain | **0.05** (5%) | Evaporated moisture heat gain to space | Prototype `WaterUse:Equipment` fraction schedules |
| Fraction lost to **drain** (no zone gain) | **0.75** (75%) | Water directly leaving zone drain | Derived ($1.0 - 0.20 - 0.05$) |
| **Recirculation pump present?** | **Yes** / **No** | **Yes**: Midrise/Highrise Apartment, Hotels, Hospital, Outpatient, FullServiceRestaurant, SecondarySchool, College, Laboratory, TallBuilding, SuperTallBuilding. <br>**No**: Offices, Retail, Warehouse, PrimarySchool, QuickServiceRestaurant. | Baseline IDF plant loop definitions |
| **Recirculation pump power / loss adder** | Head: **29,891 Pa** <br>Eff: **30%** <br>Control: **Intermittent** | Design head is equivalent to 10 ft of water (3.05 m H2O). Design motor efficiency is 30%. Power is autosized based on design loop flow. Loop pipes are modeled as adiabatic. | Prototype `Pump:ConstantSpeed` definitions |

---

### Table 5 — DHW draw schedule

Below are the names of the primary schedules used to define the domestic hot water draw profiles, along with summaries of their peak fractions.

| Archetype group | Peak-fraction profile | Reference schedule name | Source |
|---|---|---|---|
| **Residential** <br>(Apartments) | Morning peak (1.00 at 8:00) and evening peak (0.86 at 19:00). Sleep hours drop to 0.01 at 3:00. | `APT_DHW_SCH` | DOE Commercial Prototype Building Models (Residential Compact Schedule) |
| **Lodging** <br>(Hotels) | Weekdays: Morning peak (0.80 at 8:00), evening peak (0.60 at 22:00). Weekends: Shifted morning peak (0.80 at 9:00). | `GuestRoom_SWH_Sch` <br>`GuestRoom_SHW_Sch` | DOE Commercial Prototype Building Models (Lodging Occupancy-Driven Draw) |
| **Food service** <br>(Restaurants) | Dual peaks representing meal-time dishwasher loads. Lunch peak (0.82 at 12:00) and dinner peak (0.82 at 14:00 and 18:00). | `BLDG_SWH_SCH` | DOE Commercial Prototype Building Models (SitDown/FastFood Restaurants) |
| **Office / retail / education** | Midday peak (0.90 at 13:00) representing lunch breaks and restroom use. Drops to 0 during unoccupied hours. | `BLDG_SWH_SCH` <br>`Office DHW Schedule` <br>`Type1_SWH_SCH` | DOE Commercial Prototype Building Models (Business Hours handwashing) |

---

## 2. Sector-Level Details & Normalizing Basis

### Residential (Apartments)
- **Normalizing Basis**: The peak DHW load in residential archetypes is derived from unit occupancy and fixture flow rates. The Midrise Apartment baseline has a peak hot-water draw of 1.604 gpm (364.34 L/h) for 32 apartments, which equates to **0.050 gpm (3.0 gal/h) per apartment unit**. Highrise Apartment has a peak flow of 1.190 gpm (270.32 L/h) for 24 apartment units in the active simulated zone, also equating to **0.050 gpm (3.0 gal/h) per unit**.
- **Conversion to Floor Area**: Division by conditioned floor area yields a normalized peak flow rate of **0.154976 L/h·m²** for Midrise and **0.114983 L/h·m²** for Highrise.

### Lodging (Hotels)
- **Normalizing Basis**: The peak DHW load is calculated per guest room. Small Hotel has 77 guest rooms and a peak hot-water draw of 4.902 gpm (1113.40 L/h), which is **0.0637 gpm (3.82 gal/h) per room**. Large Hotel has 122 guest rooms (with 61 rooms in the active simulated zone) and a peak draw of 9.509 gpm (2159.68 L/h), yielding **0.1559 gpm (9.35 gal/h) per room** to account for the larger laundry and kitchen facilities.
- **Conversion to Floor Area**: Division by conditioned floor area yields a normalized peak flow rate of **0.277409 L/h·m²** for Small Hotel and **0.370219 L/h·m²** for Large Hotel.

### Food Service (Restaurants)
- **Normalizing Basis**: Peak DHW loads are driven by kitchen dishwashing operations and are highly intensive. FullServiceRestaurant has a peak draw of 2.217 gpm (503.46 L/h) over a floor area of 1,022.31 m², which normalizes to **0.492473 L/h·m²**. QuickServiceRestaurant has a peak draw of 1.521 gpm (345.53 L/h) over a floor area of 464.69 m², normalizing to **0.743567 L/h·m²** (the highest EUI intensity of all commercial types).

### Offices, Retail, and Warehouses
- **Normalizing Basis**: Handwashing in restrooms is the sole driver. Peak flow rates are small and directly proportional to occupancy. Medium Office has 268 people (density of 18.58 m²/person), with a peak draw of 0.850 gpm (193.06 L/h) yielding **0.19 gal/h per person**. Standalone Retail has a peak draw of 0.2996 gpm (68.04 L/h) over 2,293.99 m² (0.029660 L/h·m²), which is also used as a direct proxy for Supermarket. Warehouses have the lowest hot-water demand of all, with a peak flow of 0.128 gpm (29.07 L/h) over 4,598.25 m² (0.006322 L/h·m²).

---

## 3. Confidence and Caveats

- **Negligible DHW Loads**: Data centers (`SmallDataCenterHighITE`, `SmallDataCenterLowITE`, `LargeDataCenterHighITE`, `LargeDataCenterLowITE`) are modeled with zero DHW loads (0 gpm peak flow and 0 EUI) as they are unoccupied server facilities with no restrooms or kitchens.
- **Recirculation Loops**: Recirculation loops are modeled as adiabatic pipes (`Pipe:Adiabatic`) in the baseline prototypes, meaning thermal losses are ignored, and energy is consumed solely by the pump and water heater. The circulator pump is a constant speed pump operating with a head of 29,891 Pa (10 ft H2O) and a low motor efficiency of 30%, which is typical for fractional horsepower domestic hot water circulators.
- **Sentinel Proxies**: Courthouse is mapped to the `LargeOffice` prototype and `OpenUBEMUnknown` is mapped to the `MediumOffice` prototype. These choices represent conservative handwashing-only loads suitable for general commercial operations.

---

## 4. References

1. **DOE Commercial Prototype Building Models (STD2022 Release)**, Pacific Northwest National Laboratory (PNNL), U.S. Department of Energy. [PNNL Prototypes](https://www.energycodes.gov/development/commercial/prototype_models).
2. **ASHRAE Standard 90.1-2019**, *Energy Standard for Buildings Except Low-Rise Residential Buildings*, Section 7 "Service Water Heating" and Table 7.8 "Performance Requirements for Water-Heating Equipment".
3. **ASHRAE Handbook — HVAC Applications (2019)**, Chapter 50 "Service Water Heating", American Society of Heating, Refrigerating and Air-Conditioning Engineers.
4. **Craig Christensen and Jay Burch (2001)**, *Water Mains Temperature Correlation*, National Renewable Energy Laboratory (NREL).
5. **Climate.OneBuilding.Org**, TMYx weather database for New York, California, and Texas stations. [OneBuilding Weather Data](https://climate.onebuilding.org).
6. **EnergyPlus Input-Output Reference (v22.1)**, *Site:WaterMainsTemperature* and *WaterHeater:Mixed* objects.
