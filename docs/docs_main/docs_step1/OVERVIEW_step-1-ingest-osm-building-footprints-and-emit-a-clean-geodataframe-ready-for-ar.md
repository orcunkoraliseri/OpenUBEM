# OVERVIEW — Step 1 — OSM Building Footprint Ingest
### OpenUBEM Stage 1 / Module 01: `openubem/acquisition/osm_fetcher.py` — emit a clean, projected, schema-stable GeoDataFrame for downstream archetype assignment

> **Slug:** `step-1-ingest-osm-building-footprints-and-emit-a-clean-geodataframe-ready-for-ar` &nbsp;•&nbsp; **Snapshot of:** `DESIGN_step-1-ingest-osm-building-footprints-and-emit-a-clean-geodataframe-ready-for-ar.md` &nbsp;•&nbsp; **Generated:** `2026-05-03`
>
> Compact dashboard. For depth → read the DESIGN doc. For revision history → read DESIGN §11.

---

## AIM

This step turns a user's location specification (city/address string, `(lat, lon)` point, bounding box, or pre-downloaded `.osm` file) into a clean, UTM-projected, 23-column GeoDataFrame of building footprints. It is the single ingress point of the OpenUBEM pipeline — every downstream stage (archetype classifier, imputer, IDF generator) reads its 23-column contract.

**Why it matters.** If raw OSM flows downstream unfiltered, geomeppy extrude fails silently on invalid polygons, the EnergyPlus 120-vertex limit is breached on supertall footprints, and the KDE/PDE imputer cannot tell *missing* from *present-but-generic* — the pipeline produces non-physical zones or quietly drops most of the building stock.

---

## PIPELINE

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  3A — INPUT MODE DISPATCH                                                    ║
║  Inputs:    location (str | tuple) | bbox (N,S,E,W) | osm_path (.osm XML)    ║
║  Operation: single ingest_buildings() entry; one of 4 osmnx calls;           ║
║             optional retry_policy= keyword wraps fetch (tenacity.Retrying)   ║
║  Output:    raw GeoDataFrame in EPSG:4326                                    ║
║  Validation: exactly one of {location, bbox, osm_path} non-None              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3B — OSMNX VERSION PIN + TAG FLATTENING                                     ║
║  Inputs:    raw osmnx GeoDataFrame                                           ║
║  Operation: rename OSM tags → 9 canonical OpenUBEM cols; route rest to JSON; ║
║             shared _parse_height_to_m() for height_m and roof_height_m       ║
║             (handles "ft", "'", "m", bare-metric numerics)                   ║
║  Output:    GeoDataFrame with building_tag, function_tag, levels, height_m,  ║
║             year_built, postcode, underground, roof_shape, roof_height_m     ║
║  Validation: 1.9 <= osmnx.__version__ < 2.0 asserted at import (relaxes to   ║
║             <3.0 only after 6mo PyPI + 2 stable minor releases + CI sprint)  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3C — UTM REPROJECTION                                                       ║
║  Inputs:    GeoDataFrame in EPSG:4326                                        ║
║  Operation: gdf.estimate_utm_crs() → to_crs(); record EPSG in crs_utm column ║
║  Output:    GeoDataFrame in metric UTM (e.g. EPSG:32619 for Boston)          ║
║  Validation: crs.is_projected == True; crs_utm string per row                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3D — EIGHT-STEP GEOMETRY CLEANER (1, 2, 3, 4, 4b, 5, 6, 7)                  ║
║  Inputs:    UTM-projected GeoDataFrame                                       ║
║  Operation: null filter → non-poly drop → MultiPolygon explode → buffer(0)   ║
║             → is_valid re-filter → area/perimeter compute → 20 m² min-area   ║
║             → IoU>0.95 dedup with STRtree pre-filter                         ║
║  Output:    deduplicated, valid Polygon-only GeoDataFrame                    ║
║  Validation: 100% shapely.is_valid; min area ≥ 20 m²; no IoU>0.95 pairs      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3E — PROVENANCE FLAGS + data_quality_flag                                   ║
║  Inputs:    cleaned GeoDataFrame                                             ║
║  Operation: write 7 provenance columns + comma-joined quality flag string;   ║
║             OSM_OVERLAP_RESOLVED & OSM_GENERIC are canonical §12 tokens;     ║
║             100%-generic neighbourhood → WARN-and-flow (structured payload)  ║
║  Output:    +7 provenance cols + 1 data_quality_flag col                     ║
║  Validation: every flag token in closed vocabulary of 7                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3F — SCHEMA ENFORCEMENT + SERIALISATION                                     ║
║  Inputs:    23-column GeoDataFrame                                           ║
║  Operation: _validate_schema(); write 01_buildings_clean.gpkg + .log + .json ║
║  Output:    (N_buildings, 23) GeoPackage; in-process gpd.GeoDataFrame return ║
║  Validation: column count == 23; column order matches spec; osm_id unique    ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## INPUT MODES

