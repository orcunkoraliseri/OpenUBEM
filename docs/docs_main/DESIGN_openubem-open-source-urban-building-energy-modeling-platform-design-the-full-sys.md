# DESIGN — OpenUBEM: Open-Source Urban Building Energy Modeling Platform

> **Slug:** `openubem-open-source-urban-building-energy-modeling-platform-design-the-full-sys` &nbsp;•&nbsp; **First created:** `2026-05-02` &nbsp;•&nbsp; **Latest revision:** `2026-05-02` &nbsp;•&nbsp; **Status:** APPROVED (Pass 1)
>
> Sections 1–11 are **append-once, edit-never** after first APPROVED verdict. All later changes are recorded under **Section 12 — Revision Log**.

---

## 1. Motivation & Context

Cities account for over two-thirds of global energy use and more than 70% of greenhouse gas emissions, with buildings consuming approximately 40% of that energy [reports/Open Source Urban Building Energy Modeling - General.md]. Urban Building Energy Modeling (UBEM) is the principal computational paradigm for evaluating heating, cooling, electricity, and carbon flows at neighbourhood, district, and city scale, and is the analytical foundation for retrofit programs, district heating/cooling, photovoltaic siting, and climate-policy formulation [reports/Open Source Urban Building Energy Modeling - General.md; reports/Open Source Urban Building Energy Modeling-Architecture.md].

Despite this, **every dominant UBEM tool today imposes a structural barrier on a researcher trying to script an end-to-end run** [inputs/aim/OpenUBEM_Aim_Document.md §1]:

- **CityEnergyAnalyst (CEA, ETH Zurich)** — comprehensive but operates as a standalone toolbox originally tied to ArcGIS V10.4, with proprietary shapefile/DBF formats and a custom RC engine; it cannot be invoked from a Jupyter notebook without re-engineering, and its Archetypes DB is European-context-only [papers/city-energy-analyst-cea-future-cities-laboratory-eth-zurich.md; reports/Open Source Urban Building Energy Modeling - General.md].
- **UBEM.io / UMI (MIT Sustainable Design Lab)** — UMI runs as a Rhinoceros 3D plug-in (Rhino is paid, GUI-only, Windows-centric); UBEM.io is a web abstraction over the same engine, hiding intermediate IDFs from the user [reports/Open Source Urban Building Energy Modeling - General.md].
- **URBANopt (NREL)** — Ruby-centric SDK; powerful for grid-interactive analyses via OpenDSS and REopt, but requires the OpenStudio CLI/HPXML toolchain rather than a pure-Python pip install [reports/Open Source Urban Building Energy Modeling - General.md].
- **TEASER (RWTH Aachen)** — Python, but exports Modelica (.mo) files requiring Dymola or OpenModelica, and is geared at European CityGML/TABULA inputs, not OSM [reports/Open Source Urban Building Energy Modeling-Architecture.md].
- **CityBES (LBNL)** — closed web platform for benchmarking; cannot be embedded in a custom workflow [reports/Open Source Urban Building Energy Modeling - General.md].
- **SimStadt, CitySim, OpenIDEAS** — strictly CityGML / Modelica-centric, GUI-driven, and not pip-installable [reports/Open Source Urban Building Energy Modeling - General.md].

**OpenUBEM fills a specific gap**: a fully open-source, pip-installable, scriptable Python library that takes a city name, bounding box, or coordinate pair and runs the entire pipeline — OSM ingest → ASHRAE/IECC archetype assignment → eppy/geomeppy IDF generation → parallel EnergyPlus simulation → spatial GeoDataFrame export — with **no proprietary dependencies, no GUI, and no hidden intermediate state** [inputs/aim/OpenUBEM_Aim_Document.md §2; §7].

The target audience is researchers, urban planners, and sustainability consultants in the Concordia / NSERC / Calcul Québec ecosystem. The methodological foundation is the probabilistic UBEM methodology of **Iseri, Duran, Canlı, Meral Akgul, Kalkan, & Gursel Dino (2025), Energy & Buildings 337, 115620** [inputs/aim/OpenUBEM_Aim_Document.md §4], generalised from a single Bahçelievler case study to American cities, then extended to Canada (NECB), Europe (TABULA), and climate-morphed futures in later phases. Phase 1 deliberately targets the United States first because the **DOE Prototype Buildings (16 commercial types × ASHRAE climate zones 1A–8 × 5 vintage tiers ≈ 5,168 baseline IDFs)** plus IECC residential prototypes plus ASHRAE 90.1-2019 Appendix B U-values plus US EPA eGRID emission factors plus EnergyPlus EPW catalogue collectively eliminate the need for any custom data collection before modelling can begin [inputs/aim/OpenUBEM_Aim_Document.md §3.1–§3.6; reports/UBEM Inputs and GitHub Repository Review.md].

Practical impact targets: pip-installable; runnable in three lines of Python; backed by GitHub + Zenodo DOI + JOSS software paper; worked notebooks for Boston, Chicago, Phoenix, Seattle [inputs/aim/OpenUBEM_Aim_Document.md §2, §8.2].

## 2. Scope & Boundaries

### 2.1 In scope (this design — Phase 1 + Phase 2 architectural hooks)

The design covers the **complete five-stage pipeline** as specified in `inputs/aim/OpenUBEM_Technical_Pipeline.md`:

1. **Stage 1 — Data Acquisition.** OSM ingest via osmnx (or local `.osm` XML), reprojection to local UTM, ASHRAE climate zone detection, EPW download/cache from climate.onebuilding.org.
2. **Stage 2 — Semantic Enrichment.** OSM-tag-to-OpenStudio-30-type classification, ASHRAE 90.1-2019 / IECC 2021 construction sets, DOE prototype loads/schedules, KDE/PDE/ML imputation with provenance tracking.
3. **Stage 3 — IDF Generation.** Per-building IDF (one IDF per building, never combined), geomeppy extrusion, thermal-zoning strategy selection, shading-sphere context as `Shading:Building:Detailed` boxes (NOT simulated zones), HVAC template assignment.
4. **Stage 4 — Simulation.** Parallel EnergyPlus via `joblib` with the `loky` backend, isolated per-building output directories, IDD-version-locked at startup.
5. **Stage 5 — Results.** SQL/CSV parsing, EUI / GWP / IOD computation, GeoDataFrame join + GeoJSON / GeoPackage / CSV export, provenance columns preserved.

Plus: a **top-level `run_ubem()` API**, a **`main_openubem.py` CLI**, a **`pyproject.toml`** declaring all pip dependencies, and **architectural hooks for Phase 2** (probabilistic / ML imputation) and **Phase 3** (NECB Canada, TABULA Europe, solar via ladybug-core, EPW morphing).

### 2.2 Out of scope (explicit non-goals for Phase 1)

