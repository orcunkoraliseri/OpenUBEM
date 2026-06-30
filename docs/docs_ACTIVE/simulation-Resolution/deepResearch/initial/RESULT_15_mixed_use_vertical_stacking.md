# RESULT — MIXED-USE Vertical Stacking Enabled by Resolution (Per-Floor Archetypes)

This document establishes the methodology, parameters, and architectural conventions for modeling vertically mixed-use buildings in OpenUBEM. It details how the user-selectable resolution switch (`building`, `floor`, and `zone` modes) enables the transition from single-use approximations to floor-by-floor archetype assignments, resolving key physics and simulation coherence questions.

---

## 1. Required Output Tables

### Table 1 — Modelability of mixed use per resolution

| Mode | Can carry per-floor archetype? | How | Limitation | Source |
|---|---|---|---|---|
| `building` (1 zone) | **No** (Single use dominant) | The entire building volume is modeled as a single thermal zone (full height). The building takes the dominant archetype ID (e.g., `MidriseApartment` if residential area > 50%), and its associated loads, schedules, and HVAC system are applied globally. | Under-represents load diversity, mismatches peak demand timing, applies incorrect ventilation rates, and mischaracterizes HVAC system selection and end-use energy splits. | Cerezo Davila et al. (2016) [4]; CityBES LBNL documentation (Hong et al., 2016) [1] |
| `floor` (1 zone/floor) | **Yes** (Archetype per floor) | The building volume is divided into one zone per floor. Each floor is assigned its respective archetype ID (e.g., ground floor as `RetailStandalone` and upper floors as `MidriseApartment`), loading its specific equipment, lighting, occupant densities, schedules, and HVAC templates. | Treats each floor as a single, fully-mixed zone. Solar gains are averaged across the floor footprint, which under-predicts peak heating/cooling loads and misses daylighting control savings. | City Energy Analyst (CEA) (Fonseca et al., 2016) [2]; LBNL CityBES "OneZone" mode [1, 5] |
| `zone` (core/perimeter) | **Yes** (Archetype per floor, split into zones) | Each floor is sliced into core and perimeter zones. The archetype of each floor is applied to all zones (core and perimeter) belonging to that floor, ensuring floor-level load, schedule, and HVAC assignment. | High geometry and thermal coupling complexity. Significantly increases EnergyPlus simulation runtime (10x–50x compared to building-level) due to the large zone count. | OpenUBEM Zoning Schema [6]; Dogan & Reinhart (2013) "Shoeboxer" [8] |

### Table 2 — Common vertical mixed-use patterns

| Pattern | Typical floors | Per-floor archetypes | Source |
|---|---|---|---|
| **Retail base + residential tower** | Ground floor: retail <br>Floors 2+: apartments | Ground: `RetailStandalone` (or `RetailStripmall`) <br>Floors 2+: `MidriseApartment` or `HighriseApartment` | LBNL CityBES Mixed-Use Prototypes [5]; CEA Database Archetypes [2] |
| **Retail base + office tower** | Ground floor: retail <br>Floors 2+: offices | Ground: `RetailStandalone` <br>Floors 2+: `LargeOffice` (or `MediumOffice`) | LBNL CityBES Mixed-Use Prototypes [5] |
| **Parking podium + residential** | Ground/podium: parking <br>Floors 2+: apartments | Ground/podium: `Warehouse` (used as proxy with zero internal loads, no HVAC, and high exhaust infiltration) <br>Floors 2+: `HighriseApartment` | ASHRAE 90.1 Appendix G Section G3.1.1 [7]; CEA unconditioned podium convention [2] |
| **Ground commercial + hotel** | Ground floor: restaurant or retail <br>Floors 2+: guest rooms | Ground: `FullServiceRestaurant` or `RetailStandalone` <br>Floors 2+: `LargeHotel` or `SmallHotel` | Common urban morphology and taxonomy studies (e.g., Yeo et al., 2020) [9] |

### Table 3 — Cross-floor coherence questions

