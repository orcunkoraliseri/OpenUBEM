# Deep-Research Prompt 04 — CORE vs PERIMETER parameter differentiation (loads, OA, setpoints, WWR, HVAC terminal)

> SCOPE GUARD — READ FIRST. This is a **numeric zone-parameter** task. The deliverable is, for
> zone-level models, **whether and how core and perimeter zones receive different inputs** — internal
> loads, ventilation, setpoints, window-to-wall, and HVAC terminal — versus OpenUBEM's current
> practice of applying the **archetype-level** density uniformly to every zone. It is NOT about the
> zoning geometry (Prompt 03). If you are writing about anything other than **a per-zone parameter
> value, whether it differs core-vs-perimeter, and the source**, stop and return to the tables. See
> `00_README_resolution_prompt_set.md` for modes, roster, conventions.

---

## What this document is

A fill-in-the-blanks request resolving one question: when a floor is split into core + perimeter, do
the zones get the **same** archetype densities (OpenUBEM today) or **differentiated** values (as the
DOE prototypes assign)? If differentiated, by how much, per source. Treat each cell as a question.

## Role

Building-energy-modelling research analyst. Trace every value to: the **DOE/PNNL prototype IDFs and
documentation** (which carry per-zone LPD/EPD/occupancy/OA and per-zone thermostat schedules),
**ASHRAE 90.1-2019 §6 / Std 62.1-2019** (ventilation rates by space type), and the **EnergyPlus I/O
Reference** (`People`, `Lights`, `ElectricEquipment`, `DesignSpecification:OutdoorAir`,
`ZoneControl:Thermostat`). SI + IP. No fabricated precision.

## Why this matters (so you scope correctly)

Perimeter zones are envelope-driven (solar, conduction, daylight); cores are internally-load-dominated
(no exterior exposure, often higher equipment/IT density, different setpoints, no daylighting). A
zone-level model that applies one uniform archetype density to both is simpler but can mis-place
heating (perimeter) vs cooling (core) loads. We need the sourced per-zone deltas, or a defensible
statement that uniform densities are an acceptable UBEM simplification.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Core vs perimeter internal-load deltas (representative archetypes)

| Archetype | Quantity | Core value | Perimeter value | Differentiated? | Source |
|---|---|---|---|---|---|
| SmallOffice | LPD (W/m²) | | | | |
| SmallOffice | EPD (W/m²) | | | | |
| SmallOffice | Occupant density | | | | |
| MediumOffice | LPD / EPD / occ | | | | |
| LargeOffice | LPD / EPD / occ | | | | |
| Retail (Standalone) | LPD / EPD / occ | | | | |
| MidriseApartment | LPD / EPD / occ | | | | |
| Hospital | LPD / EPD / occ | | | | |
| PrimarySchool | LPD / EPD / occ | | | | |

> If the prototype assigns the same density to core and perimeter for a type, say "uniform (cite)".
> The question is empirical: do the DOE prototypes differentiate, or not?

### Table 2 — Ventilation (outdoor air) core vs perimeter

| Archetype | OA basis core (cfm/person + cfm/ft²) | OA basis perimeter | Differentiated? | Source (62.1 space type) |
|---|---|---|---|---|
| Office (small/med/large) | | | | |
| Retail | | | | |
| Residential (apt) | | | | |
| School | | | | |
| Hospital | | | | |

### Table 3 — Thermostat setpoints & schedules core vs perimeter

| Item | Core | Perimeter | Differentiated? | Source |
|---|---|---|---|---|
| Cooling setpoint (occ / unocc) | | | | |
| Heating setpoint (occ / unocc) | | | | |
| Setpoint schedule name (DOE prototype) | | | | |

### Table 4 — Window-to-wall ratio & daylighting

| Item | Core | Perimeter | Source |
|---|---|---|---|
| WWR (core has no exterior wall → 0?) | | | |
| Daylighting controls (perimeter only?) | | | |
| Glazing properties (U / SHGC — same as archetype?) | | | |

### Table 5 — HVAC terminal per zone

| Item | Recommendation | Source |
|---|---|---|
| Does each core/perimeter zone get its own terminal unit (PTAC / VAV box)? | | |
| Core vs perimeter reheat / economizer differences | | |
| How this maps onto OpenUBEM's per-zone HVAC assignment (already per-zone) | | |

---

## Part C — Synthesis (verdict)

State a single **accept-or-differentiate verdict**: should OpenUBEM's `zone` mode (a) keep applying
uniform archetype densities to core and perimeter — simplest, defensible if prototypes are uniform —
or (b) differentiate, and if so the **minimum set of deltas** worth coding (likely WWR=0 in core and
daylighting in perimeter, possibly higher core equipment). Tie the recommendation to the
zero-fitted-parameters rule.

## Output format (follow exactly)

1. **Lead with Tables 1–5 fully populated.**
2. Then Part C verdict.
3. Cite the DOE prototype per-zone values, 62.1 for OA, EnergyPlus refs for objects.
4. **"Confidence and caveats":** the one differentiation that matters most (if any).
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Answer the binary clearly:** do DOE prototypes differentiate core vs perimeter densities (Y/N per type)?
- **WWR and daylighting must be resolved** (core typically 0 WWR / no daylight).
- **Map onto OpenUBEM's existing per-zone assignment** (it already loops per zone).
- **No fabricated precision;** flag GAPs with a defensible default.
- **Stay on topic.** If it is not a per-zone parameter, cut it.
