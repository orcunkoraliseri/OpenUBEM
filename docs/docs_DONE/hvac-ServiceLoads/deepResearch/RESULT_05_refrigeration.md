# RESULT_05_refrigeration — Supermarket Cases/Racks + Walk-Ins with Zone Case Credit

This report documents the commercial refrigeration parameters for OpenUBEM Phase-E simulation integration. The findings are based on the authoritative primary sources: the **U.S. DOE Commercial Reference Building — Supermarket** model (using the standard `Supermarket_V22.1.idf` baseline), the **PNNL/DOE Commercial Prototype Building Models (STD2022/STD2013)**, the **EnergyPlus Input-Output & Engineering References (v22.1.0)**, and the **ASHRAE Handbook — Refrigeration**.

---

## 1. REQUIRED OUTPUT TABLES

### Table 1 — Lumped refrigeration energy intensity (fallback basis)

| Archetype | Refrigeration energy intensity (kWh/m²·yr) | Refrigeration energy intensity (kWh/ft²·yr) | Share of whole-building site energy (%) | Source |
|---|---|---|---|---|
| **SuperMarket** | 309.15 | 28.72 | 50.0% | ESPM-2024 (618.3 kWh/m²·yr national median) × 50.0% `refrig` fraction in `enduse_fractions_table4.json` |
| **FullServiceRestaurant** (walk-ins) | 154.08 | 14.31 | 15.0% | ESPM-2024 (1027.2 kWh/m²·yr national median) × 15.0% `refrig` fraction in `enduse_fractions_table4.json` |
| **QuickServiceRestaurant** (walk-ins) | 190.55 | 17.70 | 15.0% | ESPM-2024 (1270.3 kWh/m²·yr national median) × 15.0% `refrig` fraction in `enduse_fractions_table4.json` (FSR proxy) |
| **LargeHotel** (kitchen cold storage) | 3.98 | 0.37 | 2.0% | ESPM-2024 (198.8 kWh/m²·yr national median) × 2.0% `refrig` fraction in `enduse_fractions_table4.json` |
| **Hospital** (kitchen / morgue / pharmacy) | 7.39 | 0.69 | 1.0% | ESPM-2024 (739.2 kWh/m²·yr national median) × 1.0% `refrig` fraction in `enduse_fractions_table4.json` |
| **SuperMarket** — refrigeration as % of total store electricity | — | — | 50% to 60% | NREL Supermarket Reference Model (Deru et al. 2011) / PNNL Prototype Supermarket |

*Note: EUI values are based on the national median site energy intensities from the ENERGY STAR Portfolio Manager (ESPM-2024) database and the approved end-use splits in `enduse_fractions_table4.json`.*

---

### Table 2 — Display-case parameters (physical model — SuperMarket)

* **Store-Size Basis:** Total floor area of **4,181 m² (45,000 ft²)**, representing NREL's standard supermarket baseline.
* **Sales Floor Area:** **3,437 m² (37,000 ft²)**.
* **Total Remote Case Length:** **89.3 m (293 ft)** (representing a typical case-mix ratio of **0.021 m of case length per m² of total floor area**).

| Case type | Operating temp (°C / °F) | Rated cooling capacity per unit length (W/m) | Rated cooling capacity per unit length (Btu/h·ft) | Case length basis (m per store) | Latent heat ratio (LHR) | Defrost type + energy | Case fan + lighting (W/m) | Source |
|---|---|---|---|---|---|---|---|---|
| **Low-temp frozen** (reach-in/door) | -23.3 / -9.9 | 615.8 | 592.3 | 11.7 | 0.13 | Hot Gas w/ Temp Term; 1106.5 W/m | Fan: 57.9, Light: 99.8 (Total: 157.7) | `Supermarket_V22.1.idf` (`GlassDoorFrozenFood`), Tyler spec sheet SG02056 |
| **Medium-temp dairy/deli** (open vertical) | -1.1 / 30.0 | 1890.0 | 1817.3 | 12.0 | 0.30 | Off-Cycle; 0.0 W/m | Fan: 78.7, Light: 307.3 (Total: 386.0) | `Supermarket_V22.1.idf` (`MultiDeckDairyAndDeliCase`), Tyler spec sheet SG02053 |
| **Medium-temp meat** (open top/vertical) | -4.4 / 24.1 | 456.6 | 439.0 | 26.0 | 0.10 | Electric w/ Temp Term; 585.8 W/m | Fan: 47.2, Light: 86.8 (Total: 134.0) | `Supermarket_V22.1.idf` (`MeatDisplayCase`), Tyler spec sheet SG00524 |
| **Produce** (open multi-deck) | 3.3 / 38.0 | 1154.0 | 1109.6 | 15.0 | 0.30 | Off-Cycle; 0.0 W/m | Fan: ~50.0, Light: ~90.0 (Total: 140.0) | EnergyPlus example `RefrigerationCases.idf` / `FishDisplayCase` in `Supermarket_V22.1.idf` |

---

