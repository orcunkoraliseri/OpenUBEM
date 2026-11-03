# Deep-Research Prompt L03 — DOUBLE-LOADED CORRIDOR & residential/hotel layout on real footprints

> SCOPE GUARD — READ FIRST. This is a **residential/lodging layout-generation** task. The deliverable is
> how the **units-along-a-central-corridor** layout (apartments or hotel guest rooms wrapping a hallway
> "core") is generated or approximated on an **arbitrary real footprint**, where the corridor is placed,
> and the building-code constraints that force it (egress, daylight/ventilation to habitable rooms). It is
> NOT about residential loads/ventilation values (`../RESULT_04` already gives corridor vs dwelling LPD/OA)
> and NOT about the generic perimeter split (Prompt L02). If you are writing about anything other than
> **how the corridor + units layout is placed on a real polygon and the source**, stop and return to the
> tables. See `00_README_layout_mapping_prompt_set.md` for the decision, shared facts, conventions.

---

## What this document is

A fill-in-the-blanks request on corridor/unit layout geometry. The DOE MidriseApartment is a
**double-loaded corridor**: a central hallway with apartments on both sides (≈8 units + 1 corridor per
floor). OpenUBEM's `zone` mode must reproduce "corridor core + dwelling perimeter" on the real OSM
footprint. We need the sourced method for placing the corridor and arranging units when the footprint is
not the DOE rectangle. Treat each cell as a question; fill with a sourced method or a GAP.

## Role

UBEM geometry research analyst. Trace to: **URBANopt/OpenStudio** double-loaded-corridor and
space-type templates, **PNNL Mid/High-rise Apartment & Hotel prototype** specifications, **building-code**
daylight/egress requirements driving the typology (IBC §1205 / habitable-space natural light), and any
**automated floor-plan / corridor-generation** literature (straight-skeleton spine, medial axis). SI.

## Why this matters (so you scope correctly)

`../RESULT_03` set the **Core-as-Corridor** rule (geometry uses core/perimeter; the core is *labelled* a
corridor with corridor loads). But a geomeppy inward-offset "core" is a central **blob**, not a linear
**hallway** — and for a long thin slab the real corridor is a spine down the middle, not an offset ring.
We need to know whether peers (a) accept the offset-core-as-corridor approximation, or (b) generate a true
linear corridor (medial axis / straight skeleton) with units on each side, and what that costs in
robustness. This decides how literally OpenUBEM reproduces residential layout.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Corridor placement methods on a real footprint

| Method | How the corridor geometry is derived | Works on rectangle? | Works on L/thin/curved? | Used by | Source |
|---|---|---|---|---|---|
| Inward-offset **core blob** = corridor (geomeppy core/perim) |  |  |  |  |  |
| **Medial axis / straight-skeleton spine** corridor |  |  |  |  |  |
| **Fixed-width central strip** (e.g. 1.5–2.4 m hallway) |  |  |  |  |  |
| Template **double-loaded corridor** scaled to footprint |  |  |  |  |  |

### Table 2 — Unit arrangement around the corridor

| Item | Rule | Source |
|---|---|---|
| Apartments per floor (DOE Midrise/Highrise) |  |  |
| Hotel guest rooms per floor (DOE Small/Large Hotel) |  |  |
| Typical unit facade width / depth |  |  |
| How units map onto perimeter zones (1 zone/unit vs lumped) |  |  |

### Table 3 — Code & physical constraints that force the typology

| Constraint | Requirement | Implication for zoning | Source |
|---|---|---|---|
| Daylight/ventilation to habitable rooms (IBC §1205 or equiv.) |  | units must be on the perimeter |  |
| Egress / corridor width |  | corridor is interior, low occupancy |  |
| Windowless-core prohibition for dwellings |  | core ≠ apartment loads |  |

### Table 4 — How peer tools handle residential corridors

| Tool | Corridor generated? | Method | Residential applied at city scale? | Source |
|---|---|---|---|---|
| URBANopt / OpenStudio |  |  |  |  |
| CityBES |  |  |  |  |
| UMI |  |  |  |  |
| CEA |  |  |  |  |

---

## Part C — Synthesis (residential layout rule)

Give: (1) whether OpenUBEM should keep the **offset-core-as-corridor approximation** (`../RESULT_03`) or
generate a **true linear corridor** (medial axis / central strip), with the sourced trade-off; (2) the
rule for arranging units (1 zone per unit vs lumped perimeter), and whether to target the DOE unit count
(Option 1) or split by edges/orientation (Option 2); (3) the corridor width/placement values to use; (4)
the fallback when no sensible corridor fits (e.g. tiny or thin footprint → single zone). Apply to
MidriseApartment, HighriseApartment, SmallHotel, LargeHotel.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C residential layout rule.
3. Cite URBANopt corridor templates, PNNL apartment/hotel prototypes, and the code constraint.
4. **"Confidence and caveats":** where the corridor approximation most distorts results, and on which shapes it fails.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Decide offset-core-as-corridor vs true linear corridor**, sourced.
- **Give corridor width + unit-arrangement rule**, mapped to the 4 residential/lodging archetype IDs.
- **State the fallback** when no corridor fits.
- **No fabricated precision;** flag GAPs. **Stay on topic** — corridor/unit layout geometry only.
