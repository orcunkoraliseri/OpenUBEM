# Deep-Research Prompt 15 — MIXED-USE vertical stacking enabled by resolution (per-floor archetypes)

> SCOPE GUARD — READ FIRST. This is a **capability/methodology** task. The deliverable is whether and
> how the resolution switch should support **vertically mixed-use buildings** — e.g. ground-floor
> retail with residential above — by assigning **different archetypes/loads per floor**, which only
> becomes representable at `floor` or `zone` resolution. It is NOT about classifying which buildings
> are mixed-use (a data problem) — it is about the modelling method once mixed use is known. If you
> are writing about anything other than **how per-floor use mixing is modelled per resolution and the
> source**, stop and return to the tables. See `00_README_resolution_prompt_set.md` for modes, roster,
> conventions.

---

## What this document is

A fill-in-the-blanks request on mixed-use × resolution. Today OpenUBEM assigns **one archetype per
building**. A single-zone (`building`) model cannot represent ground-retail-over-residential; a
per-floor (`floor`) or zone (`zone`) model can carry a **different archetype per floor**. This prompt
scopes whether the resolution switch should unlock per-floor archetype assignment, and the method for
doing it consistently. Treat each cell as a question; fill with a sourced approach or a GAP.

## Role

Building-energy-modelling research analyst. Trace to: **peer-reviewed UBEM literature** on mixed-use /
per-floor use modelling (how CityBES/CEA/AutoBEM handle vertical mixed use), **DOE/PNNL prototype**
conventions (mixed-use prototypes? combining single-use prototypes by floor), OSM/tax-assessor
mixed-use tagging practice, and the **EnergyPlus** mechanics of per-zone load/schedule/HVAC assignment
(already per-zone in OpenUBEM). SI.

## Why this matters (so you scope correctly)

Vertical mixed use is common in dense urban cells (the centre/urban density tiers OpenUBEM validates).
Modelling a whole mixed-use tower as one archetype mis-states both energy and its split. The resolution
switch is the natural enabler: `floor` mode lets each storey take its own archetype's loads/schedules/
HVAC. But this raises questions — how to source the per-floor use split, how to keep HVAC/DHW coherent
across mixed floors, and whether this is in-scope for v1 or a follow-on. We need the method and a
scope recommendation.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Modelability of mixed use per resolution

| Mode | Can carry per-floor archetype? | How | Limitation | Source |
|---|---|---|---|---|
| `building` (1 zone) | (no — single use) | | | |
| `floor` (1 zone/floor) | (yes — archetype per floor) | | | |
| `zone` (core/perimeter) | (yes — archetype per floor, split into zones) | | | |

### Table 2 — Common vertical mixed-use patterns

| Pattern | Typical floors | Per-floor archetypes | Source |
|---|---|---|---|
| Retail base + residential tower | ground retail + apt above | RetailStandalone + MidriseApartment | |
| Retail base + office tower | | RetailStandalone + LargeOffice | |
| Parking podium + residential | | (unconditioned + apartment) | |
| Ground commercial + hotel | | | |

### Table 3 — Cross-floor coherence questions

| Issue | Method | Source |
|---|---|---|
| HVAC across mixed floors (separate systems per use vs shared) | | |
| DHW/service loads per use floor | | |
| Schedules differ by floor (retail vs residential occupancy) | | |
| Shared envelope / thermal coupling between use floors | | |
| Unconditioned floors (parking podium) treatment | | |

### Table 4 — How peer tools handle it

| Tool / paper | Per-floor use modelling method | Source |
|---|---|---|
| CityBES | | |
| City Energy Analyst | | |
| AutoBEM | | |
| Other | | |

---

## Part C — Synthesis (scope recommendation)

Give: (1) confirmation that `floor`/`zone` resolution is the **enabler** for per-floor mixed use and
the method to assign archetype-per-floor consistently; (2) the cross-floor coherence rules (HVAC, DHW,
schedules, unconditioned podiums); and (3) a **scope verdict** — should per-floor mixed use be part of
the resolution switch v1, or a documented follow-on once the switch exists? Note the data dependency
(per-floor use must come from somewhere) as a separate prerequisite.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C scope recommendation.
3. Cite ≥2 UBEM tools' mixed-use methods and prototype-combination practice.
4. **"Confidence and caveats":** the data dependency (per-floor use tagging) and whether to defer.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Confirm resolution is the enabler** and give the archetype-per-floor assignment method.
- **Resolve cross-floor HVAC/DHW/schedule coherence.**
- **Give a v1 vs follow-on scope verdict** with the data dependency called out.
- **No fabricated precision;** flag GAPs. **Stay on topic** — per-floor mixed-use modelling only.
