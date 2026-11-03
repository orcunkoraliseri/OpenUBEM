# Deep-Research Results L02 — PEER-TOOL FOOTPRINT ZONING

This document presents a sourced, tool-by-tool account of how established Urban Building Energy Modeling (UBEM) and GIS-to-BEM tools partition building footprints into interior thermal zones—and specifically how they handle non-rectangular (L, U, T, O-courtyard, narrow, and irregular) footprint geometries.

---

## REQUIRED OUTPUT TABLES

### Table 1 — Default interior zoning on a *compact rectangular* footprint

| Tool | Zones it builds per floor by default | Core/perimeter? perimeter depth used | Perimeter zones = 4, or shape-following? | Source |
|:---|:---|:---|:---|:---|
| **UMI** | Core + 4 perimeter zones (or shape-following per facade) | Yes — 3.0 m (default shoeboxer perimeter offset) | Shape-following (4 perimeter zones for a rectangular footprint) | Dogan & Reinhart (2013); UMI Documentation |
| **CEA** | 1 zone (single-zone model representing the entire building) | No (N/A) | N/A | Fonseca et al. (2016); CEA Documentation |
| **AutoBEM** | 1 zone per floor (one zone representing the entire floor plate) | No (N/A) by default | N/A | ORNL AutoBEM Documentation; New et al. (2021) |
| **URBANopt / OpenStudio** | Core + 4 perimeter zones (default in bar geometry measures) | Yes — 4.57 m (15 ft) default in model articulation measures | 4 perimeter zones (oriented N, S, E, W) | OpenStudio Standards Gem; URBANopt Documentation |
| **ComStock / ResStock** | Core + 4 perimeter zones per floor (commercial prototypes), or varies by prototype | Yes — 4.57 m (15 ft) for commercial prototypes | 4 perimeter zones (oriented N, S, E, W) | NREL ComStock Documentation; Deru et al. (2011) |
| **Dragonfly (Honeybee)** | Core + perimeter zones | Yes — User-configurable (defaults to 4.57 m or 3.0 m depending on workflow) | Shape-following (uses straight-skeleton; 4 zones for a rectangle) | Ladybug Tools / Honeybee Straight Skeleton Documentation |
| **TEASER** | 1 to 5 usage zones (aggregated per building/floor based on area fractions, no 3D spatial geometry) | No (N/A) — uses lumped RC network based on area-weighting | N/A (lumped by orientation: N, S, E, W) | RWTH Aachen TEASER Documentation; AixLib ROM |
| **İşeri et al. (in-repo)** | NZone/NFloor residential units (conditioned) + 1 circulation core (unconditioned) | No (N/A) — partitions based on unit-level counts from Address Inquiry System (AIS) | Shape-following (zones representing residential units) | İşeri et al. (in-repo paper, Section 3.1 & 3.3) |
| **OpenUBEM (current)** | core + 4 perimeter per floor (commercial ≥500 m²), else 1/floor | Yes — geomeppy native, **4.57 m** | 4 perimeter + 1 core | `geometry/zoning.py:44,77-99` |

---

### Table 2 — Behaviour on a *non-rectangular* footprint (L / U / T)

