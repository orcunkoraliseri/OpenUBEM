# Deep-Research Prompt 14 — INFILTRATION & airtightness scaling across resolution

> SCOPE GUARD — READ FIRST. This is an **infiltration-parameterization** task. The deliverable is the
> rule for setting **air infiltration** so the building-total leakage is consistent as zone count and
> exposed-surface bookkeeping change across modes — including the **stack-effect height dependence**
> that single-zone full-height models distort. It is NOT about mechanical ventilation/OA (Prompt 08)
> or boundary conditions (Prompt 06). If you are writing about anything other than **how infiltration
> is specified/scaled per resolution and the source**, stop and return to the tables. See
> `00_README_resolution_prompt_set.md` for modes, roster, conventions.

---

## What this document is

A fill-in-the-blanks request on infiltration × resolution. EnergyPlus infiltration
(`ZoneInfiltration:DesignFlowRate`) can be specified per zone by `Flow/Zone`, `Flow/Area` (zone floor
area), `Flow/ExteriorArea`, `Flow/ExteriorWallArea`, or `AirChanges/Hour`. Each basis scales
differently when a building is split into zones — and the **exterior-wall-area** basis is the
physically correct one but changes as core (no exterior wall) vs perimeter zones are created. We need
the basis that keeps total infiltration invariant and correctly placed. Treat each cell as a question.

## Role

Building-energy-modelling research analyst. Trace every rule to: the **EnergyPlus I/O Reference**
(`ZoneInfiltration:DesignFlowRate` design-flow-rate calculation methods and the Constant/Temperature/
Velocity coefficients), the **DOE/PNNL prototype** documentation (infiltration basis + rate, and the
"on when fans off" schedule), **ASHRAE 90.1-2019 / Fundamentals** (envelope leakage rates, stack
effect), and **AIVC / blower-door literature** for airtightness. SI + IP.

## Why this matters (so you scope correctly)

If infiltration is `Flow/Area` (zone floor area), splitting a floor preserves total but puts leakage in
the windowless **core** — physically wrong (cores don't leak to outside). If `Flow/ExteriorWallArea`,
the core correctly gets zero and perimeter zones carry it — but then total depends on how much exterior
wall the zoning creates. And a single full-height zone cannot represent stack-driven infiltration
varying with height. We need the sourced basis + rate that is both conserved and correctly placed.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Infiltration specification basis (behaviour under splitting)

| Basis | Conserves building total under splitting? | Places leakage correctly (core = 0)? | Recommended? | Source |
|---|---|---|---|---|
| `Flow/Zone` | | | | |
| `Flow/Area` (zone floor area) | | | | |
| `Flow/ExteriorArea` (all exterior incl. roof) | | | | |
| `Flow/ExteriorWallArea` | | | | |
| `AirChanges/Hour` | | | | |

### Table 2 — Prototype infiltration rate & basis

| Item | Value | Source |
|---|---|---|
| DOE prototype infiltration rate (e.g. m³/s·m² exterior wall at 4 Pa) | | |
| The basis the prototypes use | | |
| Infiltration schedule (reduced when HVAC on?) | | |
| Constant/Temp/Velocity coefficients (the DOE/“Sherman-Grimsrud”-style set) | | |

### Table 3 — Stack effect & height

| Item | Effect | Resolution dependence | Source |
|---|---|---|---|
| Stack-driven infiltration vs building height | | (single full-height zone distorts?) | |
| Tall-building infiltration treatment | | | |
| Recommended handling for `building` mode (tall, 1 zone) | | | |

### Table 4 — Per-archetype airtightness (if differentiated)

| Archetype group | Tightness (rate) | Source |
|---|---|---|
| Residential | | |
| Office / commercial | | |
| Warehouse / industrial | | |
| Default | | |

---

## Part C — Synthesis (rule)

Give the **single infiltration rule** OpenUBEM should code: the specification basis (recommend the one
that both conserves total and zeroes the core — likely `Flow/ExteriorWallArea`), the rate + schedule +
coefficients from the prototypes, and the handling of stack effect for tall single-zone (`building`)
models. State the expected infiltration difference between modes for the same building and whether it
is a real effect or should be neutralized.

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated.**
2. Then Part C rule.
3. Cite the E+ infiltration object, prototype rates, ASHRAE/AIVC airtightness data.
4. **"Confidence and caveats":** the basis pitfall (core leakage) and stack-effect distortion.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Recommend an infiltration basis** that conserves total AND zeroes the windowless core.
- **Give the prototype rate, schedule, and coefficients.**
- **Address stack effect** for tall single-zone models.
- **No fabricated precision;** flag GAPs. **Stay on topic** — infiltration only.
