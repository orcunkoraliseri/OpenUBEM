# Step 2.1 — Classified GeoDataFrame → ASHRAE Climate Zone, US State, and EPW Weather File per Building
### OpenUBEM Stage 1 / Module 02: `openubem/acquisition/{climate_zone,epw_manager}.py` — append `climate_zone` + `epw_path` + `provenance_climate_zone` (26 → 29 columns), resolve and validate one cached EPW weather file per run, and emit the `02a_climate_epw.parquet` sidecar that carries `state` to Stage 5's eGRID lookup

> **Slug:** `step-2-1-assign-ashrae-climate-zone-us-state-and-epw-weather-file-to-every-build` &nbsp;•&nbsp; **First created:** `2026-06-09` &nbsp;•&nbsp; **Latest revision:** `2026-06-09`
>
> Sections 1–9 are **append-once, edit-never** after first APPROVED verdict. Section 10 (Progress Log) is owned by the downstream `/run` reporter. All `/design` re-run changes are recorded under **Section 11 — Revision Log**.
>
> **Scope rule.** This document covers exactly **one** step of the umbrella pipeline — Step 2.1 (Module 02: climate zone detection + EPW management). The step's *internal* sub-stages (3A–3E) live under §3 Pipeline. Step 2 (archetype classification) and Step 2.2 (construction/loads/schedules enrichment) are covered in their own per-step DESIGN docs.

---

## 1. Aim

Step 2.1 takes the 26-column classified GeoDataFrame produced by Step 2 (`02_buildings_classified.gpkg`) and answers, for every building, the two questions the rest of the pipeline silently assumes are answered: *which ASHRAE climate zone does this building sit in* (the lookup key for every Module 04 construction table) and *which EPW weather file will EnergyPlus consume* (the file Step 4 binds at launch with `-w`). It appends exactly three columns — `climate_zone`, `epw_path`, `provenance_climate_zone` — bringing the flowing schema from 26 to 29 columns, and emits a per-building sidecar (`02a_climate_epw.parquet`) that additionally carries the 2-letter US `state` and county FIPS needed by Stage 5's eGRID carbon lookup (resolving Step 5 OQ-3) without widening the frozen 57-column Step 3 contract. This module is the recurring blocker named in Step 3 OQ-7, Step 4 OQ-5, and Step 5 OQ-5: until it exists, no end-to-end integration test can run. The module decomposition follows `inputs/aim/OpenUBEM_Technical_Pipeline.md` §4 (Module 02: `acquisition/climate_zone.py` + `epw_manager.py`); downstream consumers are Step 2.2 (Module 04 keys its envelope lookup on `climate_zone`), Step 3 (carries `epw_path` through its manifest join), Step 4 (binds the EPW), and Step 5 (joins `state` from the sidecar).

**Pipeline-position note (documented refinement).** The Technical Pipeline places Module 02 in Stage 1 (acquisition) and resolves a single climate zone per run inside `run_ubem()` (§9). The frozen Step 2 contract, however, commits to a byte-identical 23-column pass-through plus exactly three appended columns (design_state row 71) — so in the *column-accretion order* Module 02 must execute **after** Step 2: Step 1 (23) → Step 2 (26) → **Step 2.1 (29)** → Step 2.2 (57). Nothing in Module 02 depends on `archetype_id`, so the module remains logically Stage-1; only its position in the artifact chain is fixed by the frozen contracts.

---

## 2. Inputs

