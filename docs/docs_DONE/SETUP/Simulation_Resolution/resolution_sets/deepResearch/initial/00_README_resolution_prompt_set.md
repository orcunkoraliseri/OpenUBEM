# Resolution-Mode — Deep-Research Prompt Set (INDEX)

> READ FIRST. This folder holds a SET of standalone deep-research prompts supporting the OpenUBEM
> **user-selectable resolution-mode switch** (`PLAN_resolution_mode_switch.md`). Each gathers the
> **sourced methodology + parameters** needed to *correctly implement and defend* one resolution
> mode or one cross-cutting concern that changes when zone count changes. Run each prompt in your
> deep-research tool; save the answer beside it as `RESULT_<nn>_<slug>.md`. The manager then audits,
> fills any GAP with a defensible default, and folds the decision into the plan. Prompts are
> self-contained and may be run in any order.

---

## What the resolution switch is (so every researcher scopes correctly)

OpenUBEM is an Urban Building Energy Model that builds **one EnergyPlus IDF per building** for
neighbourhoods of thousands of buildings, each mapped to one of **30 archetypes** and an ASHRAE
climate zone. Inside each building the number of **thermal zones** is today chosen *automatically*
("auto" mode) from `archetype_id`, `footprint_area_m2`, and `num_floors`
(`openubem/geometry/zoning.py`). We are adding a **user switch** so a study can fix the fidelity:

| Mode | Zoning forced on every building | Zones/building | Status |
|---|---|---|---|
| **1. `building`** | whole building = **1 zone** (full height) | 1 | ⬜ to implement |
| **2. `floor`** | each floor = **1 zone** | `num_floors` | ⬜ to implement |
| **3. `zone` (B1)** | **core + perimeter per floor**, all archetypes, cut from the **real footprint** | ~5 × `num_floors` | ⬜ to implement |
| **`auto`** *(default)* | adaptive (current validated baseline) | mixed | ✅ exists |

**B1 definition (binding):** at `zone` level OpenUBEM slices core + perimeter zones from the
building's **actual OSM footprint polygon** via an inward buffer (currently 4.57 m), preserving the
true shape and neighbour shading — NOT a resized DOE rectangular prototype.

**The research question is not "can we add a zone" (the code is easy) — it is "how do we build each
resolution so the physics stays correct and the result is defensible in a paper."** Collapsing a
10-floor building into one zone, or stacking floors, or slicing core/perimeter, each changes surface
boundary conditions, window placement, load distribution, and inter-zone heat flow. These prompts
source the right conventions for each.

---

## The prompts

| # | Prompt file | What it decides | Primary mode |
|---|-------------|-----------------|--------------|
| 01 | `01_building_level_single_zone_prompt.md` | How to correctly collapse a multi-floor real building into ONE thermal zone (full-height single zone): internal mass, infiltration, loads, when it's valid. | mode 1 |
| 02 | `02_floor_level_per_floor_prompt.md` | How to stack each floor as one zone: inter-floor surface boundary conditions, ground/middle/top-floor differentiation, party walls. | mode 2 |
| 03 | `03_zone_level_zoning_schema_prompt.md` | The procedural core/perimeter schema on a real footprint for ALL archetypes (incl. residential/tall): perimeter depth, perimeter-zone count, degenerate-footprint handling. | mode 3 |
| 04 | `04_core_perimeter_parameter_differentiation_prompt.md` | Whether/how core vs perimeter zones get different loads / OA / setpoints / WWR. | mode 3 |
| 05 | `05_vertical_aggregation_multiplier_prompt.md` | Zone multiplier vs every-floor — representative-floor modelling, accuracy/cost trade at city scale. | mode 3 |
| 06 | `06_interzone_boundary_conditions_prompt.md` | Surface boundary conditions between stacked/adjacent zones: adiabatic vs heat-transfer floors/ceilings/party walls — for every mode. | all |
| 07 | `07_fenestration_wwr_across_resolution_prompt.md` | Where windows go and what WWR applies as zone count changes (whole-building vs per-floor vs perimeter-only glazing). | all |
| 08 | `08_load_schedule_hvac_conservation_prompt.md` | How archetype-level internal loads, schedules, ventilation, and HVAC are distributed across N zones **without double-counting or losing totals**. | all |
| 09 | `09_LOD_accuracy_and_mode_selection_prompt.md` | The energy-accuracy difference between building/floor/zone resolution — to justify the switch and tell users when each mode is appropriate + expected divergence. | all |
| 10 | `10_computational_cost_scaling_prompt.md` | EnergyPlus runtime/memory per mode at city scale, parallelization, when zone-level is tractable for thousands of buildings. | all |
| 11 | `11_validation_methodology_resolution_prompt.md` | How to prove (or disprove) that higher resolution improves accuracy vs measured benchmarks **without fitting parameters**. | all |
| 12 | `12_shading_solar_context_across_resolution_prompt.md` | How neighbour/self-shading and `Solar Distribution` interact with zone count and height (single-zone averaging loses height-varying shading). | all |
| 13 | `13_daylighting_lighting_controls_across_resolution_prompt.md` | Daylight-responsive lighting controls — only meaningful where perimeter zones exist; the lighting-energy effect of including vs omitting. | all |
| 14 | `14_infiltration_airtightness_scaling_prompt.md` | Infiltration specification basis so building-total leakage is conserved and correctly placed (core = 0) as zones split; stack-effect for tall single-zone. | all |
| 15 | `15_mixed_use_vertical_stacking_prompt.md` | Whether the switch should enable per-floor archetypes (ground retail + residential above) — representable only at `floor`/`zone` resolution. | mode 2/3 |
| 16 | `16_output_aggregation_reporting_provenance_prompt.md` | Rolling multi-zone output back to one building EUI/carbon consistently across modes; EUI denominator; recording `resolution_mode` as provenance. | all |

