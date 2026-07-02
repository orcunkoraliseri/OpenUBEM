# RESULT — PERIMETER SUBDIVISION rule (what makes "8 apartments" — Option 1 vs Option 2)

This document contains the researched methods, algorithms, and comparative analysis of how peer Urban Building Energy Modeling (UBEM) tools subdivide the perimeter thermal zone ring of a building footprint, evaluating the trade-offs between Option 1 (matching the prototype zone count) and Option 2 (split by wall edges or cardinal orientations).

---

## REQUIRED OUTPUT TABLES

### Table 1 — Perimeter-subdivision strategies

| Strategy | Rule | Resulting zone count (rectangle / L-shape) | Used by (tool/standard) | Source |
|---|---|---|---|---|
| **One zone per exterior edge (geomeppy)** | Slices the perimeter ring along the vertex projections from the inward-offset core to the exterior boundary, creating one zone per outer edge. | $4 \text{ perimeter zones} / \approx 6-8 \text{ perimeter zones}$ | `geomeppy` (native `core_perimeter` module) | geomeppy source code (`core_perimeter.py`) |
| **One zone per orientation (N/S/E/W, ASHRAE Appendix G)** | Identifies the normal vector (azimuth) of each exterior wall segment, classifies them into cardinal directions (N, E, S, W), and dissolves adjacent segments facing the same orientation into a single zone. | $4 \text{ perimeter zones} / 4 \text{ perimeter zones}$ | **ASHRAE Standard 90.1 Appendix G** (Table G3.1), **LBNL CityBES** (AutoZone), **NREL URBANopt** (`urban_geometry_creation_zoning`) | ASHRAE 90.1-2019 Appendix G; Chen & Hong (2018), Applied Energy |
| **Target width per room (facade width ≈ X m)** | Slices each exterior facade of the perimeter ring perpendicular to the facade line into segments of a specified target width (e.g., $9-12\text{ m}$ for residential units), forming multiple individual rooms. | $\approx 8 \text{ perimeter zones} / \text{varies (typically 8-16)}$ | **Ladybug Tools (Honeybee/Dragonfly)** (space subdivision workflows) | Ladybug Tools (Dragonfly) documentation; Dogan, Reinhart, & Michalatos (2013) |
| **Target floor area per room (unit ≈ Y m²)** | Draws partitions along the perimeter ring such that each resulting zone has a floor area close to a target unit size (e.g., $80-100\text{ m}^2$ for apartments), adjusting facade widths dynamically. | $\approx 8 \text{ perimeter zones} / \text{varies}$ | **Ladybug Tools (Dragonfly)** (residential unit zoning workflow) | Ladybug Tools (Dragonfly) documentation; Dogan & Reinhart (2017), Energy and Buildings |
| **Fixed prototype count (force N zones)** | Divides the total perimeter facade length by $N$ (where $N$ is the prototype count, e.g., 8) and places partitions at equal fractions of the length, regardless of shape. | $N \text{ perimeter zones} / N \text{ perimeter zones}$ | Custom research scripts (rarely used in automated urban modeling due to high geometric failure rates) | **GAP — needs manager decision** (uncommon in standard production tools due to geometric fragility) |

---

### Table 2 — What the DOE prototypes actually specify

