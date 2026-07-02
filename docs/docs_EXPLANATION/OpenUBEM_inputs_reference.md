# OpenUBEM — Inputs Reference

**What this document is:** a single map of every kind of input data OpenUBEM consumes —
building layout, occupancy/loads, envelope standards, weather, HVAC, service loads, carbon
factors, and the ground-truth datasets used for validation. For each input: what it is,
where the real-world data comes from, where it physically lives in the repo, and which code
module reads it. For the *pipeline* explanation see
[`OpenUBEM_fundamentals.md`](OpenUBEM_fundamentals.md); for the *reporting* methodology see
[`simulated_vs_reconstructed_methodology.md`](simulated_vs_reconstructed_methodology.md); for
the binding specs see `docs/docs_main/` (cross-cutting) and `docs/docs_main/docs_stepN/`
(per-step).

Two things are always true about every row below:

- **Bundled data is frozen and versioned.** Everything under `openubem/data/` ships inside
  the pip wheel — no network access needed to run a simulation once EnergyPlus and weather
  data are in place. Each subfolder with a `PROVENANCE.md` records the exact upstream
  commit/URL/retrieval date it was built from (cited per row below).
- **Only two things are fetched at runtime:** the OpenStreetMap building footprints
  themselves (via `osmnx` → Overpass API) and the EPW weather file for the resolved
  location (via climate.onebuilding.org, cached locally afterward).

---

## 1. At a glance — input category → real-world source → file → consumer

