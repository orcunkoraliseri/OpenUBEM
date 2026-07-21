# Deep-Research Prompt L09 — OFFICE, RETAIL & SCHOOL LAYOUT SPECIFICS (service core, open/cellular perimeter, classroom wings)

> SCOPE GUARD — READ FIRST. This prompt details the **office / retail / school** branch of the generator.
> These archetypes are *not* primarily corridor+units — offices are core+perimeter around a service core
> (elevators/stairs/restrooms), big-box retail is one deep space, schools are classroom wings off a
> double-loaded corridor. Deliver the archetype-specific layout logic and its mapping to App-G
> core/perimeter (`L03`) and the DOE templates (`L07`). Residential/hotel is `L08`; hospitals/large
> complexes are `L10`. See `00_README_layoutgenerator_prompt_set.md` for shared facts.

---

## What this document is

The commercial/institutional playbook. OpenUBEM already core/perimeters large commercial (≥500 m²), so
this branch mostly *extends the existing App-G logic to non-rectangular office/retail footprints* and adds
the school classroom-wing pattern. The manager needs: where the service core actually goes (App-G puts
"core" as a residual, but real offices cluster stairs/elevators/restrooms into a compact service core),
how open-plan vs. cellular perimeter affects zoning, and how a school's classroom wings map to
corridor+rooms.

## Role

Commercial / institutional space-planning research analyst. Ground the layouts in the DOE Small/Medium/
Large Office, RetailStandalone/Stripmall, Primary/Secondary School prototype documentation, plus
Architectural Graphic Standards / Neufert / Time-Saver Standards for these building types, and ASHRAE 90.1
App-G core/perimeter (`L03`). Distinguish *service core* (fixed vertical circulation + toilets, a real
compact block) from App-G's *thermal core* (the residual interior zone) — they are not the same thing.

## Why this matters (so you scope correctly)

Offices/retail are the archetypes the current code *does* zone, so the risk is a regression: the
generalized generator must not produce worse office layouts than today's geomeppy core/perimeter for the
compact case, while adding L/U/O handling. Schools introduce the wing pattern that reuses `L06`'s
corridor logic. Getting the service-core placement right matters for daylight/perimeter fraction on
non-rectangular plates.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Layout organization per archetype

| Archetype | Primary organization | Service-core placement | Perimeter treatment (open / cellular) | Source |
|---|---|---|---|---|
| SmallOffice |  |  |  |  |
| MediumOffice |  |  |  |  |
| LargeOffice |  |  |  |  |
| RetailStandalone (big-box) |  | (usually none — one space) |  |  |
| RetailStripmall |  |  |  |  |
| SuperMarket |  |  |  |  |
| PrimarySchool |  | classroom wings + corridor |  |  |
| SecondarySchool |  |  |  |  |

### Table 2 — Non-rectangular handling

| Footprint | Office/retail rule | School rule | Source |
|---|---|---|---|
| Compact rectangle | App-G core/perimeter (as today) | wing = corridor + classrooms |  |
| L / U / T | decompose to wings, core/perimeter each? or shape-following band? |  |  |
| O / courtyard | perimeter ring; core = ? |  |  |
| Big single-storey deep plan (retail) | core/perimeter or single deep zone? | — |  |

### Table 3 — Service core vs. thermal core

| Question | Field practice | Source |
|---|---|---|
| Where do real offices put the vertical service core (center / offset / end)? |  |  |
| Should the generator place a fixed-size service core (stairs+elevators+toilets) or use App-G residual core? |  |  |
| Does service-core placement change perimeter daylight zone for BEM? |  |  |
| For a big-box retail with no perimeter offices, is single-zone-per-floor correct? |  |  |

### Table 4 — Fit to OpenUBEM

| Question | Answer + source |
|---|---|
| Does the generalized generator reproduce today's geomeppy core/perimeter for a compact office (no regression)? |  |
| For an L-office, is decompose-to-wings better than a shape-following band? |  |
| Does school classroom-wing layout reuse the `L06` corridor method cleanly? |  |
| Should single-storey big-box retail stay single-zone even in `zone` mode? |  |

---

## Part C — Synthesis (the commercial/institutional branch spec)

Give: (1) the **layout rule per archetype** — service-core placement, perimeter treatment, non-rectangular
handling; (2) an explicit **no-regression check** — the generalized method must equal today's core/perim
on compact offices; (3) the **school = corridor-wing** mapping to `L06`; (4) a recommendation on
service-core vs. App-G residual core, with source. Every dimension cited or flagged GAP.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C branch spec.
3. Cite DOE prototype / design standard / App-G clause per rule.
4. **"Confidence and caveats":** which archetype's non-rectangular layout is least evidenced.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Explicit no-regression statement** for compact offices vs. current geomeppy core/perimeter.
- **Distinguish service core from App-G thermal core** and recommend which the generator uses.
- **Every dimension cited**; flag invented values GAP.
- **No fabricated precision;** flag GAPs. **Stay on topic** — office/retail/school only; residential/hotel
  is `L08`, hospital/large-complex `L10`.