### Table 3 — Walk-in coolers & freezers

*Note: In the DOE/PNNL prototype models (STD2022/STD2013), walk-ins are modeled physically as `Refrigeration:Case` objects to simplify zone envelope heat balances. The parameters below reflect both the physical cabinet properties and their simplified EnergyPlus case equivalents.*

| Item | Cooler (medium-temp) | Freezer (low-temp) | Basis (per store / per restaurant) | Source |
|---|---|---|---|---|
| **Operating temp** (°C / °F) | 2.0 / 35.6 (Meat: -2.22 / 28.0) | -23.0 / -9.4 | Per-restaurant / per-hospital / per-hotel walk-in units | `ASHRAE901_RestaurantSitDown_STD2022_Buffalo.idf` (`Kitchen_Case:1_WALKINFREEZER` / `Kitchen_Case:2_SELFCONTAINEDDISPLAYCASE`) |
| **Floor area or volume basis** | 13.0 m² (140 ft²) | 10.0 m² (108 ft²) | Typical walk-in box dimensions (e.g. 10' x 14' x 9' for Supermarket Cooler) | `Supermarket_V22.1.idf` WalkIn Cooler comments |
| **U-value of walls/ceiling/floor** | 0.227 W/m²·K (0.040 Btu/h·ft²·°F) | 0.177 W/m²·K (0.031 Btu/h·ft²·°F) | R-25 (cooler) and R-32 (freezer) polyurethane foam insulation panels | PNNL Prototype Building Models / ASHRAE 90.1-2019 Table 6.8.1-11 |
| **Rated cooling capacity (W)** | 3,550 W (12,100 Btu/h) | 1,678 W (5,728 Btu/h) | Supermarket meat cooler vs. restaurant walk-in freezer capacity | `Supermarket_V22.1.idf` Walk-in Meat Cooler / Restaurant SitDown low-temp rack serving walk-in freezer |
| **Infiltration / door schedule** | Walk-in stocking schedule (10-25% open) | Walk-in stocking schedule (10-25% open) | `WalkInStockingSched` (compact schedule, 0.2 fraction overnight, 1.0 peak during store hours) | PNNL Prototype Building Models |

---

### Table 4 — Compressor rack / refrigeration system

| Parameter | Low-temp rack | Medium-temp rack | Source |
|---|---|---|---|
| **Rack / system COP (design)** | **1.50** (Supermarket) / **2.30 - 2.51** (Hospital/Restaurant) | **1.70** (Supermarket) / **6.93 - 7.29** (Hospital/Restaurant) | `Supermarket_V22.1.idf` (`LowTempRack` / `MediumTempRack`), `ASHRAE901_Hospital_STD2022_Buffalo.idf` (`RACK1` / `RACK2`) |
| **Suction / saturated evaporating temperature** (°C / °F) | -37.2 / -35.0 | -9.4 / 15.0 | `Supermarket_V22.1.idf` Low-temp suction (-35°F) vs. Medium-temp suction (15°F) |
| **Condenser type** | Air-Cooled | Air-Cooled | All DOE/PNNL Prototype Models (refrigeration heat rejection outdoors) |
| **Condenser fan power / heat rejection** | 1025 W (Supermarket) / 330 W (Restaurant) | 1025 W (Supermarket) / 330 W (Restaurant) | `Supermarket_V22.1.idf` Design Condenser Fan Power fields |
| **Number of racks per typical store** | 1 per store | 1 per store (plus 1 self-contained rack) | `Supermarket_V22.1.idf` rack list |
| **Heat-recovery / subcooling present?** | No | No | Not modeled in baseline prototypes to ensure model robustness and avoid simulation failures. |

---

### Table 5 — ZONE CASE CREDIT (the key coupling) + schedules

| Parameter | Value | Notes | Source |
|---|---|---|---|
| **Fraction of case cooling drawn from the zone (sensible)** | **70% to 92%** | Calculated as `1 - LHR` at rated conditions. Dairy/Produce = 70%, Meat = 90%, Frozen Reach-in = 87%, Ice Cream Well = 92% | EnergyPlus Engineering Reference §Refrigeration Case Zone Interactions |
| **Fraction drawn from the zone (latent)** | **8% to 30%** | Equal to the Latent Heat Ratio (`LHR`) at rated conditions. Dairy/Produce = 30%, Meat = 10%, Frozen Reach-in = 13%, Ice Cream Well = 8% | EnergyPlus Engineering Reference §Refrigeration Case Zone Interactions |
| **Net sales-floor cooling effect** (W/m² of sales floor) | **15.5 W/m²** (sensible + latent) | Based on average case cooling load (62.53 kW total remote capacity × 0.85 runtime fraction / 3,437 m² sales floor). Equivalent to **12.7 W/m²** of total floor area. | Derived from case capacities and floor areas in `Supermarket_V22.1.idf` |
| **Effect on space heating / cooling** (qualitative + magnitude) | Raises heating, lowers cooling | Sensible case heat extraction reduces zone air temperature, lowering active cooling loads by **20% to 40%** in summer, while increasing space heating loads by **30% to 50%** in winter. | NREL Supermarket Reference Building Model Documentation (Deru et al. 2011) |
| **Case operating schedule** (24/7 vs store hours) | 24/7 (compressors) | Compressors and fans run 24/7 to maintain food safety. Case lighting and night curtains cycle based on store occupancy schedules. | `Supermarket_V22.1.idf` schedules |
| **Anti-sweat heater / night-curtain assumptions** | Humidity-controlled; 80% case credit reduction | Anti-sweat heaters (70 W/m to 218.7 W/m) are active on low-temp cases. Night curtains are closed during closed hours (9 PM to 7 AM), dropping the case credit fraction from 1.0 to **0.2** (reducing zone heat exchange by 80%). | `CaseCreditReductionSched` and anti-sweat control types in `Supermarket_V22.1.idf` |

---

## 2. PART C — RECOMMENDATION

We recommend a **hybrid modeling approach** for OpenUBEM Phase-E:

1. **Physical modeling** (`Refrigeration:Case`/`:CompressorRack`) should be used **exclusively for the `SuperMarket` archetype**. Refrigeration represents 50% of a supermarket's total energy footprint. Because EnergyPlus display cases act as heat sinks on the sales floor, physical modeling is the only way to capture the **sales-floor cooling effect** (raising heating and lowering cooling). A lumped approach would miss this coupling entirely, leading to significant HVAC sizing and energy validation errors.
2. **Lumped electric intensity modeling** (Table 1) should be used as a fallback for all other archetypes (`FullServiceRestaurant`, `QuickServiceRestaurant`, `LargeHotel`, and `Hospital`). For these building types, refrigeration is a minor service load (1% to 15% of whole-building site energy) concentrated in kitchen walk-in coolers/freezers. Detailed physical modeling of cases, walk-ins, and compressor racks for kitchens adds hundreds of simulation objects and input parameters that are prone to simulation failure modes (e.g., airflow imbalances, defrost temperature spikes, loop convergence failures) with negligible thermal feedback on the main occupied zones.

---

## 3. CONFIDENCE AND CAVEATS

* **High Sourcing Confidence:** The display case parameters, COP, fan/lighting power, and defrost specifications are extracted directly from the baseline `Supermarket_V22.1.idf` and restaurant/hospital/hotel IDF models. These reflect the standard ASHRAE 90.1-2019 / STD2022 commercial building prototype baselines.
* **Case-Credit Magnitude Uncertainty:** While the rated LHR and sensible/latent split are mathematically firm, the actual in-situ heat extraction is highly sensitive to ambient humidity and dry-bulb temperatures. In dry climates (like Los Angeles) or highly air-conditioned spaces, display cases operate at off-rated conditions, which can alter the actual sensible/latent ratio by ±10–20%.
* **Scaling to Footprints:** To scale the single reference supermarket (4,181 m²) to the range of building footprints present in the 8,160-building OpenUBEM:
  * Scale the **total case length** (m) linearly with the building's floor area, using the baseline case-mix ratios: **0.021 m of case length per m² of total floor area**.
  * Keep case operating temperatures, LHRs, fan/light powers per unit length, and COP constants identical to the reference model.
  * Scale compressor rack capacities and condenser fan power proportionally to the total scaled case length to prevent undersizing/oversizing errors.

---

## 4. REFERENCES

1. Deru, M., Field, K., Studer, D., Benne, K., Griffith, B., Torcellini, P., Halverson, M., Winiarski, D., Liu, B., & Crawly, D. (2011). *U.S. Department of Energy Commercial Reference Building Models of the National Building Stock*. National Renewable Energy Laboratory. NREL/TP-5500-46861. [https://www.nrel.gov/docs/fy11osti/46861.pdf](https://www.nrel.gov/docs/fy11osti/46861.pdf)
2. Pacific Northwest National Laboratory (PNNL) & U.S. Department of Energy. *Commercial Prototype Building Models*. Standard 90.1-2019 / STD2022 release. [https://www.energycodes.gov/prototype-building-models](https://www.energycodes.gov/prototype-building-models)
3. EnergyPlus™ Version 22.1.0. *Input Output Reference* and *Engineering Reference*. U.S. Department of Energy. [https://energyplus.net/documentation](https://energyplus.net/documentation)
4. ASHRAE. (2018). *ASHRAE Handbook—Refrigeration*. Atlanta, GA: ASHRAE.
5. ENERGY STAR® Portfolio Manager®. (2024). *U.S. Energy Use Intensity (EUI) National Medians*. U.S. Environmental Protection Agency. [https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf](https://portfoliomanager.energystar.gov/pdf/reference/US%20National%20Median%20Table.pdf)
6. U.S. Energy Information Administration (EIA). (2018). *Commercial Buildings Energy Consumption Survey (CBECS) 2018*. [https://www.eia.gov/consumption/commercial/data/2018/](https://www.eia.gov/consumption/commercial/data/2018/)
