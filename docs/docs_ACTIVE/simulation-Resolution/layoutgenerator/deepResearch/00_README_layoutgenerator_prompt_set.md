# LayoutGenerator — Deep-Research Prompt Set (INDEX)

> READ FIRST. This set is about the step that decides **what interior thermal-zone layout OpenUBEM
> builds inside a building's real OSM footprint when that footprint is *not* a clean rectangle** — the
> L-, U-, T-, O-/courtyard-, and irregular-shaped buildings that today the pipeline cannot slice into
> core+perimeter and so silently drops back to a coarser resolution. It is NOT about *which archetype a
> building becomes* (that is the `input-framework/` set) and NOT about *how many zones per building the
> adaptive rule picks* (that is `SIMULATION_RESOLUTION_zoning_by_building.md`). It is about the geometry
> + program logic of a proposed new module, `openubem/geometry/layoutGenerator.py`, that takes an
> arbitrary footprint polygon + an archetype + a floor count and emits a room/zone-level floor plan —
> a corridor/circulation core with perimeter rooms packed along edges and corners, following the DOE
> reference-building interior program (MidriseApartment dwelling units, SmallHotel guest rooms, etc.).
> Run each prompt in your deep-research tool (Gemini Antigravity); save the answer beside it as
> `RESULT_<id>_<slug>.md`. The manager audits each RESULT and only then drafts
> `PLAN_layoutgenerator_implementation.md`.

---

## The exact decision this set must inform

OpenUBEM already has a highest-fidelity zoning strategy — `perimeter_core` (the `zone` / B1 resolution
mode) — that cuts a **core + 4 perimeter zones per floor** from the building's *actual* OSM polygon by
a 4.57 m (15 ft, ASHRAE 90.1 Appendix G) inward buffer, preserving true shape and neighbour shading.
It works only for **compact, convex-ish, hole-free** footprints. When the footprint is:

- **narrow** — the 4.57 m inward buffer collapses (core empties or `core.area < 10 m²`), or
- **a courtyard / O-shape** — the footprint has an interior ring, and geomeppy's donut core produces
  mismatched inter-floor vertex counts → EnergyPlus **Fatal**,

…the code silently falls back to `one_zone_per_floor` (`openubem/geometry/zoning.py:78-89`). So an
L-shaped tower, a U-shaped school, an O-shaped courtyard apartment block, or a thin ribbon building is
simulated at **floor level, never room level**, even in the highest-fidelity `zone` mode.

`layoutGenerator.py` is the module that closes this gap. The user's proposed method — the thing this
set must validate, refine, or replace against the literature — is:

> **Decompose the real footprint into a corridor spine + perimeter rooms.** Place a circulation
> corridor along the footprint's medial axis / spine (for an L-shape, an L-shaped corridor; for a U,
> a U-corridor), then pack rooms onto the corners and edges using the *same standard module the DOE
> reference building uses* — MidriseApartment dwelling-unit depth and mix for residential, SmallHotel
> guest-room module for hotels, and analogous programs for offices, schools, hospitals, and large
> hotels. This reuses the DOE prototype's per-space loads/schedules verbatim, just re-laid-out onto the
> building's true shape.

The set decomposes into: **(a) how the field does it** (`L01`–`L03`), **(b) the geometry algorithms**
(`L04`–`L06`), **(c) the per-archetype interior programs to replicate** (`L07`–`L10`, `L12`),
**(d) making the result physically conservative + provenanced** (`L11`), **(e) the frontier and the
accuracy/cost/validation case** (`L13`–`L15`).