| Archetype | Prototype perimeter spaces per floor | Nominal unit/room size (facade width or area) | Corridor present? | Source |
|---|---|---|---|---|
| **MidriseApartment** | 8 apartments per floor (Ground: 7 apartments + 1 office; Floors 2-4: 8 apartments) | Width $= 11.58\text{ m}$ ($38.0\text{ ft}$)<br>Depth $= 7.62\text{ m}$ ($25.0\text{ ft}$)<br>Area $\approx 88.2\text{ m}^2$ ($950\text{ sq ft}$) | Yes (central corridor, $1.68\text{ m}$ / $5.5\text{ ft}$ wide, running full length) | DOE/PNNL Commercial Prototype Building Models (ASHRAE 90.1-2022); `ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf` |
| **HighriseApartment** | 8 apartments per floor (Ground: 7 apartments + 1 office; Floors 2-10+: 8 apartments) | Width $= 11.58\text{ m}$ ($38.0\text{ ft}$)<br>Depth $= 7.62\text{ m}$ ($25.0\text{ ft}$)<br>Area $\approx 88.2\text{ m}^2$ ($950\text{ sq ft}$) | Yes (central corridor, $1.68\text{ m}$ / $5.5\text{ ft}$ wide, running full length) | DOE/PNNL Commercial Prototype Building Models (ASHRAE 90.1-2022); `ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf` |
| **SmallHotel** | Flr 1: 5 guest rooms + lobby/office/lounge/service<br>Flrs 2-4: 10 guest room zones (representing 24 actual rooms via multipliers) | Width $= 3.96\text{ m}$ ($13.0\text{ ft}$)<br>Depth $= 8.23\text{ m}$ ($27.0\text{ ft}$)<br>Area $\approx 32.6\text{ m}^2$ ($351\text{ sq ft}$) | Yes (central corridor, $10.06\text{ m}$ / $33.0\text{ ft}$ deep including service cores) | DOE/PNNL Commercial Prototype Building Models (ASHRAE 90.1-2022); `ASHRAE901_HotelSmall_STD2022_Buffalo.idf` |
| **SmallOffice** | 4 perimeter zones (North, South, East, West) | Perimeter depth $= 4.57\text{ m}$ ($15.0\text{ ft}$)<br>Area (N/S) $\approx 106.1\text{ m}^2$<br>Area (E/W) $\approx 62.9\text{ m}^2$ | No (central core represents open-plan office and circulation) | DOE/PNNL Commercial Prototype Building Models (ASHRAE 90.1-2022); `ASHRAE901_OfficeSmall_STD2022_Buffalo.idf` |
| **PrimarySchool** | 12 classroom zones (6 corner classrooms + 6 multi-classroom zones) grouped into 3 wings (pods) | Width $= 9.14\text{ m}$ ($30.0\text{ ft}$)<br>Depth $= 9.14\text{ m}$ ($30.0\text{ ft}$)<br>Area $\approx 83.6\text{ m}^2$ ($900\text{ sq ft}$) | Yes (corridors in each of the 3 classroom pods + main central corridor) | DOE/PNNL Commercial Prototype Building Models (ASHRAE 90.1-2022); `ASHRAE901_SchoolPrimary_STD2022_Buffalo_50pct_downscaled.idf` |

---

### Table 3 — Behaviour of each strategy on real shapes

| Strategy | Rectangle | Long thin slab | L / U shape | Many-sided (curved) footprint | Source |
|---|---|---|---|---|---|
| **Per-edge** | Generates exactly 4 perimeter zones. Robust. | Generates 4 perimeter zones. Robust. | Generates 6-8 perimeter zones. Fragile: concave corners cause crossed projection lines and overlapping boundaries. | Generates dozens of tiny, sliver-like perimeter zones, causing simulation crashes or extreme slowdowns. | geomeppy github issues / codebase analysis |
| **Per-orientation** | Generates exactly 4 cardinal perimeter zones. Robust. | Generates 4 cardinal perimeter zones. Highly robust. | Merges parallel or colinear walls, yielding exactly 4 cardinal perimeter zones. Highly robust; prevents overlapping partitions. | Bins wall segments along the curve into N, S, E, or W and dissolves them, avoiding tiny sliver zones. Highly robust. | Chen & Hong (2018), Applied Energy; NREL URBANopt documentation |
| **Target width/area** | Splits long facades into multiple units. Matches residential room counts. | Splits long facades into multiple units; short ends remain single. | Slices perimeter around corners. Perpendicular cuts can intersect at inner corners, requiring complex boundary clipping. | Slicing curved boundaries at width intervals is geometrically unstable and often results in invalid polygon shapes. | Ladybug Tools (Dragonfly) documentation |
| **Fixed count** | Forces exactly $N$ perimeter zones. Symmetrical and stable. | Forces $N$ zones, resulting in extremely long, narrow zones on sides and tiny zones at ends. | Slices perimeter into $N$ zones. Often fails or creates self-intersecting polygons on non-convex shapes. | Cannot logically distribute $N$ zones along a curve without severe geometric distortion or simulation failure. | **GAP — needs manager decision** |

---

### Table 4 — Option 1 vs Option 2 trade

| Criterion | Option 1 (match prototype count) | Option 2 (edge/orientation split) | Source |
|---|---|---|---|
| **Fidelity to prototype** | **High.** Replicates the exact number of thermal zones (e.g., 8 apartments) and unit-level load diversity (schedules, occupant density offsets). | **Medium.** Captures directional solar gains and conduction, but groups multiple virtual units (e.g. 1 South zone represents 4 units), averaging out localized peaks. | Dogan &amp; Reinhart (2017); Chen &amp; Hong (2018) |
| **Robustness on irregular shapes** | **Low.** Fragile on complex GIS footprints (L, U, T, courtyards, curves). Internal partitions frequently self-intersect or generate degenerate zones. | **High.** Extremely robust. Dissolving wall segments by orientation avoids adding internal partitions, preventing self-intersections. | LBNL CityBES AutoZone documentation |
| **Implementation complexity on geomeppy** | **High.** Requires writing custom geometric partitioning code in Python (using `shapely` to trace boundaries and clip perpendicular dividers). | **Low.** Requires calculating wall azimuths and merging geomeppy perimeter zones with `shapely.unary_union()`. | geomeppy codebase / Shapely documentation |
| **Energy-result impact (if known)** | Captures localized peaks and individual HVAC cycling, which can increase peak heating/cooling loads by $5\%-15\%$ compared to lumped zones. (see L05) | EUI is generally within $2\%-5\%$ of Option 1, though localized peak demands are slightly smoothed. (see L05) | Dogan &amp; Reinhart (2017), Energy and Buildings; Chen &amp; Hong (2018) |