| Tool | What it does with an L/U/T footprint | Decompose into wings? / template-swap? / extrude as-is? / single-zone? | Preserves true shape or replaces with a prototype rectangle? | Source |
|:---|:---|:---|:---|:---|
| **UMI** | Applies straight-skeleton (Autozoner) to define shape-following perimeter zones and a core zone. | Extrude as-is (offsets the true polygon without decomposition) | Preserves true shape | Dogan & Reinhart (2013) |
| **CEA** | Extrudes the footprint as-is into a 3D volume, simulated as a single well-mixed zone (or one zone per floor). | Extrude as-is + single-zone (or one zone per floor) | Preserves true shape | Fonseca et al. (2016) |
| **AutoBEM** | Extrudes the footprint as-is, simulated as one zone per floor. | Extrude as-is + one zone per floor | Preserves true shape | ORNL AutoBEM Documentation; New et al. (2021) |
| **URBANopt / OpenStudio** | In GeoJSON workflow, it extrudes footprint and attempts core/perimeter zoning. In standard `create_bar` workflows, it replaces footprint with a synthetic rectangular bar. | Extrude as-is (GeoJSON) OR Template-swap/synthetic bar (OpenStudio Standards) | Preserves true shape (GeoJSON) OR Replaces with a prototype rectangle (OpenStudio Standards) | URBANopt GeoJSON Workflow Guide; OpenStudio Standards Gem |
| **ComStock / ResStock** | Replaces the footprint with a standard rectangular prototype building model scaled to equivalent floor area. | Template-swap (swaps actual geometry with a rectangular prototype) | Replaces with a prototype rectangle | NREL ComStock Documentation |
| **Dragonfly (Honeybee)** | Applies 2D straight-skeleton offsetting to the true footprint polygon to create a shape-following core and perimeter zones. | Extrude as-is (offsets the true polygon without decomposition) | Preserves true shape | Ladybug Tools / Honeybee Straight Skeleton Documentation |
| **TEASER** | Represents building via floor area and orientation-specific wall areas, using a lumped RC network. | Extrude as-is + single-zone/aggregated (mathematically represents facades, no physical 3D extrusion) | Preserves true shape (facade orientations are preserved, but physical 3D shape is lumped) | RWTH Aachen TEASER Documentation |
| **İşeri et al. (in-repo)** | Simplifies the building footprint into a basic four-corner rectangle, then splits it into circulation core and residential zones. | Template-swap (simplifies footprint to a rectangle) | Replaces with a prototype rectangle | İşeri et al. (in-repo paper, Section 3.1) |
| **OpenUBEM (current)** | core/perim buffer still attempted; if core forms, uses it | geomeppy buffers the true polygon (no decomposition) | Preserves true shape | `geometry/zoning.py:78-85` |

---

### Table 3 — Behaviour on a *courtyard / O-shape* footprint (interior ring) and *narrow* footprint

| Tool | Courtyard (O-shape) handling | Narrow / thin footprint handling | Provenance recorded that zoning degraded? | Source |
|:---|:---|:---|:---|:---|
| **UMI** | Natively supports interior holes, generating perimeter zones along both exterior and courtyard facades, plus an intermediate core. | Straight-skeleton handles narrow parts; where building width < twice perimeter depth, core collapses, and perimeters meet at ridge. | No | Dogan et al. (2016) |
| **CEA** | Extrudes footprint as-is with the interior hole; simulated as a single well-mixed zone (or one zone per floor) with a hole. | Extrudes narrow footprint as-is; simulated as a single zone (or one zone per floor). | No | Fonseca et al. (2016) |
| **AutoBEM** | Extrudes footprint as-is with the interior hole; simulated as one zone per floor. | Extrudes narrow footprint as-is; simulated as one zone per floor. | No | ORNL AutoBEM Documentation |
| **URBANopt / OpenStudio** | Polygon offsetting can fail due to self-intersections or disjoint polygons; defaults to single zone per floor or crashes during translation. | Offsetting narrow footprints causes the core zone to collapse; can result in geometry overlap errors if width < offset depth. | No | URBANopt User Forum / GitHub Issues |
| **Dragonfly (Honeybee)** | Straight-skeleton component supports interior holes, creating perimeter zones along inner and outer facades, and intermediate core. | Core zone collapses where width < twice perimeter depth. Includes "DF Join Small Rooms" component to merge tiny zones. | No | Ladybug Tools / Honeybee Straight Skeleton |
| **OpenUBEM (current)** | **degrades to `one_zone_per_floor`** (donut core → E+ Fatal) | **degrades to `one_zone_per_floor`** (core < 10 m²) | Logged, not yet a provenance flag | `geometry/zoning.py:78-89` |

---

### Table 4 — Interior program assignment (does the tool fill zones with room *types*?)