| Issue | Method | Source |
|---|---|---|
| **HVAC across mixed floors** (separate systems per use vs shared) | Assign separate HVAC templates (`HVACTemplate:Zone:*` or `ZoneHVAC:*`) to the zones of each floor based on that floor's archetype. Packaged or local terminal systems (e.g., split systems, PTACs, WLHPs, PSZs) operate independently, avoiding complex inter-zone plant loop dependencies in the IDF that trigger compilation errors. | ASHRAE 90.1-2019 Appendix G Section G3.1.1 (system type selection based on zone use and size) [7] |
| **DHW/service loads per use floor** | Model independent `WaterHeater:Mixed` and `WaterUse:Equipment` systems for each archetype-occupied floor, placed directly within the zone(s) of that floor. This represents sub-metered water heating systems and isolates the draw schedules. | DOE/PNNL Prototype Building Models (each prototype is self-contained with its own DHW loop) [10] |
| **Schedules differ by floor** (retail vs residential occupancy) | Link archetype-specific occupancy, lighting, equipment, infiltration, and thermostat schedules directly to the respective zone loads in EnergyPlus. Since the zones are separated by floor, EnergyPlus native scheduling handles this cleanly. | EnergyPlus Input-Output Reference [11] |
| **Shared envelope / thermal coupling between use floors** | Model the horizontal partitions (ceilings/floors) between stacked zones of different uses as interzone surfaces with a `Surface` boundary condition pointing to the adjacent zone. Do not use `Adiabatic` here, to correctly simulate thermal exchange due to differing setbacks and schedule profiles. | EnergyPlus Engineering Reference [12] |
| **Unconditioned floors** (parking podium) treatment | Model the podium as a separate unconditioned zone. Set its archetype to a proxy (e.g., `Warehouse` with zero internal loads, no HVAC, and high outdoor air ventilation). The partition above it is modeled as an interzone ceiling/floor with appropriate construction insulation. | ASHRAE 90.1-2019 Section 5 (Envelope requirements for floors separating conditioned space from unconditioned space) [7] |

### Table 4 — How peer tools handle it

| Tool / paper | Per-floor use modelling method | Source |
|---|---|---|
| **CityBES** | Supports assigning different prototype templates by story (e.g., ground-floor retail, upper-floor office/residential). It automates this by assigning archetype properties (loads, schedules, envelope, HVAC) to the respective zones of each story. It also supports floor multipliers for intermediate identical floors to save simulation time. | LBNL CityBES documentation (Hong et al., 2016 [1]; Chen, Hong, & Piette, 2017 [5]) |
| **City Energy Analyst (CEA)** | Allows defining a "uses-split" (percentages of different building functions like residential, office, retail, etc. for the building). The tool can either model the building as a single zone with consolidated weighted-average properties (schedules and loads) or distribute these uses vertically by assigning different occupancy typologies to specific zones/floors in the building database. | CEA Documentation & papers (Fonseca et al., 2016) [2] |
| **AutoBEM** | Maps building footprints to tax assessor and GIS data. When a building is identified as mixed-use, AutoBEM can split the floor area into separate thermal zones by floor or use type and assign corresponding prototype schedules and systems (e.g., ground-floor retail with residential above) to generate the final IDF. | ORNL AutoBEM documentation & papers (New et al., 2018 [3]; Allen et al., 2020 [13]) |
| **SimStadt** | Models mixed-use buildings by splitting the volume into different "usage zones" based on building type percentages, assigning different occupant loads, schedules, and temperature setpoints to each sub-volume. | SimStadt documentation (Nouvel et al., 2015) [14] |

---

## Part C — Synthesis & Scope Recommendation

### 1. Resolution as the Mixed-Use Enabler
Single-zone (`building`) resolution cannot model mixed-use vertical stacking because a single EnergyPlus thermal zone can only have one set of loads, schedules, and HVAC systems. Thus, vertical mixed-use modeling physically **requires** `floor` (one zone per floor) or `zone` (core/perimeter zoning) resolution.

