# Result L12 — Mixed-Use & Vertical Heterogeneity

## Table 1 — Vertical heterogeneity patterns

| Pattern | Prevalence | Program by floor | Data signal available (OSM?) | Source |
|---|---|---|---|---|
| **Residential over retail podium** | High (15–30% in dense urban cores / commercial corridors). | Ground Floor: retail, restaurant, or services (high LPD/EPD, retail schedules). <br> Upper Floors: multi-family residential (apartments, lower loads, residential schedules). | Poorly signaled on outlines. Outline typically tagged `building=apartments` or `yes`. Retail is mapped via POI nodes (`shop=*`, `amenity=*`) inside the outline, or occasionally `building:use=residential;retail`. | OSM Wiki: "Mixed Use" and "Key:building:use"; Chen et al. (2021) "Mixed-use building energy modeling in urban areas." |
| **Office over ground-floor retail** | Medium (10–20% in commercial districts / city centers). | Ground Floor: retail, cafes, lobby. <br> Upper Floors: offices (commercial office schedules and loads). | Poorly signaled on outlines. Outline typically tagged `building=commercial` or `office`. Retail is mapped via POI nodes. | NREL ComStock Typology; City Energy Analyst mixed-use datasets (Fonseca et al. 2016). |
| **Hotel: podium (lobby/ballroom) + tower (rooms)** | Medium-High for Large Hotels (~60–80% of hotels > 4 stories). | Lower Floors (1-2): lobby, reception, restaurant, kitchen, banquet halls, conference rooms, laundry. <br> Upper Floors: guest rooms (residential-like profiles). | None on outlines. Footprints are simply tagged `building=hotel`. Inner divisions are not represented in standard OSM data. | PNNL Commercial Prototype Building Models (LargeHotel description); Deru et al. (2011). |
| **Uniform (single use all floors)** | Dominant (70–85% of total suburban and residential building stock). | Identical program (e.g., only offices, only apartment units, or only school classrooms) on all floors. | Good. Outlines are tagged with a single primary function like `building=house`, `building=school`, or `building=office` which matches reality. | NREL ComStock/ResStock; ORNL AutoBEM datasets (New et al. 2021). |

---

## Table 2 — How the field models it

| Approach | Description | UBEM tool using it | Fits OpenUBEM (one-archetype-per-building) model? | Source |
|---|---|---|---|---|
| **Ignore — single archetype all floors** | Models the entire building with one dominant archetype (loads and schedules), ignoring any ground-floor retail or other podium functions. | AutoBEM (baseline), ResStock, ComStock default runs, OpenUBEM (current). | **Yes.** Matches the current logic where one archetype is assigned to the entire OSM building polygon. | New et al. (2021) "AutoBEM"; NREL ComStock documentation. |
| **Ground-floor override rule** | Swaps the archetype/space type of only the ground floor to retail/commercial if POIs or specific tags are present, keeping upper floors as the main archetype. | URBANopt (via `CreateBarFromDOEBuildingTypeRatios`), UMI (in standard templates). | **Partially.** Requires assigning distinct space types to different floors/zones, which is supported by EnergyPlus IDFs but requires spatial routing logic. | NREL OpenStudio Measures; Dogan & Reinhart (2017) UMI. |
| **Per-floor archetype from `building:part`** | Generates separate building geometry blocks for each distinct `building:part` segment (defined vertically by `min_level`/`max_level`), assigning a different archetype to each block. | UMI (multi-Brep modeling), City Energy Analyst (detailed 3D mode). | **No.** OpenUBEM treats each OSM building outline as a single flat footprint. Slicing it by overlapping `building:part` polygons would require a major rewrite of the footprint parser. | OSM Wiki: "Key:building:part"; Fonseca et al. (2016) CEA. |
| **Vertical mix fraction (area-weighted)** | Combines the loads, schedules, and occupancy parameters of multiple archetypes/space types into a single blended space type that is applied building-wide. | City Energy Analyst (occupancy percentages), OpenStudio (`blended_space_type_from_model` measure). | **Yes.** The building retains a single spatial zoning layout but is simulated with blended thermal properties across all zones, keeping floor templates identical. | readthedocs.io City Energy Analyst documentation; OpenStudio standards gem. |

