# RESULT 08 — Load / Schedule / HVAC Distribution & Conservation Across Resolution

This document establishes the rule set and mathematical formulations to ensure that when a building is partitioned from a single zone to multiple stacked floors or core/perimeter zones ($1 \rightarrow N \rightarrow \approx 5N$), the building-total internal loads, ventilation, and HVAC capacities are conserved. It specifies the EnergyPlus input objects and PNNL/DOE prototype foundations needed to maintain energy invariants and avoid double-counting or loss of loads during resolution transitions.

---

## REQUIRED OUTPUT TABLES

### Table 1 — Internal-load specification basis (conservation under splitting)

| Quantity | Recommended E+ basis | Conserved under zone-splitting? | Gotcha | Source |
|---|---|---|---|---|
| **Lighting** | `Watts/Area` (`Watts per Zone Floor Area` field in `Lights` object) | **Yes** (scales with zone floor area; $\sum A_{zone} = A_{building}$) | Zone-level daylighting controls in perimeter zones will reduce lighting energy selectively. While E+ inputs are conserved, simulated lighting energy will decrease in multi-zone models due to realistic daylight availability. | EnergyPlus Input-Output Reference (`Lights`), ASHRAE 90.1-2019 Section 9 |
| **Equipment** | `Watts/Area` (`Watts per Zone Floor Area` field in `ElectricEquipment` object) | **Yes** (scales with zone floor area; $\sum A_{zone} = A_{building}$) | Plug load densities must be applied uniformly to preserve total load. Localized process loads (e.g. servers, kitchens) must be handled separately using absolute inputs to prevent double-counting. | EnergyPlus Input-Output Reference (`ElectricEquipment`), PNNL Prototype Building Models |
| **Occupancy** | `People/Area` (`People per Floor Area` field in `People` object) | **Yes** (scales with zone floor area; $\sum A_{zone} = A_{building}$) | EnergyPlus allows fractional people per zone, which prevents rounding losses. Avoid absolute `Number of People` specifications as they will duplicate unless manually partitioned. | EnergyPlus Input-Output Reference (`People`), PNNL Prototype Building Models |
| **Any absolute/`Watts/Zone` loads** (elevators, IT, process loads) | `Watts` (`Design Level` field in `ElectricEquipment` or `OtherEquipment` object) | **Only if assigned to exactly one zone** (not replicated) | Central building loads (e.g. elevators, central server closets, transformers) specified in prototypes must be assigned to a single designated zone (e.g. first-floor core zone). Replicating these across all zones multiplies the load by $N$. | PNNL Prototype Building Models (STD2022 release), ASHRAE 90.1-2019 Appendix G |

### Table 2 — Ventilation / outdoor-air under multiple zones

| Item | Rule | Source (62.1 / E+) |
|---|---|---|
| **Per-zone OA basis** (`Flow/Person` + `Flow/Area`) | Specify outdoor air using the sum method: $V_{bz} = R_p \cdot P_z + R_a \cdot A_z$, where $R_p$ is flow/person and $R_a$ is flow/area. In EnergyPlus, use `DesignSpecification:OutdoorAir` with `Outdoor Air Method` = `Sum` referencing the rates. | ASHRAE Standard 62.1-2019 Section 6.2.2.1, EnergyPlus Input-Output Reference (`DesignSpecification:OutdoorAir`) |
| **Multiple-zone system OA** — sum vs `Vot` (ventilation efficiency) | In central multi-zone systems (e.g. VAV), the system outdoor air intake ($V_{ot}$) is calculated as $V_{ot} = V_{ou} / E_v$, where $V_{ou} = D \sum R_p P_z + \sum R_a A_z$ is the uncorrected outdoor air flow, $D$ is the occupancy diversity factor, and $E_v$ is the system ventilation efficiency (based on the critical zone outdoor air fraction $Z_{pz}$). For single-zone systems (e.g. PTAC, PSZ), $E_v = 1.0$ and $V_{ot} = \sum V_{bz}$. | ASHRAE Standard 62.1-2019 Section 6.2.4 (Multiple-Zone Systems), EnergyPlus Engineering Reference (Multi-zone ventilation sizing) |
| **Does splitting into core/perimeter change *system* OA?** | **Yes.** Core zones have high occupant densities but low heating/cooling loads (low primary supply airflow $V_{dz}$), yielding a high zone outdoor air fraction $Z_{pz} = V_{bz} / V_{dz}$. This reduces the central system ventilation efficiency $E_v$ ($E_v < 1.0$), forcing the central air handler to intake *more* total outdoor air ($V_{ot}$) to satisfy the critical core zone. | ASHRAE Standard 62.1-2019 Section 6.2.4 |
| **OpenUBEM recommendation** (zonal PTAC today — per-zone OA; confirm) | **Confirmed for zonal systems.** For zonal systems (PTAC, FCU, PSZ-AC), OA is delivered directly to each zone (efficiency $E_v = 1.0$, system OA is the sum of zone OA). For central multi-zone systems (PVAV, Built-up VAV), configure `Sizing:System` with `System Outdoor Air Method` = `VentilationRateProcedure` in E+ to dynamically compute $E_v$ and the correct $V_{ot}$. | EnergyPlus Engineering Reference (System Sizing), OpenUBEM `openubem/idf/hvac.py` |

