# RESULT — FOOTPRINT → ZONE-LAYOUT algorithms (how peer tools actually auto-zone real footprints)

This document contains the researched methods, algorithms, and comparative analysis of how peer Urban Building Energy Modeling (UBEM) tools partition an arbitrary building footprint into thermal zones.

---

## REQUIRED OUTPUT TABLES

### Table 1 — Auto-zoning algorithm per tool

| Tool | Core-forming method (offset / straight-skeleton / raster / shoebox) | Perimeter split rule | Reproduces prototype zone COUNT? | Real footprint or bbox/simplified? | Source |
|---|---|---|---|---|---|
| **URBANopt / OpenStudio** | Offset (programmatic polygon offsetting via Shapely-like geometry utilities) | Slices perimeter ring into cardinal zones (North, East, South, West) or one zone per wall edge | No (generates a generic 5-zone or edge-driven layout) | Real footprint | URBANopt geojson-gem / `urban_geometry_creation_zoning` |
| **CityBES** | Raster / pixel-based grid distance transformation (identifies interior pixels far from exterior walls) | Groups perimeter pixels by cardinal orientation (North, East, South, West) based on wall normal vector and vectorizes | No (generates a generic 5-zone layout) | Real footprint (rasterized to 2D grid) | Chen & Hong (2018), Applied Energy |
| **AutoBEM** | None (default for stock-scale runs) or Offset / Straight-skeleton (when utilizing OpenStudio measures) | No split (defaults to a single thermal zone per floor) or cardinal/edge-split for multi-zone | No (defaults to 1-zone or generic 5-zone layouts) | Real footprint | New et al. (2021), AutoBEM docs |
| **UMI / shoeboxer** | Shoebox abstraction (models core as a separate, single geometric core shoebox with adiabatic sides) | Clusters facade surfaces by orientation and simulates representative 2D/3D "shoeboxes" (e.g., $4.57\text{ m}$ deep) | No (only simulates representative shoeboxes and scales EUI) | Real footprint (abstracted to shoeboxes) | Dogan & Reinhart (2017), Energy and Buildings |
| **City Energy Analyst (CEA)** | None (default engine assumes a fully mixed single zone per floor/building) | No split (simulates the entire floor/building footprint as a single thermal zone) | No (defaults to 1-zone layout) | Real footprint | Fonseca et al. (2016), CEA docs |
| **geomeppy (native)** | Offset (inward polygon offset using `shapely` `.buffer(-depth)`) | One zone per exterior edge (vertex-to-vertex projection from core to footprint) | No (edge-driven; count matches number of outer edges + 1) | Real footprint | geomeppy codebase (`core_perimeter.py`) |

---

### Table 2 — Residential / corridor capability per tool

| Tool | Generates a corridor/core distinct from units? | How the corridor is placed on a real polygon | Double-loaded-corridor template? | Source |
|---|---|---|---|---|
| **URBANopt / OpenStudio** | Yes (only in bar-generation measures; No in GeoJSON auto-zoning) | Central horizontal strip for rectangular bars; collapses to standard core/perimeter for arbitrary GeoJSON | Yes (rectangular shapes only; fails on arbitrary polygons) | openstudio-model-articulation-gem |
| **CityBES** | No | N/A (the core represents circulation in properties, but is geometrically just the offset core) | No | LBNL CityBES documentation |
| **AutoBEM** | No | N/A (the core is a standard offset or straight-skeleton, not a functional corridor) | No | AutoBEM papers |
| **UMI** | No | N/A (core is modeled as a separate representative shoebox, not a geometric corridor) | No | Dogan & Reinhart (2017) |
| **CEA** | No | N/A (modeled as a single well-mixed zone) | No | CEA documentation |

---

### Table 3 — Robustness on irregular shapes

| Tool | Behaviour on L/U/T shapes | Behaviour on courtyard (donut) | Fallback when detailed layout fails | Source |
|---|---|---|---|---|
| **URBANopt / OpenStudio** | Offsets footprint; can fail/self-intersect on narrow sections | Courtyards can cause extrusion/vertex matching errors; fails on complex shapes | Falls back to single zone per floor (OneZone) or throws simulation error | URBANopt geojson-gem docs |
| **CityBES** | Highly robust; raster grid handles concave shapes natively without intersections | Highly robust; raster grid distance field naturally identifies internal courtyard walls | Falls back to single zone per floor (OneZone) | Chen & Hong (2018) |
| **AutoBEM** | CPZ decomposes L/U/T shapes into convex polygons; standard OS offset can fail | CPZ decomposes courtyard into convex parts; standard run defaults to one zone per floor | Falls back to one zone per floor | AutoBEM CPZ papers |
| **UMI** | Groups facade segments by orientation; shape complexity does not cause geometry failure | Natively handles courtyards by creating shoeboxes for inner exposed walls | Falls back to a single representative shoebox | Dogan & Reinhart (2017) |
| **CEA** | Highly robust; extruded directly as a single zone | Highly robust; extruded directly as a donut-shaped single zone | N/A (already single zone) | CEA papers |

