# RESULT_L11 — LOAD/SCHEDULE CONSERVATION & INTERIOR SURFACES

This report establishes the physical-correctness rules and surface boundary-condition conventions for the OpenUBEM `layoutGenerator.py` module. Refining a building's thermal zones from a single zone to $N$ zones must not change its total conditioned floor area, occupancy, ventilation rates, or internal loads. Furthermore, the newly created interior partitions and inter-zone surfaces must be assigned physically realistic boundary conditions that prevent artificial heat flow while avoiding EnergyPlus simulation crashes (specifically the courtyard/donut core fatal).

---

## 1. REQUIRED OUTPUT TABLES

### Table 1 — Conservation invariants (what must be preserved across resolutions)

| Quantity | Invariant across single/floor/zone resolution | How to enforce in E+ | Source |
|---|---|---|---|
| **Conditioned floor area (EUI denominator)** | $= \text{footprint\_area\_m2} \times \text{num\_floors}$ | Ensure the sum of the floor areas of all conditioned zones equals the building's total conditioned floor area. In E+, the floor area of a zone is determined by its horizontal geometry (`Floor` surface area). So the sum of the horizontal floor surfaces of all conditioned zones must equal the footprint area. | EnergyPlus Input-Output Reference (v23.1) & OpenUBEM zoning guidelines |
| **Total lighting power (LPD × area)** | $= A_{\text{tot}} \sum_t f_t \text{LPD}_t$ where $f_t$ is the prototype space type area fraction. | Specify `Lights` objects using absolute `Design Level` (Watts) per zone, distributed from the building total proportional to zone floor area ($P_{\text{lights, z}} = P_{\text{lights, tot}} \times \frac{A_z}{A_{\text{tot}}}$ or per space type). Alternatively, scale the `Watts/Area` input by a normalization factor $\alpha = \frac{\sum f_t \text{LPD}_t}{\sum (A_z/A_{\text{tot}}) \text{LPD}_z}$. | EnergyPlus Input-Output Reference (`Lights` object, `Design Level` or `Watts per Zone Floor Area`), PNNL Prototype Building Models. |
| **Total equipment power (EPD × area)** | $= A_{\text{tot}} \sum_t f_t \text{EPD}_t$ | Specify `ElectricEquipment` objects using absolute `Design Level` (Watts) per zone, or normalize `Watts/Area` by a scaling factor. Assign whole-building absolute loads (elevators, IT, domestic hot water pump losses) to exactly one designated zone (e.g. first-floor core). | EnergyPlus Input-Output Reference (`ElectricEquipment` object), PNNL Prototype Building Models. |
| **Total occupancy (ppl/area × area)** | $= A_{\text{tot}} \sum_t f_t \text{Density}_t$ | Specify `People` objects using absolute `Number of People` per zone (distributed from the building total proportional to zone floor area), or normalize `People per Floor Area` by a scaling factor. | EnergyPlus Input-Output Reference (`People` object), PNNL Prototype Building Models. |
| **Total outdoor-air / ventilation** | $= V_{\text{oa, tot}} = \sum_t (N_{\text{people, t}} \cdot R_p + A_t \cdot R_a)$ where $R_p$ is flow/person and $R_a$ is flow/area. | For zonal systems, specify `DesignSpecification:OutdoorAir` using the `Flow/Zone` method with the conserved rate per zone distributed by area. For central multi-zone systems (VAV), use `System Outdoor Air Method` = `VentilationRateProcedure` in `Sizing:System` to calculate system outdoor air intake accounting for zone ventilation efficiency. | EnergyPlus Input-Output Reference (`DesignSpecification:OutdoorAir`), ASHRAE Standard 62.1-2019 Section 6.2. |
| **Total exterior envelope area** | = Geometrically constant exterior wall, roof, and ground floor area. | Set boundary condition of all actual exterior surfaces to `Outdoors` (or `Ground` for bottom floor) using `BuildingSurface:Detailed`. Do not use `Adiabatic` on any true exterior surfaces. | EnergyPlus Input-Output Reference (`BuildingSurface:Detailed` outside boundary condition). |
| **Schedules (fractions unchanged per space type)** | = Uniform hourly fractional profiles per space type across all zones. | Apply the identical PNNL/DOE archetype fractional schedules (lighting, equipment, occupancy, HVAC setpoints) to the respective zone loads. | PNNL Prototype Building Models, ASHRAE 90.1 Appendix G. |

