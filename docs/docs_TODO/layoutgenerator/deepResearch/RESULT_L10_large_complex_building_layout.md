# RESULT — LARGE & COMPLEX BUILDING LAYOUT (zoning specifications for hospitals, large hotels, deep-plan & high-rise archetypes)

This document provides the research findings, comparison tables, and synthesis specifications for zoning large and complex buildings (hospitals, large hotels, deep-plan offices, and high-rise structures) within OpenUBEM. It defines how to handle functional space-type distributions, deep floor plate concentric subdivision, and courtyard/atrium cases without fabricating interior layouts.

---

## REQUIRED OUTPUT TABLES

### Table 1 — As-modeled complex-prototype zoning

| Prototype | Departments / zone groups (as modeled by DOE) | Thermal zones per floor | Deep-plan handling (concentric zones?) | Source |
|---|---|---|---|---|
| **Hospital** | `PatientRoom` (North, South, East, West perimeter), `ICU` (intensive care), `OperatingRoom` (surgical), `Laboratory` (clinical), `Corridor` (circulation), `Physical_Therapy`, `Reception`, `MechRoom`, `Basement` | 15–17 zones (varies by floor) | Yes. High-internal-load clinical core (OR, ICU, labs) is concentrically surrounded by perimeter spaces (patient rooms, ER, offices). | DOE/PNNL Commercial Prototype Building Models (ASHRAE 90.1-2019/2022) |
| **Outpatient** | `ExamRoom` (North, South, East, West perimeter exam rooms & offices), `Core_ZN` (central waiting area, reception, corridor, and restrooms) | 5 zones | Yes. Standard perimeter (4.57 m / 15 ft) exam rooms surrounding a central administrative and waiting core. | DOE/PNNL Commercial Prototype Building Models (ASHRAE 90.1-2019/2022) |
| **LargeHotel** | **Ground:** `Lobby`, `Restaurant`, `Retail`, `Laundry`, `Lounge`, `MechRoom`<br>**Guest Floors (2–5):** `GuestRoomEast`, `GuestRoomWest` (representing 24 guest rooms via multipliers), central `Corridor`, `ElevMechRoom`<br>**Top Floor (6):** `GuestRoom`, `Banquet`, `Dining`, `Kitchen`, `Corridor`<br>**Basement:** `HotelBasement` | Ground: 7<br>Guest Floors: 7<br>Top Floor: 7<br>Basement: 1 | Yes. Central corridor acts as the core zone, flanked by East and West perimeter guest room zones. | DOE/PNNL Commercial Prototype Building Models (ASHRAE 90.1-2019/2022) |
| **LargeOffice (deep plate)** | `Perimeter_Bot_ZN_1–4` (cardinal office perimeter), `Core_Bot_ZN` (central open-office core), `DataCenter_Bot_ZN` (IT closet) | 6 zones (above-grade) + 1 (basement) | Yes. Single deep core zone with a 4.57 m (15 ft) outer perimeter ring; includes a dedicated internal zone for server rooms. | DOE/PNNL Commercial Prototype Building Models (ASHRAE 90.1-2019/2022) |
| **TallBuilding / high-rise** | No native prototype; proxied as LargeOffice: 4 cardinal perimeter zones (offices) + 1 central core (elevators, stairs, mechanical shafts) | 5 zones (proxy) | Yes. Standard core+perimeter (5 zones per floor) to prevent orientation-based solar load dilution. | OpenUBEM custom proxy based on LargeOffice (openubem/data/loads/openstudio_loads.json) |

### Table 2 — Deep-floorplate subdivision (beyond one perimeter ring)