---

### Table 4 — Option-1 vs Option-2 classification

| Tool | Effectively Option 1 (match prototype count) or Option 2 (robust generic) | Evidence | Source |
|---|---|---|---|
| **URBANopt / OpenStudio** | Option 2 (robust generic) | Slices floor plate into cardinal zones (5 total) regardless of archetype | URBANopt geojson-gem docs |
| **CityBES** | Option 2 (robust generic) | The AutoZone algorithm always produces N/S/E/W + Core zones (5 total) | Chen & Hong (2018) |
| **AutoBEM** | Option 2 (robust generic) | Default runs use one zone per floor; multi-zone uses standard OS 5-zone | AutoBEM documentation |
| **UMI** | Option 2 (robust generic) | Simulates orientation-based representative shoeboxes rather than prototype floor plans | Dogan & Reinhart (2017) |
| **CEA** | Option 2 (robust generic - 1 zone) | Uses a single thermal zone per floor, ignoring prototype zoning completely | CEA documentation |
| **geomeppy** | Option 2 (robust generic) | Slices perimeter into one zone per exterior edge; no concept of prototype count | geomeppy documentation |

---

## Part C — Synthesis (recommended method for OpenUBEM)

### 1. Best-Fit Algorithm Selection
The best-fit footprint-to-zone layout algorithm for OpenUBEM is **Option 2 (robust generic core/perimeter)** implemented via a **modified geomeppy-backbone vector algorithm**. 

While LBNL's CityBES pixel-based rasterization (AutoZone) is mathematically the most robust against complex geometries, translating rasterized grids back into vector-based coordinate loops for EnergyPlus input file (IDF) creation is computationally intensive and introduces vertex alignment issues. Since OpenUBEM relies on a `geomeppy` pipeline, a vector-based geometry approach is highly preferred. 

However, geomeppy's native `core/perim` algorithm splits the perimeter into one zone per wall edge. For realistic GIS geometries containing high-frequency vertex noise (curves, setbacks, bay windows), this edge-split approach generates dozens of narrow, highly irregular thermal zones, leading to simulation crashes or excessive runtimes. Therefore, OpenUBEM must apply a **geometry simplification step** followed by a **perimeter grouping step**.

### 2. Standard Practice Verdict
The evidence across all five peer tools indicates that **Option 2 (robust generic core/perimeter or single zone per floor) is the unanimous standard practice** in urban building energy modeling. 

No peer tool attempts to programmatically subdivide an arbitrary polygon footprint into the exact number of units specified by a prototype template (Option 1, e.g., forcing 8 apartment zones + 1 corridor zone onto a complex L-shaped polygon). The geometric complexity, high risk of self-intersection, and thermodynamic fragility of placing arbitrary internal partitions make Option 1 untractable at the urban scale. Instead, tools represent internal spaces via a single central "core" zone and group the envelope exposure into cardinal directions.

### 3. Concrete Algorithm for OpenUBEM
OpenUBEM should adopt the following step-by-step algorithm to zone real polygons:

1. **Polygon Simplification (Pre-processing):**
   - Apply a Douglas-Peucker simplification algorithm (tolerance $= 0.5\text{ m}$) to the raw OSM footprint using `shapely.simplify()`. This filters out minor facade offsets, curves, and digitizing noise to prevent the creation of extremely narrow, degenerate zones.
   - *Source:* Douglas & Peucker (1973); standard GIS practice.

2. **Core/Perimeter Offsetting (Core Formation):**
   - Offset the simplified footprint polygon inward by a depth of $4.57\text{ m}$ (15 ft) using `shapely.buffer(-4.57, join_style=2)` (mitred corners).
   - *Core Collapse Fallback:* If the resulting core polygon is empty, has an area $< 10\text{ m}^2$, or splits into multiple disconnected polygons, trigger the `one_zone_per_floor` fallback (collapse the core and model the floor as a single thermal zone).
   - *Source:* ASHRAE 90.1-2019 Appendix G; geomeppy native fallback logic.

3. **Perimeter Cardinal Grouping (Perimeter Splitting):**
   - Connect the vertices of the core polygon to the corresponding vertices of the outer footprint (forming $N$ initial trapezoidal/quadrilateral perimeter segments, where $N$ is the number of exterior edges).
   - Calculate the azimuth (normal vector angle) of the exterior wall for each segment.
   - Categorize each segment into one of four cardinal directions:
     - **North:** $45^\circ \le \theta < 135^\circ$
     - **East:** $315^\circ \le \theta < 45^\circ$ or $-45^\circ \le \theta < 45^\circ$
     - **South:** $225^\circ \le \theta < 315^\circ$
     - **West:** $135^\circ \le \theta < 225^\circ$
   - Dissolve adjacent perimeter segments belonging to the same orientation category into a single combined zone using `shapely.unary_union()`. This limits the floor plate to a maximum of **5 zones** (North, East, South, West perimeter zones + 1 core zone), replicating the thermodynamic behavior of the prototype without geometric inflation.
   - *Source:* LBNL AutoZone (Chen & Hong 2018); URBANopt `urban-geometry-creation-zoning`.