| Mode | Trigger | Use case |
|---|---|---|
| (a) address | `location` is `str` | Named neighbourhood ("Chicago Loop") |
| (b) point | `location` is `(lat, lon)` tuple | Programmatic centroid |
| (c) bbox | `bbox=(N,S,E,W)` set | Reproducible study extent |
| (d) xml | `osm_path` set | Air-gapped / frozen-input HPC run |

Optional `retry_policy=` (a `tenacity.Retrying` object) wraps live-network fetches (a/b/c); mode (d) is deterministic and not retried. `tenacity` is not a base-install dependency.

---

## QUALITY FLAGS (closed vocabulary of 7)

| Token | Meaning |
|---|---|
| `no_floors` | `levels` (building:levels) was missing |
| `no_height` | `height_m` was missing |
| `generic_tag` | `building_tag` was `"yes"` / `""` / None — building exists but is untyped |
| `no_function` | both `function_tag` empty AND `building_tag` generic — no semantic signal at all |
| `overlap_resolved` | this row was the larger of an IoU>0.95 duplicate pair |
| `height_only_ft` | OSM `height` tag was in imperial feet, converted |
| `no_year` | `year_built` (start_date) was missing |

Empty string ⇒ fully observed. Tokens are comma-joined alphabetically for grep stability. When 100% of returned rows carry `generic_tag`, the cleaner emits one structured `logging.warning` with payload `{"event": "all_generic_neighbourhood", "bbox": (n,s,e,w), "n_rows": int}` and flows through (does not raise).

---

## KEY NUMBERS

| Quantity | Value | Source |
|---|---|---|
| Output schema width | exactly 23 columns | DESIGN §3F, decision row 54 |
| Min footprint kept | 20 m² | DESIGN §3D step 6, decision row 48 |
| IoU dedup threshold | > 0.95 (keep larger) | DESIGN §3D step 7 |
| EnergyPlus vertex ceiling | 120 vertices/polygon (warn ≥ 80) | DESIGN §5.1; Technical Pipeline §11.1 |
| Typical N_buildings | 200–5,000 per km² | DESIGN §4 |
| Peak memory | ~150 MB / 1,000 buildings | DESIGN §6 (empirical, Boston fixture) |
| Wall-clock target | ≤ 30 s for 5,000 buildings (default; loosens with retry_policy) | DESIGN §6 |
| GPU hours | 0 (CPU-only step) | DESIGN §6 |

---

## VALIDATION SUMMARY

- Schema column count: **exactly 23** — fail if narrower or wider.
- Geometry validity: **100%** of returned rows pass `shapely.is_valid` (enforced by step 4b explicit re-filter after `buffer(0)`).
- CRS: **every row projected** (`crs.is_projected == True`); UTM EPSG recorded per-row in `crs_utm`.
- Min footprint area: `min(footprint_area_m2) >= 20.0`.
- Vertex count: 95th percentile ≤ 120 (warn ≥ 80, fail ≥ 120) — Stage 3 simplify-or-hull engages on warn.
- Dedup outcome: **no two rows have IoU > 0.95**.
- `osm_id` uniqueness: 100% (after `_part{k}` MultiPolygon suffixing).
- `_parse_height_to_m` fixtures: `"30 ft"`→9.144, `"10'"`→3.048, `"12"`→12.0, `"12 m"`→12.0 (±1e-4).
- All-generic neighbourhood: returns gdf normally + emits exactly one structured warning.
- Retry-policy passthrough: `tenacity.Retrying` with 3-attempt-then-raise → raises after exactly 3 fetcher invocations.
- True Future Test: held-out cities (Seattle, Atlanta, Anchorage) span UTM zones 10N/16N/6W and ASHRAE climate zones 4C/3A/7 — integration smoke test on tagged releases asserts only universal §5.1 thresholds.

