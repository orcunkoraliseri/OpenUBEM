# Rigorous Review of Automatic Thermal Zoning and Fallback Strategies in UBEM and BEM Tools

This report reviews the automatic thermal zoning practices—specifically the decomposition of building footprints into a **core zone** and **perimeter zones**—across major Urban Building Energy Modeling (UBEM) and Building Energy Modeling (BEM) tools. It details the geometric algorithms used, perimeter depth configurability, pre-cleaning tolerances, and the fallback behaviors when encountering degenerate geometries (e.g., highly concave shapes, narrow wings, interior courtyard holes, sliver zones, and polygon self-intersections).

---

## 1. City Energy Analyst (CEA)

### Auto-Zoning Algorithm
*   **Methodology:** In its default and standard release, CEA does **not** auto-generate core-perimeter zones. Instead, it models each building floor as a **single well-mixed thermal zone** (or a single thermal zone for the entire building volume).
*   **Zoning Logic:** CEA assumes that detailed spatial zoning is unavailable at the urban scale. It extrudes building footprints (`zone.shp`) into simple 3D envelopes and computes building-level heating and cooling demands using a reduced-order resistance-capacitance (RC) model based on ISO 52016-1:2017.

### Perimeter Depth
*   **Value:** Not applicable (defaults to a single zone per floor).
*   **Configurability:** No default parameter exists for geometric perimeter offsetting in the core codebase.

### Robustness & Failure Handling
*   **Fallback Strategy:** Because CEA avoids geometric decomposition of the floor plate, it is inherently immune to core-perimeter zoning crashes (such as self-intersection or sliver zones). If a footprint is concave or contains holes, CEA simply extrudes the polygon as a single zone.
*   **Holes/Courtyards:** Courtyards and interior holes represented in the GIS shapefile are extruded as empty space (voids) in the envelope, but the surrounding floor area remains modeled as a single, contiguous thermal zone.

### Pre-cleaning & Footprint Simplification
*   **Approach:** CEA does not automatically simplify footprint vertices, collapse coordinates, or compute convex hulls. It relies on the user importing pre-cleaned shapefiles into `inputs/building-geometry/zone.shp`. If the shapefile contains topological errors, the simulation will fail during the subsequent radiation or demand calculations.

