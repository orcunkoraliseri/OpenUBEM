# RESULT — ASHRAE 90.1 APP-G CORE/PERIMETER ZONING & ITS GENERALIZATION TO NON-RECTANGULAR FOOTPRINTS

*Prompt file: `L03_ashrae_appG_core_perimeter_generalization_prompt.md`. OpenUBEM layout-generator deep-research sub-set. 2026-07-02.*

---

## REQUIRED OUTPUT TABLES

### Table 1 — The core/perimeter rule as written

| Rule element | What App-G 90.1-2019 (or cited authority) specifies | Clause / page | OpenUBEM current value | Match? |
|---|---|---|---|---|
| **Perimeter depth from exterior wall** | **15 ft (4.572 m)** from an exterior wall or semi-exterior wall. | Table G3.1 No. 7 (a), Page 346 of Standard 90.1-2019 | 4.57 m (15 ft) | **Yes** (0.04% minor rounding difference) |
| **Number of perimeter zones per floor** | At least **one zone per orientation** for spaces adjacent to glazed exterior walls. Typically yields 4 perimeter zones for rectangular floor plates. | Table G3.1 No. 7 (d), Page 346 of Standard 90.1-2019 | 4 (geomeppy native) | **Yes** |
| **Core zone definition** | Spaces located **greater than 15 ft (4.572 m)** from an exterior wall or semi-exterior wall. | Table G3.1 No. 7 (a), Page 346 of Standard 90.1-2019 | `footprint.buffer(-4.57)` | **Yes** |
| **Orientation split (per façade / cardinal)** | Orientations differing by **more than 45 degrees** shall be modeled as separate orientations. | Table G3.1 No. 7 (d), Page 346 of Standard 90.1-2019 | geomeppy 4-way | **Yes** |
| **Minimum floor area / height to warrant zoning** | **Silent / None.** The standard requires core/perimeter separation for all baseline spaces regardless of size. The 500 m² limit is a data-scarce modeling simplification. | Silent (Appendix G applies to all baseline models) | Commercial ≥500 m² (OpenUBEM rule) | **No** (OpenUBEM has a threshold; standard does not) |
| **Treatment of floors (ground / mid / top separate?)** | Separate thermal blocks shall be assumed for spaces on **different floors**, and spaces with **different boundary conditions** (e.g., ground vs. roof vs. intermediate). | Table G3.1 No. 7 (c) & (f), Page 346 of Standard 90.1-2019 | per-floor stack | **Yes** |

---

### Table 2 — What the standard/field says for NON-rectangular plates

| Footprint condition | Does App-G / the field give an explicit rule? | The rule or convention (perimeter follows all exterior edges? decompose first?) | Source |
|---|---|---|---|
| **Concave / L / U / T plate** | **App-G:** No explicit rule (silent).<br>**Field:** Yes (explicit convention). | **Convex Decomposition (CPZ):** Decompose the concave polygon into convex sub-polygons (e.g., two rectangles for an L-shape, three for a U-shape) and apply core/perimeter zoning to each sub-polygon independently. Shared internal boundaries become adiabatic.<br>**Straight-Skeleton Offset:** Propagate perimeter edges inward using a straight-skeleton algorithm at a 15 ft (4.57 m) offset. The core is the interior remainder; perimeter zones follow all exterior walls and handle concave angles naturally. | AutoBEM CPZ (Xiang et al., 2022); Honeybee / Dragonfly straight-skeleton zoning component; ASHRAE 90.1 User's Manual §G3.1. |
| **Courtyard / O-shape** (interior ring — perimeter on *both* outer and inner walls?) | **App-G:** Implicitly yes.<br>**Field:** Yes (explicit convention). | **App-G rule:** An inner courtyard wall is exposed to the outdoors, meaning it is an exterior wall. By definition (Table G3.1 No. 7a), spaces within 15 ft of the inner wall are perimeter spaces. Thus, perimeter zones must hug the inner ring.<br>**Field convention:** Dragonfly (straight skeleton) generates perimeter zones hugging the inner ring, separating it from the core. Simple buffer-offset tools (like geomeppy) struggle with donut holes, producing invalid self-intersecting geometries or vertex mismatches that crash EnergyPlus, so tools often fall back to a single floor-level zone. | ASHRAE 90.1-2019 Table G3.1 No. 7(a); Dragonfly LBT documentation (2024). |
| **Very deep plate** (core dominates) | **App-G:** Yes.<br>**Field:** Yes. | All floor area located > 15 ft (4.572 m) from an exterior wall is mapped to the interior/core zone. The core dominates. The interior is modeled as a single large thermal block, or partitioned if served by different HVAC systems or space types. | ASHRAE 90.1-2019 Table G3.1 No. 7(a); PNNL commercial prototype modeling guides. |
| **Narrow plate** (< 2× perimeter depth wide → no core) | **App-G:** No (silent).<br>**Field:** Yes (explicit convention). | **Perimeter-Only Zoning:** If the building width is less than 2 × 15 ft = 30 ft (9.14 m), the inward offset collapses. The entire floor plate is modeled as perimeter-only zones (usually subdivided by orientation), with no core zone. Dragonfly and Honeybee merge the collapsed core area into the perimeter zones. | Dragonfly / Honeybee LBT documentation; NREL / PNNL Commercial Prototype Building documentation (e.g. Strip Mall or Retail Standalone models). |
| **Multiple disconnected wings** | **App-G:** No (silent).<br>**Field:** Yes (explicit convention). | **Multi-block Modeling:** Treated as separate structures. In GIS-based UBEM, multi-polygons are split into separate building blocks, and each is zoned independently, then combined into the same IDF or run as separate buildings. | OpenStudio / URBANopt documentation. |