> Modes 1–2 reuse strategies already in the code; the prompts for them are about **methodological
> correctness and defensibility**, not new geometry. Mode 3 needs the most new method (prompts 03–05).
> Prompts 06–16 apply across all three modes (with 15 specific to floor/zone, which can carry per-floor
> use). Run the prompts most relevant to your study first; 03–05 + 06 + 08 are the load-bearing core
> for getting `zone` mode physically correct.

---

## Shared facts (all prompts assume these)

- **Engine:** EnergyPlus 23.1, one IDF per building, annual 8760-hour run, geomeppy geometry
  (`add_block` with `single_zone`, `one_zone_per_floor`, or native `core/perim`).
- **Floor-to-floor height:** 3.5 m. **Current perimeter depth:** 4.57 m (15 ft).
- **Floor area (EUI denominator):** always `footprint_area_m2 × num_floors`, in every mode.
- **Current zone-level geometry (mode 3 today):** inward buffer of 4.57 m forms the core; the
  annulus splits into 4 perimeter zones; geomeppy stacks `num_floors` identical core/perimeter slices
  (no zone multiplier — every floor modelled). Two hard fallbacks fire and **must be preserved**:
  narrow footprint (core empties / core < 10 m²) → `one_zone_per_floor`; courtyard footprint
  (interior ring) → `one_zone_per_floor` (geomeppy donut core → mismatched vertices → E+ Fatal).
- **Energy standard / vintage:** ASHRAE **90.1-2019**, DOE/PNNL prototype "STD2022" release.
- **Cities → climate zones:** NYC = **4A**, LA = **3B** (coastal **3C** if distinguished), Austin = **2A**.
- **Zero-fitted-parameters philosophy:** OpenUBEM never tunes to pass a benchmark. Any resolution
  choice must be a published convention, not a calibration knob. The validated `auto` baseline (city
  EUI within ±9% measured) must remain the default.

## Conventions for every answer (enforced by each prompt)

1. **Lead with the filled tables**; supporting prose after. Empty / "TBD" cells are failures.
2. Every value/rule carries a **named, dated source** — ASHRAE 90.1-2019 (table/section), DOE/PNNL
   prototype documentation, the EnergyPlus Input-Output / Engineering Reference, or a peer-reviewed
   UBEM paper (author, venue, year). Blogs/vendor pages last resort, labelled.
3. Geometry in **SI** (m, m²); state any IP the source uses (ft, ft²) + conversion.
4. **No fabricated precision.** If a rule is your synthesis, say so. If unpublished, write
   **"GAP — needs manager decision"** + the closest defensible default and its source.
5. **Map onto the exact OpenUBEM archetype IDs** in the roster below.

---

## Archetype roster — use these exact IDs

| Sector | Archetype IDs |
|---|---|
| Office | `SmallOffice`, `SmallOfficeDetailed`, `MediumOffice`, `MediumOfficeDetailed`, `LargeOffice`, `LargeOfficeDetailed` |
| Retail | `RetailStandalone`, `RetailStripmall`, `SuperMarket` |
| Food service | `FullServiceRestaurant`, `QuickServiceRestaurant` |
| Lodging | `SmallHotel`, `LargeHotel` |
| Residential | `MidriseApartment`, `HighriseApartment` |
| Healthcare | `Hospital`, `Outpatient` |
| Education | `PrimarySchool`, `SecondarySchool`, `College` |
| Government | `Courthouse` (no DOE prototype — proxy) |
| Data center | `SmallDataCenterHighITE`, `SmallDataCenterLowITE`, `LargeDataCenterHighITE`, `LargeDataCenterLowITE` |
| Research | `Laboratory` |
| Industrial | `Warehouse` |
| High-rise (custom) | `TallBuilding`, `SuperTallBuilding` |
| Fallback | `OpenUBEMUnknown` (sentinel — proxy) |

> The four archetypes currently **forced** to `one_zone_per_floor` even when large
> (`MidriseApartment`, `HighriseApartment`, `TallBuilding`, `SuperTallBuilding`) are the most
> important residential/tall cases for the mode-3 prompts — they have never taken the core/perimeter path.

---

*OpenUBEM resolution-mode prompt set. Markdown only; binding specs remain `docs/docs_main/`. 2026-06-29.*
