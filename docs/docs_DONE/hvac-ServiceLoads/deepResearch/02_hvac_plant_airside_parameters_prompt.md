# Deep-Research Prompt 02 — HVAC PLANT & AIR-SIDE PARAMETERS (efficiency, pumps, fans, loops, economizer)

> SCOPE GUARD — READ FIRST. This is a **numeric EnergyPlus-parameter** task. The deliverable is the
> set of **efficiency, sizing, and operational numbers** needed to instantiate the HVAC systems that
> Prompt 01 assigned — especially the values that make **fans and pumps** physical. It is NOT HVAC
> design narrative, product comparison, or controls philosophy. If you are writing about anything
> other than **a number that goes into an EnergyPlus field, its unit, and its source**, stop and
> return to the tables.

---

## What this document is

A fill-in-the-blanks request for the per-system-type HVAC parameters OpenUBEM Phase-E needs.
It **extends the existing anchor file** `openubem/data/loads/hvac_cop_by_archetype.json` (current
state shown below) by adding the fields that file is missing: **pump power, fan static pressure/power,
chilled-/hot-water loop temperatures, economizer thresholds, and part-load behaviour** — and by
confirming/updating the cooling-COP and heating-efficiency values already there. See
`00_README_phaseE_prompt_set.md` for roster, climate zones, and conventions.

## Role

Building-energy-modelling research analyst. Every value traceable to a named, dated, primary source:
**ASHRAE 90.1-2019** (Tables 6.8.1-1 … 6.8.1-3 for equipment efficiency; §6.5.3.1 fan power
limitation; §6.5.1 economizers; §6.5.6 energy recovery; Appendix G G3.1.2–G3.1.3 for baseline
fan/pump sizing), the **PNNL prototype documentation**, the **ASHRAE Handbook — HVAC Systems &
Equipment**, and the **EnergyPlus Input-Output / Engineering Reference** for field definitions. Give
SI + IP. No fabricated precision; show any kW/ton↔COP or in.w.c.↔Pa conversion.

## Why these numbers (so you scope correctly)

Prompt 01 says *which* system each archetype gets; this prompt says *how efficient and how big* its
parts are. EnergyPlus autosizes capacities and flows from design days, so we do **not** need per-
building capacities — we need the **intensive** parameters EnergyPlus multiplies by autosized flow:
chiller/DX **COP**, boiler **efficiency**, **pump power per unit flow** (W/gpm) + loop **ΔT** +
**pump head**, supply-**fan total static pressure** + **fan total efficiency** (→ W/cfm), minimum
**outdoor air**, and **economizer** enable thresholds by climate zone. These are what move pump and
fan energy from "structurally zero" to "metered."

---

## Current anchor state (Table 0) — what `hvac_cop_by_archetype.json` ALREADY has

Confirm or update each; ADD the missing parameters in the tables that follow. (Source for all rows:
DOE/PNNL STD2022 "Buffalo" prototypes, as recorded in the file.)

| Archetype | cooling_cop | central_plant | raw_chiller_cop | plant_factor | heating_coil_type | heating_efficiency |
|---|---|---|---|---|---|---|
| SmallOffice | 4.53 | no | — | — | Gas | 0.84 |
| MediumOffice | 3.74 | no | — | — | Gas | 0.84 |
| LargeOffice | 5.18 | yes | 6.908 | 0.75 | Gas | 0.945 |
| RetailStandalone | 3.57 | no | — | — | Gas | 0.88 |
| RetailStripmall | 3.99 | no | — | — | Gas | 0.88 |
| SuperMarket | 3.0 | no | — | — | Gas | 0.80 |
| FullServiceRestaurant | 3.40 | no | — | — | Gas | 0.8505 |
| QuickServiceRestaurant | 3.80 | no | — | — | Gas | 0.84 |
| SmallHotel | 3.81 (PTAC unit) | no | — | — | Gas | 0.80 |
| LargeHotel | 2.331 | yes | 3.108 | 0.75 | Gas | 0.945 |
| MidriseApartment | 4.32 | no | — | — | Gas | 0.84 |
| HighriseApartment | 3.516 | yes | 4.688 | 0.75 | Electric | 4.515 (WSHP COP) |
| Hospital | 4.197 | yes | 5.597 | 0.75 | Gas | 0.945 |
| Outpatient | 3.57 | no | — | — | Gas | 0.84 |
| PrimarySchool | 3.92 | no | — | — | Gas | 0.84 |
| SecondarySchool | 3.46 | no | — | — | Gas | 0.8505 |
| College | 4.32 | yes | 5.766 | 0.75 | Gas | 0.813 |
| Laboratory | 3.59 | no | — | — | Gas | 0.813 |
| Warehouse | 4.11 | no | — | — | Gas | 0.84 |
| Large/SmallDataCenter* | 3.0–4.71 | mixed | up to 6.28 | 0.75 | none | none |
| TallBuilding / SuperTallBuilding | 5.18 | yes | 6.908 | 0.75 | Gas | 0.945 |
| Courthouse / OpenUBEMUnknown | 3.0 (fallback) | no | — | — | Gas | 0.80 |

