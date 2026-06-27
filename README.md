# OpenUBEM

**Open-source Urban Building Energy Modeling platform.**

OpenUBEM takes a city neighbourhood — defined by an address, a coordinate, a bounding box, or an OSM XML export — and estimates the **annual energy use** and **carbon emissions** of every building in it. It does so by mapping each building to an archetype-based EnergyPlus simulation, running a full-year whole-building energy model per building, and aggregating results into neighbourhood-level metrics.

The platform is designed for urban planners, energy researchers, and policy makers who need building-level energy-use estimates at neighbourhood or district scale without requiring per-building audits or metered data.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Pipeline — Step by Step](#pipeline--step-by-step)
   - [Step 1 — Data Acquisition](#step-1--data-acquisition)
   - [Step 2 — Semantic Enrichment](#step-2--semantic-enrichment)
     - [Step 2.0 — Building Classification](#step-20--building-classification)
     - [Step 2.1 — Climate Zone & Weather](#step-21--climate-zone--weather)
     - [Step 2.2 — Physics Enrichment](#step-22--physics-enrichment)
   - [Step 3 — IDF Generation](#step-3--idf-generation)
   - [Step 4 — EnergyPlus Simulation](#step-4--energyplus-simulation)
   - [Step 5 — Results, Carbon & Validation](#step-5--results-carbon--validation)
3. [Project Layout](#project-layout)
4. [Data Assets](#data-assets)
5. [Configuration & Constants](#configuration--constants)
6. [Run Scripts](#run-scripts)
7. [Test Suite](#test-suite)
8. [Requirements & Installation](#requirements--installation)
9. [Quick Start](#quick-start)
10. [Status & Validation](#status--validation)
11. [License](#license)

---

## Architecture Overview

OpenUBEM is a **5-stage pipeline** where each stage writes versioned artifacts (GeoPackage, Parquet, JSON) consumed by the next. Stages can be re-run independently:

```
  ┌──────────────┐    ┌──────────────────┐    ┌────────────────┐    ┌──────────────┐    ┌────────────────────┐
  │  Step 1      │    │  Step 2          │    │  Step 3        │    │  Step 4      │    │  Step 5            │
  │  Data        │ →  │  Semantic        │ →  │  IDF           │ →  │  EnergyPlus  │ →  │  Results           │
  │  Acquisition │    │  Enrichment      │    │  Generation    │    │  Simulation  │    │  Carbon & Validate │
  └──────────────┘    └──────────────────┘    └────────────────┘    └──────────────┘    └────────────────────┘
  01_buildings_       02_classified.gpkg      03_idf_manifest       04_simulation_      05_results.gpkg
  clean.gpkg          02a_climate.gpkg        + idfs/*.idf          manifest.parquet    05_summary.json
                      02b_enriched.gpkg                                                 figures/
```

**Key design principles:**

- **Archetype-based.** Each building is mapped to one of 30 DOE/OpenStudio archetypes (e.g., MidriseApartment, LargeOffice, Hospital) via a rule-based classifier.
- **Per-building simulation.** Every building gets its own EnergyPlus IDF with true footprint geometry (not a shoe-box proxy), extruded to actual height, with neighbourhood context shading.
- **Deterministic & reproducible.** Seeded RNG for all stochastic operations; versioned artifact schemas with provenance columns.
- **Resume-capable.** The simulation step writes a manifest so partially-completed runs can be resumed without re-simulating successful buildings.
- **Metered-energy basis.** HVAC is modelled with packaged equipment (PTAC) carrying per-archetype efficiencies, so heating/cooling energy come from EnergyPlus end-use meters — directly comparable to metered utility data, not raw thermal loads.
- **Measured-data validated.** Results are scored against independent measured benchmarks (NYC Local Law 84, LA EBEWE, national CBECS 2018) with all gates evaluated report-only, never tuned to pass.

---

## Pipeline — Step by Step

### Step 1 — Data Acquisition

**Module:** `openubem/acquisition/osm_fetcher.py`

Downloads building footprints and attributes from OpenStreetMap via [OSMnx](https://github.com/gboeing/osmnx). Accepts four input modes:

| Mode | Parameter | Description |
|---|---|---|
| Address | `location="Boston, MA"` | Geocoded address + radius |
| Point | `location=(42.36, -71.06)` | Lat/lon coordinate + radius |
| Bbox | `bbox=(N, S, E, W)` | Bounding box |
| XML | `osm_path="file.osm"` | Pre-downloaded OSM XML |

**Processing pipeline (7-step clean):**

1. Drop null/empty geometry rows
2. Keep only Polygon/MultiPolygon geometries
3. Explode MultiPolygons → individual Polygon parts with re-keyed `osm_id`
4. `buffer(0)` geometry repair + validity filter
5. Compute `footprint_area_m2` and `perimeter_m`
6. Minimum area filter (≥ 20 m²)
7. Overlap resolution — near-duplicate footprints (IoU > 0.95) resolved by keeping the larger polygon

**Tag flattening & parsing:**

- `building_tag`, `function_tag` ← OSM `building`, `amenity`, `shop`, `office` tags
- `height_m` ← parsed from string (handles metres and feet with unit conversion)
- `levels` ← `building:levels` (nullable Int64)
- `year_built` ← `start_date` (4-digit year or century notation)
- `postcode`, `underground`, `roof_shape`, `roof_height_m` ← extracted where available
- `surplus_tags` ← all remaining OSM tags captured as JSON

**Provenance & quality tracking:**

Each row carries provenance columns (`provenance_levels`, `provenance_height_m`, `provenance_year_built`, `provenance_building_tag`, `provenance_function_tag`, `provenance_postcode`, `provenance_geometry`) and a composite `data_quality_flag` (e.g., `no_floors,no_height,generic_tag`).

**Output:** `01_buildings_clean.gpkg` — 23-column GeoDataFrame in UTM CRS + sidecar schema JSON and cleaning log.

---

### Step 2 — Semantic Enrichment

Enrichment is split into three sub-steps that progressively add columns to the GeoDataFrame: 23 → 26 → 29 → 57 columns.

#### Step 2.0 — Building Classification

**Module:** `openubem/semantic/building_classifier.py`

Maps each building to one of **30 OpenStudio archetypes** using a rule-based classifier with 17 rules organized by priority:

| Priority | Rule | Example output |
|---|---|---|
| 1a–1b | Super-tall / tall (≥ 40 / ≥ 20 floors, commercial) | `SuperTallBuilding`, `TallBuilding` |
| 2a–2b | Residential tier (≥ 9 / < 9 floors) | `HighriseApartment`, `MidriseApartment` |
| 3a–3b | Lodging tier (hotel ≥ 4 / < 4 floors) | `LargeHotel`, `SmallHotel` |
| 4–11 | Function-tag direct rules | `Hospital`, `Outpatient`, `College`, `Warehouse`, etc. |
| 12a–12c | Commercial use-class + size buckets | `SmallOffice`, `MediumOffice`, `LargeOffice` |
| 13–14 | Use-class fallbacks (industrial, institutional) | `Warehouse`, `Courthouse` |
| 15–16 | Mixed-use dominant-tag routing | Recursive sub-evaluation |
| 17 | Unknown fallback | `OpenUBEMUnknown` |

**Key features:**
- **Levels imputation** — when OSM `levels` is missing, the classifier infers floor count from `height_m` ÷ 3.5 m, or defaults to 1.
- **Confidence scoring** — each assignment gets `HIGH`, `MEDIUM`, or `LOW` confidence based on data quality (observed vs. imputed inputs, tag specificity).
- **Detailed office variant** — optionally promotes `SmallOffice`/`MediumOffice`/`LargeOffice` to their `*Detailed` counterparts.
- **User overrides** — CSV-based per-building override of archetype assignment.

**Output:** 26-column GeoDataFrame (23 upstream + `archetype_id`, `archetype_confidence`, `archetype_source`) saved as `02_buildings_classified.gpkg` + distribution CSV.

#### Step 2.1 — Climate Zone & Weather

**Module:** `openubem/acquisition/__init__.py` (orchestrator) + `openubem/acquisition/climate_zone.py` + `openubem/acquisition/epw_manager.py`

Assigns each building its **ASHRAE climate zone** (16-token vocabulary: `1A`–`8`) via spatial join against a bundled ASHRAE climate zone GeoPackage, then resolves and downloads the closest **EPW weather file** from climate.onebuilding.org.

**EPW station resolution:**
1. Compute the neighbourhood's representative geographic point
2. Search the bundled `epw_stations.csv` catalogue (all One Building stations) for the nearest station within 300 km
3. Fetch the EPW file (user-provided directory > network download > cached)
4. Validate the downloaded file integrity

**Output:** 29-column GeoDataFrame (26 upstream + `climate_zone`, `epw_path`, `provenance_climate_zone`) saved as `02a_buildings_climate.gpkg` + `02a_climate_epw.parquet` sidecar.

#### Step 2.2 — Physics Enrichment

**Module:** `openubem/semantic/__init__.py` (orchestrator) + `construction_sets.py` + `loads.py` + `schedules.py` + `imputation.py`

Appends **28 physics columns** to each building row, transforming the 29-column input into a 57-column enriched GeoDataFrame:

**Envelope properties (14 columns):**
- `vintage_standard` — ASHRAE 90.1 standard era (e.g., `DOERefPre1980`, `90.1-2019`) resolved from `year_built`
- U-values: `u_roof_w_m2k`, `u_wall_w_m2k`, `u_window_w_m2k`, `u_floor_w_m2k` — looked up from a bundled ASHRAE 90.1-2019 construction table keyed by (archetype, climate zone, vintage)
- `shgc_window` — solar heat gain coefficient
- `assembly_roof`, `assembly_wall` — assembly description strings
- `infiltration_m3_s_m2` — envelope air leakage rate
- Provenance columns for each property

**Internal loads (14 columns):**
- `lighting_w_m2`, `equipment_w_m2` — lighting and equipment power densities
- `occupant_m2_per_person` — occupant density
- `heating_setpoint_c`, `cooling_setpoint_c` — thermostat setpoints
- `heating_setback_c`, `cooling_setup_c` — setback/setup temperatures
- `wwr` — window-to-wall ratio
- Provenance columns for each property

**Load modes:**
- `deterministic` (default) — exact archetype-specific lookup values
- `probabilistic` — KDE-resampled perturbation of density values for Monte Carlo analysis

**OpenUBEMUnknown handling:**
Buildings that could not be classified receive donor properties from `MediumOffice@DOERefPre1980` with probabilistic density estimation (PDE) for range coverage.

**Schedule library:**
For each unique archetype in the fleet, an 8760-hourly schedule library is built from bundled DOE prototype schedule data (occupancy, lighting, equipment, heating/cooling setpoint profiles) and serialized as `02b_schedule_library.json`.

**Output:** `02b_buildings_enriched.gpkg` (57 columns) + schema JSON + schedule library JSON.

---

### Step 3 — IDF Generation

**Module:** `openubem/idf/builder.py` (orchestrator) + `openubem/idf/surfaces.py` + `openubem/idf/hvac.py` + `openubem/idf/outputs.py`

**Supporting:** `openubem/geometry/footprint.py` + `openubem/geometry/zoning.py` + `openubem/geometry/context.py`

Converts each enriched building row into a complete **EnergyPlus Input Data File (IDF)** ready for simulation:

**3A — Footprint simplification:**
Multi-step Douglas-Peucker simplification cascade (0.5 m → 1.5 m → convex hull → bounding box) to keep vertex count ≤ 120 while preserving shape fidelity.

**3B — Thermal zoning:**
Three strategies based on archetype and footprint area:

| Strategy | Condition | Description |
|---|---|---|
| `single_zone` | 1-floor buildings | One thermal zone for the whole building |
| `one_zone_per_floor` | Multi-floor < 500 m² or residential/tall | One zone per floor |
| `perimeter_core` | Multi-floor ≥ 500 m² commercial | Core + perimeter zoning per floor (4.57 m depth) |

**3C — Context discovery:**
Neighbouring buildings within a 30 m radius are discovered and injected as shading surfaces, accounting for inter-building solar obstruction.

**3D — Schedule injection:**
Archetype-specific hourly schedules (occupancy, lighting, equipment, thermostat setpoints) written directly into the IDF.

**3E — 3D geometry extrusion:**
Footprint polygons extruded via geomeppy's `add_block()` to actual building height. Interzone surface integrity is validated (vertex-count mismatches fail the building at generation time, not runtime).

**3F — Construction assignment:**
- Opaque assemblies (roof, wall, floor) as `Material:NoMass` objects with R-value = 1/U
- Glazing via `WindowMaterial:SimpleGlazingSystem` with archetype-specific U-factor and SHGC
- Window-to-wall ratio applied via `set_wwr()`
- Per-zone infiltration via `ZoneInfiltration:DesignFlowRate`

**3G — Internal loads:**
`People`, `Lights`, `ElectricEquipment`, and `HVACTemplate:Thermostat` objects created for every thermal zone.

**3H — HVAC:**
Packaged Terminal Air Conditioner (`HVACTemplate:Zone:PTAC`) per thermal zone, parameterised by a per-archetype rated cooling COP and heating-coil type (gas or electric) from `data/loads/hvac_cop_by_archetype.json` (30/30 archetypes). This emits **metered** HVAC electricity and gas, so reported heating/cooling energy reflect real equipment efficiency rather than ideal thermal loads. (Supersedes the earlier `IdealLoadsAirSystem` abstraction, which remains the documented Phase-1 baseline.)

**3I — Output variables:**
Hourly reporting of zone-level energy, operative temperature, and occupant count.

**Template routing:**
Four base IDF templates selected by archetype family:
- `residential_base.idf` — apartments
- `highrise_base.idf` — tall/super-tall buildings
- `specialized_base.idf` — laboratories, data centres, warehouses
- `commercial_base.idf` — everything else (default)

**Parallelisation:** Optional joblib/loky process pool for multi-core IDF generation.

**Output:** `03_idf_manifest.parquet` (one row per building with generation status) + `idfs/*.idf` files.

---

### Step 4 — EnergyPlus Simulation

**Module:** `openubem/simulation/runner.py` (single-building runner) + `openubem/simulation/parallel.py` (fleet orchestrator)

Runs EnergyPlus 23.1 on the entire building fleet in parallel:

**4A — Task construction:**
Each simulable building (generation status = `success`) becomes a `SimTask(osm_id, idf_path, epw_path, work_dir)`.

**4B — Resume detection:**
Before running, each work directory is checked for successful completion (presence of `eplusout.end` + `eplusout.sql` with success marker). Completed buildings are skipped; stale crash debris is cleaned up.

**4C — Version handshake:**
Before any dispatch, `energyplus --version` is called to verify the installed version matches the expected `23.1`.

**4D — Parallel dispatch:**
Fresh tasks fan out via `joblib.Parallel` with configurable worker count. Each worker:
1. Launches `energyplus -w <epw> -d <workdir> -x -r <idf>` as a subprocess
2. `-x` flag runs ExpandObjects (required for HVACTemplate objects)
3. `-r` flag runs ReadVarsESO to produce `eplusout.csv` (CSV fallback for Step 5)
4. Enforces a per-building timeout (default 3600 s)
5. Classifies the outcome:

| Status | Condition |
|---|---|
| `success` | `eplusout.end` contains success marker + `eplusout.sql` exists |
| `success_cached` | Resume hit (previously completed successfully) |
| `failed_timeout` | Subprocess killed at timeout |
| `failed_crash` | No `eplusout.end` file produced |
| `failed_fatal` | `eplusout.end` contains fatal error marker |
| `not_attempted_invalid_idf` | IDF generation failed in Step 3 |

**4E — File purging:**
After successful simulation, non-essential files are purged from each work directory. Retained files: `eplusout.sql`, `eplusout.csv`, `eplusout.mtr`, `eplusout.err`, `eplusout.end`, `eplustbl.htm`, `openubem_run.log`.

**4F — Manifest:**
All results (fresh, cached, skipped) are assembled into `04_simulation_manifest.parquet` with 11 columns: `osm_id`, `idf_path`, `work_dir`, `sql_path`, `status`, `n_warnings`, `n_severe`, `wall_clock_s`, `ep_version`, `epw_path`, `error_summary`.

**Output:** `04_simulation_manifest.parquet` + per-building work directories containing EnergyPlus output files.

---

### Step 5 — Results, Carbon & Validation

**Module:** `openubem/results/__init__.py` (orchestrator) + `parser.py` + `carbon.py` + `aggregator.py` + `service_loads.py` + `visualization.py` + `plotting_suite.py`

Parses simulation outputs, computes energy metrics, converts to emissions, and validates against benchmarks:

**5A — SQL/CSV parsing (`parser.py`):**
- Primary: extract hourly reporting data from `eplusout.sql` via SQLite queries
- Fallback: parse `eplusout.csv` (ReadVarsESO output) if SQL is unavailable
- Energy unit conversion: J → kWh at the parse boundary

**5B — Zone integrity check:**
- Regex-based zone name resolution against the expected building's `osm_id`
- I2 invariant: foreign `osm_id` in a work directory aborts the entire run
- Zone count verification against the IDF manifest

**5C — EUI computation:**
Energy Use Intensity metrics (kWh/m²/yr) computed per building from **metered** EnergyPlus end-use sources:

| Metric | EnergyPlus source |
|---|---|
| `heating_eui_kwh_m2` | `Heating:Electricity` + `Heating:NaturalGas` meters (all-fuel site energy) |
| `cooling_eui_kwh_m2` | `Cooling:Electricity` meter |
| `lighting_eui_kwh_m2` | Zone Lights Electricity Energy |
| `equipment_eui_kwh_m2` | Zone Electric Equipment Electricity Energy |
| `fans_eui_kwh_m2` | `Fans:Electricity` meter (reported separately) |
| `total_eui_kwh_m2` | heating + cooling + lighting + equipment (fans reported but not folded into the total) |

Floor area denominator = `footprint_area_m2 × num_floors`.

**5D — Indoor Overheating Degree (IOD):**
Adaptive thermal comfort metric computed over summer months (June–September):
- Comfort threshold: Tₙ + 2.5 °C where Tₙ = 0.31 × T̄ₘₒₙₜₕₗᵧ + 17.8
- Occupant-count-weighted mean across all zones
- Flags `IOD_NO_OCCUPIED_HOURS` when no occupied summer hours exist

**5E — Carbon emissions (`carbon.py`):**
Five GWP (Global Warming Potential) columns (kg CO₂e/m²) computed per building under the **`load_referenced_v1`** convention:
- **Heating:** EUI × 0.181 kg CO₂e/kWh (natural gas emission factor)
- **Cooling, Lighting, Equipment:** EUI × state-specific eGRID 2022 electricity emission factor

**5F — Spatial join & aggregation (`aggregator.py`):**
- 14 Step-5 columns LEFT-joined onto the 57-column enriched GeoDataFrame → 71-column results GeoDataFrame
- Neighbourhood summary statistics: fleet-wide mean EUI, total emissions, simulation success rate, etc.

**5G — Validation gates (`__init__.py`):**
CBECS 2018 (Commercial Buildings Energy Consumption Survey) validation when a reference dataset is provided:

| Gate | Metric | Threshold |
|---|---|---|
| CV(RMSE) | Quantile-matched RMSE vs. weighted CBECS distribution | < 30% |
| NMBE | Normalised Mean Bias Error | < 10% |
| R² | Archetype-level Pearson correlation with PBA-matched CBECS means | > 0.6 |
| KS D | Kolmogorov–Smirnov statistic vs. weighted CBECS CDF | < 0.10 |

Exclusions: residential apartments, data centres excluded from all gates; `OpenUBEMUnknown` excluded from R² only.

**5H — Visualisation (`visualization.py`, `plotting_suite.py`):**
Automated figure generation: spatial EUI maps with basemap tiles, ordered archetype charts, validation comparison plots. All outputs saved to `openubem/outputs/`.

**5I — Service-loads reconstruction (`service_loads.py`, reporting layer):**
EnergyPlus simulates four end-uses (heating, cooling, lighting, plug equipment); metered building energy also carries service loads the archetype models omit (DHW, pumps, process, and other "Other" loads). The reporting layer reconstructs a measured-comparable `total_eui_reconstructed_kwh_m2` by dividing the modelled total by the modelled-energy fraction drawn from CBECS 2018 end-use splits. Fractions are **region-aware** — per-census-division (mid-Atlantic / Pacific / West-South-Central) where available, with national fallback — so the uplift tracks regional end-use mix without any anchor fitting. This is post-processing: it appends columns and never mutates the simulated EUIs.

**Output:** `05_results.gpkg` + `05_summary.json` + `figures/` directory.

---

## Project Layout

```
openubem/                          # Core pipeline source code
├── __init__.py
├── config.py                      # Global constants and path configuration
├── acquisition/                   # Step 1 & 2.1
│   ├── __init__.py                #   Step 2.1 orchestrator (enrich_climate)
│   ├── osm_fetcher.py             #   Step 1: OSM ingest, clean, schema-validate
│   ├── climate_zone.py            #   ASHRAE climate zone spatial join
│   └── epw_manager.py             #   EPW station resolution and download
├── semantic/                      # Step 2.0 & 2.2
│   ├── __init__.py                #   Step 2.2 orchestrator (enrich_semantics)
│   ├── building_classifier.py     #   Step 2.0: 30-archetype rule classifier
│   ├── construction_sets.py       #   Envelope U-value lookups
│   ├── loads.py                   #   Internal load density lookups
│   ├── schedules.py               #   8760-hourly schedule builder
│   └── imputation.py              #   Missing-value imputation helpers
├── geometry/                      # Shared geometry utilities
│   ├── footprint.py               #   Footprint simplification, num_floors
│   ├── zoning.py                  #   Thermal zoning strategy
│   └── context.py                 #   Context building discovery (shading)
├── idf/                           # Step 3
│   ├── builder.py                 #   Per-building IDF orchestrator + run_step3
│   ├── surfaces.py                #   3D extrusion, interzone matching, adiabatic
│   ├── hvac.py                    #   PTAC HVAC assignment (per-archetype COP)
│   ├── outputs.py                 #   EnergyPlus output variable injection
│   └── templates/                 #   Base IDF templates (4 variants)
├── simulation/                    # Step 4
│   ├── runner.py                  #   Single-building subprocess + classify
│   └── parallel.py                #   Fleet fan-out, resume, manifest
├── results/                       # Step 5
│   ├── __init__.py                #   Results orchestrator + CBECS validation
│   ├── parser.py                  #   SQL/CSV hourly-data extraction + EUI + IOD
│   ├── carbon.py                  #   GWP computation via eGRID factors
│   ├── aggregator.py              #   Spatial join + neighbourhood summary
│   ├── service_loads.py           #   Service-loads reconstruction (regional CBECS fractions)
│   ├── visualization.py           #   Basic map/chart rendering
│   └── plotting_suite.py          #   Advanced multi-figure plotting
├── data/                          # Bundled reference data
│   ├── osm_to_use_class.json      #   OSM tag → use-class mapping
│   ├── openstudio_archetypes.json #   30-archetype vocabulary definition
│   ├── cbecs_pba_map.json         #   Archetype → CBECS PBA code mapping
│   ├── epw_stations.csv           #   Global EPW station catalogue
│   ├── climate_zones/             #   ASHRAE CZ shapefile (GeoPackage)
│   ├── construction/              #   ASHRAE 90.1-2019 envelope tables
│   ├── loads/                     #   DOE load densities + per-archetype HVAC COP
│   ├── schedules/                 #   DOE prototype hourly schedules
│   ├── carbon/                    #   eGRID 2022 emission factors
│   └── service_loads/             #   End-use fraction tables (national + regional)
└── outputs/                       # Generated figures and results
    ├── simulationResults/
    ├── validaitonResults/
    └── comparisons/

scripts/                           # End-to-end run scaffolds
├── run_r3_fleet.py                #   Full-chain Boston fleet run (Steps 2–5)
├── run_r3_step5.py                #   Step 5 standalone re-run
├── run_r3_gates_report.py         #   CBECS validation gate report
├── run_r3_gen_only.py             #   Step 3 IDF generation only
├── run_t12_boston.py               #   Legacy Boston run
├── run_c4_regen.py                #   Configuration iteration run
├── run_c4_build_manifest.py       #   Manifest rebuild utility
├── run_r1_t12.py                  #   R1 targeted run
├── run_r1_targeted.py             #   Targeted single-building debug
├── render_plots.py                #   Standalone plot rendering
├── build_construction_tables.py   #   Rebuild envelope data from ASHRAE sources
├── build_loads_tables.py          #   Rebuild load density data
├── build_schedules_json.py        #   Rebuild schedule data from DOE prototypes
├── build_epw_stations_csv.py      #   Rebuild EPW station catalogue
├── build_climate_zones_gpkg.py    #   Rebuild climate zone GeoPackage
├── build_egrid_json.py            #   Rebuild eGRID emission factor data
├── extract_cbecs_reference.py     #   Extract CBECS reference dataset
├── reconstruct_service_loads.py   #   Reconstruct service load fractions
├── cluster/                       #   HPC/SLURM cluster utilities
├── diagnostics/                   #   Debugging and diagnostic tools
└── validation/                    #   Validation analysis scripts

tests/                             # Pytest suite
├── conftest.py
├── fixtures/                      #   Golden test data (GeoPackage, SQL)
├── test_osm_fetcher.py            #   Step 1 unit tests
├── test_building_classifier.py    #   Step 2.0 classifier tests
├── test_climate_zone.py           #   Step 2.1 climate zone tests
├── test_epw_manager.py            #   Step 2.1 EPW manager tests
├── test_construction_sets.py      #   Step 2.2 envelope tests
├── test_loads.py                  #   Step 2.2 loads tests
├── test_schedules.py              #   Step 2.2 schedule tests
├── test_imputation.py             #   Imputation tests
├── test_footprint.py              #   Geometry simplification tests
├── test_zoning.py                 #   Thermal zoning tests
├── test_context.py                #   Context discovery tests
├── test_surfaces.py               #   Surface extrusion tests
├── test_idf_builder.py            #   Step 3 IDF builder tests
├── test_hvac.py                   #   HVAC assignment tests
├── test_outputs.py                #   Output variable tests
├── test_sim_runner.py             #   Step 4 runner unit tests
├── test_sim_parallel.py           #   Step 4 parallel orchestration tests
├── test_sim_integration.py        #   Step 4 integration tests (EnergyPlus)
├── test_results_parser.py         #   Step 5 parser tests
├── test_results_carbon.py         #   Step 5 carbon calculation tests
├── test_results_aggregator.py     #   Step 5 aggregation tests
├── test_service_loads.py          #   Service load tests
├── test_plotting_suite.py         #   Plotting tests
└── test_step*_orchestrator.py     #   Per-step orchestrator integration tests

docs/                              # Design specifications (read-only)
├── docs_main/                     #   Cross-cutting OVERVIEW, DESIGN, flowcharts
├── docs_step1/                    #   Step 1 specs
├── docs_step2/                    #   Step 2.0 specs
├── docs_step-2-1/                 #   Step 2.1 specs
├── docs_step-2-2/                 #   Step 2.2 specs
├── docs_step3/                    #   Step 3 specs
├── docs_step-4/                   #   Step 4 specs
├── docs_step-5/                   #   Step 5 specs
├── validations/                   #   Validation methodology
└── examples/                      #   Usage examples

Data Imputation/                   # ML-based data imputation (experimental)
├── local_data_classifier.ipynb    #   Local data enrichment classifier
├── u_val_classifier_scaled.ipynb  #   U-value prediction model
├── Datasets/                      #   Training data
└── Models/                        #   Saved model artefacts

notebooks/                         # Standalone analysis notebooks
└── IP1_UBEMOccDataGenerate.ipynb  #   Occupancy data generation notebook
```

---

## Data Assets

All bundled reference data lives under `openubem/data/`:

| Asset | File | Description |
|---|---|---|
| OSM tag map | `osm_to_use_class.json` | Maps ~100 OSM building/amenity/shop/office tags to 5 use-classes (residential, commercial, industrial, institutional, unknown) |
| Archetype vocabulary | `openstudio_archetypes.json` | 30 DOE/OpenStudio archetype definitions |
| CBECS PBA map | `cbecs_pba_map.json` | Maps archetypes to CBECS 2018 Principal Building Activity codes |
| EPW catalogue | `epw_stations.csv` | ~2,800 global weather stations with coordinates and download URLs |
| Climate zones | `climate_zones/*.gpkg` | ASHRAE Standard 169 climate zone polygons |
| Envelope tables | `construction/ashrae_90_1_2019.json` | U-values, SHGC, infiltration rates keyed by (archetype, climate zone, vintage) — 7 vintage eras × 16 climate zones × 30 archetypes |
| Internal loads | `loads/doe_prototype_loads.json` + `openstudio_loads.json` | Lighting, equipment, occupant densities and setpoints per archetype |
| HVAC COP | `loads/hvac_cop_by_archetype.json` | Per-archetype rated cooling COP + heating-coil type/efficiency for the PTAC HVAC template (30/30 archetypes) |
| Schedules | `schedules/doe_schedules.json` | 8760-hourly fractional schedules per archetype (occupancy, lighting, equipment, heating, cooling) |
| Carbon factors | `carbon/egrid_2022.json` | EPA eGRID 2022 electricity emission factors by U.S. state (kg CO₂e/kWh) |
| Service loads | `service_loads/enduse_fractions_table4.json` + `enduse_fractions_regional.json` | CBECS 2018 end-use fraction splits — national and per-census-division |

---

## Configuration & Constants

All tuneable parameters live in `openubem/config.py`:

| Constant | Default | Description |
|---|---|---|
| `ENERGYPLUS_PATH` | `C:\EnergyPlusV23-1-0` | EnergyPlus installation directory |
| `ENERGYPLUS_VERSION` | `23.1` | Expected EnergyPlus version |
| `ENERGYPLUS_IDD_PATH` | Auto-resolved | IDD file path (23.1 preferred, eppy bundled fallback) |
| `FLOOR_TO_FLOOR_M` | `3.5` | Default floor-to-floor height (metres) |
| `PERIMETER_DEPTH_M` | `4.57` | Perimeter zone depth for core/perim zoning |
| `DP_TOLERANCE_M` | `0.5` | Douglas-Peucker simplification tolerance (fine) |
| `DP_COARSE_TOLERANCE_M` | `1.5` | Douglas-Peucker simplification tolerance (coarse) |
| `MAX_VERTICES` | `120` | Maximum exterior polygon vertices |
| `SHADING_SPHERE_RADIUS` | `30.0` | Context building discovery radius (metres) |
| `EPW_CACHE_DIR` | `~/.openubem/epw` | Local EPW file cache |
| `EPW_MAX_STATION_KM` | `300.0` | Maximum distance to nearest EPW station |
| `LOAD_MODE` | `deterministic` | Load assignment mode (`deterministic` or `probabilistic`) |
| `RANDOM_SEED` | `42` | Global RNG seed |
| `SIM_TIMEOUT_S` | `3600` | Per-building simulation timeout (seconds) |
| `N_JOBS` | `-1` (all cores) | Parallel simulation worker count (`SLURM_CPUS_PER_TASK` override) |
| `GWP_NATURAL_GAS_KGCO2_KWH` | `0.181` | Natural gas emission factor |
| `GWP_CONVENTION` | `load_referenced_v1` | Carbon accounting convention |
| `IOD_SUMMER_MONTHS` | `(6, 9)` | Summer months for IOD computation (June–September) |
| `EUI_PLAUSIBILITY_BOUNDS` | `(25, 1000)` | Plausible EUI range (kWh/m²/yr) |

**Environment variable overrides:**
- `ENERGYPLUS_PATH` — EnergyPlus installation directory
- `OPENUBEM_ENERGYPLUS_IDD_PATH` — explicit IDD file path
- `OPENUBEM_EPW_CACHE` — EPW cache directory
- `SLURM_CPUS_PER_TASK` — auto-detect cluster parallelism

---

## Run Scripts

The `scripts/` directory contains ready-to-use pipeline runners:

| Script | Description |
|---|---|
| `run_r3_fleet.py` | **Full pipeline** (Steps 2–5) for the Boston test neighbourhood. 483 buildings, 6 parallel workers. |
| `run_r3_step5.py` | Re-run Step 5 only (results aggregation) from existing simulation outputs |
| `run_r3_gates_report.py` | Compute CBECS validation gates and generate report |
| `run_r3_gen_only.py` | Run Step 3 (IDF generation) only |
| `run_t12_boston.py` | Legacy Boston integration run |
| `render_plots.py` | Standalone figure rendering from existing results |

**Data build scripts** (rebuild bundled reference data from source):

| Script | Source |
|---|---|
| `build_construction_tables.py` | ASHRAE 90.1-2019 appendix tables |
| `build_loads_tables.py` | DOE prototype buildings |
| `build_schedules_json.py` | DOE prototype schedule files |
| `build_epw_stations_csv.py` | One Building weather station index |
| `build_climate_zones_gpkg.py` | ASHRAE Standard 169 shapefiles |
| `build_egrid_json.py` | EPA eGRID 2022 dataset |
| `extract_cbecs_reference.py` | CBECS 2018 microdata |

---

## Test Suite

37 test files covering all pipeline stages and validation analyses, run with `pytest`:

```bash
pytest                                    # All tests
pytest -m "not slow"                      # Skip integration tests
pytest -m "not energyplus"                # Skip tests requiring EnergyPlus binary
pytest tests/test_building_classifier.py  # Single module
```

Test markers:
- `slow` — integration tests that hit the network or take significant time
- `energyplus` — tests requiring EnergyPlus 23.1 installed

Golden fixtures (GeoPackage files with known-good data) are stored in `tests/fixtures/`.

---

## Requirements & Installation

**System requirements:**
- Python ≥ 3.10
- EnergyPlus 23.1 installed at `C:\EnergyPlusV23-1-0` (or set `ENERGYPLUS_PATH`)

**Python dependencies** (from `pyproject.toml`):

| Package | Purpose |
|---|---|
| `osmnx ≥ 1.9, < 2.0` | OpenStreetMap data download |
| `geopandas ≥ 0.14` | Geospatial DataFrame operations |
| `shapely ≥ 2.0` | Computational geometry |
| `pandas`, `numpy` | Data manipulation |
| `eppy ≥ 0.5.63, < 1.0` | EnergyPlus IDD/IDF parsing |
| `geomeppy ≥ 0.11.8, < 1.0` | 3D geometry extrusion for EnergyPlus |
| `pyogrio` | Fast vector I/O |
| `pyarrow` | Parquet read/write |
| `pyproj` | Coordinate system transforms |
| `scipy` | Statistical functions (KDE, KS test) |
| `joblib` | Parallel processing |
| `matplotlib` | Plotting |
| `contextily ≥ 1.3` | Basemap tiles for spatial plots |
| `requests` | HTTP downloads (EPW files) |
| `packaging` | Version string comparison |

**Installation:**

```bash
# Clone the repository
git clone https://github.com/orcunkoraliseri/OpenUBEM.git
cd OpenUBEM

# Create virtual environment and install
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e ".[dev]"
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv sync
```

---

## Quick Start

```python
from pathlib import Path
from openubem.acquisition.osm_fetcher import ingest_buildings
from openubem.semantic.building_classifier import BuildingClassifier
from openubem.acquisition import enrich_climate
from openubem.semantic import enrich_semantics
from openubem.idf.builder import run_step3
from openubem.simulation.parallel import run_neighbourhood
from openubem.results import aggregate_results

output = Path("my_neighbourhood")

# Step 1: Download and clean building footprints
gdf = ingest_buildings(location="Boston, MA", radius_m=500, output_dir=output / "step1")

# Step 2.0: Classify buildings into archetypes
classifier = BuildingClassifier()
gdf = classifier.classify(gdf, output_dir=output / "step2")

# Step 2.1: Assign climate zone and fetch weather file
gdf = enrich_climate(gdf, output_dir=output / "step2")

# Step 2.2: Enrich with envelope, loads, and schedules
gdf, schedules = enrich_semantics(gdf, output_dir=output / "step2")

# Step 3: Generate EnergyPlus IDF files
manifest = run_step3(gdf, schedules, output / "step3")

# Step 4: Run EnergyPlus simulations in parallel
sim_manifest = run_neighbourhood(manifest, gdf, output / "sim", n_jobs=6)

# Step 5: Parse results, compute EUI and carbon, validate
results = aggregate_results(sim_manifest, manifest, gdf, output / "results", state="MA")
```

---

## Status & Validation

OpenUBEM has been validated at neighbourhood scale across **three U.S. cities** against independent measured-energy benchmarks. All gates are evaluated report-only — never tuned to pass.

**Validation matrix — 12 cells, 8,160 buildings.** Four density cells (centre / urban / suburban / rural) in each of **New York City, Los Angeles, and Austin** were simulated end-to-end with 100% EnergyPlus success and zero exclusions.

**Adopted baseline:** metered PTAC HVAC + service-loads reconstruction on **regional CBECS end-use fractions** — a **zero-fitted-parameter** model.

| Benchmark | Result |
|---|---|
| City-Overall vs. measured (NYC LL84, LA EBEWE, Austin proxy) | within **±9%** all three cities (NYC +2.1% / LA −3.7% / Austin −8.6%) |
| National CBECS 2018 NMBE | **passing** all three census regions |
| National CBECS 2018 R² | **passing** all three census regions |
| EnergyPlus simulation success | 8,160 / 8,160 (100%) |

Earlier single-city milestones: a 483-building Boston neighbourhood reached 100% simulation success with CBECS gates passing, and a 12-cell matrix (8,152 buildings) confirmed climate-correct city ordering (LA < Austin < NYC total EUI). Distribution-shape gates (CV(RMSE), KS) are structural for an archetype-deterministic UBEM — reported for transparency rather than used as pass/fail.

> Detailed validation methodology, per-cell results, and the full calibration record live under `docs/`.

---

## License

*To be specified.*