| Plate depth condition | Recommended zoning | Number of concentric bands / interior zones | Source |
|---|---|---|---|
| **Depth $\le 2\times$ perimeter** (total width $\le 9.14\text{ m}$) | **Centerline split (perimeter-only, no core)**. Facades from opposite sides meet at the building's medial axis. | 1 band (perimeter-only) | NREL ComStock / Ladybug Honeybee geometry measures (Dragonfly `perimeter_core` default) |
| **Depth $2\text{–}4\times$ perimeter** (width $9.14\text{–}18.28\text{ m}$) | **Standard core + perimeter (App-G)**. One perimeter ring of $4.57\text{ m}$ (15 ft) depth and a single central core zone. | 2 bands (1 perimeter + 1 core) | ASHRAE 90.1-2019 Appendix G / NREL ComStock |
| **Very deep ($>4\times$ perimeter)** (width $>18.28\text{ m}$) | **Concentric multi-band zoning**. Outer perimeter band ($4.57\text{ m}$), intermediate core band ($4.57\text{ m}$, transition/circulation/open office), and deep central core (service core/shafts). | 3+ bands (outer perimeter + intermediate core + deep core) | NREL ComStock deep-plan defaults, LBNL CityBES, Sefaira zoning guidelines |
| **Atrium / lightwell present** | **Concentric inner & outer perimeter zoning**. Outer perimeter band ($4.57\text{ m}$ from exterior) + inner perimeter band ($4.57\text{ m}$ from courtyard/lightwell walls) + core zone in between. | 3 bands (outer perimeter, core, inner perimeter) | ENCODE Screening registry, NREL Commercial Reference Buildings (Deru et al. 2011), Dragonfly geometry workflows |

### Table 3 — Placing departments without location data

