# Result L01 — Interior Zoning Landscape & Method Taxonomy

## Table 1 — The method families for footprint → thermal zones

| Method family | Core idea | Inputs required | Footprint shapes it handles well | Zones produced (few thermal vs. many program) | Fidelity tier | Representative source |
|---|---|---|---|---|---|---|
| **Rule-based standards zoning (App-G core/perimeter)** | Offsets the exterior building envelope polygon inward by a standard distance to create a self-shaded core zone and oriented perimeter zones. | Footprint polygon, perimeter depth (typically 4.57 m / 15 ft). | Compact, convex-ish, hole-free shapes (rectangles, circles, convex polygons). | Few thermal zones (typically 5 zones per floor: 1 core and 4 oriented perimeter). | Low-to-medium thermal zoning. | ASHRAE Standard 90.1-2019 Appendix G (Clause G3.1.1.1); LEED v4 Reference Guide. |
| **Procedural template / prototype floorplate transplant** | Fits a pre-defined parametric zoning layout from standardized prototype models onto the building's geometry (e.g., stretching a template to fit). | Footprint geometry, building archetype/type, pre-defined template geometries and dimensions. | Simple rectangular or regular L/U/T/H layouts matching prototype specs. | Medium mixed zones (separating offices, retail, corridors based on prototype fractions). | Medium fidelity. | Deru et al. (2011) "U.S. Department of Energy Commercial Reference Building Models of the National Building Stock." NREL/TP-5500-46861. |
| **Corridor-spine + room-packing (the proposed method)** | Extracts the medial axis or straight skeleton to place a central corridor, then packs standardized functional room/dwelling modules along perimeter edges. | Footprint polygon, archetype space requirements (room depth/width, corridor width), circulation fraction. | Linear, branched, non-convex shapes (L, U, T, cross, courtyard O-shape, thin ribbon). | Many program-motivated (architectural-like) zones that act as thermal zones. | High fidelity. | Dogan, Reinhart, & Michalatos (2016) "Autozoner: an algorithm for automatic thermal zoning of buildings with unknown interior space definitions." *Journal of Building Performance Simulation*. |
| **Geometric decomposition (skeleton / rectangular split, then zone each part)** | Slices a complex non-convex polygon into simpler convex/rectangular sub-polygons (wings) and zones each part individually. | Footprint polygon, decomposition algorithms (e.g., convex partitioning or skeleton branch slicing). | L-shape, U-shape, T-shape, cross, courtyard (O-shape), and irregular polygons. | Few-to-medium thermal zones per wing (each wing has its own core/perimeter). | Medium-to-high thermal fidelity. | Convex Partition Zoner (CPZ) (e.g., İşeri et al. / research on CPZ); Dogan et al. (2016). |
| **Grid / raster subdivision** | Overlays a uniform grid or voxel grid on the footprint, treating each cell or cell cluster as a thermal zone. | Footprint polygon, grid/cell size (resolution). | Irregular, concave blobs, highly complex geometries. | Many uniform thermal zones (requires clustering to manage simulation overhead). | Medium-to-high thermal (lacks architectural meaning). | Voxel-based BEM approaches (e.g., Ladybug/Honeybee Dragonfly grid tools). |
| **ML / generative floorplan synthesis** | Uses deep generative neural networks (GANs, GNNs, diffusion) trained on real floorplans to synthesize rooms inside the footprint. | Boundary polygon, room adjacency graphs, trained network weights. | Compact residential/commercial layouts similar to training data. | Many program-motivated (architectural-like) zones representing real rooms. | High architectural fidelity (violates BEM simplicity rules). | Graph2Plan (Hu et al. 2020), HouseGAN (Nauata et al. 2020). |
| **No-subdivision fallbacks (single-zone, one-zone-per-floor)** | Treats the entire floorplate or building volume as a single zone, assuming uniform internal air mixing. | Footprint polygon, floor/building height. | All shapes (including complex concave blobs). | Minimal thermal zones (1 per floor or 1 per building). | Very low fidelity. | ISO 13790 simplified hourly methods; TEASER (reduced-order model fallbacks); OpenUBEM baseline. |