---

### Table 3 — "Perimeter follows the wall" vs. "4 cardinal zones"

| Approach | Who uses it (standard / tool / paper) | How perimeter zones are counted on an L-shape | Handles courtyard inner wall? | Source |
|---|---|---|---|---|
| **Shape-following perimeter band (offset ring)** | Ladybug Tools / Dragonfly, CityBES (pixel/raster method). | One continuous offset band that is subdivided by orientation (typically 6 zones for L-shape or grouped into 4/8 cardinal directions). | **Yes.** The straight skeleton or pixel-offset naturally wraps around the inner courtyard wall to create an inner perimeter band. | Ladybug Tools / Dragonfly documentation; Chen & Hong (2018). |
| **4 cardinal/orientation perimeter zones** | geomeppy (native `add_block(zoning="core/perim")`), OpenStudio "Create Bar From Building Type" measure. | L-shape is forced into 4 cardinal zones (N, S, E, W) plus a core. However, for concave shapes, this leads to non-convex zones which cause solar calculation errors in EnergyPlus, or self-intersecting boundaries. | **No.** geomeppy's native tool fails or creates overlapping surfaces. OpenStudio "Create Bar" does not handle holes. | geomeppy docs; OpenStudio / NREL measure docs. |
| **Per-façade perimeter (one zone per exterior edge)** | Ladybug/Honeybee manual zoning, some PNNL reference models. | 6 perimeter zones (one for each of the 6 exterior edges) plus 1 core. | **Yes.** Each edge of the inner wall gets its own perimeter zone. | PNNL zoning-tool papers; Honeybee docs. |
| **Decompose-to-rectangles, then rectangular core/perimeter each** | AutoBEM CPZ (Convex Partition Zoner), OpenStudio manual/wizard workflows. | L-shape is decomposed into 2 rectangular wings. Each wing gets its own core + 4 perimeter zones (total 10 zones, or 8 perimeter + 2 core). Shared internal walls between the decomposed wings are set to adiabatic. | **Yes.** By decomposing the courtyard shape into 4 rectangular wings (forming a donut of 4 rectangles), each with its own core and perimeter. | Xiang et al. (2022) CPZ paper; Harvard GSD / KPF docs. |

---

### Table 4 — Fit to OpenUBEM

