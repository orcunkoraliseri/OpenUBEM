# Deep-Research Prompt 03 — SERVICE WATER HEATING (DHW) per Archetype

> SCOPE GUARD — READ FIRST. This is a **numeric EnergyPlus-parameter** task for domestic/service hot
> water. The deliverable is, per archetype, the **hot-water demand intensity, supply/inlet
> temperatures, water-heater fuel + efficiency, and zone-gain split** — the numbers that instantiate
> `WaterHeater:Mixed` + `WaterUse:Equipment` + `WaterUse:Connections`. It is NOT plumbing-code
> narrative, fixture selection, or Legionella policy. If you are writing about anything other than a
> **number bound for an EnergyPlus DHW field and its source**, stop and return to the tables.

---

## What this document is

A fill-in-the-blanks request for per-archetype service-hot-water parameters. OpenUBEM Phase-E moves
DHW from a reporting-layer estimate into the simulation. Treat each cell as a question; fill it with a
sourced value or a GAP. See `00_README_phaseE_prompt_set.md` for roster, climate zones, conventions.

## Role

Building-energy-modelling research analyst. Trace every value to: the **DOE/PNNL prototype
documentation and prototype IDFs** (they specify peak flow, schedules, setpoints, water-heater type
and efficiency per building type), **ASHRAE 90.1-2019 §7** + **Table 7.8** (water-heater minimum
efficiency), the **ASHRAE Handbook — HVAC Applications, Service Water Heating** chapter, and the
**EnergyPlus I/O Reference** for field semantics. SI + IP. No fabricated precision.

## Why these numbers (so you scope correctly)

EnergyPlus models DHW as a **peak volumetric flow × a fractional schedule**, drawn through a
`WaterHeater:Mixed` tank with a thermal efficiency and standby loss, mixed from **mains/inlet temp**
up to a **supply setpoint**. The heater fuel (gas vs electric) decides whether DHW shows up on the
gas or electricity meter. A fraction of the water-use energy returns to the **zone as sensible/latent
gain** (e.g., dishwashing, showers); the rest goes down the drain. So we need, per archetype: the
**peak flow and its normalizing basis**, the **schedule**, **setpoint + mains temp**, **heater fuel +
efficiency + standby loss**, and the **sensible/latent zone fractions**.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Hot-water demand intensity (per archetype)

Give the demand in the basis the prototype/source uses AND normalized per floor area so OpenUBEM (which
knows floor area) can apply it. State the basis explicitly.

| Archetype | Peak hot-water flow (value + basis: gal/h·person, gal/day·unit, gal/h·ft², gal/meal) | Annual HW volume intensity (gal/ft²·yr or L/m²·yr) | Peak flow normalized (L/h·m²) | Source |
|---|---|---|---|---|
| MidriseApartment | | | | |
| HighriseApartment | | | | |
| SmallHotel | | | | |
| LargeHotel | | | | |
| Hospital | | | | |
| Outpatient | | | | |
| FullServiceRestaurant | | | | |
| QuickServiceRestaurant | | | | |
| PrimarySchool | | | | |
| SecondarySchool | | | | |
| College | | | | |
| SmallOffice / MediumOffice / LargeOffice | | | | |
| RetailStandalone / RetailStripmall | | | | |
| SuperMarket | | | | |
| Warehouse | | | | |

> For low-DHW types (offices, retail, warehouse) a small handwashing load is fine — give the prototype
> value or "negligible (state value)". Do NOT leave blank.

### Table 2 — Water heater (per archetype or per archetype group)

| Archetype (or group) | Heater fuel | Type (storage / instantaneous) | Thermal efficiency (Et / EF / UEF) | Standby loss (W or %/h) | Supply setpoint (°C / °F) | Cite |
|---|---|---|---|---|---|---|
| Residential (Mid/High apt) | | | | | | |
| Lodging (Small/Large hotel) | | | | | | |
| Healthcare (Hospital/Outpatient) | | | | | | |
| Food service (FSR/QSR) | | | | | | |
| Education (schools/college) | | | | | | |
| Office / retail / warehouse | | | | | | |

### Table 3 — Mains / inlet water temperature by city (seasonal)

| City (climate zone) | Annual-avg mains temp (°C / °F) | Winter low (°C / °F) | Summer high (°C / °F) | Source / method |
|---|---|---|---|---|
| New York City (4A) | | | | |
| Los Angeles (3B) | | | | |
| Austin (2A) | | | | |

> If using the EnergyPlus `Site:WaterMainsTemperature` correlation from annual-average + max-difference
> outdoor air, state that and give the inputs instead of monthly values.

### Table 4 — Zone-gain split & distribution losses

| Parameter | Value | Notes | Source |
|---|---|---|---|
| Fraction of DHW load returned to zone as **sensible** gain | | (showers/dishwashing latent vs drain) | |
| Fraction returned as **latent** gain | | | |
| Fraction lost to **drain** (no zone gain) | | | |
| Recirculation pump present? (by archetype) | | (hotels/hospitals likely yes) | |
| Recirculation pump power / loss adder | | | |

### Table 5 — DHW draw schedule

| Archetype group | Peak-fraction profile | Reference schedule name | Source |
|---|---|---|---|
| Residential | (morning + evening peaks) | (DOE prototype SWH schedule) | |
| Lodging | | | |
| Food service | (meal-time peaks) | | |
| Office/retail | | | |

> Naming the DOE prototype schedule (so we can transcribe its 24-hour fractions) is acceptable in
> place of redrawing the profile — give the schedule name + where it lives.

---

## Output format (follow exactly)

1. **Lead with Tables 1–5 fully populated** (every archetype in Table 1).
2. Supporting prose grouped by sector.
3. SI + IP; state every normalizing basis; show any per-person→per-area conversion (give the
   occupant density or unit-count assumption used).
4. **"Confidence and caveats":** firm prototype values vs estimated; which archetypes have negligible
   DHW; recirculation assumptions.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **Every archetype in Table 1 gets a value** (negligible is a value — state it).
- **State the normalizing basis** for every demand figure and give the per-floor-area normalization.
- **Name the heater fuel** (gas vs electric) per archetype — it routes DHW to the right meter.
- **Mains temps for all three cities.**
- **No fabricated precision;** flag GAPs with a defensible default.
- **Primary sources first** (PNNL prototypes, 90.1-2019 §7/Table 7.8, ASHRAE Applications).
- **Stay on topic.** If it is not a DHW number, its basis, or its source, cut it.
