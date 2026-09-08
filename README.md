# OpenUBEM

**Open-source Urban Building Energy Modeling platform.**

Give OpenUBEM a neighbourhood (address, coordinate, bounding box, or OSM XML export) and it estimates the **annual energy use** and **carbon emissions** of every building in it. Each building is mapped to an archetype, simulated as its own full-year whole-building EnergyPlus model, and the results are aggregated to neighbourhood metrics. Built for urban planners, energy researchers and policy makers who need building-level estimates at neighbourhood or district scale without per-building audits or metered data.

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
13. [European Locations](#european-locations)
14. [Status & Validation](#status--validation)
15. [Documentation Map](#documentation-map)
16. [License](#license)

---

## Architecture Overview

A **5-stage pipeline**. Each stage writes versioned artifacts (GeoPackage, Parquet, JSON) that the next consumes, and any stage can be re-run alone:

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

**Step 6 is deliberately outside the spine.** It answers a different question (*what does it feel like to stand outside in this neighbourhood?*), has its own runner, reads Steps 1–5 read-only, and never writes into `05_results.*`. See [Step 6](#step-6-outdoor-microclimate--thermal-comfort-optional).

**Design principles:**

- **Archetype-based.** A rule-based classifier maps each building to one of 30 DOE/OpenStudio archetypes (MidriseApartment, LargeOffice, Hospital, …).
- **Per-building simulation.** Every building gets its own IDF with true footprint geometry (no shoe-box proxy), extruded to real height, with neighbourhood context shading.
- **Physically modelled, not reconstructed.** HVAC is dispatched per archetype across **10 real system families** (central VAV with chiller + boiler, PSZ rooftops, PVAV with reheat, fan-coil units, water-loop heat pumps, PTAC/PTHP, CRAC/CRAH, radiant/unit heaters); DHW, cooking, refrigeration and elevators are real EnergyPlus objects. All reported energy comes from EnergyPlus **meters**, directly comparable to metered utility data, never a post-hoc multiplier.
- **Zero fitted parameters.** No threshold, fraction or coefficient is tuned against a simulated or measured EUI target; every value traces to a cited source (ASHRAE 90.1, DOE prototypes, CBECS, eGRID, IBC).
- **Provenance everywhere.** Every input carries a provenance column and a `data_quality_flag` token: observed, imputed, fused from an external source, or standard default.
- **Deterministic & reproducible.** Seeded RNG for all stochastic operations; versioned artifact schemas.
- **Resume-capable.** Step 4 writes a manifest, so partial runs resume without re-simulating successes.
- **Measured-data validated.** Scored against NYC Local Law 84, LA EBEWE and national CBECS 2018; every gate is report-only, never tuned to pass.

---

## Pipeline: Step by Step

### Step 1: Data Acquisition

**Module:** `openubem/acquisition/osm_fetcher.py`

Downloads footprints and attributes from OpenStreetMap via [OSMnx](https://github.com/gboeing/osmnx). Four input modes:

| Mode | Parameter | Description |
|---|---|---|
| Address | `location="Boston, MA"` | Geocoded address + radius |
| Point | `location=(42.36, -71.06)` | Lat/lon coordinate + radius |
| Bbox | `bbox=(N, S, E, W)` | Bounding box |
| XML | `osm_path="file.osm"` | Pre-downloaded OSM XML |

**7-step clean:** (1) drop null/empty geometry; (2) keep Polygon/MultiPolygon only; (3) explode MultiPolygons into Polygons with re-keyed `osm_id`; (4) `buffer(0)` repair + validity filter; (5) compute `footprint_area_m2` and `perimeter_m`; (6) drop area < 20 m²; (7) resolve near-duplicates (IoU > 0.95) by keeping the larger polygon.

**Tag parsing:** `building_tag`, `function_tag` ← OSM `building`/`amenity`/`shop`/`office`; `height_m` ← string parse (metres or feet, unit-converted); `levels` ← `building:levels` (nullable Int64); `year_built` ← `start_date` (4-digit year or century notation); `postcode`, `underground`, `roof_shape`, `roof_height_m` where present; all remaining tags → `surplus_tags` JSON.

**Optional external sources (off by default):** `overture_fetcher.py` (Overture Maps footprints/heights from an offline GeoParquet slice or live DuckDB query) and `height_cache.py` (resolved-height cache). Both feed the Step 2.3 fusion tier.

**Provenance:** per-row `provenance_levels`, `provenance_height_m`, `provenance_year_built`, `provenance_building_tag`, `provenance_function_tag`, `provenance_postcode`, `provenance_geometry`, plus a composite `data_quality_flag` (e.g. `no_floors,no_height,generic_tag`).

**Output:** `01_buildings_clean.gpkg`, 23 columns in UTM CRS, plus sidecar schema JSON and cleaning log.

---

### Step 2: Semantic Enrichment

Sub-steps add columns progressively: 23 → 26 → 29 → 57.

#### Step 2.0: Building Classification

**Module:** `openubem/semantic/building_classifier.py`

Rule-based classifier, 17 rules by priority, mapping to **30 OpenStudio archetypes**:

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

- **DOE-aligned cut-points.** The office bins (2,322 / 9,290 m²), school split (Primary = 1 storey, Secondary ≥ 2) and hotel threshold (≥ 5 levels) are the DOE prototypes' own definitions. Fix `E-R3-3` removed a systematic Medium→Small office misclassification that crossed an HVAC template cliff.
- **Levels imputation:** missing OSM `levels` → `height_m` ÷ 3.5 m, else 1.
- **Confidence:** `HIGH` / `MEDIUM` / `LOW` per assignment, from data quality (observed vs imputed inputs, tag specificity).
- **Detailed office variant:** optional promotion of `SmallOffice`/`MediumOffice`/`LargeOffice` to `*Detailed`.
- **User overrides:** CSV per-building archetype override.

> ⚠️ **Before/after gate (binding project rule).** No classification-moving change to `building_classifier.py` is adopted until the labelled fixture has run on **both** sides and **both** accuracies are recorded. Two fixtures, gated separately: the frozen 50-row fixture at ≥ 0.70 fine top-1, and `tests/fixtures/labelled_archetypes_tagrich_v2.csv` at ≥ 0.80 (measured **88.8%** on 98 graded rows). **Every accuracy figure names its fixture**; a bare percentage is meaningless here.

**Output:** 26 columns (23 + `archetype_id`, `archetype_confidence`, `archetype_source`) → `02_buildings_classified.gpkg` + distribution CSV.

#### Step 2.1: Climate Zone & Weather

**Module:** `openubem/acquisition/__init__.py` (orchestrator) + `openubem/acquisition/climate_zone.py` + `openubem/acquisition/epw_manager.py`

Assigns the **ASHRAE climate zone** (16-token vocabulary, `1A`–`8`) by spatial join against a bundled ASHRAE GeoPackage, then resolves and downloads the closest **EPW** from climate.onebuilding.org: (1) compute the neighbourhood's representative point; (2) find the nearest station in bundled `epw_stations.csv` (all One Building stations) within 300 km; (3) fetch, preferring user-provided directory > network download > cache; (4) validate file integrity.

**Output:** 29 columns (26 + `climate_zone`, `epw_path`, `provenance_climate_zone`) → `02a_buildings_climate.gpkg` + `02a_climate_epw.parquet` sidecar.

#### Step 2.2: Physics Enrichment

**Module:** `openubem/semantic/__init__.py` (orchestrator) + `construction_sets.py` + `loads.py` + `schedules.py` + `imputation.py`

Appends **28 physics columns** (29 → 57), each property with its own provenance column:

- **Envelope (14 columns):** `vintage_standard` (ASHRAE 90.1 era from `year_built`, e.g. `DOERefPre1980`, `90.1-2019`); `u_roof_w_m2k`, `u_wall_w_m2k`, `u_window_w_m2k`, `u_floor_w_m2k` from a bundled ASHRAE 90.1-2019 construction table keyed by (archetype, climate zone, vintage); `shgc_window`; `assembly_roof`, `assembly_wall` description strings; `infiltration_m3_s_m2` air leakage.
- **Internal loads (14 columns):** `lighting_w_m2`, `equipment_w_m2` power densities; `occupant_m2_per_person`; `heating_setpoint_c`, `cooling_setpoint_c`; `heating_setback_c`, `cooling_setup_c`; `wwr` window-to-wall ratio.
- **Load modes:** `deterministic` (default, exact archetype lookup) or `probabilistic` (KDE-resampled density perturbation for Monte Carlo).
- **OpenUBEMUnknown:** unclassified buildings get donor properties from `MediumOffice@DOERefPre1980` with probabilistic density estimation (PDE) for range coverage.
- **Schedule library:** for each archetype in the fleet, 8760-hourly occupancy / lighting / equipment / heating-cooling setpoint profiles from bundled DOE prototype data → `02b_schedule_library.json`.

**Output:** `02b_buildings_enriched.gpkg` (57 columns) + schema JSON + schedule library JSON.

#### Step 2.3: Input Imputation & Provenance

**Modules:** `openubem/semantic/imputation.py` (routing) + `provenance.py` + `spatial_impute.py` + `fusion.py` + `draw_methods.py` + `debias.py`

OSM lacks heights, storey counts, vintages and use-classes for a large share of any real fleet. Instead of silent fills, every gap goes through an explicit, ordered tier stack that records **how** each value was obtained:

| Tier | What it does | Status |
|---|---|---|
| `fusion` | Joins an external observation (Overture Maps footprint/height, LiDAR nDSM, assessor parcel record). A joined field → `HIGH` confidence; a value *derived* from one (e.g. `levels` from LiDAR height) → `MED`. Never emits `LOW`. | enabled, inert until sources are configured |
| `spatial` | k = 10 nearest neighbours within 100 m: neighbour-vote for categorical, distance-weighted kNN for continuous. No trainable weights. Deactivates itself when the local neighbourhood is itself ≥ 60% missing (MNAR guard). | enabled (default) |
| `statistical` | Group median / mode over observed values. | enabled (default) |
| `ml` | MissForest / MICE / kNN / RF / HistGBM / linear supervised imputers with per-target minimum sample floors, plus a quantile-mapping de-bias corrector for newer-skew. | **opt-in only**, never in the default tier list |
| `draw` | Variance-preserving draws (KDE, PMM, hot-deck, residual, ABB, categorical-frequency), for when the *distribution*, not the point estimate, matters. | **opt-in only**, not wired into the default call graph |

**Hard rules (enforced in code and tests):** no imputer or fusion source may read an EUI column (`_assert_no_eui_leakage`); no source order, join tolerance, neighbourhood size or confidence cut-point is ever swept against a simulated-EUI target; every fill emits a `data_quality_flag` token `{METHOD}_{SOURCE}_{TIER}` with `TIER ∈ {HIGH, MED, LOW}`, and no site invents its own vocabulary.

**Validation** (`openubem/validation/`): `mask_recover.py` hides known values, imputes, and scores recovery; `eui_impact.py` runs the check that matters: simulate the same buildings on observed vs imputed inputs and compare annual EUI and peak load. Input-reconstruction accuracy alone is not accepted as validation.

---

### Step 3: IDF Generation

**Module:** `openubem/idf/builder.py` (orchestrator) + `surfaces.py` + `hvac.py` + `dhw.py` + `cooking.py` + `refrigeration.py` + `elevators.py` + `opaque_assembly.py` + `outputs.py`
**Supporting:** `openubem/geometry/footprint.py` + `zoning.py` + `context.py` + `layout_assigner.py` + `envelope_patcher.py`

Each enriched row becomes a complete **EnergyPlus Input Data File (IDF)**:

**3A. Footprint simplification:** Douglas-Peucker cascade (0.5 m → 1.5 m → convex hull → bounding box) keeps ≤ 120 vertices while preserving shape.

**3B. Thermal zoning:** chosen by the active [resolution mode](#simulation-resolution-modes); in default `auto`:

| Strategy | Condition | Description |
|---|---|---|
| `single_zone` | 1-floor buildings | One thermal zone for the whole building |
| `one_zone_per_floor` | Multi-floor < 500 m² or residential/tall | One zone per floor |
| `perimeter_core` | Multi-floor ≥ 500 m² commercial | Core + perimeter zoning per floor (4.57 m depth) |

**3C. Context:** neighbours within 30 m are injected as shading surfaces (inter-building solar obstruction).

**3D. Schedules:** archetype hourly occupancy, lighting, equipment and setpoint schedules written into the IDF.

**3E. Extrusion:** footprints extruded via geomeppy `add_block()` to real height. Interzone vertex-count mismatches fail the building at generation time, not runtime.

**3F. Constructions:** opaque assemblies (roof, wall, floor) via `opaque_assembly.py`, a massless R-value layer by default or a real multilayer construction when thermal mass is requested (`Thickness = R × k`, the inversion fixed at both former defect sites); glazing via `WindowMaterial:SimpleGlazingSystem` with archetype U-factor and SHGC; WWR via `set_wwr()`; per-zone `ZoneInfiltration:DesignFlowRate`.

**3G. Internal loads:** `People`, `Lights`, `ElectricEquipment` and thermostat objects per zone.

**3H. HVAC (10 families):** `hvac.py` dispatches a real system per archetype × size × floor count per ASHRAE 90.1-2019 Appendix G, emitted as `HVACTemplate:*` and expanded with `ExpandObjects`:

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

A single-zone guard stops a degenerate one-zone building from receiving a multi-zone VAV it cannot represent. Because the HVAC is real equipment rather than ideal loads, heating and cooling energy come from EnergyPlus **meters** at real equipment efficiency.

**3I. Service loads (physically modelled):**

| Load | EnergyPlus objects | Applies to |
|---|---|---|
| Domestic hot water | `WaterHeater:Mixed` + `WaterUse:Equipment` | all archetypes with a DOE DHW intensity |
| Commercial cooking | `ZoneVentilation:DesignFlowRate` kitchen exhaust + `OtherEquipment` process load | food-service archetypes (FSR, QSR, schools, LargeHotel, Hospital) |
| Refrigeration | `Refrigeration:Case` (5-case layout) + `Refrigeration:CompressorRack` | SuperMarket |
| Elevators | `ElectricEquipment` lift motor, DOE `ElevatorLift` transcribed verbatim with its own schedule and heat-gain split | archetypes with a DOE elevator object |

Every intensity is area-scaled from the DOE prototype's own footprint, with no fitted multipliers.

**3J. Outputs:** hourly zone-level energy, operative temperature and occupant count, plus the end-use meters Step 5 parses. `trim_outputs=True` drops per-zone hourly variables for large fleets.

**Templates** by archetype family: `residential_base.idf` (apartments), `highrise_base.idf` (tall/super-tall), `specialized_base.idf` (laboratories, data centres, warehouses), `commercial_base.idf` (everything else, default).

**Parallelisation:** optional joblib/loky process pool for multi-core generation.

**Output:** `03_idf_manifest.parquet` (one row per building with generation status and `resolution_mode`) + `idfs/*.idf`.

---

### Step 4: EnergyPlus Simulation

**Module:** `openubem/simulation/runner.py` (single-building runner) + `openubem/simulation/parallel.py` (fleet orchestrator)

Runs EnergyPlus 23.1 on the whole fleet in parallel:

**4A. Tasks:** each building with generation status `success` → `SimTask(osm_id, idf_path, epw_path, work_dir)`.

**4B. Resume:** a work directory holding `eplusout.end` (success marker) + `eplusout.sql` is skipped; stale crash debris is cleaned.

**4C. Version handshake:** `energyplus --version` must report `23.1` before any dispatch.

**4D. Dispatch:** `joblib.Parallel` with configurable worker count. Each worker runs `energyplus -w <epw> -d <workdir> -x -r <idf>` (`-x` = ExpandObjects, required for HVACTemplate; `-r` = ReadVarsESO, producing the `eplusout.csv` fallback for Step 5), enforces the per-building timeout (default 3600 s), and classifies the outcome:

| Status | Condition |
|---|---|
| `success` | `eplusout.end` contains success marker + `eplusout.sql` exists |
| `success_cached` | Resume hit (previously completed successfully) |
| `failed_timeout` | Subprocess killed at timeout |
| `failed_crash` | No `eplusout.end` file produced |
| `failed_fatal` | `eplusout.end` contains fatal error marker |
| `not_attempted_invalid_idf` | IDF generation failed in Step 3 |

**4E. Purge:** after success, only `eplusout.sql`, `eplusout.csv`, `eplusout.mtr`, `eplusout.err`, `eplusout.end`, `eplusout.eio`, `eplustbl.htm`, `openubem_run.log` are kept (`.eio` because Step 5 reads the *simulated* floor area from it, see 5C).

**4F. Manifest:** fresh, cached and skipped results → `04_simulation_manifest.parquet` with `osm_id`, `idf_path`, `work_dir`, `sql_path`, `status`, `n_warnings`, `n_severe`, `wall_clock_s`, `ep_version`, `epw_path`, `error_summary`. `results/err_parse.py` extracts the leading fatal/severe cause from `eplusout.err`, so failures are reported by reason, not just count.

**Output:** the manifest + per-building work directories of EnergyPlus output files.

---

### Step 5: Results, Carbon & Validation

**Module:** `openubem/results/__init__.py` (orchestrator) + `parser.py` + `carbon.py` + `aggregator.py` + `service_loads.py` + `err_parse.py` + `visualization.py` + `plotting_suite.py`

**5A. Parsing (`parser.py`):** hourly data and end-use meters from `eplusout.sql` via SQLite, falling back to `eplusout.csv` (ReadVarsESO) if SQL is unavailable; J → kWh at the parse boundary.

**5B. Zone integrity:** regex zone-name resolution against the building's `osm_id`; a foreign `osm_id` in a work directory aborts the entire run (I2 invariant); zone count checked against the IDF manifest.

**5C. EUI:** ten metered end-uses (kWh/m²/yr), all from EnergyPlus meters:

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

**Floor-area denominator:** the **multiplier-aware simulated floor area** read from `eplusout.eio` (Σ zone floor area × zone multiplier × zone-list multiplier), falling back to nominal `footprint_area_m2 × num_floors` when `.eio` is absent, with the choice recorded as provenance. This closed a defect where any `Zone.Multiplier` building had its EUI divided by an area EnergyPlus never simulated.

**5D. Indoor Overheating Degree (IOD):** adaptive comfort metric over June–September. Threshold Tₙ + 2.5 °C with Tₙ = 0.31 × T̄ₘₒₙₜₕₗᵧ + 17.8; occupant-count-weighted mean across zones; flags `IOD_NO_OCCUPIED_HOURS` when no occupied summer hours exist.

**5E. Carbon (`carbon.py`):** one GWP column per end-use plus a total (kg CO₂e/m²) under the **`load_referenced_v1`** convention: gas fractions (heating, DHW gas, cooking) × 0.181 kg CO₂e/kWh; electric fractions × state-specific eGRID 2022 factor. Columns: `gwp_heating`, `gwp_cooling`, `gwp_lighting`, `gwp_equipment`, `gwp_fans`, `gwp_pumps`, `gwp_dhw`, `gwp_cooking`, `gwp_refrigeration`, `gwp_elevators`, `gwp_total`.

**5F. Aggregation (`aggregator.py`):** metric columns LEFT-joined onto the enriched GeoDataFrame; neighbourhood summary = fleet mean EUI, total emissions, total floor area, simulation success rate, IOD mean/p95.

**5G. Validation gates (`__init__.py`):** CBECS 2018 (Commercial Buildings Energy Consumption Survey), when a reference dataset is provided:

| Gate | Metric | Threshold |
|---|---|---|
| CV(RMSE) | Quantile-matched RMSE vs. weighted CBECS distribution | < 30% |
| NMBE | Normalised Mean Bias Error | < 10% |
| R² | Archetype-level Pearson correlation with PBA-matched CBECS means | > 0.6 |
| KS D | Kolmogorov–Smirnov statistic vs. weighted CBECS CDF | < 0.10 |

Exclusions: residential apartments and data centres from all gates; `OpenUBEMUnknown` from R² only.

> **NMBE is never quoted alone.** It is blind to variance collapse: predicting every building at the fleet mean scores a perfect NMBE. Read it beside R² and the distribution-shape gates.

**5H. Visualisation:** `visualization.py` and `plotting_suite.py` produce spatial EUI maps with basemap tiles, ordered archetype charts and validation plots; `impute_figures.py` / `impute_scatter.py` / `impute_montage.py` / `draw_leaderboard.py` cover imputation-method reporting. All figures → `openubem/outputs/` (flat).

**5I. Service-loads reconstruction (legacy, default OFF):** `service_loads.py` is the pre-Phase-E approach: divide the modelled total by a region-aware CBECS-2018 modelled-energy fraction to reconstruct a measured-comparable total. **Retired** (`config.RECONSTRUCT_SERVICE_LOADS` defaults to `False`) because those loads are now physically simulated (3I); kept so historical runs can be re-scored on their original basis.

**Output:** `05_results.gpkg` + `05_results.csv` + `05_summary.json` + `figures/` + optional `<run_id>_viewer.html`.

---

### Step 6: Outdoor Microclimate & Thermal Comfort (optional)

**Module:** `openubem/microclimate/` · **Runner:** `scripts/run_step6_microclimate.py`

Steps 1–5 answer *"how much energy do these buildings use?"*; Step 6 answers *"what does it feel like to stand outside among them?"* It is invoked **explicitly**, never in a standard run, reads Steps 1–5 read-only, and writes only `06_mc_*` artifacts.

From a run's buildings, resolved EPW, and optionally real EnergyPlus exterior surface temperatures, it computes at pedestrian height (1.1 m) over a chosen analysis window:

| Layer | What it is |
|---|---|
| **Radiative geometry** | Sky view factor (32-azimuth horizon sampling) + per-hour building and vegetation shadow rasters; the dominant cost of a run |
| **Surface temperatures** | Ground and facade temperature; empirical tier by default, optional tier reads real E+ exterior surface temperatures back out of Step 4 |
| **Four driver fields** | Air temperature, humidity, wind speed (EPW 10 m downscaled to pedestrian height), and mean radiant temperature from a 6-directional radiant flux balance on a standing person |
| **UTCI** | The COST-730 Bröde 210-term operational polynomial, transcribed from the canonical Fortran source and matched to the reference table at 1e-6, on the official 10-class cold/heat stress scale |
| **Exposure metrics** | CTSI (cumulative thermal stress, °C·h above threshold) and PHEH (person-hours above 46 °C), aggregated per parcel |
| **Mitigation scenarios** | Tree canopy, PV canopy, cool pavement, cool roof, high-albedo facade; each is a *domain-layer* edit (albedo, canopy), never a physics change |

Outputs: per-hour **GeoTIFF** rasters, figures, and a per-building GeoPackage joining outdoor heat exposure onto each building's own energy results, so you can ask which buildings sit in the worst outdoor heat and what their energy use is.

**Honest limits.** Step 6 is **not validated against any measurement**: no outdoor comfort campaign exists for any of the twelve cells, and every gate is internal-consistency or behavioural. That is exactly why its numbers stay out of `05_results.*` rather than sitting beside validated numbers with borrowed authority. The optional `macdonald` wind tier is safe (zero physically-impossible values across 113 M checked cell-hours) but falls back to the default `cost730` tier for ~32% of cell-hours on a real mid/high-rise domain. Buildings with no known height cast no shade, so cells with heavy `height_m` gaps compute as an open field rather than an urban canyon.

```bash
py -3 scripts/run_step6_microclimate.py --run-dir <completed_run_dir>
py -3 scripts/run_step6_microclimate.py --run-dir <dir> --wind-tier macdonald --vegetation-tier osm
```

---

## Simulation Resolution Modes

Zoning fidelity is selectable per study via `run_step3(..., resolution_mode=...)`: coarse for early-design screening, finer for detailed work.

| Mode | What it does | Zones/building | Status |
|---|---|---|---|
| **`auto`** *(default)* | Adaptive: picks `single_zone` / `one_zone_per_floor` / `perimeter_core` per building | mixed | ✅ validated, **the reported baseline** |
| **`building`** | Whole building = 1 zone | 1 | ✅ validated (screening) |
| **`floor`** | Each floor = 1 zone | `num_floors` | ✅ validated (screening) |
| **`fast_zone`** | Generic core + perimeter on every floor, every archetype | ~5 × `num_floors` | ✅ validated |
| **`layout_assign`** | Substitutes a validated DOE/ASHRAE 90.1 baseline prototype IDF for the archetype and scales it to the real building (√S geometry, S loads), with storey matching via `Zone.Multiplier` and climate/vintage envelope patching | Real DOE-prototype zone count (1–256) | ⚠️ adopted for zone/HVAC-topology studies, **not certified for fleet-level EUI reporting** |
| **`zone`** | Room-level polygon layout generation (`layoutGenerator.py`) | many | ⏸ parked, not a validated baseline |

**Mode-to-mode differences are physics, not error.** Internal loads conserve across modes (the same building accounts for the same total floor area at any resolution), but coarser zoning under-predicts annual heating by ~10–26% and shifts peak/solar behaviour. Those differences wash out to < ~2.3% at district scale. Use `building`/`floor` for stock totals and screening; they are **not** appropriate for peak-demand or equipment-sizing studies.

**Why `layout_assign` is not used for fleet EUI.** It takes an excellent suit off the rack and alters it: the prototype's interior beats any generated layout, but it is not the real building's shape. Storey matching reaches only prototypes with 1 or 3 native storeys, and only when the real building is taller, so for most of the fleet the simulated and nominal floor areas disagree, giving a correct number for the wrong building. Internal loads also stay at 2022-code densities regardless of real vintage (the envelope *is* patched to the real vintage; the loads are not).

---

## Interactive 3D Viewer

**Module:** `openubem/viz/`: `viewer_export.py` (Step-5 post-processor), `cityjson_emitter.py`, `geometry_extract.py`, `attribute_binding.py`, `basemap_raster.py`, `context_features.py`, `utci_layer.py`, `shell/` (vendored JS/CSS engine)

Once a run's `05_results.*` exist, the neighbourhood exports as **one self-contained HTML file** opened by double-click: no server, no install, no network. Each building is extruded to its real massing and coloured by simulated EUI; select one to drill into its surfaces and windows.

**Two constraints it never breaks:**

1. **Faithful to the model.** It renders exactly what the pipeline produced: real IDF geometry and real `05_results` values. Absent facts show **"not recorded"**, never a made-up default. A zone breakdown opens **only** where the pipeline made real zone geometry; synthetic zones are prohibited.
2. **Self-contained and reproducible.** Engine, styles, scene data and the street-map basemap are all inlined (the basemap is baked once at export time, not streamed), so the file opens from `file://` with zero network requests, and re-exporting the same run state gives a byte-identical file.

It also carries **per-building provenance** (resolution-mode border, trust badge, failure hatch, raw `data_quality_flag` tokens) and honest data-gap styling (footprints with no OSM height are badged *"Height: not in OSM"*, not rendered as broken buildings). Step 6 UTCI can be switched on as an optional layer; off by default, and a run without it rebuilds byte-identically.

Pre-built viewers for all 12 U.S. validation cells and the four European districts: `openubem/outputs/3D/`.

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

City-scale fleets (thousands of buildings) run on SLURM. `scripts/cluster/` holds the submit and harvest utilities; `scripts/cluster/README.md` is the full runbook.

Pattern: **generate locally, simulate remotely, harvest back**:

1. Generate IDFs locally (`run_r3_gen_only.py`) and stage them with the EPW into a tarball.
2. `scp` to the cluster and submit as a **job array**, one building per array task, 1 CPU each (EnergyPlus is single-threaded per building).
3. Harvest with `t*_harvest_results.py`, which rebuilds a Step-4 manifest from the returned work directories so Step 5 runs unchanged locally.

Rules that are non-negotiable on the Concordia *Speed* cluster and generalise well:

- **Never run compute on the login node.** Always `sbatch --array`, fire-and-forget, then read the output file. The login node is for `mkdir`, `scp`, `tar`, `squeue`, `sacct`.
- **The remote login shell is tcsh.** Bash syntax over a bare `ssh` fails silently, so wrap remote commands in `bash -lc` (the `_ssh()` helper in the harvest scripts does this).
- **Multiple simulations always run in parallel, never one after another, and Speed comes first** because it is faster. Speed takes up to 32 concurrent CPUs (array width 32); a local machine takes up to 20 concurrent EnergyPlus processes; add local capacity when the case count justifies it.

---

## Test Suite

150 test modules cover all pipeline stages, the imputation framework, the European locations arc (51 modules), the microclimate stage and the viewer.

```bash
pytest -q -n 8 tests/                     # the suite baseline; always scope to tests/ (pytest-xdist, ~7 min)
pytest -m "not slow"                      # skip integration tests
pytest -m "not energyplus"                # skip tests requiring the EnergyPlus binary
pytest tests/test_building_classifier.py  # single module
```

> ⚠️ **Always pass `tests/`.** A bare root-level `pytest` also collects archived copies of old test trees under `docs/` and reports many false failures.

Markers: `slow` (integration tests that hit the network or take significant time); `energyplus` (requires EnergyPlus 23.1 installed).

Latest full run of the scoped suite: **0 failed · 2,345 passed · 55 skipped · 0 errors** (2026-08-28). Every skip names the open item it waits on; a skip is tracked as a debt, not counted as a pass — **cite the enumerated 55-skip list, never the bare count**, since a count alone cannot identify the one skip that flipped to a pass.

Golden fixtures (GeoPackage files, EnergyPlus SQL, labelled classifier exams) live in `tests/fixtures/`.

---

## Requirements & Installation

**System requirements:** Python ≥ 3.10; EnergyPlus 23.1 installed at `C:\EnergyPlusV23-1-0` (or set `ENERGYPLUS_PATH`).

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

**Dev extras:** `pytest`, `pytest-mock`, `tenacity`, `openpyxl`, `pythermalcomfort` (Step-6 comfort cross-checks). `duckdb` is needed only for the live Overture fusion path, never exercised by the test suite.

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

## European Locations

The pipeline runs outside North America. Four European residential districts are modelled end to end, with country-specific archetypes and a dwelling-level zoning path that does not exist in the U.S. cells.

| District | Country | Buildings | Status |
|---|---|---|---|
| `FR-LYO-HAUTCOEURPENTES` — Lyon, Haut-Cœur / Pentes | France | 509 | ✅ published |
| `GB-LDN-STDUNSTANS` — London, St Dunstan's | United Kingdom | 706 | ✅ published |
| `ES-MAD-BERRUGUETE` — Madrid, Berruguete | Spain | 1,175 | ✅ published |
| `IT-BOL-GALVANI2` — Bologna, Galvani 2 | Italy | 1,211 | ⏳ simulating |

**What is different from the U.S. path:**

- **Archetypes come from TABULA / EPISCOPE**, per country and construction period, instead of the DOE/ASHRAE reference set.
- **Weather is `TMYx.2009-2023`** for every fold — the only window covering all fieldwork periods — with the station chosen by scoring candidates against TABULA's own monthly temperatures, not by nearest-distance.
- **Buildings are divided into dwellings, not floors.** A ruled grid regularizes the footprint, allocates up to 12 dwellings per floor, and branches on morphology (L-shape, U/T-shape, multi-wing) with a habitability retry. Where the ruled grid refuses — the reason is recorded per building (`L_SHAPE_DECOMPOSITION_FAILED`, `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_12`, `REGULARIZATION_AREA_DELTA_GT_2PCT`) — the building falls back to one undivided zone per storey and is badged as such in the viewer. Refusals are shown, never hidden.

**Published numbers** (pooled: total simulated energy ÷ total simulated floor area):

| District | Pooled EUI | Population |
|---|---|---|
| Lyon | **69.595307 kWh/m²** | 505 of 509 buildings |
| London | **120.064327 kWh/m²** | 706 of 706 buildings |
| Madrid | **80.694006 kWh/m²** | 1,166 of 1,175 buildings |

Every quoted figure names its population. A building whose EUI was carried from a different IDF than the one finally simulated is never published as a result: it is marked `pending_resimulation` with blank result columns until it is re-simulated.

**Definition of done, per district.** A district is not published until five measured checks pass, reported pass/fail rather than summarised:

1. The merged summary carries a pooled EUI *and* the population it was pooled over.
2. The manifest row count equals the district building count, and its non-null EUI count equals the summary's.
3. The viewer draws floor plans from the same IDF vintage the EUI came from — a fresh number on a superseded plan is a defect, not a cosmetic issue.
4. The viewer's EUI join matches the manifest exactly, and the `docs_ACTIVE` mirror is byte-identical.
5. Every superseded figure still in the docs carries an explicit supersession marker.

Evidence trees: `openubem/outputs/eu_evidence/` (per campaign, per district). Working state and findings: `docs/docs_ACTIVE/europeanLocations/`.

---

## Status & Validation

Validated at neighbourhood scale across **three U.S. cities** against independent measured-energy benchmarks. All gates are report-only, never tuned to pass.

**Validation matrix: 12 cells, 8,160 buildings.** Four density cells (centre / urban / suburban / rural) in each of **New York City, Los Angeles, and Austin**, simulated end-to-end. **8,154 of 8,160 buildings succeeded (99.93%)**; the six failures are geometry defects in `la_rural` / `la_urban`, documented rather than dropped silently.

**Adopted baseline, "Phase-E full realism":** DOE-aligned archetype thresholds (E-R3-3) + 10 archetype-specific HVAC system families + physically modelled DHW, cooking, refrigeration and elevators. The former CBECS reconstruction overlay is **retired**. **Zero fitted parameters.**

| Metric | Result |
|---|---|
| Fleet EUI | **153.8231 kWh/m²**, *pooled*: total simulated energy ÷ total simulated floor area over 8,153 buildings (restated 2026-08-19; **157.1 and 158.0 are superseded and must not be quoted**) |
| City-Overall vs. measured | NYC **−31.3%** · LA **−3.6%** · Austin **−30.5%** (LL84 / EBEWE / CBECS proxy) |
| Archetype-level R² | NYC **0.877** · LA **0.902** · Austin **0.723** |
| National CBECS 2018 | scored across all three census regions (mid-Atlantic, Pacific, West-South-Central) |
| EnergyPlus success | 8,154 / 8,160 |

**How to read the under-prediction.** The earlier Phase-D2 baseline reported city-overall accuracy within ±9%, but part of that agreement came from a post-hoc reconstruction overlay that silently carried a residual "Other" category (process loads, miscellaneous plug loads). Phase-E replaced the overlay with physics, which makes the remaining gap visible instead of absorbed. Closing it would mean fitting office plug loads to CBECS, which breaks the zero-fitted-parameters rule, so it is recorded as an accepted residual, not silently corrected. The distribution shape (R²) is strong; the mean level is biased low; both numbers are published together.

**Known limitations, stated plainly:**

- **The published fleet figure is not yet end-to-end reproducible from `HEAD`.** The adopted run came from a working tree whose elevator wiring was never committed. The wiring has since been restored and regenerates the elevator column exactly, but a separate window-geometry re-randomisation defect (mechanism fixed 2026-08-17) means the confirming third fleet re-run has not been done. `153.8231 kWh/m²` is correct and complete for the run that produced it; the provenance caveat stays live until that re-run lands.
- **The fleet figure is not volume-correct.** 91.64% of zones carry a 10 m³ volume stub; the effect is about **+1.0 kWh/m²**, which is *not* in the published number. `154.8` was measured but is **not adopted**.
- **District heating is absent from the total.** Measured at **19.47 kWh/m² (12.7%)** over an 8,144-building census, 70% of it concentrated on 116 `SuperTall`/`Tall` buildings — an archetype effect, never a flat offset. The code fix exists; the restatement was ruled **not adopted** (2026-08-22) because it lands on a different population and carbon does not follow it. Never difference the restated value against `153.8231`.
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
