# OpenUBEM — Fundamentals

**What this document is:** a plain-language explanation of what OpenUBEM does, what it
simulates, where, and at what resolution. It is the "start here" overview — no design
specs, no task lists, just the fundamentals. For the detailed reporting methodology see
[`simulated_vs_reconstructed_methodology.md`](simulated_vs_reconstructed_methodology.md);
for the full per-step specification see `docs/docs_main/` and the per-step `docs/docs_stepN/`
folders.

---

## 1. What OpenUBEM does (one paragraph)

OpenUBEM is an **Urban Building Energy Modeling (UBEM)** platform. You give it a
neighbourhood — an address, a coordinate, a bounding box, or an OpenStreetMap export — and
it estimates the **annual energy use** and **carbon emissions** of **every building** in
that neighbourhood. It does this without per-building audits or metered data: each building
is matched to a building *archetype*, turned into a physics-based EnergyPlus model, simulated
for a full year, and rolled up into neighbourhood-level numbers. The intended users are urban
planners, energy researchers, and policy makers who need building-level estimates at
district scale.

---

## 2. The core idea — archetype-based, per-building physics

OpenUBEM does not have a meter on every building. Instead it leans on two ideas:

1. **Archetypes.** Every building is classified into one of **30 standard building types**
   (DOE / OpenStudio archetypes — e.g. `MidriseApartment`, `LargeOffice`, `Hospital`,
   `Warehouse`). The archetype carries the "physics" the OSM data doesn't: envelope
   insulation, internal load densities, operating schedules, and HVAC efficiencies.

2. **Per-building physics simulation.** Each building still gets its **own** EnergyPlus
   model built from its **true footprint** (not a generic box), extruded to its real height,
   and shaded by its real neighbours. The archetype fills in the unknowns; the geometry and
   location are the building's own.

So the output is building-specific even though the inputs are archetype-generalised.

---

## 3. The five-stage pipeline

OpenUBEM runs as a **5-stage pipeline**. Each stage writes a versioned artifact that the
next stage reads, so any stage can be re-run on its own.

| Stage | Name | What it produces |
|---|---|---|
| **1** | Data Acquisition | Downloads + cleans building footprints from OpenStreetMap → `01_buildings_clean.gpkg` |
| **2** | Semantic Enrichment | Classifies each building into an archetype, assigns a climate zone + weather file, and attaches envelope / loads / schedules → `02b_buildings_enriched.gpkg` |
| **3** | IDF Generation | Builds one EnergyPlus input file (`.idf`) per building — geometry, zoning, constructions, loads, schedules, HVAC, shading → `idfs/*.idf` |
| **4** | EnergyPlus Simulation | Runs EnergyPlus on the whole fleet in parallel → `04_simulation_manifest.parquet` |
| **5** | Results, Carbon & Validation | Parses outputs into EUI, converts to carbon, aggregates to neighbourhood level, validates against measured data → `05_results.gpkg` + figures |

---

## 4. What gets simulated

### 4.1 The engine

- **EnergyPlus 23.1** — a whole-building physics engine (heat balance, solar gains,
  conduction, infiltration, internal gains, HVAC).
- **Full year, hourly.** Each building is simulated over an annual run period at **8760
  hourly timesteps**, driven by a real weather file (EPW) for the nearest station.

### 4.2 The end-uses

Each building's IDF carries packaged HVAC (**PTAC** — Packaged Terminal Air Conditioner)
per thermal zone, with a per-archetype rated cooling COP and heating-coil type. Because the
HVAC is real equipment (not an idealised abstraction), EnergyPlus reports **metered**
energy that is directly comparable to a utility bill. The simulation produces:

| End-use | Simulated? | Notes |
|---|---|---|
| Space heating | ✅ | electricity + natural gas, per archetype coil type |
| Space cooling | ✅ | DX electricity via PTAC COP |
| Lighting | ✅ | from archetype lighting power density |
| Plug / equipment | ✅ | from archetype equipment power density |
| Fans | ✅ | metered separately (not folded into the headline total) |
| Pumps / DHW / refrigeration / cooking | ❌ | not modelled — added back in reporting (§6) |

### 4.3 The outputs per building

- **EUI** (Energy Use Intensity, kWh/m²·yr) per end-use and a total.
- **Carbon** (kg CO₂e/m²) — electricity end-uses × state eGRID 2022 factor; heating gas ×
  0.181 kg CO₂e/kWh.
- **IOD** (Indoor Overheating Degree) — a summer thermal-comfort metric.

---

## 5. Simulation resolution