### Table 3 — Schedules & occupancy diversity

| Item | Rule | Source |
|---|---|---|
| **Same archetype schedule applied to all zones of a building?** | **Yes.** The exact same normalized archetype-level fractional schedules (occupancy, lighting, equipment) must be applied to all zones. This ensures that the building-total coincident peak and daily/annual energy profiles are conserved. | PNNL Commercial Prototype Building Models (which apply uniform schedules to core/perimeter zones on all floors), ASHRAE 90.1-2019 Appendix G |
| **Occupancy diversity factor** (does splitting change effective diversity)? | **No.** If all zones share the same normalized schedule, the coincident peak building-level occupancy remains identical to a single-zone model. The PNNL prototype schedules already incorporate a whole-building occupancy diversity factor into their hourly fractions. | PNNL Prototype Model schedules, ASHRAE 90.1-2019 Appendix G |
| **Should core and perimeter share one schedule or differ?** | **They must share one schedule.** Introducing separate schedules for core vs. perimeter zones without empirical spatial data violates the zero-fitted-parameters philosophy of OpenUBEM and introduces artificial energy shifts. | PNNL Prototype Building Models, OpenUBEM Zero-Fitted-Parameters Philosophy |

### Table 4 — HVAC capacity & autosizing under resolution

| Item | Rule | Source |
|---|---|---|
| **Per-zone autosizing** (`Sizing:Zone`) — capacity = sum of zones ≈ building total? | **No.** The sum of per-zone autosized terminal capacities ($\sum Q_{zone}$) is typically 15% to 30% higher than the whole-building coincident peak capacity. Zones peak at different hours (non-coincident peaks), while the building-level single zone sizes for the coincident peak. | ASHRAE Handbook of Fundamentals Chapter 18, EnergyPlus Engineering Reference (`Sizing:Zone`) |
| **Does core/perimeter splitting change total installed capacity vs single zone?** | **Yes.** Core/perimeter zoning forces each terminal unit and zone coil to be sized for its local peak. East zones peak in the morning, west in the afternoon. In a single-zone model, these facade loads average out, resulting in a significantly lower coincident peak and smaller equipment size. | ASHRAE Handbook of Fundamentals, EnergyPlus Engineering Reference (`Sizing:Zone` vs `Sizing:System`) |
| **Fan/pump power conservation** when zone/terminal count changes | **Total fan power increases in multi-zone models.** Zonal systems sum individual fan flows. For VAV systems, VAV terminal boxes and reheat coils add pressure drop, and VAV systems use higher static pressure (e.g. 1389 Pa vs 622 Pa for single-zone). To conserve fan power parameters, static pressure and fan/motor efficiencies must be held constant at the archetype system level, allowing E+ to autosize the volumetric flow rates. | ASHRAE 90.1-2019 Appendix G, OpenUBEM `openubem/idf/hvac.py` |
| **Part-load / diversity effect** of more zones on plant sizing | Central plants (chillers/boilers) serve the central loop and are sized for the coincident block load of all zones. Therefore, central plant capacity remains close to the single-zone model. However, multi-zone terminal systems run more reheat and part-load cycles, which increases annual heating and cooling energy. | ASHRAE 90.1-2019 Section 6.4.2.1, EnergyPlus Engineering Reference (`Sizing:Plant`) |

