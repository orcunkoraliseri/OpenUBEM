# OpenUBEM × GeoLibre Implementation Hub

**Status:** Implemented & verified offline + real-district tested on `ES-MAD-BERRUGUETE` (Madrid)  
**GeoLibre Version Tested:** `geolibre 3.8.0` (MIT License)  
**Scope:** Opt-in GIS workspace exporter (`.geolibre.json`), standalone web iframe wrapper (`geolibre_viewer.html`), GeoJSON export (`buildings_wgs84.geojson`), and Jupyter notebook `anywidget` helper (`create_geolibre_map`).

---

## 1. Architecture & File Inventory

GeoLibre is integrated strictly as an **opt-in companion layer** in OpenUBEM's `viz` package. Core Stage 1–6 simulation pipelines, deterministic CI CityJSON exports, and protected validation paths remain unchanged and require zero browser/widget dependencies unless the optional `geolibre` extra is installed.

| Component | Path | Responsibility |
|---|---|---|
| Core exporter & notebook API | [openubem/viz/geolibre_export.py](../../../openubem/viz/geolibre_export.py) | Read-only Stage 1–6 loader, optional results CSV join, RFC-8259 `NaN`/`Inf` sanitizer, 2.5D `fill-extrusion` + graduated choropleth styling, popups, STAC-aligned metadata, legend, bookmarks, Story Map, `export_geolibre_bundle`, and `create_geolibre_map`. |
| Step-5 & EU viewer pipeline hooks | [openubem/results/__init__.py](../../../openubem/results/__init__.py), [scripts/generate_eu_3d_viewers.py](../../../scripts/generate_eu_3d_viewers.py), [scripts/update_eu_outputs_3d.py](../../../scripts/update_eu_outputs_3d.py) | Automatically generate the GeoLibre bundle alongside the CityJSON/EU 3D viewers whenever `export_html=True` (`OPENUBEM_EXPORT_HTML=1`) or EU district viewer generation runs (opt-out via `export_geolibre=False` or `--no-geolibre`). |
| CLI entrypoint | [scripts/export_geolibre_project.py](../../../scripts/export_geolibre_project.py) | CLI wrapper (`parse_args`, `main`) exporting `<cell>.geolibre.json`, `buildings_wgs84.geojson`, `geolibre_viewer.html`, and `sources_manifest.json`. |
| Offline test suite | [tests/test_geolibre_export.py](../../../tests/test_geolibre_export.py) | Unit & integration tests covering constant-height resilience, CSV EUI join + `NaN` sanitization, Stage 6 UTCI/AQI caveats + context layers, `geolibre.Map` widget, CLI flags, and `docs_VALIDATION` write protection. |
| Optional extra | [pyproject.toml](../../../pyproject.toml) | `[project.optional-dependencies]` -> `geolibre = ["geolibre >= 3.8; python_version >= '3.11'"]`. |

---

## 2. Installation

Install OpenUBEM with the optional `geolibre` extra on Python 3.11+:

```bash
pip install -e ".[geolibre]"
```

Headless CLI/HPC environments on Python 3.10+ without `geolibre` installed can still invoke `export_geolibre_bundle` via its pure-Python fallback JSON/HTML emitter (without `geolibre.Map` widget support).

---

## 3. CLI Usage & Flags

```bash
python scripts/export_geolibre_project.py \
  --run-dir openubem/outputs/eu02/ES-MAD-BERRUGUETE \
  --results-csv docs/docs_ACTIVE/europeanLocations/results/EU11_results_2026-10-08_per_home.csv \
  --district ES-MAD-BERRUGUETE \
  --output-dir openubem/outputs/geolibre_companion/ES-MAD-BERRUGUETE
```