---

## OUTPUT

A **GeoPackage** at `<output_dir>/01_buildings_clean.gpkg` (layer `buildings`), shape `(N_buildings, 23)`, with:

- 1 geometry column
- 2 identity columns (`osm_id`, `crs_utm`)
- 9 raw OSM tag columns (`building_tag`, `function_tag`, `levels`, `height_m`, `year_built`, `postcode`, `underground`, `roof_shape`, `roof_height_m`)
- 2 computed columns (`footprint_area_m2`, `perimeter_m`)
- 1 surplus JSON column (`surplus_tags`) — **presence binding, key set non-binding** (best-effort; see DESIGN §6.1)
- 7 provenance columns (one per imputable parameter; canonical §12 tokens: `OSM_OBSERVED` / `OSM_MISSING` / `OSM_GENERIC` / `OSM_OVERLAP_RESOLVED` / `OSM_OBSERVED_FT`)
- 1 quality column (`data_quality_flag`, comma-joined tokens)

GeoPackage chosen because it round-trips pandas-nullable `Int64` for `levels` and `year_built` (GeoJSON lifts these to float and loses integer semantics).

---

## KEY DECISIONS

> Mirrors DESIGN §9 — same rows, one line each.

| Decision | Rationale (one line) |
|---|---|
| Single `ingest_buildings()` with four-mode dispatch + optional `retry_policy=` keyword | One stable API; mode (d) enables air-gapped HPC runs; retry keyword serves HPC/CI without a hard `tenacity` dep. |
| `osmnx >= 1.9, < 2.0` pin; relaxes to `<3.0` only after 6 mo PyPI + 2 stable minor releases + CI sprint | osmnx 2.x removed `geometries_from_*`; dual-trigger relaxation prevents premature jumps to a moving 2.x API. |
| UTM CRS via `estimate_utm_crs()`, recorded per row in `crs_utm` | Metric, near-conformal, globally available; unblocks the 20 m² metric filter. |
| Eight-step geometry cleaner (1, 2, 3, 4, 4b, 5, 6, 7) in fixed order | Order is load-bearing; 20 m² removes OSM noise; step 4b guarantees post-buffer validity. |
| Type coercions: `Int64` for `levels`/`year_built`; shared `_parse_height_to_m` for `height_m` and `roof_height_m` | Preserves integer semantics through GeoPackage; imperial values converted (not NaN'd) to avoid US completeness bias; one parser prevents regex drift. |
| `data_quality_flag` closed vocabulary (7 tokens); `OSM_OVERLAP_RESOLVED`+`OSM_GENERIC` canonical §12; 100%-generic neighbourhood WARN-and-flow | Grep-able fixed-width schema; canonical tokens survive downstream; raising on all-generic would block legitimate rural runs. |
| 23-column GeoPackage as binding output contract; `surplus_tags` presence binding but key set explicitly non-binding | Stage 2's `validate_schema()` needs a fixed contract; binding `surplus_tags` keys would couple Stage 1 release cadence to OSM tag-vocabulary changes. |

---

## OPEN QUESTIONS

- **Pipeline-spec follow-up:** canonical Technical Pipeline §12 vocabulary list must be edited to add `OSM_OVERLAP_RESOLVED` and `OSM_GENERIC`, and the Stage 2 schema-validation gate updated in lockstep. Until then, end-to-end runs fail at Stage 2's gate. → DESIGN §7
