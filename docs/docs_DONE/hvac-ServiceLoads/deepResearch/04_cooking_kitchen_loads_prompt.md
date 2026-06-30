# Deep-Research Prompt 04 — COOKING / KITCHEN LOADS per Archetype

> SCOPE GUARD — READ FIRST. This is a **numeric EnergyPlus-parameter** task for commercial cooking.
> The deliverable is, per archetype with a kitchen, the **cooking equipment power density, gas/electric
> split, heat-gain fractions, and kitchen exhaust/makeup-air airflow** — the numbers that instantiate
> `OtherEquipment` (gas) / `ElectricEquipment` plus the kitchen ventilation. It is NOT menu design,
> appliance brand selection, or food-safety narrative. If you are writing about anything other than a
> **number bound for an EnergyPlus cooking/ventilation field and its source**, stop and return to the
> tables.

---

## What this document is

A fill-in-the-blanks request for per-archetype cooking parameters. OpenUBEM Phase-E moves cooking from
a reporting-layer estimate into the simulation, primarily for the food-service archetypes but also for
the kitchens embedded in hotels, hospitals, schools, and supermarket delis. See
`00_README_phaseE_prompt_set.md` for roster and conventions.

## Role

Building-energy-modelling research analyst. Trace every value to: the **DOE/PNNL prototype
documentation and prototype IDFs** (the RestaurantSitDown / RestaurantFastFood prototypes specify
cooking gas + electric intensities, schedules, and exhaust), the **ASHRAE Handbook — Fundamentals
(Nonresidential Cooling/Heating Load, kitchen equipment heat gains)** and **HVAC Applications (Kitchen
Ventilation)**, **ASHRAE Standard 154** (commercial kitchen ventilation) for exhaust rates, and the
**EnergyPlus I/O Reference**. SI + IP. No fabricated precision.

## Why these numbers (so you scope correctly)

EnergyPlus models cooking as a **process load** (`OtherEquipment` for gas, `ElectricEquipment` for
electric) with a power density, a schedule, and **heat-gain fractions** (radiant / latent / lost) that
decide how much of the cooking energy lands in the zone vs leaves through the hood. A commercial
kitchen also drives a large **exhaust** airflow with **makeup air** — a real and often dominant HVAC
load in restaurants. So we need: **gas + electric cooking power density**, the **fraction split**, the
**heat-gain fractions**, and the **exhaust + makeup-air cfm**.

---

## REQUIRED OUTPUT TABLES — fill every cell

### Table 1 — Cooking equipment power density (per archetype with a kitchen)

Normalize per **kitchen floor area** AND per **whole-building floor area** (state both; OpenUBEM
applies per whole-building area unless we model a kitchen sub-zone).

| Archetype | Total cooking connected power | Gas density (W/m² and Btu/h·ft²) | Electric density (W/m²) | Gas : electric split (%) | Basis (per kitchen ft² / per building ft²) | Source |
|---|---|---|---|---|---|---|
| FullServiceRestaurant | | | | | | |
| QuickServiceRestaurant | | | | | | |
| LargeHotel (kitchen) | | | | | | |
| Hospital (kitchen) | | | | | | |
| SecondarySchool (kitchen) | | | | | | |
| PrimarySchool (kitchen) | | | | | | |
| College (dining) | | | | | | |
| SuperMarket (deli/bakery) | | | | | | |

> For archetypes without a kitchen (offices, retail, warehouse, apartments) state "no cooking load"
> explicitly — do not leave blank.

### Table 2 — Cooking heat-gain fractions (how much reaches the zone)

| Parameter | Gas equipment | Electric equipment | Notes | Source |
|---|---|---|---|---|
| Fraction **radiant** | | | | |
| Fraction **latent** | | | | |
| Fraction **lost** (captured by hood / to exhaust) | | | | |
| Fraction **convective to zone** (remainder) | | | | |
| With vs without exhaust hood (unhooded appliances) | | | | |

> These fractions are the realism term reconstruction omits — a hooded range dumps most heat to
> exhaust, an unhooded warmer dumps it to the zone. Give ASHRAE Handbook values for hooded equipment.

### Table 3 — Kitchen ventilation (exhaust + makeup air)

| Parameter | FullServiceRestaurant | QuickServiceRestaurant | Notes | Source |
|---|---|---|---|---|
| Kitchen exhaust airflow (cfm, and cfm/ft² of kitchen) | | | | ASHRAE 154 / prototype |
| Hood type / duty (light/medium/heavy/extra-heavy) | | | | |
| Makeup-air fraction (% of exhaust) | | | | |
| Makeup-air conditioning (tempered? unconditioned?) | | | | |
| Exhaust operating schedule | | | | |

### Table 4 — Cooking schedule

| Archetype group | Peak fraction + meal-time profile | Reference schedule name | Source |
|---|---|---|---|
| Restaurants (FSR/QSR) | | (DOE prototype cooking schedule) | |
| Institutional kitchens (hotel/hospital/school) | | | |

> Naming the DOE prototype cooking schedule is acceptable in place of redrawing it — give the name +
> location.

---

## Output format (follow exactly)

1. **Lead with Tables 1–4 fully populated** (every kitchen archetype; "no cooking load" where none).
2. Supporting prose by archetype group.
3. SI + IP; state the normalizing basis (per-kitchen vs per-building) for every density and give both.
4. **"Confidence and caveats":** firm prototype values vs estimated; whether to model a separate
   kitchen sub-zone or apply cooking at building level; exhaust/makeup-air modelling depth.
5. **Reference list** — full citations, dates, URLs.

## Hard requirements

- **State the gas : electric split** for every cooking archetype — it routes cooking to the right meter.
- **Give heat-gain fractions for hooded equipment** (the zone-coupling realism term).
- **Give exhaust + makeup-air airflow for both restaurant types** — often the largest cooking-related
  HVAC load.
- **Both normalizations** (per kitchen ft² and per building ft²), with the kitchen-area assumption.
- **No fabricated precision;** flag GAPs with a defensible default.
- **Primary sources first** (PNNL prototypes, ASHRAE Handbook, ASHRAE 154).
- **Stay on topic.** If it is not a cooking/ventilation number, its basis, or its source, cut it.
