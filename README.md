# OpenUBEM

Open-source Urban Building Energy Modeling platform. Takes a city neighbourhood and estimates the annual energy use and carbon emissions of every building in it, using archetype-based EnergyPlus simulation.

## Pipeline

- **Step 1 — Data acquisition.** Download building footprints and attributes (height, use type, construction year) from OpenStreetMap.
- **Step 2 — Semantic enrichment.** Match each building to an archetype so its physical properties can be inferred.
  - **Step 2.1 — Climate.** Assign each building its ASHRAE climate zone and fetch the matching EPW weather file.
  - **Step 2.2 — Enrichment.** Fill in archetype physics: envelope U-values, window properties, lighting/equipment power densities, occupancy, and schedules.
- **Step 3 — IDF generation.** Convert each enriched building into an EnergyPlus input file: 3D geometry, thermal zones, constructions, internal loads, ideal-loads HVAC.
- **Step 4 — Simulation.** Run EnergyPlus (23.1) on the whole fleet in parallel, one full-year simulation per building, with a resumable run manifest.
- **Step 5 — Results & carbon.** Parse simulation outputs into per-building EUI, convert electricity to CO₂e with regional grid factors, compute overheating/comfort metrics, validate against quality gates, and aggregate to neighbourhood-level maps and summary statistics.

Each step writes a versioned artifact (parquet/GeoPackage) consumed by the next, so steps can be re-run independently.

## Layout

```
openubem/        pipeline source code
scripts/         end-to-end run scaffolds
tests/           pytest suite (incl. golden SQL fixtures)
docs/docs_main/  cross-cutting specs
docs/docs_step*/ per-step specs and implementation plans
```

## Status

Boston test neighbourhood: 483 buildings, 483 successful full-year simulations (100%), all results-validation gates passing. Headline results: mean EUI ≈ 148.7 kWh/m²/yr, total fleet emissions ≈ 359.2 million kgCO₂e, mean indoor overheating degree ≈ 0.03 °C.

## Requirements

- Python 3.14, dependencies in `pyproject.toml`
- EnergyPlus 23.1 installed (default path `C:\EnergyPlusV23-1-0`)
