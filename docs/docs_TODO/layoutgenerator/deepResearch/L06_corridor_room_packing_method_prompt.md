# Deep-Research Prompt L06 — CORRIDOR-SPINE ROOM PACKING (the proposed method — double-loaded corridor + edge/corner units)

> SCOPE GUARD — READ FIRST. This prompt validates and details **the user's proposed layout method**:
> place a circulation corridor along the footprint's spine, then pack rooms/units onto the edges and
> corners following a standard module (double-loaded corridor). Deliver: (1) whether this is the field's
> recognized convention for residential/hotel/institutional plans, (2) the **published design rules** —
> corridor width, room/unit depth, minimum dimensions, corner handling, single- vs. double-loaded — and
> (3) where the method breaks and what the fallback is. Do NOT re-derive the geometry primitives (that's
> `L05`, which this prompt *uses*), and do NOT enumerate per-archetype unit mixes (that's `L07`–`L10`,
> which detail the modules this method places). See `00_README_layoutgenerator_prompt_set.md` for shared
> facts.

---

## What this document is

The design-rules reference for OpenUBEM's chosen layout strategy. The user's mental model: an L-shaped
midrise apartment building is *just a bent double-loaded corridor* — put the corridor down the middle of
each wing, hang dwelling units off both sides, wrap units around the corner, and use the DOE
MidriseApartment unit as the module. The same pattern serves hotels (guest rooms off a corridor),
schools (classrooms off a corridor), and dormitories. This prompt must confirm that pattern is the
architectural norm (not an OpenUBEM invention), give the numeric design rules so the packing is
zero-fitted-parameters, and define exactly when it fails (footprint too shallow for double-loading, corner
geometry, etc.).

## Role

Architectural space-planning / building-typology research analyst. Ground the corridor-and-room typology
in architectural-standards references: **Architectural Graphic Standards** (Ramsey/Sleeper), **Neufert
Architects' Data**, **Time-Saver Standards for Building Types** (De Chiara), HUD / multifamily design
guidelines, and hotel/dormitory design standards. Ground the "double-loaded corridor" efficiency and
dimensional rules (net-to-gross, circulation factor) in those sources and in any UBEM/archetype paper that
uses corridor-based layouts. Give real dimensions (corridor width in m, unit depth in m, bay width in m),
each cited.

## Why this matters (so you scope correctly)

This is the heart of `layoutGenerator.py`. If the double-loaded corridor is the documented norm with
published dimensions, OpenUBEM can generate defensible layouts with zero fitted parameters. If the
dimensions vary widely or the corner/short-wing cases are undefined, the manager needs those flagged as
decisions now, before Sonnet implements. The prompt also decides the crucial modeling question: **do the
packed rooms become individual thermal zones, or are same-orientation units merged into one perimeter
zone with a multiplier?** — which controls zone count and runtime.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Is corridor+room-packing the recognized convention?

| Building type | Is double-loaded corridor the standard plan organization? | Alternative organizations (single-loaded, point-access, open) | Source |
|---|---|---|---|
| Midrise / highrise apartment |  |  |  |
| Small / large hotel |  |  |  |
| Dormitory / residence hall |  |  |  |
| School (classroom wing) |  |  |  |
| Office (cellular) |  |  |  |
| Hospital (ward / nursing unit) |  |  |  |

### Table 2 — Published dimensional design rules (the zero-fitted-parameters inputs)

| Parameter | Typical / code-minimum value | Building type it applies to | Source (Graphic Standards / Neufert / code clause) |
|---|---|---|---|
| Corridor clear width (double-loaded) |  |  |  |
| Corridor clear width (single-loaded) |  |  |  |
| Dwelling-unit depth (corridor wall → façade) |  | apartment |  |
| Hotel guest-room depth / bay width |  | hotel |  |
| Classroom depth / bay | | school | |
| Minimum room dimension for a habitable/rentable space |  |  |  |
| Net-to-gross / circulation factor (corridor+core share of floor) |  |  |  |
| Wall thickness assumption for interior partitions |  |  |  |

### Table 3 — Corridor placement on non-rectangular plates

| Footprint | Corridor geometry | Room-packing rule | Corner unit handling | Source |
|---|---|---|---|---|
| Bar / slab | straight central corridor | units both sides |  |  |
| L-shape | L-shaped corridor along both wings | units both sides of each wing | corner where wings meet |  |
| U-shape | U corridor |  |  |  |
| O / courtyard | ring corridor around court | units on outer edge (and inner?) |  |  |
| T / cross | branched corridor at junction |  |  |  |

### Table 4 — Thermal-zone mapping (the modeling decision)

| Question | Field practice / recommendation | Source |
|---|---|---|
| Does each packed unit become its own thermal zone, or are like-orientation units merged? |  |  |
| Is the corridor its own (semi-conditioned) zone or lumped into the core? |  |  |
| Is a zone-multiplier used to represent repeated identical units (E+ `Zone Multiplier`)? |  |  |
| How many thermal zones does a corridor+units floor typically reduce to for BEM (vs. architectural room count)? |  |  |
| Does this map onto App-G core/perimeter (corridor≈core, units≈perimeter) or is it a distinct scheme? |  |  |

### Table 5 — When the method breaks (fallback triggers)

| Failure condition | Why the packing fails | Recommended fallback | Source |
|---|---|---|---|
| Wing too shallow for double-loaded corridor + 2 unit rows |  | single-loaded? single-zone? |  |
| Wing too shallow even for single-loaded |  |  |  |
| Footprint too small for any unit module |  |  |  |
| Non-orthogonal / curved edges |  |  |  |
| Corner geometry produces sub-minimum units |  |  |  |

---

## Part C — Synthesis (the method spec)

Give: (1) a verdict on **whether the corridor+room-packing method is the defensible architectural norm**
for the residential/hotel/institutional archetypes (and where it is not); (2) the **table of pinned,
cited dimensions** the generator will use (corridor width, unit depth, circulation factor) — every value
cited or flagged GAP; (3) the **thermal-zone mapping recommendation** — per-unit zones vs. merged-with-
multiplier — with its zone-count/runtime implication; (4) the **explicit fallback chain** when a wing is
too shallow or a shape too irregular to pack. This section IS the algorithm the plan will encode.

## Output format (follow exactly)

1. **Lead with Tables 1–5 fully populated.**
2. Then Part C method spec.
3. Cite an architectural-standards source for every dimension; separate code-minimums from typical values.
4. **"Confidence and caveats":** which dimension or corner rule is least standardized across sources.
5. **Reference list** — full citations, dates, URLs/DOIs.

## Hard requirements

- **Every dimension must be cited** (Graphic Standards / Neufert / Time-Saver / code) — zero-fitted-
  parameters; flag any invented value as GAP.
- **Explicitly answer the per-unit-zone vs. merged-zone-with-multiplier question** — it sets zone count.
- **Give the fallback chain** for shallow wings and irregular shapes — the method must degrade, never
  fatal.
- **No fabricated precision;** flag GAPs. **Stay on topic** — the corridor-packing *method & its
  dimensions* only, not the geometry libs (`L05`) or the full per-archetype unit mix (`L07`–`L10`).
