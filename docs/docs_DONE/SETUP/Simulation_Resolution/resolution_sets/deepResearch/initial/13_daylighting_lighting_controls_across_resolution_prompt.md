# Deep-Research Prompt 13 — DAYLIGHTING & lighting controls across resolution

> SCOPE GUARD — READ FIRST. This is a **daylighting-modelling** task. The deliverable is whether and
> how **daylight-responsive lighting controls** are modelled at each resolution — they are only
> physically meaningful where perimeter (daylit) zones exist — and the **lighting-energy effect** of
> including vs omitting them. It is NOT about glazing geometry (Prompt 07) or load densities (Prompt
> 04). If you are writing about anything other than **daylighting control modelling per resolution and
> the source**, stop and return to the tables. See `00_README_resolution_prompt_set.md` for modes,
> roster, conventions.

---

## What this document is

A fill-in-the-blanks request on daylighting × resolution. DOE prototypes apply daylighting controls in
perimeter zones (dimming/stepped) that cut lighting energy. A single-zone or whole-floor model has no
distinct daylit perimeter, so it cannot represent this — meaning coarse modes may **over-state lighting
energy**. We need the sourced control parameters and the magnitude of the effect. Treat each cell as a
question.

## Role

Building-energy-modelling research analyst. Trace every value to: the **DOE/PNNL prototype**
documentation (which zones have daylighting, control type, setpoints, fraction of lighting controlled),
**ASHRAE 90.1-2019 §9.4** (daylighting-control requirements), and the **EnergyPlus I/O Reference**
(`Daylighting:Controls`, `Daylighting:ReferencePoint`). SI + IP.

## Why this matters (so you scope correctly)

Daylighting can cut perimeter lighting energy by a meaningful fraction. If `zone` mode includes it but
`building`/`floor` cannot, the modes diverge for a *correct physical reason* — and OpenUBEM must
decide whether to include daylighting at all (it adds inputs and runtime) and how to keep modes
interpretable. We need the control parameters per archetype and the lighting-energy delta.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Daylighting controls per archetype (DOE prototype basis)

| Archetype | Daylit zones | Control type (continuous / stepped / off) | Illuminance setpoint (lux) | Fraction of lighting controlled | Source |
|---|---|---|---|---|---|
| SmallOffice | | | | | |
| MediumOffice | | | | | |
| LargeOffice | | | | | |
| RetailStandalone | | | | | |
| PrimarySchool | | | | | |
| SecondarySchool | | | | | |
| MidriseApartment | | | | | |
| Warehouse | | | | | |
| (others / default) | | | | | |

### Table 2 — Modelability per resolution

| Mode | Daylighting representable? | How | Source |
|---|---|---|---|
| `building` (1 zone) | (one ref point? whole-building average?) | | |
| `floor` (1 zone/floor) | (per-floor average — partial?) | | |
| `zone` (core/perimeter) | (perimeter ref points — full) | | |

### Table 3 — Lighting-energy effect

| Comparison | Lighting-energy reduction from daylighting | Conditions | Source |
|---|---|---|---|
| Perimeter daylighting on vs off | | | |
| Effect by climate (sunny LA/Austin vs NYC) | | | |
| Whole-building lighting EUI sensitivity | | | |

### Table 4 — Recommendation

| Question | Recommendation | Source |
|---|---|---|
| Include daylighting in OpenUBEM at all? (currently?) | | |
| If yes, only at `zone` level, or approximate at coarser levels? | | |
| Keep modes comparable despite daylighting only at `zone`? | | |

---

## Part C — Synthesis

State (1) the daylighting control parameters OpenUBEM should use per archetype (or "omit, with this
justification"); (2) whether daylighting is only meaningful at `zone` level and the resulting
lighting-energy divergence between modes; and (3) how to keep that divergence interpretable (it is a
real effect, not a bug).

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated** (every archetype in Table 1).
2. Then Part C synthesis.
3. Cite prototype daylighting setup, 90.1 §9.4, EnergyPlus `Daylighting:Controls`.
4. **"Confidence and caveats":** the lighting-energy error of omitting daylighting in coarse modes.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Give per-archetype daylighting control parameters** (or a justified omit).
- **State at which resolution daylighting becomes representable.**
- **Quantify the lighting-energy effect**, by climate where possible.
- **No fabricated precision;** flag GAPs. **Stay on topic** — daylighting/lighting controls only.