- **No native CityGML ingest.** OSM is the canonical input. CityGML / 3DCityDB integration is a Phase 3+ extension [inputs/aim/OpenUBEM_Aim_Document.md §9].
- **No detailed HVAC system sizing.** Phase 1 ships `HVACTemplate:Zone:IdealLoadsAirSystem` as default and `PackagedTerminalAirConditioner` as an option; no chiller plant, district loop, or VAV optimisation [inputs/aim/OpenUBEM_Technical_Pipeline.md Module 10b].
- **No grid co-simulation.** No OpenDSS, no REopt, no battery dispatch (URBANopt handles those; out of OpenUBEM's scope).
- **No microclimate (UHI) coupling in Phase 1.** Urban Weather Generator integration is deferred; rural EPW from climate.onebuilding.org is used as-is. Listed in §10 Open Questions.
- **No embodied carbon / LCA.** Operational GWP only via eGRID + 0.181 kg CO₂e/kWh for natural gas [inputs/aim/OpenUBEM_Aim_Document.md §3.6].
- **No Bayesian calibration loop.** Calibration is supported only by surfacing ground-truth comparison metrics; a closed-loop Bayesian / MCMC tuner is Phase 2+.
- **No interactive dashboard / web UI.** Visualization is a static module producing maps + violin plots + EUI charts; no Dash / Flask server.
- **No Rhino / Grasshopper / proprietary CAD path.**

### 2.3 Terminal inputs and outputs

**Inputs (minimal contract)** [inputs/aim/OpenUBEM_Technical_Pipeline.md §2]:
- A `location: str | tuple` (city name, lat/lon) **OR** a path to a pre-exported `.osm` XML file.
- Optionally: `radius_m`, `epw_path`, `output_dir`, `n_jobs`, `zoning_strategy`, `hvac_system`, `load_mode`, `imputation_mode`, `export_formats`.
- Bundled data shipped with the wheel: `ashrae_climate_zones.gpkg`, `ashrae_90_1_2019.json`, `iecc_residential.json`, `necb_canada.json` (Phase 3 stub), `doe_prototype_loads.json`, `openstudio_loads.json`, `doe_schedules.json`, `egrid_2022.json`, `epw_stations.csv`.

**Outputs**:
- A primary `gpd.GeoDataFrame` (and serialisation to GeoJSON / GeoPackage / CSV) containing one row per OSM building with the schema specified in §6.
- Per-building IDF files in `output_dir/idfs/<osm_id>.idf`.
- Per-building EnergyPlus output directories `output_dir/results/<osm_id>/` (eplusout.sql, eplusout.csv, eplustbl.htm, eplus.err).
- Optional figures (PNG / HTML maps).

## 3. Prior Art & Confirmed Decisions

### 3.1 Confirmed decisions inherited from `design_state.md`

The Confirmed Decisions Index is currently empty (this is the first `/design` session for this workspace). Therefore **all decisions in this draft are new and proposed**, and DOCUMENTER should append them on approval. The session log will record this as Session 1.

### 3.2 Tooling / library decisions (selected — see §8 for rationale)

| Concern | Decision | Rejected alternatives |
|---|---|---|
| Geometry library | **geomeppy ≥ 0.11.8** on top of **eppy ≥ 0.5.63** | Honeybee/Dragonfly (requires Rhino or Ladybug runtime); raw eppy alone (no 3D extrusion); ArchiCAD/Revit IFC (proprietary). |
| Simulation engine | **EnergyPlus 9.6 / 23.1** (open-source subprocess) | Modelica/AixLib (compile time, requires Dymola for production); custom RC (CEA-style — sacrifices fidelity); TRNSYS (commercial). |
| Spatial input | **OpenStreetMap via osmnx ≥ 1.9** | CityGML (rare in North America, requires 3DCityDB); proprietary parcel data (paywalled, region-locked); LiDAR-only (no semantic tags). |
| Parallelism | **joblib ≥ 1.3, `loky` backend** | `multiprocessing.Pool` (fragile error handling, no isolation); Dask (heavyweight for embarrassingly-parallel jobs); MPI (HPC-only). |
| Imputation core | **scipy.stats.gaussian_kde + scipy.stats.uniform; scikit-learn for ML hooks** | PyMC (Bayesian — Phase 2+); deep generative (TabDDPM, GAN — overkill for Phase 1). |
| Standards data | **DOE Prototype Buildings + ASHRAE 90.1-2019 + IECC 2021 + eGRID 2022** | TABULA (European, Phase 3); custom ASHRAE 169 zone shapefiles (already covered by bundled `ashrae_climate_zones.gpkg`). |
| License | **MIT** | GPL (viral, deters industry adoption); BSD-3 (acceptable but MIT preferred for JOSS workflow). |
| Distribution | **pip + Zenodo DOI + JOSS** | conda-forge first (community step 2); Docker-only (excludes laptop users). |

### 3.3 Methodological inheritance from Iseri et al. (2025)

Five elements are directly carried forward from the Bahçelievler case study and generalised here [inputs/aim/OpenUBEM_Aim_Document.md §4]:

1. **Zone-level resolution** (one floor = one thermal zone for residential; perimeter/core for large commercial).
2. **KDE imputation** (Gaussian kernel, Silverman bandwidth) for partially observed parameters.
3. **PDE imputation** (uniform within ASHRAE bounds) for fully missing parameters.
4. **ML-based imputation** (Random Forest / GBM / NN) for parameters with learnable structural relationships.
5. **VBASELINE → VOCCUPANT → VCONSTRUCTION → VCOMBINED four-version comparison framework** as a built-in analysis mode for sensitivity / uncertainty decomposition.

**Two prior-art alternatives explicitly rejected at the architecture level:**

- **Single combined neighbourhood IDF (UMI / CityBES style).** Rejected because (a) parallel EnergyPlus runs share the file unpredictably; (b) re-simulating one changed building forces re-simulation of the whole district; (c) error propagation across thousands of zones in one IDF makes failure diagnosis intractable. Decision: **one IDF per building**, neighbours added only as `Shading:Building:Detailed` boxes inside a sphere of influence [inputs/aim/OpenUBEM_Technical_Pipeline.md §6].
- **Reduced-order RC core (CEA / TEASER style).** Rejected for Phase 1 because (a) RC engines are tuned per-region and per-archetype, defeating standards-driven generalisation; (b) RC outputs don't expose the granular `Output:Variable` introspection that IDF-level transparency promises; (c) the project's stated competitive advantage is *full IDF access* [inputs/aim/OpenUBEM_Aim_Document.md §7]. RC surrogates may be **trained from EnergyPlus outputs** in Phase 2 via besos-style workflows [papers/besos-documentation-besos-documentation.md].

## 4. Architecture Overview

### 4.1 Top-down view

```
                ┌────────────────────────────────────────────────────────────────┐
                │                     run_ubem()  /  main_openubem.py            │
                └────────────────────────────────────────────────────────────────┘
                                              │
   ┌──────────────────────┬──────────────────┼──────────────────┬──────────────────────┐
   ▼                      ▼                  ▼                  ▼                      ▼
[STAGE 1]            [STAGE 2]           [STAGE 3]          [STAGE 4]              [STAGE 5]
acquisition/         semantic/           geometry/+idf/      simulation/            results/
   │                    │                    │                    │                    │
   ▼                    ▼                    ▼                    ▼                    ▼
osm_fetcher ─► classify (OSM tag→OpenStudio30) ─► footprint.simplify (≤120 verts)
climate_zone   construction_sets (ASHRAE 90.1) ─► zoning.generate_zones
epw_manager    loads / schedules               ─► context.shading_sphere (30 m default)
   │           imputation (KDE/PDE/ML)         ─► builder.BuildingIDF
   │                    │                       ─► surfaces (geomeppy extrude, WWR)
   │                    │                       ─► hvac (IdealAir | PackagedDX)
   │                    │                       ─► outputs (Output:Variable list)
   │                    ▼                              │
   │              GeoDataFrame                         ▼
   │              + provenance flags             one IDF / building
   ▼                                                   │
  buildings_gdf ─────────────────────────────► joblib.Parallel(loky, n_jobs=-1)
  (UTM, ≥20 m²)                                        │
                                              EnergyPlus subprocess (per worker)
                                              isolated work_dir/<osm_id>/
                                                       │
                                                       ▼
                                              parser (.sql primary, .csv fallback)
                                              compute_eui / compute_iod
                                              carbon.compute_gwp (eGRID)
                                              aggregator.aggregate_to_geodataframe
                                              export_results (GeoJSON, GPKG, CSV)
                                                       │
                                                       ▼
                                                results_gdf  +  visualization/
```

### 4.2 Module boundaries (15 modules, 5 stages)

The package layout follows `inputs/aim/OpenUBEM_Technical_Pipeline.md §3` exactly. Folder = stage; module file = unit of responsibility:

| Folder | Modules | Responsibility |
|---|---|---|
| `acquisition/` | 1 osm_fetcher · 2 climate_zone · 2 epw_manager | Location → projected GeoDataFrame + ASHRAE zone + EPW path |
| `semantic/` | 3 building_classifier · 4 construction_sets · 5 loads · 6 schedules · 6b imputation | OSM row → complete EnergyPlus parameter table + provenance |
| `geometry/` | 7 footprint · 8 zoning · 8b context | Polygon → validated, zoned geometry + shading neighbours |
| `idf/` | 9 builder · 10 surfaces · 10b hvac · 11 outputs | Zone dicts + parameters → valid `.idf` file on disk |
| `simulation/` | 12a runner · 12b parallel | Dispatch EnergyPlus subprocesses, isolate output dirs |
| `results/` | 13 parser · 14 aggregator · 15 carbon · 16 visualization | Parse outputs → results GeoDataFrame → exports |

### 4.3 Architectural invariants (binding)

These are non-negotiable; they directly resolve known failure modes documented in the inputs:

- **(I1) One IDF per building.** Parallel jobs cannot share an IDF or output directory; this resolves the silent-overwrite bug class flagged in `inputs/aim/OpenUBEM_Technical_Pipeline.md §11.2`.
- **(I2) Each EnergyPlus worker writes to a unique `work_dir/<osm_id>/`.** EnergyPlus emits fixed filenames (`eplusout.sql`, `eplusout.csv`); shared dirs corrupt results.
- **(I3) IDD version is locked once at module import** via `eppy.modeleditor.IDF.setiddname(IDD_PATH)` matching the EnergyPlus binary; mismatched IDD/binary is a known silent failure [inputs/aim/OpenUBEM_Technical_Pipeline.md §11.3].
- **(I4) Footprint simplification (Douglas-Peucker, 0.5 m) runs *before* any geomeppy call.** EnergyPlus has a 120-vertex limit per surface, and geomeppy's `intersect_match` fails silently on non-convex inputs [inputs/aim/OpenUBEM_Technical_Pipeline.md §11.1].
- **(I5) Each parameter carries a provenance code** in {`OSM_OBSERVED`, `ASHRAE_STANDARD`, `KDE_IMPUTED`, `PDE_GENERATED`, `ML_PREDICTED`, `HEURISTIC`} [inputs/aim/OpenUBEM_Technical_Pipeline.md §12]. The provenance column is preserved through to the exported GeoDataFrame.
- **(I6) Every stage writes a persistent intermediate** (GeoDataFrame parquet, semantic JSON, IDF, EnergyPlus output dir, aggregated GeoDataFrame) — Stage *N* can be re-run without repeating Stages 1..*N–1*.
- **(I7) No proprietary dependencies.** Every import in `pyproject.toml` is OSI-approved licensed.

### 4.4 Data-flow summary

```
location ─► buildings_gdf (geom + OSM tags)
        ─► climate_zone (str like "5A")
        ─► epw_path (Path)

buildings_gdf + (climate_zone, epw_path)
        ─► enriched_gdf (+ building_type, construction_set, loads, schedules,
                          provenance_<param> for each)

enriched_gdf  ─► [for each row]  BuildingIDF object  ─► <osm_id>.idf

{<osm_id>.idf} + epw_path  ─► joblib parallel  ─► {results/<osm_id>/eplusout.sql}

{results/<osm_id>/}  ─► parser  ─► per-building eui/iod dict
                     ─► aggregator  ─► results_gdf (joined on osm_id)
                     ─► export  ─► {.geojson, .gpkg, .csv}
```

## 5. Component Specifications

For each component below: **purpose · inputs · outputs · key methods · libraries · validation criterion**. Module numbers match `inputs/aim/OpenUBEM_Technical_Pipeline.md`.

---

### 5.1 (a) GIS data ingestion & preprocessing — `acquisition/`

**Module 1 — `osm_fetcher.fetch_buildings`**
- **Purpose**: Pull OSM building footprints for a location, project to local UTM, return standardised GeoDataFrame.
- **Inputs**: `location: str | tuple`, `radius_m: float = 1000`, `bbox: tuple = None`, `osm_path: Path = None`, `tags: dict = {'building': True}`.
- **Outputs**: `gpd.GeoDataFrame` with columns specified in §6.1.
- **Key methods**: `osmnx.features_from_point()` / `features_from_bbox()`; `gdf.estimate_utm_crs()`; filter to Polygon/MultiPolygon; drop `footprint_area_m2 < 20` (OSM noise threshold) [inputs/aim/OpenUBEM_Technical_Pipeline.md §4 Module 01].
- **Libraries**: osmnx ≥ 1.9, geopandas ≥ 0.14, shapely ≥ 2.0, pyproj ≥ 3.6.
- **Validation criterion**: For Boston downtown 500 m radius test fixture, expect **n_buildings between 200 and 600** (sanity bounds; exact count is OSM-state-dependent — listed in §10 Open Questions). All returned geometries are valid Polygons in a projected UTM CRS; no NaN in `geometry`.

**Module 2 — `climate_zone.get_climate_zone` + `epw_manager.get_nearest_epw`**
- **Purpose**: Map (lat, lon) → ASHRAE zone code; resolve nearest EPW file, downloading from climate.onebuilding.org if absent.
- **Inputs**: `lat: float`, `lon: float`, optional `epw_dir: Path`.
- **Outputs**: `climate_zone: str` (e.g. "5A"), `epw_path: Path`.
- **Key methods**: Spatial join against bundled `data/climate_zones/ashrae_climate_zones.gpkg` (DOE county-level mapping); fallback US-city lookup table. EPW resolution order: user-provided dir → `~/.openubem/epw/` cache → download from climate.onebuilding.org → fallback energyplus.net/weather. Uses `pyproj.Geod` for geodesic distance to find nearest station.
- **Libraries**: geopandas, pyproj, requests ≥ 2.31.
- **Validation criterion**: 100% accuracy on a 50-city sanity tuple list (Boston→5A, Phoenix→2B, Seattle→4C, Chicago→5A, Miami→1A, …); EPW found for every US lat/lon ≥ 24°N within 200 km geodesic distance.

---

### 5.2 (b) Building footprint + attribute enrichment — handled across `acquisition/` (geom) and `semantic/` (attributes)

The OSM tags consumed are: `building=*`, `building:levels=*`, `height=*`, `building:levels:underground=*`, `roof:shape=*`, `start_date=*`, `amenity=*`, `shop=*`, `office=*`, `addr:postcode=*` [inputs/aim/OpenUBEM_Technical_Pipeline.md §2 table]. Missing values are not yet imputed at this stage — they are passed through with NaN to the imputation module (5.4).

---

### 5.3 (c) Archetype assignment & template mapping — `semantic/building_classifier.py`, `construction_sets.py`, `loads.py`, `schedules.py`

**Module 3 — `building_classifier.classify_building`**
- **Purpose**: Resolve OSM tags + footprint + floor count → an OpenStudio Standards 30-type label (16 DOE commercial + IECC residential + extended types Lab/DataCenter/Courthouse/TallBuilding/SuperTallBuilding) [inputs/aim/OpenUBEM_Technical_Pipeline.md §5 Module 03].
- **Inputs**: a single GeoDataFrame row.
- **Outputs**: `os_type: str` (one of 30 fixed labels).
- **Key methods**: priority cascade `function_tag → building_tag → footprint+floors heuristic`. The fixed `OSM_TO_OPENSTUDIO_TYPE` dictionary is the single source of truth. High-rise heuristic: n_floors > 20 → TallBuilding; n_floors > 40 → SuperTallBuilding. Size tier rules (`select_prototype_size`) for office/hotel/apartment/data-centre per the table in `inputs/aim/OpenUBEM_Technical_Pipeline.md §5`.
- **Libraries**: pandas, numpy.
- **Validation criterion**: Manual ground-truth on 200 buildings from Boston Downtown — target ≥ 90% top-1 accuracy for residential vs commercial split (residential vs commercial is a coarser, easier task than the 30-type fine label, where ground truth is sparse on OSM — see §10).

**Module 4 — `construction_sets.get_construction_set`**
- **Purpose**: Look up envelope U-values, SHGC, infiltration for `(building_type, climate_zone, vintage)`.
- **Inputs**: `building_type: str`, `climate_zone: str`, `year_built: int = None`, `standard: str = '90.1-2019'`.
- **Outputs**: dict `{roof: {u_value, assembly}, wall: {…}, window: {u_value, shgc}, floor: {u_value}, infiltration_rate}`.
- **Key methods**: JSON lookup into bundled `data/construction/ashrae_90_1_2019.json` (commercial), `iecc_residential.json` (residential), `necb_canada.json` (Phase 3 stub). Vintage correction multipliers on U-values (see §7.2).
- **Libraries**: json (stdlib).
- **Validation criterion**: For MediumOffice / 5A / 2019, returned roof U = 0.273 W/m²K, wall U from ASHRAE 90.1-2019 Table 5.5-5 (within ±0.001 W/m²K of published value).

**Module 5 — `loads.get_loads`** — DOE prototype internal load densities (lighting W/m², equipment W/m², occupant density m²/person, infiltration m³/s/m², heating/cooling setpoints/setbacks). Deterministic mode: published DOE values. Probabilistic mode: PDE sampling with ASHRAE 90.1 bounds. Example MediumOffice values listed in `inputs/aim/OpenUBEM_Technical_Pipeline.md §5 Module 05`.

**Module 6 — `schedules.get_schedule_definitions`** — Returns list of `Schedule:Compact` dicts (occupancy, lighting, equipment, HVAC operation, thermostat) differentiated Weekday / Saturday / Sunday from `data/schedules/doe_schedules.json`.

**Validation criterion (modules 5–6)**: Round-trip a generated IDF through EnergyPlus; verify `Output:Variable` annual totals match published DOE prototype monthly EUIs within ±5% for the climate zone (DOE prototypes are themselves the ground truth here).

---

### 5.4 Imputation — `semantic/imputation.py`

**Module 6b — `impute_column`**
- **Purpose**: Fill missing values in a parameter column (e.g., `year_built`, `wall_u_value`) using KDE / PDE / ML based on missingness fraction.
- **Inputs**: `series: pd.Series`, `method: 'auto'|'kde'|'pde'|'ml' = 'auto'`, `bounds: (float, float) = None`, `model_path: Path = None`.
- **Outputs**: `pd.Series` of same length with NaN replaced + a parallel `provenance: pd.Series` of codes.
- **Key methods (auto logic)**:
  - 0% < missing < 100% → `scipy.stats.gaussian_kde` with Gaussian kernel and Silverman bandwidth, resample until value within `[bounds]`. Tag: `KDE_IMPUTED`.
  - 100% missing → `scipy.stats.uniform(loc=a, scale=b-a).rvs(n_missing)`. Tag: `PDE_GENERATED`.
  - `model_path` provided → `joblib.load(model_path).predict(feature_matrix)`. Tag: `ML_PREDICTED`.
- **Libraries**: scipy ≥ 1.11, scikit-learn ≥ 1.4, joblib ≥ 1.3.
- **Validation criterion**: On a synthetic test set of 1,000 buildings where 30% of `wall_u_value` is hidden, KDE-imputed values reproduce the true distribution within Kolmogorov-Smirnov D < 0.10 against the observed 70%. PDE values lie within bounds 100% of the time.

---

### 5.5 (d) IDF generation (geomeppy / eppy) — `geometry/`, `idf/`

**Modules 7–8 — `footprint.py`, `zoning.py`** — Polygon validation (`shapely.is_valid`, area > 20 m², not self-intersecting); Douglas-Peucker simplification at 0.5 m tolerance with convex-hull fallback (invariant I4); zoning strategy selection (`single_zone` for footprint < 500 m²; `one_zone_per_floor` for residential; `perimeter_core` for large commercial per ASHRAE 90.1 Appendix G with 4.57 m perimeter depth). Geometry metrics computed: `footprint_area_m2`, `perimeter_m`, `total_height_m`, `form_factor` (S/V — flagged in `inputs/aim/OpenUBEM_Technical_Pipeline.md §6 Module 07` as the dominant 70.3% predictor of QH), `aspect_ratio`, `floor_area_m2 = footprint × n_floors`.

**Module 8b — `context.get_shading_context` + `build_shading_boxes`**
- **Sphere of influence**: default 30 m, configurable. 20–30 m for residential/low-rise (covers 1–2 rows of neighbours); 40–60 m for dense commercial/downtown urban canyon. Spatial query: `gdf[gdf.intersects(target.buffer(r))]`, exclude self by `osm_id`. Context buildings emitted as `Shading:Building:Detailed` boxes (footprint bbox × height) — **never as zones**.

**Module 9 — `idf/builder.py:BuildingIDF`** — Central class orchestrating `_load_base_idf` → `set_geometry` → `set_construction` → `set_loads` → `set_schedules` → `set_hvac` → `set_outputs` → `add_shading_context` → `save`. Templates in `idf/templates/`: `commercial_base.idf`, `residential_base.idf`, `highrise_base.idf` (TallBuilding/SuperTall), `specialized_base.idf` (Lab/DataCenter/Warehouse). Each template contains only Version, SimulationControl, RunPeriod, Site:Location, Timestep stubs — the rest is populated programmatically.

**Modules 10, 10b — `surfaces.py`, `hvac.py`** — `extrude_zone` calls `geomeppy.geom.polygons` to create `BuildingSurface:Detailed`; assigns `FenestrationSurface:Detailed` (windows) by WWR per orientation; OutdoorAir for exterior, Surface for interior. Critical exception path: catch `geomeppy.geom.core.NotARectangleError` → fallback to `polygon.minimum_rotated_rectangle`. HVAC default: `HVACTemplate:Zone:IdealLoadsAirSystem`; opt-in `PackagedTerminalAirConditioner` with `cop_heat`, `cop_cool` from construction_set.

**Module 11 — `outputs.py`** — Writes the fixed `STANDARD_OUTPUTS` list (11 zone-level + site variables), `OutputControl:Table:Style HTML`, and `Output:Table:SummaryReports` for ABUPS [inputs/aim/OpenUBEM_Technical_Pipeline.md §6 Module 11].

**Validation criterion (Stage 3)**: For every IDF written, EnergyPlus `--design-day` smoke test must terminate with zero severe errors. On the 200-building Boston fixture, ≥ 98% IDFs must pass; failures must be classified (geomeppy fallback, vertex limit, missing class) and counted.

---

### 5.6 (e) Simulation orchestration & HPC parallelism — `simulation/`

**Modules 12a/12b — `runner.py`, `parallel.py`**
- **Purpose**: Dispatch one EnergyPlus subprocess per IDF in parallel, isolated by output directory.
- **Inputs**: `buildings_gdf`, `idf_dir: Path`, `output_dir: Path`, `epw_path: Path`, `n_jobs: int = -1`, `backend: str = 'loky'`.
- **Outputs**: List of `{osm_id, status: 'success'|'failed', output_dir, error}` dicts.
- **Key methods**:
  ```python
  Parallel(n_jobs=n_jobs, backend=backend, verbose=verbose)(
      delayed(run_single_building)(*task) for task in tasks
  )
  ```
  where `run_single_building` enforces invariant I2 (`work_dir = output_dir / osm_id; work_dir.mkdir(...)` before subprocess) and calls `energyplus -w {epw} -d {work_dir} -r {idf}`.
- **HPC adaptation**: On Calcul Québec / Concordia HPC, `n_jobs` is set to `SLURM_CPUS_PER_TASK` (read from env), and the same `joblib`+`loky` code runs unchanged on a single SLURM allocation. For multi-node scale-out, an SLURM array job submits chunks of N buildings per array task — matching the spatial-chunking pattern in `reports/Open Source Urban Building Energy Modeling-Architecture.md` (avoids O(N²) intersect cost across chunk boundaries).
- **Libraries**: joblib ≥ 1.3, subprocess (stdlib).
- **Validation criterion**: 200-building Boston fixture: ≥ 95% success rate; total wall-clock time on a 32-core node ≤ 30 min (estimate based on annual 8760 h IdealAir runs ≈ 5–10 s of EnergyPlus CPU-time per small building, so 200 buildings × 8 s × 1.5 (HVAC overhead) / 32 cores ≈ 75 s + I/O. Rounded up to 30 min for first-pass safety. Listed in §10 if measured timing is unavailable.)

---

### 5.7 (f) Results aggregation & uncertainty quantification — `results/`

**Modules 13–15 — `parser.py`, `aggregator.py`, `carbon.py`**
- **`parse_building_results`**: Reads SQL via `sqlite3` (preferred — structured query), falls back to `eplusout.csv`. Returns DataFrame with columns `[zone_name, month, heating_kwh, cooling_kwh, lighting_kwh, equipment_kwh, infiltration_kwh, mean_temp_c, operative_temp_c, occupant_hours]`.
- **`compute_eui(zone_df, floor_area_m2)`**: monthly→annual aggregation, divide by floor area → `{heating_eui_kwh_m2, cooling_eui_kwh_m2, lighting_eui_kwh_m2, equipment_eui_kwh_m2, total_eui_kwh_m2}`.
- **`compute_iod(zone_df, epw_path)`**: ASHRAE 55 adaptive comfort, Tn = 0.31·Tave + 17.8, Tcomf = Tn + 2.5, IOD = mean(max(OT − Tcomf, 0)) over occupied summer hours.
- **`carbon.compute_gwp`**: eGRID subregion electricity factor (state-indexed JSON); natural gas 0.181 kg CO₂e/kWh per Iseri et al. (2025); returns per-end-use and total GWP in kg CO₂e/m²/yr.
- **`aggregator.aggregate_to_geodataframe`**: left-join on `osm_id` to original `buildings_gdf`; appends 14 result columns + `simulation_status`.
- **`export_results`**: GeoJSON, GeoPackage, CSV via `gpd.to_file`.

**Phase 2 — uncertainty quantification module hook**: a `results/uncertainty.py` (architectural placeholder) will run the **VBASELINE → VOCCUPANT → VCONSTRUCTION → VCOMBINED four-version sweep** by re-running Stages 2–5 with successive layers of probabilistic inputs enabled, then aggregating per-building energy distributions (mean, std, 5th/95th percentile). Output: `uncertainty_gdf` with `eui_mean`, `eui_std`, `eui_p05`, `eui_p95`, `eui_attribution: dict` (% variance from occupant / construction / interaction).

**Validation criterion**: Reproduce Iseri et al. (2025) Bahçelievler annual EUIs for the published 24 buildings within ±10% (assuming the same EPW and construction inputs). Listed in §8.

---

### 5.8 (g) Output layer / visualization / API — `results/visualization.py`, `openubem/__init__.py`, `main_openubem.py`

- **`run_ubem(...)` API**: signature in `inputs/aim/OpenUBEM_Technical_Pipeline.md §9`. Returns the `results_gdf`. Three-line minimal usage:
  ```python
  import openubem
  results = openubem.run_ubem('Downtown Boston, MA', radius_m=500)
  print(results[['building_type', 'total_eui_kwh_m2', 'gwp_total_kgco2_m2']])
  ```
- **CLI `main_openubem.py`**: `--location`, `--osm_file`, `--radius`, `--output`, `--mode {deterministic|probabilistic}`, `--n_jobs`.
- **Visualization (Module 16)**: choropleth maps via `geopandas.plot()` on Folium / Matplotlib; violin plots of EUI by building_type; provenance heatmap.

## 6. Data Model & Interfaces

### 6.1 Stage-1 GeoDataFrame schema (`buildings_gdf`)

| Column | dtype | Source | Notes |
|---|---|---|---|
| `geometry` | shapely Polygon | OSM | Projected UTM (EPSG via `estimate_utm_crs`) |
| `osm_id` | str | OSM | Primary key downstream |
| `building_tag` | str | OSM `building=*` | NaN allowed |
| `function_tag` | str | OSM `amenity`/`shop`/`office` | NaN allowed |
| `levels` | float | OSM `building:levels` | NaN if missing — imputed Stage 2 |
| `height_m` | float | OSM `height` | NaN if missing — derived from `levels × 3.5 m` |
| `year_built` | float (year) | OSM `start_date` | NaN if missing — KDE/PDE imputed |
| `underground` | float | OSM `building:levels:underground` | Default 0 |
| `roof_shape` | str | OSM `roof:shape` | Default "flat" |
| `footprint_area_m2` | float | computed | Drop if < 20 m² |
| `perimeter_m` | float | computed | |
| `postcode` | str | OSM `addr:postcode` | None allowed |

### 6.2 Stage-2 enriched GeoDataFrame (additions)

| Column | dtype | Notes |
|---|---|---|
| `building_type` | str | OpenStudio 30-type label |
| `climate_zone` | str | "1A".."8" |
| `vintage` | str | "pre1980"\|"1980-2004"\|"2004-2010"\|"2010-2016"\|"2016+" |
| `n_floors` | int | from `levels` or imputed |
| `floor_to_floor_m` | float | derived (default 3.5) |
| `wall_u_value`, `roof_u_value`, `floor_u_value`, `window_u_value`, `window_shgc`, `infiltration_rate` | float | from construction_set |
| `lighting_w_m2`, `equipment_w_m2`, `occupant_density_m2_person`, `heating_setpoint_c`, `cooling_setpoint_c`, `heating_setback_c`, `cooling_setup_c` | float | from loads |
| `provenance_<param>` | str | one of {OSM_OBSERVED, ASHRAE_STANDARD, KDE_IMPUTED, PDE_GENERATED, ML_PREDICTED, HEURISTIC} |

### 6.3 Stage-5 results GeoDataFrame (additions)

`heating_eui_kwh_m2`, `cooling_eui_kwh_m2`, `lighting_eui_kwh_m2`, `equipment_eui_kwh_m2`, `total_eui_kwh_m2`, `gwp_heating_kgco2_m2`, `gwp_cooling_kgco2_m2`, `gwp_lighting_kgco2_m2`, `gwp_equipment_kgco2_m2`, `gwp_total_kgco2_m2`, `iod`, `simulation_status` (success|failed), `error_message` (str|None).

### 6.4 Persistent intermediate formats

- `buildings_stage1.parquet` — Stage 1 GeoDataFrame.
- `enriched_stage2.parquet` + `enriched_stage2.json` (semantic table with provenance).
- `idfs/<osm_id>.idf` — Stage 3 outputs.
- `results/<osm_id>/eplusout.sql` — Stage 4 outputs.
- `openubem_results.{geojson|gpkg|csv}` — Stage 5 final.

### 6.5 External data dependencies (frozen versions)

| Resource | Version | Source | Distribution |
|---|---|---|---|
| OpenStreetMap | live | osmnx ≥ 1.9 → Overpass API | runtime fetch |
| ASHRAE climate zones | DOE county-level mapping | bundled `ashrae_climate_zones.gpkg` | wheel |
| ASHRAE 90.1 | 2019 (commercial) | encoded JSON | wheel |
| IECC | 2021 (residential) | encoded JSON | wheel |
| NECB (Phase 3) | 2011/2015/2017 | encoded JSON stub | wheel |
| DOE Prototype Buildings | 2013/2019/2022 vintages | derived loads + schedules JSON | wheel |
| eGRID | 2022 | bundled JSON | wheel |
| EPW catalogue | climate.onebuilding.org TMYx | runtime download → `~/.openubem/epw/` cache | runtime |
| EnergyPlus | 9.6 or 23.1 | energyplus.net | user-installed binary, path via env |

## 7. Algorithms & Methods

### 7.1 Archetype classification — rule-based, NOT clustered or ML-based for Phase 1

Three approaches were reviewed in `reports/UBEM Inputs and GitHub Repository Review.md` and `papers/comparing-domain-expert-and-machine-learning-data-enrichment-of-building-registry.md`:

1. **Rule-based / deterministic engineering** (DOE Prototype + ASHRAE) — high structure, fast, but rigid.
2. **k-means / clustering on observed EUIs** (Therrien 2020 Victoria, Cerezo et al. 2015 Kuwait) — captures real variance but requires utility-meter ground truth that we explicitly do not assume in Phase 1.
3. **ML classifiers (RF / XGBoost) trained on building registries** [papers/comparing-domain-expert-and-machine-learning-data-enrichment-of-building-registry.md] — outperform domain experts on type imputation when ≥ 1k labelled training rows are available.

**Decision: rule-based for Phase 1.** Justification: (a) the OSM tag → OpenStudio mapping is the only path that requires zero pre-training data, satisfying the "data-scarce environments" goal of `OpenUBEM_Aim_Document.md §4`. (b) DOE / ASHRAE provides a defensible standards baseline that auditors and policymakers accept. (c) Clustering and ML approaches are deferred to Phase 2 and exposed as drop-in replacements via the same `classify_building` interface (interface-stable, implementation-pluggable).

### 7.2 Vintage correction multipliers on U-values

From `inputs/aim/OpenUBEM_Technical_Pipeline.md §5 Module 04`:
- pre-1980 → multiply by 1.6 (ASHRAE 90.1 baseline + degradation factor; rationale: empirical in-situ studies show measured U-values up to 2× theoretical due to degradation [reports/UBEM Inputs and GitHub Repository Review.md, Concrete envelopes 0.14–5.45 W/m²K range]).
- 1980–2004 → ASHRAE 90.1-1999 factors.
- 2004–2016 → ASHRAE 90.1-2013 factors.
- 2016+ → ASHRAE 90.1-2019 (factor 1.0, baseline).

### 7.3 Imputation — three-tier strategy (KDE + PDE + ML)

Direct port of the Iseri et al. (2025) framework [inputs/aim/OpenUBEM_Aim_Document.md §4]:

- **KDE** for partial missingness (0% < missing < 100%): `scipy.stats.gaussian_kde` with Silverman bandwidth, Gaussian kernel; resample with rejection on `[bounds]`. Justification: Silverman is robust default; KDE preserves the empirical distribution of observed buildings without parametric assumption [reports/Open Source Urban Building Energy Modeling - General.md].
- **PDE** for full missingness (100% missing): `scipy.stats.uniform(loc=a, scale=b-a)` with bounds from ASHRAE 90.1 / DOE prototype ranges. Justification: when no observation exists, the principle of maximum entropy under bound constraints is a uniform — does not inject false structure.
- **ML** when a pre-trained model is supplied: `joblib.load(model_path).predict(X)`. Phase-2 default: `RandomForestRegressor` on `(year_built, building_type, climate_zone) → wall_u_value`.

Rejected alternatives:
- **Multiple Imputation by Chained Equations (MICE)** — strong on tabular, but assumes MAR; OSM missingness is closer to MNAR (e.g., older buildings systematically lack `start_date`), so MICE residual bias is substantial [reports/Open Source Urban Building Energy Modeling - General.md].
- **Deep generative (VAE / TabDDPM)** — requires ≥ 10k training rows; unavailable for Phase 1.
- **Single deterministic mean/median imputation** — destroys variance, exactly the failure mode we are trying to avoid.

### 7.4 Energy simulation configuration — annual 8760 h, NOT representative-day

Decision: full annual hourly EnergyPlus run (8760 h) with `RunPeriod` = full year. Justification:
- **Representative-day approaches** (heating design day + cooling design day + 12 typical days per month) speed up by ~30× but lose hourly profile fidelity needed for downstream peak-load and ML-surrogate training tasks [papers/a-systematic-literature-review-of-physics-based-urban-building-energy-modeling-ubem-tools-data-sourc.md].
- **Hourly 8760** is the gold standard for EUI and IOD outputs (IOD requires hourly operative-temperature trace). The DOE Prototype protocol is also 8760.
- Cost: a small commercial 8760 IdealAir run is 5–15 s wall-clock on modern hardware; at city scale this is acceptable when parallelised (see §9).

Rejected: **reduced-order RC core** (CEA / TEASER style) — see §3.3.

### 7.5 Surrogate / ML acceleration — Phase 2 only

Phase 2 will train surrogate ML models on EnergyPlus outputs via the **besos** workflow [papers/besos-documentation-besos-documentation.md]: parametric sample (Latin Hypercube) → run EnergyPlus batch → train scikit-learn / TensorFlow regressor → use as surrogate predictor for new buildings. This enables city-scale (≫ 10⁵ building) inference without re-running EnergyPlus.

### 7.6 Shading-context algorithm

Per-building sphere of influence (default 30 m, configurable). Rationale (from `inputs/aim/OpenUBEM_Aim_Document.md §5` and `inputs/aim/OpenUBEM_Technical_Pipeline.md §6`): EnergyPlus long-wave radiant exchange between buildings can change cooling/heating load by up to 3.6% in dense canyons [reports/Open Source Urban Building Energy Modeling-Architecture.md citing Hong et al.]. We capture this via simplified `Shading:Building:Detailed` boxes (footprint bbox × estimated height) — not as zoned thermal models, which would explode IDF size and runtime.

Spatial chunking: on city-scale runs, the buildings_gdf is partitioned into geographic tiles before parallel dispatch; each tile carries its own neighbour buffer. This avoids the O(N²) all-pairs intersect query that stalls naive implementations [reports/Open Source Urban Building Energy Modeling-Architecture.md].

## 8. Validation Strategy

### 8.1 Validation hierarchy (4 levels)

**Level 1 — Component unit tests (`tests/`):**
- `test_acquisition.py`: OSM fetch from canned `.osm` fixture; climate zone correctness; EPW resolution.
- `test_semantic.py`: Classifier on 50-row labelled CSV (≥ 90% top-1); construction-set lookup byte-equal to ASHRAE 90.1-2019 published values.
- `test_imputation.py`: KS test that KDE-imputed series matches truth (D < 0.10); PDE values within bounds 100%.
- `test_geometry.py`: Vertex count ≤ 120 for 100% of simplified footprints; convex-hull fallback path exercised.
- `test_idf.py`: every generated IDF passes EnergyPlus design-day smoke test with zero severe errors.

**Level 2 — DOE Prototype round-trip (synthetic ground truth):**
For each of 16 DOE commercial prototypes × 5 climate zones (1A, 3A, 5A, 7, 8), run OpenUBEM's IDF generator with the prototype's footprint and parameters, then compare its annual EUI to DOE's published prototype EUI. Pass criterion: **±5% on `total_eui_kwh_m2`** for IdealAir HVAC. This isolates OpenUBEM's IDF-assembly correctness from envelope-data correctness.

**Level 3 — Iseri et al. (2025) Bahçelievler replication:**
Reproduce the published 24-building case study from Energy & Buildings 337, 115620 [inputs/aim/OpenUBEM_Aim_Document.md §4]. Pass criterion: **±10%** on per-building annual heating EUI vs. the paper's reported values, given the same EPW and construction inputs. The 10% tolerance accounts for the methodology being generalised from Turkish residential to a US/ASHRAE pipeline.

**Level 4 — City-scale calibration against utility data:**
For Boston, Chicago, Phoenix, Seattle worked-example notebooks [inputs/aim/OpenUBEM_Aim_Document.md §8.2], compare aggregate simulated EUI to the **U.S. Building Performance Database (BPD)** [reports/Open Source Urban Building Energy Modeling-Architecture.md] median EUI by building type per city. Targets follow ASHRAE Guideline 14:
- **CV(RMSE) < 30%** at building level (relaxed because input archetypes are non-calibrated; Guideline 14's 15% bound assumes calibrated models).
- **NMBE within ±10%** at neighbourhood aggregate level (n ≥ 100 buildings).
- **R² > 0.6** for predicted vs measured median EUI by building_type × city.

### 8.2 Ground truth sources

- **DOE Prototype Buildings** (Level 2) — direct, exact published numbers.
- **Iseri et al. 2025 supplementary data** (Level 3) — the methodology origin study.
- **U.S. Building Performance Database (BPD)** (Level 4) — > 1 M building records.
- **CBECS / RECS** (Level 4 sanity bounds) — Commercial / Residential Buildings Energy Consumption Surveys.
- **City-disclosure data** where available (e.g., NYC Local Law 84 reports, San Francisco Existing Buildings Energy Performance Ordinance) — listed in §10 since access is per-city.

### 8.3 Metrics

- **CVRMSE** (Coefficient of Variation of RMSE) — primary Level-4 fit metric; ASHRAE 14 standard.
- **NMBE** (Normalized Mean Bias Error) — sign of systematic bias.
- **R²** — explained variance, archetype-level.
- **Kolmogorov-Smirnov D** — distributional fit (imputation, archetype variance).
- **Top-1 accuracy** — classifier (rule-based and Phase-2 ML).
- **% IDFs passing smoke test** — IDF generation health.

### 8.4 Spatial scales

| Scale | Metric | Target |
|---|---|---|
| Building | CVRMSE | < 30% |
| Block (5–20 buildings) | NMBE | ±15% |
| Neighbourhood (~ 100 buildings) | NMBE | ±10% |
| City-aggregated | NMBE | ±5% |

### 8.5 Two rejected validation strategies

- **Bayesian calibration loop (UBEM Cambridge style, Sokol et al.)** — rejected for Phase 1 because (a) it requires per-building monthly utility data, which is unavailable openly for most US cities; (b) closed-loop calibration violates the "no hidden state" goal; (c) the four-version VBASELINE→VCOMBINED framework already provides uncertainty decomposition. Phase 2 may add this as an opt-in module.
- **Sensor / monitored-data validation (CityFFD coupling style)** — rejected because the cost of deploying or accessing IoT sensor networks is outside the project's open-data charter [inputs/aim/OpenUBEM_Aim_Document.md §11].

## 9. Compute & Resource Plan

### 9.1 Per-building EnergyPlus cost (single-threaded baseline)

From the systematic literature review and Nassau-County 346,827-building precedent [reports/Open Source Urban Building Energy Modeling - General.md] and the Iseri et al. (2025) Bahçelievler base case:

| Building class | Zones | Annual 8760 wall-clock (1 core, EnergyPlus 23.1, IdealAir) |
|---|---|---|
| Small residential (single zone) | 1–3 | ~ 5 s |
| Medium commercial (perim+core, 4 floors) | ~ 25 | ~ 30 s |
| Large commercial / hotel (≥ 9 floors) | ~ 60 | ~ 90 s |
| TallBuilding / SuperTall | ~ 200 | ~ 300 s |

Mean used for budget estimates: **~ 15 s/building** (mixed urban distribution skewed residential).

### 9.2 Scenario budgets

| Scenario | n_buildings | Cores | Wall-clock (est.) |
|---|---|---|---|
| Boston Downtown 500 m worked example | ~ 400 | 32 (1 node) | ~ 4 min |
| Chicago Loop worked example | ~ 1,500 | 32 | ~ 15 min |
| Full Boston city scale | ~ 90,000 | 1,024 (32 nodes × 32 cores) | ~ 25 min |
| Nassau County replication | ~ 350,000 | 4,096 (128 nodes × 32 cores) | ~ 30 min |

Sensitivity scenarios (4-version framework — VBASELINE → VOCCUPANT → VCONSTRUCTION → VCOMBINED): multiply by 4.
Probabilistic Monte-Carlo runs (Phase 2): 100 samples × 4 versions = 400× — gating these to subset analyses (≤ 1,000 buildings) keeps wall-clock tractable.

### 9.3 HPC target — Calcul Québec / Concordia

- **Cluster**: Béluga / Narval / Cedar (Calcul Québec / Digital Research Alliance of Canada).
- **Allocation strategy**: SLURM array jobs, one task per spatial chunk of ~ 100 buildings, `--cpus-per-task=32`, `--time=01:00:00`, `--mem=64G` (EnergyPlus is memory-light, ~ 200 MB per worker; 64 G accommodates 32 workers + EPW caching).
- **Phase-1 ceiling**: 2,000 core-hours/month is sufficient for development + validation + the four worked examples + one city-scale run. Listed in §10 as confirmation pending — PI to allocate.

### 9.4 Python parallelism choice — joblib + loky

Justification (matching `inputs/aim/OpenUBEM_Technical_Pipeline.md §7`):
- **joblib.Parallel** is the eppy-community standard (`runIDFs` uses it) [papers/besos-documentation-besos-documentation.md].
- **loky backend** is process-based (bypasses GIL), survives worker crashes (re-spawn), and integrates cleanly with `Parallel(n_jobs=-1, verbose=10)` for progress.
- Each EnergyPlus invocation is a `subprocess.run` — joblib's job is to dispatch many in parallel; once dispatched, EnergyPlus runs natively.

Two rejected alternatives:
- **`multiprocessing.Pool`** — coarser error model; a single worker crash can deadlock the pool; no built-in retry.
- **Dask** — dataset-oriented; overkill when the per-task payload is just `(idf_path, work_dir, epw_path)`. Adds scheduler overhead without benefit. Reconsider for Phase 2 if surrogate-model training pipelines are added.

### 9.5 Disk / I/O budget

Per building: IDF ~ 200 KB; EnergyPlus output dir (SQL + CSV + ERR + tables) ~ 5–20 MB, retained until parsed; results GeoDataFrame row ~ 1 KB.
For 100,000 buildings: ≈ 1 TB raw EnergyPlus outputs — auto-cleaned after Stage-5 parse unless `keep_raw=True`. Listed as a configurable option to control disk pressure on shared HPC scratch.

## 10. Open Questions

These are explicitly NOT resolvable from `inputs/` and must be answered before/during implementation:

1. **Per-building EnergyPlus wall-clock on Calcul Québec hardware.** §9.1 numbers are inferred from literature precedent (Nassau County) and EnergyPlus's typical performance, not measured on Béluga / Narval. Need: measure on a 200-building Boston fixture before committing to Phase-2 scale numbers.
2. **Calcul Québec / Concordia HPC core-hour allocation.** §9.3 assumes 2,000 core-hours/month — needs PI confirmation through DRAC RAC/RAS process.
3. **Boston-Downtown 500 m radius expected building count.** §5.1 cites a 200–600 sanity bound, but OSM completeness varies; needs a definitive `osmnx.features_from_point()` snapshot to fix the unit-test fixture.
4. **Per-city utility-disclosure data licences.** §8.2 mentions NYC LL84, SF Existing Buildings Ordinance — terms-of-use for redistributing benchmark CSVs alongside example notebooks need legal review.
5. **OSM-to-OpenStudio classifier accuracy on the full 30-type taxonomy.** §5.3 cites ≥ 90% accuracy *for residential vs commercial split only*. The fine-grained 30-type accuracy is unknown without a hand-labelled ground-truth set; budget 200 buildings × 4 cities for a manual labelling sprint.
6. **Iseri et al. (2025) supplementary-data accessibility.** §8.1 Level-3 replication assumes the 24-building Bahçelievler dataset (geometries, EPC values) is published as supplementary. Confirm with author (PI is co-author).
7. **NECB Canada construction JSON.** §3.2 lists `necb_canada.json` as a Phase-3 stub; sourcing the full NECB 2011/2015/2017 envelope-table machine-readable form (or transcribing from the standard) is unscheduled work.
8. **Urban Heat Island morphing.** §2.2 lists UWG out of scope for Phase 1. Should the architecture pre-wire a `weather/uwg_morph.py` placeholder and a `weather_morph_method` config flag now to avoid breaking-change later? Recommend yes; needs explicit decision.
9. **Non-rectangular footprint failure rate on real OSM data.** §5.5 sets a target of ≥ 98% IDFs passing smoke test. Actual rate is unknown for messy OSM polygons (especially historic city cores); needs empirical measurement on the Boston / Chicago fixtures.
10. **CV(RMSE) target relaxation.** §8.1 Level 4 sets CV(RMSE) < 30% at building level. ASHRAE Guideline 14 sets 15%; we doubled because models are uncalibrated. Is 30% acceptable to the research community / NSERC reviewers? Decision needed.
11. **OSM tag → OpenStudio mapping coverage on edge cases.** The `OSM_TO_OPENSTUDIO_TYPE` dict in `inputs/aim/OpenUBEM_Technical_Pipeline.md §5` covers 24 source tags; OSM has hundreds of `building=*` values. Default fallback for unknown tags (currently `MediumOffice` — to be confirmed) is unspecified.
12. **Probabilistic/ML imputation training data for Canadian context.** Phase 3 NECB pathway needs Canadian building-stock training data (year_built × type × envelope_U); CMHC and Statistics Canada hold relevant data but neither is on the bundled-data list yet.
13. **Schedule realism.** Phase 1 ships deterministic DOE schedules (Module 6). The Section-1 critique that homogeneous schedules artificially inflate peak loads [reports/UBEM Inputs and GitHub Repository Review.md, Dabirian 2024] is acknowledged. Stochastic schedule integration (Markov / Gaussian-mixture from Concordia's own Dabirian 2024 thesis) is Phase-2 work — confirm scope.
14. **EnergyPlus version pin.** §3.2 supports 9.6 OR 23.1. Should the wheel ship two IDD files and auto-detect? Or pin to 23.1 only and document 9.6 as a known-working alternative?

## 11. References

All references are file paths within `inputs/` of this workspace. No fabricated DOIs.

**AIM (charter):**
- `inputs/aim/OpenUBEM_Aim_Document.md` — sections 1 (problem statement), 2 (project aim, five goals), 3.1–3.6 (DOE/IECC/ASHRAE/eGRID stack), 4 (Iseri et al. 2025 methodological foundation), 5 (eppy/geomeppy rationale), 6 (five-stage pipeline), 7 (differentiation table), 9 (roadmap), 10 (case study), 11 (open-source commitment).
- `inputs/aim/OpenUBEM_Technical_Pipeline.md` — sections 2 (minimum inputs), 3 (project structure), 4 (Stage 1 modules 1–2), 5 (Stage 2 modules 3–6 + 6b), 6 (Stage 3 modules 7–11), 7 (Stage 4 module 12), 8 (Stage 5 modules 13–15), 9 (run_ubem API), 10 (dependencies), 11 (critical impl notes), 12 (provenance tracking).

**Reports (deep research):**
- `inputs/reports/Open Source Urban Building Energy Modeling - General.md` — comparative analysis of CEA, UMI, URBANopt, SimStadt, CityBES, TEASER, CitySim, OpenIDEAS; KDE / PDE methodological framing; Nassau County 346,827-building precedent; Energy ADE.
- `inputs/reports/Open Source Urban Building Energy Modeling-Architecture.md` — Python architecture patterns, geomeppy procedural geometry, surface-matching via PyClipper, joblib/loky parallelism, BESOS surrogate modelling, GIS spatial chunking, residual/Bayesian calibration.
- `inputs/reports/UBEM Inputs and GitHub Repository Review.md` — LoD framework; deep-learning WWR extraction (Turin study, 35.5% cooling delta); deterministic vs statistical archetype comparison (Andorra, Victoria); CityGML Energy ADE structure; BuildingSync; envelope U-value empirical ranges; PPL / LPD ranges; stochastic occupancy (Dabirian 2024 Concordia, ABM, MCMC); UWG / ENVI-met / CityFFD; BPD ground truth; Bayesian calibration (Cambridge MA case).

**Selected papers:**
- `inputs/papers/a-systematic-literature-review-of-physics-based-urban-building-energy-modeling-ubem-tools-data-sourc.md` — physics-based UBEM systematic review.
- `inputs/papers/urban-building-energy-modeling-ubem-a-systematic-review-of-challenges-and-opportunities-university-o.md` — challenges/opportunities review.
- `inputs/papers/open-source-urban-building-energy-modeling-pdf.md` — open-source UBEM landscape.
- `inputs/papers/besos-documentation-besos-documentation.md` — BESOS surrogate modelling and parametric workflow.
- `inputs/papers/city-energy-analyst-cea-future-cities-laboratory-eth-zurich.md` — CEA history, RC engine, ETH Zurich, 32% building / 5% neighbourhood mean error baseline.
- `inputs/papers/geomeppy-0-11-8-documentation.md` — geomeppy IDF API (add_block, add_shading_block, intersect_match).
- `inputs/papers/deep-research-report-analytical-frameworks-for-the-construction-of-urban-building-energy-models-meth.md` — analytical frameworks methodology.
- `inputs/papers/data-shortage-for-urban-energy-simulations-an-empirical-survey-on-data-availability-and-enrichment-m.md` — empirical data-availability survey.
- `inputs/papers/an-approach-to-data-acquisition-for-urban-building-energy-modeling-using-a-gaussian-mixture-model-an.md` — Gaussian-mixture data-acquisition method (Phase-2 schedule reference).
- `inputs/papers/information-mining-for-urban-building-energy-models-ubems-from-two-data-sources-openstreetmap-and-ba.md` — OSM information mining for UBEM.
- `inputs/papers/comparing-domain-expert-and-machine-learning-data-enrichment-of-building-registry.md` — domain-expert vs ML data enrichment (justifies Phase-2 ML imputation).
- `inputs/papers/step-3-gis-data-preparation-ubem-io.md` — UBEM.io GIS data preparation step.
- `inputs/papers/a-new-workflow-for-detailed-urban-scale-building-energy-modeling.md` — detailed urban-scale workflow paper.
- `inputs/papers/validating-gis-ubem-a-residential-open-data-driven-urban-building-energy-model.md` — GIS-UBEM residential validation.
- `inputs/papers/bausim2024-22-pdf.md` — CityGML data preparation for thermal building simulation at district level (BauSim 2024).

**External anchor cited via inputs (no fabricated DOI):**
- Iseri, O.K., Duran, A., Canlı, I., Meral Akgul, C., Kalkan, S., & Gursel Dino, I. (2025). *A method for zone-level urban building energy modeling in data-scarce built environments.* Energy & Buildings, 337, 115620 — cited at `inputs/aim/OpenUBEM_Aim_Document.md §4`. This is the methodological origin of OpenUBEM's KDE/PDE/four-version framework and is referenced throughout §3.3, §5.7, §7.3, and §8.1.

---

## 11. Progress Log *(populated by downstream `/run` reporter — leave empty here)*

<!-- The downstream execution project's reporter agent appends `### Session: <date> | Loop: <N>` blocks under this header after each /run cycle. This design file becomes the canonical living record once execution begins. -->

---

## 12. Revision Log

### Session: 2026-05-02 | Pass 1 | APPROVED
- Initial design. All 11 sections written from scratch.
- Critic verdict: APPROVED on first pass (4 minor non-blocking notes).
- Key decisions locked: one-IDF-per-building invariant, joblib/loky parallelism, KDE/PDE Phase-1 imputation, ASHRAE 90.1-2019 + IECC 2021 + DOE prototype library, four-stage validation (unit/integration/literature/calibration).

<!-- Append-only. DOCUMENTER inserts a new block on each /design re-run. -->