| Artifact | Source | Dtype | Shape | Notes |
|---|---|---|---|---|
| `02_buildings_classified.gpkg` (layer `buildings`) | Step 2 / Module 03 | GeoDataFrame | (N, 26) | UTM-projected geometry; 23 Step-1 columns byte-identical + `archetype_id`, `archetype_confidence`, `archetype_source` (design_state rows 54, 71). Step 2.1 reads geometry and `osm_id` only; all 26 columns pass through untouched. |
| `data/climate_zones/ashrae_climate_zones.gpkg` | bundled in wheel | GeoPackage (EPSG:4326) | ~3,100 US county polygons | DOE/PNNL county→zone mapping per Technical Pipeline §4 Module 02. Required attributes per polygon: `county_geoid` (5-digit FIPS), `state_abbrev` (2-letter USPS), `climate_zone` (16-token closed vocabulary, §3B). Edition pinning + checksum is OQ-1. |
| `data/epw_stations.csv` | bundled in wheel | CSV | one row per EPW station | Station index per Technical Pipeline §4 (`data/epw_stations.csv`): `station_id` (WMO index), `name`, `state`, `lat`, `lon`, `url`, `tmy_edition`. One-time extraction from the climate.onebuilding.org catalog is OQ-2. |
| EPW mirrors (network) | climate.onebuilding.org (primary), energyplus.net/weather (fallback) | HTTPS | ~1.5–2 MB per file | Per Technical Pipeline §4 resolution order. Only touched on cache miss with `offline=False`. |
| `config.py` | package config | Python module | — | Exposes `EPW_CACHE_DIR` (default `~/.openubem/epw/`), `EPW_MAX_STATION_KM` (default 300, `ASSUMPTION_DESIGN_DEFAULT`, OQ-4), `EPW_PRIMARY_MIRROR`, `EPW_FALLBACK_MIRROR`, `OFFLINE` (default False). |

---

## 3. Pipeline

Step 2.1 is two near-independent resolutions — a *per-building* spatial join (climate zone + state) and a *per-run* weather-file resolution — joined by a single column-append at the end. Sub-stages 3A–3B run entirely offline against the bundled GeoPackage; 3C–3D touch the network only on a cold cache; 3E emits the artifacts.

### 3A — Input Gate & Representative-Point Extraction (Module 02: `openubem/acquisition/climate_zone.py`)

The 26-column input is schema-validated (column names, dtypes, `archetype_id` within the closed 30-element vocabulary) and a join geometry is derived per building:

```python
# Module 02: openubem/acquisition/climate_zone.py
def _join_points(gdf: gpd.GeoDataFrame) -> gpd.GeoSeries:
    # representative_point(), NOT centroid: guaranteed inside the polygon,
    # so a concave footprint near a county line cannot project its join
    # point into the neighbouring county (or into water).
    pts_utm = gdf.geometry.representative_point()
    return pts_utm.to_crs(epsg=4326)   # one vectorized reprojection
```

The reprojection happens once for the whole frame (UTM → EPSG:4326, the CRS of the bundled county layer); no per-row pyproj calls.

> **Why this approach:** `representative_point()` is the geopandas-documented way to get a point guaranteed inside the polygon (`inputs/papers/geopandas.md`); a centroid of an L- or U-shaped footprint can fall outside the building and — exactly at administrative borders, where it matters — inside the wrong county. **Rejected:** (a) polygon-centroid join — wrong-county risk for concave footprints at borders; (b) joining the full polygons instead of points — a footprint straddling a county line would double-match and the dedup rule would be arbitrary; points make the assignment single-valued by construction.

### 3B — Per-Building ASHRAE Zone + State Spatial Join (Module 02: `climate_zone.py`)

Every building's join point is matched against the bundled county layer with a two-tier fallback:

| Tier | Operation | Provenance / method token |
|---|---|---|
| 1 | `gpd.sjoin(points, counties, predicate='within')` — vectorized point-in-polygon via the spatial index | `provenance_climate_zone = ASHRAE_STANDARD`, `climate_zone_method = county_within` |
| 2 | Unmatched points only (coastal slivers, harbor gaps, boundary-degenerate topology): `gpd.sjoin_nearest(..., max_distance=5_000)` computed in the run's UTM CRS (metres), against the counties reprojected once | `provenance_climate_zone = HEURISTIC`, `climate_zone_method = nearest_fallback` |
| — | Still unmatched after Tier 2, or zero Tier-1 matches across the entire run | **abort** with a structured error — the input is outside the bundled US coverage (wrong continent / Phase-3 territory), not a per-building data gap |