---

### Table 2 — Distributing DOE loads to generated zones

| Approach | How loads are apportioned | Conserves totals? | Fits zero-fitted-parameters? | Source |
|---|---|---|---|---|
| **Per-zone-floor-area × space-type intensity** | Assign the raw prototype intensity (e.g., LPD, EPD, occupancy density) directly to each zone based on its assigned space type: $L_z = A_z \times I_{t(z)}$. | **No**. If the generated zone area fractions differ from the prototype fractions, total building loads will drift (e.g. if corridor fraction increases, building-wide average intensity shifts). | **Yes**, uses standard space-type values directly without adjustment. | Standard BEM zoning tools (e.g. basic OpenStudio/Dragonfly workflows). |
| **Space-type-weighted (corridor vs. unit intensities)** | Scale the space-type intensities by a building-wide normalization factor $\alpha = \frac{\sum_t f_t I_t}{\sum_z (A_z / A_{\text{tot}}) I_{t(z)}}$ so that $I'_z = \alpha I_{t(z)}$, or distribute absolute prototype totals to zones proportional to area. | **Yes**. Mathematically guarantees that $\sum_z A_z I'_z = A_{\text{tot}} \sum_t f_t I_t$. | **Yes**, it is a deterministic physical constraint. | OpenUBEM custom load builder / conservation-first workflows (Cerezo Davila 2017). |
| **E+ `Space`/`SpaceType` objects (native)** | Define native E+ `SpaceType` objects with prototype load densities, associate them with zones via E+ `Space` objects, and let E+ aggregate loads. | **No** (unless intensities are scaled). If space type area fractions in the generated geometry differ from the prototype, the aggregated building-level loads will drift. | **Yes**, uses native EnergyPlus schema features. | EnergyPlus Input/Output Reference (v9.6+), Space and SpaceType objects. |
| **Zone-multiplier for repeated units** | Model a single representative zone (e.g., a single dwelling unit) and apply a multiplier $M$ to scale its geometry and loads in E+. | **Yes**, within the multiplied zones, but does not capture shape-specific solar or neighbor shading variations of individual units. | **Yes**, if multiplier matches the geometry. | EnergyPlus Input/Output Reference, `Zone` multiplier field. |

---

### Table 3 — Interior / inter-zone surface treatment

| Surface | Boundary condition to use | Rationale | E+ object | Source |
|---|---|---|---|---|
| **Interior partition between two conditioned zones (same temp)** | `Adiabatic` | If setpoints and schedules are identical, $\Delta T \approx 0$, making `Adiabatic` a valid simplification that reduces zone coupling complexity and runtime. | `BuildingSurface:Detailed` with `Outside Boundary Condition` = `Adiabatic` | EnergyPlus Input-Output Reference, Cerezo Davila (2017) |
| **Corridor ↔ unit wall** | `Surface` (coupled) | Corridors have different setpoints, internal loads, and schedules than dwelling units, creating a persistent temperature gradient. | `BuildingSurface:Detailed` with `Outside Boundary Condition` = `Surface` and matched pairs | PNNL Prototype Models (e.g., `MidriseApartment`), ASHRAE 90.1 Appendix G |
| **Floor/ceiling between stacked floors** | `Surface` (coupled) where matched; fallback to `Adiabatic` | Matched floors are coupled to capture vertical heat transfer (critical for top/bottom storey gradients). Fallback to `Adiabatic` is required if footprints mismatch or matching fails to ensure simulation robustness. | `BuildingSurface:Detailed` with `Outside Boundary Condition` = `Surface` / `Adiabatic` | OpenUBEM `_pair_interfloor_surfaces`, Cerezo Davila (2017) |
| **Perimeter ↔ core wall** | `Surface` (coupled) | Perimeter zones experience solar gains and conduction through exterior walls, while core zones are dominated by internal gains, creating significant temperature differences. | `BuildingSurface:Detailed` with `Outside Boundary Condition` = `Surface` and matched pairs | PNNL Prototype Models (e.g., `MediumOffice`), ASHRAE 90.1 Appendix G |
| **Courtyard inner wall (exterior, faces court)** | `Outdoors` | Exposes the wall to outdoor temperatures, wind, and solar radiation, while allowing self-shading by adjacent building wings. | `BuildingSurface:Detailed` with `Outside Boundary Condition` = `Outdoors` | EnergyPlus Input-Output Reference, geomeppy documentation |