---

## Table 2 — Behaviour on a *non-rectangular* footprint (L / U / T)

Which families cope with which shapes. Mark ✓ / partial / ✗ and one-line why.

| Footprint shape | Rule-based core/perim | Procedural template | Corridor+packing | Geometric decomposition | ML/generative |
|---|---|---|---|---|---|
| **Compact rectangle** | ✓ (Default standard; works perfectly). | ✓ (Standard templates map directly without stretching). | ✓ (Packs rooms easily along a straight corridor). | ✓ (Trivial case; no splitting required). | ✓ (Highly represented in training datasets like RPLAN). |
| **L-shape** | Partial (Can cause self-intersection or thin zones at corner joins). | Partial (Requires dedicated L-shape templates, fails to scale flexibly). | ✓ (Corridor naturally follows the L-spine; rooms pack cleanly). | ✓ (Split at corner into two rectangles, then zoned). | Partial (Can fail to generate stable layouts if boundary ratios are unusual). |
| **U-shape** | ✗ (Offsetting inward leads to self-intersection and empty core issues). | Partial (Requires complex parametric U-shape template). | ✓ (Corridor follows U-spine; rooms pack along outer and inner edges). | ✓ (Split into three rectangles, then zoned). | ✗ (Difficulty handling narrow wings and concave voids). |
| **T / cross** | ✗ (Complex junctions cause overlapping buffers and invalid geometries). | Partial (Requires highly specific T/cross templates). | ✓ (Spine branches at junctions; rooms pack along wings). | ✓ (Slices into multiple intersecting rectangles). | ✗ (Fails to construct logical circulation across multiple intersections). |
| **O-shape / courtyard (interior ring)** | ✗ (Produces donut-shaped polygons; causes inter-floor vertex mismatch and EnergyPlus Fatal errors). | ✗ (Standard templates do not support internal courtyard holes). | ✓ (Spine forms a loop around the courtyard; double-loaded packing works outwards and inwards). | ✓ (Slices ring into four wings, zoned individually). | ✗ (Standard floorplan GANs cannot handle internal boundary rings/voids). |
| **Thin ribbon (narrow)** | ✗ (Inward 4.57 m buffer collapses entirely, leaving empty/negative core). | Partial (Stretching templates to narrow spans yields invalid room shapes). | ✓ (Adapts to single-loaded or open-plan zoning with no core). | Partial (Can decompose, but sub-polygons remain narrow, so buffer still fails). | ✗ (Fails to pack valid room ratios within tight boundaries). |
| **Irregular / concave blob** | ✗ (Offsets create complex self-intersecting loops and slivers). | ✗ (No template fits an arbitrary curved/concave shape). | Partial (Medial axis extraction is noisy, but smoothed spine works). | Partial (Decomposes into convex parts, but parts may be non-rectangular). | ✗ (Completely out of distribution for floorplan datasets). |

---

## Table 3 — Fit to OpenUBEM's constraints, per family

| Method family | Satisfies zero-fitted-parameters? (uses published dimensions, no target tuning) | Can emit provenance (which method / fallback touched a building)? | Expressible in `shapely`+`geomeppy`? | Verdict for OpenUBEM (adopt / adopt-as-fallback / skip) |
|---|---|---|---|---|
| **Rule-based core/perimeter** | Yes (uses ASHRAE 90.1 4.57 m standard). | Yes (records "rule_based_app_g_4.57m_offset"). | Yes (already implemented for simple shapes). | **Adopt** as primary for convex / simple shapes. |
| **Procedural template transplant** | Yes (uses published DOE prototype dimensions). | Yes (records "procedural_template_<archetype>"). | Partial (stretching and scaling templates is highly complex in shapely). | **Skip** (redundant; corridor+packing is more flexible). |
| **Corridor+packing** | Yes (uses published DOE room and corridor dimensions). | Yes (records "corridor_spine_room_packing"). | Yes (can extract straight skeleton in Python and slice using shapely). | **Adopt** as primary for non-convex / complex shapes. |
| **Geometric decomposition** | Yes (partitioning is purely geometric/algorithmic). | Yes (records "geometric_decomposition_hertel_mehlhorn" or similar). | Yes (implemented via convex partitioning in shapely). | **Adopt** as preprocessing step (partitions complex footprints into wings). |
| **ML/generative** | No (fits millions of weights, non-deterministic). | Partial (can log model name, but not the specific layout rationale). | No (requires PyTorch/TensorFlow, cannot run natively in shapely/geomeppy). | **Skip** (violates zero-fitted-parameters, not reproducible, too heavy). |

