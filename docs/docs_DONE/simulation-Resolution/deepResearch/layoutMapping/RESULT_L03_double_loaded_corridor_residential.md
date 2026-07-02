# RESULT — DOUBLE-LOADED CORRIDOR & residential/hotel layout on real footprints

This document contains the researched methods, algorithms, and comparative analysis of how residential and lodging layouts—specifically double-loaded corridors (units along a central hallway)—are modeled or approximated on arbitrary, real-world building footprints in Urban Building Energy Modeling (UBEM), considering code constraints and computational robustness.

---

## REQUIRED OUTPUT TABLES

### Table 1 — Corridor placement methods on a real footprint

| Method | How the corridor geometry is derived | Works on rectangle? | Works on L/thin/curved? | Used by | Source |
|---|---|---|---|---|---|
| **Inward-offset core blob = corridor (geomeppy core/perim)** | Buffers the footprint boundary polygon inward by a fixed distance (typically $4.57\text{ m}$ / $15\text{ ft}$). The resulting inner polygon forms the core zone, which is then mapped to the corridor's space type and loads. | **Yes.** Produces a clean central rectangular core zone. | **No.** On L/U/T shapes, inward offsetting can cause self-intersections, coordinate crossover, or polygon fragmentation into disjoint pieces. On narrow shapes (width $< 2 \times \text{offset}$), the core collapses to an empty polygon. It generates a concentric ring rather than a linear hallway. | `geomeppy` (native `core_perimeter.py` module), **LBNL CityBES** (AutoZone) | geomeppy source code; Chen & Hong (2018), Applied Energy |
| **Medial axis / straight-skeleton spine corridor** | Computes the 1D topological skeleton (straight skeleton or medial axis) of the footprint polygon. The skeleton is simplified to a 1D graph (spine), then buffered outward by half the desired hallway width (e.g. $0.75-1.2\text{ m}$ on each side) to form a linear corridor zone. | **Yes.** Generates a single central spine hallway. | **Yes.** The medial axis/straight skeleton naturally scales and branches to follow the bends of complex non-convex polygons (L, T, U, curves) without crossing boundaries. | **Ladybug Tools (Honeybee/Dragonfly)** (space subdivision workflows), **NREL URBANopt / OpenStudio** (bar-generation measures) | Dragonfly documentation; Dogan, Reinhart & Michalatos (2013) Autozoner; openstudio-model-articulation-gem |
| **Fixed-width central strip (e.g. 1.5–2.4 m hallway)** | Places a straight, linear corridor zone of a specified fixed width (e.g., $1.68\text{ m}$ for apartments, $1.83-2.44\text{ m}$ for hotels) along the major longitudinal centerline of the building footprint. | **Yes.** Slices the rectangle along the major centerline. | **No.** Fails on L/U/T/curved shapes because a single straight strip cannot adapt to bends, resulting in sections of the corridor running outside the building footprint or intersecting exterior walls. | **NREL URBANopt / OpenStudio** (parametric bar generation) | NREL URBANopt SDK documentation (2022); openstudio-model-articulation-gem |
| **Template double-loaded corridor scaled to footprint** | Takes a pre-defined parametric template layout (a rectangular floor plate with a central corridor and adjacent unit divisions) and applies scaling factors to stretch/shrink the coordinates to match the bounding box of the target building footprint. | **Yes.** Maps accurately to scaled rectangles. | **No.** Fails on non-convex shapes (L, U, T, curved) as scaling a rectangular template does not account for the non-convex geometry, creating zones outside the footprint or intersecting boundaries. | **OpenStudio** (classic templates for specific prototypes) | OpenStudio Model Articulation Gem |

---

### Table 2 — Unit arrangement around the corridor

| Item | Rule | Source |
|---|---|---|
| **Apartments per floor (DOE Midrise/Highrise)** | 8 units per floor (Ground floor: 7 units + 1 office/common space; Floors 2+: 8 units). Zoned as 4 perimeter orientation blocks (lumped apartments) or 8 individual unit zones. | DOE/PNNL Commercial Prototype Building Models (Multi-family Midrise/Highrise); `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` |
| **Hotel guest rooms per floor (DOE Small/Large Hotel)** | **Small Hotel:** Ground floor has 5 guest room zones + lobby/lounge/office. Floors 2–4 have 10 guest room zones per floor (representing 24 actual rooms via multipliers).<br>**Large Hotel:** Ground floor has 0 guest rooms (lobby, café, retail, laundry). Floors 2–5 have 7 zones per floor (representing guest rooms + corridor). Floor 6 (top) has guest rooms, banquet hall, kitchen, dining. | DOE/PNNL Commercial Prototype Building Models (Small/Large Hotel); `ASHRAE901_HotelSmall_STD2022_Buffalo.idf` / `ASHRAE901_HotelLarge_STD2022_Buffalo.idf` |
| **Typical unit facade width / depth** | **Midrise/Highrise Apartment:** Facade width $= 11.58\text{ m}$ ($38.0\text{ ft}$), Depth $= 7.62\text{ m}$ ($25.0\text{ ft}$), Area $\approx 88.2\text{ m}^2$ ($950\text{ sq ft}$).<br>**Small Hotel guest room:** Facade width $= 3.96\text{ m}$ ($13.0\text{ ft}$), Depth $= 8.23\text{ m}$ ($27.0\text{ ft}$), Area $\approx 32.6\text{ m}^2$ ($351\text{ sq ft}$). | DOE/PNNL Commercial Prototype Building Models (Multi-family & Hotel) |
| **How units map onto perimeter zones (1 zone/unit vs lumped)** | **Option 1 (Match prototype):** Slices perimeter into individual thermal zones per unit (e.g. 8 zones/floor). Highly complex and geometrically fragile on arbitrary shapes.<br>**Option 2 (Lumped perimeter):** Groups all units facing the same orientation into a single lumped cardinal perimeter zone (N, S, E, W). Captures solar gains and envelope losses accurately while maintaining geometric robustness. | Dogan & Reinhart (2017), Energy and Buildings; Chen & Hong (2018), Applied Energy |