To assign archetypes consistently across floors:
* **Input Definition:** Sourced data must define a vertical vector of archetypes, e.g., $A = [A_1, A_2, \dots, A_N]$ where $A_i$ represents the archetype ID assigned to floor $i$.
* **Geometric & Physical Mapping:** During IDF generation, the OpenUBEM builder loops through each floor $i$. For all zones generated on floor $i$ (a single zone in `floor` mode, or core and perimeter zones in `zone` mode), the builder applies the properties of archetype $A_i$.
* **Parameter Assignment:** Lighting Power Density (LPD), Equipment Power Density (EPD), occupancy density, ventilation rates, schedules, thermostats, and HVAC systems are assigned zone-by-zone according to the corresponding floor's archetype.

### 2. Cross-Floor Coherence Rules
To ensure physical realism and simulation stability in EnergyPlus:
* **HVAC Systems:** Model separate, independent HVAC systems for each use type. Do not attempt to link zones of different archetypes (e.g., retail and residential) to a single shared central plant loop in v1, as cross-archetype plant coupling introduces extreme complexity and compilation vulnerability in EnergyPlus templates. Instead:
  * Retail floors get Packaged Single Zone AC (PSZ-AC) or Packaged VAV (PVAV) systems.
  * Residential floors get split systems, Packaged Terminal Heat Pumps (PTHPs), or Water-Loop Heat Pumps (WLHPs).
* **Domestic Hot Water (DHW):** Model separate, self-contained DHW systems for each floor. A `WaterHeater:Mixed` tank and its corresponding `WaterUse:Equipment` and `WaterUse:Connections` objects are created for each archetype and assigned to the respective zone on that floor, using archetype-specific draw schedules.
* **Schedules:** Apply the archetype-specific schedule files directly to the respective zones. Since zones are separated by floor, schedules do not need to be averaged or blended.
* **Thermal Coupling:** Inter-zone floors/ceilings separating different use floors must be modeled as standard `Surface` boundary conditions (pointing to the adjacent floor zone). Using `Adiabatic` boundary conditions is prohibited here, as it fails to capture significant heat transfer caused by differing setpoints and schedule profiles (e.g., residential heating transferring heat to unoccupied retail setback zones at night).
* **Unconditioned Podiums:** Modeled as unconditioned zones using the `Warehouse` archetype as a proxy, but with internal gains, lighting, and HVAC templates disabled. Infiltration/ventilation is set to high rates (e.g., 1.5 ACH) to represent natural ventilation. The floor separating the podium and the first conditioned residential zone above is assigned an insulated construction assembly according to ASHRAE 90.1 Section 5.

### 3. Scope Verdict
It is **strongly recommended to defer per-floor mixed-use modeling to a documented follow-on (post-v1)**. 

* **Data Dependency:** Sourcing per-floor or percentage-use data for city-scale models is a major unresolved challenge. Standard open geospatial datasets (like OpenStreetMap, tax assessor data, or Microsoft building footprints) typically only provide a single dominant building use tag (e.g., "retail" or "residential") or a generic "mixed" tag. They rarely provide a per-floor or percentage-based use breakdown. Without a reliable source of per-floor archetype mapping, implementing the geometry/physics code for per-floor vertical stacking in v1 would create a feature that cannot be used or validated.
* **Refactoring Complexity:** OpenUBEM's IDF builder currently assumes a single `archetype_id` per building, which dictates construction sets, HVAC systems, and global variables. Refactoring the builder to handle multiple archetypes per building requires significant structural changes to the codebase.
* **Validation Hygiene:** To keep the resolution switch evaluation clean, all modes (`building`, `floor`, `zone`) should use the same dominant archetype in v1. Introducing mixed-use modeling in `floor`/`zone` modes while keeping `building` mode single-use would introduce a confounding variable. Any change in EUI would be due to both zoning resolution and archetype change, making it impossible to evaluate the physical impact of the resolution switch alone.

---

## 2. Confidence and Caveats