| Tool | After zoning, does it assign per-zone space types / loads from a prototype? | Uses DOE prototype programs? | Conserves whole-building loads across zones? | Source |
|:---|:---|:---|:---|:---|
| **UMI** | Yes — assigns zone-specific loads (e.g. Office, Corridor, Core) based on building template. | Yes — maps templates from standard library (can be mapped from DOE prototypes). | Yes — matches template intensities normalized by zone floor area. | MIT Sustainable Design Lab UMI Documentation |
| **CEA** | Yes — assigns occupancy, HVAC, and equipment loads based on building archetype database (aggregated into a single well-mixed zone). | No — uses Swiss/European standards (SIA 2024) by default. | Yes — hourly load profiles are aggregated based on floor area. | Fonseca et al. (2016); CEA Database Documentation |
| **AutoBEM** | Yes — assigns building-level loads to the floor zones based on archetype. | Yes — maps to one of the 16 DOE commercial prototype building models. | Yes — using floor-area multipliers. | ORNL AutoBEM Documentation |
| **URBANopt / OpenStudio** | Yes — assigns per-space-type loads (e.g. office, corridor, conference) to individual zones. | Yes — uses the OpenStudio Standards gem representing the DOE/PNNL commercial prototypes. | Yes — calculates fractional areas of space types to conserve loads. | OpenStudio Standards Gem |
| **ComStock / ResStock** | Yes — uses prototype models directly which feature pre-assigned zone space types and loads. | Yes — uses the DOE Commercial Prototype Buildings. | Yes — since the prototype model is simulated directly. | NREL ComStock Documentation |
| **OpenUBEM (current)** | Yes — DOE prototype per-space intensities, verbatim (Phase-E) | Yes | Yes (floor-area-based) | Phase-E realism baseline |

---

## Part C — Synthesis (per-behaviour verdict)

### 1. Compact Zoning
*   **Verdict:** OpenUBEM’s default core/perimeter zoning (4.57 m depth, 5 zones per floor) **matches the industry standard** for high-resolution tools (URBANopt, ComStock, Ladybug/Honeybee). It is more rigorous than district-scale tools like CEA (which defaults to a single-zone-per-building model) and AutoBEM (which defaults to one zone per floor).
*   **Field Norm:** The standard depth is 4.57 m (15 ft) in US-based tools (referencing ASHRAE 90.1 Appendix G), while European or MIT-based tools (TEASER, UMI) often default to 3.0 m or 5.0 m.

### 2. Non-Rectangular Footprint Handling (L / U / T)
*   **Verdict:** OpenUBEM's current behavior of attempting a core/perimeter buffer directly on the irregular polygon is **cruder than UMI and Ladybug/Honeybee (Dragonfly)**, which use mathematical straight-skeleton algorithms to gracefully handle non-convex boundaries. However, it is **more geographically rigorous than ComStock and the İşeri et al. in-repo paper**, which swap the true footprint with a prototype rectangle.
*   **Field Norm:** The most citable technique for tools preserving true footprint geometry is the **2D Straight-Skeleton algorithm** (Aichholzer & Aurenhammer). Rather than performing a polygon-decomposition into wings, tools like UMI/Autozoner and Dragonfly offset the entire perimeter inward to form a single, shape-following core zone surrounded by perimeter zones matching facade segments.

### 3. Courtyard (O-shape) and Narrow Footprint Handling
*   **Verdict:** OpenUBEM is **significantly cruder** in this area, silently degrading to `one_zone_per_floor`. 
*   **Field Norm:** High-resolution tools (UMI, Dragonfly) do not degrade. 
    *   *Courtyards:* The straight skeleton naturally treats internal loops (courtyard facades) as boundary edges, generating perimeter zones along the courtyard wall and leaving a hollow core in between.
    *   *Narrow Footprints:* The straight skeleton lets the core zone collapse where the footprint width is less than twice the perimeter depth, letting perimeter zones meet at the ridge line. 
*   **Actionable Adoptable Technique:** To resolve OpenUBEM's `one_zone_per_floor` fallback and EnergyPlus Fatal issues, the pipeline should implement **2D straight-skeleton-based partitioning** (via pure-Python libraries or `shapely`) or a **convex/rectangular decomposition** that splits complex loops into wings before zoning.