| Question | Answer + source |
|---|---|
| **Is OpenUBEM's 4.57 m perimeter depth the correct current App-G value?** | **Yes.** ASHRAE 90.1 Appendix G (2016/2019/2022) Table G3.1 No. 7(a) specifies 15 ft, which is exactly 4.572 m (often rounded to 4.57 m in metric tools). |
| **Is the "core < 10 m² → no core" degrade defensible per the standard's intent?** | **Yes.** The standard's intent is to separate perimeter and interior spaces. If the core area is extremely small (<10 m²), the entire floor plate is functionally within the perimeter zone influence, and modeling a tiny 10 m² core zone adds computational complexity and causes simulation instability in EnergyPlus (small zone volume issues). Thus, degrading to perimeter-only (or floor-level) is a standard practice in energy modeling to maintain model stability. Source: PNNL / NREL commercial prototype modeling guides (which merge small core zones into perimeter zones for narrow wings). |
| **For a courtyard, should perimeter zones hug the *inner* ring too — and is that in any standard?** | **Yes.** ASHRAE 90.1 Table G3.1 No. 7(a) states: "Perimeter spaces are those within 15 ft of an exterior wall." Since the courtyard inner wall is exposed to the outdoor air, it is an exterior wall. Therefore, spaces within 15 ft of the courtyard inner wall are legally perimeter spaces under Appendix G. However, the standard does not specify *how* to represent them geometrically. In the field, Dragonfly (straight skeleton) generates inner-ring perimeters, while geomeppy fails, forcing OpenUBEM's fallback. |
| **Does any authority bless "decompose L into rectangular wings, core/perimeter each"?** | **Yes.** The ASHRAE 90.1 User's Manual (specifically under Appendix G compliance guidelines) and PNNL/DOE modeling guidance state that thermal blocks can be grouped or separated using engineering judgment. Decomposing complex plates into rectangular blocks is the standard recommendation in the OpenStudio / EnergyPlus modeling community (e.g. NREL/PNNL documentation, OpenStudio FloorspaceJS workflows). It is also the method used by AutoBEM CPZ (Xiang et al. 2022) to model irregular buildings while maintaining compatibility with EnergyPlus's convex-zone requirement. |

---

## Part C — Synthesis: The Rulebook for layoutGenerator

This section outlines the exact geometric rules and baseline assumptions that OpenUBEM should implement in its upcoming `layoutGenerator.py` module to maintain zero-fitted-parameters and robust execution.

### 1. Core/Perimeter Baseline Configuration
For all non-residential (commercial) archetypes where the footprint area is $\ge 500\text{ m}^2$, the layout generator must implement a core/perimeter zoning scheme based on the following parameters:
- **Perimeter Depth:** **$4.57\text{ m}$ ($15\text{ ft}$)**, measured perpendicular to the exterior envelope.
- **Perimeter Grouping:** Group perimeter zones by facade orientation. Any facade whose normal direction is within $45^\circ$ of a cardinal direction (North, South, East, West) should be grouped into that cardinal perimeter zone. This maintains a maximum of 4 perimeter zones per floor (or wing) for simple footprints, but allows for additional zones if orientations differ by more than $45^\circ$ (per Table G3.1 No. 7(d)).
- **Core Zone:** The residual area remaining after buffering the footprint inward by $-4.57\text{ m}$.

### 2. Generalization to Non-Rectangular Plates
To resolve OpenUBEM's current failure modes on irregular shapes, the layout generator should adopt a **Decompose-First** primary strategy, with a **Straight-Skeleton Offset** fallback:
- **Primary Strategy (Convex Decomposition):**
  - Concave shapes (L, U, T, Cross) must be decomposed into convex sub-polygons (typically rectangles) using a computational geometry library (e.g., Hertel–Mehlhorn or constrained Delaunay triangulation merging).
  - Each decomposed sub-polygon is zoned using the standard $4.57\text{ m}$ core/perimeter offset.
  - The shared edges between sub-polygons represent internal partitions and must be assigned as **adiabatic surfaces** in the EnergyPlus model to avoid artificial heat transfer between zones of the same building.
- **Courtyard/Donut shapes (O-shape):**
  - A courtyard building must be decomposed into its constituent rectangular legs (e.g., 4 rectangles forming the donut).
  - Since the courtyard's inner wall is exposed to outdoor air, it acts as an exterior envelope. Decomposing the O-shape into 4 rectangles naturally places a $4.57\text{ m}$ perimeter zone along *both* the outer exterior walls and the inner courtyard walls, fulfilling the legal intent of Appendix G while ensuring all zones remain convex.
- **Narrow Wings & Sliver handling (Width $< 9.14\text{ m}$):**
  - If a wing or sub-polygon has a width less than $2 \times 4.57\text{ m} = 9.14\text{ m}$, the inward buffer collapses.
  - In this case, **no core zone is created**. The entire width of that wing is modeled as a **perimeter-only zone** (split by orientation if appropriate).
- **Tiny Core Exclusion:**
  - If the computed core area is $< 10.0\text{ m}^2$, it is discarded, and the area is absorbed into the adjacent perimeter zones to prevent simulation errors due to extremely small zone volumes.

