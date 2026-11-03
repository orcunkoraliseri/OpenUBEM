# Deep-Research Prompt 03 — ZONE-LEVEL core/perimeter zoning schema on a real footprint (all archetypes)

> SCOPE GUARD — READ FIRST. This is a **geometry/zoning** task. The deliverable is the **procedural
> rule set** for slicing a building's real footprint into core + perimeter thermal zones at "zone
> level," for **every** archetype including residential and tall — plus how to handle degenerate
> footprints. It is NOT about per-zone load values (Prompt 04), vertical stacking (Prompt 05), or
> architectural room layout. If you are writing about anything other than **how to procedurally cut a
> footprint into core/perimeter zones and the source**, stop and return to the tables. See
> `00_README_resolution_prompt_set.md` for modes, roster, conventions.

---

## What this document is

A fill-in-the-blanks request defining the **core/perimeter zoning schema** OpenUBEM's `zone` mode
applies to every building. OpenUBEM cuts zones from the **real OSM footprint** via an inward buffer
(B1), not a DOE rectangle. Today this runs only for multi-floor commercial ≥500 m². This prompt
sources the rules to extend it to **all** archetypes — most importantly residential (apartments) and
tall buildings, which DOE models very differently from generic core/perimeter. Treat each cell as a
question; fill it with a sourced value or a GAP.

## Role

Building-energy-modelling research analyst. Trace every rule to: **ASHRAE 90.1-2019 Appendix G** (the
core/perimeter convention and the **perimeter depth**), the **DOE/PNNL prototype** documentation (the
*actual* zoning each prototype uses — apartment units + corridor for residential, 5-zone-per-floor for
offices), the **EnergyPlus I/O Reference** (`Building`, `Zone`, geometry), and **peer-reviewed UBEM
auto-zoning literature** (CityBES, AutoBEM, URBANopt, UMI, City Energy Analyst — how each
automatically zones footprints at scale). SI; state IP + convert.

## Why these rules (so you scope correctly)

OpenUBEM's `build_zones` buffers the footprint inward by a **perimeter depth** to form the core, then
splits the annulus into perimeter zones and stacks per floor. The choices that decide the result are:
the **perimeter depth**, whether **residential/tall** archetypes should use core/perimeter at all
(DOE prototypes do NOT), how many **perimeter zones** the annulus becomes and how they map to
orientation on an irregular polygon, the **core-existence test**, and how to handle **degenerate
footprints** (too narrow to buffer, courtyards). We need sourced answers so the extension is a
published convention, not an invention.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Core/perimeter geometry convention

| Parameter | Value (SI / IP) | Source (90.1 App G § / table, or prototype doc) |
|---|---|---|
| Perimeter depth (zone thickness from façade inward) | (confirm 4.57 m / 15 ft) | |
| Number of perimeter zones per floor (4 by orientation? more for long façades?) | | |
| How perimeter is split by orientation on a real (non-rectangular) polygon | | |
| Core-existence test (min core area before core is dropped) | | |
| Does perimeter depth vary by archetype / climate / use? | | |

### Table 2 — Per-archetype zone-level scheme (does core/perimeter even apply?)

For each archetype, state DOE's actual per-floor zoning and what OpenUBEM's `zone` mode should do
(B1 generic core/perimeter is the default — confirm or flag where it is a poor proxy).

| Archetype | DOE prototype's ACTUAL per-floor zoning | Is generic core+perimeter a defensible proxy? (Y / N / caveat) | Recommended `zone`-mode scheme | Source |
|---|---|---|---|---|
| SmallOffice | (core + 4 perim?) | | | |
| MediumOffice | | | | |
| LargeOffice | | | | |
| RetailStandalone | | | | |
| RetailStripmall | | | | |
| SuperMarket | | | | |
| FullServiceRestaurant | | | | |
| QuickServiceRestaurant | | | | |
| SmallHotel | | | | |
| LargeHotel | | | | |
| **MidriseApartment** | (units + corridor — NOT core/perim?) | | | |
| **HighriseApartment** | | | | |
| Hospital | | | | |
| Outpatient | | | | |
| PrimarySchool | | | | |
| SecondarySchool | | | | |
| College | | | | |
| Laboratory | | | | |
| Warehouse | (single zone? heated-only?) | | | |
| SmallDataCenterHighITE / LowITE | | | | |
| LargeDataCenterHighITE / LowITE | | | | |
| **TallBuilding** | | | | |
| **SuperTallBuilding** | | | | |
| Courthouse | (proxy) | | | |
| OpenUBEMUnknown | (proxy) | | | |

> The bolded residential/tall rows are the crux: DOE apartment prototypes zone by **dwelling unit +
> corridor**, not core/perimeter. State clearly whether B1 generic core/perimeter is an acceptable
> UBEM-scale simplification for them (cite a tool that does this), or whether a different procedural
> scheme (perimeter-only "ring," no conditioned core) is better.

### Table 3 — Degenerate-footprint handling (the fallbacks)

OpenUBEM today reverts narrow and courtyard footprints to `one_zone_per_floor`. Confirm this is the
right convention; source any better practice.

| Case | OpenUBEM current behaviour | Recommended behaviour + rule | Source |
|---|---|---|---|
| Footprint too narrow to buffer (core empties / core < 10 m²) | revert to one_zone_per_floor | | |
| Footprint with interior courtyard (ring/hole) | revert to one_zone_per_floor | | |
| Very small total footprint (e.g. < 100 m²) | core/perim attempted | | |
| Single-floor building in `zone` mode | core/perim with num_floors=1 | | |
| L-/U-/T-shaped real footprint | inward buffer (shape preserved) | | |

### Table 4 — Precedent: how peer UBEM tools auto-zone real footprints

| Tool / paper | Auto-zoning method (core/perim? perimeter depth? real footprint or bbox?) | Applies to residential? | Source |
|---|---|---|---|
| CityBES | | | |
| AutoBEM / AutoBEM-Energy | | | |
| URBANopt / OpenStudio | | | |
| UMI / shoeboxer | | | |
| City Energy Analyst (CEA) | | | |
| Other | | | |

---

## Part C — Synthesis (rule block + verdict)

Give: (1) the **minimum sourced rule set** OpenUBEM should code for `zone`-mode zoning — perimeter
depth, perimeter-zone count/orientation rule, core-existence test, the residential/tall decision; and
(2) an explicit **accept-or-revise** verdict on OpenUBEM's current implementation (generic
core/perimeter on the real footprint, narrow/courtyard fallbacks) — is it defensible for a published
UBEM, and if not, the smallest change that makes it so.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated** (every archetype in Table 2).
2. Then Part C synthesis + accept/revise verdict.
3. Cite ASHRAE App G for perimeter depth, prototype docs for actual zoning, ≥2 UBEM tools for the
   "core/perimeter on a real footprint at scale" precedent.
4. **"Confidence and caveats":** where generic core/perimeter is weakest (residential), and your
   recommended default given the zero-fitted-parameters rule.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Every archetype in Table 2 gets a verdict** on whether generic core/perimeter applies.
- **The residential/tall decision is mandatory and explicit** — the load-bearing question.
- **Give the perimeter depth with its 90.1 App G citation.**
- **Cite ≥2 peer UBEM tools** that auto-zone real footprints into core/perimeter at scale.
- **No fabricated precision;** flag GAPs with a defensible default.
- **Stay on topic.** If it is not a zoning geometry rule or its source, cut it.