> `plant_factor 0.75` is an OpenUBEM reporting derate applied to the raw chiller COP. Tell us whether,
> for a **physical** Phase-E model, we should drop that derate and use the raw chiller COP directly
> (since the plant is now actually simulated). This is a GAP for the manager — give your recommendation.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table A — Cooling equipment efficiency (90.1-2019 minimums by type & size)

| Equipment / system | Size bracket | Metric (as published) | Value | Converted COP (W/W) | Cite (90.1 Table) |
|---|---|---|---|---|---|
| PTAC (through-wall) | per cap | EER / COP | | | 6.8.1-4 |
| Packaged single-zone DX (PSZ-AC) | < 65 kBtu/h | SEER2 / EER | | | 6.8.1-1 |
| Packaged single-zone DX (PSZ-AC) | 65–135 kBtu/h | EER / IEER | | | 6.8.1-1 |
| Packaged single-zone DX | 135–240 kBtu/h | EER / IEER | | | 6.8.1-1 |
| Air-cooled chiller | < 150 / ≥ 150 ton | kW/ton / COP / IPLV | | | 6.8.1-3 |
| Water-cooled centrifugal chiller | < 150 / 150–300 / ≥ 600 ton | kW/ton / COP / IPLV | | | 6.8.1-3 |
| Water-cooled positive-displacement (screw/scroll) | by ton | kW/ton / COP / IPLV | | | 6.8.1-3 |

### Table B — Heating equipment efficiency

| Equipment | Size bracket | Metric | Value | Cite |
|---|---|---|---|---|
| Gas furnace (warm-air) | < 225 kBtu/h | AFUE / Et | | 6.8.1-5 |
| Gas furnace | ≥ 225 kBtu/h | Ec / Et | | 6.8.1-5 |
| Gas-fired hot-water boiler | < 300 / ≥ 2,500 kBtu/h | Et / Ec | | 6.8.1-6 |
| Electric resistance | — | (COP 1.0) | 1.0 | — |
| Water-source / air-source heat pump (if used by a prototype) | by cap | COP / HSPF | | 6.8.1-2/-4 |

### Table C — Chilled-water & hot-water LOOP parameters (the pump numbers)

| Parameter | Chilled-water loop | Hot-water loop | Condenser-water loop | Cite |
|---|---|---|---|---|
| Design supply temperature (°C / °F) | | | | |
| Design loop ΔT (°C / °F) | | | | |
| Pump head / design pressure rise (kPa / ft w.c.) | | | | |
| **Pump power per unit flow (W/gpm and W/(L/s))** | | | | App G G3.1.3.5 / .10 |
| Pump motor + impeller efficiency assumed | | | | |
| Pump control (riding-the-curve / VFD / staged) | | | | |
| Primary-only vs primary-secondary | | | | |

> The App G baseline pump power values (e.g. **chilled-water ~22 W/gpm, hot-water ~19 W/gpm,
> condenser-water ~19 W/gpm** — confirm against G3.1.3.5/.10/.11) are the single most important
> numbers in this prompt, since pumps are currently unmodelled. Give the exact 90.1-2019 figures.