### Table 5 — Conservation test matrix (the invariant)

| Quantity | building (1 zone) | floor (N) | zone (~5N) | Must be equal? |
|---|---|---|---|---|
| **Total lighting energy** | $LPD \cdot A_{bld} \cdot \sum S_{lt}(t) \cdot 1\text{ hr}$ | $\sum_{f=1}^N LPD \cdot A_f \cdot \sum S_{lt}(t) \cdot 1\text{ hr}$ | $\sum_{z=1}^{5N} LPD \cdot A_z \cdot \sum S_{lt}(t) \cdot 1\text{ hr}$ | **Yes** |
| **Total equipment energy** | $EPD \cdot A_{bld} \cdot \sum S_{eq}(t) \cdot 1\text{ hr} + P_{abs} \cdot \sum S_{abs}(t) \cdot 1\text{ hr}$ | $\sum_{f=1}^N EPD \cdot A_f \cdot \sum S_{eq}(t) \cdot 1\text{ hr} + P_{abs} \cdot \sum S_{abs}(t) \cdot 1\text{ hr}$ (placed on one floor) | $\sum_{z=1}^{5N} EPD \cdot A_z \cdot \sum S_{eq}(t) \cdot 1\text{ hr} + P_{abs} \cdot \sum S_{abs}(t) \cdot 1\text{ hr}$ (placed in one zone) | **Yes** (provided absolute loads $P_{abs}$ are not replicated) |
| **Total occupancy** | $PeopleDensity \cdot A_{bld} \cdot \sum S_{occ}(t)$ | $\sum_{f=1}^N PeopleDensity \cdot A_f \cdot \sum S_{occ}(t)$ | $\sum_{z=1}^{5N} PeopleDensity \cdot A_z \cdot \sum S_{occ}(t)$ | **Yes** |
| **Total design OA** | $R_p \cdot P + R_a \cdot A_{bld}$ | $\sum_{f=1}^N (R_p \cdot P_f + R_a \cdot A_f)$ | System $V_{ot} = V_{ou} / Ev$ where $V_{ou} = D \sum R_p P_z + \sum R_a A_z$ | **No** (higher for multi-zone VAV due to $E_v < 1.0$) |
| **EUI denominator** (footprint × N) | $Footprint \cdot NumFloors$ | $Footprint \cdot NumFloors$ | $Footprint \cdot NumFloors$ | **Yes** (identical) |

---

## PART C — SYNTHESIS (RULE BLOCK)

### The Conservation Rule Set

To prevent artificial shifts in energy use intensity (EUI) when switching between `building`, `floor`, and `zone` resolution modes, OpenUBEM must strictly adhere to the following rules:

1. **Area-Normalized Load Basis**:
   * For **occupancy**, **lighting**, and **plug loads**, the IDF builder must assign density-based inputs (`People per Floor Area`, `Watts per Zone Floor Area`) rather than absolute levels. Because the sum of the floor areas of the split zones mathematically equals the original footprint area ($\sum A_{zone} = A_{building}$), EnergyPlus will scale and conserve these totals automatically.
   
2. **Absolute Process Loads (Per-Building Allocation)**:
   * Any process load that is specified on a whole-building absolute basis (W) must **never** be multiplied across zones or floors. It must be assigned to exactly **one designated zone** (e.g., the core zone on the first floor, or the basement floor).
   * **List of Per-Building Loads that must NOT be replicated**:
     * **Elevator Motor and Cab Loads**: Model as a single `ElectricEquipment` or `OtherEquipment` object with the absolute power (W) assigned to the first-floor core zone.
     * **Central IT Server Rooms**: Large, localized server racks (such as those in `LargeOffice` or `Hospital` server spaces) must be represented as a single `ElectricEquipment` object in one central core zone.
     * **Domestic Hot Water (DHW) Standby Losses and Circulating Pumps**: Assign the central water heating loop, standby losses, and pump power to a single mechanical room zone (or first-floor core zone).
     * **Transformers and Electric Vault Losses**: Place utility transformer losses in a single mechanical/electrical room zone.
     * **Exterior Lighting**: Model using `Exterior:Lights` which does not belong to a thermal zone and thus avoids duplication when zone counts change.

