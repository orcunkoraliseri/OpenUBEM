# Deep-Research Prompt L06 — PER-ARCHETYPE DOE LAYOUT catalog (the target zone layout for every archetype)

> SCOPE GUARD — READ FIRST. This is a **reference-catalog** task. The deliverable is, for **every
> OpenUBEM archetype**, the DOE/PNNL prototype's **actual per-floor internal zone layout** — number of
> zones per floor, the zone types/names, whether there is a corridor/core, and the rough adjacency — i.e.
> the **target layout** `zone` mode is trying to reproduce on the real footprint. It is NOT about loads
> (`../RESULT_04`) or how to place the layout (Prompts L01–L04); it is the catalog of WHAT each prototype
> looks like. If you are writing about anything other than **each archetype's prototype zone makeup and
> the source**, stop and return to the table. See `00_README_layout_mapping_prompt_set.md` for shared
> facts, roster, conventions.

---

## What this document is

A fill-in-the-blanks catalog. To apply "the DOE layout" per archetype, OpenUBEM needs the target zone
makeup for each of the 30 archetype IDs, sourced from the DOE/PNNL Commercial Prototype Building Models
(and Residential prototypes). This single reference drives the per-archetype zone-mode scheme. Treat each
row as a lookup; fill from the prototype documentation or flag a GAP/proxy.

## Role

Building-prototype documentation analyst. Trace every layout to the **DOE/PNNL Commercial Prototype
Building Models (STD2022 release)** documentation and IDFs, and the **PNNL Residential prototype**
specifications. Where an archetype has no DOE prototype (custom/proxy), say so and name the closest proxy.
SI for any dimensions.

## Why this matters (so you scope correctly)

`../RESULT_03` gave a one-line zoning verdict per archetype; this prompt produces the **detailed target
layout** (counts, types, corridor presence) that the geometry algorithm (L01–L04) must aim at and that the
load builder (`../RESULT_04`) maps space-types onto. Without it, "follow the DOE layout" is undefined per
archetype. This catalog is the binding reference.

---

## REQUIRED OUTPUT TABLE — fill every row (all 30 IDs)

### Table 1 — DOE prototype per-floor zone layout, per archetype

| Archetype ID | Zones per floor (prototype) | Zone types / names | Corridor or core type | Reduces to (core+perim / units+corridor / single / functional-split) | DOE prototype? (Y/proxy) | Source |
|---|---|---|---|---|---|---|
| SmallOffice |  |  |  |  |  |  |
| SmallOfficeDetailed |  |  |  |  |  |  |
| MediumOffice |  |  |  |  |  |  |
| MediumOfficeDetailed |  |  |  |  |  |  |
| LargeOffice |  |  |  |  |  |  |
| LargeOfficeDetailed |  |  |  |  |  |  |
| RetailStandalone |  |  |  |  |  |  |
| RetailStripmall |  |  |  |  |  |  |
| SuperMarket |  |  |  |  |  |  |
| FullServiceRestaurant |  |  |  |  |  |  |
| QuickServiceRestaurant |  |  |  |  |  |  |
| SmallHotel |  |  |  |  |  |  |
| LargeHotel |  |  |  |  |  |  |
| MidriseApartment | (e.g. 9: 8 apt + corridor) |  | central corridor | units+corridor | Y |  |
| HighriseApartment |  |  |  |  |  |  |
| Hospital |  |  |  |  |  |  |
| Outpatient |  |  |  |  |  |  |
| PrimarySchool |  |  |  |  |  |  |
| SecondarySchool |  |  |  |  |  |  |
| College |  |  |  |  | proxy |  |
| Courthouse |  |  |  |  | proxy |  |
| Laboratory |  |  |  |  | proxy |  |
| SmallDataCenterHighITE |  |  |  |  |  |  |
| SmallDataCenterLowITE |  |  |  |  |  |  |
| LargeDataCenterHighITE |  |  |  |  |  |  |
| LargeDataCenterLowITE |  |  |  |  |  |  |
| Warehouse |  |  |  | single |  |  |
| TallBuilding |  |  |  |  | proxy/custom |  |
| SuperTallBuilding |  |  |  |  | proxy/custom |  |
| OpenUBEMUnknown |  |  |  |  | sentinel |  |

### Table 2 — Vertical variation (does the layout change by floor?)

| Archetype | Ground floor differs? | Top floor differs? | Repeating mid-floor? | Source |
|---|---|---|---|---|
| LargeOffice (basement/IT) |  |  |  |  |
| MidriseApartment |  |  |  |  |
| LargeHotel (ground retail/lobby) |  |  |  |  |
| SmallOffice |  |  |  |  |

---

## Part C — Synthesis (the binding per-archetype target)

Give: (1) the **catalog itself** as the deliverable (Table 1 complete for all 30 IDs); (2) a grouping of
archetypes into the four reduction families (core+perim / units+corridor / single-zone / functional-split)
so OpenUBEM can route each archetype to a geometry strategy; (3) flag every archetype with **no DOE
prototype** and the proxy chosen; (4) note any archetype whose layout **varies by floor** (ground/top),
which the every-floor model must respect.

## Output format (follow exactly)

1. **Lead with Tables 1–2 fully populated** (every archetype ID present).
2. Then Part C grouping + proxy list.
3. Cite the DOE/PNNL prototype docs (and residential prototype source) per row family.
4. **"Confidence and caveats":** which rows are proxies/synthesis vs documented.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Every one of the 30 archetype IDs appears** in Table 1 with a reduction family.
- **Flag proxies/GAPs explicitly** (College, Courthouse, Laboratory, Tall/SuperTall, Unknown).
- **State the per-floor variation** where it exists.
- **No fabricated precision;** flag GAPs. **Stay on topic** — prototype zone layouts only.