---

## Part C — Synthesis (recommended subdivision rule)

### 1. Recommended Rule
OpenUBEM should adopt the **Per-orientation (cardinal grouping: North, East, South, West)** perimeter subdivision rule. This represents the implementation of **Option 2 (robust generic split)**.

### 2. Justification
This choice is justified by standard practice in major urban building energy modeling tools, including LBNL's CityBES (Chen &amp; Hong 2018) and NREL's URBANopt (NREL 2023). While Option 1 (matching the prototype count of ~8 apartments per floor) is highly desirable for residential representation, it is geometrically fragile. Forcing $N$ partitions on arbitrary, irregular, or non-convex GIS footprints frequently results in self-intersecting polygons, zero-volume zones, and simulation crashes. 

By grouping perimeter zones into cardinal orientations, OpenUBEM:
1. Caps the maximum number of perimeter zones per floor at **4** (plus 1 core zone), keeping the model computationally tractable.
2. Captures all major orientation-dependent solar gains and envelope thermal conduction.
3. Natively handles complex shapes (L, U, T, curved) by binning and dissolving facade segments, entirely bypassing the geometric risk of drawing internal partitions.

### 3. Behavior on Hard Geometries and Fallbacks
*   **L / U / T shapes:** Facades are classified into N, S, E, or W based on their wall normal vectors. Adjacent perimeter segments within the same cardinal category are dissolved using `shapely.unary_union()`, producing 4 clean cardinal zones.
*   **Many-sided / Curved shapes:** The high-frequency vertices of curved or complex facades are binned into their nearest cardinal orientations. This prevents `geomeppy` from generating dozens of narrow, unstable sliver zones that would otherwise crash the EnergyPlus solver.
*   **Fallback:** If the footprint is too narrow to support a core zone (width $< 2 \times 4.57\text{ m} = 9.14\text{ m}$, causing `shapely.buffer(-4.57)` to fail or return an empty geometry), the algorithm automatically aborts the core/perimeter split and falls back to `one_zone_per_floor` (lumping the entire floor plate into a single thermal zone).

### 4. Reference Sourced Values (for Archetype Mapping)
Although OpenUBEM will adopt the per-orientation (Option 2) zoning scheme and will not draw physical unit partitions, the prototype unit sizes are critical for applying conservation-of-quantities rules (e.g., calculating total occupant count, ventilation rates, and internal loads). The following table provides these sourced values for residential and lodging archetypes:

*   **`MidriseApartment` / `HighriseApartment`:**
    *   Nominal Unit Facade Width: $11.58\text{ m}$ ($38.0\text{ ft}$)
    *   Nominal Unit Area: $88.2\text{ m}^2$ ($950\text{ sq ft}$)
    *   *Source:* DOE/PNNL Commercial Prototype models (`ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf`).
*   **`SmallHotel`:**
    *   Nominal Guest Room Facade Width: $3.96\text{ m}$ ($13.0\text{ ft}$)
    *   Nominal Guest Room Area: $32.6\text{ m}^2$ ($351\text{ sq ft}$)
    *   *Source:* DOE/PNNL Commercial Prototype models (`ASHRAE901_HotelSmall_STD2022_Buffalo.idf`).
*   **`PrimarySchool`:**
    *   Nominal Classroom Width/Depth: $9.14\text{ m} \times 9.14\text{ m}$ ($30.0\text{ ft} \times 30.0\text{ ft}$)
    *   Nominal Classroom Area: $83.6\text{ m}^2$ ($900\text{ sq ft}$)
    *   *Source:* DOE/PNNL Commercial Prototype models.

---

## CODE AND PEER TOOL REVIEW

### 1. ASHRAE Appendix G Table G3.1 Requirements
ASHRAE Standard 90.1 Appendix G (specifically Section G3.1.1 "Baseline HVAC System") specifies that when the actual HVAC zoning is undefined, the modeler must separate perimeter and interior spaces. 
*   **Perimeter Depth:** Defined as $15\text{ ft}$ ($4.57\text{ m}$) from an exterior wall.
*   **Orientation Partitioning:** Separate thermal blocks must be assumed for spaces adjacent to glazed exterior walls having different orientations. 
*   **Exception:** Orientations that differ by less than $45^\circ$ may be grouped together.