3. **Ventilation Rates and Efficiency**:
   * **Zonal Systems (PTAC, FCU, PSZ)**: Assign `DesignSpecification:OutdoorAir` to each zone. Since there is no central mixing loop, the system ventilation efficiency $E_v = 1.0$. The total outdoor air flow is the sum of the zone requirements: $V_{ot} = \sum (R_p P_z + R_a A_z)$.
   * **Central Multi-Zone Systems (VAV, PVAV)**: The system-level outdoor air intake must account for system ventilation efficiency $E_v$ in accordance with the ASHRAE 62.1 Multiple-Zone System Design Procedure. Configure `Sizing:System` with `System Outdoor Air Method` = `VentilationRateProcedure` in the EnergyPlus templates. EnergyPlus will automatically calculate $E_v$ based on the critical zone and size the central system OA intake accordingly.

4. **HVAC Fan and Pump Power**:
   * To prevent fan power from scaling artificially with terminal count, keep the supply fan static pressure drop (e.g., 622.5 Pa for PSZ, 1389.42 Pa for VAV) and fan/motor efficiencies constant at the system family level in `openubem/idf/hvac.py`. Allow EnergyPlus to autosize the supply air flow rates (`Supply Air Maximum Flow Rate` = `autosize`).

---

## EXPECTED RESIDUAL DIFFERENCE BETWEEN MODES

Even with perfect load conservation at the input level, the simulated EUI for the same building will differ between resolution modes. This is a physical consequence of zoning resolution, not a bookkeeping bug. The manager should audit results using these guidelines:

1. **Reheat Energy Penalty (Multi-Zone Only)**:
   * **Divergence**: `zone` mode EUI > `floor` mode EUI > `building` mode EUI.
   * **Mechanism**: Core/perimeter zoning splits spaces with different thermal profiles. When perimeter zones require heating and core zones require cooling, central VAV systems trigger simultaneous heating and cooling (reheat). A single-zone model averages these loads out, leading to zero reheat energy.
   
2. **System Ventilation Load (Multi-Zone Only)**:
   * **Divergence**: Central system outdoor air flow is higher in `zone` mode.
   * **Mechanism**: Under ASHRAE 62.1, the system ventilation efficiency ($E_v$) is determined by the critical zone. Core zones have high occupant densities but low heating/cooling airflow, leading to low $E_v$ (often 0.6 to 0.8). A single-zone model assumes $E_v = 1.0$. The extra outdoor air in `zone` mode increases the conditioning load on central coils.

3. **Part-Load Efficiency and Autosizing**:
   * **Divergence**: Peak cooling/heating capacities are larger in `zone` mode, leading to different part-load efficiency curves.
   * **Mechanism**: Individual zones are sized for local, non-coincident peaks (e.g., west facades peaking in the afternoon). The sum of zone capacities is greater than the coincident building peak. Larger terminal capacities and frequent part-load operation generally increase annual energy consumption.

4. **Daylighting Control Savings**:
   * **Divergence**: Lighting energy is lower in `zone` mode if daylighting controls are modeled.
   * **Mechanism**: Daylighting sensors only dim lights near windows (perimeter zones). A single-zone model cannot represent this local effect unless it artificially dims the whole space or ignores daylighting entirely.

---

## CITE E+ OBJECTS AND REGULATORY STANDARDS

* **EnergyPlus Input-Output Reference (v23.1)**:
  * `People`: Utilizes `People/Area` (or `Zone Floor Area per Person`) to normalize occupant loads.
  * `Lights`: Utilizes `Watts/Area` to normalize lighting power densities.
  * `ElectricEquipment`: Utilizes `Watts/Area` for general plug loads and absolute `Watts` for point process loads.
  * `DesignSpecification:OutdoorAir`: Utilizes `Sum` method for combining person-based ($R_p$) and area-based ($R_a$) ventilation.
  * `Sizing:System`: Uses `System Outdoor Air Method` = `VentilationRateProcedure` to execute ASHRAE 62.1 multi-zone ventilation sizing calculations.
