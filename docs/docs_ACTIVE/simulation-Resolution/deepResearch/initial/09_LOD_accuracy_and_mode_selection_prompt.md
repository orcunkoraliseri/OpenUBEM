# Deep-Research Prompt 09 — LEVEL-OF-DETAIL accuracy & mode-selection guidance

> SCOPE GUARD — READ FIRST. This is a **literature-synthesis** task. The deliverable is the
> **quantified energy-accuracy difference** between building-, floor-, and zone-level thermal
> resolution in UBEM, and **decision guidance** telling a user which mode to pick for which study —
> with the **expected divergence** between modes so OpenUBEM can report it. It is NOT about how to
> build each mode (Prompts 01–08). If you are writing about anything other than **how much resolution
> changes the answer, when each is appropriate, and the source**, stop and return to the tables. See
> `00_README_resolution_prompt_set.md` for modes, roster, conventions.

---

## What this document is

A fill-in-the-blanks request synthesizing the published evidence on thermal-zoning resolution / level
of detail (LOD) in building and urban energy modelling. The output justifies offering the switch at
all, and gives users a sourced basis for choosing `building` vs `floor` vs `zone` vs `auto`. Treat
each cell as a question; fill with a sourced value or a GAP.

## Role

Building-energy-modelling research analyst. Trace every value to **peer-reviewed UBEM / BEM LOD
literature** — e.g. studies on single-zone vs multi-zone error, core/perimeter vs one-zone-per-floor,
the "shoeboxer" reduced-order approach, AutoBEM/CityBES validation papers, and any ASHRAE/IBPSA work
on zoning sensitivity. Name author, venue, year for every number. Where the literature reports ranges,
give the range and the conditions.

## Why this matters (so you scope correctly)

The switch is only worth offering if resolution **changes the answer** meaningfully — and users need
to know **by how much** and **when**. We need: the typical annual-energy error of coarse vs fine
zoning, which building types/uses are resolution-sensitive (perimeter-dominated, tall, mixed-use) vs
insensitive (internally-load-dominated, low-rise big-box), and whether coarser modes bias heating vs
cooling. This lets OpenUBEM (a) recommend a default per study type and (b) **report an expected
divergence band** when a user picks a coarse mode.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Reported accuracy by resolution (annual energy)

| Resolution comparison | Heating error/bias | Cooling error/bias | Total energy error | Conditions | Source |
|---|---|---|---|---|---|
| Single-zone vs core/perimeter multi-zone | | | | | |
| One-zone-per-floor vs core/perimeter | | | | | |
| Single-zone vs one-zone-per-floor | | | | | |
| Core/perimeter vs detailed room-level | | | | | |

### Table 2 — Resolution sensitivity by building characteristic

| Characteristic | Resolution-sensitive? | Why | Recommended minimum mode | Source |
|---|---|---|---|---|
| Perimeter-dominated (low aspect, lots of façade) | | | | |
| Internally-load-dominated (deep plan, high IT/equipment) | | | | |
| Tall / high-rise | | | | |
| Mixed-use vertical | | | | |
| Big-box single-storey | | | | |
| Residential apartment | | | | |

### Table 3 — Bias direction of coarsening (so OpenUBEM can caveat)

| Coarsening step | Typical bias | Mechanism | Source |
|---|---|---|---|
| → fewer zones (toward single-zone) | (over/under heating? cooling?) | (loses perimeter/core separation) | |
| → adiabatic inter-floor | | | |
| → ignoring daylight (no perimeter zones) | | | |

### Table 4 — Mode-selection guidance (the user-facing table)

| Study type | Recommended mode | Rationale | Expected divergence vs `zone` | Source |
|---|---|---|---|---|
| Early-design / screening / city-scale triage | `building`? | | | |
| Stock policy / retrofit ranking | `floor`? | | | |
| Detailed per-building / peak / comfort | `zone` | | | |
| Validated baseline reporting | `auto` | | | |

---

## Part C — Synthesis (decision guidance)

Give: (1) a one-paragraph verdict on **whether resolution materially changes UBEM results** (with the
headline numbers); (2) a **mode-selection recommendation** mapping study questions → mode; and (3) an
**expected-divergence statement** OpenUBEM can surface to users ("choosing `building` typically
shifts total EUI by X% vs `zone`, biased toward …"). Tie to OpenUBEM's validated ±9% city result —
i.e., is resolution a first- or second-order effect relative to archetype/weather uncertainty?

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C decision guidance.
3. Every accuracy number cited to a named paper (author, venue, year).
4. **"Confidence and caveats":** how transferable the literature is to OpenUBEM's archetype + real-
   footprint approach; where evidence is thin.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Give quantified error ranges**, not adjectives, for each resolution step.
- **Identify which building types are resolution-sensitive** vs not.
- **State the bias direction** of coarsening (for caveating coarse-mode outputs).
- **Produce the user-facing mode-selection table.**
- **Relate resolution effect to OpenUBEM's existing ±9% uncertainty** (first vs second order).
- **No fabricated precision;** flag GAPs. **Stay on topic** — accuracy and mode choice only.
