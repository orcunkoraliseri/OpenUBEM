# Deep-Research Prompt L02 — PERIMETER SUBDIVISION rule (what makes "8 apartments" — Option 1 vs Option 2)

> SCOPE GUARD — READ FIRST. This is the **apartment-count crux**. The deliverable is the sourced rule for
> **how the perimeter ring of a footprint is divided into individual rooms/units** — by exterior wall
> edge, by a target room width/area, or by orientation (N/S/E/W) — i.e. exactly what determines whether a
> floor ends up with ~8 apartment zones or ~4. This is the heart of the Option 1 (match the DOE zone
> count) vs Option 2 (split by the building's own edges) decision. It is NOT about the core/corridor
> (Prompt L03) or loads (`../RESULT_04`). If you are writing about anything other than **how the perimeter
> ring is subdivided into zones and the source**, stop and return to the tables. See
> `00_README_layout_mapping_prompt_set.md` for the decision, shared facts, conventions.

---

## What this document is

A fill-in-the-blanks request on the perimeter-subdivision step. geomeppy's native core/perim makes **one
perimeter zone per exterior wall edge** — so a rectangular apartment slab yields 4 perimeter zones, not
the DOE prototype's 8 apartments. We need to know how peer methods control the **number and size** of
perimeter zones on a real polygon, and whether matching the prototype count is standard or unusual. Treat
each cell as a question.

## Role

UBEM geometry research analyst. Trace to: **DOE/PNNL prototype** zone layouts (how many perimeter spaces
each defines and their nominal size), **ASHRAE 90.1-2019 Appendix G Table G3.1** (perimeter thermal-block
rule: one block per orientation, 4.57 m deep), and **tool documentation** (URBANopt corridor/space
templates, CityBES 4-orientation split, CEA, UMI) and any **space-subdivision / floor-plan-generation**
literature. SI + IP.

## Why this matters (so you scope correctly)

If we split by edge (Option 2), a 4-sided apartment building gets 4 perimeter zones — each lumping ~2
apartments — which under-resolves the unit count but is robust. If we target the prototype count (Option
1, ~8 apartments), we must subdivide each facade into multiple rooms by width or area, which needs a rule
for where to cut and breaks on odd shapes. ASHRAE Appendix G itself only mandates **one block per
orientation** (i.e. ~4), so there is real tension between "code thermal-block convention" and "prototype
room count." We need the sourced options and their consequences.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Perimeter-subdivision strategies

| Strategy | Rule | Resulting zone count (rectangle / L-shape) | Used by (tool/standard) | Source |
|---|---|---|---|---|
| One zone per exterior **edge** (geomeppy) |  | 4 / ~6 |  |  |
| One zone per **orientation** (N/S/E/W, ASHRAE Appendix G) |  | 4 / 4 |  |  |
| **Target width** per room (e.g. apartment ≈ X m of facade) |  | ~8 / varies |  |  |
| **Target floor area** per room (e.g. unit ≈ Y m²) |  | ~8 / varies |  |  |
| Fixed prototype **count** (force N zones) |  | N / N (if it fits) |  |  |

### Table 2 — What the DOE prototypes actually specify

| Archetype | Prototype perimeter spaces per floor | Nominal unit/room size (facade width or area) | Corridor present? | Source |
|---|---|---|---|---|
| MidriseApartment | (e.g. 8 apartments) |  | yes (core) |  |
| HighriseApartment |  |  |  |  |
| SmallHotel |  |  |  |  |
| SmallOffice | (4 perimeter) |  | no |  |
| PrimarySchool |  |  |  |  |

### Table 3 — Behaviour of each strategy on real shapes

| Strategy | Rectangle | Long thin slab | L / U shape | Many-sided (curved) footprint | Source |
|---|---|---|---|---|---|
| Per-edge |  |  |  |  |  |
| Per-orientation |  |  |  |  |  |
| Target width/area |  |  |  |  |  |
| Fixed count |  |  |  |  |  |

### Table 4 — Option 1 vs Option 2 trade

| Criterion | Option 1 (match prototype count) | Option 2 (edge/orientation split) | Source |
|---|---|---|---|
| Fidelity to prototype |  |  |  |
| Robustness on irregular shapes |  |  |  |
| Implementation complexity on geomeppy |  |  |  |
| Energy-result impact (if known) | (see L05) | (see L05) |  |

---

## Part C — Synthesis (recommended subdivision rule)

Give: (1) the **single perimeter-subdivision rule** OpenUBEM should adopt — name it (per-edge,
per-orientation, target-width, target-area, or fixed-count) and justify with a published source; (2)
whether that effectively chooses **Option 1 or Option 2**; (3) how it behaves on the hard shapes in Table
3 and the fallback when it can't hit the target; (4) if a target size is recommended, the **sourced
value** (apartment facade width or unit area) per residential/lodging archetype.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C rule.
3. Cite ASHRAE Appendix G thermal-block rule and ≥2 tools' subdivision behaviour.
4. **"Confidence and caveats":** whether "match the prototype count" is even well-defined on arbitrary shapes.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Resolve the "8 apartments vs 4" question** with a sourced rule.
- **State explicitly whether ASHRAE Appendix G supports ~4 (orientation) or ~8 (rooms).**
- **Give target room width/area values** if Option 1 is recommended.
- **No fabricated precision;** flag GAPs. **Stay on topic** — perimeter subdivision only.