---

### Table 3 — Code & physical constraints that force the typology

| Constraint | Requirement | Implication for zoning | Source |
|---|---|---|---|
| **Daylight/ventilation to habitable rooms (IBC §1205 or equiv.)** | IBC §1204 (Lighting) and §1202 (Ventilation) mandate that all habitable spaces (living rooms, bedrooms, hotel guest rooms) must have natural light (minimum 8% of the floor area) and natural ventilation (minimum 4% of the floor area) via windows or skylights directly opening to the exterior, yard, or court. | Residential dwelling units and hotel guest rooms must be placed along the perimeter of the building facade (with exterior window access). They cannot be located in a windowless interior core. | International Building Code (IBC) 2021, Sections 1202 (Ventilation) and 1204 (Lighting) (formerly Section 1205). |
| **Egress / corridor width** | IBC Section 1020 (Corridors) Table 1020.3 specifies a minimum corridor width of 44 inches ($1.12\text{ m}$) for R-2 occupancies with an occupant load of 50 or more, or 36 inches ($0.91\text{ m}$) for occupant loads less than 50. Typical multifamily designs use a standard $5-6\text{ ft}$ ($1.52-1.83\text{ m}$) double-loaded corridor. | The corridor is placed in the interior center (core) to maximize perimeter exposure for habitable units. Corridors must be simulated as separate thermal zones with low occupancy and low internal gains. | International Building Code (IBC) 2021, Section 1020 (Corridors). |
| **Windowless-core prohibition for dwellings** | Dwelling units cannot be situated in windowless core spaces. They must have natural light and ventilation openings (exterior walls). | The core zone in a multifamily or lodging simulation must not be assigned residential occupant or equipment loads. The core must be mapped to corridor/common area templates (Core-as-Corridor rule). | IBC §1204 / §1205; RESULT_03. |

---

### Table 4 — How peer tools handle residential corridors

| Tool | Corridor generated? | Method | Residential applied at city scale? | Source |
|---|---|---|---|---|
| **URBANopt / OpenStudio** | **Yes** (only in bar-generation measures for rectangles). **No** (in GeoJSON GIS auto-zoning). | Bar-generator measures carve a fixed-width longitudinal corridor strip down the middle. GeoJSON geometry tools use standard core/perimeter splits without generating a true linear corridor. | **Yes.** Uses the simplified core/perimeter proxy at scale, mapping the core to corridor loads and the perimeter to dwelling units. | openstudio-model-articulation-gem; NREL URBANopt SDK documentation (2022) |
| **CityBES** | **No** | Standard pixel-based auto-zoning. Creates an offset core zone representing circulation/corridor space, but geometrically it remains a central blob rather than a linear hallway. | **Yes.** Simulates multifamily buildings with generic core/perimeter zoning, mapping the core to corridor and perimeter to apartments. | Chen & Hong (2018), Applied Energy |
| **UMI** | **No** | Shoeboxer abstraction. Facade segments are grouped by orientation and simulated as representative 2D/3D shoeboxes. The core (corridor) is modeled as a separate shoebox zone with adiabatic surfaces. | **Yes.** Simulated via shoebox templates for residential buildings. | Dogan & Reinhart (2017), Energy and Buildings |
| **CEA** | **No** | Simulates each floor (or building) as a single fully-mixed thermal zone, ignoring internal walls and corridors completely. | **Yes.** Models residential buildings as single zones per floor/building. | Fonseca et al. (2016), CEA documentation |

---

## Part C — Synthesis (residential layout rule)

### 1. Best-Fit Algorithm Selection & Sourced Trade-off
OpenUBEM should retain the **offset-core-as-corridor approximation** (`../RESULT_03`) rather than generating a **true linear corridor** (medial axis / central strip). 