### Citations
*   **Paper:** Fonseca, J. A., Nguyen, T.-A., Schlueter, A., & Thomas, D. (2016). *City Energy Analyst (CEA): An open-source framework for analysis and optimization of building energy systems in districts.* Energy and Buildings, 120, 71-85. [DOI: 10.1016/j.enbuild.2016.03.054](https://doi.org/10.1016/j.enbuild.2016.03.054) (Access Date: June 19, 2026).
*   **Code Reference:** `architecture-building-systems/CityEnergyAnalyst` GitHub repository. [Link](https://github.com/architecture-building-systems/CityEnergyAnalyst) (Access Date: June 19, 2026).

---

## 2. URBANopt + NREL openstudio-standards

### Auto-Zoning Algorithm
*   **Methodology:** URBANopt automatically generates core-perimeter zones from 2D footprints using the OpenStudio Measure `UrbanGeometryCreationZoning` (part of the `urbanopt-geojson-gem` library).
*   **Zoning Logic:** It uses a **fixed-depth vertex offset bisector method** implemented in Ruby. For each vertex in the footprint, it:
    1. Projects the vertex onto a local 2D coordinate system aligned with the floor plate.
    2. Calculates the bisector of the angle between the two adjacent edges.
    3. Shifts the vertex along this bisector inward by the specified `perimeter_depth` to generate the core boundary.
    4. Connects the original outer edges with their corresponding inner offset segments to form quadrilateral perimeter zones.

### Perimeter Depth
*   **Value:** **4.0 meters** (~13.1 feet).
*   **Configurability:** The value `4.0` is hardcoded in `create_space_per_floor` in `lib/urbanopt/geojson/building.rb` and is **not configurable** via standard GeoJSON properties.

### Robustness & Failure Handling
*   **Holes/Courtyards:** URBANopt **explicitly ignores interior holes**. In `lib/urbanopt/geojson/building.rb`, the parser loops over the polygons of a GeoJSON `MultiPolygon` feature. The first polygon (outer ring) is processed, a warning is registered if multiple rings exist (`"Ignoring holes in polygon"`), and a `break` statement immediately exits the loop, discarding all interior boundaries.
*   **Slivers & Collapse:** If a footprint is narrower than twice the perimeter depth ($2 \times 4.0\text{ m} = 8.0\text{ m}$), the inward offset vectors cross over each other, causing the core polygon to collapse or invert.
*   **Fallback Behavior:** 
    *   **Inverted Normal Check:** The code checks if the offset core polygon has a reversed normal direction (negative Z component) via `OpenStudio.getOutwardNormal`. If true, it logs `'Wrong direction for resulting normal, will not divide'` and falls back to representing the entire floor as a **single thermal zone** (`return [floor_print]`).
    *   **Self-Intersection Check:** The algorithm checks for self-intersections using `OpenStudio.selfIntersects`. If true, it logs `'Self intersecting surface result, will not divide'`. *However, due to a programmatic omission in `zoning.rb`, it fails to return early in this block and continues to partition the geometry anyway*, which can write invalid, self-intersecting surfaces to the OSM file and crash EnergyPlus during runtime.

### Pre-cleaning & Footprint Simplification
*   **Approach:** No automatic vertex simplification (like Douglas-Peucker) or convex-hull wrapping is performed prior to the zoning calculations. The tool relies on clean, single-ring polygons in the GeoJSON file.

### Citations
*   **Documentation:** NREL (2020). *URBANopt Documentation: GeoJSON Geometry Creation.* [URL](https://urbanopt.github.io/) (Access Date: June 19, 2026).
*   **Code Reference:** `urbanopt/urbanopt-geojson-gem` GitHub repository:
    *   Measure Entry: [`lib/measures/urban_geometry_creation_zoning/measure.rb`](https://github.com/urbanopt/urbanopt-geojson-gem/blob/develop/lib/measures/urban_geometry_creation_zoning/measure.rb)
    *   Geometry Processor: [`lib/urbanopt/geojson/building.rb`](https://github.com/urbanopt/urbanopt-geojson-gem/blob/develop/lib/urbanopt/geojson/building.rb) (Line range showing hardcoded 4m depth and hole skipping).
    *   Zoning Heuristics: [`lib/urbanopt/geojson/zoning.rb`](https://github.com/urbanopt/urbanopt-geojson-gem/blob/develop/lib/urbanopt/geojson/zoning.rb) (Line range containing vertex offset logic).

---

## 3. Ladybug Tools: Dragonfly / Honeybee

### Auto-Zoning Algorithm
*   **Methodology:** Ladybug Tools utilizes the **Straight Skeleton** algorithm to subdivide floor plans.
*   **Zoning Logic:** The core geometry library (`ladybug-geometry-polyskel`, a fork of Ármin Scipiades's `polyskel` based on Felkel and Obdržálek's 1998 wavefront propagation model) shrinks the footprint inward. This wavefront propagation traces the paths of vertices moving inwards at a constant rate, resolving topology changes (e.g., splitting a narrowing polygon into multiple pieces) dynamically.

### Perimeter Depth
*   **Value:** Commonly defaulted to **4.57 meters (15 feet)**.
*   **Configurability:** Fully configurable via the `perimeter_offset` input parameter on Honeybee and Dragonfly components (e.g., `DF Room2D` or `HB Straight Skeleton`).

### Robustness & Failure Handling
*   **Degenerate Geometry Fallback:** The straight skeleton algorithm frequently fails on complex non-convex shapes, creating overlapping lines or infinite loops. To handle this:
    *   **Shallow Offset Fallback:** Ladybug Tools implements an alternate workflow for shallow offset depths. If the straight skeleton fails, it attempts a simple inward boundary offset of the outer curve, verifying that it does not self-intersect.
    *   **Graceful Degradation to Single Zone:** If the offset calculations fail or if `perimeter_offset` is set to `0`, Dragonfly falls back to creating a **single thermal zone per floor** (representing each story as a single `Room2D`). 
    *   **Error Handling:** In grasshopper-based workflows, if a geometry is too complex and both offset methods fail, the component throws a warning/error. Developers are advised to handle this in Python using `try...except` blocks to set `perimeter_offset = 0` (falling back to a single zone) to prevent script crashes.
*   **Holes/Courtyards:** The straight skeleton can fail when interior holes split core polygons (Issue #33 in `ladybug-geometry-polyskel`). The documented fallback is to simplify the footprint by removing minor interior holes before zoning.

### Pre-cleaning & Footprint Simplification
*   **Approach:** The library does not auto-simplify footprints by default. It relies on the user feeding clean polygons. However, it recommends pre-processing shapes in Rhino/Grasshopper (e.g., using vertex collapse tolerances, rebuilding curves, or selecting the largest part of a multi-polygon).

### Citations
*   **Paper:** Felkel, P., & Obdržálek, J. (1998). *Straight skeleton computation.* Proceedings of the Spring Conference on Computer Graphics (SCCG 98), Budmerice, Slovakia, 210-217.
*   **Code Reference:** `ladybug-tools/ladybug-geometry-polyskel` GitHub repository. [Link](https://github.com/ladybug-tools/ladybug-geometry-polyskel) (Access Date: June 19, 2026).
*   **SDK Reference:** `ladybug-tools/dragonfly-core` GitHub repository. [Link](https://github.com/ladybug-tools/dragonfly-core) (Access Date: June 19, 2026).

---

## 4. ORNL AutoBEM / AutoBEM2

### Auto-Zoning Algorithm
*   **Methodology:** By default, AutoBEM simplifies geometries to **one thermal zone per floor** (no core-perimeter split).
*   **Zoning Logic:** In massive national-scale simulation runs (e.g., the ORNL "Model America" dataset containing 124+ million buildings), geometry auto-zoning is bypassed for computational efficiency and to guarantee 100% execution robustness. Buildings are extruded from 2D footprints based on LiDAR heights, and each story is modeled as a single well-mixed thermal zone.

### Perimeter Depth
*   **Value:** Not applicable in default simulations.
*   **Configurability:** While researchers in ORNL’s orbit have tested core-perimeter partitioning experimentally using external packages (e.g., Geomeppy or OpenStudio Measures), the standard AutoBEM engine uses a single zone per floor.

### Robustness & Failure Handling
*   **Fallback Strategy:** Bypassing core-perimeter zoning acts as the ultimate robustness strategy. By avoiding geometric offsetting, the pipeline eliminates the risk of self-intersection, slivers, and twisted polygons. Highly awkward footprints (multi-part, narrow wings, courtyards) are extruded as-is, resulting in a single thermal zone per floor that matches the exact outer footprint shape.
*   **Courtyards:** Courtyards and interior holes are extruded as hollow voids inside the single-zone floor plates.

### Pre-cleaning & Footprint Simplification
*   **Approach:** AutoBEM performs extensive pre-cleaning of footprints extracted from satellite/GIS sources (OSM). This includes:
    *   Redundant vertex collapse (removing vertices within close tolerances, e.g., < 0.5 meters).
    *   Squaring of nearly perpendicular corners (regularization).
    *   Selection of the largest part for multi-polygon structures to ensure clean EnergyPlus execution.

### Citations
*   **Paper:** New, J., Adams, E., Im, P., Kukay, A., et al. (2018). *Automatic Building Energy Modeling (AutoBEM) - Simulation of 124 million US buildings.* Oak Ridge National Laboratory Technical Report. [URL](https://www.osti.gov/biblio/1479262) (Access Date: June 19, 2026).
*   **Paper:** Allen, M. C., New, J. R., & Adams, E. E. (2020). *Scale and Accuracy Trade-offs in Urban Building Energy Modeling.* Oak Ridge National Laboratory. [URL](https://www.osti.gov/biblio/1615674) (Access Date: June 19, 2026).

---

## 5. UMI (MIT) and the umi/archetype workflow

### Auto-Zoning Algorithm
*   **Methodology:** UMI uses the **"Autozoner"** and **"Shoeboxer"** algorithms (developed by Timur Dogan, Christoph Reinhart, and Panagiotis Michalatos) to automate thermal zoning.
*   **Zoning Logic:** The algorithm uses a wavefront propagation technique (straight skeleton) to shrink the footprint. 
*   **Convex Decomposition:** Because the raw output of the straight skeleton offset can result in concave polygons (which EnergyPlus cannot simulate correctly), the Autozoner applies a secondary **Convex Decomposition (CD)** step. This partitions the resulting perimeter and core spaces into strictly convex polygons (such as triangles and quadrilaterals) before generating the EnergyPlus zones.

### Perimeter Depth
*   **Value:** Configurable. It commonly defaults to **twice the floor-to-floor height** (e.g., ~6.0 to 9.0 meters) or a fixed depth of **4.57 meters (15 feet)**.
*   **Configurability:** Fully configurable inside Rhinoceros 3D UMI templates.

### Robustness & Failure Handling
*   **Sliver Zones & Sharp Angles:** To avoid the creation of tiny, razor-thin sliver zones, the algorithm uses distance and area thresholds (often set to half the perimeter depth). If an offset vertex falls within this threshold of an edge, the zone collapses.
*   **Triangle Zones:** The algorithm avoids creating "triangle zones" (perimeter zones with only one vertex on the exterior boundary) except when necessary to close the loop over the core.
*   **Fallback Behavior:** If the building footprint is too narrow to support a core zone (the offset shrinks the core to an area below a minimum threshold), the core is eliminated, and the remaining space is merged into a **single zone** representing the entire floor plate.

### Pre-cleaning & Footprint Simplification
*   **Approach:** UMI operates within the Rhinoceros CAD environment. It requires closed, planar curves. It performs vertex collapse and intersection cleanup, and uses the convex decomposition step to clean up awkward geometry before sending it to the simulation engine (Archsim/EnergyPlus).

### Citations
*   **Paper:** Dogan, T., Reinhart, C., & Michalatos, P. (2012). *Autozoner: An algorithm for automatic thermal zoning of buildings.* Proceedings of SimBuild 2012, Madison, Wisconsin. [URL](https://www.researchgate.net/publication/268484931_Autozoner_An_algorithm_for_automatic_thermal_zoning_of_buildings) (Access Date: June 19, 2026).
*   **Paper:** Dogan, T., & Reinhart, C. (2013). *Shoeboxer: An algorithm for abstracting complex building geometries into representative shoebox models.* Proceedings of BS2013: 13th Conference of International Building Performance Simulation Association, Chambery, France. [URL](https://www.researchgate.net/publication/268485124_Shoeboxer_An_algorithm_for_abstracting_complex_building_geometries_into_representative_shoebox_models) (Access Date: June 19, 2026).

---

## 6. TEASER (RWTH Aachen) and CityBES (LBNL)

### TEASER (RWTH Aachen)
*   **Auto-Zoning Algorithm:** TEASER does **not** perform geometric core-perimeter zoning. It utilizes archetype-based lumping to translate building envelopes into simplified reduced-order resistance-capacitance (RC) networks.
*   **Zoning Logic:** Depending on the desired complexity, TEASER lumps the envelope and interior partitions into a single-zone RC model (e.g., "OneElement" to "FourElement" configurations). Multi-zone layouts are assigned based on building usage type and predefined archetype ratios, rather than geometric footprint offsetting.
*   **Robustness / Fallback:** By lumping geometry, TEASER avoids geometric splitting crashes. Recent developments include the Multizone Assignment Algorithm (MZA) based on **Binary Space Partitioning (BSP)** to divide floors among diverse usage zones.
*   **Citations:** Remmen, P., Lauster, M., Balfour, M., Fuchs, M., et al. (2018). *TEASER: an open-source library for building data enrichment and Modelica simulation.* Journal of Building Performance Simulation, 11(2), 146-158. [DOI: 10.1080/19401493.2017.1328990](https://doi.org/10.1080/19401493.2017.1328990) (Access Date: June 19, 2026).

---

### CityBES (LBNL)
*   **Auto-Zoning Algorithm:** CityBES uses the **AutoZone** algorithm, which is a **pixel-based automatic zoning algorithm**.
*   **Zoning Logic:** Rather than manipulating vector boundaries (which are prone to precision issues, twisted nodes, and self-intersections), the algorithm:
    1. Rasterizes the building footprint into a grid of 2D pixels.
    2. Identifies interior pixels and colors them white.
    3. Offsets the perimeter pixels inward by a set distance, coloring the perimeter area dark gray.
    4. Designates the remaining central pixels as the core zone.
    5. Translates the pixel boundaries back into vector coordinates and simplifies the resulting polygon edges for EnergyPlus.

### Perimeter Depth
*   **Value:** **4.57 meters (15 feet)** or **5.0 meters**.
*   **Configurability:** Configurable in the CityBES pipeline settings.

### Robustness & Failure Handling
*   **Fallback Strategy:** The pixel-based approach is highly robust because raster operations do not fail on concave edges, slivers, or overlapping coordinates. If a building footprint is too narrow to have a core (no core pixels remain after the perimeter offset), the core collapses, and the algorithm **falls back to a single zone per floor** (equivalent to CityBES's "OneZone" method).
*   **Holes/Courtyards:** Courtyards are represented as empty pixel spaces. The algorithm offsets inward from both the exterior walls and the courtyard walls, creating perimeter zones along the inner courtyard edges.

### Pre-cleaning & Footprint Simplification
*   **Approach:** Footprint shapes are cleaned up during the rasterization process. Small geometric deviations, minor self-intersections, and redundant vertices are smoothed out when mapped to the pixel grid resolution.

### Citations
*   **Paper:** Chen, Y., Hong, T., & Piette, M. A. (2017). *Automatic zoning of building footprints for city-scale energy modeling.* Energy and Buildings, 149, 396-412. [DOI: 10.1016/j.enbuild.2017.05.056](https://doi.org/10.1016/j.enbuild.2017.05.056) (Access Date: June 19, 2026).

---

## 7. geomeppy & EnergyPlus features

### geomeppy
*   **Auto-Zoning Algorithm:** geomeppy implements a core-perimeter zoning workflow when adding a building block using `IDF.add_block(zoning="core/perim")`.
*   **Zoning Logic:** 
    1. **Core Generation:** It computes the core polygon by applying a negative buffer to the footprint via the Shapely library: `core = poly.buffer(distance=-perim_depth)`.
    2. **Perimeter Generation:** The function `get_perims(footprint, core)` in `geomeppy/geom/core_perim.py` loops through each outer footprint edge. For each edge, it finds the point on the core boundary closest to the edge's start vertex (`c1`) and the point closest to the edge's end vertex (`c2`). It then creates a perimeter zone quadrilateral with vertices `[c1, edge.p1, edge.p2, c2]`.

### Perimeter Depth
*   **Value:** Default is **3.0 meters**.
*   **Configurability:** Configurable via the `perim_depth` argument in `add_block`.

### Robustness & Failure Handling
*   **Slivers & Collapse Crash:** If a footprint is too narrow relative to the perimeter depth, the negative buffer returns an empty polygon. In this case, `len(core)` is 0. Inside `get_perims`, the Cartesian product `product([edge.p1] * len(core), core)` is empty. The `sorted` function receives an empty list, and calling `[0]` on it raises a hard **`IndexError: list index out of range`** crash.
*   **Fallback Behavior:** No graceful fallback is implemented. In `geomeppy/idf.py`, a `try...except` block catches `NotImplementedError` (raising `ValueError("Perimeter depth is too great")`). However, because the empty core raises an `IndexError`, the crash is **not caught** and propagates, crashing the execution.
*   **Concave & Courtyard Failures:** If the footprint is concave or contains holes, Shapely's negative buffer can return a `MultiPolygon` or a shape with holes. In these cases, the closest-point matching logic in `get_perims` maps vertices incorrectly, creating twisted, overlapping, or self-intersecting perimeter zones that crash EnergyPlus during simulation.

### Pre-cleaning & Footprint Simplification
*   **Approach:** geomeppy does not perform footprint cleaning, vertex reduction, or hole removal before attempting the core-perimeter offset.

### Citations
*   **Code Reference:** `jamiebull1/geomeppy` GitHub repository:
    *   Geometry Script: [`geomeppy/geom/core_perim.py`](https://github.com/jamiebull1/geomeppy/blob/master/geomeppy/geom/core_perim.py)
    *   IDF Entry: [`geomeppy/idf.py`](https://github.com/jamiebull1/geomeppy/blob/master/geomeppy/idf.py#L22) (Access Date: June 19, 2026).

---

### EnergyPlus Floorplan / Auto-Zoning
*   **Methodology:** EnergyPlus is a simulation engine and **does not perform auto-zoning**. It expects an IDF file where all thermal zones are already defined as 3D spaces.
*   **FloorspaceJS:** The web-based 2D editor for OpenStudio/EnergyPlus geometry does not contain a button or algorithm to auto-generate core-perimeter zones. Users must draw spaces manually, and then OpenStudio measures (like `create_bar...` or `urban_geometry...`) perform the automatic zoning post-processing.
*   **Citations:** OpenStudio Coalition (2020). *FloorspaceJS: A 2D Floor Plan Editor for Building Energy Modeling.* [URL](https://github.com/openstudiocoalition/floorspace.js) (Access Date: June 19, 2026).

---

## 8. OpenStudio Core Measures

### Auto-Zoning Algorithm
*   **Methodology:** OpenStudio uses the `create_bar_from_building_type_ratios` measure (in `openstudio-model-articulation-gem`) to generate core-perimeter models.
*   **Zoning Logic:** This measure **does not slice custom or arbitrary footprints**. Instead, it procedurally generates simple, clean rectangular bar shapes and splits them into perimeter and core zones.
*   **Double-Loaded Corridors:** It supports a custom zoning variant where a central circulation corridor is created down the center of the bar, replacing the standard core zone.

### Perimeter Depth
*   **Value:** Default is **4.57 meters (15 feet)**.
*   **Configurability:** Configurable via the measure's `perimeter_zone_depth` argument.

### Robustness & Failure Handling
*   **Fallback Strategy:** Because this measure operates strictly on procedurally generated rectangular geometry, it **never encounters degenerate shapes, concave polygons, sliver zones, or courtyards**.
*   **Custom Geometry:** If a modeler imports custom geometry, the OpenStudio SDK provides a lower-level C++ API method `Space.fromFloorPrint` to generate spaces, but it does not have a native, robust auto-zoning method for arbitrary shapes. Custom footprints must be zoned using external measures like URBANopt's `urban_geometry_creation_zoning`.

### Citations
*   **Code Reference:** `NREL/openstudio-model-articulation-gem` GitHub repository. [Link](https://github.com/NREL/openstudio-model-articulation-gem) (Access Date: June 19, 2026).

---

## 9. Synthesis

### Comparison Table

| Tool | Zoning Method | Perimeter Depth | Degenerate-Shape Fallback | Pre-clean / Simplify | Source Code / Reference |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **City Energy Analyst (CEA)** | None (Single Zone per Floor) | N/A | N/A (No offset performed) | None (Relies on GIS pre-cleaning) | Fonseca et al. (2016); `CityEnergyAnalyst` GitHub |
| **URBANopt + openstudio-standards** | Fixed-depth vertex offset bisector | 4.0 m (Hardcoded) | Falls back to single zone on collapsed core; **crashes** on self-intersection | None (Ignores GeoJSON holes/courtyards) | `urbanopt-geojson-gem` GitHub |
| **Ladybug Tools (Dragonfly/Honeybee)** | Straight Skeleton | Configurable (Default 4.57 m) | Falls back to simple inward offset; then to single zone per floor | None (Recommends manual hole removal) | `ladybug-geometry-polyskel` GitHub; Felkel & Obdržálek (1998) |
| **ORNL AutoBEM** | None (Single Zone per Floor) | N/A | N/A (No offset performed) | Vertex collapse, corner squaring, largest-part selection | New et al. (2018); Allen et al. (2020) |
| **UMI (MIT)** | Straight Skeleton + Convex Decomposition | Configurable (Default 4.57 m) | Core collapses to single zone; sliver zones merged | Vertex collapse and cleanup in Rhino | Dogan et al. (2012); Dogan & Reinhart (2013) |
| **TEASER (RWTH)** | None (Archetype lumping) | N/A | N/A (No offset performed) | Archetype mapping, BSP for multizone | Remmen et al. (2018); `TEASER` GitHub |
| **CityBES (LBNL)** | Pixel-based Rasterization (AutoZone) | Configurable (Default 4.57 m) | Core collapses to single zone per floor (OneZone) | Grid-based smoothing during rasterization | Chen et al. (2017) |
| **geomeppy** | Shapely negative buffer + closest edge-point mapping | Configurable (Default 3.0 m) | **Crashes** (IndexError) on narrow shapes; creates invalid overlapping zones on concave shapes | None | `geomeppy/geom/core_perim.py` GitHub |
| **OpenStudio Core Measures** | Procedural Rectangular Bar Generator | Configurable (Default 4.57 m) | N/A (Procedural geometry is always rectangular) | N/A | `openstudio-model-articulation-gem` GitHub |

---

### Industry-Accepted Fallback Practices

The most common fallback strategy across Urban Building Energy Modeling (UBEM) tools is **graceful degradation to a single-zone-per-floor (or one-zone-per-storey) model**. 

Treating the entire floor footprint as a single well-mixed thermal zone when core-perimeter zoning fails is an **accepted, widely documented, and industry-standard practice** in the field. 
*   **Validation:** Both ORNL's **AutoBEM** and LBNL's **CityBES** (via its "OneZone" method) rely heavily on single-zone-per-floor representations for district-scale modeling. 
*   **Scientific Consensus:** Peer-reviewed literature (e.g., Allen et al., 2020; Chen et al., 2017) establishes that while single-zone models can introduce minor EUI deviations (typically within $\pm 5-10\%$ for annual EUI and $\pm 15\%$ for peak HVAC sizing) compared to core-perimeter models, they provide a highly robust, non-crashing baseline. This trade-off is widely accepted in UBEM because it guarantees simulation completion across large, unclean city datasets where vector offsetting algorithms fail.

---

### Robust Perimeter-Offset Algorithms

Two tools stand out for using advanced algorithms specifically designed to handle complex geometries and avoid self-intersections or sliver zones:

1.  **Ladybug Tools (Dragonfly/Honeybee) & UMI (MIT):** These tools use the **Straight Skeleton** algorithm (implemented in the Python library `ladybug-geometry-polyskel` and UMI's `Autozoner`). Because the straight skeleton dynamically models the shrinking of a polygon (wavefront propagation), it naturally splits narrowing wings, handles acute angles, and divides complex non-convex floor plates without self-intersecting boundaries. UMI further improves robustness by applying **Convex Decomposition** to ensure the resulting zones are strictly convex and simulation-safe for EnergyPlus.
2.  **CityBES (LBNL):** CityBES uses the **pixel-based AutoZone algorithm** (Chen et al., 2017). By converting the vector footprint into a discrete raster grid, applying offset operations in pixel space, and then converting back to vectors, the algorithm completely bypasses the topological precision issues, twisted nodes, and intersecting edges that plague vector-based offset libraries (like Shapely or custom bisector offsets). If the core is too narrow, the core pixels simply disappear, resulting in a clean, single-zone fallback.
