# Deep-Research Prompt 01 — HVAC SYSTEM-TYPE ASSIGNMENT per Archetype (ASHRAE 90.1 App G + PNNL prototypes)

> SCOPE GUARD — READ FIRST. This is a **building-energy modelling** data task. The deliverable is a
> **per-archetype assignment of an HVAC system type**, traceable to ASHRAE 90.1-2019 Appendix G and
> the DOE/PNNL Commercial Prototype Building Models. It is NOT about brand selection, cost,
> controls philosophy, or HVAC design theory in the abstract. If you are writing prose about
> anything other than **which system type each building archetype gets, why (the App G rule), the
> heating fuel, and the air-distribution type**, stop and return to the tables.

---

## What this document is

A fill-in-the-blanks request that assigns, to each of OpenUBEM's 30 archetypes, the **EnergyPlus
HVAC system type** it should be built with in Phase-E. Treat each row as a question; fill it with a
sourced value or an explicit GAP. Lead with the filled tables, then the detail. See
`00_README_phaseE_prompt_set.md` for the shared archetype roster, climate zones, and conventions.

## Role

You are a building-energy-modelling research analyst. Every assignment must trace to a named, dated,
primary source: **ASHRAE Standard 90.1-2019 Appendix G, Table G3.1.1-3 and G3.1.1-4** (baseline HVAC
system type by building type / size / number of floors), the **PNNL prototype documentation** (which
records the *actual* system each prototype uses), and the ASHRAE 90.1-2019 system-type definitions
(Systems 1–13). No fabricated precision.

## Why these numbers (so you scope correctly)

OpenUBEM builds each IDF with EnergyPlus **`HVACTemplate`** objects and runs ExpandObjects. Phase-E
extends the existing per-zone `HVACTemplate:Zone:PTAC` to the correct system per archetype:
- packaged single-zone (`HVACTemplate:Zone:PTAC` / `:PTHP` / `:Unitary` + `HVACTemplate:System:UnitarySystem`),
- packaged/central **VAV** (`HVACTemplate:Zone:VAV` + `HVACTemplate:System:VAV` and, for chilled water,
  `HVACTemplate:Plant:ChilledWaterLoop` + `:Chiller` + `:HotWaterLoop` + `:Boiler`).

The choice of system per archetype is what makes **fans and pumps physical**. We need: the system
type, whether it is **zonal vs central**, whether the fan is **constant-volume vs VAV**, the **heating
fuel** (gas furnace / hot-water boiler / electric resistance / heat pump), and the **App G rule** that
justifies it (so reviewers can check it). Prompt 02 then supplies the efficiency/sizing numbers for
whatever systems you assign here.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Per-archetype HVAC system assignment

One row per archetype ID (use the roster in the README). For each, give BOTH the App G baseline
system AND the system the matching PNNL prototype actually uses (they can differ — note it).