* **Evidence Strength:** The literature on mixed-use modeling in UBEM tools (CityBES, CEA, AutoBEM) is mature and confirms that floor-by-floor zoning is the primary vehicle for representing mixed-use physics.
* **GAPs identified:**
  * **Data Gap:** Standard GIS datasets do not contain floor-by-floor use divisions. Tools like CEA rely on custom survey databases, while CityBES and AutoBEM rely on tax assessor records which often require manual processing or crude assumptions (e.g., ground floor is always retail if the tag is "mixed").
  * **HVAC templates:** EnergyPlus templates (`HVACTemplate:*`) are convenient but struggle when multiple distinct HVAC templates try to reference the same central plant loops. Keeping systems packaged/independent is the only reliable way to automate this.

---

## 3. References

1. **Hong, T., Chen, Y., Lee, S. H., & Piette, M. A. (2016).** *CityBES: A Web-based Platform for City-Scale Building Energy Simulation.* Lawrence Berkeley National Laboratory (LBNL) Report. LBNL-1005821. [LBNL CityBES](https://doi.org/10.2172/1344406).
2. **Fonseca, J. A., Nguyen, T. A., Schlueter, A., & Pinel, P. (2016).** *City Energy Analyst (CEA): An open-source framework for energy system optimization in districts.* Applied Energy, 184, 1269-1278. [Applied Energy](https://doi.org/10.1016/j.apenergy.2016.03.070).
3. **New, J. R., Adams, M. B., Im, P., & Bhandari, M. S. (2018).** *Automatic building energy model (AutoBEM) generation.* Oak Ridge National Laboratory (ORNL). [ORNL AutoBEM](https://www.ornl.gov/project/autobem).
4. **Cerezo Davila, C., Reinhart, C. F., & Bemis, J. L. (2016).** *A systematic approach to creating city-scale building templates for urban energy models.* Building and Environment, 102, 137-148. [Building and Environment](https://doi.org/10.1016/j.buildenv.2016.03.002).
5. **Chen, Y., Hong, T., & Piette, M. A. (2017).** *Automatic generation of EnergyPlus models for city-scale building retrofit analysis.* Applied Energy, 207, 304-315. [Applied Energy](https://doi.org/10.1016/j.apenergy.2017.06.012).
6. **OpenUBEM Zoning Module.** `openubem/geometry/zoning.py`.
7. **ASHRAE. (2019).** *Standard 90.1-2019: Energy Standard for Buildings Except Low-Rise Residential Buildings.* American Society of Heating, Refrigerating and Air-Conditioning Engineers.
8. **Dogan, T. & Reinhart, C. F. (2013).** *Shoeboxer: An algorithm for clustering and representing energy models of complex building geometries.* Proceedings of BS2013: 13th Conference of International Building Performance Simulation Association, Chambéry, France. [IBPSA](http://www.ibpsa.org/proceedings/BS2013/p_1409.pdf).
9. **Yeo, Z. Y., Fonseca, J. A., & Schlueter, A. (2020).** *A review of urban building energy modeling (UBEM) tools and their application to mixed-use developments.* Energy and Buildings, 224, 110250. [Energy and Buildings](https://doi.org/10.1016/j.enbuild.2020.110250).
10. **U.S. Department of Energy. (2022).** *Commercial Prototype Building Models.* Pacific Northwest National Laboratory (PNNL). [PNNL Prototypes](https://www.energycodes.gov/development/commercial/prototype_models).
11. **EnergyPlus Input-Output Reference (v23.1).** U.S. Department of Energy. [EnergyPlus IO](https://energyplus.net/documentation).
12. **EnergyPlus Engineering Reference (v23.1).** U.S. Department of Energy. [EnergyPlus EngRef](https://energyplus.net/documentation).
13. **Allen, M., New, J. R., & Adams, M. B. (2020).** *Modeling America: Nationwide building energy simulation using AutoBEM.* ORNL Report.
14. **Nouvel, R., Bahu, J. M., Gruzinger, V., Coors, V., Schroter, B., & Strzalka, A. (2015).** *SimStadt - A new workflow-driven urban energy simulation platform.* Proceedings of BS2015: 14th Conference of International Building Performance Simulation Association, Hyderabad, India. [IBPSA](http://www.ibpsa.org/proceedings/BS2015/p2315.pdf).