| # | Input category | What it represents | Real-world source | Bundled file (`openubem/data/…`) | Consuming module |
|---|---|---|---|---|---|
| 1 | Building footprints & tags | Geometry + raw attribute tags per building | OpenStreetMap (live, via `osmnx` → Overpass API) | *(runtime fetch — not bundled)* | `acquisition/osm_fetcher.py` |
| 2 | OSM tag → use-class map | Maps ~60 OSM `building=`/`amenity=`/`shop=`/`office=` values to 6 use-classes | Manually curated map, DESIGN §3A Module 03; checked against peer UBEM-tool practice in `RESULT_I01` (§6) | `osm_to_use_class.json` | `semantic/building_classifier.py` |
| 3 | Archetype vocabulary | 30 fixed DOE/OpenStudio archetype definitions (the classifier's only possible outputs); the 17-rule size/level cascade that picks among them was threshold-checked in `RESULT_I02` (§6) | OpenStudio *Building Types and Templates* (NREL) | `openstudio_archetypes.json` | `semantic/building_classifier.py` |
| 4 | Climate zone polygons | County → ASHRAE climate zone (1A–8) | US Census county boundaries + NREL ResStock housing-characteristics matrix (ASHRAE 169-2013-consistent) | `climate_zones/ashrae_climate_zones.gpkg` | `acquisition/climate_zone.py` |
| 5 | Weather station catalogue | Nearest-station lookup index (~2,900 US stations) | climate.onebuilding.org TMYx KML index | `epw_stations.csv` | `acquisition/epw_manager.py` |
| 6 | Weather data (EPW) | Actual 8760-hour weather file used by EnergyPlus | climate.onebuilding.org (primary) / energyplus.net (fallback) | *(runtime download → `~/.openubem/epw` cache)* | `acquisition/epw_manager.py`, `simulation/runner.py` |
| 7 | Envelope / construction | U-values, SHGC, infiltration by (archetype, climate zone, vintage) — all 30 archetypes, residential and commercial alike | ASHRAE 90.1-2019, via NREL `openstudio-standards` (commit `83b1e64`) | `construction/ashrae_90_1_2019.json` | `semantic/construction_sets.py` |
| 8 | Internal loads | Lighting/equipment power density, occupant density, setpoints per archetype | PNNL-20405 DOE Prototype Buildings + NREL `openstudio-standards` space types | `loads/doe_prototype_loads.json`, `loads/openstudio_loads.json` | `semantic/loads.py` |
| 9 | Occupancy/lighting/equipment/setpoint schedules | Hourly fractional operating profiles, weekday/Sat/Sun, per archetype | Digitized from real DOE Commercial Prototype IDFs, ASHRAE 90.1-2013 edition (energycodes.gov) | `schedules/doe_schedules.json` | `semantic/schedules.py` |
| 10 | HVAC system assignment | Which of 10 system families (VAV, PSZ, PVAV, FCU, WLHP, PTAC/PTHP, …) per archetype/size/climate | ASHRAE 90.1-2019 Appendix G system-type rules + DOE prototype baselines | `loads/hvac_systems_by_archetype.json` | `idf/hvac.py` |
| 11 | HVAC efficiency (COP) | Rated heating/cooling efficiency per archetype × climate zone | DOE Commercial Reference Buildings + AHRI equipment ratings | `loads/hvac_cop_by_archetype.json` | `idf/hvac.py` |
| 12 | Domestic hot water (DHW) | Peak flow, annual volume, heater fuel/setpoint, city mains temperature | PNNL commercial prototypes + ASHRAE 90.1 Appendix G baseline DHW | `loads/dhw_by_archetype.json` | `idf/dhw.py` |
| 13 | Cooking loads | Kitchen exhaust + process-load intensity per archetype/hood type | PNNL Full/Quick-Service-Restaurant prototypes + ASHRAE 90.1 §6.5.3.1 kitchen exhaust | `loads/cooking_by_archetype.json` | `idf/cooking.py` |
| 14 | Refrigeration | Lumped equipment intensity (4 archetypes) + detailed case/rack layout (SuperMarket) | ENERGY STAR Portfolio Manager supermarket data + ASHRAE 90.1 Appendix G refrigeration specs | `refrigeration/refrigeration_lumped.json`, `refrigeration/supermarket_cases.json` | `idf/refrigeration.py` |
| 15 | Service-load end-use fractions (legacy overlay) | % split of whole-building energy across 9 end-uses, by archetype / census region | CBECS 2018 + PNNL Commercial Prototype models (deep-research Table 4) | `service_loads/enduse_fractions_table4.json`, `service_loads/enduse_fractions_regional.json` | `results/service_loads.py` *(Phase-D2 reconstruction overlay — retired as of Phase-E, kept for back-compat/report mode)* |
| 16 | Archetype ↔ CBECS mapping | Maps OpenUBEM's 30 archetypes to CBECS Principal Building Activity codes for national benchmarking; crosswalk validated against the CBECS 2018 codebook in `RESULT_I03` (§6) | CBECS 2018 (Commercial Buildings Energy Consumption Survey) | `cbecs_pba_map.json` | validation/aggregation scripts |
| 17 | Carbon intensity (electricity) | kg CO₂e/kWh, state-level and eGRID-subregion-level | EPA eGRID 2022 | `carbon/egrid_2022.json`, `carbon/egrid_2022_subregions.json` | `results/carbon.py` |
| 18 | Carbon intensity (natural gas) | Fixed factor, 0.181 kg CO₂e/kWh | Iseri et al. (2025), Energy & Buildings 337 | hard-coded constant, `openubem/config.py` | `results/carbon.py` |
| 19 | EnergyPlus engine | The physics solver itself | EnergyPlus 23.1 (energyplus.net), user-installed binary | *(not bundled — path via `ENERGYPLUS_PATH` env var)* | `simulation/runner.py` |

**Classification audit (rows 2, 3, 16).** Three deep-research reports
(`docs/docs_ACTIVE/input/deepResearch/RESULT_I01`–`I03`, full citations in §6) checked the OSM tag
map, the archetype size/level cascade, and the CBECS crosswalk against peer UBEM-tool practice and
primary sources (DOE/PNNL prototype TSDs, the CBECS 2018 codebook). Headline findings — not yet
acted on, audit pending manager review:

- **`RESULT_I01`** — OpenUBEM's symmetric tag-agreement rule (a `function_tag` and `building_tag`
  must agree, or the row becomes `mixed`) is a likely deviation from peer practice (URBANopt,
  CityBES, AutoBEM, CEA all let a specific function tag like `amenity=clinic` outrank a generic
  structural tag outright). ~24 common OSM tags (e.g. `building=duplex`, `amenity=place_of_worship`,
  `office=government`) are absent from `osm_to_use_class.json` and currently fall through to
  `unknown`.