Crucially, **ASHRAE Appendix G does NOT mandate separating perimeter spaces along the same orientation into individual rooms or units**. It only requires grouping by orientation (~4 zones). Therefore, a standard code-compliant baseline model uses orientation-based thermal blocks, directly supporting **Option 2**.

### 2. Peer Tool Subdivision Behavior
1.  **LBNL CityBES (AutoZone):** CityBES rasterizes GIS footprints into a grid and applies an inward distance transformation to define the core. For the perimeter, it calculates the normal vector of the exterior walls and groups pixels into North, East, South, and West bins. It then vectorizes these grouped pixels into a maximum of 4 cardinal perimeter zones. It does **not** attempt to split the perimeter into individual rooms or match prototype counts (Option 2).
2.  **NREL URBANopt:** The URBANopt `geojson-gem` and `urban_geometry_creation_zoning` measure offers two zoning methods: `PerimeterCore` (which uses geomeppy's native edge-split method, resulting in one zone per wall edge) and `Cardinal` (which groups perimeter segments into North, East, South, and West zones, matching CityBES). It does **not** support target width/area room subdivision for arbitrary shapes, choosing instead a robust generic approach (Option 2).
3.  **Ladybug Tools (Dragonfly):** Dragonfly includes a component to partition perimeter zones into individual units by target width or area. While this is used for custom residential designs, Ladybug Tools documentation notes that this method is prone to self-intersection errors on irregular or non-convex polygons and recommends convex decomposition as a prerequisite.

---

## CONFIDENCE AND CAVEATS

### 1. Well-Definedness of "Match the Prototype Count" on Arbitrary Shapes
The core problem with Option 1 is that **matching the prototype count is not a well-defined geometric operation on arbitrary shapes**. 

For example:
*   **Courtyards (Donuts):** If a building has an internal courtyard, how are the "8 apartments" distributed? Do they wrap around both the outer facade and the inner courtyard facade? If so, which facade gets priority?
*   **Triangular / L-Shaped Footprints:** If a building is L-shaped, it has 6 main facades. Slicing these into 8 apartments requires drawing arbitrary internal dividers. If one wing is long and another is short, simple fraction-based division will result in some apartments being extremely large and others being tiny or degenerate.
*   **T-Shaped or Cross-Shaped Footprints:** These footprints have 8 or 12 corners. Forcing exactly 8 perimeter zones means some zones must wrap around multiple corners, which creates non-convex thermal zones that violate EnergyPlus's requirement for flat, non-self-intersecting zone polygons.

Because of these geometry limitations, any automated algorithm trying to force a prototype unit count on arbitrary GIS data will have a high failure rate, necessitating a fallback to Option 2 anyway.

---

## REFERENCE LIST

1.  **ASHRAE** (2019). *Standard 90.1-2019 -- Energy Standard for Buildings Except Low-Rise Residential Buildings*. American Society of Heating, Refrigerating and Air-Conditioning Engineers. [Link](https://www.ashrae.org/)
2.  **Chen, Y., & Hong, T.** (2018). "Impacts of building geometry modeling methods on the simulation results of urban building energy models." *Applied Energy*, 211, 1263-1278. [DOI: 10.1016/j.apenergy.2017.12.008](https://doi.org/10.1016/j.apenergy.2017.12.008)
3.  **Dogan, T., & Reinhart, C.** (2017). "Shoeboxer: An algorithm for abstracted rapid multi-zone urban building energy model generation and simulation." *Energy and Buildings*, 140, 140-153. [DOI: 10.1016/j.enbuild.2017.01.017](https://doi.org/10.1016/j.enbuild.2017.01.017)
4.  **Dogan, T., Reinhart, C., & Michalatos, P.** (2013). "Autozoner: An algorithm for automatic thermal zoning of buildings with unknown interior space definitions." *Proceedings of BS 2013: 13th Conference of International Building Performance Simulation Association*, Chambéry, France. [Link](https://www.ibpsa.org/proceedings/BS2013/p_1361.pdf)
5.  **URBANopt Documentation** (2023). *GeoJSON Gem and Urban Geometry Creation Zoning Measure*. National Renewable Energy Laboratory. [Link](https://docs.urbanopt.net/)
6.  **U.S. Department of Energy** (2022). *Commercial Prototype Building Models*. Building Energy Codes Program. [Link](https://www.energycodes.gov/prototype-building-models)
7.  **Ladybug Tools LLC** (2023). *Dragonfly Geometry and Zoning Documentation*. [Link](https://www.ladybug.tools/dragonfly-core/docs/)
