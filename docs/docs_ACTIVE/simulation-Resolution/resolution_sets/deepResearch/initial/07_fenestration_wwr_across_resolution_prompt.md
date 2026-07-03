# Deep-Research Prompt 07 — FENESTRATION & WWR placement across resolution modes

> SCOPE GUARD — READ FIRST. This is a **fenestration-geometry** task. The deliverable is **where
> windows go and what window-to-wall ratio (WWR) applies** as zone count changes: whole-building band
> vs per-floor strips vs perimeter-only glazing — and how to keep the **total glazing area and solar
> gains consistent** across modes. It is NOT about glazing U/SHGC values (those are archetype
> properties OpenUBEM already has). If you are writing about anything other than **window placement,
> WWR, glazing area conservation, and the source**, stop and return to the tables. See
> `00_README_resolution_prompt_set.md` for modes, roster, conventions.

---

## What this document is

A fill-in-the-blanks request on fenestration across resolutions. A single full-height zone, stacked
per-floor zones, and core/perimeter zones distribute the same façade glazing very differently —
affecting solar gains, daylight, and peak loads. We need a consistent WWR-application rule per mode so
the same building has comparable glazing across modes. Treat each cell as a question.

## Role

Building-energy-modelling research analyst. Trace every rule to: the **DOE/PNNL prototype**
documentation (per-type WWR and sill/head heights), **ASHRAE 90.1-2019 §5 / App G** (baseline WWR
40% and vertical fenestration rules), the **EnergyPlus I/O Reference**
(`FenestrationSurface:Detailed`, `Window`, geomeppy `set_wwr`), and the **EnergyPlus Engineering
Reference** on solar distribution. SI + IP.

## Why this matters (so you scope correctly)

geomeppy applies WWR to exterior walls. On one full-height zone the glazing is a tall band; on
per-floor zones it is repeated strips; on core/perimeter only the perimeter walls glaze (core has no
exterior wall). If WWR is applied naively, total glazing area and thus solar gain can differ between
modes for the *same* building — breaking comparability. We need the rule that keeps glazing physically
consistent while respecting that perimeter zones are where daylight/solar actually act.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — WWR application rule per mode

| Mode | Which walls glaze | WWR applied to | Resulting total glazing area vs other modes | Source |
|---|---|---|---|---|
| `building` (1 zone full height) | all exterior walls, full height | archetype WWR | | |
| `floor` (1 zone/floor) | each floor's exterior walls | archetype WWR | should equal `building` total | |
| `zone` (core/perimeter) | perimeter exterior walls only (core = 0) | archetype WWR | should equal per-floor total | |

> The key check: does the **same building** get the **same total glazing area** in all three modes? If
> geomeppy's per-wall WWR preserves total area automatically, confirm; if not, give the correction.

### Table 2 — Archetype WWR and window geometry (DOE prototype basis)

| Archetype | Prototype WWR (%) | Sill / head height (m) | Orientation-specific WWR? | Source |
|---|---|---|---|---|
| SmallOffice | | | | |
| MediumOffice | | | | |
| LargeOffice | | | | |
| RetailStandalone | | | | |
| MidriseApartment | | | | |
| HighriseApartment | | | | |
| Hospital | | | | |
| PrimarySchool | | | | |
| Warehouse | | | | |
| (others / default) | | | | |

### Table 3 — Solar & daylight consequences of placement

| Effect | building (tall band) | floor (strips) | zone (perimeter only) | Source |
|---|---|---|---|---|
| Solar gain total | | | | |
| Solar gain distribution (which zones heat up) | | | | |
| Daylight availability (perimeter only meaningful) | | | | |
| Self-shading / overhang effects | | | | |

### Table 4 — Conservation & comparability rule

| Item | Rule | Source |
|---|---|---|
| Keep total glazing area equal across modes? (Y/N + how) | | |
| If not equal, the intended interpretation (e.g. zone mode is "more correct") | | |
| Default WWR when archetype/source is silent | | |

---

## Part C — Synthesis (rule block)

Give a **single WWR-application rule** per mode that (a) uses the DOE prototype WWR, (b) glazes
perimeter walls only at `zone` level, and (c) keeps the same building's total glazing area comparable
across modes (or states explicitly and defensibly why it differs). Note any geomeppy-specific gotcha.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated** (every archetype in Table 2).
2. Then Part C rule block.
3. Cite prototype WWR, 90.1 §5/App G, EnergyPlus/geomeppy fenestration behaviour.
4. **"Confidence and caveats":** whether cross-mode glazing comparability holds.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Answer the comparability check:** same building → same total glazing area across modes? (Y/N + fix).
- **Give per-archetype WWR** from the prototypes.
- **Resolve perimeter-only glazing at `zone` level** (core WWR = 0).
- **No fabricated precision;** flag GAPs with a defensible default.
- **Stay on topic.** If it is not window placement/WWR/area, cut it.
