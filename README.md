# OpenUBEM

**Open-source Urban Building Energy Modeling platform.**

OpenUBEM takes a city neighbourhood (defined by an address, a coordinate, a bounding box, or an OSM XML export) and estimates the **annual energy use** and **carbon emissions** of every building in it. It does so by mapping each building to an archetype-based EnergyPlus simulation, running a full-year whole-building energy model per building, and aggregating results into neighbourhood-level metrics.

The platform is designed for urban planners, energy researchers, and policy makers who need building-level energy-use estimates at neighbourhood or district scale without requiring per-building audits or metered data.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Pipeline: Step by Step](#pipeline-step-by-step)
   - [Step 1: Data Acquisition](#step-1-data-acquisition)
   - [Step 2: Semantic Enrichment](#step-2-semantic-enrichment)
     - [Step 2.0: Building Classification](#step-20-building-classification)
     - [Step 2.1: Climate Zone & Weather](#step-21-climate-zone--weather)
     - [Step 2.2: Physics Enrichment](#step-22-physics-enrichment)
     - [Step 2.3: Input Imputation & Provenance](#step-23-input-imputation--provenance)
   - [Step 3: IDF Generation](#step-3-idf-generation)
   - [Step 4: EnergyPlus Simulation](#step-4-energyplus-simulation)
   - [Step 5: Results, Carbon & Validation](#step-5-results-carbon--validation)
   - [Step 6: Outdoor Microclimate & Thermal Comfort](#step-6-outdoor-microclimate--thermal-comfort-optional)
3. [Simulation Resolution Modes](#simulation-resolution-modes)
4. [Interactive 3D Viewer](#interactive-3d-viewer)
5. [Project Layout](#project-layout)
6. [Data Assets](#data-assets)
7. [Configuration & Constants](#configuration--constants)
8. [Run Scripts](#run-scripts)
9. [Running on an HPC Cluster](#running-on-an-hpc-cluster)
10. [Test Suite](#test-suite)
11. [Requirements & Installation](#requirements--installation)
12. [Quick Start](#quick-start)
13. [Status & Validation](#status--validation)
14. [Documentation Map](#documentation-map)
15. [License](#license)

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
                      02b_enriched.gpkg                                                 figures/ + viewer.html
                                                                                                │
                                                                                                ▼ (read-only, opt-in)
                                                                                    ┌────────────────────────┐
                                                                                    │  Step 6                │
                                                                                    │  Outdoor Microclimate  │
                                                                                    │  & Thermal Comfort     │
                                                                                    └────────────────────────┘
                                                                                    06_mc_*.tif / .gpkg
```

**Step 6 is deliberately not part of that spine.** It answers a different question (*what does it feel like to stand outside in this neighbourhood?*), is invoked explicitly by its own runner, reads Steps 1–5 read-only, and never writes into `05_results.*`. See [Step 6](#step-6-outdoor-microclimate--thermal-comfort-optional).

**Key design principles:**

- **Archetype-based.** Each building is mapped to one of 30 DOE/OpenStudio archetypes (e.g., MidriseApartment, LargeOffice, Hospital) via a rule-based classifier.
- **Per-building simulation.** Every building gets its own EnergyPlus IDF with true footprint geometry (not a shoe-box proxy), extruded to actual height, with neighbourhood context shading.
- **Physically modelled, not reconstructed.** HVAC is dispatched per archetype across **10 real system families** (central VAV with chiller + boiler, PSZ rooftops, PVAV with reheat, fan-coil units, water-loop heat pumps, PTAC/PTHP, CRAC/CRAH, radiant/unit heaters), and DHW, cooking, refrigeration and elevators are real EnergyPlus objects. All reported energy comes from EnergyPlus **meters**, directly comparable to metered utility data and never a post-hoc multiplier.
- **Zero fitted parameters.** No threshold, fraction, or coefficient anywhere in the model is tuned against a simulated or measured EUI target. Every value traces to a cited source (ASHRAE 90.1, DOE prototypes, CBECS, eGRID, IBC).
- **Provenance everywhere.** Every input carries a provenance column and a `data_quality_flag` token recording whether it was observed, imputed, fused from an external source, or filled from a standard default.
- **Deterministic & reproducible.** Seeded RNG for all stochastic operations; versioned artifact schemas.
- **Resume-capable.** The simulation step writes a manifest so partially-completed runs can be resumed without re-simulating successful buildings.
- **Measured-data validated.** Results are scored against independent measured benchmarks (NYC Local Law 84, LA EBEWE, national CBECS 2018) with all gates evaluated report-only, never tuned to pass.

---

## Pipeline: Step by Step

### Step 1: Data Acquisition

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
7. Overlap resolution: near-duplicate footprints (IoU > 0.95) resolved by keeping the larger polygon

**Tag flattening & parsing:**

- `building_tag`, `function_tag` ← OSM `building`, `amenity`, `shop`, `office` tags
- `height_m` ← parsed from string (handles metres and feet with unit conversion)
- `levels` ← `building:levels` (nullable Int64)
- `year_built` ← `start_date` (4-digit year or century notation)
- `postcode`, `underground`, `roof_shape`, `roof_height_m` ← extracted where available
- `surplus_tags` ← all remaining OSM tags captured as JSON

**Optional external sources:** `overture_fetcher.py` fetches Overture Maps building footprints/heights (offline GeoParquet slice or live DuckDB query), and `height_cache.py` caches resolved heights. Both feed the fusion tier in Step 2.3 and are **off by default**.

**Provenance & quality tracking:**

Each row carries provenance columns (`provenance_levels`, `provenance_height_m`, `provenance_year_built`, `provenance_building_tag`, `provenance_function_tag`, `provenance_postcode`, `provenance_geometry`) and a composite `data_quality_flag` (e.g., `no_floors,no_height,generic_tag`).

**Output:** `01_buildings_clean.gpkg`, a 23-column GeoDataFrame in UTM CRS, plus sidecar schema JSON and cleaning log.

---

### Step 2: Semantic Enrichment

Enrichment is split into sub-steps that progressively add columns to the GeoDataFrame: 23 → 26 → 29 → 57 columns.

#### Step 2.0: Building Classification

**Module:** `openubem/semantic/building_classifier.py`

Maps each building to one of **30 OpenStudio archetypes** using a rule-based classifier with 17 rules organized by priority:

| Priority | Rule | Example output |
|---|---|---|
| 1a–1b | Super-tall / tall (≥ 40 / ≥ 20 floors, commercial) | `SuperTallBuilding`, `TallBuilding` |
| 2a–2b | Residential tier (≥ 9 / < 9 floors) | `HighriseApartment`, `MidriseApartment` |
| 3a–3b | Lodging tier (hotel ≥ 5 / < 5 levels) | `LargeHotel`, `SmallHotel` |
| 4–11 | Function-tag direct rules | `Hospital`, `Outpatient`, `College`, `Warehouse`, etc. |
| 12a–12c | Commercial use-class + size buckets (2,322 / 9,290 m²) | `SmallOffice`, `MediumOffice`, `LargeOffice` |
| 13–14 | Use-class fallbacks (industrial, institutional) | `Warehouse`, `Courthouse` |
| 15–16 | Mixed-use dominant-tag routing | Recursive sub-evaluation |
| 17 | Unknown fallback | `OpenUBEMUnknown` |

**Key features:**
- **DOE-aligned cut-points.** The office size bins (2,322 / 9,290 m²), the school split (Primary = 1 storey, Secondary ≥ 2) and the hotel level threshold (≥ 5) are the DOE prototypes' own definitions. This correctness fix (`E-R3-3`) removed a systematic Medium→Small office misclassification crossing an HVAC template cliff.
- **Levels imputation**: when OSM `levels` is missing, the classifier infers floor count from `height_m` ÷ 3.5 m, or defaults to 1.
- **Confidence scoring**: each assignment gets `HIGH`, `MEDIUM`, or `LOW` confidence based on data quality (observed vs. imputed inputs, tag specificity).
- **Detailed office variant**: optionally promotes `SmallOffice`/`MediumOffice`/`LargeOffice` to their `*Detailed` counterparts.
- **User overrides**: CSV-based per-building override of archetype assignment.

> ⚠️ **Before/after gate (binding project rule).** No change to `building_classifier.py` that can move classification is adopted until the labelled fixture has been run on **both** sides of the change and **both** accuracy numbers are recorded. Two fixtures are gated separately: the frozen 50-row fixture at ≥ 0.70 fine top-1, and `tests/fixtures/labelled_archetypes_tagrich_v2.csv` at ≥ 0.80 (measured **88.8%** on 98 graded rows). **Every accuracy figure must name its fixture**; a bare percentage is not meaningful here.

**Output:** 26-column GeoDataFrame (23 upstream + `archetype_id`, `archetype_confidence`, `archetype_source`) saved as `02_buildings_classified.gpkg` + distribution CSV.

#### Step 2.1: Climate Zone & Weather

**Module:** `openubem/acquisition/__init__.py` (orchestrator) + `openubem/acquisition/climate_zone.py` + `openubem/acquisition/epw_manager.py`

Assigns each building its **ASHRAE climate zone** (16-token vocabulary: `1A`–`8`) via spatial join against a bundled ASHRAE climate zone GeoPackage, then resolves and downloads the closest **EPW weather file** from climate.onebuilding.org.

**EPW station resolution:**
1. Compute the neighbourhood's representative geographic point
2. Search the bundled `epw_stations.csv` catalogue (all One Building stations) for the nearest station within 300 km
3. Fetch the EPW file (user-provided directory > network download > cached)
4. Validate the downloaded file integrity

**Output:** 29-column GeoDataFrame (26 upstream + `climate_zone`, `epw_path`, `provenance_climate_zone`) saved as `02a_buildings_climate.gpkg` + `02a_climate_epw.parquet` sidecar.

#### Step 2.2: Physics Enrichment

**Module:** `openubem/semantic/__init__.py` (orchestrator) + `construction_sets.py` + `loads.py` + `schedules.py` + `imputation.py`

Appends **28 physics columns** to each building row, transforming the 29-column input into a 57-column enriched GeoDataFrame:

**Envelope properties (14 columns):**
- `vintage_standard`: ASHRAE 90.1 standard era (e.g., `DOERefPre1980`, `90.1-2019`) resolved from `year_built`
- U-values (`u_roof_w_m2k`, `u_wall_w_m2k`, `u_window_w_m2k`, `u_floor_w_m2k`), looked up from a bundled ASHRAE 90.1-2019 construction table keyed by (archetype, climate zone, vintage)
- `shgc_window`: solar heat gain coefficient
- `assembly_roof`, `assembly_wall`: assembly description strings
- `infiltration_m3_s_m2`: envelope air leakage rate
- Provenance columns for each property

**Internal loads (14 columns):**
- `lighting_w_m2`, `equipment_w_m2`: lighting and equipment power densities
- `occupant_m2_per_person`: occupant density
- `heating_setpoint_c`, `cooling_setpoint_c`: thermostat setpoints
- `heating_setback_c`, `cooling_setup_c`: setback/setup temperatures
- `wwr`: window-to-wall ratio
- Provenance columns for each property

**Load modes:**
- `deterministic` (default): exact archetype-specific lookup values
- `probabilistic`: KDE-resampled perturbation of density values for Monte Carlo analysis

**OpenUBEMUnknown handling:**
Buildings that could not be classified receive donor properties from `MediumOffice@DOERefPre1980` with probabilistic density estimation (PDE) for range coverage.

**Schedule library:**
For each unique archetype in the fleet, an 8760-hourly schedule library is built from bundled DOE prototype schedule data (occupancy, lighting, equipment, heating/cooling setpoint profiles) and serialized as `02b_schedule_library.json`.

**Output:** `02b_buildings_enriched.gpkg` (57 columns) + schema JSON + schedule library JSON.

#### Step 2.3: Input Imputation & Provenance

**Modules:** `openubem/semantic/imputation.py` (routing) + `provenance.py` + `spatial_impute.py` + `fusion.py` + `draw_methods.py` + `debias.py`

OSM is incomplete: heights, storey counts, vintages and use-classes are missing for a large share of any real fleet. Rather than filling silently, OpenUBEM routes every gap through an explicit, ordered tier stack and records **how** each value was obtained.

| Tier | What it does | Status |
|---|---|---|
| `fusion` | Joins an external observation (Overture Maps footprint/height, LiDAR nDSM, assessor parcel record). A joined field → `HIGH` confidence; a value *derived* from one (e.g. `levels` from LiDAR height) → `MED`. Never emits `LOW`. | enabled, inert until sources are configured |
| `spatial` | k = 10 nearest neighbours within 100 m: neighbour-vote for categorical, distance-weighted kNN for continuous. No trainable weights. Deactivates itself when the local neighbourhood is itself ≥ 60% missing (MNAR guard). | enabled (default) |
| `statistical` | Group median / mode over observed values. | enabled (default) |
| `ml` | MissForest / MICE / kNN / RF / HistGBM / linear supervised imputers with per-target minimum sample floors, plus a quantile-mapping de-bias corrector for newer-skew. | **opt-in only**, never in the default tier list |
| `draw` | Variance-preserving draws (KDE, PMM, hot-deck, residual, ABB, categorical-frequency), for when the *distribution*, not the point estimate, matters. | **opt-in only**, not wired into the default call graph |

**Hard rules enforced in code and tests:**
- No imputer or fusion source may read an EUI column (`_assert_no_eui_leakage`).
- No source order, join tolerance, neighbourhood size or confidence cut-point is ever swept against a simulated-EUI target.
- Every fill emits a `data_quality_flag` token of the form `{METHOD}_{SOURCE}_{TIER}` with `TIER ∈ {HIGH, MED, LOW}`; no site invents its own vocabulary.

**Validation utilities** (`openubem/validation/`): `mask_recover.py` runs a mask-and-recover harness (hide known values, impute, score recovery), and `eui_impact.py` runs the downstream check that matters: simulate the same buildings twice, on observed vs. imputed inputs, and compare annual EUI and peak load. Input-reconstruction accuracy alone is not accepted as validation.

---

### Step 3: IDF Generation

**Module:** `openubem/idf/builder.py` (orchestrator) + `surfaces.py` + `hvac.py` + `dhw.py` + `cooking.py` + `refrigeration.py` + `elevators.py` + `opaque_assembly.py` + `outputs.py`

**Supporting:** `openubem/geometry/footprint.py` + `zoning.py` + `context.py` + `layout_assigner.py` + `envelope_patcher.py`

Converts each enriched building row into a complete **EnergyPlus Input Data File (IDF)** ready for simulation:

**3A. Footprint simplification:**
Multi-step Douglas-Peucker simplification cascade (0.5 m → 1.5 m → convex hull → bounding box) to keep vertex count ≤ 120 while preserving shape fidelity.

**3B. Thermal zoning:**
Chosen by the active [resolution mode](#simulation-resolution-modes); in the default `auto` mode, three strategies apply:

| Strategy | Condition | Description |
|---|---|---|
| `single_zone` | 1-floor buildings | One thermal zone for the whole building |
| `one_zone_per_floor` | Multi-floor < 500 m² or residential/tall | One zone per floor |
| `perimeter_core` | Multi-floor ≥ 500 m² commercial | Core + perimeter zoning per floor (4.57 m depth) |

**3C. Context discovery:**
Neighbouring buildings within a 30 m radius are discovered and injected as shading surfaces, accounting for inter-building solar obstruction.

**3D. Schedule injection:**
Archetype-specific hourly schedules (occupancy, lighting, equipment, thermostat setpoints) written directly into the IDF.

**3E. 3D geometry extrusion:**
Footprint polygons extruded via geomeppy's `add_block()` to actual building height. Interzone surface integrity is validated (vertex-count mismatches fail the building at generation time, not runtime).

**3F. Construction assignment:**
- Opaque assemblies (roof, wall, floor) built by `opaque_assembly.py`: a massless R-value layer by default, or a real multilayer construction when thermal mass is requested (`Thickness = R × k`, the inversion fixed at both former defect sites)
- Glazing via `WindowMaterial:SimpleGlazingSystem` with archetype-specific U-factor and SHGC
- Window-to-wall ratio applied via `set_wwr()`
- Per-zone infiltration via `ZoneInfiltration:DesignFlowRate`

**3G. Internal loads:**
`People`, `Lights`, `ElectricEquipment`, and thermostat objects created for every thermal zone.

**3H. HVAC (10 system families):**
`hvac.py` dispatches a real system per archetype × size × floor count, following ASHRAE 90.1-2019 Appendix G assignments, emitted as `HVACTemplate:*` objects and expanded with `ExpandObjects`:

| Family | Typical archetypes |
|---|---|
| Built-up VAV w/ chilled water & hot water reheat | LargeOffice, TallBuilding, Hospital-class |
| Packaged VAV w/ hot water reheat | SecondarySchool, Courthouse, Outpatient |
| Packaged VAV w/ electric reheat | MediumOffice-class |
| PSZ-AC w/ gas furnace | Small/medium nonresidential, retail |
| PSZ-HP w/ gas backup | Mild-climate small nonresidential |
| Four-pipe fan coil units | LargeHotel |
| Water-loop heat pump | HighriseApartment |
| PTAC w/ electric reheat | SmallHotel |
| Data-centre CRAC / CRAH | DataCenter variants |
| Heated-only radiant / unit heaters | Warehouse |

A single-zone guard prevents a degenerate one-zone building from being handed a multi-zone VAV system it cannot physically represent. Because the HVAC is real equipment rather than an ideal-loads abstraction, heating and cooling energy come from EnergyPlus **meters** at real equipment efficiency.

**3I. Service loads (physically modelled):**

| Load | EnergyPlus objects | Applies to |
|---|---|---|
| Domestic hot water | `WaterHeater:Mixed` + `WaterUse:Equipment` | all archetypes with a DOE DHW intensity |
| Commercial cooking | `ZoneVentilation:DesignFlowRate` kitchen exhaust + `OtherEquipment` process load | food-service archetypes (FSR, QSR, schools, LargeHotel, Hospital) |
| Refrigeration | `Refrigeration:Case` (5-case layout) + `Refrigeration:CompressorRack` | SuperMarket |
| Elevators | `ElectricEquipment` lift motor, DOE `ElevatorLift` transcribed verbatim with its own schedule and heat-gain split | archetypes with a DOE elevator object |

Every intensity is area-scaled from the DOE prototype's own footprint, with no fitted multipliers.

**3J. Output variables:**
Hourly reporting of zone-level energy, operative temperature, and occupant count, plus the end-use meters Step 5 parses. `trim_outputs=True` drops per-zone hourly variables for large-fleet runs.

**Template routing:**
Four base IDF templates selected by archetype family:
- `residential_base.idf`: apartments
- `highrise_base.idf`: tall/super-tall buildings
- `specialized_base.idf`: laboratories, data centres, warehouses
- `commercial_base.idf`: everything else (default)

**Parallelisation:** Optional joblib/loky process pool for multi-core IDF generation.

**Output:** `03_idf_manifest.parquet` (one row per building with generation status and `resolution_mode`) + `idfs/*.idf` files.

---

### Step 4: EnergyPlus Simulation

**Module:** `openubem/simulation/runner.py` (single-building runner) + `openubem/simulation/parallel.py` (fleet orchestrator)

Runs EnergyPlus 23.1 on the entire building fleet in parallel:

**4A. Task construction:**
Each simulable building (generation status = `success`) becomes a `SimTask(osm_id, idf_path, epw_path, work_dir)`.

**4B. Resume detection:**
Before running, each work directory is checked for successful completion (presence of `eplusout.end` + `eplusout.sql` with success marker). Completed buildings are skipped; stale crash debris is cleaned up.

**4C. Version handshake:**
Before any dispatch, `energyplus --version` is called to verify the installed version matches the expected `23.1`.

**4D. Parallel dispatch:**
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

**4E. File purging:**
After successful simulation, non-essential files are purged from each work directory. Retained files: `eplusout.sql`, `eplusout.csv`, `eplusout.mtr`, `eplusout.err`, `eplusout.end`, `eplusout.eio`, `eplustbl.htm`, `openubem_run.log`. (`eplusout.eio` is retained because Step 5 reads the *simulated* floor area from it; see 5C.)

**4F. Manifest:**
All results (fresh, cached, skipped) are assembled into `04_simulation_manifest.parquet` with `osm_id`, `idf_path`, `work_dir`, `sql_path`, `status`, `n_warnings`, `n_severe`, `wall_clock_s`, `ep_version`, `epw_path`, `error_summary`. `results/err_parse.py` extracts the leading fatal/severe cause from `eplusout.err` so failures are reported by reason, not just by count.

**Output:** `04_simulation_manifest.parquet` + per-building work directories containing EnergyPlus output files.

---

### Step 5: Results, Carbon & Validation

**Module:** `openubem/results/__init__.py` (orchestrator) + `parser.py` + `carbon.py` + `aggregator.py` + `service_loads.py` + `err_parse.py` + `visualization.py` + `plotting_suite.py`

Parses simulation outputs, computes energy metrics, converts to emissions, and validates against benchmarks:

**5A. SQL/CSV parsing (`parser.py`):**
- Primary: extract hourly reporting data and end-use meters from `eplusout.sql` via SQLite queries
- Fallback: parse `eplusout.csv` (ReadVarsESO output) if SQL is unavailable
- Energy unit conversion: J → kWh at the parse boundary

**5B. Zone integrity check:**
- Regex-based zone name resolution against the expected building's `osm_id`
- I2 invariant: foreign `osm_id` in a work directory aborts the entire run
- Zone count verification against the IDF manifest

**5C. EUI computation:**
Ten metered end-uses (kWh/m²/yr), all from EnergyPlus meters:

| Metric | EnergyPlus source |
|---|---|
| `heating_eui_kwh_m2` | `Heating:Electricity` + `Heating:NaturalGas` (all-fuel site energy) |
| `cooling_eui_kwh_m2` | `Cooling:Electricity` |
| `lighting_eui_kwh_m2` | Zone Lights Electricity Energy |
| `equipment_eui_kwh_m2` | Zone Electric Equipment Electricity Energy, less the elevator sub-meter |
| `fans_eui_kwh_m2` | `Fans:Electricity` |
| `pumps_eui_kwh_m2` | `Pumps:Electricity` |
| `dhw_eui_kwh_m2` | `WaterSystems:Electricity` + `WaterSystems:NaturalGas` (also broken out as `dhw_elec_*` / `dhw_gas_*`) |
| `cooking_eui_kwh_m2` | `InteriorEquipment:NaturalGas` (gas cooking; electric cooking stays in equipment) |
| `refrigeration_eui_kwh_m2` | `Refrigeration:Electricity` (compressor rack) |
| `elevators_eui_kwh_m2` | `Elevators:InteriorEquipment:Electricity`, de-folded out of equipment |
| `total_eui_kwh_m2` | **sum of all ten**, whole-building site energy |

**Floor-area denominator.** The denominator is the **multiplier-aware simulated floor area** read from `eplusout.eio` (`Σ zone floor area × zone multiplier × zone-list multiplier`), falling back to the nominal `footprint_area_m2 × num_floors` when the `.eio` is absent, with the choice recorded as provenance. This closed a defect where any building using `Zone.Multiplier` had its EUI divided by an area EnergyPlus never simulated.

**5D. Indoor Overheating Degree (IOD):**
Adaptive thermal comfort metric computed over summer months (June–September):
- Comfort threshold: Tₙ + 2.5 °C where Tₙ = 0.31 × T̄ₘₒₙₜₕₗᵧ + 17.8
- Occupant-count-weighted mean across all zones
- Flags `IOD_NO_OCCUPIED_HOURS` when no occupied summer hours exist

**5E. Carbon emissions (`carbon.py`):**
A GWP column per end-use plus a total (kg CO₂e/m²) under the **`load_referenced_v1`** convention:
- **Gas fractions** (heating, DHW gas, cooking) × 0.181 kg CO₂e/kWh
- **Electric fractions** × state-specific eGRID 2022 electricity emission factor
- `gwp_heating`, `gwp_cooling`, `gwp_lighting`, `gwp_equipment`, `gwp_fans`, `gwp_pumps`, `gwp_dhw`, `gwp_cooking`, `gwp_refrigeration`, `gwp_elevators`, `gwp_total`

**5F. Spatial join & aggregation (`aggregator.py`):**
Step-5 metric columns are LEFT-joined onto the enriched GeoDataFrame, and a neighbourhood summary is written: fleet mean EUI, total emissions, total floor area, simulation success rate, IOD mean/p95.

**5G. Validation gates (`__init__.py`):**
CBECS 2018 (Commercial Buildings Energy Consumption Survey) validation when a reference dataset is provided:

| Gate | Metric | Threshold |
|---|---|---|
| CV(RMSE) | Quantile-matched RMSE vs. weighted CBECS distribution | < 30% |
| NMBE | Normalised Mean Bias Error | < 10% |
| R² | Archetype-level Pearson correlation with PBA-matched CBECS means | > 0.6 |
| KS D | Kolmogorov–Smirnov statistic vs. weighted CBECS CDF | < 0.10 |

Exclusions: residential apartments, data centres excluded from all gates; `OpenUBEMUnknown` excluded from R² only.

> **NMBE is never quoted alone.** It is blind to variance collapse: a model that predicts every building at the fleet mean scores a perfect NMBE. Read it beside R² and the distribution-shape gates.

**5H. Visualisation:**
`visualization.py` and `plotting_suite.py` produce spatial EUI maps with basemap tiles, ordered archetype charts, and validation comparison plots; `impute_figures.py` / `impute_scatter.py` / `impute_montage.py` / `draw_leaderboard.py` cover the imputation-method reporting. All figure outputs go to `openubem/outputs/` (flat).

**5I. Service-loads reconstruction (legacy, default OFF):**
`service_loads.py` implements the pre-Phase-E approach: divide the modelled total by a CBECS-2018 modelled-energy fraction (region-aware) to reconstruct a measured-comparable total. It is **retired** (`config.RECONSTRUCT_SERVICE_LOADS` defaults to `False`) because those loads are now physically simulated (3I). The code is retained so historical runs can be re-scored on their original basis.

**Output:** `05_results.gpkg` + `05_results.csv` + `05_summary.json` + `figures/` + optional `<run_id>_viewer.html`.

---

### Step 6: Outdoor Microclimate & Thermal Comfort (optional)

**Module:** `openubem/microclimate/` · **Runner:** `scripts/run_step6_microclimate.py`

Steps 1–5 answer *"how much energy do these buildings use?"* Step 6 answers *"what does it feel like to stand outside among them?"* It is invoked **explicitly**, never as part of a standard run, reads Steps 1–5 read-only, and writes only `06_mc_*` artifacts.

Given a run's buildings, resolved EPW, and optionally real EnergyPlus exterior surface temperatures, it computes at pedestrian height (1.1 m) over a chosen analysis window:

| Layer | What it is |
|---|---|
| **Radiative geometry** | Sky view factor (32-azimuth horizon sampling) + per-hour building and vegetation shadow rasters; the dominant cost of a run |
| **Surface temperatures** | Ground and facade temperature; empirical tier by default, optional tier reads real E+ exterior surface temperatures back out of Step 4 |
| **Four driver fields** | Air temperature, humidity, wind speed (EPW 10 m downscaled to pedestrian height), and mean radiant temperature from a 6-directional radiant flux balance on a standing person |
| **UTCI** | The COST-730 Bröde 210-term operational polynomial, transcribed from the canonical Fortran source and matched to the reference table at 1e-6, on the official 10-class cold/heat stress scale |
| **Exposure metrics** | CTSI (cumulative thermal stress, °C·h above threshold) and PHEH (person-hours above 46 °C), aggregated per parcel |
| **Mitigation scenarios** | Tree canopy, PV canopy, cool pavement, cool roof, high-albedo facade; each is a *domain-layer* edit (albedo, canopy), never a physics change |

Outputs are per-hour **GeoTIFF** rasters, figures, and a per-building GeoPackage that joins outdoor heat exposure onto each building's own energy results, letting you ask which buildings sit in the worst outdoor heat, and what their energy use is.

**Honest limits.** Step 6 results are **not validated against any measurement**: there is no outdoor comfort measurement campaign for any of the twelve cells, and every gate is internal-consistency or behavioural. That is exactly why its numbers are kept out of `05_results.*` rather than sitting beside validated numbers with borrowed authority. The optional `macdonald` wind tier is safe (zero physically-impossible values across 113 M checked cell-hours) but falls back to the default `cost730` tier for ~32% of cell-hours on a real mid/high-rise domain. Buildings with no known height cannot cast shade, so cells with heavy `height_m` gaps compute as an open field rather than an urban canyon.

```bash
py -3 scripts/run_step6_microclimate.py --run-dir <completed_run_dir>
py -3 scripts/run_step6_microclimate.py --run-dir <dir> --wind-tier macdonald --vegetation-tier osm
```

---

## Simulation Resolution Modes

Zoning fidelity is user-selectable per study via `run_step3(..., resolution_mode=...)`: coarse for early-design screening, finer for detailed work.

| Mode | What it does | Zones/building | Status |
|---|---|---|---|
| **`auto`** *(default)* | Adaptive: picks `single_zone` / `one_zone_per_floor` / `perimeter_core` per building | mixed | ✅ validated, **the reported baseline** |
| **`building`** | Whole building = 1 zone | 1 | ✅ validated (screening) |
| **`floor`** | Each floor = 1 zone | `num_floors` | ✅ validated (screening) |
| **`fast_zone`** | Generic core + perimeter on every floor, every archetype | ~5 × `num_floors` | ✅ validated |
| **`layout_assign`** | Substitutes a validated DOE/ASHRAE 90.1 baseline prototype IDF for the archetype and scales it to the real building (√S geometry, S loads), with storey matching via `Zone.Multiplier` and climate/vintage envelope patching | Real DOE-prototype zone count (1–256) | ⚠️ adopted for zone/HVAC-topology studies, **not certified for fleet-level EUI reporting** |
| **`zone`** | Room-level polygon layout generation (`layoutGenerator.py`) | many | ⏸ parked, not a validated baseline |

**Mode-to-mode differences are physics, not error.** Internal loads conserve across modes (the same building accounts for the same total floor area at any resolution), but coarser zoning under-predicts annual heating by ~10–26% and shifts peak/solar behaviour. Those differences wash out to < ~2.3% once results are aggregated to district scale. Use `building`/`floor` for stock totals and screening; they are **not** appropriate for peak-demand or equipment-sizing studies.

**Why `layout_assign` is not used for fleet EUI.** It takes an excellent suit off the rack and alters it: the prototype's interior is far better than any generated layout, but it isn't the real building's shape. Its storey-matching mechanism only reaches prototypes with 1 or 3 native storeys, and only when the real building is taller, so for most of the fleet the simulated floor area and the nominal floor area disagree, giving a correct number for the wrong building. Internal loads also stay at 2022-code densities regardless of the building's real vintage (the envelope *is* patched to the real vintage; the loads are not).

---

## Interactive 3D Viewer

**Module:** `openubem/viz/`: `viewer_export.py` (Step-5 post-processor), `cityjson_emitter.py`, `geometry_extract.py`, `attribute_binding.py`, `basemap_raster.py`, `context_features.py`, `utci_layer.py`, `shell/` (vendored JS/CSS engine)

After a run's `05_results.*` exist, OpenUBEM can export the neighbourhood as **one self-contained HTML file** you open by double-clicking: no server, no install, no network. Each building is extruded to its real massing and coloured by simulated EUI; select one to drill into its individual surfaces and windows.

**Two constraints it never breaks:**

1. **Faithful to the model.** It renders exactly what the pipeline produced: real IDF geometry and real `05_results` values. Where a fact is absent it shows **"not recorded"**, never a made-up default. A building's zone breakdown opens **only** where the pipeline made real zone geometry; synthetic zones are prohibited.
2. **Self-contained and reproducible.** Engine, styles, scene data and the street-map basemap are all inlined (the basemap is baked once at export time, not streamed), so the file opens from `file://` with zero network requests, and re-exporting the same run state gives a byte-identical file.

It also carries **per-building provenance** (resolution-mode border, trust badge, failure hatch, and the raw `data_quality_flag` tokens) and honest data-gap styling (e.g. footprints with no OSM height are badged *"Height: not in OSM"* rather than rendered as broken buildings). UTCI from Step 6 can be switched on as an optional layer; off by default, and a run without it rebuilds byte-identically.

Pre-built viewers for all 12 validation cells live in `openubem/outputs/3D/`.

---

## Project Layout

```
openubem/                          # Core pipeline source code
├── config.py                      # Global constants and path configuration
├── acquisition/                   # Step 1 & 2.1
│   ├── osm_fetcher.py             #   Step 1: OSM ingest, clean, schema-validate
│   ├── overture_fetcher.py        #   Overture Maps buildings (offline slice or live DuckDB)
│   ├── height_cache.py            #   Resolved-height cache
│   ├── climate_zone.py            #   ASHRAE climate zone spatial join
│   └── epw_manager.py             #   EPW station resolution and download
├── semantic/                      # Step 2.0, 2.2 & 2.3
│   ├── building_classifier.py     #   Step 2.0: 30-archetype rule classifier
│   ├── construction_sets.py       #   Envelope U-value lookups
│   ├── loads.py                   #   Internal load density lookups
│   ├── schedules.py               #   8760-hourly schedule builder
│   ├── imputation.py              #   Tiered imputation routing + ML imputers
│   ├── provenance.py              #   Canonical provenance/flag-token contract
│   ├── spatial_impute.py          #   Neighbour-vote / kNN fill + MNAR guard
│   ├── fusion.py                  #   External-source precedence layer
│   ├── draw_methods.py            #   Variance-preserving draw tier (opt-in)
│   └── debias.py                  #   Newer-skew quantile-mapping corrector
├── geometry/                      # Shared geometry utilities
│   ├── footprint.py               #   Footprint simplification, num_floors
│   ├── zoning.py                  #   Thermal zoning strategy + resolution modes
│   ├── context.py                 #   Context building discovery (shading)
│   ├── layout_assigner.py         #   DOE baseline-IDF substitution + storey matching
│   ├── layoutGenerator.py         #   Room-level layout generation (parked)
│   └── envelope_patcher.py        #   Patch a baseline IDF to real vintage/climate zone
├── idf/                           # Step 3
│   ├── builder.py                 #   Per-building IDF orchestrator + run_step3
│   ├── surfaces.py                #   3D extrusion, interzone matching, adiabatic
│   ├── opaque_assembly.py         #   Massless / multilayer opaque constructions
│   ├── hvac.py                    #   10-family HVAC dispatcher
│   ├── dhw.py                     #   WaterHeater:Mixed + WaterUse:Equipment
│   ├── cooking.py                 #   Kitchen exhaust + process load
│   ├── refrigeration.py           #   Refrigeration cases + compressor rack
│   ├── elevators.py               #   DOE ElevatorLift as ElectricEquipment
│   ├── outputs.py                 #   EnergyPlus output variable/meter injection
│   └── templates/                 #   Base IDF templates (4 variants)
├── simulation/                    # Step 4
│   ├── runner.py                  #   Single-building subprocess + classify
│   └── parallel.py                #   Fleet fan-out, resume, manifest
├── results/                       # Step 5
│   ├── __init__.py                #   Results orchestrator + CBECS validation
│   ├── parser.py                  #   SQL/CSV extraction + 10 end-use EUIs + IOD
│   ├── carbon.py                  #   Per-end-use GWP via eGRID factors
│   ├── aggregator.py              #   Spatial join + neighbourhood summary
│   ├── err_parse.py               #   eplusout.err fatal/severe cause extraction
│   ├── service_loads.py           #   Legacy reconstruction (default OFF)
│   ├── visualization.py           #   Basic map/chart rendering
│   ├── plotting_suite.py          #   Advanced multi-figure plotting
│   └── impute_*.py, draw_leaderboard.py   # Imputation reporting figures/tables
├── microclimate/                  # Step 6 (UTCI): svf, shadow, solar, wind, mrt,
│                                  #   psychro, utci, exposure, scenarios, figures, resim
├── viz/                           # Interactive 3D viewer + CityJSON emitter + shell/
├── validation/                    # mask_recover.py, eui_impact.py
├── data/                          # Bundled reference data (see Data Assets)
└── outputs/                       # Generated figures, comparisons, 3D viewers

scripts/                           # Runners, builders, analyses
├── run_r3_fleet.py                #   Full-chain fleet run (Steps 2–5)
├── run_r3_step5.py                #   Step 5 standalone re-run
├── run_r3_gates_report.py         #   CBECS validation gate report
├── run_r3_gen_only.py             #   Step 3 IDF generation only
├── run_step6_microclimate.py      #   Step 6 runner
├── render_plots.py                #   Standalone plot rendering
├── build_*.py                     #   Rebuild bundled reference data from source
├── cluster/                       #   SLURM submit/harvest utilities + runbook
├── validation/                    #   Cell pipelines, rescores, gate reports
├── analysis/                      #   One-off measurement / comparison scripts
└── diagnostics/                   #   Debugging tools

tests/                             # Pytest suite (95 test modules)
├── conftest.py
├── fixtures/                      #   Golden data + labelled classifier fixtures
└── test_*.py                      #   Per-module unit + integration tests

docs/                              # Specifications, plans, validation records
├── docs_main/                     #   Cross-cutting OVERVIEW / DESIGN / flowcharts (read-only)
├── docs_stepN/                    #   Per-step specs (read-only)
├── docs_EXPLANATION/              #   Plain-language explainers (start here)
├── docs_REPORTS/                  #   Final arc reports
├── docs_VALIDATION/               #   Frozen per-cell validation results
├── docs_ACTIVE/                   #   Live work: open-items register, plans
├── docs_DONE/                     #   Closed arc records
├── docs_TODO/                     #   Parked tracks
└── PROJECT_CHECKLIST.md           #   Master progress tracker
```

---

## Data Assets

All bundled reference data lives under `openubem/data/`:

| Asset | File | Description |
|---|---|---|
| OSM tag map | `osm_to_use_class.json` | Maps ~100 OSM building/amenity/shop/office tags to 5 use-classes |
| Archetype vocabulary | `openstudio_archetypes.json` | 30 DOE/OpenStudio archetype definitions (29 + `OpenUBEMUnknown`) |
| CBECS PBA map | `cbecs_pba_map.json` | Archetype → CBECS 2018 Principal Building Activity codes |
| EPW catalogue | `epw_stations.csv` | ~2,800 global weather stations with coordinates and download URLs |
| Climate zones | `climate_zones/*.gpkg` | ASHRAE Standard 169 climate zone polygons |
| Envelope tables | `construction/ashrae_90_1_2019.json` | U-values, SHGC, infiltration keyed by (archetype, climate zone, vintage) |
| Internal loads | `loads/doe_prototype_loads.json`, `openstudio_loads.json`, `doe_space_type_loads.json` | Lighting, equipment, occupant densities and setpoints, per archetype and per space type |
| HVAC systems | `loads/hvac_systems_by_archetype.json` | System family, plant, and sizing per archetype (10 families) |
| HVAC COP | `loads/hvac_cop_by_archetype.json` | Rated cooling COP + heating-coil type/efficiency (30/30 archetypes) |
| DHW | `loads/dhw_by_archetype.json` | Water-heater fuel, capacity, and use intensity |
| Cooking | `loads/cooking_by_archetype.json` | Kitchen exhaust flow + process load for food-service archetypes |
| Refrigeration | `refrigeration/` | Case and compressor-rack parameters (SuperMarket 5-case layout) |
| Elevators | `loads/elevators_by_archetype.json` | DOE `ElevatorLift` design level, schedule, and heat-gain split |
| Schedules | `schedules/doe_schedules.json` | 8760-hourly fractional schedules per archetype |
| Carbon factors | `carbon/egrid_2022.json` | EPA eGRID 2022 electricity emission factors by U.S. state |
| Service loads | `service_loads/enduse_fractions_table4.json`, `enduse_fractions_regional.json` | CBECS 2018 end-use splits, national and per-census-division (legacy reconstruction) |
| Fusion fixtures | `fixtures/fusion/` | Committed Overture slice, LiDAR nDSM, and assessor test cell (offline tests) |

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
| `DP_TOLERANCE_M` / `DP_COARSE_TOLERANCE_M` | `0.5` / `1.5` | Douglas-Peucker simplification tolerances |
| `MAX_VERTICES` | `120` | Maximum exterior polygon vertices |
| `SHADING_SPHERE_RADIUS` | `30.0` | Context building discovery radius (metres) |
| `BASELINE_IDF_DIR` | *(local path)* | DOE baseline IDF library for `layout_assign` mode |
| `EPW_CACHE_DIR` | `~/.openubem/epw` | Local EPW file cache |
| `EPW_MAX_STATION_KM` | `300.0` | Maximum distance to nearest EPW station |
| `LOAD_MODE` | `deterministic` | Load assignment mode (`deterministic` / `probabilistic`) |
| `RANDOM_SEED` | `42` | Global RNG seed |
| `SIM_TIMEOUT_S` | `3600` | Per-building simulation timeout (seconds) |
| `SIM_RETAIN_FILES` | *(set)* | Files kept after a successful run (includes `eplusout.eio`) |
| `N_JOBS` | `-1` (all cores) | Parallel worker count (`SLURM_CPUS_PER_TASK` override) |
| `GWP_CONVENTION` | `load_referenced_v1` | Carbon accounting convention |
| `IOD_SUMMER_MONTHS` | `(6, 9)` | Summer months for IOD computation |
| `EUI_PLAUSIBILITY_BOUNDS` | `(25, 1000)` | Plausible EUI range (kWh/m²/yr) |
| `RECONSTRUCT_SERVICE_LOADS` | `False` | Legacy CBECS reconstruction overlay (retired by Phase-E) |
| `IMPUTE_ENABLED_TIERS` | `("fusion", "spatial", "statistical")` | Active imputation tiers (`ml` / `draw` are opt-in only) |
| `IMPUTE_STRICT_MODE` | `False` | Raise instead of imputing when a value is missing |
| `IMPUTE_ML_METHOD_BY_TARGET` / `IMPUTE_ML_FLOORS` | *(dicts)* | Per-target ML method and minimum-sample floors |
| `FUSION_SOURCES_BY_TARGET` | `{}` | External-source precedence per attribute (empty = fusion is a no-op) |
| `FUSION_OVERTURE_*` / `FUSION_LIDAR_NDSM_PATH` / `FUSION_ASSESSOR_*` | `None` | Fusion source locations |
| `HEIGHT_CACHE_DIR` | `~/.openubem/heights` | Resolved-height cache |
| `UTCI_GRID_RES_M` | `2.0` | Step-6 raster resolution (metres) |
| `UTCI_PEDESTRIAN_HEIGHT_M` | `1.1` | Analysis height (human centre of gravity) |
| `UTCI_SVF_AZIMUTHS` | `32` | Horizon-sampling azimuths for sky view factor |
| `UTCI_DOMAIN_BUFFER_M` | `200.0` | Shading-context radius for the radiation domain |
| `UTCI_ANALYSIS_WINDOW` | `hottest_week` | Step-6 analysis window |
| `UTCI_WIND_TIER` / `UTCI_VEGETATION_TIER` / `UTCI_WALL_TEMP_TIER` | `cost730` / `none` / `empirical` | Step-6 model tiers |

**Environment variable overrides:** `ENERGYPLUS_PATH`, `OPENUBEM_ENERGYPLUS_IDD_PATH`, `OPENUBEM_EPW_CACHE`, `OPENUBEM_BASELINE_IDF_DIR`, `OPENUBEM_HEIGHT_CACHE`, `OPENUBEM_RECONSTRUCT_SERVICE_LOADS`, `OPENUBEM_FUSION_*`, `OPENUBEM_UTCI_*`, `SLURM_CPUS_PER_TASK`.

---

## Run Scripts

| Script | Description |
|---|---|
| `run_r3_fleet.py` | **Full pipeline** (Steps 2–5) for a test neighbourhood |
| `run_r3_step5.py` | Re-run Step 5 only (results aggregation) from existing simulation outputs |
| `run_r3_gates_report.py` | Compute CBECS validation gates and generate report |
| `run_r3_gen_only.py` | Run Step 3 (IDF generation) only |
| `run_step6_microclimate.py` | Run Step 6 (UTCI / outdoor microclimate) against a completed run |
| `render_plots.py` | Standalone figure rendering from existing results |
| `validation/v12_cell_pipeline.py` | Per-cell validation pipeline (the 12-cell matrix driver) |
| `validation/phaseE_rescore.py` | Re-score a completed fleet against measured benchmarks |

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

## Running on an HPC Cluster

City-scale fleets (thousands of buildings) are run on SLURM. `scripts/cluster/` holds the submit and harvest utilities, and `scripts/cluster/README.md` is the full runbook.

The pattern is **generate locally, simulate remotely, harvest back**:

1. Generate IDFs locally (`run_r3_gen_only.py`) and stage them with the EPW into a tarball.
2. `scp` to the cluster and submit as a **job array**, one building per array task, 1 CPU each (EnergyPlus is single-threaded per building).
3. Harvest with `t*_harvest_results.py`, which rebuilds a Step-4 manifest from the returned work directories so Step 5 runs unchanged locally.

Two rules that are non-negotiable on the Concordia *Speed* cluster and generalise well:

- **Never run compute on the login node.** Always `sbatch --array`, fire-and-forget, then read the output file. The login node is for `mkdir`, `scp`, `tar`, `squeue`, `sacct`.
- **The remote login shell is tcsh.** Bash syntax sent over a bare `ssh` fails silently, so wrap remote commands in `bash -lc` (the `_ssh()` helper in the harvest scripts does this).

---

## Test Suite

95 test modules covering all pipeline stages, the imputation framework, the microclimate stage, and the viewer.

```bash
pytest -q tests/                          # the suite baseline; always scope to tests/
pytest -m "not slow"                      # skip integration tests
pytest -m "not energyplus"                # skip tests requiring the EnergyPlus binary
pytest tests/test_building_classifier.py  # single module
```

> ⚠️ **Always pass `tests/`.** A bare root-level `pytest` also collects archived copies of old test trees under `docs/` and reports a large number of false failures.

Test markers:
- `slow`: integration tests that hit the network or take significant time
- `energyplus`: tests requiring EnergyPlus 23.1 installed

Latest full run of the scoped suite: **0 failed · 1,859 passed · 55 skipped · 0 errors**. Every skip names the open item it waits on. A skip is tracked as a debt, not counted as a pass.

Golden fixtures (GeoPackage files, EnergyPlus SQL, labelled classifier exams) are stored in `tests/fixtures/`.

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
| `rasterio` | Raster I/O (Step 6 GeoTIFFs, LiDAR nDSM fusion) |
| `scipy` | Statistical functions (KDE, KS test) |
| `scikit-learn` | ML imputation tier (opt-in) |
| `joblib` | Parallel processing |
| `matplotlib` | Plotting |
| `contextily ≥ 1.3` | Basemap tiles for spatial plots and the 3D viewer |
| `requests` | HTTP downloads (EPW files) |
| `packaging` | Version string comparison |

**Dev extras:** `pytest`, `pytest-mock`, `tenacity`, `openpyxl`, `pythermalcomfort` (Step-6 comfort cross-checks). `duckdb` is needed only for the live Overture fusion path, which is never exercised by the test suite.

**Installation:**

```bash
git clone https://github.com/orcunkoraliseri/OpenUBEM.git
cd OpenUBEM

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

# Step 3: Generate EnergyPlus IDF files (resolution_mode="auto" is the validated default)
manifest = run_step3(gdf, schedules, output / "step3", n_jobs=6, resolution_mode="auto")

# Step 4: Run EnergyPlus simulations in parallel
sim_manifest = run_neighbourhood(manifest, gdf, output / "sim", n_jobs=6)

# Step 5: Parse results, compute EUI and carbon, validate
results = aggregate_results(sim_manifest, manifest, gdf, output / "results", state="MA")
```

Optional post-processing:

```python
# Interactive 3D viewer (self-contained HTML)
from openubem.viz.viewer_export import export_viewer_from_run
export_viewer_from_run(
    run_id="my_neighbourhood",
    results_dir=output / "results",
    manifest_path=output / "step3" / "03_idf_manifest.parquet",
)
```

```bash
# Step 6: outdoor microclimate / UTCI
py -3 scripts/run_step6_microclimate.py --run-dir my_neighbourhood/results
```

---

## Status & Validation

OpenUBEM has been validated at neighbourhood scale across **three U.S. cities** against independent measured-energy benchmarks. All gates are evaluated report-only and never tuned to pass.

**Validation matrix: 12 cells, 8,160 buildings.** Four density cells (centre / urban / suburban / rural) in each of **New York City, Los Angeles, and Austin**, simulated end-to-end. **8,154 of 8,160 buildings succeeded (99.93%)**; the six failures are geometry defects in `la_rural` / `la_urban`, documented rather than dropped silently.

**Adopted baseline, "Phase-E full realism":** DOE-aligned archetype thresholds (E-R3-3) + 10 archetype-specific HVAC system families + physically modelled DHW, cooking, refrigeration and elevators. The former CBECS reconstruction overlay is **retired**. **Zero fitted parameters.**

| Metric | Result |
|---|---|
| Fleet EUI | **157.1 kWh/m²**, *pooled*: total simulated energy ÷ total simulated floor area over all 8,154 successful buildings |
| City-Overall vs. measured | NYC **−31.3%** · LA **−3.6%** · Austin **−30.5%** (LL84 / EBEWE / CBECS proxy) |
| Archetype-level R² | NYC **0.877** · LA **0.902** · Austin **0.723** |
| National CBECS 2018 | scored across all three census regions (mid-Atlantic, Pacific, West-South-Central) |
| EnergyPlus success | 8,154 / 8,160 |

**How to read the under-prediction.** The earlier Phase-D2 baseline reported city-overall accuracy within ±9%, but part of that agreement came from a post-hoc reconstruction overlay that silently carried a residual "Other" category (process loads, miscellaneous plug loads). Phase-E removed the overlay and replaced it with physics, which makes the remaining gap visible instead of absorbed. Closing it would require fitting office plug loads to CBECS, which breaks the zero-fitted-parameters rule, and is therefore recorded as an accepted residual, not silently corrected. The distribution shape (R²) is strong; the mean level is biased low, and both numbers are published together.

**Known limitations, stated plainly:**

- **The published fleet figure is not yet end-to-end reproducible from `HEAD`.** The adopted run was produced by a working tree whose elevator wiring was never committed. The wiring has since been restored and regenerates the elevator column exactly, but a separate window-geometry re-randomisation defect (mechanism fixed 2026-08-17) means the confirming third fleet re-run has not been done. `157.1 kWh/m²` is correct and complete for the run that produced it; the provenance caveat stays live until that re-run lands.
- **`layout_assign` is not certified for fleet EUI reporting**: see [Simulation Resolution Modes](#simulation-resolution-modes).
- **Step 6 (UTCI) is not validated against measurement** and is deliberately excluded from `05_results.*`.
- **Distribution-shape gates** (CV(RMSE), KS) are structural for an archetype-deterministic UBEM, reported for transparency rather than used as pass/fail.

Earlier single-city milestone: a 483-building Boston neighbourhood reached 100% simulation success with CBECS gates passing.

> Detailed validation methodology, per-cell results, and the full record live under `docs/docs_VALIDATION/`, `docs/docs_REPORTS/`, and `docs/PROJECT_CHECKLIST.md`.

---

## Documentation Map

| You want… | Read |
|---|---|
| Plain-language orientation | `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` |
| What the inputs are and where they come from | `docs/docs_EXPLANATION/OpenUBEM_inputs_reference.md` |
| The imputation methods in detail | `docs/docs_EXPLANATION/OpenUBEM_imputation_methods.md` |
| Outdoor analysis (Step 6) reference | `docs/docs_EXPLANATION/OpenUBEM_outdoor_analysis_reference.md` |
| Results by topic (classification, HVAC/service loads, resolution) | `docs/docs_EXPLANATION/Results/` |
| The Phase-E final validation report | `docs/docs_REPORTS/REPORT_phaseE_final.md` |
| The binding design specs | `docs/docs_main/` (cross-cutting) + `docs/docs_stepN/` (per step) |
| Current project status and open items | `docs/PROJECT_CHECKLIST.md` and `docs/docs_ACTIVE/openings/` |
| Cluster runbook | `scripts/cluster/README.md` |

---

## License

*To be specified.*