| Concern | Prompt(s) | What it must decide |
|---|---|---|
| Solution-space map + peer practice | `L01`, `L02` | the taxonomy of auto-interior-zoning methods; what shipped UBEM/BEM tools do for non-rectangular footprints |
| The rule we already use, generalized | `L03` | how ASHRAE 90.1 App-G core/perimeter zoning is defined for non-convex / holed polygons |
| Geometry primitives | `L04`, `L05` | footprint shape classification; offset / straight-skeleton / medial-axis / polygon-decomposition algorithms to slice arbitrary shapes |
| The proposed corridor+rooms method | `L06` | double-loaded-corridor room-packing — is the user's method the field's convention? |
| Interior programs to replicate | `L07`–`L10`, `L12` | what the DOE prototypes actually contain; residential/hotel, office/retail/school, hospital/large, mixed-use per-archetype layout logic |
| Physical conservation + provenance | `L11` | distributing DOE loads/schedules to generated zones so totals are conserved; interior/adiabatic surfaces |
| Frontier, accuracy, validation | `L13`, `L14`, `L15` | generative/ML floorplan methods; EUI sensitivity vs. cost; how to validate a layout with no ground-truth interior |

---

## The prompts

| # | File | What it learns | Priority |
|---|------|----------------|----------|
| L01 | `L01_interior_zoning_landscape_prompt.md` | The full solution space: rule-based (App-G), procedural/template, decomposition-based, and generative methods for turning a footprint into interior thermal zones — and when each is appropriate. Scopes every downstream prompt. | **core** |
| L02 | `L02_peer_tool_footprint_zoning_prompt.md` | Tool-by-tool: how UMI, CEA, AutoBEM, URBANopt/OpenStudio, ComStock/ResStock, geomeppy, TEASER handle non-rectangular footprints — do they core/perimeter, single-zone, decompose, or give up? | **core** |
| L03 | `L03_ashrae_appG_core_perimeter_generalization_prompt.md` | The exact definition of App-G / LEED core+perimeter auto-zoning, the 4.57 m perimeter rule, and how standards + tools generalize it to L/U/T/non-convex and courtyard footprints. | **core** |
| L04 | `L04_footprint_shape_classification_prompt.md` | How to classify an OSM footprint (rectangle / L / U / T / O-courtyard / cross / irregular / ribbon) from the polygon alone — the morphological typologies and the metrics (compactness, rectangularity, skeleton branches) that detect them. | high |
| L05 | `L05_polygon_geometry_primitives_prompt.md` | The computational-geometry toolkit: inward offset/buffer, straight skeleton, medial axis, rectangular/convex decomposition — which primitive slices which shape into corridor+core+perimeter, robustly, in `shapely`/geomeppy terms. | **core** |
| L06 | `L06_corridor_room_packing_method_prompt.md` | The user's proposed method: double-loaded-corridor room packing along a footprint spine — is it the field's convention, what are the design rules (corridor width, unit depth, packing on corners), and where does it break? | **core** |
| L07 | `L07_doe_prototype_interior_programs_prompt.md` | What the DOE/PNNL reference buildings actually contain inside: space-type mix, unit/room modules & dimensions, circulation fraction, zone multipliers — the templates `layoutGenerator` replicates onto real shapes. | **core** |
| L08 | `L08_residential_hotel_layout_prompt.md` | Residential + hotel specifics: MidriseApartment / HighriseApartment dwelling-unit depth & mix, SmallHotel guest-room modules, the double-loaded corridor on L/U/O plans. | high |
| L09 | `L09_office_retail_school_layout_prompt.md` | Office / retail / school specifics: elevator-stair-restroom core placement, open vs. cellular perimeter, classroom-wings-off-a-corridor, big-box single-space retail. | high |
| L10 | `L10_large_complex_building_layout_prompt.md` | Hospitals, large hotels, deep-plan / high-rise: functional/department zoning, multi-core plans, deep-floorplate interior zones beyond a single core+perimeter ring. | medium |
| L11 | `L11_load_schedule_conservation_and_interior_surfaces_prompt.md` | Physical correctness: how to apportion DOE prototype loads/schedules/setpoints to the generated zones so building totals + intensities are conserved, and how interior partitions / inter-zone surfaces are treated (adiabatic vs. heat-transfer). | **core** |
| L12 | `L12_mixed_use_vertical_heterogeneity_prompt.md` | Vertical program change: ground-floor retail podiums, per-floor use changes, and how layout generation differs floor-to-floor within one building. | low |
| L13 | `L13_generative_ml_floorplan_prompt.md` | The frontier: procedural + ML/generative floorplan generation (Graph2Plan, HouseGAN, RPLAN, procedural building generators, CityGML LoD4 interiors) — capability, and the zero-fitted-params / provenance / reproducibility cost. | low |
| L14 | `L14_accuracy_fidelity_tradeoff_prompt.md` | Does room-level layout actually change EUI vs. core/perimeter vs. floor vs. single-zone, and by how much — the evidence for *when* the extra fidelity is worth it, and the LOD-selection rule. | high |
| L15 | `L15_validation_and_computational_cost_prompt.md` | How to validate a *generated* layout when no ground-truth interior plan exists (mask-and-recover, expert plausibility, downstream-EUI), and how zone count / runtime scale with layout resolution. | medium |