`climate_zone` is drawn from a **closed 16-token US vocabulary** `{1A, 2A, 2B, 3A, 3B, 3C, 4A, 4B, 4C, 5A, 5B, 5C, 6A, 6B, 7, 8}` (the zones occurring in US county assignments; zones 0A/0B have no US county). `state` and `county_geoid` come from the same matched county row — no second lookup, no separate states layer. If a point matches more than one county polygon (degenerate shared-boundary topology), the row with the lexically smallest `county_geoid` is kept and a structured warning is logged. If more than one distinct `climate_zone` appears in a single run, a structured `logging.warning` with payload `{"event": "multi_zone_neighbourhood", "zones": [...], "counts": [...]}` is emitted — legal, but worth surfacing because Module 04 will produce zone-heterogeneous envelopes.

> **Why this approach:** The spec's `run_ubem()` sketch resolves **one** zone for the whole neighbourhood from the union centroid (Technical Pipeline §9). Per-building joins cost essentially nothing extra (one vectorized `sjoin` over the spatial index, the same pattern as Step 1's IoU dedup pre-filter, design_state row 57) and are *correct* when a bbox crosses a county or zone boundary — silent mis-zoning of half a neighbourhood is exactly the class of bug the provenance system exists to prevent. The county join earns `ASHRAE_STANDARD` provenance because the DOE county table *is* the ASHRAE/IECC zone assignment instrument; the nearest-fallback earns `HEURISTIC` — both tokens are canonical §12 vocabulary (design_state row 62). The severity asymmetry (per-building fallback vs whole-run abort) mirrors Step 5 §3B: a local gap degrades one row traceably; a systemic mismatch fails loudly. **Rejected:** (a) spec-literal single-centroid resolution — silent wrong-zone assignment for boundary-crossing bboxes; (b) reverse-geocoding web APIs — adds a network dependency to a step that must run air-gapped (invariant I7, Step 1 mode (d)); (c) appending a quality token to `data_quality_flag` for fallback rows — Step 2.1 commits to byte-identical pass-through of all 26 upstream columns (§4), so quality detail lives in the sidecar's `climate_zone_method` instead.

### 3C — EPW Station Resolution (Module 02: `openubem/acquisition/epw_manager.py`)

One EPW station is resolved **per run**, at the representative point of the neighbourhood union, using vectorized geodesic distance against the bundled station index:

```python
# Module 02: openubem/acquisition/epw_manager.py
def resolve_station(lat: float, lon: float,
                    stations: pd.DataFrame) -> tuple[pd.Series, float]:
    geod = pyproj.Geod(ellps='WGS84')
    _, _, dist_m = geod.inv(
        np.full(len(stations), lon), np.full(len(stations), lat),
        stations['lon'].to_numpy(), stations['lat'].to_numpy())
    i = int(np.argmin(dist_m))
    return stations.iloc[i], dist_m[i] / 1_000.0   # (station row, km)
```

The chosen distance is recorded per building as `epw_distance_km` in the sidecar. If it exceeds `EPW_MAX_STATION_KM` (default 300 km, `ASSUMPTION_DESIGN_DEFAULT` — OQ-4), a structured warning `{"event": "epw_far_station", "station_id": ..., "distance_km": ...}` is logged and the run proceeds: a far station is a documented data-quality condition, not a failure.

File resolution order (Technical Pipeline §4, verbatim): **(1)** user-provided `epw_dir` — if it contains exactly one `.epw`, use it; if several, use the geodesically nearest by header location; **(2)** `EPW_CACHE_DIR` local cache hit on the station's canonical filename (e.g. `USA_MA_Boston-Logan.Intl.AP.725090_TMYx.epw`); **(3)** download from `climate.onebuilding.org`; **(4)** fallback mirror `energyplus.net/weather`. With `offline=True`, tiers 3–4 are skipped; a cold cache then **aborts the run**.