| Question | Defensible OpenUBEM approach | Source |
|---|---|---|
| **Can OSM tell us where a hospital's surgery vs. wards are? (No?) — so what's the fallback?** | **No.** OSM only provides the 2D footprint and general building tags. The fallback must be **Functional Proxy Zoning**: assign patient-room loads to the perimeter zones, and clinical/operating/laboratory loads to the core zone. This captures the solar/envelope vs internal gain dynamics without fabricating room locations. | Deru et al. (2011) NREL Hospital benchmark layout, UMI Shoeboxer methodology. |
| **Should complex buildings use area-weighted mixed space type per zone instead of located departments?** | **Yes.** For generic zones, OpenUBEM should use an **area-weighted space-type load blend** (e.g., blending LPD, EPD, and ventilation rates based on the prototype's total floor area fractions of each department). This ensures total building energy consumption and peak demands are physically conserved. | NREL ComStock / URBANopt, Cerezo et al. (2014) UMI templates. |
| **Does the DOE prototype itself place departments, or use representative floors?** | The DOE prototype uses **simplified representative floors** with localized space-type zones (e.g. Ground floor contains public and outpatient, mid-floors contain wards, top floor contains ICU/OR). It does not represent actual complex 3D routing of department blocks. | DOE Commercial Prototype Building Models (PNNL 2022). |
| **Is a "dominant program + core/perimeter" simplification defensible for UBEM?** | **Yes, highly defensible.** It is the industry standard for city-scale modeling. By dividing the building into a core (internal load-dominated, high ventilation) and perimeter (envelope-dominated, solar-responsive), BEM tools capture the major thermal drivers without requiring interior CAD drawings. | Hong et al. (CityBES, 2016), Fonseca et al. (CEA, 2016). |

### Table 4 — Fit to OpenUBEM

| Question | Answer + source |
|---|---|
| **Minimum zones/floor for a hospital to not bias EUI, without inventing department locations?** | **5 zones per floor (1 core + 4 cardinal perimeter zones)** or **6 zones** (adding a corridor). This is the minimum necessary to prevent EUI bias by separating perimeter solar gains from core internal loads. (NREL Commercial Reference Buildings, Deru et al. 2011). |
| **Should high-rise (TallBuilding, currently forced per-floor) get core/perimeter/deep-plan zoning?** | **Yes. TallOffice / TallBuilding currently forces per-floor single zones.** They should get **core+perimeter (or concentric deep-plan) zoning** because their floor plates are large and deep, and envelope exposure varies by orientation. Single-zone-per-floor dilutes solar gains and biases EUI. (ASHRAE 90.1 Appendix G, LBNL CityBES, Hong et al. 2016). |
| **Do large hotels reuse the L08 guest-room-wing method for room floors + a distinct podium treatment?** | **Yes.** A LargeHotel should be modeled with a **podium-tower split**: the ground floor (podium) uses core+perimeter zoning with high-load public spaces (lobby, café), while the upper floors (tower) reuse the `L08` guest-room-wing method. (PNNL LargeHotel Prototype, 2022). |
| **Where is single-zone-per-floor an acceptable fallback for these archetypes?** | Only in three cases: (1) building footprint area is **very small** ($< 500\text{ m}^2$), (2) the geometry is **extremely degenerate** (fails offsetting/centerline split), or (3) for **Warehouse** archetypes where a single open volume is physically correct. (OpenUBEM current zoning default, `zoning.py`). |

---

## Part C — Synthesis (the complex-building branch spec)

### 1. Minimal Defensible Zone Scheme per Complex Archetype

To model complex structures without inventing room locations, OpenUBEM's `layoutGenerator.py` will route complex archetypes to the following zoning schemes, which map the aggregate prototype loads into perimeter and core zones:

*   **Hospital (Inpatient):**
    *   *Zoning:* 5 zones per floor (1 core + 4 cardinal perimeter zones).
    *   *Perimeter Zones:* Assigned `PatientRoom` and `Office` load/schedule templates. These are envelope-dominated spaces with lower base ventilation.
    *   *Core Zone:* Assigned clinical loads (`OperatingRoom`, `ICU`, `Laboratory`, and `Corridor` support) with high equipment power densities (EPD) and high constant ventilation rates ($24/7$ schedules, high air changes per hour).
*   **Outpatient Healthcare:**
    *   *Zoning:* 5 zones per floor (1 core + 4 cardinal perimeter zones).
    *   *Perimeter Zones:* Assigned `ExamRoom` and `Office` loads.
    *   *Core Zone:* Assigned `Lobby`, `Corridor`, and `Waiting` loads.
*   **LargeHotel:**
    *   *Zoning:* Vertical split.
        *   **Ground Floor (Podium):** Core+perimeter zoning ($4.57\text{ m}$ perimeter depth) assigned public space loads (`Lobby`, `Restaurant`, `Retail`, `Lounge`).
        *   **Upper Floors (Tower):** Double-loaded corridor room-wing layout (from `L08`). A central corridor zone lies along the wing's medial axis, flanked by East/West perimeter guest room zones.
*   **TallBuilding / SuperTallBuilding:**
    *   *Zoning:* 5 zones per floor (1 core + 4 cardinal perimeter zones) assigned LargeOffice load parameters to prevent solar load dilution on tall glazed facades.

### 2. Deep-Plate Subdivision Rule

For very deep or high-rise building floor plates, OpenUBEM will apply a multi-band concentric zoning rule based on the building's footprint depth:

Let $D_{perim} = 4.57\text{ m}$ ($15\text{ ft}$, representing the standard ASHRAE 90.1 Appendix G perimeter depth).
Let $W$ be the minimum width (minor axis) of the footprint polygon.

1.  **Narrow Wing ($W \le 2 \times D_{perim}$ / $9.14\text{ m}$):**
    *   *Rule:* **Centerline Split**. Inward buffer collapses. Divide the footprint into perimeter-only zones meeting at the medial axis. No core zone is generated.
2.  **Standard Plate ($2 \times D_{perim} < W \le 4 \times D_{perim}$ / $9.14\text{–}18.28\text{ m}$):**
    *   *Rule:* **Standard Core+Perimeter**. Generate one outer perimeter ring of depth $D_{perim}$ and one central core zone.
3.  **Very Deep Plate ($W > 4 \times D_{perim}$ / $18.28\text{ m}$):**
    *   *Rule:* **Concentric Multi-Band Zoning**. Generate:
        *   **Outer Perimeter Band:** Depth $= 4.57\text{ m}$ from the facade.
        *   **Intermediate Core Band:** Depth $= 4.57\text{ m}$ concentric ring immediately inward of the perimeter. Models transition spaces, open offices, and corridors.
        *   **Deep Core:** Central remaining polygon. Models services, elevators, restrooms, and HVAC mechanical shafts.
4.  **Courtyard / Atrium present (Interior Ring):**
    *   *Rule:* **Inner & Outer Perimeter split**.
        *   Generate an outer perimeter band (depth $= 4.57\text{ m}$) from the exterior boundary.
        *   Generate an inner perimeter band (depth $= 4.57\text{ m}$) from the interior ring boundary (courtyard walls).
        *   The remaining space is the core. If the core width collapses below $2.0\text{ m}$, merge the core space into the adjacent perimeter zones to prevent sliver zone errors.

```mermaid
graph TD
    A[Footprint Polygon] --> B{Courtyard / Atrium?}
    B -- Yes --> C[Inner & Outer Perimeter Split]
    B -- No --> D{Minor Axis Width W}
    D -- "W <= 9.14m" --> E[Centerline Split (No Core)]
    D -- "9.14m < W <= 18.28m" --> F[Standard Core + Perimeter]
    D -- "W > 18.28m" --> G[Concentric Multi-Band Zoning]
```

### 3. Located Departments vs. Mixed/Dominant Space Type

> [!IMPORTANT]
> Because GIS/OSM data contains no interior department maps, attempting to locate specific departments (such as a hospital's surgery department in the south wing or the lobby in the north wing) is a **fabricated precision** that cannot be verified. 

OpenUBEM rejects located departments and adopts **Area-Weighted Mixed Space Types** or **Perimeter-vs-Core Functional Proxies**:
*   Total building loads (lighting, equipment, occupancy, ventilation) are calculated by multiplying the prototype's total floor area fractions by their respective intensities, ensuring physical conservation.
*   These loads are distributed systematically: envelope-sensitive loads (patient rooms, offices) are assigned to the perimeter zones; process-heavy and circulation-heavy loads (ORs, ICU, labs, corridors) are assigned to the core zones.

### 4. Fallback to Single-Zone-per-Floor

A single zone per floor (`one_zone_per_floor`) remains the only honest fallback under three conditions:
1.  **Low Area:** Footprint area $< 500\text{ m}^2$. Zoning adds negligible accuracy for small buildings but increases computational cost.
2.  **Geometry Failures:** Footprints with self-intersecting boundaries, extreme concave notches, or complex non-convex shapes where the straight skeleton or buffer offsetting yields degenerate polygons (e.g., self-touching boundaries).
3.  **Open Plan Typologies:** Warehouses, which are physically single open volumes.

---

## CONFIDENCE AND CAVEATS

*   **High Confidence:** The zoning logic for `Outpatient`, `LargeOffice`, and `LargeHotel` is well-evidenced. Outpatient models naturally map to a standard 5-zone layout. LargeHotel's guest floors are linear wings that fit the double-loaded corridor template. LargeOffice fits the core-perimeter division cleanly.
*   **Low Confidence (Caveat):** The `Hospital` archetype is the most difficult to simplify. A hospital contains a highly diverse mix of specialized spaces (MRI suites, kitchens, laundry, psychiatric wards) with distinct air change and temperature requirements. Simplifying this to a 5-zone perimeter/core layout with homogenized loads assumes well-mixed conditions that do not exist in reality. However, this simplification is thermodynamics-based (solar vs. internal gains) and is the only tractable approach for urban-scale modeling without detailed interior plans.

---

## REFERENCE LIST

1.  **U.S. Department of Energy (DOE) / Pacific Northwest National Laboratory (PNNL)**. (2022). *Commercial Prototype Building Models — ASHRAE 90.1-2022 Release*. Building Energy Codes Program. [https://www.energycodes.gov/prototype-building-models](https://www.energycodes.gov/prototype-building-models)
2.  **Deru, M., Field, K., Studer, D., Benne, K., Griffith, B., Torcellini, P., & Crawley, D.** (2011). *U.S. Department of Energy Commercial Reference Building Models of the National Building Stock*. NREL/TP-5500-46861. Golden, CO: National Renewable Energy Laboratory. [https://www.nrel.gov/docs/fy11osti/46861.pdf](https://www.nrel.gov/docs/fy11osti/46861.pdf)
3.  **Chen, Y., & Hong, T.** (2018). "Impacts of building geometry modeling methods on the simulation results of urban building energy models." *Applied Energy*, 211, 1263–1278. [DOI: 10.1016/j.apenergy.2017.12.008](https://doi.org/10.1016/j.apenergy.2017.12.008)
4.  **Dogan, T., & Reinhart, C.** (2017). "Shoeboxer: An algorithm for abstracted rapid multi-zone urban building energy model generation and simulation." *Energy and Buildings*, 140, 140–153. [DOI: 10.1016/j.enbuild.2017.01.017](https://doi.org/10.1016/j.enbuild.2017.01.017)
5.  **Cerezo, C., Dogan, T., & Reinhart, C.** (2014). "Towards standardizing building description templates for urban energy modeling." *Proceedings of the 2014 ASHRAE/IBPSA-USA Building Simulation Conference*, Atlanta, GA.
6.  **ASHRAE**. (2019). *Standard 90.1-2019 — Energy Standard for Buildings Except Low-Rise Residential Buildings*. American Society of Heating, Refrigerating and Air-Conditioning Engineers.
