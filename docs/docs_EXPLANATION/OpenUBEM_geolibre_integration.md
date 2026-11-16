# OpenUBEM × GeoLibre Integration Guide

**What this document is:** a conceptual and practical guide to OpenUBEM's opt-in **GeoLibre** companion layer (`openubem/viz/geolibre_export.py` and `scripts/export_geolibre_project.py`). It explains *why* GeoLibre sits alongside OpenUBEM's offline 3D viewers rather than replacing them, how provenance and Stage 6 caveats are preserved inside GIS workspaces, and how to use GeoLibre for browser and Jupyter district QA.

For CLI flags, schema details, and test metrics, see the active implementation hub: [`docs/docs_ACTIVE/GeoLibre/README_geolibre_implementation.md`](../docs_ACTIVE/GeoLibre/README_geolibre_implementation.md).

---

## 1. Role in OpenUBEM's Visualization Ecosystem

OpenUBEM produces physics-grounded urban building energy models (Stages 1–5) and optional pedestrian thermal comfort fields (Stage 6). Different inspection tasks demand different viewer trade-offs:

1. **Deterministic Physics & Provenance Audit (`viewer_export.py`):**
   Compiles a single zero-network `file://` HTML file embedding CityJSON v2.0 LOD1/LOD3 surfaces (walls, roofs, windows, doors), baked basemaps, and byte-reproducible CI hashes.
2. **Dwelling-Level Architectural Audit (`generate_eu_3d_viewers.py`):**
   Reads EnergyPlus `.idf` zones directly so users can click any building and inspect storey-by-storey dwelling/core partitions.
3. **Photorealistic Street Context (`gmaps_web_export.py`):**
   Exports WGS 84 footprints onto Google Maps `<gmp-map-3d>` Photorealistic 3D Tiles when the user supplies a Google Maps API key at runtime.
4. **Interactive GIS Exploration & Spatial SQL (`geolibre_export.py` — New):**
   Bridges OpenUBEM artifacts into **GeoLibre** (`opengeos/GeoLibre`, MIT-licensed), providing MapLibre 2.5D building extrusions, graduated EUI/UTCI choropleths, click/hover popups, bookmarks, Story Map tours, in-browser **DuckDB-WASM Spatial SQL**, and two-way Jupyter notebook synchronization (`geolibre.Map`)—with **zero API keys required**.

> **Design boundary:** GeoLibre visualizes 2.5D footprints, multi-layer GeoJSON/vector/raster overlays, and tabular attributes. It does **not** parse CityJSON LOD3 openings or EnergyPlus IDF dwelling floor plans, so it complements—and never replaces—`viewer_export.py` and `generate_eu_3d_viewers.py`.

---

## 2. Why Keep GeoLibre Optional?

OpenUBEM targets both interactive desktop researchers and headless HPC/SLURM cluster campaigns running on Python 3.10+. Requiring `geolibre` (which pulls in `anywidget`, `ipywidgets`, and IPython notebook plumbing on Python 3.11+) in core dependencies would unnecessarily bloat batch simulation environments.

Therefore:
- `pyproject.toml` places `geolibre >= 3.8; python_version >= '3.11'` under `[project.optional-dependencies]`.
- `openubem/viz/geolibre_export.py` checks `has_geolibre()` at runtime and includes a pure-Python JSON/HTML fallback so `export_geolibre_bundle` still emits valid `.geolibre.json`, `.geojson`, `.html`, and manifest files even when the optional extra is not installed.
- `create_geolibre_map()` explicitly requires `pip install "openubem[geolibre]"` to render interactive `anywidget` maps inside JupyterLab or VS Code notebooks.

---

## 3. Data Integrity, Provenance & Scientific Caveats

OpenUBEM's core reporting discipline applies equally inside GeoLibre workspaces:

### 3.1 Separate Display Height (`extrusion_height_m`)
Buildings missing an observed or fused `height_m` cannot be extruded as `null` in WebGL, yet OpenUBEM never overwrites raw `height_m` or `provenance_height_m` with guessed heights. The exporter creates a dedicated display column `extrusion_height_m`:
- Uses finite positive `height_m` when present;
- Falls back to `levels * 3.0 m` when storey count is known;
- Otherwise sets `extrusion_height_m = 0.0` while leaving `height_m: null` and `provenance_height_m` intact in popups and attribute tables.

### 3.2 Strict RFC-8259 JSON Sanitization
Pandas/GeoPandas represent missing or failed simulations as `NaN` or `Inf`, which invalidates strict JSON parsers (`geolibre.save_project(..., allow_nan=False)` and browser `JSON.parse`). Every feature property passes through `_to_json_scalar` so `NaN`, `Inf`, and `pd.NA` serialize cleanly as JSON `null`.

### 3.3 Mandatory Stage 6 & Air Quality Caveats
Whenever Stage 6 microclimate columns (`utci_peak_c`, `utci_mean_c`, `ctsi_degc_h`) or Google Air Quality fields (`aq_provenance`) are detected:
- Layer catalog metadata (`descriptiveMetadata.abstract`), Story Map chapter descriptions, and `sources_manifest.json` explicitly record that **Stage 6 UTCI is an unvalidated analysis product** (not measured thermal comfort) and that **ambient AQI (`GMAPS_AIR_QUALITY_AMBIENT_NOT_DISPERSED`) reflects macro-scale regional context rather than street-canyon dispersion**.

### 3.4 Protected Validation Paths
Following OpenUBEM's snapshot protection rule, `resolve_geolibre_output_dir` never writes into `docs/docs_VALIDATION/`: reading from a frozen validation directory redirects default output to `openubem/outputs/geolibre_companion/<cell>/`, and passing an explicit `docs_VALIDATION` destination raises `ValueError`.

---

## 4. Offline Workspace vs. Hosted HTML Viewer

| Artifact | Offline Behavior | Best Used When… |
|---|---|---|
| `<cell>.geolibre.json` | 100% self-contained data (inlined WGS 84 GeoJSON + styles + Story Map); vector basemap tiles load from OpenFreeMap unless an offline PMTiles basemap is configured in GeoLibre. | Opening in GeoLibre Desktop, dragging into `geolibre.app`, or sharing reproducible GIS state files. |
| `buildings_wgs84.geojson` | Pure local RFC-7946 GeoJSON file. | Running DuckDB-WASM SQL queries in `geolibre.app`, QGIS, or Python `geopandas`. |
| `geolibre_viewer.html` | Embeds `https://web.geolibre.app/?embed=1` in an `<iframe>` and posts the project via `postMessage`. | Quick sharing in a browser when internet access to `web.geolibre.app` is available (note: for air-gapped `file://` viewing, use `viewer_export.py` instead). |

---

## 5. Interactive Notebook Workflow

In a Jupyter notebook, you can inspect any pipeline stage directly without writing custom `matplotlib` scripts:

```python
from openubem.viz.geolibre_export import create_geolibre_map

# Inspect Stage 2 footprints or Stage 5 energy results interactively
m = create_geolibre_map(
    "openubem/outputs/eu02/ES-MAD-BERRUGUETE",
    results_csv_path="docs/docs_ACTIVE/europeanLocations/results/EU11_results_2026-10-08_per_home.csv",
    district_filter="ES-MAD-BERRUGUETE",
    color_by="eui_heating_kwh_m2",
    colormap="turbo",
    scheme="quantile",
)
m
```

Because `geolibre.Map` syncs UI state bidirectionally with Python, you can pan/filter interactively in the cell, inspect selected buildings (`m.get_selected_features()`), draw regions of interest (`m.user_rois()`), or export an updated workspace (`m.save_project("edited.geolibre.json")`).

---

*OpenUBEM × GeoLibre integration guide — companion to `OpenUBEM_fundamentals.md` §8.7 (2026-11-16).*