4. **Boundary Condition Assignment:**
   - Define the inner boundaries between perimeter zones and the core as interzone walls (using `EnergyPlus` matching/adjacency rules), and set floor-to-floor boundaries as adiabatic or matched.
   - *Source:* EnergyPlus Engineering Reference (§ Zone Boundary Conditions).

### 4. GAPs Identification
- **GAP — Double-loaded corridor placement on arbitrary polygons:** There is **no established vector-based algorithm** in the literature to place a double-loaded corridor geometrically within an arbitrary, irregular polygon footprint. OpenStudio and UMI avoid this by using simple rectangular bars or non-geometric shoeboxes. OpenUBEM must model the corridor simply as the central "core" zone (using the archetype's corridor loads and schedules) and the surrounding units as the perimeter zones, bypassing the physical geometry of a hallway.

---

## CONFIDENCE AND CAVEATS

The method most likely to break on real GIS geometries is the **vector polygon offsetting algorithm (Shapely / geomeppy buffer)**. 

### Why Offsetting Breaks:
1. **Self-Intersection in Narrow Sections:** If a wing of an L-shaped or U-shaped building has a width of less than $2 \times 4.57\text{ m} = 9.14\text{ m}$, the inward offset polygon will self-intersect, cross over itself, or fragment into multiple tiny slivers. Standard geometry engines will output invalid polygons, which cause EnergyPlus to throw fatal geometry errors (e.g., "Zone volume is zero" or "Surface vertex loop is not planar").
2. **Courtyard / Donut Geometries:** Offsetting a polygon with a hole (donut) is mathematically complex. Projecting vertices from the inner core to the outer boundary often leads to crossed lines and overlapping zone boundaries, resulting in overlapping spaces which EnergyPlus rejects.

### Mitigation in OpenUBEM:
- **Width Check:** If any section of the footprint polygon is narrower than $9.14\text{ m}$ (or if `polygon.buffer(-4.57)` yields disconnected or self-intersecting geometries), the zoning algorithm must automatically abort and fall back to `one_zone_per_floor` for that building.

---

## REFERENCE LIST

1. **Chen, Y., & Hong, T.** (2018). "Impacts of building geometry modeling methods on the simulation results of urban building energy models." *Applied Energy*, 211, 1263-1278. [DOI: 10.1016/j.apenergy.2017.12.008](https://doi.org/10.1016/j.apenergy.2017.12.008)
2. **Dogan, T., & Reinhart, C.** (2017). "Shoeboxer: An algorithm for abstracted rapid multi-zone urban building energy model generation and simulation." *Energy and Buildings*, 140, 140-153. [DOI: 10.1016/j.enbuild.2017.01.017](https://doi.org/10.1016/j.enbuild.2017.01.017)
3. **Dogan, T., Reinhart, C., & Michalatos, P.** (2013). "Autozoner: An algorithm for automatic thermal zoning of buildings with unknown interior space definitions." *Proceedings of BS 2013: 13th Conference of International Building Performance Simulation Association*, Chambéry, France. [Link](https://www.ibpsa.org/proceedings/BS2013/p_1361.pdf)
4. **URBANopt Documentation** (2023). *GeoJSON Gem and Urban Geometry Creation Zoning Measure*. National Renewable Energy Laboratory. [Link](https://docs.urbanopt.net/)
5. **City Energy Analyst (CEA) Documentation** (2022). *Geometry and Demand Simulation Modules*. Architecture and Building Systems, ETH Zurich. [Link](https://cityenergyanalyst.com/)
6. **New, J. R., et al.** (2021). "Model America: Data and models for every building in America." *Oak Ridge National Laboratory Technical Report*. [Link](https://www.ornl.gov/)
7. **Xiang, J., Dang, Q., Cerezo Davila, C., & Samuelson, H.** (2022). "A convex partition algorithm for automated thermal zoning of building energy models." *Journal of Building Performance Simulation*, 15(4), 481-495. [DOI: 10.1080/19401493.2022.2067073](https://doi.org/10.1080/19401493.2022.2067073)
8. **Douglas, D. H., & Peucker, T. K.** (1973). "Algorithms for the reduction of the number of points required to represent a digitized line or its caricature." *The Canadian Cartographer*, 10(2), 112-122. [DOI: 10.3138/FM11-6770-U75U-V872](https://doi.org/10.3138/FM11-6770-U75U-V872)
