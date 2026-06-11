# Step 5 — EnergyPlus Work Directories → EUI / GWP / IOD Results GeoDataFrame
### OpenUBEM Stage 5 / Modules 13–16: `openubem/results/{parser,aggregator,carbon,visualization}.py` — parse each building's `eplusout.sql`, compute five EUI metrics, five GWP metrics, and IOD, join everything back onto the 57-column GeoDataFrame, and export `05_results.{gpkg,geojson,csv}` — the pipeline's final deliverable

> **Slug:** `step-5-parse-energyplus-outputs-into-eui-gwp-iod-and-aggregate-results-back-to-th` &nbsp;•&nbsp; **First created:** `2026-06-09` &nbsp;•&nbsp; **Latest revision:** `2026-06-09`
>
> Sections 1–9 are **append-once, edit-never** after first APPROVED verdict. Section 10 (Progress Log) is owned by the downstream `/run` reporter. All `/design` re-run changes are recorded under **Section 11 — Revision Log**.
>
> **Scope rule.** This document covers exactly **one** step of the umbrella pipeline — Step 5 (results aggregation). The step's *internal* sub-stages (3A–3G) live under §3 Pipeline. Stage 4 (parallel simulation) is covered in its own per-step DESIGN doc; there is no downstream pipeline step — Step 5 emits the final OpenUBEM deliverable.

---

## 1. Aim

Step 5 converts the fleet of per-building EnergyPlus work directories produced by Step 4 into the pipeline's final deliverable: a results GeoDataFrame in which every building carries five EUI metrics (kWh/m²/yr), five GWP metrics (kg CO₂e/m²/yr), an Indoor Overheating Degree (IOD, °C), and a simulation status — exported as GeoPackage, GeoJSON, and CSV. Upstream it consumes `04_simulation_manifest.parquet` plus each success-row's `eplusout.sql`, and re-joins onto the 57-column enriched GeoDataFrame from Stages 1–2. There is no downstream pipeline stage; downstream *consumers* are humans (maps, retrofit screening), the umbrella project's ML stages (surrogate training labels), and the §5 validation harness — Step 5 is also where the umbrella project's headline validation thresholds (CV(RMSE) < 30%, NMBE ±10%, R² > 0.6, KS D < 0.10 against CBECS 2018 — `.claude/design_state.md` confirmed decision) are actually computed. Without Step 5 the pipeline produces terabytes of SQL files and no answer to the question OpenUBEM exists to answer: *what is the energy use, carbon footprint, and overheating risk of every building in this neighbourhood?* The module decomposition (parser / aggregator / carbon / visualization) and metric definitions follow `inputs/aim/OpenUBEM_Technical_Pipeline.md` §8 (Stage 5); the GWP factor conventions follow Iseri et al. (2025, *Energy & Buildings* 337, 115620 — `inputs/papers/1-s2-0-s0378778825003500-main-pdf.md`).

---

## 2. Inputs