---

## Table 4 — The thermal-zoning vs. architectural-floorplan distinction

| Question | Answer + source |
|---|---|
| **How many zones does BEM practice put on a typical floor (vs. an architectural plan's room count)?** | BEM typically uses 1 to 5 zones per floor (e.g., 4 perimeter + 1 core) to minimize simulation time and errors. Architectural plans have 10 to 50+ rooms per floor motivated by functional layout, privacy, and physical walls. <br> *Source: ASHRAE Standard 90.1-2019 Appendix G; Dogan et al. (2016) "Autozoner" paper.* |
| **Is the App-G "4 perimeter + 1 core" the field's default *thermal* zoning granularity?** | Yes. It is the industry standard default when the internal layout is unknown, ensuring that zones with different solar/wind exposures are modeled separately from the self-shaded core. <br> *Source: ASHRAE 90.1-2019 Clause G3.1.1.1; PNNL Commercial Prototype Building Models.* |
| **When does a study go finer than core/perimeter (per-room), and what drives that (daylighting, HVAC zoning, load diversity)?** | Studies go finer when analyzing localized daylighting control (e.g., photo-sensors in individual rooms), spatial diversity of internal loads (e.g., server rooms vs. bedrooms), or room-level HVAC controls (e.g., VRF/FCU systems). <br> *Source: Reinhart & Fitz (2006); Crawley et al. (2001) EnergyPlus documentation.* |
| **Does the corridor+DOE-module approach produce *thermal* zones or *architectural* rooms — and does that matter for EUI?** | It produces architectural-like rooms that are simulated directly as thermal zones. This matters for EUI: representing rooms individually captures local solar peak diversity and load schedules, changing heating/cooling EUI by 5-15% compared to lumped perimeter zones. <br> *Source: Dogan et al. (2016) Autozoner; İşeri et al. (2025) "Zoning Granularity Tiers" in-repo preprint.* |

---

## Part C — Synthesis (the family recommendation)

### 1. Proposed Method Taxonomy Classification
OpenUBEM's proposed **corridor-spine + room-packing method** belongs to the **Procedural template / prototype floorplate transplant** family, driven by a **Geometric decomposition** preprocessing step. The BEM field regards this combination as a highly sound and defensible approach for UBEM-scale zoning. It bridges the gap between raw GIS footprints and standardized EnergyPlus prototypes (DOE Reference Buildings) by geometrically restructuring the prototype's interior space types to fit the actual building's boundary while conserving its thermal load properties.

### 2. Recommended Primary Family + Fallback Chain
We recommend the following hierarchical fallback chain for OpenUBEM's geometry pipeline:
1. **Primary (Simple/Convex)**: Rule-based core/perimeter (ASHRAE 90.1 App-G 4.57m offset) applied directly via `geomeppy`.
2. **Primary (Complex/Non-Convex/Courtyard)**: Geometric decomposition to partition the footprint into convex wings, followed by Corridor+packing (double-loaded corridor along straight skeleton spine with packed DOE-module rooms) on each wing.
3. **Fallback (Narrow/Thin Ribbon)**: Corridor+packing (single-loaded corridor or open-plan zones) where core buffer collapses.
4. **Ultimate Fallback**: `one_zone_per_floor` if geometric decomposition or spine extraction fails completely (e.g., self-intersecting boundaries or highly irregular geometries).

### 3. Downstream Prompt Details
The downstream prompts should focus on detailing:
*   **Rule-based core/perimeter generalization** (`L03`): To handle non-convex boundary cases without complete failure.
*   **Geometric decomposition & shape classification** (`L04` and `L05`): To classify footprints and slice them into simpler convex components.
*   **Corridor+packing algorithm** (`L06`): To define the double-loaded corridor packing rules.
*   **Procedural DOE program templates** (`L07` to `L10`, `L12`): To extract and represent room dimensions, mixes, and circulation ratios for archetypes.
*   **Load conservation and fallback logistics** (`L11`): To ensure thermodynamic consistency.
*   **Generative/ML floorplan synthesis** (`L13`): Kept in a low-priority/exploratory status (skip for core pipeline but analyze limitations).

### 4. Critical Gap in Current Approach
The current approach lacks **geometric flexibility for non-convex and courtyard layouts**, causing it to drop back to `one_zone_per_floor` for a significant portion of urban building stock. This means complex-shaped buildings (which often have high skin-to-volume ratios and unique solar exposures) are simulated with virtually no spatial resolution, leading to massive inaccuracies in perimeter solar load calculations and heating/cooling sizing.

---

## Confidence and Caveats

*   **Generative ML (Graph2Plan, HouseGAN, RPLAN)** is the least evidenced family for city-scale UBEM. While highly researched in computer-aided architectural design, there is almost zero peer-reviewed evidence showing that ML-synthesized floorplans improve EUI simulation accuracy compared to geometric-decomposition or corridor-packing methods. Furthermore, ML-based layouts fail the zero-fitted-parameters constraint, suffer from geometric non-determinism, and have high computational overhead that prevents them from scaling to millions of buildings.
*   **Corridor+packing** is highly robust for linear and regular shapes, but its extraction on irregular/concave "blobs" is sensitive to straight-skeleton noise (spurious branches), requiring careful geometric simplification and pruning.

---

## References

1. **ASHRAE Standard 90.1-2019 Appendix G.** *Energy Standard for Buildings Except Low-Rise Residential Buildings*, Clause G3.1.1.1. [ASHRAE](https://www.ashrae.org)
2. **Deru, M., Field, K., Studer, D., Benne, K., Griffith, B., Torcellini, P., Halverson, M., Winiarski, D., Liu, B., & Bartlett, R. (2011).** *U.S. Department of Energy Commercial Reference Building Models of the National Building Stock*. National Renewable Energy Laboratory (NREL), Technical Report NREL/TP-5500-46861. [NREL](https://www.nrel.gov/docs/fy11osti/46861.pdf)
3. **Dogan, T., Reinhart, C., & Michalatos, P. (2016).** "Autozoner: an algorithm for automatic thermal zoning of buildings with unknown interior space definitions." *Journal of Building Performance Simulation*, 9(2), 176-189. DOI: [10.1080/19401493.2015.1018285](https://doi.org/10.1080/19401493.2015.1018285)
4. **Hu, R., Huang, J., Patton, D., & Zhang, H. (2020).** "Graph2Plan: Learning Floorplan Generation from Layout Graphs." *ACM Transactions on Graphics*, 39(4), Article 118. DOI: [10.1145/3386569.3392391](https://doi.org/10.1145/3386569.3392391)
5. **Nauata, N., Chang, K. H., Cheng, C. Y., Mori, G., & Furukawa, Y. (2020).** "HouseGAN: Relational Generative Adversarial Networks for Graph-constrained House Layout Generation." *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (ECCV 2020)*. [arXiv:2003.06988](https://arxiv.org/abs/2003.06988)
6. **Wu, W., Fu, X. M., Tang, R., Wang, Y. H., Qi, Y. H., & Liu, L. (2019).** "RPLAN: Vector-based Dataset of Residential Floor Plans." *ACM Transactions on Graphics (SIGGRAPH Asia 2019)*. [RPLAN Project](https://chinge.github.io/rplan/)
7. **İşeri, O. K., et al. (2025).** *Zoning Granularity Tiers in Data-Scarce Urban Building Energy Modeling.* OpenUBEM Preprint.
8. **NREL (2023).** *OpenStudio Measures: Create Bar From Building Type.* GitHub Repository. [GitHub](https://github.com/NREL/openstudio-common-measures-gem)