### Table D — Air-side / supply-fan parameters (the fan numbers)

| Parameter | PSZ (constant-volume) | VAV (central) | PTAC/PTHP | Cite |
|---|---|---|---|---|
| Supply-fan total static pressure (Pa / in. w.c.) | | | | |
| Fan total efficiency (motor × drive × impeller) | | | | |
| **Resulting fan power (W/cfm and W/(L/s))** | | | | |
| 90.1 §6.5.3.1 fan power limitation (bhp/cfm allowance + adders) | | | | 6.5.3.1 |
| VAV minimum airflow turndown (%) | | (n/a) | | App G G3.1.3.13 |
| Supply-air temperature setpoint (cooling / reset) | | | | |
| Fan operation (cycling vs continuous during occupied) | | | | |

### Table E — Outdoor air & economizer (climate-zone dependent: 2A / 3B / 4A)

| Parameter | Value | By climate zone? | 2A (Austin) | 3B (LA) | 4A (NYC) | Cite |
|---|---|---|---|---|---|---|
| Minimum OA — per person (cfm/person, L/s·person) | | | | | | 62.1-2019 |
| Minimum OA — per area (cfm/ft², L/s·m²) | | | | | | 62.1-2019 |
| Air-side economizer required? (Y/N by CZ & capacity) | | yes | | | | 6.5.1.1 |
| Economizer high-limit shutoff type + setpoint | | yes | | | | 6.5.1.1.3 |
| Energy recovery (ERV) required? (Y/N by CZ & %OA) | | yes | | | | 6.5.6.1 |
| ERV sensible/latent effectiveness if required | | | | | | |
| Demand-controlled ventilation required? | | | | | | 6.4.3.8 |

### Table F — Part-load performance curves

| Item | Recommendation | Source |
|---|---|---|
| Chiller part-load (EIR-f-PLR) curves | (reuse PNNL prototype curves? EnergyPlus dataset?) | |
| DX coil performance curves | | |
| Fan/pump part-load (VFD) curves | | |

> We expect the answer here is "reuse the curves embedded in the PNNL prototype IDFs / EnergyPlus
> `Curve` datasets" rather than novel coefficients — confirm and name the dataset, or flag GAP.

---

## Part C — Sanity arithmetic (show your work)

For a representative **LargeOffice (System 7: VAV + water-cooled chiller + HW boiler)** and a
representative **MediumOffice (System 5/3: packaged)**, show the back-of-envelope that turns your
intensive values into an energy expectation:
- **Fan:** W/cfm × design cfm/ft² → fan W/ft² → annual fan kWh/m² at a stated run-fraction.
- **Pump:** W/gpm × design gpm/ton × tons/ft² → pump W/ft² → annual pump kWh/m².
- State the resulting **expected fans + pumps EUI (kWh/m²·yr)** range so the manager can sanity-check
  the eventual simulated output against it. (CBECS shows fans+pumps ≈ 10–15% of commercial site
  energy — your numbers should land near that.)

## Output format (follow exactly)

1. **Lead with Table 0 (confirm/update) + Tables A–F fully populated.**
2. Then Part C arithmetic + the expected fans/pumps EUI range.
3. SI + IP for every value; show conversions.
4. **"Confidence and caveats":** which values are firm 90.1 minimums vs prototype-specific vs
   estimated; your recommendation on the `plant_factor 0.75` derate (keep vs drop for a physical model);
   any vintage-dependence worth adding.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Give the App G baseline pump power (W/gpm) and the fan static pressure / W-cfm explicitly** — these
  are the headline missing numbers.
- **Economizer + ERV broken out by climate zone 2A / 3B / 4A.**
- **Every value in SI and IP**, with conversions shown.
- **Recommend keep-vs-drop on the 0.75 plant_factor derate** for the physical Phase-E model.
- **No fabricated precision;** mark estimates and show method; flag GAPs.
- **Primary sources first** (90.1-2019 tables, PNNL prototype docs, EnergyPlus references).
- **Stay on topic.** If it is not an EnergyPlus-bound number, its unit, or its source, cut it.
