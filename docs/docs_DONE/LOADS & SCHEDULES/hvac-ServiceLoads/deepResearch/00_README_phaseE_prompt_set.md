# Phase-E — HVAC + Service-Loads Deep-Research Prompt Set (INDEX)

> READ FIRST. This folder holds a SET of standalone deep-research prompts. Each gathers the
> **sourced numeric parameters** needed to instantiate one family of EnergyPlus objects for
> OpenUBEM **Phase-E (full physical realism)**. Run each prompt in your deep-research tool; save
> the answer beside it as `RESULT_<nn>_<slug>.md`. The manager then audits, fills any GAP cells
> with ASHRAE 90.1 defaults, and writes `PLAN_phaseE_full_realism.md`. The prompts are written
> to be run **independently** (each is self-contained), in any order.

---

## What Phase-E is (so every researcher scopes correctly)

OpenUBEM is an Urban Building Energy Model that generates **one EnergyPlus IDF per building** for
neighbourhoods of thousands of buildings, mapping each building to one of **30 archetypes** and an
ASHRAE climate zone. Today it conditions every zone with a packaged **PTAC** and *estimates* the
unmodelled service loads (DHW, cooking, refrigeration, pumps) in a reporting-layer post-process.

**Phase-E replaces that with full physical modelling:** archetype-appropriate **central HVAC** (so
fans and pumps become physically simulated), plus **DHW, cooking, and refrigeration** as real IDF
objects — then a full re-simulation of the 12-cell / 8,160-building validation matrix (New York,
Los Angeles, Austin) and a re-score against measured benchmarks. **Integration rule:** for every
end-use moved into the simulation, the matching reconstruction term is removed (no double-count).

These prompts produce the numbers that parameterize that build.

---

## The five prompts and the EnergyPlus objects they feed

| # | Prompt file | Feeds these EnergyPlus objects |
|---|-------------|--------------------------------|
| 01 | `01_hvac_system_assignment_prompt.md` | Per-archetype **system-type selection** (`HVACTemplate:Zone:*` + `HVACTemplate:System:*`) |
| 02 | `02_hvac_plant_airside_parameters_prompt.md` | Chiller/boiler efficiency, **pumps**, **fans**, loop temps, economizer (`HVACTemplate:Plant:Chiller`/`:Boiler`, fan & OA fields) |
| 03 | `03_service_water_heating_DHW_prompt.md` | `WaterHeater:Mixed`, `WaterUse:Equipment`, `WaterUse:Connections` |
| 04 | `04_cooking_kitchen_loads_prompt.md` | `OtherEquipment` (gas) / `ElectricEquipment` + kitchen exhaust / makeup-air |
| 05 | `05_refrigeration_prompt.md` | `Refrigeration:Case` / `:WalkIn` / `:CompressorRack` / `:System` + **zone case credit** |

---

## Shared facts (all five prompts assume these)

- **Energy standard / baseline vintage:** ASHRAE **90.1-2019**, as implemented in the DOE/PNNL
  Commercial Prototype Building Models **"STD2022" release** (this is the release OpenUBEM already
  drew its envelope and cooling-COP values from). Where a value differs for older stock, note the
  **DOERef Pre-1980 / Post-1980** delta as *optional vintage-dependence* and flag it for the manager.
- **Cities → climate zones:** New York City = ASHRAE **4A**, Los Angeles = **3B** (use **3C** for the
  immediate coast if the source distinguishes it), Austin = **2A**. Give **climate-independent**
  values where the standard is climate-independent (most equipment efficiencies, system selection);
  break out **by zone (2A / 3B / 4A)** only where it genuinely differs (economizer requirement,
  energy-recovery requirement, design conditions).
- **Existing anchor file:** `openubem/data/loads/hvac_cop_by_archetype.json` already carries, per
  archetype, a cooling COP, heating-coil type + efficiency, a `central_plant` boolean, and the
  `source_prototype` IDF name (STD2022, "Buffalo" CZ). Prompt **02 extends this same file**; confirm
  or update its values where your source differs and cite the difference.

## Conventions for every answer (enforced by each prompt)

1. **Lead with the filled tables**; supporting prose after. Empty / "TBD" cells are failures.
2. Every numeric cell carries a **named, dated source** — PNNL prototype documentation (report +
   table/section + year), an ASHRAE 90.1-2019 table number, ASHRAE Handbook (Fundamentals /
   Applications) chapter, or the EnergyPlus Input-Output Reference / Engineering Reference. Blogs and
   vendor pages only as a last resort, labelled as such.
3. Give values in **SI** (W, W/m², m³/s, L/s, L, °C, kPa, kW/(L/s)) **and** the **IP** the source
   uses (Btu/h, cfm, gpm, °F, kW/ton, in. w.c.), so transcription is independently checkable.
4. **No fabricated precision.** If a value is interpolated, escalated, or downscaled, show the
   arithmetic. If it is not published, write **"GAP — needs manager decision"** and give the closest
   defensible default + its source.
5. **Map every value onto the exact OpenUBEM archetype IDs** in the roster below.

---

## Archetype roster — use these exact IDs (the JSON keys results must slot into)

| Sector | Archetype IDs | DOE/PNNL prototype basis |
|---|---|---|
| Office | `SmallOffice`, `SmallOfficeDetailed`, `MediumOffice`, `MediumOfficeDetailed`, `LargeOffice`, `LargeOfficeDetailed` | OfficeSmall / OfficeMedium / OfficeLarge |
| Retail | `RetailStandalone`, `RetailStripmall`, `SuperMarket` | RetailStandalone / RetailStripmall / Supermarket (DOE Commercial Reference) |
| Food service | `FullServiceRestaurant`, `QuickServiceRestaurant` | RestaurantSitDown / RestaurantFastFood |
| Lodging | `SmallHotel`, `LargeHotel` | HotelSmall / HotelLarge |
| Residential | `MidriseApartment`, `HighriseApartment` | ApartmentMidRise / ApartmentHighRise |
| Healthcare | `Hospital`, `Outpatient` | Hospital / OutpatientHealthCare |
| Education | `PrimarySchool`, `SecondarySchool`, `College` | SchoolPrimary / SchoolSecondary / (College — 90.1-2019 set) |
| Government | `Courthouse` | **no DOE prototype — proxy decision needed** |
| Data center | `SmallDataCenterHighITE`, `SmallDataCenterLowITE`, `LargeDataCenterHighITE`, `LargeDataCenterLowITE` | DataCenter High/Low ITE |
| Research | `Laboratory` | Laboratory (90.1-2019 set) |
| Industrial | `Warehouse` | Warehouse |
| High-rise (custom) | `TallBuilding`, `SuperTallBuilding` | map to OfficeLarge central-plant system |
| Fallback | `OpenUBEMUnknown` | sentinel — proxy decision needed |

> `*Detailed` office variants inherit from their base office. `Courthouse` and `OpenUBEMUnknown`
> have no native prototype — each prompt asks for an explicit proxy recommendation.

---

*OpenUBEM Phase-E prompt set. Markdown only; binding design specs remain `docs/docs_main/`. 2026-06-26.*