This is the part most people ask about. There are two resolutions: **spatial** (how the
building is divided up) and **temporal** (how time is divided up).

### 5.1 Spatial resolution — one model per building, adaptive thermal zoning

The unit of simulation is **one building = one IDF = one EnergyPlus run**. Inside each
building, the number of **thermal zones** is chosen automatically based on the building's
size and type. It is **not** always single-zone — there are three strategies
(`openubem/geometry/zoning.py`):

| Strategy | When it is used | Zones |
|---|---|---|
| **`single_zone`** | Genuine 1-floor buildings (`num_floors == 1`) | One zone for the whole building |
| **`one_zone_per_floor`** | Multi-floor **residential / tall** buildings, **small** (<500 m²) commercial, or unclassified | One zone per floor |
| **`perimeter_core`** | Multi-floor **commercial ≥ 500 m²** | Core + perimeter zones per floor (4.57 m perimeter depth) |

So a small house is one zone; a 10-storey apartment is ten zones (one per floor); a large
office tower is core+perimeter zones on every floor. The pipeline degrades gracefully —
narrow buildings or courtyard footprints that can't form a valid core fall back to
one-zone-per-floor.

**Floor area** (the denominator for EUI) is always `footprint_area_m2 × num_floors`.

### 5.2 Temporal resolution

- **Annual run period**, **8760 hourly timesteps**.
- Schedules (occupancy, lighting, equipment, thermostat setpoints) are hourly fractional
  profiles drawn from DOE prototype building schedules per archetype.

### 5.3 What the resolution is *not*

OpenUBEM is a **stock-level / neighbourhood** model. It is deliberately not a
detailed-design tool: it does not model individual rooms, specific duct/plant networks,
occupant behaviour per unit, or sub-hourly dynamics. The archetype + adaptive-zoning
approach is the trade-off that makes thousands of buildings tractable.

---

## 6. Reporting: simulated vs. reconstructed energy

EnergyPlus, as configured, meters four end-uses (heating, cooling, lighting, equipment;
fans separately). Real buildings also use energy for pumps, hot water, refrigeration, and
cooking. The **reporting layer** adds those missing service loads back using published
CBECS-2018 end-use fraction splits — producing a "reconstructed" whole-building EUI that is
comparable to a real utility total. This is **post-processing only**: it never re-runs the
simulation or changes the physics. Full method in
[`simulated_vs_reconstructed_methodology.md`](simulated_vs_reconstructed_methodology.md).

---

## 7. Locations

### 7.1 Where it can run

Anywhere OpenStreetMap has building footprints and a weather station exists within ~300 km
(the EPW search radius). The four input modes are address, coordinate, bounding box, or a
pre-downloaded OSM XML file.

### 7.2 Where it has been validated

OpenUBEM has been validated at neighbourhood scale across **three U.S. cities**, in a
**12-cell matrix** (four urban-density cells per city), totalling **8,160 buildings** with
100% EnergyPlus success:

| City | Density cells | Measured benchmark |
|---|---|---|
| **New York City** | centre / urban / suburban / rural | NYC Local Law 84 (LL84) |
| **Los Angeles** | centre / urban / suburban / rural | LA EBEWE |
| **Austin** | centre / urban / suburban / rural | CBECS proxy |

All buildings are also scored against the **national CBECS 2018** survey across three census
regions (mid-Atlantic, Pacific, West-South-Central). Every validation gate is **report-only
— never tuned to pass**.

**Headline result (adopted baseline):** city-overall EUI within **±9%** of measured in all
three cities (NYC +2.1% / LA −3.7% / Austin −8.6%), with national CBECS NMBE and R² passing
in all three regions — using a **zero-fitted-parameter** model.

---

## 8. Two properties worth knowing

- **Deterministic & reproducible.** All stochastic operations use a seeded RNG; artifacts
  carry provenance columns and versioned schemas. The same inputs give the same outputs.
- **Resume-capable.** Step 4 writes a manifest, so a partially-completed fleet run resumes
  without re-simulating buildings that already succeeded — important at city scale.

---

## 9. Where to go next

| You want… | Read |
|---|---|
| The full feature reference | `README.md` (root) |
| The simulated-vs-reconstructed energy method | `docs/docs_EXPLANATION/simulated_vs_reconstructed_methodology.md` |
| The binding design specs | `docs/docs_main/` (cross-cutting) + `docs/docs_stepN/` (per step) |
| The validation record | `docs/validations/` |
| Current project status | `docs/PROJECT_CHECKLIST.md` |

---

*OpenUBEM — fundamentals overview. Plain-language orientation; the design docs remain the
binding source of truth. 2026-06-26.*
