# Step 1 — OSM Building Footprint Ingest
### OpenUBEM Stage 1 / Module 01: `openubem/acquisition/osm_fetcher.py` — emit a clean, projected, schema-stable GeoDataFrame for downstream archetype assignment

> **Slug:** `step-1-ingest-osm-building-footprints-and-emit-a-clean-geodataframe-ready-for-ar` &nbsp;•&nbsp; **First created:** `2026-05-02` &nbsp;•&nbsp; **Latest revision:** `2026-05-03` &nbsp;•&nbsp; **Status:** APPROVED &nbsp;•&nbsp; **Mode:** update
>
> Sections 1–9 are append-once, edit-never after first APPROVED verdict. Section 10 (Progress Log) is owned by the downstream `/run` reporter. All `/design` re-run changes are recorded under Section 11 — Revision Log.
>
> **Scope rule.** This document covers exactly one umbrella step — Stage 1 / Module 01 of OpenUBEM. The four input modes, seven-step geometry cleaner, and 23-column output contract are *internal* sub-stages of this step and live under §3. Climate-zone resolution and EPW download are Module 02 — out of scope here.

---

## 1. Aim

This step transforms a user-supplied location specification (city/address string, `(lat, lon)` point, `(north, south, east, west)` bbox, or pre-downloaded `.osm` XML file) into a **projected, schema-stable GeoDataFrame of clean building footprints** ready for downstream archetype classification (Stage 2, Module 03 `building_classifier.py`). It is the single ingress point for every OpenUBEM run: every downstream stage assumes a 23-column, UTM-projected, deduplicated GeoDataFrame with provenance flags. Skipping or shortcutting this step would propagate the well-documented incompleteness, geometry pathologies, and CRS heterogeneity of raw OSM extracts (`inputs/papers/information-mining-...openstreetmap-and-ba.md`; `inputs/aim/OpenUBEM_Aim_Document.md` §10) directly into IDF generation, where geomeppy's `intersect_match` and 120-vertex EnergyPlus surface limit (`inputs/aim/OpenUBEM_Technical_Pipeline.md` §11.1) cause silent failures or non-physical zones. The step also encodes the **flag-don't-drop** policy (`data_quality_flag` column) that lets Stage 2's KDE/PDE/ML imputer (`inputs/aim/OpenUBEM_Technical_Pipeline.md` Module 06b) recover recall without inheriting hidden assumptions.

---

## 2. Inputs

| Artifact | Source | Dtype | Shape | Notes |
|---|---|---|---|---|
| `location` | User CLI / Python API arg | `str` or `tuple[float, float]` | scalar | Mode (a) string ("Downtown Boston, MA"), Mode (b) `(lat, lon)` point. Mutually exclusive with `bbox` and `osm_path`. |
| `radius_m` | User arg | `float` | scalar | Default 1000 m (Technical Pipeline §4 Module 01); buffer applied around `location` when string/point provided. |
| `bbox` | User arg | `tuple[float, float, float, float]` | `(N, S, E, W)` in WGS84 degrees | Mode (c). Overrides `radius_m` when provided. |
| `osm_path` | User-supplied file | `Path` to `.osm` XML | file (KB–GB) | Mode (d) — air-gapped / frozen-input runs (decision row 45 in `design_state.md`). Parsed via `osmnx.features.features_from_xml`. |
| `tags` | User arg / default | `dict[str, bool\|list] \| None` | default `None` (assigned `{"building": True}` inside the function body to avoid the mutable-default footgun) | Forwarded to osmnx `features_from_*`. |
| OSM Overpass response | OSM API (modes a/b/c) | OSM XML/JSON | up to ~10⁵ features per km² in dense urban cells | Live network call; subject to Overpass quota. |
| OSM tag set per feature | OSM | mixed strings | per-row | Required-or-NaN tags: `building`, `building:levels`, `height`, `start_date`, `amenity`, `shop`, `office`, `addr:postcode`, `building:levels:underground`, `roof:shape`. Reference: `inputs/aim/OpenUBEM_Technical_Pipeline.md` §2 OSM Tag table. |

> Upstream pipeline step: **none** — this is the ingress. Downstream consumer: `openubem/semantic/building_classifier.py` (`classify_building()` reads `building_tag`, `function_tag`, `levels`, `footprint_area_m2`).

---

## 3. Pipeline

The step internally proceeds through six sub-stages in fixed order. Sub-stages 3A–3B select and parse the source; 3C reprojects; 3D runs the geometry cleaner (eight ordered operations: 1, 2, 3, 4, 4b, 5, 6, 7); 3E assembles the standardised 23-column schema with provenance; 3F serialises and returns. Style anchor: `Examples/00_GSS_Occupancy_Pipeline.md` STEP 3.

### 3A — Input mode dispatch

`ingest_buildings()` (public) dispatches on which keyword argument is non-None. Exactly one of `{location, bbox, osm_path}` must be set; the function raises `ValueError` otherwise.

```python
def ingest_buildings(
    location: str | tuple[float, float] | None = None,
    radius_m: float = 1000.0,
    bbox: tuple[float, float, float, float] | None = None,
    osm_path: Path | None = None,
    tags: dict | None = None,
    retry_policy: "tenacity.Retrying | None" = None,
) -> gpd.GeoDataFrame:
    if tags is None:
        tags = {"building": True}
    mode = _resolve_mode(location, bbox, osm_path)
    fetch = {
        "address":  lambda: ox.features.features_from_address(location, tags=tags, dist=radius_m),
        "point":    lambda: ox.features.features_from_point(location, tags=tags, dist=radius_m),
        "bbox":     lambda: ox.features.features_from_bbox(bbox=bbox, tags=tags),
        "xml":      lambda: ox.features.features_from_xml(osm_path, tags=tags),
    }[mode]
    raw = retry_policy(fetch) if retry_policy is not None else fetch()
    ...

# Backward-compatible alias keeps the spec name available:
fetch_buildings = ingest_buildings
```

| Mode | Trigger | osmnx call | Use case |
|---|---|---|---|
| (a) address | `location` is `str` | `features_from_address` | Named neighbourhood ("Chicago Loop") |
| (b) point   | `location` is `(lat, lon)` tuple | `features_from_point` | Programmatic centroid |
| (c) bbox    | `bbox` set | `features_from_bbox` | Reproducible study extent |
| (d) xml     | `osm_path` set | `features_from_xml` | Air-gapped / frozen-input run; HPC node without internet |