| Flag | Default | Description |
|---|---|---|
| `--run-dir` | *required* | Stage 1–6 OpenUBEM run directory (opened read-only). |
| `--output-dir` | `<run_dir>/geolibre_companion` | Destination directory (refuses paths inside `docs_VALIDATION/`; redirects `docs_VALIDATION/` inputs to `openubem/outputs/geolibre_companion/<cell>`). |
| `--buildings-path` | `None` | Explicit `.gpkg`, `.parquet`, or `.geojson` file override. |
| `--results-csv` | `None` (auto-reads `<run_dir>/05_results.csv` if present) | Optional results CSV left-joined by `osm_id` / `building_id`. |
| `--district` | `None` | Optional district filter when joining multi-district result CSVs (e.g. `ES-MAD-BERRUGUETE`). |
| `--color-by` | Auto-selected by priority | Explicit numeric column for graduated choropleth styling. |
| `--colormap` | `turbo` | GeoLibre vector color ramp (`turbo`, `viridis`, `plasma`, `inferno`, etc.). |
| `--basemap` | `dark` | Named GeoLibre basemap (`dark`, `liberty`, `bright`, `positron`, `fiord`) or MapLibre style URL. |
| `--scheme` | `quantile` | Choropleth classification scheme (`quantile` or `equal-interval`). |
| `--class-count` | `5` | Number of graduated classes (2–12). |
| `--no-extrude` | `False` | Disable 2.5D `fill-extrusion` and set camera pitch/bearing to 0°. |
| `--no-story-map` | `False` | Omit interactive Story Map chapters from `.geolibre.json`. |

---

## 4. Multi-Stage Input Resolution & Data Hygiene

1. **Candidate Vector Resolution Order (`_CANDIDATE_BUILDING_FILES`):**
   `06_mc_summary.gpkg` -> `05_results.gpkg` -> `buildings.parquet` -> `buildings.gpkg` -> `buildings.geojson` -> `02b_enriched.gpkg` -> `02_buildings_imputed.gpkg` -> `02_classified.gpkg` -> `02_residential_manifest.gpkg` -> `01_buildings_clean.gpkg` -> `01_buildings_raw.gpkg` -> `01_buildings.gpkg`.
2. **Results CSV Join:** Automatically joins `<run_dir>/05_results.csv` (when present) or `--results-csv`, matching on `osm_id` or `building_id` and preserving non-colliding columns.
3. **Metric Auto-Selection Priority (`_METRIC_PRIORITY`):**
   `total_eui_kwh_m2` -> `eui_heating_kwh_m2` -> `utci_peak_c` -> `utci_mean_c` -> `total_gwp_kgco2e` -> `height_m` -> `year_built` -> `footprint_area_m2`.
4. **Honest Height & Missing-Value Handling:**
   - Computes display-only `extrusion_height_m` (`height_m` when finite `> 0`, else `levels * 3.0`, else `0.0`) **without modifying raw `height_m` or `provenance_height_m`**.
   - Sanitizes all `NaN`, `Inf`, and `pd.NA` cells to `null` (`None`) so strict RFC-8259 JSON serialization (`allow_nan=False`) succeeds cleanly in GeoLibre and DuckDB-WASM.
5. **Context Layers & Stage 6 Caveats:**
   - Optional `06_context_blocks.geojson`, `06_context_green.geojson`, and `06_context_roads.geojson` are placed underneath the buildings layer.
   - Stage 6 UTCI attributes embed the mandatory unvalidated-product caveat in `descriptiveMetadata.abstract`, Story Map text, and `sources_manifest.json`.
   - Ambient Air Quality attributes embed `GMAPS_AIR_QUALITY_AMBIENT_NOT_DISPERSED` macro-scale context caveats.

---

## 5. Jupyter Notebook Two-Way Exploration & DuckDB Spatial SQL

### Interactive Notebook Widget

```python
from openubem.viz.geolibre_export import create_geolibre_map

m = create_geolibre_map(
    "openubem/outputs/eu02/ES-MAD-BERRUGUETE",
    results_csv_path="docs/docs_ACTIVE/europeanLocations/results/EU11_results_2026-10-08_per_home.csv",
    district_filter="ES-MAD-BERRUGUETE",
    height="760px",
    app_layout="full",
    theme="dark",
)
m
```

