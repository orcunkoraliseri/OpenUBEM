# Deep-Research Prompt 02 — FLOOR-LEVEL methodology (one zone per floor: stacking, inter-floor boundaries, floor differentiation)

> SCOPE GUARD — READ FIRST. This is a **building-energy-modelling resolution** task. The deliverable
> is the **method + parameters** for representing each storey of a real building as a **single
> stacked thermal zone** (mode `floor`): the **surface boundary conditions between stacked floors**,
> how **ground / middle / top** floors differ (slab, roof, exposure), party walls to neighbours, and
> the **accuracy** vs single-zone and multi-zone. It is NOT about intra-floor core/perimeter zoning;
> that is Prompts 03–05. If you are writing about anything other than **how to stack one-zone floors
> correctly and its accuracy**, stop and return to the tables. See
> `00_README_resolution_prompt_set.md` for modes, roster, conventions.

---

## What this document is

A fill-in-the-blanks request defining OpenUBEM's mid-fidelity tier: `resolution_mode="floor"` stacks
the real footprint `num_floors` times, each storey one zone (3.5 m). The load-bearing question is the
**boundary condition on the floor/ceiling surfaces between adjacent stacked zones**, and the
**top/ground/middle differentiation**. Treat each cell as a question; fill with a sourced value or GAP.

## Role

Building-energy-modelling research analyst. Trace every rule to: **EnergyPlus Input-Output /
Engineering Reference** (`BuildingSurface:Detailed` Outside Boundary Condition — `Surface`,
`Adiabatic`, `Ground`, `Outdoors`; `ZoneList`; surface matching / `intersect_match`), the **DOE/PNNL
prototype** documentation (how multi-storey prototypes set inter-floor boundaries and which floors
they actually model), the **ASHRAE Handbook — Fundamentals** (ground coupling, multi-storey stack),
and **peer-reviewed UBEM literature** on per-floor / per-storey modelling. SI; state IP + convert.

## Why this matters (so you scope correctly)

When floors are separate zones, every inter-floor surface can be (a) **adiabatic** (no heat crosses —
assumes neighbours at equal temperature), or (b) a **heat-transfer interzone surface** (`Surface`
boundary, conduction + solar/long-wave bookkeeping between zones). The choice changes heating/cooling
distribution between floors and the middle-floor energy. Separately, the **ground floor** sees slab
ground coupling, the **top floor** sees the roof, and **middle floors** see neither — so a uniform
per-floor model that ignores this mis-states the envelope. We need the sourced convention for each.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Inter-floor surface boundary condition

| Surface | Recommended Outside Boundary Condition | Rationale | Source |
|---|---|---|---|
| Floor of zone *i* / ceiling of zone *i−1* (between stacked storeys) | (Adiabatic vs Surface interzone?) | | |
| If `Surface` (heat-transfer): construction to use for the interior slab | | | |
| If `Adiabatic`: what physical assumption it encodes + when it's valid | | | |
| Inter-floor air leakage / open stairwells (model or ignore?) | | | |

> State the DOE/PNNL prototype convention explicitly — do the multi-storey prototypes use adiabatic
> inter-floor surfaces, heat-transfer interzone surfaces, or a zone-multiplier middle floor?

### Table 2 — Floor-position differentiation (ground / middle / top)

| Floor position | Distinct envelope features | Boundary conditions | Source |
|---|---|---|---|
| Ground floor | slab-on-grade / exposed underside / basement? | `Ground` vs `Outdoors` | |
| Middle floors | inter-floor top & bottom only; exterior walls + windows | interzone / adiabatic | |
| Top floor | roof (insulation, solar) | `Outdoors` roof | |
| Single-storey case (num_floors=1) | floor + roof both exterior | | |

### Table 3 — Ground coupling for the ground-floor zone

| Parameter | Value / method | Source |
|---|---|---|
| Slab-on-grade method (`Ground`, `GroundDomain`, F-factor, or simple `Ground` temp) | | |
| Ground temperature basis (monthly `Site:GroundTemperature:*`) | | |
| Below-grade (basement) handling if levels imply it | | |

### Table 4 — Party walls / shared surfaces with neighbours (attached rows, urban infill)

| Case | Exterior wall treatment | Source |
|---|---|---|
| Detached building (all walls `Outdoors`) | | |
| Attached / row building (shared party wall) | (adiabatic party wall vs modelled neighbour?) | |
| OpenUBEM's neighbour shading vs thermal coupling (shading-only today — confirm appropriate) | | |

> OpenUBEM currently treats neighbours as **shading** geometry, not thermally-coupled party walls.
> Confirm whether per-floor mode should keep shading-only or add adiabatic party walls for attached
> stock, and the energy implication.

### Table 5 — Accuracy of one-zone-per-floor

| Comparison | Reported error / bias on annual energy | Conditions | Source |
|---|---|---|---|
| Per-floor vs single-zone whole-building | | | |
| Per-floor vs full core/perimeter multi-zone | | | |
| Sensitivity to adiabatic-vs-interzone inter-floor choice | | | |
| Where per-floor is sufficient vs where core/perimeter is needed | | | |

---

## Part C — Synthesis (one paragraph + rule block)

Give: (1) the **minimum sourced recipe** for `floor` mode — inter-floor boundary condition, ground/
top/middle differentiation rule, party-wall policy; and (2) a **"valid-for" statement** — when
per-floor is the right tier and the expected error envelope vs `building` and `zone`.

## Output format (follow exactly)

1. **Lead with Tables 1–5 fully populated.**
2. Then Part C recipe + valid-for statement.
3. Cite the EnergyPlus boundary-condition docs, the prototype convention, and ≥2 UBEM papers for
   accuracy.
4. **"Confidence and caveats":** the single most consequential choice (likely the inter-floor
   boundary condition) and your recommendation.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Give a definite inter-floor boundary-condition recommendation** (adiabatic vs interzone) with cite.
- **Differentiate ground / middle / top floors explicitly.**
- **State the ground-coupling method** for the ground-floor zone.
- **Resolve the party-wall question** (keep shading-only vs add adiabatic party walls).
- **Quantified accuracy bounds**, with sources.
- **No fabricated precision;** flag GAPs with a defensible default.
- **Stay on topic.** If it is not about stacking one-zone floors, cut it.