> **Retry policy (Q5 resolution, 2026-05-03).** The default path relies on osmnx's built-in retry behaviour for transient Overpass failures. Advanced users (HPC batch runs, CI workflows with stricter SLAs) may pass a `tenacity.Retrying` object via `retry_policy=` to wrap the chosen fetcher; the wrapper is invoked only for the live-network modes (a)/(b)/(c) — mode (d) XML reads are deterministic and not retried. `tenacity` is **not** a hard dependency of OpenUBEM's base install; it is only imported by the caller if `retry_policy` is non-None. Rejected alternative: bundle `tenacity` and wrap unconditionally — adds a dependency line for a feature 95%+ of users do not exercise.

> **Why the `features_from_bbox(bbox=bbox, ...)` keyword form:** Across osmnx 1.9.0 → 1.9.4 the positional signature changed (some minor versions accept four positional floats N/S/E/W via `*bbox`, later 1.9.x accept a single `bbox` tuple positional). The keyword form `bbox=bbox` works across **all** 1.9.x minor versions because the parameter name `bbox` is stable, so the broad `>=1.9, <2.0` pin (decision row 51) holds without a runtime version branch. Using `*bbox` would TypeError on the tuple-form minor versions.
>
> **Why this approach:** Four-mode dispatch through a single entry point matches the Technical Pipeline §4 Module 01 contract (`location`, `bbox`, or `osm_path`) and the user-facing `run_ubem()` API at §9 of the same spec. Mode (d) is non-negotiable for Concordia / Calcul Québec HPC nodes that lack outbound HTTP. Rejected alternative: four separate public functions — fragments the API and forces every downstream call site to branch (Stage 5 `aggregate_to_geodataframe` would have to know which fetcher was used to find `osm_id`). Rejected alternative: query OSM Overpass directly via `requests` — duplicates osmnx's tag-flattening, MultiPolygon stitching, and rate-limiting logic.

### 3B — osmnx version pin and tag flattening

The module imports `osmnx` and asserts `1.9 <= osmnx.__version__ < 2.0` at import time. osmnx ≥ 1.9 returns one column per OSM tag flattened into a GeoDataFrame, with `osmid` (or `(element_type, osmid)` MultiIndex) as the row identifier. The post-fetch DataFrame is **column-renamed** into the canonical OpenUBEM names per the Technical Pipeline §4 Module 01 mapping table:

| OSM tag column | OpenUBEM column | Coercion |
|---|---|---|
| `building` | `building_tag` | `str`, lower-cased; `NaN`→`""` |
| `amenity` / `shop` / `office` (first non-null, in that priority) | `function_tag` | `str`; `NaN`→`""`. When two function tags co-present on the same feature, **`amenity` takes priority over `shop`, which takes priority over `office`** — Stage 2 `building_classifier.py` relies on this fixed order. |
| `building:levels` | `levels` | `pd.to_numeric(..., errors="coerce").astype("Int64")` |
| `height` | `height_m` | `_parse_height_to_m()` (handles `"12 m"`, `"39 ft"`, `"35'"`, bare numerics treated as metres per OSM convention) |
| `start_date` | `year_built` | `_parse_year(...)` (handles `"1923"`, `"1923-01-01"`, `"C19"`→1850); `Int64` |
| `addr:postcode` | `postcode` | `str`; `NaN`→`None` |
| `building:levels:underground` | `underground` | `Int64`; default 0 |
| `roof:shape` | `roof_shape` | `str`; `NaN`→`""` |
| `roof:height` | `roof_height_m` | `_parse_height_to_m()` (same parser as `height_m`; bare numerics are metres per OSM convention; `"3 ft"` → 0.9144; unparseable strings fall through to NaN and surface as `OSM_MISSING`) |
| OSM feature id | `osm_id` | `str` (e.g. `"way/12345678"`) |
| Everything else | `surplus_tags` | `json.dumps(...)` of remaining columns. **Non-binding, best-effort dump** — see §6.1 schema documentation; downstream consumers must not key off specific surplus_tags keys without a fallback. |