> **Load-bearing core: `L01 + L02 + L03 + L05 + L06 + L07 + L11`.** These decide whether the proposed
> corridor+DOE-module method is the defensible convention, give the geometry primitives to implement it,
> and ensure the result conserves the DOE loads and carries provenance. Run them first. Run
> `L04`/`L08`/`L09`/`L14` next to detail the per-archetype logic and justify the fidelity. Treat
> `L10`/`L12`/`L13`/`L15` as the depth/frontier tier, run once the MVP method is chosen.

---

## Shared facts (all prompts assume these)

Grounded in `../../resolution_sets/SIMULATION_RESOLUTION_zoning_by_building.md` and
`openubem/geometry/zoning.py` (verified against code 2026-06-29 / 2026-07-02). Every prompt pre-fills
its own **OpenUBEM-current** row from this list — do not re-derive it.

- **One IDF / one EnergyPlus run per building, always.** Floors and rooms are thermal *zones inside one
  model*, never separate models. Temporal resolution is fixed: annual, 8760 hourly timesteps.
- **Three existing zoning strategies** (`openubem/geometry/zoning.py`, `decide_zoning_strategy` /
  `build_zones`):
  - `single_zone` — footprint extruded to full height (`num_floors × 3.5 m`), 1 zone.
  - `one_zone_per_floor` — footprint stacked N times, 1 zone/floor.
  - `perimeter_core` — geomeppy **native** core/perimeter via `add_block(zoning="core/perim")`, core =
    `footprint.buffer(-4.57)`, 4 perimeter zones + 1 core per floor. **This is the `zone`/B1 mode.**
- **The gap `layoutGenerator` fills.** `perimeter_core` degrades to `one_zone_per_floor` when
  (a) the footprint is **narrow** — `core_poly.is_empty or core_poly.area < 10.0` — or (b) the footprint
  has an **interior ring / courtyard** — `list(footprint_poly.interiors)` non-empty, because geomeppy's
  donut core yields mismatched inter-floor vertex counts → **E+ Fatal** (`zoning.py:78-89`). So today
  **L / U / T / cross / O-courtyard / ribbon footprints never reach room-level resolution.**
- **Real footprint is preserved, not resized to a DOE rectangle.** B1's whole point is true shape +
  neighbour shading. The layoutGenerator must lay rooms out *inside the actual OSM polygon*, not swap in
  a prototype's rectangular floorplate.
- **Floor area (the EUI denominator) is always `footprint_area_m2 × num_floors`**, independent of zoning
  strategy — any generated layout must conserve this.
- **Floor-to-floor height is 3.5 m** everywhere.
- **`resolution_mode` switch** (`building` / `floor` / `zone` / `auto`, `auto` = validated default):
  layoutGenerator is the upgrade to the `zone` mode so it can honour its promise — core/perimeter (or
  finer) on **all** archetypes and **all** footprint shapes, not just compact convex ones.
- **Forced-per-floor archetypes today** (never core/perim even when large): `MidriseApartment`,
  `HighriseApartment`, `TallBuilding`, `SuperTallBuilding`, `OpenUBEMUnknown`. The proposed method would
  *change this* for residential (a midrise apartment floor is naturally corridor + dwelling units) — so
  the set must establish whether residential room-level layout is defensible and better than per-floor.
- **Loads / schedules / setpoints come from the DOE/PNNL reference buildings**, adopted verbatim under
  the project's Phase-E "full realism" baseline. `layoutGenerator` does **not** invent new loads — it
  re-distributes the prototype's per-space-type intensities onto the generated zones.
