
# Deep-Research Prompt 05 — REFRIGERATION (supermarket cases/racks + walk-ins) with Zone Case Credit

> SCOPE GUARD — READ FIRST. This is a **numeric EnergyPlus-parameter** task for commercial
> refrigeration. The deliverable is, per archetype with refrigeration, EITHER a **total refrigeration
> energy intensity** OR the **case/walk-in/rack parameters** that instantiate `Refrigeration:Case` /
> `:WalkIn` / `:CompressorRack` / `:System` — AND the **zone case-credit split** (how display cases
> remove heat from the sales floor). It is NOT refrigerant policy, leak/GWP accounting, or equipment
> brand selection. If you are writing about anything other than a **number bound for an EnergyPlus
> refrigeration field and its source**, stop and return to the tables.

---

## What this document is

A fill-in-the-blanks request for refrigeration parameters, primarily for `SuperMarket`, plus the
walk-in coolers/freezers in restaurants, hotels, hospitals, and supermarket back-of-house. OpenUBEM
Phase-E moves refrigeration from a reporting-layer estimate into the simulation — and crucially models
the **zone case credit**, the heat display cases pull out of the space (which reconstruction ignores).
See `00_README_phaseE_prompt_set.md` for roster and conventions.

## Role

Building-energy-modelling research analyst. Trace every value to: the **DOE Commercial Reference
Building — Supermarket** model and its documentation (it specifies cases, racks, and schedules), the
**PNNL / DOE prototype refrigeration documentation**, the **EnergyPlus Input-Output Reference &
Engineering Reference (Refrigeration objects, "case credit")**, and **ASHRAE Handbook —
Refrigeration**. SI + IP. No fabricated precision.

## Why these numbers (so you scope correctly)

EnergyPlus offers two fidelities, and we want to know which is feasible to apply at UBEM scale:
- **Simple/lumped:** refrigeration as a metered electric load at a **kWh/m²·yr intensity** (fast, but
  misses zone coupling).
- **Physical:** `Refrigeration:Case`/`:WalkIn` on a `:CompressorRack` or `:System`, where each case
  has a rated cooling capacity, operating temperature, latent/defrost behaviour, and a **case credit
  fraction** that removes sensible + latent heat from the zone air (cooling the sales floor, which
  raises space-heating and lowers space-cooling — the realism reconstruction throws away).

We need both: the **lumped intensity** (as a fallback / sanity check) AND the **physical parameters +
the case-credit split** (for the real model). Tell us which you recommend for a 8,160-building UBEM.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Lumped refrigeration energy intensity (fallback basis)

| Archetype | Refrigeration energy intensity (kWh/m²·yr and kWh/ft²·yr) | Share of whole-building site energy (%) | Source |
|---|---|---|---|
| SuperMarket | | | |
| FullServiceRestaurant (walk-ins) | | | |
| QuickServiceRestaurant (walk-ins) | | | |
| LargeHotel (kitchen cold storage) | | | |
| Hospital (kitchen / morgue / pharmacy) | | | |
| SuperMarket — refrigeration as % of total store electricity | | | |

### Table 2 — Display-case parameters (physical model — SuperMarket)

Give a representative case mix for a typical supermarket; state the store-size basis (cases per m² of
sales floor, or total case length per store).

| Case type | Operating temp (°C / °F) | Rated cooling capacity per unit length (W/m and Btu/h·ft) | Case length basis (m per store / per m² sales) | Latent heat ratio | Defrost type + energy | Case fan + lighting (W/m) | Source |
|---|---|---|---|---|---|---|---|
| Low-temp frozen (reach-in/door) | | | | | | | |
| Medium-temp dairy/deli (open vertical) | | | | | | | |
| Medium-temp meat | | | | | | | |
| Produce (open) | | | | | | | |

### Table 3 — Walk-in coolers & freezers

| Item | Cooler (medium-temp) | Freezer (low-temp) | Basis (per store / per restaurant) | Source |
|---|---|---|---|---|
| Operating temp (°C / °F) | | | | |
| Floor area or volume basis | | | | |
| U-value of walls/ceiling/floor | | | | |
| Rated cooling capacity (W) | | | | |
| Infiltration / door schedule | | | | |

### Table 4 — Compressor rack / refrigeration system

| Parameter | Low-temp rack | Medium-temp rack | Source |
|---|---|---|---|
| Rack / system COP (design) | | | |
| Suction / saturated evaporating temperature (°C / °F) | | | |
| Condenser type (air-cooled / evap / water-cooled) | | | |
| Condenser fan power / heat rejection | | | |
| Number of racks per typical store | | | |
| Heat-recovery / subcooling present? | | | |

### Table 5 — ZONE CASE CREDIT (the key coupling) + schedules

| Parameter | Value | Notes | Source |
|---|---|---|---|
| Fraction of case cooling drawn from the **zone (sensible)** | | EnergyPlus "case credit" | EnergyPlus Eng. Ref |
| Fraction drawn from the **zone (latent)** | | | |
| Net sales-floor cooling effect (W/m² of sales floor) | | (how much display cases cool the space) | |
| Effect on space heating / cooling (qualitative + magnitude) | | (raises heating, lowers cooling) | |
| Case operating schedule (24/7 vs store hours) | | | |
| Anti-sweat heater / night-curtain assumptions | | | |

---

## Part C — Recommendation (one paragraph)

State plainly **which fidelity OpenUBEM should use** for an 8,160-building UBEM: (a) lumped electric
intensity (Table 1) with no zone coupling, or (b) the physical `Refrigeration:Case`/`:CompressorRack`
model (Tables 2–5) with the case credit. Note the trade-off: the physical model captures the
sales-floor cooling effect (real, and the whole reason to model refrigeration physically) but adds
simulation objects and failure modes. If you recommend a **hybrid** (physical for SuperMarket, lumped
walk-ins elsewhere), say so and justify.

## Output format (follow exactly)

1. **Lead with Tables 1–5 fully populated.**
2. Then Part C recommendation (lumped vs physical vs hybrid).
3. SI + IP; state the store-size / case-mix basis for every per-store figure.
4. **"Confidence and caveats":** firm DOE-supermarket values vs estimated; case-credit magnitude
   uncertainty; how to scale a single reference supermarket to OpenUBEM's range of footprints.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Give the zone case-credit fractions** (Table 5) — this is the entire physical-realism justification
  for modelling refrigeration; do not leave it blank.
- **Give BOTH** a lumped intensity (Table 1) AND physical parameters (Tables 2–4), so the manager can
  choose fidelity.
- **State the store-size basis** for every per-store value (case length per m² sales floor, etc.).
- **No fabricated precision;** flag GAPs with a defensible default.
- **Primary sources first** (DOE Commercial Reference Supermarket, EnergyPlus Refrigeration references,
  ASHRAE Refrigeration Handbook).
- **Stay on topic.** If it is not a refrigeration number, its basis, or its source, cut it.