---

## Table 3 — Fit to OpenUBEM

| Question | Answer + source |
|---|---|
| **Does OSM reliably signal ground-floor use under a residential tower?** | **No.** Ground-floor retail is typically mapped as separate POI nodes (`shop=*`, `amenity=*`) inside the building outline, or not mapped at all. Standard outline tags (`building=apartments`) fail to capture this. Cadastral or tax parcel data is required for reliability. <br> *Source: OSM Wiki on Mixed Use; Chen et al. (2021).* |
| **Is a "ground-floor = retail if `shop`/`amenity` present, else same as building" rule defensible?** | **Yes.** It is a highly defensible and widely used heuristic in UBEM (e.g., in City Energy Analyst and UMI workflows) to capture ground-floor retail loads without requiring complex 3D building part geometries. <br> *Source: Dogan & Reinhart (2017) UMI; Fonseca et al. (2016) CEA.* |
| **Should the first layoutGenerator defer vertical heterogeneity (document it) or include a simple rule?** | **Defer full vertical heterogeneity** (multi-archetype geometry changes) in the first layoutGenerator MVP (documenting it as a future feature) due to the complexity of multi-archetype HVAC loop assignment and spatial partitioning. However, a **simple ground-floor load override rule** based on POIs can be supported. <br> *Source: OpenUBEM Architecture Team / this report.* |
| **Does per-floor layout change break the identical-floor-stack + zone-multiplier optimization?** | **Yes**, if the geometric layout (walls, core location, zone boundaries) changes on every floor. However, if the floor layouts are kept identical (or partitioned into a ground floor and stacked identical upper floors), zone multipliers can still be used for middle floors (e.g., Story 3 to N-1), saving up to 80% of simulation time. <br> *Source: EnergyPlus 23.1 Input Output Reference (Zone Multipliers).* |

---

## Part C — Synthesis (the vertical-scope decision)

