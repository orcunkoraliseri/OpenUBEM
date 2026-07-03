# Deep-Research Prompt 01 — BUILDING-LEVEL single-zone methodology (collapse a multi-floor building into ONE thermal zone)

> SCOPE GUARD — READ FIRST. This is a **building-energy-modelling resolution** task. The deliverable
> is the **method + parameters** for correctly representing an entire multi-floor real building as a
> **single thermal zone** (mode `building`): how to set internal mass, infiltration, fenestration,
> loads and boundary conditions so a 1-zone full-height model is a *defensible* low-fidelity
> abstraction — and the **error bounds** of doing so. It is NOT about detailed zoning; that is
> Prompts 02–05. If you are writing about anything other than **how to build/justify a one-zone
> whole-building model and its accuracy**, stop and return to the tables. See
> `00_README_resolution_prompt_set.md` for modes, roster, conventions.

---

## What this document is

A fill-in-the-blanks request defining OpenUBEM's coarsest resolution: `resolution_mode="building"`
extrudes the real footprint to full height (`num_floors × 3.5 m`) as **one zone**. This is the
"early-design screening" tier. The questions: what does collapsing N floors into one tall zone get
*wrong*, how do we *compensate* with sourced parameters, and *when* is it acceptable. Treat each cell
as a question; fill it with a sourced value or a GAP.

## Role

Building-energy-modelling research analyst. Trace every rule to a named, dated, primary source: the
**ASHRAE Handbook — Fundamentals** (single-zone heat balance, internal thermal mass), the **DOE/PNNL
prototype** documentation (for the load densities being aggregated), the **EnergyPlus Input-Output /
Engineering Reference** (`Zone`, `ZoneInfiltration`, `InternalMass`, `ZoneCapacitanceMultiplier`,
single-zone airflow), and **peer-reviewed UBEM / shoebox / single-zone-model literature** (the
accuracy of one-zone-per-building reduced-order models vs multi-zone). SI; state IP + convert.

## Why this matters (so you scope correctly)

A single full-height zone removes inter-floor floors/ceilings (no internal heat storage between
floors unless `InternalMass` is added), gives the whole building one averaged air temperature,
one stack-driven infiltration regime over the full height, and one set of aggregated internal gains
on one thermostat. Each of those is a known simplification with a published correction or a known
bias. We need: the **internal-mass** treatment, the **infiltration** basis at full height (stack
effect), how **N floors of loads** map onto one zone, the **window** representation, and the
**accuracy penalty** vs a per-floor or multi-zone model.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Single-zone construction & boundary treatment

| Item | Recommended treatment for a 1-zone full-height model | Source |
|---|---|---|
| Inter-floor slabs (floors/ceilings between storeys) | (omit? represent as `InternalMass`?) | |
| Internal thermal mass to add (m² of mass per m² floor area; construction) | | |
| Exterior wall area basis (full perimeter × full height) | | |
| Roof = top only; ground floor = slab-on-grade or exposed | | |
| Zone air volume vs zone capacitance multiplier (should air capacitance be scaled?) | | |
| Interior partitions / furniture mass | | |

### Table 2 — Infiltration at full building height

| Parameter | Value / method | Source |
|---|---|---|
| Infiltration basis (ACH, or m³/s·m² of envelope, or `Flow/ExteriorArea`) | | |
| Stack-effect dependence on height (does full-height single zone over- or under-state it?) | | |
| Recommended infiltration rate for screening single-zone model (by archetype tightness) | | |
| Wind/stack coefficients (`ZoneInfiltration:DesignFlowRate` Constant/Temp/Velocity terms) | | |

### Table 3 — Internal-gain & schedule aggregation (N floors → 1 zone)

| Quantity | How to aggregate onto one zone | Conservation check | Source |
|---|---|---|---|
| Lighting power (W) | LPD × total floor area (= footprint × N) | total must equal sum of floors | |
| Equipment power (W) | EPD × total floor area | | |
| Occupants | density × total floor area | | |
| Outdoor-air ventilation | per-person + per-area on total floor area | | |
| Thermostat setpoint & schedule | single archetype schedule | | |

> The denominator for EUI stays `footprint × N`. Confirm that putting `LPD × footprint × N` of
> lighting into a single zone whose *floor* surface is only `footprint` is energetically correct
> (gains are volumetric/whole-zone, not per floor-surface) — state any EnergyPlus gotcha.

### Table 4 — Fenestration on a single full-height zone

| Item | Treatment | Source |
|---|---|---|
| Window-to-wall ratio (apply archetype WWR to full-height walls?) | | |
| Vertical glazing distribution (uniform band vs per-floor strips) | | |
| Does a single tall window vs stacked windows change solar/daylight materially? | | |

### Table 5 — Accuracy of one-zone-per-building (the headline)

| Comparison | Reported error / bias on annual energy | Conditions | Source |
|---|---|---|---|
| 1-zone whole-building vs multi-zone (heating) | (e.g. ±X%, direction) | | |
| 1-zone vs multi-zone (cooling) | | | |
| 1-zone vs multi-zone (peak loads) | | | |
| Building types where 1-zone is acceptable (low aspect, internally-load-dominated?) | | | |
| Building types where 1-zone fails (perimeter-dominated, tall, mixed-use) | | | |

---

## Part C — Synthesis (one paragraph + rule block)

Give: (1) the **minimum sourced recipe** for OpenUBEM's `building` mode — internal-mass rule,
infiltration basis, load-aggregation rule, WWR treatment; and (2) a one-line **"valid-for"
statement** — the archetypes/uses and the study questions for which single-zone screening is
defensible, and the expected error envelope vs `auto`/`zone`.

## Output format (follow exactly)

1. **Lead with Tables 1–5 fully populated.**
2. Then Part C recipe + valid-for statement.
3. Cite ASHRAE Fundamentals for mass/infiltration, EnergyPlus refs for the objects, ≥2 UBEM/ROM
   papers for the accuracy numbers.
4. **"Confidence and caveats":** the biggest physical error of single-zone and the cheapest fix.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Give a concrete internal-mass rule** (do we add `InternalMass` for omitted floors — yes/no + value).
- **Give an infiltration basis** usable per archetype.
- **Confirm the load-aggregation conservation** (N-floor totals preserved on one zone).
- **Give quantified accuracy bounds** vs multi-zone, with sources.
- **No fabricated precision;** flag GAPs with a defensible default.
- **Stay on topic.** If it is not about a one-zone whole-building model, cut it.