> **Why this approach:** TMY station spacing is tens of kilometres; OpenUBEM neighbourhoods are ≤ ~1 km across (Technical Pipeline §2: `radius_m` defaults of 500–1000 m). Per-building station assignment can therefore differ across a run only when the bbox straddles a Voronoi boundary between two stations describing the *same* climate — it would buy zero information and cost a spurious EUI discontinuity down the middle of the results map, plus N downloads. One station per run, with the actual distance recorded per building, keeps the decision auditable. **Rejected:** (a) per-building nearest station — spurious mid-neighbourhood weather discontinuity, N× metadata; (b) one EPW per climate zone — zones are county-scale administrative bands, not station Voronoi cells; the mapping is many-to-many; (c) skipping the distance record — the 300 km guard is exactly the kind of number Phase-1.5 calibration needs collected (mirrors Step 4's self-collecting `wall_clock_s`).

### 3D — EPW Download, Atomic Cache & Validation (Module 02: `epw_manager.py`)

Downloads are atomic and every EPW — downloaded, cached, or user-provided — passes the same validation gate before it is accepted:

| # | Check | Action on failure |
|---|---|---|
| 1 | Download lands in `<cache>/<name>.epw.tmp`; `os.replace()` to final name only after checks 2–4 pass | partial/corrupt downloads can never be mistaken for valid cache entries |
| 2 | First line starts with `LOCATION,` and parses to a station name + lat/lon | reject file; try next resolution tier |
| 3 | Header lat/lon vs the station-index entry: geodesic distance ≤ 10 km | structured warning `epw_header_mismatch`; file still accepted (header coordinates are occasionally rounded in published files) |
| 4 | Data row count ∈ {8760, 8784} (8784 = leap-year AMY; warn — TMY expected) | reject file; try next resolution tier |
| — | All resolution tiers exhausted with no valid EPW | **abort run** (`RuntimeError`, structured payload) |

The abort is deliberate: weather is the one input for which there is no per-building degradation path — *every* downstream stage (Module 04 keys on the zone; Stage 4 cannot launch without `-w`) is blocked, so flag-don't-drop does not apply. Finally, the accepted EPW is **copied** (not symlinked — Windows portability) into `<output_dir>/weather/<canonical_name>.epw`, and the `epw_path` column points at that run-local copy.

> **Why this approach:** The atomic `.tmp → os.replace` pattern is the standard guard against the classic poisoned-cache failure (an interrupted download leaving a half-file that every later run trusts); EnergyPlus's own failure mode on a truncated EPW is a mid-simulation fatal that Step 4 would mis-triage as a building problem. The run-local copy makes each output directory self-contained — an HPC job stages `<output_dir>` to scratch and has everything it needs (Step 4 §6 staging; `inputs/reports/Open Source Urban Building Energy Modeling-Architecture.md`), and a frozen-input re-run years later does not depend on `~/.openubem/` surviving. **Rejected:** (a) pointing `epw_path` into the user cache — breaks run-dir self-containment and HPC staging; (b) symlinks — not portable to Windows workstations; (c) warn-and-continue on missing EPW — there is nothing downstream that can run without it; a loud abort at minute 0 beats 400 `failed_crash` rows at minute 30.

### 3E — Column Append & Artifact Emission (Module 02 orchestrator: `openubem/acquisition/__init__.py :: enrich_climate()`)

Exactly three columns are appended to the flowing GeoDataFrame; everything else lands in the sidecar:

| Appended column | Dtype | Values |
|---|---|---|
| `climate_zone` | categorical | 16-token closed vocabulary (§3B); never null |
| `epw_path` | str (object) | absolute path of the run-local EPW copy (§3D); identical for all rows of a run; never null |
| `provenance_climate_zone` | categorical | `{ASHRAE_STANDARD, HEURISTIC}` (canonical §12 tokens); never null |

Emitted artifacts: `02a_buildings_climate.gpkg` (layer `buildings`, (N, 29), UTM CRS preserved) + `02a_buildings_climate.schema.json` (29 entries, same format as Step 2's schema sidecar) + `02a_climate_epw.parquet` (N × 9):

| Sidecar column | Dtype | Notes |
|---|---|---|
| `osm_id` | str | join key; row set identical to the GeoPackage |
| `climate_zone` | str | duplicated for join-free auditing |
| `climate_zone_method` | str | `{county_within, nearest_fallback}` |
| `county_geoid` | str | 5-digit FIPS from the matched county |
| `state` | str | 2-letter USPS — **consumed by Step 5 §3E for the eGRID state→subregion lookup (resolves Step 5 OQ-3)** |
| `epw_station_id` | str | WMO index of the resolved station |
| `epw_path` | str | as in the GeoPackage |
| `epw_distance_km` | float | geodesic building-representative-point… strictly, run-point → station distance (constant per run) |
| `provenance_climate_zone` | str | as in the GeoPackage |

> **Why this approach:** The Step 3 input contract is frozen at **57** columns and the Step 5 results contract at 57 + 13 = **70** (design_state rows 102; Step 3 §2); adding `state` as a flowing column would silently make them 58/71 and break both frozen documents. The sidecar keeps the flowing schema exactly on-contract while giving Stage 5 a *designed* owner for `state` — replacing the interim centroid-join Step 5 §3E had to assume (its OQ-3 named Module 02 as the natural home). The sidecar is this step's I6 persistent intermediate alongside the GeoPackage. **Rejected:** (a) `state` as a 30th flowing column — breaks two frozen contracts for one Stage-5-only value; (b) leaving Step 5's interim centroid join in place — two independent spatial-join implementations for the same fact will eventually disagree (the same drift argument as Step 5's imported `derive_num_floors`, row 99); (c) folding the sidecar into the GeoPackage as a second layer — Parquet is the established manifest format for non-spatial per-building tables (Steps 3 and 4 manifests).

---

## 4. Outputs

| Artifact | Filename | Format | Shape | Consumed by |
|---|---|---|---|---|
| Climate-located GeoDataFrame | `<output_dir>/02a_buildings_climate.gpkg` (layer `buildings`) | GeoPackage, UTM | (N, 29) | Step 2.2 / Modules 04–06b (keys envelope lookup on `climate_zone`); 26 upstream columns byte-identical. |
| Schema sidecar | `<output_dir>/02a_buildings_climate.schema.json` | JSON | 29 entries | schema validation in Step 2.2's input gate. |
| Climate/EPW sidecar | `<output_dir>/02a_climate_epw.parquet` | Parquet | (N, 9) | Step 5 / Module 15 (`state` for eGRID); audit dashboards (`climate_zone_method`, `epw_distance_km`). |
| Run-local weather copy | `<output_dir>/weather/<canonical_name>.epw` | EPW text | 1 file per run (Phase 1) | Step 4 binds it via the `epw_path` column at launch (`-w`). |

Row-level guarantees: **(1)** N rows in = N rows out in both per-building artifacts (flag-don't-drop; Step 2.1 drops nothing); **(2)** the 26 upstream columns are byte-identical pass-through; **(3)** `climate_zone`, `epw_path`, `provenance_climate_zone` are never null — the only failure modes are whole-run aborts (§3B Tier-—, §3D); **(4)** `epw_path` points inside `<output_dir>` (self-containment).

---

## 5. Validation

### 5.1 Metrics and acceptance thresholds

| Metric | Threshold | Rationale (cite source) |
|---|---|---|
| Zone/state coverage | 100% of rows non-null `climate_zone`, `state`, `county_geoid` (run aborts otherwise) | §3B fallback chain terminates in abort, never in NaN — Module 04's lookup has no NaN branch |
| Known-city zone fixture | 8/8 exact: Miami→1A, Phoenix→2B, San Francisco→3C, Boston→5A, Chicago→5A, Denver→5B, Duluth→7, Fairbanks→8 | spot-anchors the bundled county GPKG against publicly known ASHRAE city assignments (Technical Pipeline §4 examples '3A', '5A', '7') |
| `nearest_fallback` rate | ≤ 1% on the Boston 500 m fixture | Tier-1 `within` should catch effectively all on-land buildings; a higher rate indicates county-layer topology defects (→ OQ-1) |
| EPW gate integrity | 100% of accepted EPWs pass the §3D checks; the deliberately truncated fixture EPW is rejected at check 4 | the poisoned-cache failure mode is the one §3D exists to prevent |
| Header–index consistency | resolved station header lat/lon within 10 km of `epw_stations.csv` entry | catches stale or mis-keyed station-index rows (→ OQ-2) |
| Determinism | identical inputs + warm cache ⇒ byte-identical `02a_*` artifacts across re-runs | pure lookups; any drift indicates hidden state |
| Sidecar integrity | sidecar `osm_id` set == GeoPackage `osm_id` set; `epw_path` identical across all rows | the sidecar is a projection of the same run, not a second pipeline |

### 5.2 Test data and holdout strategy

- **Offline unit fixtures** (no network, bundled data only): the 8 known-city coordinate fixtures above; a synthetic point in Boston Harbor (must resolve via `nearest_fallback` + HEURISTIC); a point pair straddling the Suffolk/Middlesex county line (both 5A — assignment must differ in `county_geoid`, agree in `climate_zone`); a coordinate in open ocean > 5 km from any county (must abort); a deliberately truncated EPW and a header-less EPW in a fake cache (both rejected); `offline=True` with cold cache (must abort) and warm cache (must succeed).
- **Boston Downtown 500 m integration fixture** — the ~400-building GeoPackage from Steps 1–2: expect 100% `county_within`, all 5A/MA/25025, one station (Boston Logan, WMO 725090), `epw_distance_km` ≈ constant.
- Holdout regime: not applicable — nothing is trained. Boston remains the integration fixture by upstream convention.

### 5.3 True Future Test (only if a forecast or generalization claim is made)

Not applicable — Step 2.1 is a deterministic spatial lookup plus a file-resolution protocol; it trains no model and makes no forecast. Its generalization surface (does the bundled county layer + station index cover arbitrary US neighbourhoods?) is exercised structurally by the abort paths in §3B/§3D rather than by a holdout.

---

## 6. Compute

| Resource | Estimate | Source of estimate |
|---|---|---|
| GPU hours (Calcul Québec / Concordia HPC) | 0 | pure vector-GIS + one HTTP download |
| CPU | single core, seconds | one `sjoin` over ~3,100 county polygons + one geodesic argmin over the station index |
| Wall-clock (Boston 500 m, warm cache) | < 30 s | dominated by GeoPackage read/write |
| Wall-clock (cold cache) | + one ~1.5–2 MB EPW download | climate.onebuilding.org typical file size |
| Peak memory | < 1 GB | county layer + N-row frame |
| Storage | ~1.5–2 MB per cached station + same again for the run-local copy | §3D copy policy |
| Network | 0 bytes with `offline=True` or warm cache | §3C resolution order |

Step 2.1 is the cheapest step in the pipeline; its cost story is operational (network availability, cache hygiene), not computational.

---

## 7. Open Questions

- [ ] **OQ-1** — Pin the **edition and provenance of the bundled `ashrae_climate_zones.gpkg`**: which DOE/PNNL county-assignment vintage (ASHRAE 169-2013-consistent, as assumed by the 90.1-2019 lookup tables, vs the IECC-2021 county re-assignments that moved some counties a zone warmer), plus a committed checksum and licensing note. Recommendation: pin to the edition the bundled 90.1-2019 construction tables assume, so zone key and table values stay internally consistent. *(blocks §3B fixture sign-off and Step 2.2 §3C consistency)*
- [ ] **OQ-2** — One-time extraction of `data/epw_stations.csv` from the climate.onebuilding.org catalog (station id, name, state, lat/lon, URL, TMY edition), with a documented refresh procedure and licensing note. *(blocks §3C on real networks; unit fixtures use a 10-row synthetic index)*
- [ ] **OQ-3** — **TMY edition policy**: TMYx (2007–2021) vs older TMY3 files where both exist for a station. Affects EUI comparability against the CBECS 2018 validation anchor (Step 5 OQ-1) — a TMYx-2007-2021 climate is warmer than TMY3's 1991–2005 base period. Recommendation: TMYx, documented in the sidecar's `tmy_edition` provenance. *(blocks §3C canonical-filename rule)*
- [ ] **OQ-4** — Calibrate `EPW_MAX_STATION_KM = 300` (`ASSUMPTION_DESIGN_DEFAULT`): measure real station distances across the Phase-1 fixture cities and set the warn threshold to a value that fires on genuine outliers (mountain/rural gaps) without noise. *(blocks nothing; tunes §3C observability)*
- [ ] **OQ-5** — Phase-3 Canada hook: NECB HDD-based climate zones (HDD1–HDD7) are a *different vocabulary*, not an extension of the 16-token US set. Decide whether `climate_zone` becomes a union vocabulary with a `zone_system` discriminator column or Canada gets a parallel column. Out of Phase-1 scope (design_state row 35). *(blocks Phase 3 only)*

---

## 8. References

**`inputs/aim/`** — project charter and pipeline blueprint
- `inputs/aim/OpenUBEM_Technical_Pipeline.md` — §4 (Module 02 specification: `get_climate_zone` county join + fallback, `get_nearest_epw` resolution order, station index, geodesic distance), §2 (coordinates as a minimum required input), §9 (`run_ubem()` Stage-1 sketch — the single-centroid form §3B refines).
- `inputs/aim/OpenUBEM_Aim_Document.md` — Phase-1 US scope; open-data commitment (invariant I7).

**`inputs/papers/`** — technical references for libraries and methods
- `inputs/papers/geopandas.md` — `sjoin`/`sjoin_nearest` semantics, spatial indexing, `representative_point`, CRS handling; anchors §3A/§3B mechanics.
- `inputs/papers/12-essential-python-libraries-for-geospatial-data-analysis-with-hands-on-examples.md` — pyproj geodesic context; anchors §3C distance computation.
- `inputs/papers/a-systematic-literature-review-of-physics-based-urban-building-energy-modeling-ubem-tools-data-sourc.md` — weather files as a canonical UBEM input class; supports the fail-loud (no degradation path) argument in §3D.

**`inputs/reports/`** — UBEM methodology context
- `inputs/reports/UBEM Inputs and GitHub Repository Review.md` — weather-input practices across open UBEM tools; anchors the EPW cache/mirror design.
- `inputs/reports/Open Source Urban Building Energy Modeling-Architecture.md` — HPC scratch-staging pattern; anchors the §3D run-local copy decision.

**Prior-step DESIGN docs (binding contracts)**
- `outputs/2026-05-06_step-2-classify-each-cleaned-osm-building-into-one-of-the-30-openstudio-archetyp/DESIGN_step-2-...md` — 26-column input artifact + schema sidecar convention (§3E/§4).
- `outputs/2026-05-07_step-3-generate-one-energyplus-idf-per-building-from-the-archetype-enriched-geod/DESIGN_step-3-...md` — 57-column frozen downstream contract; OQ-7 names this module as the blocker.
- `outputs/2026-06-09_step-5-parse-energyplus-outputs-into-eui-gwp-iod-and-aggregate-results-back-to-th/DESIGN_step-5-...md` — OQ-3 (`state` owner) and §3E eGRID lookup, resolved here via the sidecar.

**External anchors (cited via inputs only — no fabricated DOIs)**
- climate.onebuilding.org / energyplus.net-weather — EPW repositories named in Technical Pipeline §4 as primary/fallback mirrors.
- ASHRAE 169 / DOE county climate-zone assignments — referenced via Technical Pipeline §4; edition pinning tracked as OQ-1.

---

## 9. Key Decisions Summary

| # | Decision | Sub-stage | Rationale (one line) | Alternatives rejected |
|---|---|---|---|---|
| 1 | Column-accretion position **after Step 2** (26 → 29), despite Module 02 being logically Stage-1 | §1 | Step 2's frozen 23 → 26 byte-identical contract (row 71) fixes the artifact order; nothing in Module 02 needs `archetype_id`, so only the chain position changes | Re-opening Step 2's frozen contract; running Module 02 inside Step 1 (would widen Step 1's frozen 23-column output). |
| 2 | Per-building county `sjoin` on `representative_point()`, not the spec's single union-centroid zone | 3A/3B | Vectorized join is near-free and correct when a bbox crosses a county/zone boundary; representative point is guaranteed inside the footprint | Spec-literal single centroid (silent mis-zoning); polygon join (double-matching at borders); reverse-geocoding APIs (network dependency, I7). |
| 3 | Closed 16-token US `climate_zone` vocabulary; `{ASHRAE_STANDARD, HEURISTIC}` provenance; nearest-fallback ≤ 5 km, else whole-run abort | 3B | Closed-vocabulary discipline (rows 50, 69, 94); local gaps degrade traceably, systemic coverage failure fails loudly | Open string zone column; NaN zone with flag (Module 04 has no NaN branch); silent nearest at unlimited distance. |
| 4 | One EPW station per run, geodesic-nearest to the neighbourhood representative point; `epw_distance_km` recorded per building | 3C | Station spacing ≫ neighbourhood size; per-building stations buy zero information and cost a spurious EUI discontinuity; the recorded distance self-collects OQ-4 calibration data | Per-building nearest station; one EPW per climate zone (zones ≠ station Voronoi cells). |
| 5 | Resolution order user `epw_dir` → cache → onebuilding → energyplus.net; atomic `.tmp → os.replace`; uniform validation gate; cold-cache + `offline` ⇒ abort | 3C/3D | Spec-mandated order; atomic rename kills the poisoned-cache failure; weather has no per-building degradation path so flag-don't-drop does not apply | Warn-and-continue without EPW (400 failed_crash rows later); trusting cache files unvalidated. |
| 6 | `epw_path` points at a run-local **copy** under `<output_dir>/weather/` | 3D | Self-contained run dirs survive cache eviction and stage cleanly to HPC scratch; copies, not symlinks, for Windows portability | Pointing into `~/.openubem/epw/`; symlinks. |
| 7 | `state` (+ `county_geoid`, method, distance) carried in the `02a_climate_epw.parquet` sidecar, **not** as a flowing column | 3E | Keeps the frozen 57-column Step 3 and 70-column Step 5 contracts intact while giving Step 5's eGRID lookup a designed owner — resolves Step 5 OQ-3 | 30th flowing column (breaks two frozen contracts); leaving Step 5's interim centroid join (duplicate spatial logic drifts). |

---

## 10. Progress Log *(populated by downstream `/run` reporter — leave empty here)*

<!-- The downstream execution project's reporter agent appends `### Session: <date> | Loop: <N>` blocks under this header after each /run cycle. NEITHER the architect NOR the documenter writes here. -->

---

## 11. Revision Log *(populated by DOCUMENTER on /design re-runs only — EMPTY on first creation)*

<!-- Append-only. DOCUMENTER inserts a new block on each /design re-run.

On MODE=new this section MUST contain only this comment block — no `### Session:` block. The first revision block is written on the first MODE=update run.

### Session: <YYYY-MM-DD> | Pass: <final-pass>
**Trigger:** <one-line: new evidence, change request, retired decision>
**Changes:** <sections touched + one-line summary each>
**Decisions retired:** <design_state.md rows retired, or "none">
-->

### Session: 2026-06-10 | Pass: n/a (direct resolution session)
**Trigger:** User resolved all 5 §7 Open Questions in chat; answers recorded in `inputs/notes/2026-06-10_step-2-1-assign-ashrae-climate-zone-us-state-and-epw-weather-file-to-every-build_resolved-open-questions.md`.
**Changes:** §7 statuses recorded here only (§1–§9 untouched per append-once rule):
- **OQ-1 RESOLVED (decision part):** bundled `ashrae_climate_zones.gpkg` pinned to **ASHRAE 169-2013-consistent** county→zone assignments — the edition the bundled 90.1-2019 construction tables assume, keeping zone key and table values internally consistent; IECC-2021 re-assignments rejected for Phase 1. Checksum + licensing note remain an implementation-repo extraction task. §3B fixture sign-off and Step 2.2 §3C consistency are unblocked on the design side.
- **OQ-2 DEFERRED to implementation repo:** `data/epw_stations.csv` extraction from climate.onebuilding.org — source, schema, and refresh requirements fully specified; execution project performs it.
- **OQ-3 RESOLVED:** **TMYx 2007–2021** preferred wherever both editions exist; edition recorded per run in the sidecar's `tmy_edition`. §3C canonical-filename rule unblocked.
- **OQ-4 DEFERRED to implementation repo:** 300 km threshold calibration needs measured fixture-city distances; `EPW_MAX_STATION_KM = 300` stands as `ASSUMPTION_DESIGN_DEFAULT`, with `epw_distance_km` self-collecting the calibration data.
- **OQ-5 RESOLVED by deferral:** Canada and NECB standards skipped at this stage (user decision); union-vocabulary vs parallel-column decided in Phase 3. Reaffirms design_state row 35.
**Decisions retired:** none. New design_state rows 114–116 record the confirmations (zone-map edition + TMYx policy; US/ASHRAE-only Phase-1 standards scope; confirmed defaults + deferred-extraction register).