| Archetype ID | DOE/PNNL prototype | App G baseline system (# + name, cite G3.1.1-3/-4) | System the prototype actually uses | Cooling source | Heating source + **fuel** | Air distribution (CV / VAV; zonal / central) | Source |
|---|---|---|---|---|---|---|---|
| SmallOffice | | | | | | | |
| MediumOffice | | | | | | | |
| LargeOffice | | | | | | | |
| RetailStandalone | | | | | | | |
| RetailStripmall | | | | | | | |
| SuperMarket | | | | | | | |
| FullServiceRestaurant | | | | | | | |
| QuickServiceRestaurant | | | | | | | |
| SmallHotel | | | | | | | |
| LargeHotel | | | | | | | |
| MidriseApartment | | | | | | | |
| HighriseApartment | | | | | | | |
| Hospital | | | | | | | |
| Outpatient | | | | | | | |
| PrimarySchool | | | | | | | |
| SecondarySchool | | | | | | | |
| College | | | | | | | |
| Laboratory | | | | | | | |
| Warehouse | | | | | | | |
| SmallDataCenterHighITE | | | | | | | |
| LargeDataCenterHighITE | | | | | | | |

> `SmallOfficeDetailed`/`MediumOfficeDetailed`/`LargeOfficeDetailed` inherit from their base office —
> state that explicitly. `SmallDataCenterLowITE`/`LargeDataCenterLowITE` inherit from their High-ITE
> sibling unless the source says otherwise.

### Table 2 — The ASHRAE 90.1-2019 Appendix G selection logic (the rule behind Table 1)

| Building-type category | #Floors / area breakpoint | Baseline system # | System name | Fan | Heating type | Cite (G3.1.1-3 / -4 row) |
|---|---|---|---|---|---|---|
| Residential | (any per App G) | | | | | |
| Public assembly < / ≥ threshold | | | | | | |
| Nonresidential ≤ 3 floors AND < 25,000 ft² | | | | | | |
| Nonresidential 4–5 floors OR 25,000–150,000 ft² | | | | | | |
| Nonresidential > 5 floors OR > 150,000 ft² | | | | | | |
| Heated-only storage | | | | | | |

State the exact floor/area thresholds in **ft² and m²**, and name the System 1–8 mapping (e.g.
System 3 = PSZ-AC, System 5 = Packaged VAV w/ reheat, System 7 = VAV w/ reheat + chilled-water +
hot-water boiler).

### Table 3 — Special-system archetypes (where App G's generic rule is overridden by use)

| Archetype | System the prototype uses | Why it differs from the generic rule | Key feature for modelling | Source |
|---|---|---|---|---|
| Hospital | | (high OA, constant-volume reheat?) | | |
| Laboratory | | (100% OA? fume-hood exhaust?) | | |
| SuperMarket | | (PSZ + refrigeration interaction) | | |
| Warehouse | | (heated-only? unit heaters? evap cooling?) | | |
| Data center (High/Low ITE) | | (CRAC/CRAH, economizer, no heating?) | | |
| Large/Highrise residential | | (PTAC vs central per prototype) | | |

### Table 4 — Custom / no-prototype archetypes — proxy recommendation

| Archetype | Recommended system proxy | Rationale | Source |
|---|---|---|---|
| TallBuilding | (LargeOffice central VAV + plant?) | | |
| SuperTallBuilding | | | |
| Courthouse | (proxy: Medium/LargeOffice or public-assembly?) | | |
| OpenUBEMUnknown | (conservative proxy?) | | |

---

## Part C — Decision summary (one paragraph)

After the tables, give a short **"system families" synthesis**: collapse the 30 archetypes into the
**minimum set of distinct HVAC system templates** OpenUBEM must implement (e.g. "PTAC", "PSZ-AC gas
furnace", "Packaged VAV + electric/HW reheat", "Built-up VAV + water-cooled chiller + HW boiler",
"CRAC", "Heated-only unit heater"). This drives how many `HVACTemplate:System` paths we code.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C synthesis (the distinct system-template families).
3. Cite App G table rows and the PNNL prototype doc for every assignment.
4. A **"confidence and caveats"** section: where App G baseline vs prototype-actual diverge, and which
   choice you recommend for a UBEM (favor what the PNNL prototype actually runs, since we re-use its
   efficiency/sizing values in Prompt 02).
5. A **reference list** — full citations, dates, URLs.

## Hard requirements

- **One row per archetype ID**, using the exact IDs from the README roster.
- **Name the heating fuel explicitly** (gas furnace vs hot-water boiler vs electric resistance vs heat
  pump) — Phase-E meters gas and electricity separately.
- **Distinguish constant-volume from VAV**, and **zonal from central** — these decide whether pumps and
  central fans exist.
- **Cite the App G table row** for each baseline assignment; **cite the prototype doc** for each
  actual-system note.
- **Flag every no-prototype archetype** (Courthouse, OpenUBEMUnknown) as a proxy decision.
- **Stay on topic.** If it is not a system type, a selection rule, a fuel, or its source, cut it.