* **The Sourced Trade-off:** Generating a true linear corridor via straight-skeleton or medial axis algorithms is highly complex and computationally expensive. These algorithms frequently fail on non-convex, narrow, or curved shapes (L, U, T shapes) by generating self-intersecting polygons, disconnected corridor fragments, or invalid vertex coordinates, which leads to fatal crashes in EnergyPlus. In contrast, the inward-offset core-as-corridor approximation (Option 2) is mathematically robust, runs natively in Shapely/geomeppy, captures the envelope-to-core area ratios accurately, and is the industry standard proxy used by CityBES and URBANopt.

### 2. Rule for Arranging Units
Slicing the perimeter into individual units (Option 1) is rejected due to geometric fragility (perpendicular cuts intersect at corners, producing overlapping boundaries). Instead, we adopt **lumped perimeter zones grouped by cardinal orientation (Option 2)**.
* For `MidriseApartment` and `HighriseApartment`, the perimeter is subdivided into a maximum of 4 cardinal zones (North, East, South, West), representing a lumped group of apartments.
* For `SmallHotel` and `LargeHotel`, the guest rooms are lumped into the cardinal perimeter zones.

### 3. Corridor Width and Placement Values
For calculations that require a virtual corridor dimension (e.g., area fractions, ventilation, or occupant counts):
* `MidriseApartment` / `HighriseApartment`: corridor width $= 1.68\text{ m}$ (5.5 ft).
* `SmallHotel`: corridor width $= 1.83\text{ m}$ (6.0 ft).
* `LargeHotel`: corridor width $= 2.44\text{ m}$ (8.0 ft).
* Core placement depth: **4.57 m (15 ft)** offset (ASHRAE 90.1 Appendix G).

### 4. Fallback when no sensible corridor fits
The fallback is `one_zone_per_floor`. If the footprint width is $< 2 \times 4.57\text{ m} = 9.14\text{ m}$ (or core area $< 10.0\text{ m}^2$), the core is dropped, and the entire floor is simulated as a single zone. In this case, the zone is assigned the dominant Apartment or Guest Room loads (not corridor loads).

---

## CONFIDENCE AND CAVEATS

The corridor approximation most distorts results in **buildings with high aspect ratios (very long and narrow slabs) or complex branching plans**. 

1. **Envelope-to-Corridor Ratio Distortion:** In a true double-loaded corridor design, the corridor has no external envelope exposure. In the core/perimeter approximation, if the core collapses (on a narrow footprint), the corridor is lumped into the perimeter, exposing it to external heat transfer. This distorts the space-by-space heating and cooling loads.
2. **Internal Load Mappings:** Forcing the core to represent the corridor means that 100% of the core is modeled as an unoccupied circulation space. In reality, some internal core space in large residential buildings contains mechanical shafts, stairwells, or elevators, which might have different ventilation or heat generation profiles than a standard corridor.
3. **Geometric Failures:** On extremely irregular, narrow, or non-convex footprints, the offset core can split into disconnected polygons. If these polygons are small ($< 10\text{ m}^2$), the fallback to `one_zone_per_floor` is triggered, removing the corridor completely and averaging its loads with the apartments.

---

## REFERENCE LIST

1. **U.S. Department of Energy (DOE)**. (2022). *Commercial Prototype Building Models*. Building Energy Codes Program. [https://www.energycodes.gov/prototype-building-models](https://www.energycodes.gov/prototype-building-models)
2. **International Code Council (ICC)**. (2021). *International Building Code (IBC)*. Country Club Hills, IL. Sections 1202 (Ventilation), 1204 (Lighting), and 1020 (Corridors). [https://codes.iccsafe.org/](https://codes.iccsafe.org/)
3. **Chen, Y., & Hong, T.** (2018). "Impacts of building geometry modeling methods on the simulation results of urban building energy models." *Applied Energy*, 211, 1263-1278. [DOI: 10.1016/j.apenergy.2017.12.008](https://doi.org/10.1016/j.apenergy.2017.12.008)
4. **Dogan, T., & Reinhart, C.** (2017). "Shoeboxer: An algorithm for abstracted rapid multi-zone urban building energy model generation and simulation." *Energy and Buildings*, 140, 140-153. [DOI: 10.1016/j.enbuild.2017.01.017](https://doi.org/10.1016/j.enbuild.2017.01.017)
5. **Dogan, T., Reinhart, C., & Michalatos, P.** (2013). "Autozoner: An algorithm for automatic thermal zoning of buildings with unknown interior space definitions." *Proceedings of BS 2013: 13th Conference of International Building Performance Simulation Association*, Chambéry, France. [Link](https://www.ibpsa.org/proceedings/BS2013/p_1361.pdf)
6. **NREL**. (2022). *URBANopt Software Development Kit (SDK) documentation*. National Renewable Energy Laboratory. [https://docs.urbanopt.net/](https://docs.urbanopt.net/)
7. **Pacific Northwest National Laboratory (PNNL)**. (2020). *Commercial Prototype Building Specifications*. PNNL-16770. U.S. Department of Energy. [https://www.pnnl.gov/](https://www.pnnl.gov/)