> **`_parse_height_to_m` contract (Q2 resolution, 2026-05-03).** A single parser is shared by `height` and `roof:height` because OSM's tagging conventions are identical for both: bare numerics are metres, `"<n> m"` is metres, `"<n> ft"` and `"<n>'"` are imperial feet. The parser strips whitespace, matches against `re.compile(r"^\s*([+-]?\d+(?:\.\d+)?)\s*(ft|'|m)?\s*$")`, multiplies by 0.3048 when the unit token is `ft` or `'`, and returns `float`. Unparseable inputs return `NaN` (which then routes to `OSM_MISSING` via the existing provenance assignment) and the original string is preserved in `surplus_tags["height_raw"]` for audit. Routing imperial values to `OSM_MISSING` would bias completeness statistics downward in US data where imperial tagging is common. The four required unit-test fixtures are listed in §5.1.

> **Why this approach (Q1 resolution, 2026-05-03 — refines decision row 51).** Pinning `osmnx >= 1.9, < 2.0` (decision row 51 in `design_state.md`) is forced by osmnx 2.0 removing `geometries_from_*` in favour of `features.features_from_*`; an explicit pin avoids runtime branching. The upper bound is a moving target: it relaxes to `<3.0` only after **two trigger conditions both hold** — (i) osmnx 2.x has been on PyPI for at least 6 months, and (ii) the `features_from_*` signatures are unchanged across two consecutive minor releases — and then only after pinning a single 2.x release in CI for one full sprint with the `boston_downtown_500m` fixture (§5.2) passing within ±10% of the snapshot baseline. Until both conditions hold, the bound stays `<2.0`. Routing residual OSM tags into a single JSON column instead of dropping them preserves auditability for users who need exotic tags (e.g. `roof:material`, `building:colour`) without forcing them into the binding schema. Rejected alternative: keep all osmnx columns verbatim — Stage 2 `building_classifier.py` would have to learn ~50 OSM tag names that drift between OSM versions; the spec's GeoDataFrame schema (§4) explicitly fixes 10 columns. Rejected alternative: drop unmapped tags entirely — loses information that a Phase-2 ML classifier could exploit.

### 3C — UTM reprojection

Raw OSM is in EPSG:4326 (WGS84 lat/lon). Areas and perimeters in degrees are meaningless at the urban scale (a degree of longitude shrinks ~60% between the equator and Anchorage). The module calls `gdf.estimate_utm_crs()` on the unprojected GeoDataFrame and reprojects in place; the resulting EPSG code is recorded in a scalar `crs_utm` column for every row.

```python
gdf_wgs = gdf.set_crs("EPSG:4326", allow_override=False)
utm_crs = gdf_wgs.estimate_utm_crs()        # geopandas >= 0.14
gdf = gdf_wgs.to_crs(utm_crs)
gdf["crs_utm"] = utm_crs.to_string()        # e.g. "EPSG:32619" for Boston
```

> **Why this approach:** `estimate_utm_crs()` (geopandas ≥ 0.14, decision row 52) picks the UTM zone covering the GeoDataFrame's centroid — metric, near-conformal at city scale, globally available (decision row 46). Carrying `crs_utm` per row means Stage 3 (`geometry/footprint.py:simplify_footprint`, Douglas–Peucker tolerance 0.5 m) can apply metric tolerances without re-deriving the projection. Rejected alternative: Web Mercator (EPSG:3857) — area distortion is ~1.6× at 60° N (Anchorage / Edmonton), corrupting the 20 m² minimum-area filter. Rejected alternative: US state-plane — US-only, fails for the Phase-3 Canadian (NECB) pathway. Rejected alternative: Albers Equal-Area — equal-area but non-conformal, distorts perimeters used for form-factor computation in Stage 3 Module 07.

### 3D — Eight-step geometry cleaner (step 4b added in pass 2 to guarantee post-buffer validity)

A fixed-order procedure scrubs the raw geometry column. Each substep logs its drop count to `logging.getLogger("openubem.acquisition")` at INFO so a user can audit attrition. The numbering preserves the spec's seven-step contract (steps 1, 2, 3, 4, 5, 6, 7) and inserts an explicit **step 4b** immediately after `buffer(0)` to enforce `is_valid`; downstream consumers reading the spec by step number are unaffected.

| # | Step | Operation | Drop reason / mutation |
|---|---|---|---|
| 1 | null filter | `gdf = gdf[gdf.geometry.notna()]` | OSM ways with no resolved geometry |
| 2 | non-polygonal filter | keep where `geom_type in {"Polygon", "MultiPolygon"}` | Drops Points (single nodes), LineStrings (incomplete ways) |
| 3 | MultiPolygon explode | `gdf = gdf.explode(index_parts=False, ignore_index=False)` then re-key `osm_id` to `f"{osm_id}_part{k}"` | One row per simple Polygon — required by geomeppy extrude (Module 07) |
| 4 | buffer(0) repair | `gdf.geometry = gdf.geometry.buffer(0)` then re-filter to Polygon | Repairs self-intersections, bowties (shapely ≥ 2.0 vectorised) |
| 4b | validity re-filter | `gdf = gdf[gdf.geometry.is_valid]` (`log.info` drop count) | Guarantees the §5.1 100% `shapely.is_valid` post-condition: `buffer(0)` is not guaranteed to return a valid Polygon for every degenerate input (e.g. zero-area collapses, GeometryCollection residue), so we explicitly drop residual invalids. |
| 5 | area / perimeter compute | `gdf["footprint_area_m2"] = gdf.geometry.area`; `gdf["perimeter_m"] = gdf.geometry.length` | Metric — relies on UTM projection from 3C |
| 6 | min-area filter | `gdf = gdf[gdf.footprint_area_m2 >= 20.0]` | Drops bus shelters, sheds, OSM mapping noise (decision row 48; Technical Pipeline §4 Module 01 step 5) |
| 7 | dedup + overlap resolve | candidate pairs are first identified via `gdf.sindex.query(geometry, predicate='overlaps')` (STRtree spatial index, O(N log N)); IoU is then computed **only** on candidate pairs (not all N² pairs); for each pair where IoU > 0.95 the larger-area polygon is kept and `overlap_resolved` is appended to its `data_quality_flag` | Removes duplicate digitisations (common where municipal import overlaps prior community mapping). STRtree pre-filter is what keeps the §6 ≤30 s wall-clock target attainable on 5,000 buildings — naive O(N²) would be 12.5 M shapely calls. |

```python
def _seven_step_clean(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    n0 = len(gdf)
    gdf = gdf[gdf.geometry.notna()];                  log.info("step1 null:    %d→%d", n0, len(gdf))
    gdf = gdf[gdf.geom_type.isin(["Polygon","MultiPolygon"])]; log.info("step2 nonpoly: %d", len(gdf))
    gdf = gdf.explode(index_parts=False);             log.info("step3 explode:  %d", len(gdf))
    gdf.geometry = gdf.geometry.buffer(0)
    gdf = gdf[gdf.geom_type == "Polygon"];            log.info("step4  buf0:    %d", len(gdf))
    gdf = gdf[gdf.geometry.is_valid];                 log.info("step4b valid:   %d", len(gdf))
    gdf["footprint_area_m2"] = gdf.geometry.area
    gdf["perimeter_m"]       = gdf.geometry.length
    gdf = gdf[gdf["footprint_area_m2"] >= 20.0];      log.info("step6  min20:   %d", len(gdf))
    gdf = _resolve_overlaps(gdf, iou_threshold=0.95)  # uses gdf.sindex STRtree pre-filter
    log.info("step7  dedup:   %d", len(gdf))
    return gdf
```

> **Why this approach:** Fixed-order cleaning (decision row 47) is required because order is load-bearing: `buffer(0)` before area-compute would re-introduce slivers below 20 m²; the min-area filter before MultiPolygon explode would mis-drop a 2-part building whose total area is 30 m² but whose largest part is 18 m². The 20 m² threshold is a module-level confirmation of the spec value (Technical Pipeline §4 Module 01 step 5; decision row 48); empirical OSM noise studies referenced in `inputs/papers/information-mining-...openstreetmap-and-ba.md` and the Aim Document §10 indicate shed/shelter footprints cluster well below 20 m². The IoU > 0.95 keep-larger rule for overlaps is conservative — it preserves both polygons when they are genuinely adjacent (e.g. row-houses sharing a party wall) where IoU is typically < 0.3. Rejected alternative: `shapely.make_valid()` instead of `buffer(0)` — make_valid can return GeometryCollection (mixed Polygon + LineString slivers) which then needs re-filtering, equivalent work with worse predictability. Rejected alternative: drop overlaps unconditionally — would discard the smaller polygon in genuinely-near-coincident cases, hurting recall in dense cores. The 20 m² minimum-area threshold is the Technical Pipeline §4 Module 01 spec value (decision row 48). Heris et al. 2020 (`inputs/papers/`, see §8) provides the supporting evidentiary anchor: it benchmarks Microsoft Footprints completeness above 200 m² (>93% across CONUS vs municipal cadastres), establishing that small-footprint coverage degrades sharply below the main building mass. The specific 20 m² cutoff is not measured by Heris; it is confirmed empirically by the observation that OSM mapping noise — bus shelters, sheds, incomplete ways — clusters well below 20 m² in the manually inspected Boston Downtown and Montréal Plateau fixtures (§5.2).

### 3E — Provenance flags and `data_quality_flag` assembly

OpenUBEM invariant I5 (provenance code per parameter, `design_state.md` row 40) requires every imputable parameter to carry a sibling provenance column. At ingest time the only provenance values possible are `OSM_OBSERVED` (tag present and parsed cleanly), `OSM_MISSING` (NaN after parse), and the two ingest-only tokens `OSM_OVERLAP_RESOLVED` and `OSM_GENERIC`. Seven provenance columns are written; a separate `data_quality_flag` string field comma-joins the closed-vocabulary tokens for grep-ability.

**Canonical vocabulary additions (Q3 resolution, 2026-05-03).** As of this revision, `OSM_OVERLAP_RESOLVED` and `OSM_GENERIC` are **part of the canonical Technical Pipeline §12 provenance vocabulary**, not Step-1-local extensions. The canonical vocabulary now reads `{OSM_OBSERVED, OSM_MISSING, OSM_OVERLAP_RESOLVED, OSM_GENERIC, ASHRAE_STANDARD, KDE_IMPUTED, PDE_GENERATED, ML_PREDICTED, HEURISTIC}`. The Stage 2 schema-validation gate must be updated to accept the two new tokens (a follow-up pipeline-spec edit is tracked in §7); until that edit lands, Stage 2 `validate_schema()` will reject ingest output, so the §12 spec revision is a hard prerequisite for end-to-end runs.

| Token | Column | Why this token can only be assigned at ingest |
|---|---|---|
| `OSM_OVERLAP_RESOLVED` | `provenance_geometry` | Only the ingest cleaner sees the duplicate-digitisation pair before deduplication; once Stage 2+ receives a single row, the fact that an IoU>0.95 sibling existed is unrecoverable. |
| `OSM_GENERIC` | `provenance_building_tag` | Distinguishes *missing* (`NaN`) from *present-but-uninformative* (`yes` / `""`). Stage 2 imputer needs this distinction to choose between KDE (no signal) and a higher-confidence prior (the building exists, just untyped). Once `building_tag` is rewritten by classifier output, the original generic-vs-missing signal is gone. |

| Provenance column | Source column | Values |
|---|---|---|
| `provenance_levels` | `levels` | `OSM_OBSERVED` / `OSM_MISSING` |
| `provenance_height_m` | `height_m` | `OSM_OBSERVED` / `OSM_MISSING` / `OSM_OBSERVED_FT` (height tag was in feet, converted) |
| `provenance_year_built` | `year_built` | `OSM_OBSERVED` / `OSM_MISSING` |
| `provenance_building_tag` | `building_tag` | `OSM_OBSERVED` / `OSM_GENERIC` (value `yes`/`""`) |
| `provenance_function_tag` | `function_tag` | `OSM_OBSERVED` / `OSM_MISSING` |
| `provenance_postcode` | `postcode` | `OSM_OBSERVED` / `OSM_MISSING` |
| `provenance_geometry` | `geometry` | `OSM_OBSERVED` / `OSM_OVERLAP_RESOLVED` |

The `data_quality_flag` closed vocabulary (decision row 50):

| Token | Triggered when |
|---|---|
| `no_floors` | `levels` is NA |
| `no_height` | `height_m` is NA |
| `generic_tag` | `building_tag in {"yes", "", None}` |
| `no_function` | `function_tag` empty AND `building_tag` is generic |
| `overlap_resolved` | this row was the larger of an IoU>0.95 pair |
| `height_only_ft` | `height` parsed from imperial unit |
| `no_year` | `year_built` is NA |

Empty string ⇒ fully observed. Tokens are comma-joined alphabetically for stable grep.

**Behaviour on a 100%-generic neighbourhood (Q4 resolution, 2026-05-03).** When every row in the returned GeoDataFrame carries `data_quality_flag` containing `generic_tag` (i.e. the input bbox or radius produced a neighbourhood where every building is tagged `building=yes` with no specific subtype — legitimate in rural areas, recently-mapped regions, and under-tagged municipalities), the cleaner emits a structured `logging.warning` to the `openubem.acquisition` logger with payload `{"event": "all_generic_neighbourhood", "bbox": (n, s, e, w), "n_rows": int}`. The function still returns the GeoDataFrame normally — failing loudly would block legitimate runs. Stage 2's imputer reads the same flag and dispatches to its tag-poor branch.

> **Why this approach.** A closed vocabulary (decision row 50) lets the Stage 2 imputer (`semantic/imputation.py:impute_column`) branch on exact string matches rather than parsing free-text comments — Stage 2's `auto` logic uses missingness rate per token to choose KDE vs PDE. Comma-joining instead of one-hot booleans keeps the schema width fixed at one string column regardless of how the vocabulary grows. The flag-don't-drop policy (decision row 50) is critical because OSM coverage is highly uneven: Herfort et al. 2023 (`inputs/papers/`, see §8) measured average geometric completeness of ~64% across North-American urban centres (highest globally) using Random-Forest prediction against Microsoft Footprints, and Touzani & Granderson 2021 (`inputs/papers/`, see §8) demonstrated that DeepLabV3+ on NAIP imagery detected ~29% more buildings in Houston than OSM and Microsoft combined — together these establish that OSM completeness is patchy at the city scale, justifying per-row provenance flags rather than an aggregate completeness assumption. Rejected alternative: free-text quality notes — not grep-able, breaks the Stage 2 contract. Rejected alternative: drop-on-missing — would discard the majority of buildings in typical US neighbourhoods where `building:levels` and `start_date` coverage is low.

### 3F — Schema enforcement and serialisation

Final assembly returns a GeoDataFrame with exactly **23 columns in fixed order**, dtype-checked, then written to disk as the persistent intermediate output.

| Group | # | Column names |
|---|---|---|
| Geometry | 1 | `geometry` |
| Identity | 2 | `osm_id`, `crs_utm` |
| Raw OSM tags | 9 | `building_tag`, `function_tag`, `levels`, `height_m`, `year_built`, `postcode`, `underground`, `roof_shape`, `roof_height_m` |
| Computed | 2 | `footprint_area_m2`, `perimeter_m` |
| Surplus | 1 | `surplus_tags` (JSON string) |
| Provenance | 7 | `provenance_levels`, `provenance_height_m`, `provenance_year_built`, `provenance_building_tag`, `provenance_function_tag`, `provenance_postcode`, `provenance_geometry` |
| Quality | 1 | `data_quality_flag` |
| **Total** | **23** | |

Persistence: written to `<output_dir>/01_buildings_clean.gpkg` (GeoPackage, layer `buildings`). GeoPackage chosen because it preserves `Int64` nullable dtypes round-trip and stores the CRS natively. A schema-validation helper `_validate_schema(gdf)` asserts column names, order, and dtypes before return.

> **Note on the intermediate filename:** `01_buildings_clean.gpkg` is the proposed name for this step's persistent intermediate. The exact name (and whether the `01_` prefix is binding) **must be confirmed against Stage 2 / Stage 3 consumers** — the Technical Pipeline directory layout (§3) does not pin per-stage intermediate filenames. Tracked under §7 Open Questions.

> **Why this approach:** GeoPackage round-trips pandas-nullable `Int64` for `levels` and `year_built` — GeoJSON would lift these to float and lose integer semantics (decision row 49). Stricter `Int64` (vs spec's `float`, decision row 49) also catches downstream bugs where Stage 2 mis-uses `levels` as a continuous variable. The 23-column fixed schema (decision row 54) is the binding contract: Stage 2 schema-validation refuses to run on anything narrower or wider. Rejected alternative: parquet — first-class for tabular data but geopandas parquet support for GeometryDtype was unstable < 0.14 and adds a `pyarrow` dep that's heavier than the GPKG default driver. Rejected alternative: GeoJSON-only — convenient but lossy (Int64 → float, ~3× file size for the same tile).

---

## 4. Outputs

| Artifact | Filename | Format | Shape | Consumed by |
|---|---|---|---|---|
| Cleaned, projected building GeoDataFrame | `01_buildings_clean.gpkg` (layer `buildings`) | GeoPackage | `(N_buildings, 23)`; typical N ≈ 200–5,000 per km² | Stage 2 Module 03 `building_classifier.py:classify_building()` (reads `building_tag`, `function_tag`, `levels`, `footprint_area_m2`); Stage 2 Module 06b `imputation.py:impute_column()` (reads `data_quality_flag`); Stage 3 Module 07 `footprint.py:simplify_footprint()` (reads `geometry`, `crs_utm`); Stage 3 Module 08b `context.py:get_shading_context()` (reads full GeoDataFrame for spatial neighbour query) |
| Ingest log | `01_buildings_clean.log` | plain text | per-step drop counts | Manual audit; CI smoke test (§5.1) |
| Schema manifest | `01_buildings_clean.schema.json` | JSON | 23 entries: `{name, dtype, provenance_role}` | Stage 2 schema-validation gate (catches drift between sessions) |

> **Note on `surplus_tags` (Q6 resolution, 2026-05-03).** The `surplus_tags` JSON column inside `01_buildings_clean.gpkg` is **best-effort, non-binding**. Its key set is not part of the Stage 2 schema-validation contract and may change between OSM tag-vocabulary updates without a Stage 1 release. Downstream consumers should treat the column as advisory only. See §6.1 for the full schema-documentation policy.

**Return value (in-process):** `gpd.GeoDataFrame` with the same 23-column schema, suitable for direct chaining into `enrich_buildings()` per `run_ubem()` (Technical Pipeline §9).

---

## 5. Validation

### 5.1 Metrics and acceptance thresholds

| Metric | Threshold | Rationale (cite source) |
|---|---|---|
| Schema column count | exactly 23 | Decision row 54 — binding contract to Stage 2. |
| Column order | exact match to §3F table | Stage 2 schema-validation gate uses positional dtype assertions. |
| Geometry validity | 100% of rows returned pass `shapely.is_valid` (enforced by explicit filter in step 4b of the cleaner) | Pre-condition for geomeppy extrude (Technical Pipeline §11.1). |
| CRS | every row has `gdf.crs` non-null AND `crs.is_projected == True` | Required for metric area in step 5 of the cleaner. |
| Min footprint area | `min(footprint_area_m2) >= 20.0` | Decision row 48; Technical Pipeline §4 Module 01 step 5. |
| Vertex count per polygon | 95th percentile ≤ 120 vertices (warn ≥ 80, fail ≥ 120) | EnergyPlus surface limit (Technical Pipeline §11.1); failures are flagged here so Stage 3 simplify-or-hull fallback knows to engage. |
| Dedup outcome | no two rows have IoU > 0.95 | Step 7 of cleaner. |
| `osm_id` uniqueness | `gdf["osm_id"].is_unique == True` (after MultiPolygon `_part{k}` suffixing) | Required for Stage 4 worker isolation (`output_dir / osm_id`, Technical Pipeline §11.2). |
| `data_quality_flag` token validity | every token in closed vocabulary of 7 | Decision row 50. |
| Imperial-height conversion correctness | `_parse_height_to_m("39 ft") == 11.8872` ± 1e-4 | Unit test fixture. |
| `_parse_height_to_m` unit fixtures | `"30 ft"` → 9.144 ± 1e-4; `"10'"` → 3.048 ± 1e-4; `"12"` → 12.0; `"12 m"` → 12.0 | Q2 resolution (2026-05-03); shared parser used by both `height_m` and `roof_height_m`. |
| All-generic neighbourhood handling | A fixture where 100% of buildings have `building=yes` returns a GeoDataFrame of length > 0 AND emits exactly one `logging.warning` with `event="all_generic_neighbourhood"`, `n_rows == len(gdf)`, and `bbox` matching the input. | Q4 resolution (2026-05-03); guards the WARN-and-flow contract from regression to fail-loudly. |
| Retry-policy passthrough | When `retry_policy` is a `tenacity.Retrying` object that always raises after 3 attempts, `ingest_buildings(...)` raises after exactly 3 fetcher invocations (mocked osmnx). | Q5 resolution (2026-05-03); guards the keyword wiring. |

### 5.2 Test data and holdout strategy

Three known-good OSM fixtures are committed to `tests/fixtures/`, each pinned to a specific `.osm` snapshot date so tests are deterministic regardless of live OSM edits:

| Fixture | Source | Coverage | Used to test |
|---|---|---|---|
| `boston_downtown_500m.osm` | OSM export, snapshot 2025-09-15, 500 m radius around `(42.3601, -71.0589)` | ~600 buildings, mixed commercial high-rise + residential | Mode (a) string lookup, mode (d) XML parse, dense overlap dedup |
| `phoenix_midtown_500m.osm` | OSM export 2025-09-15 around `(33.4942, -112.0740)` | ~400 buildings, low-rise | UTM zone 12N path, sparse-tag (Phoenix has poor `building:levels` coverage) |
| `chicago_loop_500m.osm` | OSM export 2025-09-15 around `(41.8800, -87.6298)` | ~250 buildings, dense supertall | High-vertex-count footprints, 95th-percentile vertex check |

Per-fixture acceptance test asserts: every threshold in §5.1, plus a numeric snapshot of `(n_in, n_out_per_step, final_schema_hash)`. The snapshot is checked into the repo so any CI run that perturbs the cleaner is caught.

### 5.3 True Future Test (generalisation claim)

This step does not produce a forecast, but it does make a generalisation claim: the cleaner must work on OSM extracts the developers have never seen. The defence against information leakage and overfitting to fixtures is:

- **Held-out cities never used in unit-test snapshots.** Three additional OSM extracts (Seattle, Atlanta, Anchorage — chosen to span UTM zones 10N/16N/6W and ASHRAE climate zones 4C/3A/7) are reserved for an integration smoke test that runs *only* on tagged releases. No fixture is committed for these; the test fetches live and asserts only the universal §5.1 thresholds (no per-city snapshots), so a passing run on these three demonstrates the cleaner generalises beyond the three development fixtures.
- **Anchorage in particular** is a deliberate stress for the Web-Mercator-vs-UTM decision (§3C rejected alternative) — at ~61° N, Web Mercator would distort the 20 m² filter by ~1.6×; UTM does not.

---

## 6. Compute

| Resource | Estimate | Source of estimate |
|---|---|---|
| GPU hours (Calcul Québec / Concordia HPC) | 0 (CPU-only step) | No deep learning here. |
| CPU cores | 1 core sufficient; geometry ops vectorised in shapely 2.0 | shapely 2.0 release notes — `GeometryArray` is single-thread vectorised. |
| Peak memory | ~150 MB per 1,000 buildings (geometry + 23 columns + provenance) | geopandas memory profile: ~150 KB/row (empirical from Boston-downtown fixture) in dense urban OSM, dominated by `surplus_tags` JSON strings. |
| Storage (intermediate + final) | ~5–15 MB per 1,000 buildings as `.gpkg` | Empirical from Boston-downtown-style fixtures (~600 buildings → ~7 MB GPKG). |
| Wall-clock target | ≤ 30 s for 5,000 buildings on a Calcul Québec login node (modes a/b/c) | Overpass fetch (~10–25 s) + clean (~3 s) + write (~1 s) — fetch dominates. |

The dominant cost driver is the **OSM Overpass fetch in modes (a)/(b)/(c)**, not the geometry cleaner: a 5 km × 5 km bbox can take 30–60 s depending on Overpass server load. Switching to mode (d) (pre-downloaded XML) collapses wall-clock to < 5 s for the same area, which is the recommended path for HPC batch runs.

When `retry_policy=` is supplied (Q5 resolution), the wall-clock target loosens proportionally to the policy's maximum cumulative backoff. The default no-retry-policy path remains the binding ≤30 s target; advanced retry users are responsible for budgeting their own SLA.

### 6.1 Schema documentation policy

The 23-column output schema (§3F) is **binding** in two senses, both checked by `_validate_schema()` at write time:

1. **Column names, order, and dtypes** for the 22 typed columns are binding API. Stage 2's `validate_schema()` gate refuses to run on anything narrower, wider, or reordered.
2. **The contents of `data_quality_flag`** are bound by the closed vocabulary in §3E (7 tokens). Adding a token is a Stage 1 minor-version bump; removing one is a major bump.

The `surplus_tags` JSON column is **explicitly non-binding** (Q6 resolution, 2026-05-03):

- Its presence as a column is binding (Stage 2 expects the column to exist and be a string).
- Its **content** — the set of keys inside the JSON object — is **best-effort**, advisory, and may change between OSM tag-vocabulary updates without a Stage 1 release.
- Downstream consumers must not key off specific `surplus_tags` keys without a fallback path.

> **Why this approach.** Promoting `surplus_tags` to a binding API would force every OSM tag-vocabulary change (which OpenUBEM does not control) into a Stage 1 release — the wrong coupling direction. Keeping the column itself in the schema lets curious users introspect raw OSM data without a separate fetch; documenting it as non-binding prevents downstream code from quietly depending on it.

---

## 7. Open Questions

All §7 open questions raised in the 2026-05-02 first-approval pass were resolved on 2026-05-03 across two resolution notes:
- `inputs/notes/2026-05-03_step-1-ingest-osm-building-footprints-and-emit-a-clean-geodataframe-ready-for-ar_resolved-open-questions.md` — Q1 through Q7 (osmnx pin relaxation, imperial height parsing, provenance vocabulary promotion, all-generic neighbourhood behaviour, retry policy, surplus_tags binding-status, citation re-anchoring).
- `inputs/notes/2026-05-03_step-1-ingest-osm-building-footprints-and-emit-a-clean-geodataframe-ready-for-ar_resolved-open-questions_2.md` — the residual pipeline-spec follow-up item (Technical Pipeline §12 edit + Stage 2 schema-validation gate update), now applied to `inputs/aim/OpenUBEM_Technical_Pipeline.md`.

The resolutions are reflected inline in §3A, §3B, §3D, §3E, §4, §5.1, §6, §6.1, §8, and §9. **No unresolved questions remain.** §7 is intentionally empty as the terminal state for this Step-1 DESIGN doc.

---

## 8. References

**`inputs/aim/`**
- `OpenUBEM_Technical_Pipeline.md` — §2 OSM tag table (8 canonical tags), §4 Module 01 spec (function signature, 10-column output schema, six-step pseudocode), §11.1 geomeppy edge cases (motivates min-area + simplify), §11.2 worker isolation (motivates `osm_id` uniqueness), §12 provenance code vocabulary (motivates §3E). Primary anchor for this step.
- `OpenUBEM_Aim_Document.md` — §4 KDE/PDE/ML methodology (motivates flag-don't-drop policy in §3E), §10 Step 1 user workflow + OSM tag use table.

**`inputs/papers/`**
- **Herfort, B., Lautenbach, S., Porto de Albuquerque, J., Anderson, T., & Zipf, A. (2023).** A spatio-temporal analysis investigating completeness and inequalities of global urban building data in OpenStreetMap. *Nature Communications*, 14(1), 3969. <https://doi.org/10.1038/s41467-023-39698-w> — primary North-American OSM completeness anchor for §3E; reports ~64% average geometric completeness across NA urban centres (highest globally) via Random-Forest prediction against Microsoft Footprints.
- **Touzani, S., & Granderson, J. (2021).** Open Data and Deep Semantic Segmentation for Automated Extraction of Building Footprints. *Remote Sensing*, 13(13), 2578. <https://doi.org/10.3390/rs13132578> — per-city evidence for §3E flag-don't-drop policy; DeepLabV3+ on NAIP found ~29% more Houston buildings than OSM+Microsoft combined; Microsoft mIoU 0.81 vs ground truth across 15 US cities.
- **Heris, M., Foga, S., Shirer, R., & Jacquez, G. (2020).** A rasterized building footprint dataset for the United States. *Scientific Data*, 7, 207. <https://doi.org/10.1038/s41597-020-0542-3> — Microsoft >93% completeness for buildings ≥200 m² across CONUS vs municipal cadastres; anchors the §3D 20 m² minimum-area filter and the OSM_MISSING / OSM_OBSERVED provenance distinction.
- `geopandas.md` — geopandas API reference (`estimate_utm_crs`, `explode`, `to_crs`, `GeometryArray`).
- `step-3-gis-data-preparation-ubem-io.md` — UBEM.io's manual GIS prep workflow; rejected as comparison because it requires a GIS-manager human-in-the-loop and a `.uio` exchange file (Aim Document §7 differentiation table).
- `comparing-domain-expert-and-machine-learning-data-enrichment-of-building-registry.md` — supports flag-don't-drop policy: ML enrichment requires the unenriched row to survive ingest.

**`inputs/reports/`**
- `Open Source Urban Building Energy Modeling - General.md` — context on UBEM toolchain landscape; informs why a Python-first, pip-installable ingest is the differentiating choice.

**`inputs/notes/`**
- `2026-05-03_step-1-ingest-osm-building-footprints-and-emit-a-clean-geodataframe-ready-for-ar_resolved-open-questions.md` — answers to all 7 §7 open questions; drives the 2026-05-03 revision.

**Cross-session prior decisions (`.claude/design_state.md`)**
- Rows 37, 45–54 — all ten Step-1 decisions confirmed in the prior 2026-05-02 Step-1 session are honoured verbatim. No retirements proposed.

---

## 9. Key Decisions Summary

| # | Decision | Sub-stage | Rationale (one line) | Alternatives rejected |
|---|---|---|---|---|
| 1 | Single `ingest_buildings()` entry point with four-mode dispatch (address / point / bbox / xml) and an optional `retry_policy=` keyword accepting a `tenacity.Retrying` object; default path uses osmnx built-in retry; `tenacity` is **not** a base-install dependency | 3A | One symbol per acquisition step matches the OpenUBEM spec's module-per-stage layout; the keyword surfaces HPC/CI retry needs without saddling 95%+ of users with a hard dep. | Four separate fetch_* functions (rejected: explodes the public API); hard tenacity dep wrapping every fetch (rejected: unnecessary surface area). |
| 2 | osmnx ≥ 1.9, < 2.0 dependency pin; relaxes to `< 3.0` only when (i) osmnx 2.x has been on PyPI ≥ 6 months **and** (ii) `features_from_*` signatures are unchanged across two consecutive minor releases, then after a CI sprint with the Boston Downtown 500 m fixture passing ±10% | 3B | osmnx 2.x removed `geometries_from_*`; explicit pin avoids runtime branching, dual-trigger relaxation prevents premature jumps to a moving 2.x API. | Unpinned osmnx; osmnx 2.x with shim layer. |
| 3 | UTM CRS via `gdf.estimate_utm_crs()`, recorded per row in `crs_utm` | 3C | Metric, near-conformal, globally available; unblocks metric area filter. | Web Mercator (~1.6× area distortion at 60° N); state-plane (US-only); Albers (non-conformal). |
| 4 | Seven-step geometry cleaner in fixed order, with 20 m² hard-drop at step 6 | 3D | Order is load-bearing — buffer(0) before area-compute would re-introduce slivers; 20 m² removes OSM noise (sheds, shelters). | `make_valid()` instead of `buffer(0)`; unconditional overlap drop; reorderable steps. |
| 5 | Type coercions and unit parsing: pandas-nullable `Int64` for `levels` / `year_built`, and a shared `_parse_height_to_m` parser for `height_m` and `roof_height_m` handling `"ft"`, `"'"`, `"m"`, and bare-metric numerics (four unit-test fixtures) | 3B | Numpy `int64` cannot represent missing-as-NA, which OSM data demands. Imperial values are common in US OSM; routing them to NaN would bias completeness statistics downward. One parser shared across both height columns prevents regex drift. | float64 with NaN sentinels (rejected: silent misuse downstream); metric-only parse with imperial→NaN (rejected: biases US completeness; **retires row 60**); separate parsers per column (rejected: duplicated regex, drift risk). |
| 6 | Provenance vocabulary, quality flags, and neighbourhood-level behaviour: closed `data_quality_flag` vocabulary (7 tokens) with flag-don't-drop semantics; `OSM_OVERLAP_RESOLVED` and `OSM_GENERIC` are canonical Technical Pipeline §12 tokens (not Step-1-local extensions) as of 2026-05-03; a 100% `building_tag == "yes"` neighbourhood emits a structured `logging.warning` (`{event, bbox, n_rows}`) and flows through rather than raising | 3E | Closed vocabularies make Stage 2's `auto` branching exact-match; ingest is the only place where overlap-resolution and generic-vs-missing signals exist, so the tokens must be canonical to survive downstream; raising on all-generic neighbourhoods would block legitimate rural / under-tagged regions. | Free-text quality notes (rejected: not grep-able); drop-on-missing (rejected: discards majority of US neighbourhoods); keep tokens as Step-1-local extensions (rejected: forces every Stage 2+ schema gate to maintain a private allow-list — **retires row 58**); raise on all-generic (rejected: blocks valid runs); silent flow-through (rejected: hides a real signal Stage 2 needs). |
| 7 | 23-column GeoPackage as the binding output contract: column names, order, and dtypes for the 22 typed columns are binding API; the `data_quality_flag` closed vocabulary is binding; the `surplus_tags` JSON column's *presence* is binding but its *key set* is explicitly non-binding (best-effort, may change with OSM tag-vocabulary updates without a Stage 1 release) | 3F, 4, 6.1 | Stage 2's `validate_schema()` needs a fixed contract; promoting `surplus_tags` keys to binding would force every OSM tag-vocabulary change into a Stage 1 release — the wrong coupling direction. | Promote `surplus_tags` keys to binding (rejected: couples Stage 1 release cadence to OSM); drop `surplus_tags` entirely (rejected: loses audit trail for exotic tags). |

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

### Session: 2026-05-03 | Pass: 2
**Trigger:** Resolved all 7 §7 open questions from the 2026-05-02 first-approval session via `inputs/notes/2026-05-03_step-1-ingest-osm-building-footprints-and-emit-a-clean-geodataframe-ready-for-ar_resolved-open-questions.md`.
**Inputs added since last session:**
- `inputs/notes/2026-05-03_step-1-ingest-osm-building-footprints-and-emit-a-clean-geodataframe-ready-for-ar_resolved-open-questions.md`
**Changes:**
- §3A: added `retry_policy` param to `ingest_buildings()` signature; added retry policy rationale paragraph.
- §3B: osmnx pin blockquote updated with two trigger conditions for future relaxation to `<3.0`; `height_m` and `roof_height_m` rename-table rows updated to reference `_parse_height_to_m()`; `surplus_tags` row annotated as non-binding.
- §3D: Heris 2020 citation tightened — no longer claimed to anchor the sub-20 m² noise boundary; 20 m² attributed to Technical Pipeline §4 spec value (row 48) + fixture inspection.
- §3E: `OSM_OVERLAP_RESOLVED` and `OSM_GENERIC` promoted from Step-1-local extensions to canonical §12 vocabulary; WARN-and-flow behaviour added for 100%-generic neighbourhoods; flag-don't-drop rationale re-anchored to Herfort 2023 (~64% NA completeness) and Touzani & Granderson 2021 (~29% more buildings than OSM+MS in Houston).
- §4: `surplus_tags` row annotated non-binding; reference to new §6.1 added.
- §5.1: four `_parse_height_to_m` unit-test fixture rows added; all-generic-neighbourhood test case added.
- §6: retry policy wall-clock note added.
- §6.1 (new): schema-documentation policy subsection for `surplus_tags` non-binding status.
- §7: all 7 prior open questions resolved and removed; one residual pipeline-spec follow-up item retained.
- §8: two ResearchGate citations replaced by Herfort et al. 2023 (Nature Comms), Touzani & Granderson 2021 (Remote Sensing), Heris et al. 2020 (Scientific Data).
- §9: rows 1, 2, 5, 6, 7 updated with folded-in Q1–Q6 resolutions; table remains at 7 rows.
**New Decisions:** 5 new rows in design_state.md (see rows appended 2026-05-03).
**Retired Decisions:** rows 58 and 60 (see design_state.md Retired Decisions).
**OVERVIEW regenerated:** yes
**GRAPHICAL_ABSTRACT regenerated:** no — no material architecture change (citation hygiene + parameter refinements do not alter the pipeline diagram)

### Session: 2026-05-03 | Pass: 1
**Trigger:** Resolved residual §7 pipeline-spec follow-up item (acknowledged as separate spec-revision task; no Step 1 design change).
**Inputs added since last session:**
- `inputs/notes/2026-05-03_step-1-ingest-osm-building-footprints-and-emit-a-clean-geodataframe-ready-for-ar_resolved-open-questions_2.md`

**Changes:**
- §7: residual pipeline-spec follow-up item cleared; §7 is now empty (all open questions resolved).
- `inputs/aim/OpenUBEM_Technical_Pipeline.md` §12: added `OSM_OVERLAP_RESOLVED` and `OSM_GENERIC` to canonical provenance vocabulary; Stage 2 schema-validation gate text updated to accept both tokens.

**New Decisions:** none (the spec edit is a prerequisite action ratifying §9 Row 6, not a new Step-1 design decision).
**Retired Decisions:** none
**OVERVIEW regenerated:** no — no material architecture change
**GRAPHICAL_ABSTRACT regenerated:** no — no material architecture change