- **`RESULT_I02`** — 3 of the 6 size/level cut-points in the archetype cascade (office,
  secondary-vs-primary school, large-vs-small hotel) misclassify the very DOE/PNNL prototype
  buildings the thresholds were meant to represent (e.g. the 511 m² Small Office prototype itself
  falls on the Medium-Office side of OpenUBEM's current 500 m² cut). Highrise/midrise apartment and
  data-center cut-points check out against precedent.
- **`RESULT_I03`** — the archetype↔CBECS-PBA crosswalk is correct but coarser than necessary;
  CBECS' own `PBAPLUS`/`SQFT`/`NFLOOR` sub-variables would let the office, restaurant, hotel, and
  education archetypes each score against a narrower CBECS bin instead of one shared code. The
  residential and data-center exclusions are both confirmed correct as-is.

---

## 2. Building layout & occupancy — what comes from OpenStreetMap

OpenUBEM never asks a user to enter a building's geometry, height, or use by hand. All of it
is pulled from OpenStreetMap and then completed by the archetype it is matched to.

| OSM tag | Becomes | Notes |
|---|---|---|
| `geometry` (way/relation) | `geometry` (footprint polygon, reprojected to local UTM) | Source of all geometric derivatives below |
| `building=*` | `building_tag` | e.g. `apartments`, `commercial`, `warehouse` |
| `amenity=*`, `shop=*`, `office=*` | `function_tag` | First non-null wins, in that priority order |
| `building:levels=*` | `levels` | NaN → imputed in Stage 2 |
| `height=*` | `height_m` | NaN → derived as `levels × 3.5 m` |
| `building:levels:underground=*` | `underground` | Default 0 |
| `roof:shape=*` | `roof_shape` | Default `"flat"` |
| `roof:height=*` | `roof_height_m` | Optional |
| `start_date=*` | `year_built` | NaN → KDE/PDE-imputed; feeds `vintage_standard` |
| `addr:postcode=*` | `postcode` | Informational only |

`footprint_area_m2`, `perimeter_m`, `form_factor`, `aspect_ratio`, and `floor_area_m2`
(`footprint_area_m2 × n_floors`) are all **computed**, not tagged — there is no OSM source
for them. Buildings under 20 m² are dropped as OSM noise (`acquisition/osm_fetcher.py`).

`building_tag` + `function_tag` are looked up in `osm_to_use_class.json` to get a coarse
`use_class` (residential / commercial / industrial / institutional / mixed / unknown), which
the classifier then combines with footprint area and floor count to pick one of the **30
archetypes** in `openstudio_archetypes.json` (see DESIGN §5.3 / `docs/docs_main/docs_step2/`
for the full rule cascade). "Occupancy" in the UBEM sense — how many people, when, doing
what — is **not** an OSM input at all: it comes entirely from the matched archetype's
schedules and loads (rows 8–9 above), not from anything observed about the specific
building.

The `function_tag`/`building_tag` priority rule above ("first non-null wins") and the
`osm_to_use_class.json` tag list were independently checked against peer UBEM-tool practice —
see `RESULT_I01_osm_tag_to_use_class_mapping.md` (§6) for the full comparison table and the list
of commonly-used OSM tags currently missing from the map.

---

## 3. Building energy standards — what governs the physics

| Standard | Edition | What it supplies | Bundled as |
|---|---|---|---|
| ASHRAE 90.1 | 2019 (envelope + Appendix G HVAC system rules, all 30 archetypes incl. residential) | Wall/roof/window/floor U-values, SHGC, infiltration, HVAC system-type assignment, kitchen exhaust requirements | `construction/ashrae_90_1_2019.json`, `loads/hvac_systems_by_archetype.json` |
| ASHRAE 90.1 | 2013 (digitized prototype IDFs) | Real occupancy/lighting/equipment/setpoint schedules per archetype | `schedules/doe_schedules.json` |
| DOE Prototype Buildings (PNNL-20405) | 2011/2013/2019/2022 vintages | Internal load densities, HVAC baselines, DHW/cooking/refrigeration intensities | `loads/doe_prototype_loads.json`, `loads/openstudio_loads.json`, `loads/dhw_by_archetype.json`, `loads/cooking_by_archetype.json`, `refrigeration/*.json` |
| CBECS 2018 | — | National per-archetype energy distributions for validation; end-use fraction splits (legacy reconstruction) | `cbecs_pba_map.json`, `service_loads/enduse_fractions_table4.json` |
| EPA eGRID | 2022 | Electricity carbon intensity, state + subregion | `carbon/egrid_2022.json`, `carbon/egrid_2022_subregions.json` |

Vintage correction multipliers (pre-1980 ×1.6 down to 2013+ ×1.0 on envelope U-values) are
derived from the ratio of each `openstudio-standards` edition's tables to the 2019 baseline —
see `openubem/data/construction/PROVENANCE.md` for the full derivation and the two recorded
DESIGN erratum rulings (R-2.2-1/2/3).

---

## 4. HVAC and service loads (Phase-E physical baseline)

As of the adopted Phase-E baseline (2026-06-27), every end-use is a **real EnergyPlus
object**, not a post-hoc estimate (see
[`simulated_vs_reconstructed_methodology.md` §7](simulated_vs_reconstructed_methodology.md)
for the full before/after). Each archetype gets:

| End-use | EnergyPlus object | Input data file | Real-world source |
|---|---|---|---|
| Heating / cooling | `HVACTemplate:Zone:*` (10 families: VAV, PSZ, PVAV, FCU, WLHP, PTAC/PTHP, …) | `loads/hvac_systems_by_archetype.json` + `loads/hvac_cop_by_archetype.json` | ASHRAE 90.1-2019 Appendix G + DOE prototype baselines + AHRI ratings |
| Fans / pumps | Supply/exhaust fans, hot-water/chilled-water plant pumps (central-plant archetypes only) | (parameters embedded in `hvac_systems_by_archetype.json`) | ASHRAE 90.1-2019 Appendix G |
| Domestic hot water | `WaterHeater:Mixed` + `WaterUse:Equipment` | `loads/dhw_by_archetype.json` | PNNL prototypes + ASHRAE 90.1 Appendix G baseline DHW |
| Cooking | `ZoneVentilation:DesignFlowRate` (kitchen exhaust) + `OtherEquipment` (process load) | `loads/cooking_by_archetype.json` | PNNL FSR/QSR prototypes + ASHRAE 90.1 §6.5.3.1 |
| Refrigeration | `Refrigeration:Case` + `Refrigeration:CompressorRack` (SuperMarket); lumped `ElectricEquipment` (4 other food/health archetypes) | `refrigeration/supermarket_cases.json`, `refrigeration/refrigeration_lumped.json` | ENERGY STAR Portfolio Manager supermarket data + ASHRAE 90.1 Appendix G |

The older **reconstruction overlay** (`service_loads/enduse_fractions_table4.json` /
`enduse_fractions_regional.json`, CBECS-2018-derived fraction splits applied as a multiplier
on the simulated total) is retired as the production path but still present in
`results/service_loads.py` behind the `OPENUBEM_RECONSTRUCT_SERVICE_LOADS` flag for
back-compat / reporting comparisons. Full coefficient table and per-archetype source
citations: `docs/docs_DONE/serviceLoads/SERVICE_LOADS_coefficients.md`.

---

## 5. Validation / ground-truth datasets

These are not pipeline *inputs* (they never enter a simulation) — they are the **external,
independent measured data** every result is scored against, report-only, never tuned to.

| Dataset | City / scope | What it provides | Used in |
|---|---|---|---|
| NYC Local Law 84 (LL84) disclosure data | New York City (CZ 4A) | Measured, weather-normalized site EUI by property type (EPA Portfolio Manager) | City-anchor comparison, `docs/docs_DONE/hvac-ServiceLoads/REPORT_phaseE_final.md` §6 |
| LA EBEWE (Existing Buildings Energy and Water Efficiency, CA AB 802) | Los Angeles (CZ 3B) | Measured site EUI by property type | Same |
| CBECS 2018 West-South-Central region (proxy) | Austin (CZ 2A) | National regional mean EUI — used as a proxy since Austin has no mandatory disclosure law | Same |
| CBECS 2018 national survey | All three cities | Per-archetype distribution gates (NMBE, CV(RMSE), R², KS_D) | `cbecs_pba_map.json` + validation gate scripts |
| U.S. Building Performance Database (BPD) | National | Level-4 city-scale calibration ground truth (DESIGN §8.2) | `docs/docs_main/DESIGN_...md` §8 |
| Iseri et al. (2025), *Energy & Buildings* 337 | Bahçelievler, Turkey (24 buildings) | Per-building heating EUI replication target (±10%); natural-gas carbon factor (0.181 kg CO₂e/kWh) | DESIGN §3.3, `results/carbon.py` |

Source prompts/results for the three city benchmarks live in
`docs/docs_VALIDATION/step1/external_literature/` (`RESULT_1_nyc_ll84_measured.md`,
`RESULT_2_la_california_measured.md`, `RESULT_3_austin_texas_measured.md`).

---

## 6. Cross-reference — where each input is documented in depth

| Input area | Provenance / detail doc |
|---|---|
| Construction (envelope), internal loads, schedules | `openubem/data/construction/PROVENANCE.md` |
| Climate zones, EPW station catalogue | `openubem/data/climate_zones/PROVENANCE.md` |
| Carbon factors (eGRID) | `openubem/data/carbon/PROVENANCE.md` |
| Schedules (digitized DOE prototype IDFs) | `docs/docs_DONE/scheduleDigitization/PROVENANCE.md` |
| Service-load end-use fractions (legacy overlay) | `docs/docs_DONE/serviceLoads/SERVICE_LOADS_coefficients.md` |
| HVAC / DHW / cooking / refrigeration deep research | `docs/docs_DONE/hvac-ServiceLoads/deepResearch/` (RESULT_01 through RESULT_05) |
| OSM tag → use-class mapping vs. peer UBEM-tool practice | `docs/docs_ACTIVE/input/deepResearch/RESULT_I01_osm_tag_to_use_class_mapping.md` |
| Archetype size/level cut-points vs. DOE/PNNL prototype TSDs | `docs/docs_ACTIVE/input/deepResearch/RESULT_I02_archetype_classification_cascade.md` |
| Archetype ↔ CBECS-PBA crosswalk vs. the CBECS 2018 codebook | `docs/docs_ACTIVE/input/deepResearch/RESULT_I03_cbecs_pba_crosswalk_validation.md` |
| Phase-E physical-simulation results & methodology | `docs/docs_DONE/hvac-ServiceLoads/REPORT_phaseE_final.md` |
| External validation ground truth | `docs/docs_VALIDATION/step1/external_literature/` |
| Full bundled-data inventory + config constants | root `README.md` §"Data Assets" and §"Configuration & Constants" |
| Binding architecture / data-model spec | `docs/docs_main/DESIGN_openubem-open-source-urban-building-energy-modeling-platform-design-the-full-sys.md` §5–§7 |

---

## 7. Where to go next

| You want… | Read |
|---|---|
| The plain-language pipeline overview | `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` |
| How simulated vs. reconstructed vs. physical EUI differ | `docs/docs_EXPLANATION/simulated_vs_reconstructed_methodology.md` |
| The binding design specs | `docs/docs_main/` (cross-cutting) + `docs/docs_main/docs_stepN/` (per step) |
| The full validation record | `docs/docs_VALIDATION/` |
| Current project status | `docs/PROJECT_CHECKLIST.md` |

---

*OpenUBEM — inputs reference. Cross-references the binding DESIGN spec, per-module
PROVENANCE.md files, the Phase-E adopted baseline, and the I01–I03 classification deep-research
audit. 2026-06-30.*
