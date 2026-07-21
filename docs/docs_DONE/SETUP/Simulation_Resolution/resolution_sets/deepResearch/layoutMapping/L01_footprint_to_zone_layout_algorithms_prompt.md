# Deep-Research Prompt L01 — FOOTPRINT → ZONE-LAYOUT algorithms (how peer tools actually auto-zone real footprints)

> SCOPE GUARD — READ FIRST. This is a **methods-comparison** task. The deliverable is a sourced,
> side-by-side account of the **actual algorithms** UBEM tools use to turn an **arbitrary real building
> footprint** into a set of thermal zones resembling a building-type prototype layout — the perimeter
> split rule, how the core is formed, how (or whether) the prototype zone *count* is reproduced, how
> residential corridors are handled, and how irregular shapes are survived. It is NOT about loads,
> schedules, or HVAC (covered in `../RESULT_04/08`); it is purely the **geometry/layout generation**.
> If you are writing about anything other than **how a footprint is divided into zones and the source**,
> stop and return to the tables. See `00_README_layout_mapping_prompt_set.md` for the decision, shared
> facts, roster, conventions.

---

## What this document is

A fill-in-the-blanks comparison. OpenUBEM must, in `zone` mode, divide each floor of a building's **real
OSM footprint** into the archetype's DOE-style zones inside one IDF (e.g. apartment = units + corridor;
office = core + perimeter). We need to know **how the established tools do this on arbitrary polygons** so
we can adopt a published method rather than invent one. Treat each cell as a question; fill with a sourced
method or a GAP.

## Role

UBEM geometry/zoning research analyst. Trace every method to the tool's own documentation or a
peer-reviewed description: **URBANopt/OpenStudio** geometry-and-zoning measures, **CityBES** (Hong et al.),
**AutoBEM/AutoBEM-Energy** (New et al., ORNL), **UMI / shoeboxer** (Dogan & Reinhart; Reinhart et al.),
**City Energy Analyst (CEA)** (Fonseca et al.), and **geomeppy** native core/perim. SI.

## Why this matters (so you scope correctly)

The footprint→zone step is the single biggest unknown in OpenUBEM's `zone` mode. geomeppy's native
core/perim splits the perimeter into one zone per wall edge and offsets a core — robust, but it does NOT
reproduce a prototype's fixed zone count (8 apartments) and has no concept of a corridor. We need to know
which tools go further (target zone counts, double-loaded corridors, room subdivision) and exactly how,
versus which stay at generic core/perimeter — and the robustness cost of each.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Auto-zoning algorithm per tool

| Tool | Core-forming method (offset / straight-skeleton / raster / shoebox) | Perimeter split rule | Reproduces prototype zone COUNT? | Real footprint or bbox/simplified? | Source |
|---|---|---|---|---|---|
| URBANopt / OpenStudio |  |  |  |  |  |
| CityBES |  |  |  |  |  |
| AutoBEM |  |  |  |  |  |
| UMI / shoeboxer |  |  |  |  |  |
| City Energy Analyst (CEA) |  |  |  |  |  |
| geomeppy (native) |  | one zone per exterior edge | No (edge-driven) | Real |  |

### Table 2 — Residential / corridor capability per tool

| Tool | Generates a corridor/core distinct from units? | How the corridor is placed on a real polygon | Double-loaded-corridor template? | Source |
|---|---|---|---|---|
| URBANopt / OpenStudio |  |  |  |  |
| CityBES |  |  |  |  |
| AutoBEM |  |  |  |  |
| UMI |  |  |  |  |
| CEA |  |  |  |  |

### Table 3 — Robustness on irregular shapes

| Tool | Behaviour on L/U/T shapes | Behaviour on courtyard (donut) | Fallback when detailed layout fails | Source |
|---|---|---|---|---|
| URBANopt / OpenStudio |  |  |  |  |
| CityBES |  |  |  |  |
| AutoBEM |  |  |  |  |
| UMI |  |  |  |  |
| CEA |  |  |  |  |

### Table 4 — Option-1 vs Option-2 classification

| Tool | Effectively Option 1 (match prototype count) or Option 2 (robust generic) | Evidence | Source |
|---|---|---|---|
| URBANopt / OpenStudio |  |  |  |
| CityBES |  |  |  |
| AutoBEM |  |  |  |
| UMI |  |  |  |
| CEA |  |  |  |
| geomeppy | Option 2 (edge-split) |  |  |

---

## Part C — Synthesis (recommended method for OpenUBEM)

Give: (1) which tool's footprint→zone algorithm is the **best fit for OpenUBEM** (real footprint, geomeppy
backbone, thousands of buildings) and why; (2) whether the evidence points to **Option 1 or Option 2** as
standard practice; (3) the **concrete algorithm** OpenUBEM should adopt, step by step, on a real polygon,
including how the core/corridor is formed and how the perimeter is divided. Name the published source for
each step. Flag any step that has no precedent as a GAP.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C recommended method.
3. Cite each tool's documentation/paper explicitly.
4. **"Confidence and caveats":** the method most likely to break on real GIS geometry, and why.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Compare ≥5 tools** (URBANopt, CityBES, AutoBEM, UMI, CEA) plus geomeppy.
- **Say explicitly, per tool, Option 1 or Option 2**, with evidence.
- **Recommend one concrete algorithm** for OpenUBEM on a real footprint.
- **No fabricated precision;** flag GAPs. **Stay on topic** — footprint→zone geometry only.