* **ASHRAE Standard 62.1-2019 (Ventilation for Acceptable Indoor Air Quality)**:
  * Section 6.2.2.1: Zone Outdoor Airflow equations ($V_{bz}$).
  * Section 6.2.4: Multiple-Zone Systems equations for uncorrected airflow ($V_{ou}$), occupancy diversity ($D$), and system ventilation efficiency ($E_v$).
* **ASHRAE Standard 90.1-2019 (Energy Standard for Buildings)**:
  * Section 6.4.2.1: Calculations for HVAC sizing and coincident peak considerations.
  * Appendix G: Guidelines for modeling baseline systems, including sizing factors (1.15 for cooling, 1.25 for heating) and fan power limits.
* **DOE/PNNL Commercial Prototype Building Models (STD2022 Release)**:
  * Defines the archetype-specific load densities, baseline schedules, and system configurations used as the core parameters for OpenUBEM.

---

## CONFIDENCE AND CAVEATS

* **The Double-Counting Pitfall**:
  * The most significant risk when implementing the `zone` mode is the double-counting of absolute building-level process loads (elevators, IT rooms, or domestic hot water standby losses). If the geometry script splits a floor into core and perimeter zones, and the load dispatcher loop applies the whole-building absolute load to *every* zone, the energy consumption will scale by the number of zones ($N$). This will result in an artificially inflated EUI. 
  * **Mitigation**: The IDF builder must explicitly filter zone names and assign absolute loads only to the first-floor core zone (e.g. zone name containing `_Core` and `_F1`).
* **Ventilation Sizing Failure**:
  * In VAV systems, if the `Sizing:System` outdoor air method is left as `Sum` rather than `VentilationRateProcedure`, the central fan will be undersized for outdoor air delivery, violating ASHRAE 62.1 compliance and underestimating the heating and cooling coil loads.
* **Coincident vs Non-Coincident Sizing**:
  * While EnergyPlus autosizes capacities, the central plant sizing relies on block loads. If the design days or sizing parameters are incorrectly configured, E+ might size the central chiller based on the sum of zone peaks rather than the coincident peak, causing massive over-sizing of central loops.

---

## REFERENCE LIST

1. **U.S. Department of Energy (DOE) / Pacific Northwest National Laboratory (PNNL)**:
   * *Commercial Prototype Building Models (STD2022 release)*. PNNL EnergyPlus prototype IDFs. 
   * [PNNL Prototype Models Portal](https://www.energycodes.gov/prototype-building-models)
2. **ASHRAE Standard 62.1-2019**:
   * *Ventilation for Acceptable Indoor Air Quality*. Atlanta, GA. Section 6: Procedures for Design Outdoor Air Quality (Ventilation Rate Procedure and Multiple-Zone Systems equations).
3. **ASHRAE Standard 90.1-2019**:
   * *Energy Standard for Buildings Except Low-Rise Residential Buildings*. Atlanta, GA. Appendix G: Performance Rating Method (system sizing, fan power configurations, and baseline schedules).
4. **EnergyPlus Input-Output Reference (v23.1)**:
   * *Section: Space/Zone Design Loads and Sizing*. `People`, `Lights`, `ElectricEquipment`, `DesignSpecification:OutdoorAir`, and `Sizing:System` object documentation.
   * [EnergyPlus I/O Documentation](https://energyplus.net/documentation)
5. **EnergyPlus Engineering Reference (v23.1)**:
   * *Section: Climatic Data and Sizing Calculations*. Detailed mathematical formulations for multiple-zone system outdoor air calculations and plant loop sizing.
6. **ASHRAE Handbook — Fundamentals (2021)**:
   * *Chapter 18: Nonresidential Cooling and Heating Load Calculations*. Sizing principles, diversity factor definitions, and coincident vs. non-coincident peak calculations.