---

### Table 4 — Robustness: avoiding the E+ fatal

| Failure | Cause | Fix | Source |
|---|---|---|---|
| **Donut/courtyard core → mismatched inter-floor vertices (OpenUBEM current)** | geomeppy's `add_block` extrudes the donut core as a single zone with an interior ring. EnergyPlus doesn't support floors/ceilings with holes. Stacked floors produce mismatched vertex counts in coordinate order, causing `intersect_match` or `_pair_interfloor_surfaces` to fail. | Decompose the holed/donut footprint into simple, hole-free sub-polygons (e.g., slicing the O-shape into four bar-shaped wings) *prior* to zoning. Extrude and zone each wing separately, then pair floors/ceilings of stacked simple polygons. | OpenUBEM current issue (`zoning.py:87`), computational geometry polygon decomposition (Aichholzer & Aurenhammer 1996) |
| **Interior surfaces not matched between zones** | Small alignment offsets or cyclic vertex permutations prevent geomeppy's `match_idf_surfaces` from finding interzone pairs, leaving walls exposed to outdoors. | Use a vertex-set matching helper (like `_pair_interfloor_surfaces` using `frozenset` of vertices) to pair coplanar ceiling/floor surfaces regardless of cyclic vertex ordering. | OpenUBEM `surfaces.py:60` implementation, geomeppy `intersect_match` limitations |
| **Zone with < min area / degenerate geometry** | Buffering narrow footprints produces extremely small or degenerate polygons (e.g., buffer depth $d$ exceeds footprint width). | Implement a hard threshold gate: if `core_poly.is_empty or core_poly.area < 10.0 m²`, reroute the building to `one_zone_per_floor` and log a provenance warning. | OpenUBEM `zoning.py:79` narrow-building check, Cerezo Davila (2017) |
| **Load double-counting at corridor/core boundary** | Absolute building-level loads (elevators, IT equipment, domestic hot water pumps) are blindly replicated across all split zones. | Explicitly filter zones during load assignment; assign absolute whole-building loads to exactly one designated central zone (e.g., first-floor core). | PNNL Prototype Models, RESULT_08 load conservation rules |

---

## 2. PART C — SYNTHESIS (THE CONSERVATION + SURFACES SPEC)

### 1. Conservation Invariant List and EnergyPlus Mechanisms

To ensure that spatial refinement is a faithful representation rather than a different building, `layoutGenerator.py` must enforce the following invariants:

1.  **Conditioned Floor Area Conservation**:
    *   **Invariant**: $\sum A_{z,\text{conditioned}} = A_{\text{footprint}} \times N_{\text{floors}}$.
    *   **E+ Mechanism**: Evaluated by the floor area fields in `Zone` objects. Geometry generation must ensure no overlapping polygons or gaps between zones.
2.  **Internal Gains Conservation**:
    *   **Invariant**: The sum of the peak lighting, equipment, and occupant loads across all generated zones must equal the whole-building totals defined in the prototype.
    *   **E+ Mechanism**: Specified via the `Design Level` (total Watts or Number of People) fields in `Lights`, `ElectricEquipment`, and `People` objects. By using absolute levels distributed from the building total, we bypass the area-shift drift.
3.  **Ventilation Conservation**:
    *   **Invariant**: $\sum V_{\text{oa, z}} = V_{\text{oa, building}}$.
    *   **E+ Mechanism**: Specified using the `Flow/Zone` method within `DesignSpecification:OutdoorAir` objects.