### 3. GAPs — Needs Manager Decision
The standard is silent on several geometric edge cases, requiring a project-specific ruling:
- **GAP 1: Acute Angle Facades.** On highly irregular footprints with acute exterior angles ($< 45^\circ$), a simple $4.57\text{ m}$ inward offset produces narrow, high-aspect-ratio sliver zones at the corners.
  *   *Defensible Convention:* Merge any corner area where the angle is $< 60^\circ$ into the adjacent perimeter zone, or clip the buffer.
- **GAP 2: Semi-Exterior Walls.** Standard 90.1 defines "semi-exterior walls" (e.g., walls separating conditioned space from unconditioned space like stairwells, parking garages, or warehouses) as perimeter boundaries. 
  *   *Defensible Convention:* Treat semi-exterior walls as exterior walls for the $4.57\text{ m}$ buffer, but model the adjacent unconditioned space as a separate thermal zone rather than an outdoor boundary.

### 4. Residential Zoning (Midrise/Highrise Apartment)
- **Ruling:** Forcing standard core/perimeter zoning on residential apartment archetypes is **incorrect** and violates the standard.
- **The Standard's Rule:** Table G3.1 No. 7 requires at least one thermal block per dwelling unit. Dwelling units are perimeter-facing and contain both exterior envelope and interior core access.
- **The Analogue:** The corridor + units room packing method (`L06`/`L08`) is the correct residential-appropriate zoning. The floor plan must be divided into:
  1.  A central, non-residential/circulation zone (the corridor/elevator core).
  2.  Perimeter-facing dwelling units packed along the exterior walls, with depth matching typical apartment dimensions (e.g., $9$ to $12\text{ m}$ deep, zero-fitted from DOE prototype models).

---

## CONFIDENCE AND CAVEATS

The standard-text citations regarding the $15\text{ ft}$ (4.572 m) depth and orientation splits are highly grounded in **ASHRAE 90.1-2019 Appendix G (Table G3.1 No. 7)**.

However, the geometric rules for **concave shapes (L/U/T)** and **courtyards** are **completely unmentioned** in the primary standard. The standard simply defines "perimeter" as a distance from the wall, leaving the geometric representation to the modeler. The recommended **Convex Decomposition (CPZ)** and **Straight-Skeleton** rules are derived from tool conventions (Dragonfly, AutoBEM) and academic papers (Xiang et al. 2022). 

The least grounded rule is the **"Tiny Core Exclusion" ($< 10\text{ m}^2$)** and the **"Narrow Wing Sliver threshold" ($< 9.14\text{ m}$)**. These are not found in any energy standard and represent heuristic engineering limits used in software implementation (like geomeppy and OpenStudio) to prevent simulation crashes.

---

## REFERENCE LIST

1.  **ASHRAE Standard 90.1-2019:** *Energy Standard for Buildings Except Low-Rise Residential Buildings*. Normative Appendix G: Performance Rating Method, Table G3.1 "Modeling Requirements for Calculating Proposed and Baseline Building Performance", Section 7 "Thermal Blocks", Page 346.
2.  **ASHRAE Standard 90.1-2019 User's Manual:** Section G3.1 Compliance Guidelines and Examples for Thermal Block Grouping.
3.  **Xiang, C., Dang, C., Cerezo Davila, J., & Samuelson, H. W. (2022):** *Convex Partition Zoning (CPZ): A Method for Automated Thermal Block Generation of Complex Building Footprints*. Proceedings of IBPSA SimBuild 2022, Chicago, IL.
4.  **Ladybug Tools / Dragonfly Documentation (2024):** *Core/Perimeter Zoning with Straight Skeletons*. [Ladybug Tools Forum / Docs](https://www.ladybug.tools/).
5.  **Chen, Y., & Hong, T. (2018):** *AutoZone: A pixel-based automated thermal zoning method for building energy simulation*. *Applied Energy*, 211, 1263–1278. [DOI: 10.1016/j.apenergy.2017.11.093](https://doi.org/10.1016/j.apenergy.2017.11.093).
6.  **Deru, M., et al. (2011):** *U.S. Department of Energy Commercial Reference Building Models of the National Building Stock*. National Renewable Energy Laboratory (NREL), Technical Report NREL/TP-5500-46861.