| Artifact | Source | Dtype | Shape | Notes |
|---|---|---|---|---|
| `04_simulation_manifest.parquet` | Step 4 (Module 12b) | Parquet | (N_input, 11) | Binding Step 4 output contract. Step 5 filters `status ∈ {success, success_cached}` and follows `sql_path`; all other rows pass through to the results GDF with NaN metrics + their status token (flag-don't-drop). |
| `<output_dir>/results/<osm_id>/eplusout.sql` | Step 4 work dirs | SQLite | one per success row, ~5–20 MB | Primary parse source. EnergyPlus 23.1 SQL schema: `ReportDataDictionary` / `ReportData` / `Time` for hourly variables; `TabularDataWithStrings` for the ABUPS annual summary used as a cross-check. Written because Step 3 §3I mandates `Output:SQLite SimpleAndTabular`. |
| `<output_dir>/results/<osm_id>/eplusout.csv` | Step 4 work dirs (readVarsESO) | CSV | one per success row | Documented fallback when `eplusout.sql` is missing or unreadable; rows parsed this way are flagged `RESULTS_CSV_FALLBACK` (see §3A). |
| `<output_dir>/results/<osm_id>/eplusout.mtr` | Step 4 work dirs | text | one per success row | RunPeriod `Electricity:Facility` and `NaturalGas:Facility` meters (Step 3 §3I `Output:Meter:MeterFileOnly`) — consumed only by the §5.1 closure gates. |
| `03_idf_manifest.parquet` | Step 3 | Parquet | (N_input, ≥9) | Supplies `zoning_strategy`, `num_zones`, and updated `data_quality_flag` for the results join and for filtering sensitivity analyses. |
| `02_buildings_classified.gpkg` (post-enrichment) | Step 2 → Modules 02/04/05/06/06b | GeoDataFrame | (N, 57) | The spatial frame the results join back onto: geometry, `osm_id`, `footprint_area_m2`, `levels`, `height_m`, `archetype_id`, `climate_zone`, provenance columns. The full 57-column contract is preserved byte-identical in the output (Step 2 discipline). |
| `data/carbon/egrid_2022.json` | bundled in package | JSON | US state → eGRID subregion → kg CO₂e/kWh | Electricity emission factors (eGRID 2022 — confirmed standards-stack decision). Natural gas constant 0.181 kg CO₂e/kWh per Iseri et al. (2025). |
| `config.py` | package config | Python module | — | Exposes `GWP_NATURAL_GAS_KGCO2_KWH` (0.181), `GWP_CONVENTION` (`"load_referenced_v1"`), `IOD_SUMMER_MONTHS` (default Jun 1–Sep 30), `EUI_PLAUSIBILITY_BOUNDS` ((25, 1000) kWh/m²/yr). |

> Note on the `state` lookup for eGRID: the per-neighbourhood US state required by `egrid_2022.json` is not yet a committed column of the enriched GDF — Module 02 (undesigned; Step 3 OQ-7 / Step 4 OQ-5 / pending Step 2.5) is its natural owner via the county-level climate-zone spatial join. Interim resolution in §3E; tracked as §7 OQ-3.

---

## 3. Pipeline

Step 5 is a per-building parse loop (3A–3E) followed by two whole-neighbourhood operations (3F join + aggregation, 3G export + visualization). Sub-stages 3A–3E are pure functions of one building's work dir + manifest row; 3F–3G see all buildings at once. All energy values are converted from Joules to kWh exactly once, at the parse boundary (3A) — every downstream number in this document is kWh.

### 3A — SQL Extraction (Module 13: `openubem/results/parser.py`)

For each manifest row with `status ∈ {success, success_cached}`, the parser opens `eplusout.sql` with stdlib `sqlite3` and pulls all Hourly report variables in one query:

```python
# Module 13: openubem/results/parser.py
HOURLY_QUERY = """
SELECT d.KeyValue       AS key_value,      -- zone name (UPPERCASED by EnergyPlus)
       d.Name           AS variable_name,  -- e.g. 'Zone Ideal Loads Zone Total Heating Energy'
       d.Units          AS units,          -- 'J' for energy, 'C' for temperatures
       t.Month, t.Day, t.Hour,
       r.Value          AS value
FROM   ReportData r
JOIN   ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
JOIN   Time t                 ON r.TimeIndex = t.TimeIndex
WHERE  d.ReportingFrequency = 'Hourly'
"""

J_TO_KWH = 1.0 / 3.6e6

def parse_building_sql(sql_path: Path) -> pd.DataFrame:
    with sqlite3.connect(f'file:{sql_path}?mode=ro', uri=True) as conn:
        df = pd.read_sql_query(HOURLY_QUERY, conn)
    # Single canonical unit conversion — Joules → kWh at the parse boundary
    is_energy = df['units'] == 'J'
    df.loc[is_energy, 'value'] *= J_TO_KWH
    df.loc[is_energy, 'units'] = 'kWh'
    return df
```

If `eplusout.sql` is missing or `sqlite3` cannot open it, the parser falls back to `eplusout.csv` (readVarsESO output, retained by Step 4's §3F policy), normalizing its `KEY:Variable [Units](Hourly)` column headers into the same long-format frame; the building's `parse_status` is set to `success_csv_fallback` and the token `RESULTS_CSV_FALLBACK` is appended to its `data_quality_flag`. If both sources fail, `parse_status = failed_parse` and the building flows through with NaN metrics — never dropped.

> **Why this approach:** SQL-first parsing is structured and schema-stable — the `ReportData`/`ReportDataDictionary`/`Time` triplet is documented and consistent across EnergyPlus minor versions, and `sqlite3` is stdlib (zero new dependencies). One bulk query per building beats per-variable queries by an order of magnitude on connection overhead. The single-point J→kWh conversion eliminates the classic UBEM results bug — mixed-unit arithmetic between Joules (E+ energy variables), kWh (meters as parsed elsewhere), and kWh/m² (EUI) — by making the parse boundary the *only* place a Joule exists. Read-only URI mode guarantees the parser can never corrupt a Stage-4 artifact (invariant **I6** — upstream intermediates are immutable). **Rejected:** (a) CSV-primary parsing (spec lists it as equal) — regex on readVars headers is fragile across variable-name changes and silently mis-parses when zone names contain colons; demoted to flagged fallback; (b) `eplusout.eso` direct parsing — purged by Step 4's retention policy, and ESO is the least documented format; (c) pandas `read_sql` per variable — N× connection/query overhead for no benefit.

### 3B — Zone-Name Resolution & Zone→Building Mapping (Module 13)

Step 3 §3B committed the zone naming contract `{osm_id}_F{floor_idx}_{label}` with `label ∈ {whole, core, perim}`. EnergyPlus upper-cases all names in its outputs, and geomeppy's `add_block` may wrap the supplied name as `Block {name} Storey {n}`. The parser therefore normalizes before matching:

```python
ZONE_RX = re.compile(
    r'^(?:BLOCK\s+)?(?P<osm_id>.+?)_F(?P<floor>\d+)_(?P<label>WHOLE|CORE|PERIM)'
    r'(?:\s+STOREY\s+\d+)?$'
)

def resolve_zone(key_value: str) -> dict | None:
    m = ZONE_RX.match(key_value.strip().upper())
    if m is None:
        return None          # site-level keys ('ENVIRONMENT') and non-zone keys land here
    return {'osm_id_uc': m['osm_id'], 'floor': int(m['floor']), 'label': m['label']}
```

The recovered `osm_id_uc` is matched case-insensitively against the manifest's `osm_id` (OSM IDs are numeric strings, so case-folding is lossless). Two hard checks per building: (i) every `Zone Ideal Loads*` key in the SQL must resolve to this building's `osm_id` — a foreign `osm_id` inside a work dir is an invariant-**I2** violation and fails the whole run loudly; (ii) the count of distinct resolved zones must equal the manifest's `num_zones` — a mismatch flags `parse_status = failed_zone_mismatch` for that building (likely geomeppy naming drift; flag, don't guess).

> **Why this approach:** Reusing the Step 3 zone-name contract as the join key means Step 5 needs **no auxiliary zone→building mapping file** — the contract *is* the mapping, and the regex is the contract's parser. Making the two integrity checks hard (one fails the run, one fails the building) is deliberate asymmetry: a foreign `osm_id` means the isolation invariant broke (systemic — everything downstream is suspect), while a zone-count mismatch is a single-building naming drift (local — quarantine and continue). **Rejected:** (a) emitting a `zone_map.json` per building at Step 3 — a second artifact that can drift from the IDF it describes; the name contract is self-describing; (b) positional zone matching (zone order in SQL) — EnergyPlus ordering is an implementation detail; (c) tolerating zone-count mismatches silently — exactly how partially-parsed buildings produce quietly low EUIs.

### 3C — Building-Level EUI Computation (Module 13)

Hourly zone values are summed to annual building totals, then divided by the building's conditioned floor area:

| EUI column | Source variable (summed over zones × 8760 h) |
|---|---|
| `heating_eui_kwh_m2` | `Zone Ideal Loads Zone Total Heating Energy` |
| `cooling_eui_kwh_m2` | `Zone Ideal Loads Zone Total Cooling Energy` |
| `lighting_eui_kwh_m2` | `Zone Lights Electric Energy` |
| `equipment_eui_kwh_m2` | `Zone Electric Equipment Electric Energy` |
| `total_eui_kwh_m2` | sum of the four above |

The denominator is `floor_area_m2 = footprint_area_m2 × num_floors`, where `footprint_area_m2` is the Step-1 **observed** footprint area and `num_floors` is computed by importing and calling **the same `derive_num_floors()` function** Step 3 used at IDF build time (`openubem.geometry.footprint.derive_num_floors` — levels → height ÷ 3.5 → 1):

```python
floor_area_m2 = row['footprint_area_m2'] * derive_num_floors(row)   # same function, not re-implemented
heating_eui   = annual_heating_kwh / floor_area_m2
```

Because Step 3's IdealAir HVAC reports *thermodynamic loads* (perfect-efficiency heating/cooling), `heating_eui_kwh_m2` and `cooling_eui_kwh_m2` are **load-referenced**, not fuel-referenced — they answer "how much heating/cooling did the building need", not "how much gas/electricity did it buy". This is stated here once and inherited by §3E's GWP convention.

> **Why this approach:** Importing `derive_num_floors` rather than re-implementing the levels/height/default cascade guarantees the EUI denominator describes exactly the geometry that was simulated — duplicate logic is how numerator and denominator drift apart silently after a refactor. Using the Step-1 *observed* footprint area (not the simplified/hull/bbox polygon's area) keeps EUI referenced to real-world floor area, which is what CBECS comparability and retrofit screening need; buildings where simplification inflated the simulated polygon (hull/bbox tiers) already carry `idf_hull_simplification` / `idf_bbox_simplification` flags, so a sensitivity filter can exclude them in one line. **Rejected:** (a) simulated-polygon area as denominator — makes EUI reference a fictional building and breaks CBECS comparability; (b) re-deriving floors from `height_m` locally — logic drift risk; (c) EnergyPlus's own conditioned-area from the ABUPS table — circular (derived from the simplified polygon) and unavailable on CSV-fallback rows.

### 3D — IOD Computation (Module 13)

Indoor Overheating Degree per the ASHRAE 55 adaptive-comfort formulation fixed in `inputs/aim/OpenUBEM_Technical_Pipeline.md` §8 Module 13:

```
Tn(m)   = 0.31 × Tave(m) + 17.8        # Tave(m): monthly mean outdoor dry-bulb, month m
Tcomf(m)= Tn(m) + 2.5                   # upper 90%-acceptability band
IOD     = mean over occupied summer hours of  max(OT(h) − Tcomf(month(h)), 0)
```

Operational definitions (all from the same SQL — never from the EPW directly):

| Term | Definition | Source |
|---|---|---|
| `Tave(m)` | monthly mean of `Site Outdoor Air Drybulb Temperature` (Hourly) | SQL site variable — exactly the weather the simulation saw |
| `OT(h)` | `Zone Operative Temperature` per zone, hour h | SQL zone variable |
| occupied hour | `Zone People Occupant Count > 0` for that zone-hour | SQL zone variable |
| summer | `config.IOD_SUMMER_MONTHS` = June 1 – September 30 (`ASSUMPTION_DESIGN_DEFAULT` — see OQ-4) | config |
| building IOD | occupant-count-weighted mean of per-zone IOD | aggregation rule |

Buildings with zero occupied summer hours (e.g. an unoccupied warehouse schedule) emit `iod = NaN` plus token `IOD_NO_OCCUPIED_HOURS` rather than a misleading 0.0 — an IOD of zero is a claim ("no overheating"), not an absence of data.

> **Why this approach:** Reading outdoor temperature from the SQL rather than re-parsing the EPW guarantees IOD references *exactly* the weather series the simulation consumed (an EPW re-parse can disagree on leap-day handling and time-zone conventions). Occupant-count weighting makes building IOD answer the policy question — *person-experienced* overheating — rather than averaging empty cores with occupied perimeters equally. The Jun–Sep window is a defensible continental-US default but is wrong at the climate-zone extremes (1A Miami's cooling season is longer; 7/8 shorter), hence the explicit `ASSUMPTION_DESIGN_DEFAULT` tag and OQ-4. **Rejected:** (a) EPW-derived Tave (spec sketch passes `epw_path`) — duplicate weather source that can drift from the simulated series; (b) unweighted zone mean — dilutes occupied-zone overheating with empty zones; (c) fixed 26 °C static threshold — discards the adaptive-comfort basis the Technical Pipeline §8 formula commits to; (d) IOD = 0.0 for never-occupied buildings — encodes "no data" as the strongest possible claim.

### 3E — GWP Computation (Module 15: `openubem/results/carbon.py`)

Five GWP columns, matching the full-system DESIGN's results schema (which refines the spec's three-bucket form into per-end-use attribution — confirmed decision, design_state row 39):

```python
# Module 15: openubem/results/carbon.py
F_GAS = config.GWP_NATURAL_GAS_KGCO2_KWH        # 0.181 kg CO2e/kWh — Iseri et al. (2025)

def compute_gwp(eui: dict, state: str, egrid: dict) -> dict:
    f_elec = egrid[state]['factor_kgco2_kwh']    # eGRID 2022 subregion via state
    return {
        'gwp_heating_kgco2_m2':   eui['heating_eui_kwh_m2']   * F_GAS,    # heating fuel: natural gas
        'gwp_cooling_kgco2_m2':   eui['cooling_eui_kwh_m2']   * f_elec,   # cooling: electric
        'gwp_lighting_kgco2_m2':  eui['lighting_eui_kwh_m2']  * f_elec,
        'gwp_equipment_kgco2_m2': eui['equipment_eui_kwh_m2'] * f_elec,
        'gwp_total_kgco2_m2':     <sum of the four>,
    }
```

**Convention statement (binding, Phase 1):** factors are applied directly to the IdealAir *loads* (§3C) — no boiler efficiency divides the heating load, no cooling COP divides the cooling load. This is the `load_referenced_v1` convention, recorded in the export metadata (`config.GWP_CONVENTION`). Its directional consequences are known and documented: against a fuel-referenced accounting, it *understates* heating GWP (real gas use = load ÷ η, η ≈ 0.8) and *overstates* cooling GWP (real electricity = load ÷ COP, COP ≈ 3). The numbers are therefore internally consistent comparative metrics across the building stock — valid for ranking, mapping, and scenario deltas — and are **not** absolute utility-bill carbon accounting. Whether Phase 1.5 moves to nominal conversion factors (and which η/COP) is OQ-2; the convention tag exists precisely so every exported file self-declares which regime produced it. The `state` key for the eGRID lookup is resolved per §2's note: read a `state` column if the enriched GDF carries one (future Module 02), else one spatial join of the neighbourhood centroid against a bundled US-states layer, applied uniformly (single state per run; cross-border neighbourhoods log a WARNING) — interim rule, OQ-3.

> **Why this approach:** Per-end-use attribution (four factors, not one blended factor) is the confirmed system-level refinement (design_state row 39): heating carbon rides the gas factor while cooling/lighting/equipment ride the regional electricity factor, so the *spatial variation* of GWP across eGRID subregions and the *end-use composition* per archetype both survive into the output — a single blended factor destroys both. Shipping `load_referenced_v1` now, explicitly tagged, beats blocking Phase 1 on an efficiency-convention decision: the tag makes the limitation auditable instead of silent, and every consumer of the file can see which convention it carries. **Rejected:** (a) silently applying η = 0.8 / COP = 3.0 — fabricates precision (no per-archetype equipment data exists in Phase 1) and contradicts the IdealAir decision's whole point of not modelling plant; (b) blended single emission factor — destroys end-use and regional signal; (c) emitting GWP only for heating + total (spec's three-bucket sketch) — already superseded at system level by row 39.

### 3F — Spatial Join & Neighbourhood Aggregation (Module 14: `openubem/results/aggregator.py`)

The per-building metric rows are **left-joined** onto the 57-column enriched GeoDataFrame on `osm_id`, appending exactly **13 columns** (matching the full-system DESIGN's results schema): the 5 EUI columns, the 5 GWP columns, `iod`, `simulation_status` (the Step 4 closed token, extended with `failed_parse` / `failed_zone_mismatch` / `success_csv_fallback` from §3A/§3B), and `error_summary`. The 57 upstream columns pass through byte-identical (Step 2's schema-extension discipline). Result: a 70-column GeoDataFrame with one row per Step-1 building — including every failed and never-attempted building, carrying NaN metrics and their status token.

Neighbourhood-level aggregates are computed and emitted as a compact JSON sidecar (`05_neighbourhood_summary.json`):

| Aggregate | Rule |
|---|---|
| `neighbourhood_total_eui_kwh_m2` (and per end use) | Σ(annual kWh) ÷ Σ(floor_area_m2) over success rows — i.e. **floor-area-weighted** mean EUI, *not* the unweighted mean of per-building EUIs |
| `neighbourhood_gwp_total_kgco2` | Σ(gwp_total_kgco2_m2 × floor_area_m2) — absolute tonnes, not intensity |
| `mean_iod_c`, `p95_iod_c` | over success rows with non-NaN IOD |
| `n_buildings_by_status` | counts per status token (the honesty header for every map made from this file) |
| `pct_floor_area_simulated` | Σ floor area of success rows ÷ Σ floor area of all rows |

> **Why this approach:** Flag-don't-drop through the final join is the policy that has held since Step 1 (design_state row 50): a building that failed to simulate is *information* (where, which archetype, which failure mode), and dropping it would silently bias every aggregate toward the buildings that happened to succeed. Floor-area weighting for neighbourhood EUI is not a taste choice — intensive metrics aggregate as (Σ extensive) / (Σ denominator); the unweighted mean of EUIs over-represents small buildings and is a known UBEM reporting error. `pct_floor_area_simulated` is published precisely so no neighbourhood number can masquerade as complete when 30% of the floor area failed upstream. **Rejected:** (a) inner join / success-only output — silent survivorship bias in every downstream map; (b) unweighted mean neighbourhood EUI — small-building over-representation; (c) appending Step 4 bookkeeping columns (`wall_clock_s`, `n_severe`, …) to the results GDF — observability data lives in the manifest; the deliverable carries results, status, and nothing else.

### 3G — Export & Visualization (Module 14 + Module 16: `openubem/results/visualization.py`)

Three export formats, one canonical CRS policy:

| File | CRS | Notes |
|---|---|---|
| `05_results.gpkg` (layer `buildings`) | UTM (the Step-1 `crs_utm`) | **Canonical artifact** — full 70-column schema, metric CRS preserved for any further spatial analysis. Sidecar `05_results.schema.json` (70 entries, mirroring Step 1/2 schema-documentation practice). |
| `05_results.geojson` | EPSG:4326 (reprojected at export only) | Web-map interchange (GeoJSON spec mandates WGS84). Nullable-Int columns lift to float per the documented Step-1 GeoJSON caveat. |
| `05_results.csv` | — (geometry dropped; `centroid_lon`, `centroid_lat` columns added) | Spreadsheet/ML-ingest convenience. |
| `05_neighbourhood_summary.json` | — | §3F aggregates + run metadata: `gwp_convention`, `ep_version`, eGRID subregion, generation timestamps. |

Module 16 renders three **observability-only, non-binding** matplotlib figures into `<output_dir>/figures/`: a `total_eui_kwh_m2` choropleth on the building footprints (failed buildings hatched grey, never invisible), per-archetype EUI violin plots, and a per-end-use GWP stacked bar by archetype. No figure is a pipeline contract; consumers depend only on the three export files and the summary JSON.

> **Why this approach:** GPKG-as-canonical preserves the metric UTM CRS the whole pipeline has worked in since Step 1 (reprojecting the canonical artifact to WGS84 would make every later area/distance computation subtly wrong); GeoJSON is generated *only* at the export boundary because its spec hard-requires WGS84. Declaring the figures non-binding keeps Module 16 free to improve without versioning consequences — the lesson of Step 2's "classification log marked observability-only" critic fix. Hatching failed buildings grey in the choropleth (rather than omitting them) is the visual analogue of flag-don't-drop. **Rejected:** (a) GeoJSON as canonical — WGS84 degrees break metric analysis and the file is ~3× the GPKG size; (b) shapefile export — 10-char field-name truncation destroys the 70-column schema; (c) interactive HTML maps (folium/kepler) as a Phase-1 deliverable — heavy dependencies for an observability artifact; Phase-2 candidate.

---

## 4. Outputs

| Artifact | Filename | Format | Shape | Consumed by |
|---|---|---|---|---|
| Results GeoDataFrame (canonical) | `<output_dir>/05_results.gpkg` (layer `buildings`) + `05_results.schema.json` | GeoPackage (UTM) + JSON schema sidecar | (N_input, 70) — 57 upstream byte-identical + 13 appended | Final deliverable: humans, GIS, umbrella-project ML stages (surrogate labels), §5 validation harness. |
| Web interchange | `<output_dir>/05_results.geojson` | GeoJSON (EPSG:4326) | (N_input, 70) | Web maps, kepler.gl, quick sharing. |
| Tabular | `<output_dir>/05_results.csv` | CSV (no geometry; centroid lon/lat) | (N_input, 71) | Spreadsheets, pandas/ML ingest. |
| Neighbourhood summary | `<output_dir>/05_neighbourhood_summary.json` | JSON | ~12 keys | Dashboards; the headline numbers + completeness honesty header (`pct_floor_area_simulated`). |
| Figures | `<output_dir>/figures/{eui_choropleth.png, eui_violin_by_archetype.png, gwp_stacked_by_archetype.png}` | PNG | 3 files | Observability only — explicitly non-binding (§3G). |

---

## 5. Validation

### 5.1 Metrics and acceptance thresholds

| Metric | Threshold | Rationale (cite source) |
|---|---|---|
| `pct_parse_success` | ≥ 99% of `status ∈ {success, success_cached}` rows parse from SQL without fallback or failure | The Step 4→5 interface is machine-generated; parse failures indicate contract drift, not data noise |
| ABUPS cross-check | per-building annual electricity (Σ lighting + equipment hourly kWh) matches the `eplustbl.htm`/`TabularDataWithStrings` ABUPS end-use total within ±0.5% | Independent path through EnergyPlus's own annual tabulation validates the §3A J→kWh conversion and the hourly summation |
| Meter closure | Σ(hourly `Zone Lights` + `Zone Electric Equipment`) = `Electricity:Facility` RunPeriod meter within ±1% | Internal energy-balance consistency between Output:Variable and Output:Meter paths |
| Gas-meter zero check | `NaturalGas:Facility` RunPeriod meter = 0 for 100% of buildings | IdealAir IDFs contain no gas equipment; any non-zero value means template contamination at Step 3 |
| Zone-count integrity | resolved zones = manifest `num_zones` for 100% of parsed buildings | §3B contract check; mismatch ⇒ `failed_zone_mismatch`, never silent partial parse |
| EUI plausibility envelope | `total_eui_kwh_m2` ∈ [25, 1000] for ≥ 99% of success rows (flag outliers, don't drop) | Order-of-magnitude sanity bounds spanning efficient residential → DataCenter; outliers outside this band are almost always denominator bugs |
| CV(RMSE) building-level | < 30% vs CBECS 2018 New England commercial EUI distributions (Boston fixture) | ASHRAE Guideline 14 anchored; uncalibrated-model threshold confirmed at system level (design_state row 36) |
| NMBE neighbourhood-level | ±10% | ASHRAE Guideline 14 mean-bias threshold (design_state row 36) |
| R² archetype-level | > 0.6 (predicted vs CBECS archetype-mean EUI) | system-level validation contract (design_state row 36) |
| KS test on EUI distribution | D < 0.10 vs CBECS 2018 New England distribution | distribution-shape gate beyond moment matching (design_state row 36) |
| IOD spot check | parser IOD = hand-computed IOD on the synthetic fixture's golden SQL, exact | the formula has three chained definitions (Tn, Tcomf, occupied-hour mask) — unit-tested end-to-end |

### 5.2 Test data and holdout strategy

- **Golden-SQL unit fixtures** — `tests/fixtures/golden_sql/` holds three frozen `eplusout.sql` files produced once by Step 4 on the synthetic 10-building fixture and committed: (i) a single-zone building, (ii) a 3-floor `one_zone_per_floor` residential, (iii) a `perimeter_core` commercial. Expected EUI/IOD/GWP values are hand-computed from the SQL and asserted exactly — no EnergyPlus binary needed in CI. Adversarial unit cases: SQL with a foreign-`osm_id` zone (must abort the run), SQL with one zone missing (must flag `failed_zone_mismatch`), missing SQL with present CSV (must flag `RESULTS_CSV_FALLBACK`), building with zero occupied summer hours (must emit `IOD_NO_OCCUPIED_HOURS`, not 0.0).
- **Boston Downtown 500 m integration fixture** — full Steps 1→5 chain on the ~400-building cached fixture; computes every §5.1 gate including the CBECS comparison. Requires EnergyPlus 23.1 + the CBECS 2018 New England reference table (§7 OQ-1).
- Holdout regime: unchanged from Steps 3–4 — Boston is fully held out from any Module 06b imputation training. **CBECS 2018 is used exclusively as the evaluation reference and never enters any upstream parameter** (Module 04/05 values come from ASHRAE/IECC/DOE-Prototype sources, not CBECS), so the §5.1 comparison is leak-free by construction.

### 5.3 True Future Test (only if a forecast or generalization claim is made)

Step 5 itself is a deterministic transformation (no trained model, no temporal extrapolation). However, Step 5 is where the umbrella pipeline's *generalization claim* is finally adjudicated: that OpenUBEM's standards-derived, imputation-completed building models produce EUI distributions statistically consistent with the measured US stock (CBECS 2018) on a neighbourhood never used to fit anything. The leakage defense has two independent legs: (i) spatial holdout — Boston enters no training set anywhere in Stages 1–4 (established in the Step 3 DESIGN §5.2 and inherited); (ii) reference independence — the CBECS evaluation data shares no provenance with the ASHRAE 90.1 / IECC / DOE-Prototype parameter sources, so the model cannot have memorized its own test (§5.2). A failed gate therefore indicts the pipeline's physics/enrichment, not the evaluation design.

---

## 6. Compute

| Resource | Estimate | Source of estimate |
|---|---|---|
| GPU hours (Calcul Québec / Concordia HPC) | 0 | pandas + sqlite3 + shapely; pure CPU |
| CPU | 1 core, sequential per-building loop (embarrassingly parallel-safe but unnecessary at fixture scale) | parse is I/O-bound; joblib fan-out is a city-scale option, not a Phase-1 need |
| Per-building parse time | ~1–3 s (read 5–20 MB SQL, one bulk query, ~0.5 M rows for a 5-zone building) | sqlite3 bulk-read throughput; to be confirmed on Boston fixture |
| Wall-clock target (Boston 500 m, ~400 buildings) | < 15 min single-core end-to-end (parse → join → export → figures) | 400 × ~2 s ≈ 13 min |
| Peak memory | < 4 GB | one building's hourly long-frame at a time (~50 MB) + the accumulating (N × 13) metrics frame + one 70-col GDF at export |
| Storage (final artifacts, Boston) | ~50–150 MB | GPKG ~30–80 MB + GeoJSON ~2–3× GPKG ÷ 70 cols + CSV + JSON + 3 PNGs |
| Storage (5 M-building city) | ~0.5–1.5 TB final artifacts | linear extrapolation; dwarfed by Step 4's retained work dirs |

The dominant cost driver is SQL read volume (rows = variables × zones × 8760), which scales with Step 3's zone-count decisions, not with anything Step 5 controls. The budget changes ≥2× only if the per-building variable list grows (a Step 3 §3I change) or if city-scale runs force a parallel parse fan-out (mechanically trivial — the per-building parse is a pure function — but adds the joblib plumbing Phase 1 doesn't need).

---

## 7. Open Questions

- [ ] **OQ-1** — The CBECS 2018 New England EUI reference (building-level distributions and archetype means used by four §5.1 gates) is not yet in `inputs/` as an extracted, citable table. Extract from CBECS 2018 public microdata, commit to `inputs/reports/`, and freeze the extraction script. *(blocks §5.1 CV(RMSE)/NMBE/R²/KS gates; does not block §3 implementation or unit tests)*
- [ ] **OQ-2** — GWP convention end-state: confirm against Iseri et al. (2025) §methods whether nominal conversion efficiencies (η_heating ≈ 0.8, COP_cooling ≈ 3) were applied to ideal loads, and decide whether Phase 1.5 moves from `load_referenced_v1` to a fuel-referenced `v2` (and with which per-archetype η/COP source). The convention tag in every export makes the migration auditable. *(blocks §3E refinement; Phase 1 ships `load_referenced_v1` as designed)*
- [ ] **OQ-3** — Canonical owner of the `state` column for the eGRID lookup. Natural home: Module 02's county-level climate-zone spatial join (county → state is free). Interim: centroid join against a bundled US-states layer (§3E). Resolve when Step 2.5 / Module 02 is designed. *(blocks §3E integration path; interim rule unblocks Phase 1)*
- [ ] **OQ-4** — Climate-zone-aware IOD summer window. Jun 1–Sep 30 is tagged `ASSUMPTION_DESIGN_DEFAULT`; zones 1A–2B need a longer window, 7–8 shorter. Candidate rule: cooling-season months derived per climate zone from the EPW's monthly means. *(blocks §3D calibration; default unblocks Phase 1)*
- [ ] **OQ-5** — Module 02 (`climate_zone` + `epw_path` + prospectively `state`) remains undesigned — the same blocker chain as Step 3 OQ-7 / Step 4 OQ-5; Step 5 integration testing requires it; golden-SQL unit tests do not. *(blocks full integration test)*
- [ ] **OQ-6** — Confirm with the downstream eSim execution project which columns the surrogate-training consumer needs beyond the 13 appended metrics (e.g. per-end-use *absolute* kWh in addition to intensities) before the 70-column schema is frozen by first production use. *(blocks §4 schema freeze; one-line additions are cheap before freeze, breaking after)*

---

## 8. References

**`inputs/aim/`** — project charter and pipeline blueprint
- `inputs/aim/OpenUBEM_Technical_Pipeline.md` — §8 (Stage 5 specification: Modules 13–15 decomposition, `parse_building_results`/`compute_eui`/`compute_iod`/`compute_gwp` signatures, IOD formula, eGRID + 0.181 kg CO₂e/kWh factors), §12 (provenance vocabulary preserved through the results join).
- `inputs/aim/OpenUBEM_Aim_Document.md` — §3.6 (operational-GWP-only scope; eGRID stack), validation regime (CBECS 2018 + ASHRAE Guideline 14 thresholds), final-deliverable framing (EUI/GWP/IOD per building).

**`inputs/papers/`** — technical references for libraries and methods
- `inputs/papers/1-s2-0-s0378778825003500-main-pdf.md` — Iseri et al. (2025), *Energy & Buildings* 337, 115620: GWP factor conventions (natural gas 0.181 kg CO₂e/kWh), per-building simulation → urban-scale aggregation methodology; anchors §3E.
- `inputs/papers/pdf-a-method-for-integrating-an-ubem-with-gis-for-spatiotemporal-visualization-and-analysis-research.md` — UBEM↔GIS results integration patterns; anchors §3F join-back-to-GeoDataFrame design and §3G export formats.
- `inputs/papers/validating-gis-ubem-a-residential-open-data-driven-urban-building-energy-model.md` — UBEM validation methodology against measured stock data; anchors §5.1 gate structure and §5.3 leakage reasoning.
- `inputs/papers/urban-building-energy-modeling-ubem-a-systematic-review-of-challenges-and-opportunities-university-o.md` — survey of UBEM validation/reporting pitfalls (survivorship bias, aggregation errors); anchors §3F flag-don't-drop and floor-area weighting.
- `inputs/papers/welcome-to-eppy-s-documentation-eppy-0-5-69-documentation.md` — EnergyPlus output-file ecosystem context.

**`inputs/reports/`** — UBEM methodology context
- `inputs/reports/Open Source Urban Building Energy Modeling - General.md` — how comparable tools (CEA, UMI, CityBES) report results; supports the GPKG/GeoJSON/CSV trio and per-building granularity as differentiators.
- `inputs/reports/Open Source Urban Building Energy Modeling-Architecture.md` — results-pipeline architecture patterns (SQL parsing, calibration hooks); anchors §3A SQL-first choice.

**Prior-step DESIGN docs (binding upstream contracts)**
- `outputs/2026-06-09_step-4-run-energyplus-in-parallel-for-every-generated-idf-via-joblib-loky-in-isol/DESIGN_step-4-...md` — `04_simulation_manifest.parquet` schema (§3F), retained-file set, status vocabulary Step 5 extends.
- `outputs/2026-05-07_step-3-generate-one-energyplus-idf-per-building-from-the-archetype-enriched-geod/DESIGN_step-3-...md` — zone-name contract (§3B), Output:Variable list (§3I) that §3A's query consumes, IdealAir load semantics (§3H) that drive the §3E convention.

**External anchors (cited via inputs only — no fabricated DOIs)**
- ASHRAE Guideline 14 — CV(RMSE) < 30% / NMBE ±10% calibration thresholds (via aim docs; design_state row 36).
- ASHRAE 55 — adaptive comfort model underlying the IOD formula (via Technical Pipeline §8).
- US EPA eGRID 2022 — subregion electricity emission factors (bundled `egrid_2022.json`; via aim docs).
- US EIA CBECS 2018 — evaluation reference for §5.1 (extraction pending, OQ-1).

---

## 9. Key Decisions Summary

| # | Decision | Sub-stage | Rationale (one line) | Alternatives rejected |
|---|---|---|---|---|
| 1 | SQL-first parsing via stdlib `sqlite3` (read-only URI, one bulk query); `eplusout.csv` demoted to flagged fallback (`RESULTS_CSV_FALLBACK`) | 3A | Structured, schema-stable, zero new dependencies; the spec's CSV-equal-citizen stance invites fragile regex parsing | CSV-primary (header-regex fragility); ESO parsing (purged + least documented); per-variable queries (N× overhead). |
| 2 | Single J→kWh conversion at the parse boundary — a Joule never exists past §3A | 3A | Eliminates the classic mixed-unit UBEM bug by construction; every downstream number is kWh | Convert-at-use (guarantees an eventual mixed-unit sum); reporting in GJ (breaks kWh/m² convention of every reference dataset). |
| 3 | Zone→building mapping by parsing the Step 3 zone-name contract (`{osm_id}_F{n}_{label}`, geomeppy/E+ normalization regex); foreign `osm_id` aborts the run, zone-count mismatch quarantines the building | 3B | The naming contract *is* the mapping — no auxiliary file to drift; asymmetric severity matches systemic vs local failure | Per-building `zone_map.json` (drift risk); positional matching (implementation-detail dependency); silent tolerance (quietly low EUIs). |
| 4 | EUI denominator = Step-1 observed `footprint_area_m2` × `derive_num_floors()` **imported from Step 3's module**, never re-implemented | 3C | Denominator describes exactly the simulated geometry (no logic drift) while staying referenced to real-world floor area for CBECS comparability | Simulated-polygon area (fictional building); local re-derivation (drift); ABUPS conditioned area (circular + absent on CSV-fallback rows). |
| 5 | IOD from SQL-internal series only (site drybulb + operative temp + occupant count); occupant-weighted; `NaN` + `IOD_NO_OCCUPIED_HOURS` when never occupied | 3D | References exactly the weather the simulation saw; measures person-experienced overheating; never encodes "no data" as "no overheating" | EPW re-parse (dual weather source); unweighted zone mean (empty-zone dilution); static 26 °C threshold (abandons adaptive basis); 0.0 for unoccupied. |
| 6 | Five-column per-end-use GWP under an explicit, export-tagged `load_referenced_v1` convention (gas 0.181 on heating; eGRID 2022 electricity on cooling/lighting/equipment; no η/COP) | 3E | Preserves regional + end-use carbon signal (design_state row 39); tagged convention makes the known load-vs-fuel limitation auditable instead of silent | Silent η = 0.8 / COP = 3 (fabricated precision); blended single factor (destroys signal); spec's three-bucket form (superseded by row 39). |
| 7 | Left join appending exactly 13 columns onto the byte-identical 57-column GDF; flag-don't-drop through the deliverable; floor-area-weighted neighbourhood EUI + `pct_floor_area_simulated` honesty metric | 3F | Survivorship bias is the canonical UBEM reporting error — failed buildings stay visible and aggregates declare their own completeness | Success-only inner join; unweighted mean EUI; bookkeeping columns in the deliverable (manifest's job). |
| 8 | GPKG (UTM) canonical + GeoJSON (EPSG:4326, export-boundary reprojection only) + CSV; figures explicitly observability-only / non-binding | 3G | Metric CRS survives for analysis; web interchange honours the GeoJSON WGS84 mandate; non-binding figures can improve without versioning consequences | GeoJSON-canonical (degrees break metrics); shapefile (10-char field truncation); interactive-map deliverable (dependency weight, Phase 2). |