- **Geometry engine is `shapely` (polygon ops) + `geomeppy` (IDF geometry / `add_block`) on
  EnergyPlus 23.1.** Any recommended algorithm must be expressible in that stack (or a pure-Python /
  `shapely` primitive we can add) — flag anything needing heavy external CAD/GIS engines.

## Two hard constraints (repeat in every recommendation)

1. **Zero-fitted-parameters.** Every dimension, depth, corridor width, unit module, or circulation
   fraction the generator uses must be a **published convention** (ASHRAE/IECC/DOE prototype
   documentation, a design-standards reference, a peer-reviewed source) — *not* a value tuned to make a
   validation EUI look better. Flag any method that requires target-tuned geometry.
2. **Provenance is non-negotiable.** A generated layout must leave a queryable marker recording that the
   zones were synthesized (which method, which fallback path, confidence downgrade), matching the
   Tier-A provenance convention already used elsewhere in the pipeline. A method that cannot report what
   it did is unacceptable regardless of realism.

## Source / tool roster (use across prompts where relevant)

UMI (Dogan & Reinhart) · City Energy Analyst / CEA (Fonseca et al.) · AutoBEM/AutoBEM-Geo (New et al.,
ORNL) · URBANopt / OpenStudio + the OpenStudio "create-bar-from-building-type" / geometry-from-footprint
measures (NREL) · ComStock / ResStock (NREL) · geomeppy (`add_block` core/perim) · TEASER (RWTH) ·
Ladybug/Honeybee + Dragonfly (LBT) · DOE/PNNL Commercial & Residential Prototype Buildings + the
Commercial Reference Buildings (Deru et al. 2011) · ASHRAE 90.1-2019 Appendix G / LEED core-perimeter
zoning rules · the computational-geometry literature (straight skeleton — Aichholzer & Aurenhammer;
medial axis; polygon offsetting; rectangular decomposition) · the automated-floorplan-generation
literature (Graph2Plan — Hu et al.; HouseGAN/HouseGAN++ — Nauata et al.; RPLAN — Wu et al.; procedural
building generators) · the İşeri et al. in-repo data-scarce-UBEM paper (zone-level granularity tiers).

## Conventions for every answer (enforced by each prompt)

1. **Lead with the filled tables**; prose after. Empty / "TBD" cells are failures.
2. Every method / dimension / rule carries a **named, dated source** — a peer-reviewed UBEM/BEM paper
   (author, venue, year), a standard (ASHRAE/IECC clause), tool documentation, or a library's official
   docs. Blogs / vendor pages are last resort, labelled.
3. **Always compare against OpenUBEM's actual current behaviour** (given inline in each prompt from the
   Shared facts above) — say explicitly whether peer practice matches, is more rigorous, or is looser.
4. **No fabricated precision.** If a value is your synthesis, say so. If unpublished, write **"GAP —
   needs manager decision"** + the closest defensible default and its source.
5. **Map onto OpenUBEM's exact vocabulary** — `footprint_area_m2`, `num_floors`, 3.5 m floors, 4.57 m
   perimeter depth, the `single_zone` / `one_zone_per_floor` / `perimeter_core` strategies, the DOE
   archetype names, `shapely` / `geomeppy` — not generic "space planning" in the abstract.
6. **Respect the two hard constraints** in every recommendation: zero-fitted-parameters and mandatory
   provenance. A method that violates either is a non-starter — say so.
7. **Stay on topic per prompt** — do not re-litigate archetype classification (`input-framework/`),
   missing-input imputation (`input/imputation/`), or the per-building AUTO zoning rule itself
   (`SIMULATION_RESOLUTION_zoning_by_building.md`). This set is *interior layout geometry + program* only.

---

*OpenUBEM — layoutGenerator deep-research set. Markdown only; binding specs remain `docs/docs_main/`.
Grounded in `SIMULATION_RESOLUTION_zoning_by_building.md`, `openubem/geometry/zoning.py`, and the DOE
prototype interior programs. 2026-07-02.*