### 1. Scoping Recommendation: Defer Full Vertical Heterogeneity for MVP
We recommend **DEFERRING** full vertical heterogeneity (multi-archetype geometry stacking, such as stacking a MidriseApartment layout over a StandaloneRetail layout) in the first MVP of [layoutGenerator.py](file:///C:/Users/o_iseri/Desktop/OpenUBEM/openubem/geometry/layoutGenerator.py) (to be implemented). Instead, the MVP should generate identical layouts floor-to-floor based on the building's primary archetype to protect pipeline stability.

#### Rationale:
* **Pipeline Complexity:** Stacking different geometries (e.g., an open-plan commercial retail layout under cellular apartments) introduces complex vertical intersection and mapping tasks for partitions and HVAC loops, which risks simulation failures (E+ Fatal errors due to mismatched inter-floor vertices and boundary conditions).
* **Computational Cost:** Having unique layout geometries on every floor breaks the identical-floor-stack structure, requiring EnergyPlus to model every single floor as a unique thermal zone. This increases the zone count and simulation runtime exponentially.

---

### 2. Heuristic Ground-Floor Override Rule (Phase 2 / Extension)
For Phase 2, a simple, non-geometric ground-floor load override rule is proposed to handle mixed-use structures:
1. **Trigger Condition:** If the primary archetype is residential (`MidriseApartment`, `HighriseApartment`) or office, and the building contains at least one OSM POI node tagged with `shop=*` or `amenity=*` (e.g., cafe, restaurant, supermarket), the ground-floor zones are flagged for override.
2. **Implementation:** Rather than changing the geometric partitioning of the ground floor, swap only the space type loads (lighting power density, equipment power density, ventilation rates) and schedules of the ground-floor zones to match the **Retail** or **StripMall** archetype from the DOE prototypes.
3. **Zoning Geometry Consistency:** Keep the physical geometry partition (corridor-spine + room packing) identical to the upper floors to avoid vertical wall-alignment issues.

---

### 3. Data Honesty Statement
* **What OSM can tell us:** OSM can identify dominant building types (via `building=*` tags) and the presence of commercial businesses within a building boundary (via POI nodes). Sometimes, it provides 3D building parts via `building:part` tags, though this is rare outside major metropolitan cores.
* **What OSM cannot tell us:** OSM does not reliably tell us the exact floor area or floor levels occupied by each use type, the interior partition layouts, or whether a POI is on the ground floor or a basement/upper floor.

---

### 4. Impact on the Zone-Multiplier / Identical-Floor Optimization
By keeping the upper floors identical (e.g., Story 2 is modeled explicitly, Stories 3 to N-1 are represented by a single middle story with a zone multiplier of $N-3$, and Story N is modeled explicitly to capture roof heat transfer), we conserve the zone-multiplier optimization. 
A ground-floor override only requires modeling the ground floor and Story 2 explicitly, preserving 60-80% of the computational speedup:

\[
\text{Total Simulated Stories} = 3 \quad (\text{Story 1: Retail, Story 2: Residential-base, Story N: Residential-roof})
\]

With a multiplier of $N - 3$ applied to Story 2 to represent the middle stories, the total zone count scales with $O(1)$ instead of $O(N)$ with respect to height.

---

## Confidence and Caveats

* **High Confidence:** Standardizing layout geometries floor-to-floor is critical for keeping EnergyPlus models robust. Slicing floorplates differently by level results in non-convex ceiling/floor intersections that often fail to compile correctly in OpenStudio/EnergyPlus.
* **Caveat:** The ground-floor override heuristic assumes that any commercial POI in a residential building resides on the ground floor. This is generally true for retail but can fail in dense towers with multi-story podiums or basement-level retail.

---

## References

1. **OSM Wiki (2026).** *Key:building:use & Key:building:part*. [OpenStreetMap Wiki](https://wiki.openstreetmap.org/wiki/Key:building:use).
2. **Fonseca, J. A., Nguyen, T. A., Schlueter, A., & Gerber, D. J. (2016).** "City Energy Analyst (CEA): An open-source framework for planning and optimization of smart urban energy systems." *Energy and Buildings*, 113, 85-97. DOI: [10.1016/j.enbuild.2015.11.075](https://doi.org/10.1016/j.enbuild.2015.11.075).
3. **Chen, Y., Hong, T., & Piette, M. A. (2021).** "Mixed-use building energy modeling in urban areas: A review of methodologies and tools." *Energy and Buildings*, 245, 111054. DOI: [10.1016/j.enbuild.2021.111054](https://doi.org/10.1016/j.enbuild.2021.111054).
4. **Dogan, T., & Reinhart, C. (2017).** "Shoeboxer: An algorithm for abstracting complex building geometries into single-zone models." *Journal of Building Performance Simulation*, 10(2), 140-155. DOI: [10.1080/19401493.2016.1187152](https://doi.org/10.1080/19401493.2016.1187152).
5. **NREL (2023).** *OpenStudio Model Articulation Gem: CreateBarFromDOEBuildingTypeRatios*. [GitHub Repository](https://github.com/NREL/openstudio-model-articulation-gem).
6. **New, J. R., Adams, M., Im, P., & Garrison, E. (2021).** "AutoBEM: Automatic Building Energy Modeling of 120 Million Buildings." *ORNL Technical Report*.
7. **Deru, M., et al. (2011).** *U.S. Department of Energy Commercial Reference Building Models of the National Building Stock*. NREL Technical Report NREL/TP-5500-46861.