4.  **Schedule Integrity**:
    *   **Invariant**: Hourly load fractions (lighting, plug loads, occupancy) must match the archetype profiles.
    *   **E+ Mechanism**: Assigning the exact prototype `Schedule:Compact` or `Schedule:Year` names to the load objects in the generated zones.

### 2. Recommended Load-Distribution Method

To prevent load drift while maintaining zero-fitted-parameters, OpenUBEM must implement **Space-Type-Weighted Normalization**:

Let:
*   $A_{\text{tot}}$ be the total building floor area (conditioned).
*   $f_t$ be the area fraction of space type $t$ in the prototype building.
*   $I_t$ be the prototype load intensity (e.g., LPD in $\text{W/m}^2$, occupancy in $\text{people/m}^2$).
*   $Z_t$ be the set of generated zones assigned to space type $t$.
*   $A_{t,\text{gen}} = \sum_{z \in Z_t} A_z$ be the total area of generated zones of type $t$.

The total prototype load $P_t$ for space type $t$ is calculated as:
$$P_t = A_{\text{tot}} \times f_t \times I_t$$

We distribute this total load $P_t$ among the generated zones $z \in Z_t$ proportional to their floor area:
$$P_{z,\text{conserved}} = P_t \times \frac{A_z}{A_{t,\text{gen}}} = \left(A_{\text{tot}} \cdot f_t \cdot I_t\right) \times \frac{A_z}{\sum_{z' \in Z_t} A_{z'}}$$