---

## 10. Progress Log *(populated by downstream `/run` reporter — leave empty here)*

<!-- The downstream execution project's reporter agent appends `### Session: <date> | Loop: <N>` blocks under this header after each /run cycle. NEITHER the architect NOR the documenter writes here. -->

---

## 11. Revision Log *(populated by DOCUMENTER on /design re-runs only — EMPTY on first creation)*

<!-- Append-only. DOCUMENTER inserts a new block on each /design re-run.

On MODE=new this section MUST contain only this comment block — no `### Session:` block. The first revision block is written on the first MODE=update run.

### Session: <YYYY-MM-DD> | Pass: <final-pass>
**Trigger:** <one-line: new evidence, change request, retired decision>
**Inputs added since last session:** <bullets — filenames>
**Changes:**
- §<N>: <delta>
**New Decisions:** <bullets, also propagated to .claude/design_state.md>
**Retired Decisions:** <bullets — moved to design_state.md ## Retired Decisions, with reason>
**OVERVIEW regenerated:** yes
**GRAPHICAL_ABSTRACT regenerated:** yes | no — no material architecture change

-->

### Session: 2026-06-09 | Pass: n/a (direct authoring cross-reference)

**Trigger:** Steps 2.1 and 2.2 designed (direct-authoring sessions, 2026-06-09) — the Module-02 blocker and the `state`-owner question named in this document are now closed on the design side.

