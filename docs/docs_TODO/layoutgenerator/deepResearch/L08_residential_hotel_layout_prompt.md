# Deep-Research Prompt L08 — RESIDENTIAL & HOTEL LAYOUT SPECIFICS (apartment dwelling units, hotel guest rooms on real footprints)

> SCOPE GUARD — READ FIRST. This prompt details the **residential and hotel** branch of the generator:
> how to lay out MidriseApartment / HighriseApartment dwelling units and SmallHotel / LargeHotel guest
> rooms onto L / U / O / irregular footprints using the corridor+packing method (`L06`) and the DOE
> templates (`L07`). Deliver the archetype-specific packing rules, unit mix, and thermal-zone reduction.
> Do NOT re-derive the generic corridor design rules (that's `L06`) or the DOE template values (that's
> `L07`) — *apply* them here. Offices/schools are `L09`; hospitals/large hotels' department logic is
> `L10`. See `00_README_layoutgenerator_prompt_set.md` for shared facts.

---

## What this document is

The residential/hotel playbook. These archetypes are the user's motivating case ("apply midrise DOE
building floor to L-shape … put corridor at the center and add apartments to the corners and edges") and
are currently **forced to `one_zone_per_floor`** in OpenUBEM — so moving them to corridor+units room-level
is both the biggest change and the most defensible (a residential floor genuinely *is* a corridor with
units). This prompt establishes the concrete packing rules per residential/hotel archetype and the
thermal-zone count the layout reduces to.

## Role

Multifamily / hospitality space-planning research analyst. Ground the layouts in the DOE MidriseApartment/
SmallHotel/LargeHotel prototype documentation, multifamily/hotel design standards (Graphic Standards,
Neufert, Time-Saver Standards for Building Types, hotel-brand design guides where public), and any UBEM
paper that models apartment/hotel floors with corridor+unit zoning (incl. İşeri et al.'s zone-level
apartment case). Give dimensions and unit mixes, cited.

## Why this matters (so you scope correctly)

Residential is ~half of many city stocks, so getting the apartment layout right dominates fleet accuracy.
The manager needs the exact packing rules: unit depth, corridor placement per wing, how corner units are
formed on an L, whether north/south units become separate perimeter zones (orientation matters for solar),
and whether repeated identical units collapse to one zone + multiplier. This is what makes the residential
branch of `layoutGenerator.py` both correct and cheap.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Residential/hotel unit modules & packing

| Archetype | Unit/room depth (corridor→façade) | Unit width (bay) | Corridor type & width | Units per floor (typical) | Source |
|---|---|---|---|---|---|
| MidriseApartment |  |  | double-loaded |  |  |
| HighriseApartment |  |  |  |  |  |
| SmallHotel |  |  |  |  |  |
| LargeHotel |  |  |  |  |  |
| Dormitory (if relevant) |  |  |  |  |  |

### Table 2 — Packing onto non-rectangular footprints

| Footprint | Corridor path | Where units go | Corner-unit treatment | Left-over / un-packable area handling | Source |
|---|---|---|---|---|---|
| Bar / slab |  |  |  |  |  |
| L-shape |  |  |  |  |  |
| U-shape |  |  |  |  |  |
| O / courtyard |  | units on outer ring (inner ring?) |  |  |  |
| Irregular |  |  |  |  |  |

### Table 3 — Thermal-zone reduction (how many zones per floor)

| Archetype | Architectural room count/floor | Recommended thermal zones/floor for BEM | Merge rule (by orientation? by unit type?) | Zone multiplier used? | Source |
|---|---|---|---|---|---|
| MidriseApartment |  |  |  |  |  |
| SmallHotel |  |  |  |  |  |
| LargeHotel |  |  |  |  |  |

### Table 4 — Fit to OpenUBEM

| Question | Answer + source |
|---|---|
| Is moving MidriseApartment from `one_zone_per_floor` to corridor+units defensible and beneficial? |  |
| Should orientation-split perimeter units (N/S/E/W) be separate zones (solar) or merged? |  |
| Corridor: separate semi-conditioned zone or lumped? (matches DOE prototype?) |  |
| For a courtyard apartment block, do inner-ring units matter (they see the court, not the street)? |  |

---

## Part C — Synthesis (the residential/hotel branch spec)

Give: (1) the **concrete packing algorithm per residential/hotel archetype** — corridor path, unit module,
corner rule, cited dimensions; (2) the **thermal-zone reduction rule** (per-unit vs. orientation-merged +
multiplier) and the resulting zones/floor; (3) an explicit recommendation on **whether to un-force
residential from per-floor** into corridor+units, with the accuracy/cost trade-off (cross-ref `L14`);
(4) the courtyard-apartment inner-ring decision. Every dimension cited or flagged GAP.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C branch spec.
3. Cite DOE prototype or design-standard for every dimension/mix.
4. **"Confidence and caveats":** which archetype's unit dimensions are least documented.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Every dimension cited** (DOE prototype / design standard); flag invented values GAP.
- **Explicitly recommend the zones/floor count** and the orientation-merge rule.
- **Address the courtyard case** — OpenUBEM's current hard-fail shape.
- **No fabricated precision;** flag GAPs. **Stay on topic** — residential/hotel layout only; generic
  corridor rules are `L06`, offices/schools `L09`, hospital/large-complex `L10`.