We can express this as an effective zone-level intensity $I'_z$:
$$I'_z = I_t \times \left(\frac{f_t A_{\text{tot}}}{\sum_{z' \in Z_t} A_{z'}}\right)$$

#### Proof of Total Load Conservation:
$$\sum_z P_{z,\text{conserved}} = \sum_t \sum_{z \in Z_t} P_{z,\text{conserved}} = \sum_t \sum_{z \in Z_t} P_t \frac{A_z}{A_{t,\text{gen}}} = \sum_t P_t \frac{\sum_{z \in Z_t} A_z}{A_{t,\text{gen}}} = \sum_t P_t = \sum_t A_{\text{tot}} f_t I_t = P_{\text{tot, coarse}}$$

This method mathematically guarantees that the sum of the zone-level loads equals the whole-building prototype total, even if the generated layout's space fractions differ from the prototype.

### 3. Interior-Surface Boundary-Condition Logic

*   **Corridor ↔ Unit and Core ↔ Perimeter Walls**: These must be modeled as conductively coupled `Surface` pairs. The temperature differences between zones due to solar exposure (perimeter) and high internal loads (core) drive significant lateral heat transfer that must be captured.
*   **Unit ↔ Unit and Office ↔ Office Partitions**: These should be modeled as `Adiabatic`. Since adjacent units have identical setpoints, schedules, and load profiles, the temperature gradient $\Delta T \approx 0$. Using `Adiabatic` reduces the number of surfaces in the model, speeding up the O(N^2) surface matching and coordinate-tracking phase.
*   **Inter-floor Slabs (Ceiling/Floor)**:
    *   *If floor plates match exactly*: Model as conductively coupled `Surface` pairs using the `_pair_interfloor_surfaces` helper to capture vertical heat transfer.
    *   *If floor plates mismatch (setbacks, cantilevers)*: Fall back to `Adiabatic` for those specific mismatched surfaces to prevent geometric intersection failures.
*   **Courtyard Inner Walls**: Must be modeled as `Outdoors` with `BuildingSurface:Detailed`. These are true exterior walls that exchange heat with outdoor air and receive solar radiation, shaded by the surrounding wings of the building.

### 4. Robustness Recipe

1.  **Courtyard/Donut Geometric Decomposition**:
    *   *Step 1*: Check if the building footprint polygon contains interior rings (`len(list(footprint_poly.interiors)) > 0`).
    *   *Step 2*: If true, decompose the holed polygon into a set of simple, hole-free sub-polygons (wings) using **rectangular or convex decomposition** (e.g., trapezoidal decomposition).
    *   *Step 3*: Route each simple wing to the layout generator independently. The layout generator slices each wing into corridor and perimeter zones, and extrudes them as simple, hole-free blocks.
    *   *Step 4*: Run `_pair_interfloor_surfaces` on the stacked simple polygons. Because none of the zones contain holes, the coordinate sequences match, preventing EnergyPlus geometry pairing crashes.
2.  **Narrow Footprint Guard**:
    *   If the inward buffer of a wing or footprint results in an empty core or `core_poly.area < 10.0 m²`, automatically fall back to `one_zone_per_floor` for that wing or building, and flag the fallback in the simulation log.
3.  **Load Double-Counting Filter**:
    *   Ensure that absolute building-level loads (such as elevators, central IT, hot water standby losses) are assigned to exactly one designated central zone (e.g. `osm_id_F1_core`). The load assignment loop must filter out other zones to prevent scaling these absolute loads by $N$ zones.

---

## 3. REFERENCES AND SOURCE CITATIONS

1.  **EnergyPlus™ Version 23.1.0.** *Input Output Reference* and *Engineering Reference*. U.S. Department of Energy. [https://energyplus.net/documentation](https://energyplus.net/documentation).
    *   Detailed specifications for `Zone`, `Lights`, `ElectricEquipment`, `People`, and `DesignSpecification:OutdoorAir` objects.
2.  **Cerezo Davila, C.** (2017). *Urban Building Energy Modeling: Workflows and Algorithms for Energy Efficient Cities*. PhD Thesis, Massachusetts Institute of Technology. [https://dspace.mit.edu/handle/1721.1/111956](https://dspace.mit.edu/handle/1721.1/111956).
    *   Development and validation of the AutoZone algorithm, including load-conservation formulations and adiabatic interior wall assumptions.
3.  **ASHRAE Standard 62.1-2019.** *Ventilation for Acceptable Indoor Air Quality*. Atlanta, GA: ASHRAE.
    *   Section 6.2: Ventilation Rate Procedure and system ventilation efficiency equations for multiple-zone systems.
4.  **ASHRAE Standard 90.1-2019.** *Energy Standard for Buildings Except Low-Rise Residential Buildings*. Atlanta, GA: ASHRAE.
    *   Appendix G: Performance Rating Method, specifying HVAC autosizing factors, fan power configurations, and baseline schedules.
5.  **Aichholzer, O., & Aurenhammer, F.** (1996). *Straight Skeletons for General Polygonal Shapes*. In Proc. 2nd Ann. Int. Conf. on Computing and Combinatorics (COCOON '96).
    *   Mathematical foundation for straight skeleton and polygon decomposition primitives used to resolve holed and non-convex footprints.

---

## 4. CONFIDENCE AND CAVEATS

### The Least Settled Surface-Treatment Choice: Inter-Floor Slabs
The most debated surface-treatment choice in UBEM zoning literature is the handling of **inter-floor slabs (ceilings/floors)**.

*   **The Debate**: Some research (e.g., Cerezo Davila 2017) advocates for modeling all inter-floor surfaces as `Adiabatic`. Because stacked storeys typically have similar setpoints and schedules, vertical heat transfer is small. Setting them to `Adiabatic` eliminates the O(N^2) vertex-matching bottleneck and prevents coordinate-mismatch fatals.
*   **The Catch**: However, vertical heat transfer is not zero. The top floor loses heat through the roof, and the ground floor loses heat to the ground. An adiabatic inter-floor slab isolates the middle floors, preventing vertical thermal coupling and distorting the building's thermal gradient (which is critical in multi-storey buildings).
*   **The Compromise**: OpenUBEM should employ a hybrid strategy. If the footprint plates match exactly, use `Surface` (fully coupled) via `_pair_interfloor_surfaces` to preserve vertical conduction. If the floor plates mismatch (setbacks, cantilevers) or matching fails, fall back to `Adiabatic` for those specific surfaces to ensure simulation robustness.