**Changes:** none to §1–§9 (frozen). Cross-reference notes only:
- **OQ-3 RESOLVED** — Step 2.1 §3E carries `state` (+ `county_geoid`) per building in the **`02a_climate_epw.parquet` sidecar** (N × 9), sourced from the same matched county polygon as `climate_zone` (no second spatial join to drift). For integrated runs, the §3E eGRID state→subregion lookup joins this sidecar on `osm_id`; the interim centroid join against a bundled US-states layer described in §3E remains valid only for standalone/golden-SQL runs that predate Step 2.1 artifacts. The flowing 57/70-column contracts are unchanged — `state` never becomes a flowing column.
- **OQ-5 RESOLVED** — Module 02 designed as **Step 2.1**; Modules 04/05/06/06b designed as **Step 2.2** (`outputs/2026-06-09_step-2-2-enrich-every-classified-building-with-constructions-loads-schedules-and/`). Step 5 integration testing is no longer design-blocked; the full column-accretion chain 23 → 26 → 29 → 57 → 70 is specified end-to-end.

**Decisions retired:** none (the interim centroid join was an in-section interim rule, not a design_state row).
**OVERVIEW regenerated:** no — §1–§9 unchanged.
**GRAPHICAL_ABSTRACT regenerated:** no — no material architecture change.