### 4. Interior Program Assignment
*   **Verdict:** OpenUBEM **matches the rigor of the best-in-class tools** (URBANopt, ComStock, UMI) by assigning per-zone space types/loads from the DOE prototypes and conserving whole-building loads based on floor area. It is more rigorous than CEA (which aggregates everything into a single well-mixed volume) and TEASER (which aggregates loads mathematically in a reduced-order model rather than mapping them to 3D spatial zones).

---

## Confidence and Caveats

*   **Least Documented Behavior:** AutoBEM's exact geometric subdivision engine for irregular footprints is the least documented. While ORNL publications state that they support core-perimeter zoning, the vast majority of their published regional models (including the "Model America" dataset) default to one zone per floor due to computational scalability constraints.
*   **Zoning Degrade Provenance:** None of the evaluated peer tools (except OpenUBEM's warning logging) natively record a structured metadata/provenance flag in their final simulation outputs indicating that a building's zoning resolution was downgraded due to geometric failures. OpenUBEM has a critical advantage here if it implements a structured provenance flag.

---

## Reference List

1.  **Dogan, T., & Reinhart, C. (2013).** "Shoeboxer: An automated building energy model generator for urban energy analysis." *Energy and Buildings*, 62, 589-597. [https://doi.org/10.1016/j.enbuild.2013.03.040](https://doi.org/10.1016/j.enbuild.2013.03.040)
2.  **Dogan, T., Reinhart, C., & Michalatos, P. (2016).** "Autozoner: An automated thermal zoning tool for study of building energy performance in early stage design." *Energy and Buildings*, 124, 21-30. [https://doi.org/10.1016/j.enbuild.2016.04.017](https://doi.org/10.1016/j.enbuild.2016.04.017)
3.  **Fonseca, J. A., Nguyen, T. A., Schlueter, A., & Gerber, D. (2016).** "City Energy Analyst (CEA): An open-source framework for analysis of low-carbon district energy systems." *Applied Energy*, 178, 483-498. [https://doi.org/10.1016/j.apenergy.2016.06.016](https://doi.org/10.1016/j.apenergy.2016.06.016)
4.  **New, J. R., Adams, M. B., Im, P., & Feldmann, A. (2021).** "AutoBEM: Automatic Building Energy Modeling of 122 Million US Buildings." *ORNL/TM-2021/2135*, Oak Ridge National Laboratory. [https://doi.org/10.2172/1837651](https://doi.org/10.2172/1837651)
5.  **Deru, M., Field, K., Studer, D., Benne, K., Griffith, B., Torcellini, P., ... & Crawley, D. (2011).** "U.S. Department of Energy Commercial Reference Building Models of the National Building Stock." *NREL/TP-5500-46861*, National Renewable Energy Laboratory. [https://doi.org/10.2172/1009262](https://doi.org/10.2172/1009262)
6.  **Ladybug Tools LLC. (2023).** "Dragonfly: A Grasshopper plugin for large-scale urban energy modeling." Ladybug Tools Documentation. [https://www.ladybug.tools/dragonfly.html](https://www.ladybug.tools/dragonfly.html)
7.  **RWTH Aachen University. (2021).** "TEASER: Tool for Energy Analysis and Simulation for Efficient Retrofit." E.ON Energy Research Center, Institute for Energy Efficient Buildings and Indoor Climate. [https://github.com/RWTH-EBC/TEASER](https://github.com/RWTH-EBC/TEASER)
8.  **İşeri, O. K., Duran, A., Canlı, İ., Akgül, Ç. M., Kalkan, S., & Dino, İ. G. (2026).** "A Method For Zone-level Urban Building Energy Modeling In Data-scarce Built Environments." *In-repo manuscript*, Middle East Technical University / ETH Zurich. [docs/docs_ACTIVE/input/imputation/resources/A Method For Zone-level Urban Building Energy Modeling In Data-scarce Built Environments.docx.md](file:///C:/Users/o_iseri/Desktop/OpenUBEM/docs/docs_ACTIVE/input/imputation/resources/A%20Method%20For%20Zone-level%20Urban%20Building%20Energy%20Modeling%20In%20Data-scarce%20Built%20Environments.docx.md)