### DuckDB-WASM Spatial SQL Examples (Inside `geolibre.app`)

Load `buildings_wgs84.geojson` or the `.geolibre.json` project into [geolibre.app](https://geolibre.app/) and query attributes client-side:

```sql
-- Top 20 highest heating-EUI residential buildings with observed height
SELECT osm_id, archetype_id, height_m, floor_area_m2, eui_heating_kwh_m2
FROM buildings_wgs84
WHERE eui_heating_kwh_m2 IS NOT NULL
ORDER BY eui_heating_kwh_m2 DESC
LIMIT 20;
```

```sql
-- Mean heating EUI and total heated floor area grouped by TABULA age band
SELECT age_band, COUNT(*) AS n_buildings,
       ROUND(AVG(eui_heating_kwh_m2), 2) AS mean_heating_eui,
       ROUND(SUM(floor_area_m2), 1) AS total_floor_area_m2
FROM buildings_wgs84
WHERE eui_heating_kwh_m2 IS NOT NULL
GROUP BY age_band
ORDER BY mean_heating_eui DESC;
```

---

## 6. Comparison Across OpenUBEM Viewers

| Viewer | File / Entrypoint | Geometry Model | Network Required | Primary Role |
|---|---|---|---|---|
| **Offline CityJSON 3D** | [openubem/viz/viewer_export.py](../../../openubem/viz/viewer_export.py) | CityJSON v2.0 LOD1/LOD3 (walls, roofs, windows, doors) | Zero (`file://` self-contained) | Deterministic CI-verified physics & provenance viewer |
| **EU Floor-Plan 3D** | [scripts/generate_eu_3d_viewers.py](../../../scripts/generate_eu_3d_viewers.py) | IDF-parsed storey shells + dwelling/core partitions | Zero (`file://` self-contained) | Dwelling-level zoning inspection & audit modal |
| **Google Maps 3D Companion** | [openubem/viz/gmaps_web_export.py](../../../openubem/viz/gmaps_web_export.py) | `<gmp-map-3d>` Photorealistic 3D Tiles + GeoJSON overlay | Online + runtime Google Maps API key | Street-context photogrammetry & AI Studio prompt handoff |
| **GeoLibre GIS Companion** | [openubem/viz/geolibre_export.py](../../../openubem/viz/geolibre_export.py) | MapLibre 2.5D `fill-extrusion` + multi-layer GeoJSON/raster/SQL | `.geolibre.json` local in desktop/Jupyter; `geolibre_viewer.html` loads `web.geolibre.app` | Interactive GIS exploration, DuckDB-WASM SQL, bookmarks & Story Maps (no API key) |

---

## 7. Real-District Verification: `ES-MAD-BERRUGUETE` (Madrid)

Executed after implementation against real Madrid Stage-2 footprints (`02_residential_manifest.gpkg`) joined with EU-11 EnergyPlus results (`EU11_results_2026-10-08_per_home.csv`):

- **Buildings exported:** `1,194` footprints (`1,119` matched with simulated `eui_heating_kwh_m2`, matching the published `ES-MAD-BERRUGUETE` benchmark count).
- **Bounding box (WGS 84):** `[-3.711012, 40.454341, -3.698695, 40.463801]` (center `-3.704854, 40.459071`, zoom `15.25`, pitch `52°`, bearing `-20°`).
- **Graduated `eui_heating_kwh_m2` quantile stops (`turbo`):** `18.51`, `46.56`, `80.23`, `112.12`, `282.33` kWh/m²·a.
- **Generated artifacts under `openubem/outputs/geolibre_companion/ES-MAD-BERRUGUETE/`:**
  - `ES-MAD-BERRUGUETE.geolibre.json` (`3,173,365` bytes; validated round-trip via `geolibre.load_project` and `geolibre.describe_project`)
  - `buildings_wgs84.geojson` (`1,362,797` bytes)
  - `geolibre_viewer.html` (`1,466,759` bytes)
  - `sources_manifest.json` (`671` bytes; `api_key_embedded: false`)
